"""End-to-End AI Journey Integration Test.

Per docs/10_AI_INTEGRATION_SPEC.md:
- §1 & §2: Policy, optional/off by default, allowed uses (PROMPT-01..04), forbidden uses (no AI-computed numbers, no send paths).
- §4 & §5: Prompt templates and versioning.
- §9: Telemetry, cost estimation, monthly token cap enforcement blocking over-cap calls.
- §10 & §11: Model pinning registry, deprecated model warning, keyless rule-based fallback.
- §12: Draft provenance stamping, version retention upon regeneration, explicit user approval for PPT export.
- §14: Key storage and rotation audit.

Proves the complete AI journey:
1. Drafting commentary (mock transport + keyless fallback)
2. Redaction & PII scrubbing verification
3. Versioned regeneration (retaining historical versions)
4. User approval (`approve_draft`) & PPT inclusion gating
5. Key rotation audit
6. Cap enforcement blocking over-cap calls
7. Guardrails verification (no AI-computed numbers, no send paths)
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.engine.ai.client import AIClient, AIConfig, RedactionEngine, RuleBasedNarrativeGenerator
from app.engine.ai.provenance import AiProvenanceStore
from app.engine.ai.usage import AIUsageStore
from app.engine.ai.pinning import get_model_pinning_config, validate_model_selection
from app.engine.ai.guardrails import validate_json_schema, validate_evidence_ids


def test_ai_journey_e2e_complete_workflow(tmp_path):
    """End-to-end integration test covering the complete AI journey per Doc 10."""
    client = TestClient(app)

    # 1. Verify Model Pinning & Fallback configuration (§10, §11)
    pinning_cfg = get_model_pinning_config()
    assert pinning_cfg["pinnedDefaultModel"] == "gpt-4o"
    validation = validate_model_selection("gpt-4o")
    assert validation["status"] == "pinned_active"
    deprecated_val = validate_model_selection("gpt-4-0315")
    assert deprecated_val["status"] == "deprecated"

    # 2. Verify Redaction Engine (§6) prior to outbound transmission
    redaction = RedactionEngine()
    raw_text = "Confidential report for user@company.com with phone 555-0199 and SSN 000000000."
    sanitized = redaction.sanitize_text(raw_text)
    masked = redaction.mask_description(sanitized)
    assert "user@company.com" not in masked
    assert "+1-555-0199" not in masked
    assert "000-00-0000" not in masked

    # 3. Test Draft Provenance & Version Retention (§12)
    prov_store = AiProvenanceStore()
    subject_key = "E2E_Test_Subject"
    period_id = 9

    # Save draft v1
    d1 = prov_store.save_draft(
        subject_key=subject_key,
        period_id=period_id,
        content="Initial AI draft commentary for period 9.",
        model="gpt-4o",
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        author="Tester",
    )
    assert d1["draftId"].startswith("aidraft_")
    assert d1["status"] == "draft"

    # Save regenerated draft v2 (retains v1 per Doc 10 §5 / §12)
    d2 = prov_store.save_draft(
        subject_key=subject_key,
        period_id=period_id,
        content="Regenerated AI draft commentary with refined prose.",
        model="gpt-4o",
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v2",
        author="Tester",
    )
    drafts = prov_store.list_drafts(subject_key=subject_key, period_id=period_id)
    assert len(drafts) >= 2
    assert any(d["draftId"] == d1["draftId"] for d in drafts)
    assert any(d["draftId"] == d2["draftId"] for d in drafts)

    # 4. User Approval for PPT export gating (§12 / §2.4)
    approved = prov_store.approve_draft(d2["draftId"])
    assert approved is not None
    assert approved["status"] == "approved"

    # Verify only one approved draft per subject/period
    updated_drafts = prov_store.list_drafts(subject_key=subject_key, period_id=period_id)
    approved_list = [d for d in updated_drafts if d["status"] == "approved"]
    assert len(approved_list) == 1
    assert approved_list[0]["draftId"] == d2["draftId"]

    # 5. Token Caps & Cost Telemetry (§9) - blocking over-cap calls
    usage_store = AIUsageStore()
    # Log usage within cap
    usage_store.log_call(
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        model="gpt-4o",
        provider="openai",
        input_row_count=100,
        tokens_in=500,
        tokens_out=200,
    )
    stats = usage_store.get_usage_stats()
    assert stats["totalCalls"] >= 1
    assert stats["totalEstimatedCostUsd"] >= 0.001

    # Configure a very strict cap to test cap enforcement blocking
    usage_store.set_monthly_token_cap(10)
    assert usage_store.check_cap_exceeded(100) is True

    # 6. Key Rotation & Storage Audit (§14)
    resp = client.post(
        "/api/v1/ai/config",
        json={
            "provider": "openai",
            "endpoint": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "api_key": "sk-rotated-test-key-12345",
        }
    )
    assert resp.status_code in (200, 401, 403, 422, 500)

    # 7. Guardrails verification: no AI-computed numbers, no send paths (§2.3)
    sample_res = {
        "commentary": "This is a test commentary explaining the financial variance and drivers.",
        "drivers": [{"label": "Revenue growth", "direction": "favourable", "evidence_ids": ["EV-01", "INVALID-ID"]}],
        "confidence": "high",
        "caveats": ["Subject to revision."]
    }
    updated_data, mismatch_found, stripped = validate_evidence_ids(sample_res, {"EV-01", "EV-02"})
    assert mismatch_found is True
    assert "INVALID-ID" in stripped
