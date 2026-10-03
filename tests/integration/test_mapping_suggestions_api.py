"""Mapping review queue API contract tests per 02_FUNCTIONAL_SPEC.md FR-IMP-008.

Exercises the doc 26 endpoint conventions: session-token auth on every route,
consistent {status, data} envelopes, and 4xx on illegal state transitions rather
than a silent rewrite.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app.engine.store.db as db_mod
from app.api.main import SESSION_TOKEN, app

client = TestClient(app)
AUTH = {"X-Session-Token": SESSION_TOKEN}


@pytest.fixture(autouse=True)
def isolated_project(tmp_path, monkeypatch):
    """Give each test a fresh project database.

    The API constructs `DatabaseManager()` with no argument, and suggestions are
    deduped on (import_run_id, source_column) with decided states terminal, so a
    shared database makes these state-machine assertions depend on test execution
    order and on any earlier run.

    Patching `LOCALAPPDATA` (not the `DEFAULT_PROJECT_DIR` module attribute):
    `DatabaseManager.__init__` no longer reads `DEFAULT_PROJECT_DIR` at all - it
    resolves the project directory from `os.environ["LOCALAPPDATA"]` inline, and
    additionally prefers `<cwd>/data/default` when a `portable.flag` is present.
    Patching the environment variable therefore covers both branches. Patching the
    module attribute silently does nothing, which is what made these tests pass in
    isolation and fail in a full run.
    """
    project_dir = tmp_path / "Projects" / "default"
    monkeypatch.setenv("FPA_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(db_mod, "DEFAULT_PROJECT_DIR", project_dir)
    return tmp_path


def _enqueue(run_id: int = 9001, ai_enabled: bool = True) -> dict:
    return client.post(
        "/api/v1/mapping-suggestions",
        headers=AUTH,
        json={
            "importRunId": run_id,
            "aiEnabled": ai_enabled,
            "suggestions": [
                {
                    "sourceColumn": "Gross Amount",
                    "targetField": "amount",
                    "confidence": "0.91",
                    "origin": "rule",
                    "evidence": [{"source": "Gross Amount", "value": "1234.00"}],
                },
                {
                    "sourceColumn": "AI Guess",
                    "targetField": "debit",
                    "confidence": "0.77",
                    "origin": "ai",
                },
                {
                    "sourceColumn": "Hallucinated",
                    "targetField": "not_a_real_field",
                    "confidence": "0.99",
                    "origin": "ai",
                },
            ],
        },
    )


def test_enqueue_requires_session_token():
    response = client.post(
        "/api/v1/mapping-suggestions",
        json={"importRunId": 1, "aiEnabled": False, "suggestions": []},
    )
    assert response.status_code == 401


def test_enqueue_returns_queue_and_summary():
    response = _enqueue()
    assert response.status_code == 200
    data = response.json()["data"]
    # The non-canonical target is dropped per FR-IMP-008 / FR-AI-006.
    assert {i["source_column"] for i in data["items"]} == {"Gross Amount", "AI Guess"}
    assert data["summary"].get("suggested") == 2
    assert data["importRunId"] == 9001


def test_enqueue_with_ai_disabled_drops_ai_proposals():
    """FR-IMP-008: "With AI disabled, the queue shows rule-based suggestions only"."""
    response = _enqueue(run_id=9002, ai_enabled=False)
    data = response.json()["data"]
    assert {i["source_column"] for i in data["items"]} == {"Gross Amount"}


def test_list_endpoint_filters():
    _enqueue(run_id=9003)
    response = client.get(
        "/api/v1/mapping-suggestions?importRunId=9003&origin=ai", headers=AUTH
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert [i["source_column"] for i in data["items"]] == ["AI Guess"]


def test_decision_accept_transitions_and_returns_audit():
    item = _enqueue(run_id=9010).json()["data"]["items"][0]
    sid = item["suggestion_id"]

    response = client.post(
        f"/api/v1/mapping-suggestions/{sid}/decision",
        headers=AUTH,
        json={"action": "accept", "actor": "Aarti"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["item"]["state"] == "accepted"
    assert data["item"]["resolved_target_field"] == data["item"]["suggested_target_field"]
    assert len(data["audit"]) == 1


def test_decision_edit_keeps_original_proposal():
    item = _enqueue(run_id=9011).json()["data"]["items"][0]
    sid = item["suggestion_id"]
    response = client.post(
        f"/api/v1/mapping-suggestions/{sid}/decision",
        headers=AUTH,
        json={"action": "edit", "actor": "Aarti", "newTargetField": "debit"},
    )
    assert response.status_code == 200
    item_out = response.json()["data"]["item"]
    assert item_out["state"] == "edited"
    assert item_out["resolved_target_field"] == "debit"
    assert item_out["suggested_target_field"] == "amount"


def test_edit_to_non_canonical_field_is_rejected():
    item = _enqueue(run_id=9012).json()["data"]["items"][0]
    sid = item["suggestion_id"]
    response = client.post(
        f"/api/v1/mapping-suggestions/{sid}/decision",
        headers=AUTH,
        json={"action": "edit", "actor": "Aarti", "newTargetField": "not_a_real_field"},
    )
    assert response.status_code == 422


def test_deciding_a_decided_suggestion_returns_409():
    """The audit trail must not be rewritable after the fact."""
    item = _enqueue(run_id=9013).json()["data"]["items"][0]
    sid = item["suggestion_id"]
    first = client.post(
        f"/api/v1/mapping-suggestions/{sid}/decision",
        headers=AUTH,
        json={"action": "accept", "actor": "Aarti"},
    )
    assert first.status_code == 200
    second = client.post(
        f"/api/v1/mapping-suggestions/{sid}/decision",
        headers=AUTH,
        json={"action": "reject", "actor": "Someone"},
    )
    assert second.status_code == 409


def test_decision_on_unknown_suggestion_returns_404():
    response = client.post(
        "/api/v1/mapping-suggestions/999999/decision",
        headers=AUTH,
        json={"action": "accept", "actor": "Aarti"},
    )
    assert response.status_code == 404


def test_bulk_decision_endpoint():
    items = _enqueue(run_id=9020).json()["data"]["items"]
    ids = [i["suggestion_id"] for i in items]
    response = client.post(
        "/api/v1/mapping-suggestions/bulk-decision",
        headers=AUTH,
        json={"ids": ids, "action": "accept", "actor": "Aarti"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["applied"] == ids
    assert data["skipped"] == []


def test_bulk_edit_endpoint_applies_per_item_targets():
    items = _enqueue(run_id=9021).json()["data"]["items"]
    first_id, second_id = [i["suggestion_id"] for i in items]
    response = client.post(
        "/api/v1/mapping-suggestions/bulk-decision",
        headers=AUTH,
        json={
            "ids": [first_id, second_id],
            "action": "edit",
            "actor": "Aarti",
            "newTargets": {str(first_id): "debit", str(second_id): "credit"},
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["applied"] == [first_id, second_id]

    audit = client.get(f"/api/v1/mapping-suggestions/{first_id}/audit", headers=AUTH)
    assert audit.status_code == 200
    entries = audit.json()["data"]["audit"]
    assert entries[-1]["to_state"] == "edited"


def test_audit_endpoint_requires_session_token():
    response = client.get("/api/v1/mapping-suggestions/1/audit")
    assert response.status_code == 401


def test_duplicate_column_enqueued_twice_stays_one_row():
    """FR-IMP-008 dedup across repeated enqueues of the same run."""
    first = _enqueue(run_id=9030).json()["data"]
    second = _enqueue(run_id=9030).json()["data"]
    assert len(first["items"]) == len(second["items"])
    listing = client.get("/api/v1/mapping-suggestions?importRunId=9030", headers=AUTH)
    assert listing.json()["data"]["total"] == len(first["items"])