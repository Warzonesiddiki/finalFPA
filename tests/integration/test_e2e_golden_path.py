"""Scripted API-level End-to-End Golden Path Smoke Test (TST-E2E-01) per doc 14 §9.1.

Simulates the complete month-end journey against the real FastAPI app:
1. Launch & Bootstrap: verifies health, app metadata, and retrieves session token.
2. Open project: confirms a committed import batch exists with its validation report.
3. Import & Validation: imports a *balanced* GL fixture and asserts the documented
   committed path; additionally imports an *unbalanced* fixture and asserts the
   documented rejected path (doc 04 §11).
4. BvA Matrix & Transaction Drilldown: queries BvA summary, verifies variance fields,
   and drills to transaction rows (FR-BVA-004).
5. Exceptions Register & Workflow: runs rules, lists exceptions, inspects evidence,
   updates status (Open -> In Review) with an append-only audit note (FR-EXC-006/008).
6. Forecast Workspace & Scenarios: refreshes run-rate projections, applies a manual
   override with mandatory reason, locks the version, reads the accuracy report.
7. Output Packs & Issuance: generates the Excel workbook + PPT deck, saves commentary,
   formally issues the pack, and verifies the re-issue version increment.

Spec basis for the batch-status fix (why the old `assert status == "committed"` on an
arbitrary batch was wrong):

  Doc `04` §11 (Reject vs quarantine — the decision rule):
    "File-level failure (reject) | The file as a whole cannot be trusted or read:
     unreadable/encrypted, no header, missing required columns, duplicate headers
     unresolved, ≥ 90% rows unmapped, **debit ≠ credit**, checksum re-import, newer
     template, empty data range (default) | **Nothing is committed.** The batch is
     recorded as `rejected` with the failing check, the file is not added to the
     analytic model ..."

  Doc `04` §12 (Balance and control-total reconciliation):
    "Debit = credit | Computed at minor-unit precision (exact; no epsilon, `05` §13)
     per file, per entity, per period, and overall."

  Doc `14` §4.3 (`TST-IMP` family): "one test per check: `TST-IMP-nn` exercises
  `IMP-nn` ... with its documented outcome (pass / warn / reject / confirm)".

  Doc `14` §9.1 (golden path): "Launch → open the sample project → import a file →
  pass validation → drill a variance ... Assertions at each step: the expected screen,
  the expected numbers, the expected job outcome, and no console errors."

The bank sample (`sample-data/bank_ledger_actuals.csv`) is *genuinely imbalanced*
(withdrawals 7,997,971 vs deposits 4,855,017), so per doc `04` §11 it is correctly
recorded `rejected`. The test must therefore not assume an arbitrary batch is
`committed`; it must assert the *documented* outcome for the fixture it imports.

This test is self-isolating: it points the engine at a temporary project directory
and writes synthetic fixtures there. It never edits `sample-data/` (doc `14` §16).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.engine.store.db as db_module
from app.api.main import app, SESSION_TOKEN

# Balanced GL fixture: 500,000 debit on 5200, 500,000 credit on 4000 -> debit == credit.
_BALANCED_GL = (
    "Voucher,PostingDate,CompanyCode,MainAccount,CostCenter,ProjectCode,"
    "VendorCode,InvoiceNumber,TransactionDescription,Debit,Credit,Currency,"
    "Watermark,ProjectType\n"
    "VCH-2026-0912-001,2026-09-15,IN01,5200,CC-100,PRJ-01,V-00931,INV-1001,"
    "Repair posting,500000.00,0.00,INR,{wm},sample\n"
    "VCH-2026-0912-001,2026-09-15,IN01,4000,CC-100,PRJ-01,V-00931,INV-1001,"
    "Revenue offset,0.00,500000.00,INR,{wm},sample\n"
)

# Unbalanced GL fixture: debit 1,000 vs credit 990 -> debit != credit (file-level reject).
_UNBALANCED_GL = (
    "Voucher,PostingDate,CompanyCode,MainAccount,CostCenter,ProjectCode,"
    "VendorCode,InvoiceNumber,TransactionDescription,Debit,Credit,Currency,"
    "Watermark,ProjectType\n"
    "VCH-2026-0913-001,2026-09-16,IN01,5200,CC-100,PRJ-01,V-00931,INV-2001,"
    "Unbalanced debit,1000.00,0.00,INR,{wm},sample\n"
    "VCH-2026-0913-001,2026-09-16,IN01,4000,CC-100,PRJ-01,V-00931,INV-2001,"
    "Unbalanced credit,0.00,990.00,INR,{wm},sample\n"
)

# Budget fixture for the period so BvA has a non-zero budget column.
_BUDGET = (
    "PeriodCode,EntityCode,CostCenterCode,AccountCode,BudgetAmount,"
    "Watermark,ProjectType\n"
    "FY26-P09,IN01,CC-100,5200,400000.00,{wm},sample\n"
    "FY26-P09,IN01,CC-100,4000,480000.00,{wm},sample\n"
)

_WATERMARK = "SAMPLE DATA - FICTIONAL - DO NOT USE"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Isolated engine project + synthetic fixtures on disk (no sample-data edits)."""
    project_dir = tmp_path / "project"
    monkeypatch.setattr(db_module, "DEFAULT_PROJECT_DIR", project_dir)

    wm = _WATERMARK
    (tmp_path / "gl_balanced.csv").write_text(_BALANCED_GL.format(wm=wm), encoding="utf-8")
    (tmp_path / "gl_unbalanced.csv").write_text(_UNBALANCED_GL.format(wm=wm), encoding="utf-8")
    (tmp_path / "budget.csv").write_text(_BUDGET.format(wm=wm), encoding="utf-8")

    return TestClient(app)


# The full scripted month-end journey (import, rules, forecast, Excel pack, PPT
# pack, issuance) costs 7-12s on the reference host - over the 5s threshold, and it
# is the slowest unmarked test in the suite.
#
# Marked `perf` per doc 17 section 3.0: "New slow tests (scale, benchmark,
# long-running integration) MUST be marked `perf`". It stays in the performance
# gate via `pytest -m perf` and is excluded from the fast gate, which is what keeps
# the default `pytest` usable.
@pytest.mark.perf
def test_e2e_golden_path_smoke_journey(client: TestClient, tmp_path: Path):
    """Execute the complete month-end golden path and assert every step."""
    headers = {"X-Session-Token": SESSION_TOKEN}

    # -------------------------------------------------------------------------
    # Step 1: Launch & Bootstrap (SCR-001, FR-ONB-001)
    # -------------------------------------------------------------------------
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"
    assert res_health.json()["engine_ready"] is True

    res_boot = client.get("/api/v1/bootstrap")
    assert res_boot.status_code == 200
    boot_data = res_boot.json()
    assert boot_data["status"] == "ok"
    assert "session_token" in boot_data

    # -------------------------------------------------------------------------
    # Step 2: Import a *balanced* file -> documented committed path
    #         (doc 04 §11: a balanced file is committed; doc 04 §12: debit == credit)
    # -------------------------------------------------------------------------
    res_gl = client.post(
        "/api/v1/imports",
        headers=headers,
        json={"path": str((tmp_path / "gl_balanced.csv").resolve())},
    )
    assert res_gl.status_code == 200
    gl = res_gl.json()
    assert gl["isBalanced"] is True
    assert gl["totalSourceRows"] == gl["loadedCount"] + gl["quarantinedCount"] + gl["rejectedCount"]
    assert Decimal(gl["totalDebit"]) == Decimal(gl["totalCredit"])
    committed_batch_id = gl["batchId"]

    res_batches = client.get("/api/v1/imports", headers=headers)
    assert res_batches.status_code == 200
    batch_list = res_batches.json()["data"]["items"]
    assert len(batch_list) > 0
    committed_batch = next(b for b in batch_list if b["batch_id"] == committed_batch_id)
    assert committed_batch["status"] == "committed"
    assert committed_batch["loaded_count"] > 0
    assert committed_batch["is_balanced"] == 1

    # -------------------------------------------------------------------------
    # Step 3: Import an *unbalanced* file -> documented rejected path
    #         (doc 04 §11: "debit ≠ credit" -> Nothing is committed; batch rejected)
    # -------------------------------------------------------------------------
    res_bad = client.post(
        "/api/v1/imports",
        headers=headers,
        json={"path": str((tmp_path / "gl_unbalanced.csv").resolve())},
    )
    assert res_bad.status_code == 200
    bad = res_bad.json()
    assert bad["isBalanced"] is False
    rejected_batch_id = bad["batchId"]

    rejected_batch = next(
        b for b in client.get("/api/v1/imports", headers=headers).json()["data"]["items"]
        if b["batch_id"] == rejected_batch_id
    )
    # Doc 04 §11: the batch is recorded as rejected and the file is NOT added to the model.
    assert rejected_batch["status"] == "rejected"
    res_report = client.get(
        f"/api/v1/imports/{committed_batch_id}/report", headers=headers
    )
    # The committed batch's validation report carries the balance check (IMP-023).
    if res_report.status_code == 200:
        checks = res_report.json()["data"]["checks"]
        assert any(c["check_code"] == "IMP-023" and c["status"] == "pass" for c in checks)

    # -------------------------------------------------------------------------
    # Step 4: Import budget, then BvA matrix + transaction drill (FR-BVA-001..004)
    # -------------------------------------------------------------------------
    res_bud = client.post(
        "/api/v1/imports",
        headers=headers,
        json={"path": str((tmp_path / "budget.csv").resolve())},
    )
    assert res_bud.status_code == 200
    assert res_bud.json()["sourceType"] == "budget"

    res_bva = client.get(
        "/api/v1/analysis/bva?period_id=9&window=MTD", headers=headers
    )
    assert res_bva.status_code == 200
    bva_items = res_bva.json()["data"]["items"]
    assert len(bva_items) > 0
    first_row = next(r for r in bva_items if r["accountCode"] == "5200")
    assert "varianceAmount" in first_row
    assert "favourability" in first_row

    res_drill = client.get(
        f"/api/v1/analysis/drill?account_id={first_row['accountId']}&period_id=9",
        headers=headers,
    )
    assert res_drill.status_code == 200
    drill_data = res_drill.json()["data"]
    assert drill_data["total"] >= 1
    assert len(drill_data["items"]) >= 1
    assert drill_data["items"][0]["voucherNo"].startswith("VCH-2026-")

    # -------------------------------------------------------------------------
    # Step 5: Exceptions Register & Workflow (SCR-023, FR-EXC-001..010)
    # -------------------------------------------------------------------------
    res_run = client.post(
        "/api/v1/exceptions/run",
        headers=headers,
        json={"period": "FY26-P09", "asOfDate": "2026-11-12"},
    )
    assert res_run.status_code == 200
    assert res_run.json()["data"]["rulesRun"] > 0

    res_exc = client.get("/api/v1/exceptions?period=FY26-P09", headers=headers)
    assert res_exc.status_code == 200
    exceptions = res_exc.json()["data"]["items"]
    assert len(exceptions) > 0
    target_exc = exceptions[0]
    exc_id = target_exc["exception_id"]

    res_exc_detail = client.get(f"/api/v1/exceptions/{exc_id}", headers=headers)
    assert res_exc_detail.status_code == 200
    detail = res_exc_detail.json()["data"]
    assert "evidenceRefs" in detail

    res_patch = client.patch(
        f"/api/v1/exceptions/{exc_id}",
        headers=headers,
        json={
            "status": "in_review",
            "owner": "Aarti",
            "note": "Golden path smoke review initiated.",
        },
    )
    assert res_patch.status_code == 200
    patched = res_patch.json()["data"]
    assert patched["exception"]["status"] == "in_review"
    assert any("Golden path smoke review initiated." in n["noteText"] for n in patched["notes"])

    # -------------------------------------------------------------------------
    # Step 6: Forecast refresh, override, lock & accuracy (FR-FC-001..009)
    # -------------------------------------------------------------------------
    res_fc = client.post(
        "/api/v1/forecast/run",
        headers=headers,
        json={"period": "FY26-P09", "scenario": "base", "default_method": "run_rate", "run_rate_n": 3},
    )
    assert res_fc.status_code == 200
    fc_data = res_fc.json()["data"]
    assert fc_data["scenario"] == "base"
    assert len(fc_data["lines"]) > 0

    target_acct = fc_data["lines"][0]["account_id"]
    res_ov = client.patch(
        "/api/v1/forecast/cells",
        headers=headers,
        json={
            "account_id": target_acct,
            "period_code": "FY26-P10",
            "amount": "850000.00",
            "reason": "Executive revised target per contract sign-off",
            "scenario": "base",
        },
    )
    assert res_ov.status_code == 200

    res_lock = client.post(
        f"/api/v1/forecast/versions/{fc_data['versionId']}/lock",
        headers=headers,
        json={"confirm": True},
    )
    assert res_lock.status_code == 200

    res_acc = client.get("/api/v1/forecast/accuracy", headers=headers)
    assert res_acc.status_code == 200
    assert "signedBias" in res_acc.json()["data"]

    # -------------------------------------------------------------------------
    # Step 7: Reports Pack Generation & Issuance (SCR-029..SCR-031)
    # -------------------------------------------------------------------------
    res_pack = client.post(
        "/api/v1/packs/generate",
        headers=headers,
        json={"period": "FY26-P09", "scenario": "base", "format": "both"},
    )
    assert res_pack.status_code == 200
    generated_packs = res_pack.json()["data"]["items"]
    assert len(generated_packs) == 2
    assert any(p["pack_token"] == "excel" for p in generated_packs)
    assert any(p["pack_token"] == "ppt" for p in generated_packs)

    res_comm = client.put(
        "/api/v1/commentary",
        headers=headers,
        json={
            "period_id": 9,
            "scope_type": "executive",
            "subject_key": "EXECUTIVE",
            "text": "Executive Narrative: Q3 closed strong with healthy revenue and zero material exceptions.",
        },
    )
    assert res_comm.status_code == 200

    res_issue = client.post(
        "/api/v1/issuance",
        headers=headers,
        json={
            "period_id": 9,
            "period_code": "FY26-P09",
            "recipients": ["board@acme.com", "cfo@acme.com"],
            "notes": "Month-End Board Release FY26-P09",
        },
    )
    assert res_issue.status_code == 200
    issue_record = res_issue.json()["data"]
    assert issue_record["status"] == "issued"
    assert issue_record["pack_version"] >= 1

    res_reissue = client.post(
        f"/api/v1/issuance/{issue_record['issue_id']}/reissue",
        headers=headers,
        json={
            "issue_id": issue_record["issue_id"],
            "reason": "Final audit endorsement added to slide 4",
        },
    )
    assert res_reissue.status_code == 200
    reissue_record = res_reissue.json()["data"]
    assert reissue_record["pack_version"] == issue_record["pack_version"] + 1

    res_history = client.get("/api/v1/issuance?period_id=9", headers=headers)
    assert res_history.status_code == 200
    all_issues = res_history.json()["data"]["items"]
    prev_issue = next(i for i in all_issues if i["issue_id"] == issue_record["issue_id"])
    assert prev_issue["status"] == "superseded"
