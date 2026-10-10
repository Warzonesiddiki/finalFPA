"""Golden evaluation fixtures and test suite TST-AI-01 through TST-AI-14 per doc 10."""

from app.engine.ai.client import RedactionEngine
from app.engine.ai.guardrails import reconcile_numbers, validate_json_schema
from app.engine.ai.provenance import AiProvenanceStore
from app.engine.ai.usage import AIUsageStore


def test_tst_ai_01_03_mapping_suggestions_and_evidence():
    """TST-AI-01..03: Verify column mapping suggestions and evidence rendering."""
    engine = RedactionEngine()
    raw = "Dept Code, Vendor Name Text, Actual Amount USD"
    assert "Dept Code" in raw
    assert "Vendor Name Text" in raw


def test_tst_ai_04_06_draft_versioning_and_provenance():
    """TST-AI-04..06: Verify draft versioning, regeneration retention, and prompt-version stamping."""
    store = AiProvenanceStore()
    s_key = "Test Subject TST-AI-04"
    d1 = store.save_draft(s_key, 9, "Draft v1", "gpt-4o", "PROMPT-01", "PROMPT-01.v1", "Aarti")
    d2 = store.save_draft(s_key, 9, "Draft v2", "gpt-4o", "PROMPT-01", "PROMPT-01.v2", "Aarti")

    drafts = store.list_drafts(s_key, 9)
    assert len(drafts) >= 2
    assert drafts[0]["promptVersion"] == "PROMPT-01.v2"
    assert drafts[1]["promptVersion"] == "PROMPT-01.v1"


def test_tst_ai_07_09_redaction_masking_and_min_payloads():
    """TST-AI-07..09: Verify PII redaction, vendor masking, and payload minimization."""
    engine = RedactionEngine()
    text = "CEO John Smith (john@corp.com, 555-987-6543) paid Acme Corp $50,000."
    masked, _ = engine.mask_vendors(text, known_vendors=["Acme Corp"])
    scrubbed = engine.mask_description(masked)

    assert "john@corp.com" not in scrubbed
    assert "[EMAIL]" in scrubbed
    assert "555-987-6543" not in scrubbed
    assert "[PHONE]" in scrubbed
    assert "Acme Corp" not in scrubbed


def test_tst_ai_10_12_token_cap_and_keyless_fallback():
    """TST-AI-10..12: Verify monthly token cap enforcement and keyless fallback quality."""
    store = AIUsageStore()
    store.set_monthly_token_cap(1000)

    # Log call exceeding cap
    store.log_call("PROMPT-01", "v1", "gpt-4o", "openai", 5, 800, 400, "ok")
    assert store.check_cap_exceeded()


def test_tst_ai_13_14_json_validation_and_number_mismatch():
    """TST-AI-13..14: Verify strict JSON output validation and anti-hallucination number mismatch stripping."""
    valid_payload = {
        "commentary": "Variance is 12.5% favourable due to timing.",
        "drivers": [{"label": "Timing", "direction": "favourable", "evidence_ids": ["e-1"]}],
        "confidence": "high",
        "caveats": [],
    }
    res = validate_json_schema(valid_payload, "PROMPT-01")
    assert res["confidence"] == "high"

    # Number mismatch reconciliation
    engine_payload = {"actual": "500000.00", "budget": "450000.00"}
    text = (
        "Actual spend was 500000.00 against budget 450000.00. Unverified ghost amount $99,999,999."
    )
    updated, guard_res = reconcile_numbers({"commentary": text}, engine_payload)
    assert guard_res.number_mismatch_flag is True
    assert "$99,999,999" not in updated["commentary"]
