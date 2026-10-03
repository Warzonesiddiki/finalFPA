"""Tests for central error envelope handler validating 401/404/500 error responses.

Quoted from docs/26_API_CONTRACT.md §5 & docs/08_UI_UX_SPEC.md §16:
- All error responses MUST adhere to the standardized error envelope containing `code`, `userMessage`, and `hint`.
- Under no circumstances shall unhandled exceptions, raw stack traces, or debug HTML reach the client; unexpected server errors must return status 500 formatted with `ERR-API-500`, a clean user message, and a troubleshooting hint.
"""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from app.api.main import app, SESSION_TOKEN


client = TestClient(app, raise_server_exceptions=False)


def test_error_envelope_401_unauthorized():
    res = client.post(
        "/api/v1/calc/variance-demo",
        json={"actual": "1250000.50", "budget": "1000000.00"},
    )
    assert res.status_code == 401
    data = res.json()
    assert data["status"] == "error"
    assert "ERR-API-401" in data["code"]
    assert "userMessage" in data
    assert "hint" in data
    assert "error" in data
    assert data["error"]["code"] == data["code"]


def test_error_envelope_404_route_not_found():
    res = client.get("/api/v1/nonexistent-route-99999")
    assert res.status_code == 404
    data = res.json()
    assert data["status"] == "error"
    assert data["code"] == "ERR-API-404"
    assert data["userMessage"] == "The requested resource could not be found."
    assert "hint" in data
    assert data["error"]["code"] == "ERR-API-404"
    assert data["error"]["userMessage"] == "The requested resource could not be found."


def test_crash_endpoint_gated_by_default():
    # Without FPA_TEST_MODE=1, the test crash endpoint must return 404
    os.environ.pop("FPA_TEST_MODE", None)
    headers = {"X-Session-Token": SESSION_TOKEN}
    res = client.get("/api/v1/_test_crash", headers=headers)
    assert res.status_code == 404


def test_unhandled_exception_returns_500_envelope():
    os.environ["FPA_TEST_MODE"] = "1"
    try:
        headers = {"X-Session-Token": SESSION_TOKEN}
        res = client.get("/api/v1/_test_crash", headers=headers)
        assert res.status_code == 500
        data = res.json()
        assert data["status"] == "error"
        assert data["code"] == "ERR-API-500"
        assert "userMessage" in data
        assert "hint" in data
        assert "error" in data
        assert data["error"]["code"] == "ERR-API-500"
        # Ensure no raw traceback or HTML leaked
        raw_text = res.text
        assert "Traceback" not in raw_text
        assert "<html>" not in raw_text
    finally:
        os.environ.pop("FPA_TEST_MODE", None)
