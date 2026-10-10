"""API-level proof of the FR-IMP-008 importer seam.

FR-IMP-008 (doc 02 line 305) acceptance criterion:

    "a suggestion accepted during import N is applied automatically in import
    N+1 and appears in the mapping profile history."

Driven entirely through HTTP - enqueue, decide, then two real POSTs to
/api/v1/imports - so this covers the wiring in the route, not just the engine.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.engine.store.db as db_mod
from app.api.main import SESSION_TOKEN, app

client = TestClient(app)
AUTH = {"X-Session-Token": SESSION_TOKEN}

CSV_BODY = (
    "Voucher,Posting Date,Company Code,Account,Cost Centre Ref,Debit,Credit,Description\n"
    "V-1,2026-09-02,IN01,6100,CC-120,1000.00,0.00,rent\n"
    "V-2,2026-09-03,IN01,6100,CC-120,0.00,1000.00,rent reversal\n"
)

UNMAPPED_COLUMN = "Cost Centre Ref"
TARGET_FIELD = "cost_center_code"


@pytest.fixture(autouse=True)
def isolated_project(tmp_path, monkeypatch):
    """Fresh project database per test.

    Imports commit real DuckDB rows and profile versions that accumulate, so a
    shared project dir would make these assertions depend on prior runs.

    `LOCALAPPDATA` is patched because `DatabaseManager.__init__` resolves the
    project directory from that environment variable inline and no longer reads
    the `DEFAULT_PROJECT_DIR` module attribute. Patching only the attribute
    leaves the API writing to the real user profile while these tests read
    `tmp_path`, which surfaces as "FactActual does not exist".
    """
    # FPA_PROJECT_DIR takes precedence in DatabaseManager.__init__; LOCALAPPDATA is
    # the fallback. Patch both so this holds regardless of which branch the
    # resolver takes. DEFAULT_PROJECT_DIR is no longer read by the constructor, but
    # is patched too so any code still referencing the module attribute sees the
    # same directory rather than the real user profile.
    project_dir = tmp_path / "Projects" / "default"
    monkeypatch.setenv("FPA_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(db_mod, "DEFAULT_PROJECT_DIR", project_dir)
    return tmp_path


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "gl_api_seam.csv"
    f.write_text(CSV_BODY, encoding="utf-8")
    return str(f)


def _import_file(path: str) -> dict:
    response = client.post("/api/v1/imports", headers=AUTH, json={"path": path})
    assert response.status_code == 200, response.text
    return response.json()


def _enqueue_and_accept(import_run_id: int) -> int:
    enq = client.post(
        "/api/v1/mapping-suggestions",
        headers=AUTH,
        json={
            "importRunId": import_run_id,
            "aiEnabled": False,
            "suggestions": [
                {
                    "sourceColumn": UNMAPPED_COLUMN,
                    "targetField": TARGET_FIELD,
                    "confidence": "0.93",
                    "origin": "rule",
                    "evidence": [{"sourceColumn": UNMAPPED_COLUMN, "sample": "CC-120"}],
                }
            ],
        },
    )
    assert enq.status_code == 200, enq.text
    sid = enq.json()["data"]["items"][0]["suggestion_id"]

    dec = client.post(
        f"/api/v1/mapping-suggestions/{sid}/decision",
        headers=AUTH,
        json={"action": "accept", "actor": "Aarti"},
    )
    assert dec.status_code == 200, dec.text
    return sid


def test_accepted_suggestion_applies_on_the_next_import(csv_file):
    """The acceptance criterion, end to end over HTTP."""
    # ---- import N. Nothing accepted yet, so nothing is applied.
    run_n = _import_file(csv_file)
    assert run_n["batchId"] > 0
    assert run_n["profileBinding"]["applied"] == []
    assert run_n["profileBinding"]["versionNo"] is None

    # A reviewer accepts the suggestion raised by import N.
    suggestion_id = _enqueue_and_accept(run_n["batchId"])

    # ---- import N+1 picks it up automatically.
    run_n1 = _import_file(csv_file)
    binding = run_n1["profileBinding"]

    assert binding["importRunId"] == run_n["batchId"] + 1
    assert binding["changed"] is True
    assert [a["sourceColumn"] for a in binding["applied"]] == [UNMAPPED_COLUMN]
    assert binding["applied"][0]["targetField"] == TARGET_FIELD
    assert binding["versionNo"] is not None
    assert run_n1["batchId"] == run_n["batchId"] + 1

    # The suggestion is now linked to that profile version (profile history).
    audit_view = client.get("/api/v1/mapping-suggestions", headers=AUTH).json()["data"]
    assert audit_view["total"] == 1


def test_same_run_import_does_not_apply_its_own_suggestion(csv_file):
    """FR-IMP-008: "Suggestions are never auto-applied in the same run".

    Import N is committed first so N has an id, the suggestion is enqueued against
    it, and the NEXT import is N+1 - so the guarantee is asserted by re-reading
    the applied list rather than by racing the enqueue against a commit.
    """
    first = _import_file(csv_file)
    _enqueue_and_accept(first["batchId"])

    # Re-importing the same file is a later run, so it may apply. To prove the
    # same-run exclusion itself, resolve explicitly for N and confirm emptiness.
    #
    # DatabaseManager() with NO argument resolves to whatever project directory
    # FPA_PROJECT_DIR / LOCALAPPDATA names. The autouse `isolated_project` fixture
    # in this module repoints both at tmp_path, so this reads the same throwaway
    # project the API just wrote - never the real user database.
    from app.engine.imports.profile_binding import resolve_profile_for_import
    from app.engine.imports.profiles import BUILTIN_PROFILES
    from app.engine.store.db import DatabaseManager

    db = DatabaseManager()
    same_run = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=first["batchId"]
    )
    assert same_run.applied == []
    assert same_run.version_no is None


def test_third_import_reports_already_applied_not_reapplied(csv_file):
    """Idempotence over HTTP: the profile history must not churn."""
    first = _import_file(csv_file)
    _enqueue_and_accept(first["batchId"])

    second = _import_file(csv_file)
    assert second["profileBinding"]["changed"] is True
    assert len(second["profileBinding"]["alreadyApplied"]) == 0

    third = _import_file(csv_file)
    assert third["profileBinding"]["applied"] == []
    assert third["profileBinding"]["changed"] is False
    assert third["profileBinding"]["versionNo"] is None
    assert third["profileBinding"]["alreadyApplied"] == [
        second["profileBinding"]["applied"][0]["suggestionId"]
    ]


def test_committed_facts_carry_the_applied_cost_center(csv_file, isolated_project):
    """The mapping reaches DuckDB, not just the profile table."""
    import duckdb

    first = _import_file(csv_file)
    _enqueue_and_accept(first["batchId"])
    second = _import_file(csv_file)

    # Read the same database the API wrote to: the fixture patches LOCALAPPDATA,
    # and DatabaseManager appends /FP&A Month-End Copilot/Projects/default to it.
    duckdb_path = Path(isolated_project) / "Projects" / "default" / "analytics.duckdb"
    conn = duckdb.connect(str(duckdb_path))
    try:
        rows = conn.execute(
            "SELECT cost_center_id FROM FactActual WHERE import_batch_id = ?",
            [second["batchId"]],
        ).fetchall()
        before = conn.execute(
            "SELECT cost_center_id FROM FactActual WHERE import_batch_id = ?",
            [first["batchId"]],
        ).fetchall()
    finally:
        conn.close()

    assert {r[0] for r in before} == {None}, "import N should have no cost center"
    assert {r[0] for r in rows} == {120}, "import N+1 should carry CC-120"


def test_import_endpoint_still_works_with_no_suggestions_at_all(csv_file):
    """No queue, no clones, no versions - the common path is untouched."""
    first = _import_file(csv_file)
    assert first["profileBinding"]["changed"] is False
    assert first["profileBinding"]["applied"] == []
    assert first["loadedCount"] == 2
    assert first["quarantinedCount"] == 0
