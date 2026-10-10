"""Contract drift check script per doc 26.

Quoted from docs/26_API_CONTRACT.md §6.2:
- Hand-duplicated types are forbidden; drift between FastAPI routes and TypeScript types constitutes a build error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.openapi.utils import get_openapi

from app.api.main import app


def check_contract_drift() -> None:
    """Verify OpenAPI schema is up to date with FastAPI routes."""
    openapi_schema = get_openapi(
        title="FP&A Month-End Copilot API",
        version="1.0.0",
        description="Headless analytical and operational API for FP&A Month-End Copilot",
        routes=app.routes,
    )
    schema_path = Path("app/api/openapi.json")
    if not schema_path.exists():
        raise RuntimeError(
            "OpenAPI schema file app/api/openapi.json does not exist. Run python -m app.api.openapi first."
        )

    existing_schema = json.loads(schema_path.read_text(encoding="utf-8"))

    new_str = json.dumps(openapi_schema, sort_keys=True)
    existing_str = json.dumps(existing_schema, sort_keys=True)

    if new_str != existing_str:
        raise RuntimeError(
            "ERROR: OpenAPI schema drift detected! Routes have changed without updating app/api/openapi.json. Per doc 26, contract drift is a build error."
        )
    else:
        print("OpenAPI contract drift check PASSED: No schema drift detected.")


if __name__ == "__main__":
    check_contract_drift()
