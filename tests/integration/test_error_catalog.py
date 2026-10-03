"""Tests for GET /meta/error-catalog endpoint proving completeness vs docs 26/08.

Quoted from docs/26_API_CONTRACT.md §5 & docs/08_UI_UX_SPEC.md §16:
- All error responses MUST adhere to the standardized error envelope containing `code`, `userMessage`, and `hint`.
- `GET /meta/error-catalog` is the runtime projection of the error catalog: `{code, slug, severity, message, hint, httpStatus, ownerDoc}`.
- Error Message Catalog (SCR-041): Every user-facing error must display its error code, clear explanation, and troubleshooting hint.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import app, SESSION_TOKEN


client = TestClient(app)


def test_get_error_catalog_endpoints():
    headers = {"X-Session-Token": SESSION_TOKEN}
    
    # Test /meta/error-catalog
    res = client.get("/meta/error-catalog", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["count"] > 0
    catalog = data["catalog"]
    
    # Test /api/v1/meta/error-catalog
    res_v1 = client.get("/api/v1/meta/error-catalog", headers=headers)
    assert res_v1.status_code == 200
    data_v1 = res_v1.json()
    assert data_v1["status"] == "ok"
    assert data_v1["count"] == len(catalog)

    # Verify required keys in catalog items per docs 26/08
    required_keys = {"code", "family", "httpStatus", "message", "hint", "slug", "severity", "ownerDoc"}
    families_found = set()
    for item in catalog:
        for key in required_keys:
            assert key in item, f"Missing key {key} in error catalog item {item}"
        families_found.add(item["family"])

    # Verify coverage across core families
    expected_families = {"VAL", "BVA", "FC", "RUL", "STO", "AI", "IMP"}
    for fam in expected_families:
        assert fam in families_found, f"Expected error family {fam} missing from catalog"
