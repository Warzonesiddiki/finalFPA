"""OpenAPI schema generator and TypeScript contract export per doc 26.

Quoted from docs/26_API_CONTRACT.md §6.1 & §6.2:
- OpenAPI document: `app/api/openapi.json` generated via Python script.
- TypeScript types: `ui/src/api/types.ts` generated from OpenAPI schema.
- Drift detection: build error if schema or types drift from FastAPI app.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.openapi.utils import get_openapi

from app.api.main import app


def generate_openapi_json(output_path: Path) -> dict:
    """Generate OpenAPI schema dictionary from FastAPI app."""
    openapi_schema = get_openapi(
        title="FP&A Month-End Copilot API",
        version="1.0.0",
        description="Headless analytical and operational API for FP&A Month-End Copilot",
        routes=app.routes,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(openapi_schema, indent=2), encoding="utf-8")
    return openapi_schema


if __name__ == "__main__":
    out_json = Path("app/api/openapi.json")
    generate_openapi_json(out_json)
    print(f"Generated OpenAPI schema at {out_json}")
