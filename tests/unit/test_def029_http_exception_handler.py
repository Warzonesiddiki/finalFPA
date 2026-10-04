"""Regression test for DEF-029.

DEF-029: In earlier handler layering, stacked StarletteHTTPException handlers or
unhandled exceptions called exc.errors() on standard HTTPException / StarletteHTTPException
(which lacks .errors()), resulting in an AttributeError that transformed clean 404 responses
into unhandled 500 server errors.

This regression test verifies that:
1. StarletteHTTPException and FastAPI HTTPException return clean 404 error envelopes with status 404.
2. No AttributeError (e.g. 'HTTPException' object has no attribute 'errors') is raised.
3. Neither 404 nor 405 degrades into a 500 error.
"""

from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
import pytest

from app.api.main import create_app

client = TestClient(create_app())


def test_def029_404_does_not_become_500():
    """Verify that a non-existent route returns 404 with error envelope, never 500."""
    res = client.get("/api/v1/def029_nonexistent_endpoint")
    assert res.status_code == 404
    data = res.json()
    assert data["status"] == "error"
    assert data["code"] == "ERR-API-404"
    assert "userMessage" in data
    assert "errors" not in data or data.get("errors") is None


def test_def029_method_not_allowed_does_not_become_500():
    """Verify that 405 Method Not Allowed remains 405 and does not raise AttributeError."""
    # /api/v1/health is GET only; sending POST should trigger 405
    res = client.post("/api/v1/health")
    assert res.status_code == 405
    data = res.json()
    assert data["status"] == "error"
    assert data["code"] == "ERR-API-405"
