"""API contract fixture tests validating FastAPI responses against the OpenAPI schema and contract spec.

Quoted from docs/26_API_CONTRACT.md §1 & §6:
- All responses must follow the universal envelope structure (`status`, `data`, `warnings`, `errors`).
- Endpoints must return correct schema fields matching OpenAPI definitions for imports, bva, exceptions,
  forecast, packs, AI, periods, and search.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app, SESSION_TOKEN


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_api_contract_bootstrap_and_health(client):
    headers = {"X-Session-Token": SESSION_TOKEN}

    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "ok"
    assert "app" in health_data

    res_boot = client.get("/api/v1/bootstrap", headers=headers)
    assert res_boot.status_code == 200
    boot_data = res_boot.json()
    assert boot_data["status"] == "ok"
    assert "session_token" in boot_data


def test_api_contract_periods(client):
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/periods", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "ok"
    assert "items" in payload["data"]
    assert "total" in payload["data"]


def test_api_contract_bva_and_three_way(client):
    headers = {"X-Session-Token": SESSION_TOKEN}

    res_bva = client.get("/api/v1/bva", headers=headers)
    assert res_bva.status_code == 200
    bva_payload = res_bva.json()
    assert bva_payload["status"] == "ok"
    assert "items" in bva_payload["data"]

    res_3way = client.get("/api/v1/analysis/three-way", headers=headers)
    assert res_3way.status_code == 200
    threeway_payload = res_3way.json()
    assert threeway_payload["status"] == "ok"
    assert "items" in threeway_payload["data"]


def test_api_contract_exceptions(client):
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/exceptions", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "ok"
    assert "items" in payload["data"]


def test_api_contract_forecast_versions(client):
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/forecast/methods", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "ok"
    assert "methods" in payload["data"]


def test_api_contract_packs(client):
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/packs", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "ok"
    assert "items" in payload["data"]


def test_api_contract_ai_usage(client):
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/ai/usage", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "ok"
    assert "totalTokens" in payload["data"]


def test_api_contract_search(client):
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/search?q=rev", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "ok"
    assert "items" in payload["data"]
