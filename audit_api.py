from __future__ import annotations
import re
from pathlib import Path
from fastapi.routing import APIRoute
from app.api.main import create_app

def normalize_path(p: str) -> str:
    # Remove /api/v1 prefix if present
    if p.startswith("/api/v1"):
        p = p[7:]
    if not p.startswith("/"):
        p = "/" + p
    # Normalize parameter names: {batch_id}, {exception_id}, {version_id}, etc. -> {id} or generic
    # Or just replace {foo} with {id} for comparison
    p_norm = re.sub(r'\{[^}]+\}', '{id}', p)
    return p_norm

def audit():
    app = create_app()
    registered = set()
    for r in app.routes:
        if isinstance(r, APIRoute):
            for m in r.methods:
                if m != "HEAD":
                    norm_path = normalize_path(r.path)
                    registered.add((m.upper(), norm_path))

    doc_path = Path("docs/26_API_CONTRACT.md")
    content = doc_path.read_text(encoding="utf-8")

    pattern = re.compile(r'\|\s*(`(?:GET|POST|PUT|DELETE|PATCH)\s+/[^`]+`)')
    matches = pattern.findall(content)
    
    claimed = set()
    for m in matches:
        parts = m.strip('`').split(' ', 1)
        if len(parts) == 2:
            method, path = parts
            # Clean up query params if any in path
            path = path.split('?')[0]
            norm_path = normalize_path(path)
            claimed.add((method.upper(), norm_path))

    print(f"Total claimed in doc 26 tables (normalized): {len(claimed)}")
    print(f"Total registered in FastAPI app (normalized): {len(registered)}")

    missing_in_app = claimed - registered
    extra_in_app = registered - claimed

    print("\n--- Missing in App (Claimed in Doc 26 but not registered) ---")
    for m, p in sorted(missing_in_app):
        print(f"  {m} {p}")

    print("\n--- Extra in App (Registered in FastAPI but not in Doc 26 table) ---")
    for m, p in sorted(extra_in_app):
        print(f"  {m} {p}")

if __name__ == "__main__":
    audit()
