"""
Unit tests for Stale-Derived Data Indicator API (Addon 2 B.7 / docs 08/09).
Asserts marking stale on config/mapping change and clearing on explicit re-run.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import SESSION_TOKEN, app

client = TestClient(app)
AUTH = {"X-Session-Token": SESSION_TOKEN}


def test_staleness_endpoints_flow():
    # 1. Get staleness status (initially not stale)
    res = client.get("/api/v1/staleness", headers=AUTH)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_stale"] is False

    # 2. Trigger staleness (config/mapping change)
    res2 = client.post("/api/v1/staleness/trigger", headers=AUTH, json={"reason": "Thresholds updated"})
    assert res2.status_code == 200
    assert res2.json()["data"]["is_stale"] is True
    assert res2.json()["data"]["reason"] == "Thresholds updated"

    # 3. Verify get staleness reports stale
    res3 = client.get("/api/v1/staleness", headers=AUTH)
    assert res3.status_code == 200
    assert res3.json()["data"]["is_stale"] is True

    # 4. Explicit re-run clears staleness
    res4 = client.post("/api/v1/staleness/rerun", headers=AUTH)
    assert res4.status_code == 200
    assert res4.json()["status"] == "ok"

    # 5. Verify staleness cleared
    res5 = client.get("/api/v1/staleness", headers=AUTH)
    assert res5.status_code == 200
    assert res5.json()["data"]["is_stale"] is False
    assert res5.json()["data"]["reason"] is None
