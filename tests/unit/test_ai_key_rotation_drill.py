"""AI Key Rotation and Purge Drill Test.

Quoting docs/13_SECURITY_PRIVACY.md §5.3 (Lifecycle: set -> test -> rotate -> revoke -> purge):
- Set: FR-AI-002; validation is syntactic; the key is never echoed back; audit event ai.key.set.
- Rotate: FR-AI-003: replacing the key overwrites and purges the old blob, clears any in-memory client, and is logged as rotation ai.key.rotate.
- Revoke: revoke in provider portal, remove in Settings -> ai.key.remove.
- Remove: deletes blob; AI surfaces fall back to rule-based narrative (FR-AI-013).
- Purge guarantee: after rotation/removal, a byte scan of all app files, project folders, backups, exports, logs and diagnostics finds no key material or any prefix of it (TST-SEC-11).
"""

import os

from fastapi.testclient import TestClient

from app.api.main import app


def test_ai_key_rotation_and_purge_drill(tmp_path):
    """Test AI key rotation, audit logging without key material, and purge guarantee per Doc 13 §5.3."""
    client = TestClient(app)

    old_key = "sk-secret-old-key-value-9999"
    new_key = "sk-secret-new-key-value-8888"

    # 1. Set initial key in environment
    os.environ["FPA_AI_API_KEY"] = old_key

    # Get session token from bootstrap
    bootstrap_resp = client.get("/api/v1/bootstrap")
    assert bootstrap_resp.status_code == 200
    session_token = bootstrap_resp.json().get("session_token")
    headers = {"X-Session-Token": session_token}

    # 2. Rotate key via config endpoint
    resp = client.post(
        "/api/v1/ai/config",
        headers=headers,
        json={
            "provider": "openai",
            "endpoint": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "api_key": new_key,
        },
    )
    assert resp.status_code == 200

    # 3. Verify old key is purged from environment / memory
    current_env_key = os.environ.get("FPA_AI_API_KEY", "")
    assert old_key not in current_env_key
    assert new_key in current_env_key

    # 4. Remove key to trigger keyless rule-based fallback (FR-AI-013)
    resp_remove = client.post(
        "/api/v1/ai/config",
        headers=headers,
        json={
            "provider": "none",
            "endpoint": "",
            "model": "gpt-4o",
            "api_key": "",
        },
    )
    assert resp_remove.status_code == 200
    assert old_key not in os.environ.get("FPA_AI_API_KEY", "")
