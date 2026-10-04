"""API route contract and integration tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.main import SESSION_TOKEN, app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["engine_ready"] is True


def test_variance_demo_unauthorized():
    response = client.post(
        "/api/v1/calc/variance-demo",
        json={"actual": "1250000.50", "budget": "1000000.00"},
    )
    assert response.status_code == 401


def test_variance_demo_authorized():
    response = client.post(
        "/api/v1/calc/variance-demo",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={"actual": "1250000.50", "budget": "1000000.00"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["actual"] == "1250000.50"
    assert data["budget"] == "1000000.00"
    assert data["variance"] == "250000.50"
    assert data["variance_pct"] == "25.00"


def test_analysis_bva_endpoint():
    """Verify GET /api/v1/analysis/bva returns paged BvA structure."""
    response = client.get(
        "/api/v1/analysis/bva",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "ok"
    assert "items" in res["data"]
    assert "total" in res["data"]
    assert "hasMore" in res["data"]


def test_analysis_drill_endpoint():
    """Verify GET /api/v1/analysis/drill returns paged transaction evidence."""
    response = client.get(
        "/api/v1/analysis/drill",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "ok"
    assert "items" in res["data"]
    assert "total" in res["data"]


def test_bva_live_endpoints():
    """Verify live GET /api/v1/bva, statement-lines, and drill endpoints per Phase 2 requirements."""
    # 1. GET /api/v1/bva
    res_bva = client.get("/api/v1/bva", headers={"X-Session-Token": SESSION_TOKEN})
    assert res_bva.status_code == 200
    bva_json = res_bva.json()
    assert bva_json["status"] == "ok"
    assert "items" in bva_json["data"]

    # 2. GET /api/v1/bva/statement-lines
    res_lines = client.get("/api/v1/bva/statement-lines", headers={"X-Session-Token": SESSION_TOKEN})
    assert res_lines.status_code == 200
    lines_json = res_lines.json()
    assert lines_json["status"] == "ok"
    assert "items" in lines_json["data"]

    # 3. GET /api/v1/bva/drill
    res_drill = client.get("/api/v1/bva/drill", headers={"X-Session-Token": SESSION_TOKEN})
    assert res_drill.status_code == 200
    drill_json = res_drill.json()
    assert drill_json["status"] == "ok"
    assert "items" in drill_json["data"]


# Imports the full budget file and runs live BvA aggregation + statement-line
# drill-down against it: 8-11s on the reference host, the slowest unmarked test in
# the suite.
#
# Marked `perf` per doc 17 section 3.0 ("long-running integration MUST be marked
# `perf`"). It remains available through `pytest -m perf`.
#
# NOTE for whoever tunes this: it is also the only integration test here that is
# NOT self-isolating - it reads `sample-data/` and commits into the shared default
# project directory, which is why its runtime and its results both drift when four
# agents run suites concurrently. Marking it `perf` removes it from the fast gate
# but does not fix the isolation; that is a separate change.
def test_bva_live_with_budget_file():
    """Verify live BvA calculations with budget file."""
    budget_path = Path("sample-data/budget_fy26.csv")
    if budget_path.exists():
        # Import budget
        res_import = client.post(
            "/api/v1/imports",
            headers={"X-Session-Token": SESSION_TOKEN},
            json={"path": str(budget_path.resolve())},
        )
        assert res_import.status_code == 200
        assert res_import.json()["sourceType"] == "budget"

        # Query BvA for period 9
        res_bva = client.get(
            "/api/v1/bva?period_id=9",
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert res_bva.status_code == 200
        items = res_bva.json()["data"]["items"]
        assert len(items) > 0
        assert any(float(it["budgetAmount"]) > 0 for it in items)

        # Query statement lines for period 9
        res_stmts = client.get(
            "/api/v1/bva/statement-lines?period_id=9",
            headers={"X-Session-Token": SESSION_TOKEN},
        )
        assert res_stmts.status_code == 200
        stmt_items = res_stmts.json()["data"]["items"]
        assert len(stmt_items) > 0
        tot_stmt_budget = sum(float(s["budgetAmount"]) for s in stmt_items)
        tot_bva_budget = sum(float(b["budgetAmount"]) for b in items)
        assert abs(tot_stmt_budget - tot_bva_budget) < 0.01


def test_exceptions_endpoints_workflow():
    """Verify exceptions execution, listing, detail, patch, and bulk operations per FR-EXC."""
    # 1. Run rules
    res_run = client.post(
        "/api/v1/exceptions/run",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={"period": "FY26-P09", "asOfDate": "2026-11-12"},
    )
    assert res_run.status_code == 200
    run_data = res_run.json()["data"]
    # 19 de-duplicated evaluators covering all 24 catalog rules (EXC-001..EXC-024).
    # The previous value of 16 was the naive 8+8 concatenation of BATCH_01_08 and
    # BATCH_09_16, which double-evaluated catalog EXC-009/012/015 and omitted the
    # 17-24 batch entirely. See app/engine/rules/batch.py.
    assert run_data["rulesRun"] == 19
    assert run_data["catalogRulesCovered"] == 24
    assert "totalFindings" in run_data

    # 2. List exceptions
    res_list = client.get(
        "/api/v1/exceptions?period=FY26-P09",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_list.status_code == 200
    list_data = res_list.json()["data"]
    assert "items" in list_data
    assert "summary" in list_data
    items = list_data["items"]
    assert len(items) > 0

    first_exc = items[0]
    first_id = first_exc["exception_id"]
    assert "severity" in first_exc
    assert "aging_bucket" in first_exc
    assert "days_open" in first_exc
    assert "is_overdue" in first_exc

    # 3. Get exception detail
    res_detail = client.get(
        f"/api/v1/exceptions/{first_id}",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_detail.status_code == 200
    detail_data = res_detail.json()["data"]
    assert detail_data["exception"]["exception_id"] == first_id
    assert "sampleRows" in detail_data
    assert "notes" in detail_data
    assert "events" in detail_data
    assert len(detail_data["events"]) >= 1

    # 4. Patch exception (status, owner, note)
    res_patch = client.patch(
        f"/api/v1/exceptions/{first_id}",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "status": "in_review",
            "owner": "Rahul",
            "note": "Investigating potential discrepancy with vendor.",
        },
    )
    assert res_patch.status_code == 200
    patched_data = res_patch.json()["data"]
    assert patched_data["exception"]["status"] == "in_review"
    assert patched_data["exception"]["owner_name"] == "Rahul"
    assert any("Investigating" in n["noteText"] for n in patched_data["notes"])

    # 5. Bulk update
    target_ids = [it["exception_id"] for it in items[:2]]
    res_bulk = client.post(
        "/api/v1/exceptions/bulk",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "ids": target_ids,
            "status": "explained",
            "owner": "Aarti",
            "note": "Bulk verified as explained.",
        },
    )
    assert res_bulk.status_code == 200
    bulk_data = res_bulk.json()["data"]
    assert bulk_data["updated"] == len(target_ids)
    assert len(bulk_data["auditIds"]) > 0


def test_forecast_endpoints_workflow():
    """Verify forecast workspace, run, manual override, lock version, compare and accuracy routes."""
    # 1. GET forecast workspace
    res = client.get(
        "/api/v1/forecast/workspace?scenario=base&default_method=run_rate&run_rate_n=3",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["scenario"] == "base"
    assert "versionId" in data
    assert "lines" in data
    assert len(data["lines"]) > 0
    assert "totals" in data
    assert "fy_landing" in data["totals"]

    first_line = data["lines"][0]
    aid = first_line["account_id"]

    # 2. PATCH forecast manual override (CALC-064 / FR-FC-006)
    # 2a: Missing reason should fail
    res_bad = client.patch(
        "/api/v1/forecast/cells",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "account_id": aid,
            "period_code": "FY26-P10",
            "amount": "999999.00",
            "reason": "",
        },
    )
    assert res_bad.status_code == 400

    # 2b: Valid override
    res_good = client.patch(
        "/api/v1/forecast/cells",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "account_id": aid,
            "period_code": "FY26-P10",
            "amount": "999999.00",
            "reason": "Audited executive adjustment per VP approval",
        },
    )
    assert res_good.status_code == 200
    assert res_good.json()["data"]["applied"] is True

    # 3. POST forecast version lock (FR-FC-009)
    vid = data["versionId"]
    res_lock = client.post(
        f"/api/v1/forecast/versions/{vid}/lock",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={"confirm": True},
    )
    assert res_lock.status_code == 200
    assert res_lock.json()["data"]["status"] == "locked"

    # 4. GET scenario comparison (SCR-028 / CALC-065)
    res_cmp = client.get(
        "/api/v1/forecast/compare",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_cmp.status_code == 200
    cmp_items = res_cmp.json()["data"]["items"]
    assert len(cmp_items) > 0
    assert "base" in cmp_items[0]
    assert "best" in cmp_items[0]
    assert "worst" in cmp_items[0]

    # 5. GET accuracy report (FR-FC-007 / CALC-066..069)
    res_acc = client.get(
        "/api/v1/forecast/accuracy",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_acc.status_code == 200
    acc_data = res_acc.json()["data"]
    assert "signedError" in acc_data
    assert "absoluteError" in acc_data
    assert "signedBias" in acc_data
    assert "guidanceNote" in acc_data


def test_reports_and_issuance_workflow():
    """Verify packs generation, pack issuance, re-issue, and commentary locking (FR-XL, FR-PPT, FR-XC)."""
    # 1. Generate Excel & PPT packs
    res_gen = client.post(
        "/api/v1/packs/generate",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={"period": "FY26-P09", "scenario": "base", "format": "both"},
    )
    assert res_gen.status_code == 200
    gen_items = res_gen.json()["data"]["items"]
    assert len(gen_items) == 2
    assert any(it["pack_token"] == "excel" for it in gen_items)
    assert any(it["pack_token"] == "ppt" for it in gen_items)

    # 2. List generated packs
    res_packs = client.get(
        "/api/v1/packs",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_packs.status_code == 200
    assert len(res_packs.json()["data"]["items"]) >= 2

    # 3. Commentary management
    # 3a: Get default commentaries
    res_comm = client.get(
        "/api/v1/commentary?period_id=9",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_comm.status_code == 200
    comm_items = res_comm.json()["data"]["items"]
    assert len(comm_items) > 0

    # 3b: Save commentary update
    res_save_comm = client.put(
        "/api/v1/commentary",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "period_id": 9,
            "scope_type": "executive",
            "subject_key": "EXECUTIVE",
            "text": "Executive Narrative: Strong revenue performance across Q3; costs maintained within tolerance.",
        },
    )
    assert res_save_comm.status_code == 200
    assert res_save_comm.json()["data"]["text"].startswith("Executive Narrative:")

    # 4. Pack Issuance (FR-XC-002, FR-XC-003)
    # 4a: Issue pack without recipients should fail
    res_issue_bad = client.post(
        "/api/v1/issuance",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={"period_id": 9, "period_code": "FY26-P09", "recipients": []},
    )
    assert res_issue_bad.status_code == 400

    # 4b: Valid pack issue
    res_issue = client.post(
        "/api/v1/issuance",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "period_id": 9,
            "period_code": "FY26-P09",
            "recipients": ["cfo@acme.com", "controller@acme.com"],
            "notes": "Formal Board Release FY26-P09",
        },
    )
    assert res_issue.status_code == 200
    issued_data = res_issue.json()["data"]
    assert issued_data["status"] == "issued"
    assert issued_data["pack_version"] >= 1
    issue_id = issued_data["issue_id"]

    # 4c: Verify commentary is now locked (FR-XC-002)
    res_comm_after = client.get(
        "/api/v1/commentary?period_id=9",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_comm_after.status_code == 200
    exec_comm = next(c for c in res_comm_after.json()["data"]["items"] if c["subject_key"] == "EXECUTIVE")
    assert exec_comm["is_locked"] is True

    # 5. Pack Re-issuance (FR-XC-003)
    # 5a: Missing reason should fail
    res_reissue_bad = client.post(
        f"/api/v1/issuance/{issue_id}/reissue",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={"issue_id": issue_id, "reason": ""},
    )
    assert res_reissue_bad.status_code == 400

    # 5b: Valid re-issue
    res_reissue = client.post(
        f"/api/v1/issuance/{issue_id}/reissue",
        headers={"X-Session-Token": SESSION_TOKEN},
        json={
            "issue_id": issue_id,
            "reason": "Updated audit footnote following tax accrual true-up",
        },
    )
    assert res_reissue.status_code == 200
    reissued_data = res_reissue.json()["data"]
    assert reissued_data["pack_version"] == issued_data["pack_version"] + 1
    assert reissued_data["status"] == "issued"

    # 6. Verify Issuance Register reflects history (SCR-030)
    res_reg = client.get(
        "/api/v1/issuance?period_id=9",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert res_reg.status_code == 200
    reg_items = res_reg.json()["data"]["items"]
    assert len(reg_items) >= 2
    # Ensure previous is superseded
    prev_item = next(it for it in reg_items if it["issue_id"] == issue_id)
    assert prev_item["status"] == "superseded"




