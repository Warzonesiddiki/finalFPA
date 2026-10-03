"""Integration tests for Phase 1 Ingestion and Batch API routes per 26_API_CONTRACT.md §3.2."""

from pathlib import Path
from fastapi.testclient import TestClient
from app.api.main import app, SESSION_TOKEN

client = TestClient(app)


def test_api_prescan_valid_file():
    sample_file = Path("sample-data/bank_ledger_actuals.csv")
    if sample_file.exists():
        response = client.post(
            "/api/v1/imports/pre-scan",
            headers={"X-Session-Token": SESSION_TOKEN},
            json={"path": str(sample_file.resolve())},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fileName"] == "bank_ledger_actuals.csv"
        assert data["estimatedRows"] > 0
        assert "BankAccountId" in data["sampleHeaders"]


def test_api_import_valid_file():
    sample_file = Path("sample-data/bank_ledger_actuals.csv")
    if sample_file.exists():
        response = client.post(
            "/api/v1/imports",
            headers={"X-Session-Token": SESSION_TOKEN},
            json={"path": str(sample_file.resolve())},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["batchId"] > 0
        assert data["loadedCount"] > 0
        assert data["quarantinedCount"] == 0


def test_api_list_imports():
    response = client.get(
        "/api/v1/imports",
        headers={"X-Session-Token": SESSION_TOKEN},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "items" in data["data"]
