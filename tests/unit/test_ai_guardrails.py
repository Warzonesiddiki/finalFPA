"""Unit tests for AI Output Validation, Guardrails, Provenance Tracking, and Capping.

Tests per docs/10_AI_INTEGRATION_SPEC.md §8, §9, §10, and §12.
"""

from decimal import Decimal
import json
import pytest
from app.engine.ai.guardrails import (
    validate_json_schema,
    sanitize_fields,
    check_banned_phrases,
    validate_evidence_ids,
    normalize_number_token,
    extract_payload_numbers,
    check_sentence_numbers,
    reconcile_text_numbers,
    reconcile_numbers,
    AIDraftProvenance,
    stamp_ai_draft,
    AICapConfig,
    AIUsageTracker,
    FactAIUsage,
    CapCheckResult,
    ModelPinningManager,
    AIGuardrailPipeline,
    AISchemaValidationError,
    CapExceededException,
    AI_DRAFT_STAMP,
    NUMBER_REMOVED_PLACEHOLDER,
    NUMBER_MISMATCH_WARNING,
    PROMPT_01_OUTPUT_SCHEMA,
    PROMPT_02_OUTPUT_SCHEMA,
    PROMPT_03_OUTPUT_SCHEMA,
    PROMPT_04_OUTPUT_SCHEMA,
)


# ---------------------------------------------------------------------------
# 1. JSON Schema Validation Tests (§8.1, §8.3)
# ---------------------------------------------------------------------------

def test_prompt_01_schema_validation_valid():
    valid_p1 = {
        "commentary": "Repairs and maintenance is 5.4% above budget for Sep-26, driven mainly by repairs.",
        "drivers": [
            {
                "label": "Single repair posting (V-00931)",
                "direction": "unfavourable",
                "evidence_ids": ["c-1"],
            }
        ],
        "confidence": "medium",
        "caveats": ["Contributor detail is based on 4 transaction rows."],
    }
    result = validate_json_schema(valid_p1, "PROMPT-01")
    assert result["commentary"] == valid_p1["commentary"]
    assert len(result["drivers"]) == 1


def test_prompt_01_schema_validation_markdown_fence():
    valid_p1_str = """```json
    {
      "commentary": "Repairs and maintenance is 5.4% above budget for Sep-26, driven mainly by repairs.",
      "drivers": [
        {
          "label": "Single repair posting",
          "direction": "unfavourable",
          "evidence_ids": ["c-1"]
        }
      ],
      "confidence": "high",
      "caveats": []
    }
    ```"""
    result = validate_json_schema(valid_p1_str, "PROMPT-01")
    assert result["confidence"] == "high"


def test_schema_validation_malformed_json():
    with pytest.raises(AISchemaValidationError, match="Invalid JSON response"):
        validate_json_schema("{ commentary: missing quotes, ", "PROMPT-01")


def test_schema_validation_missing_required_field():
    incomplete = {
        "commentary": "Repairs and maintenance is 5.4% above budget for Sep-26, driven mainly by repairs.",
        # Missing drivers, confidence, caveats
    }
    with pytest.raises(AISchemaValidationError, match="Schema validation failed"):
        validate_json_schema(incomplete, "PROMPT-01")


def test_schema_validation_forbidden_additional_property():
    extra_prop = {
        "commentary": "Repairs and maintenance is 5.4% above budget for Sep-26, driven mainly by repairs.",
        "drivers": [],
        "confidence": "low",
        "caveats": [],
        "unauthorized_field": "injected content",
    }
    with pytest.raises(AISchemaValidationError, match="unauthorized_field"):
        validate_json_schema(extra_prop, "PROMPT-01")


def test_prompt_02_mapping_schema():
    p2_data = {
        "suggestions": [
            {
                "source_column": "Fiscal period",
                "target_field": "period_code",
                "confidence": "high",
                "reason": "Matches period format",
                "evidence_ids": ["ev-1"],
            }
        ]
    }
    result = validate_json_schema(p2_data, "PROMPT-02")
    assert len(result["suggestions"]) == 1


def test_prompt_03_exception_summary_schema():
    p3_data = {
        "summary": "2 potential exceptions are open for Sep-26, both high severity. Timing issues predominate.",
        "groups": [
            {
                "theme": "Duplicates",
                "count": 1,
                "severity_max": "high",
                "exception_ids": ["ex-1"],
                "note": "Two postings of same invoice",
            }
        ],
        "review_order": ["ex-1"],
        "confidence": "high",
    }
    result = validate_json_schema(p3_data, "PROMPT-03")
    assert result["groups"][0]["theme"] == "Duplicates"


def test_prompt_04_message_draft_schema():
    p4_data = {
        "subject_line": "Sep-26 close: 3 items for review in your area",
        "body_markdown": "Hi Rahul,\n\nAhead of the Sep-26 close review, could you check these items?\n\nThanks,",
        "items_referenced": ["ex-1"],
        "confidence": "high",
    }
    result = validate_json_schema(p4_data, "PROMPT-04")
    assert result["subject_line"].startswith("Sep-26")


# ---------------------------------------------------------------------------
# 2. Sanitation, Evidence ID & Banned Words (§8.1)
# ---------------------------------------------------------------------------

def test_sanitize_fields_strips_newlines():
    data = {"commentary": "Line 1.\n\nLine 2.\r\nLine 3."}
    cleaned = sanitize_fields("PROMPT-01", data)
    assert "\n" not in cleaned["commentary"]
    assert "\r" not in cleaned["commentary"]
    assert cleaned["commentary"] == "Line 1. Line 2. Line 3."


def test_check_banned_phrases():
    text = "The entry is completely wrong and represents fraud by the vendor."
    found = check_banned_phrases(text)
    assert "wrong" in found
    assert "fraud" in found

    clean_text = "This variance appears to be a timing difference worth reviewing."
    assert check_banned_phrases(clean_text) == []


def test_validate_evidence_ids_strips_unknown():
    data = {
        "drivers": [
            {"label": "Repairs", "direction": "unfavourable", "evidence_ids": ["c-1", "unknown-99"]}
        ]
    }
    cleaned, mismatch, stripped = validate_evidence_ids(data, allowed_evidence_ids=["c-1", "c-2"])
    assert mismatch is True
    assert stripped == ["unknown-99"]
    assert cleaned["drivers"][0]["evidence_ids"] == ["c-1"]


def test_validate_evidence_ids_suggestions_downgrades_confidence():
    data = {
        "suggestions": [
            {
                "source_column": "ColA",
                "target_field": "amount",
                "confidence": "high",
                "reason": "looks like amount",
                "evidence_ids": ["ev-999"],
            }
        ]
    }
    cleaned, mismatch, stripped = validate_evidence_ids(data, allowed_evidence_ids=["ev-1"])
    assert mismatch is True
    assert cleaned["suggestions"][0]["confidence"] == "low"
    assert cleaned["suggestions"][0]["evidence_ids"] == []


# ---------------------------------------------------------------------------
# 3. Anti-Hallucination Number Reconciliation (§8.2 - DEC-026)
# ---------------------------------------------------------------------------

def test_extract_payload_numbers_and_normalization():
    payload = {
        "actual": "1,05,40,000.00",
        "variance_pct": "+5.4%",
        "currency": "INR",
        "contributors": [
            {"id": "c-1", "amount": 450000.0, "rows": 1},
            {"id": "c-2", "amount": "₹1,80,000", "rows": 3},
        ],
        "prior_months": [
            {"month": "Jul-26", "value": "1298591.00"},
            {"month": "Aug-26", "value": "745367.00"},
        ],
    }
    numbers = extract_payload_numbers(payload)
    # Check Indian format 1,05,40,000 -> 10540000
    assert Decimal("10540000") in numbers
    # Check scaled representation 10.54 (millions)
    assert Decimal("10.54") in numbers
    # Check 5.4% -> 5.4
    assert Decimal("5.4") in numbers
    # Check 450000
    assert Decimal("450000") in numbers
    # Check 180000
    assert Decimal("180000") in numbers
    # Check row counts 1 and 3
    assert Decimal("1") in numbers
    assert Decimal("3") in numbers


def test_reconcile_numbers_accepted_case():
    payload = {
        "actual": "10540000.00",
        "budget": "10000000.00",
        "variance_pct": "5.4%",
        "contributors": [
            {"label": "V-00931 repairs", "amount": "450000.00", "rows": 1},
            {"label": "V-00412 spares", "amount": "180000.00", "rows": 3},
        ],
        "total_rows": 4,
    }
    commentary = (
        "Repairs and maintenance is 5.4% above budget for Sep-26, driven mainly by a single "
        "₹4,50,000 repair posting to vendor V-00931 and ₹1,80,000 of spares across three rows. "
        "Total contributors accounted for 4 transaction rows."
    )
    data = {"commentary": commentary}
    updated, res = reconcile_numbers(data, payload)

    assert not res.number_mismatch_flag
    assert NUMBER_REMOVED_PLACEHOLDER not in updated["commentary"]
    assert "₹4,50,000" in updated["commentary"]
    assert "5.4%" in updated["commentary"]


def test_reconcile_numbers_strips_hallucinated_sentence():
    payload = {
        "actual": "100000.00",
        "budget": "90000.00",
    }
    commentary = (
        "Actual spend was 100000.00 against budget 90000.00. "
        "We also discovered an unrecorded invoice of ₹9,99,999 from vendor X. "
        "This indicates a potential timing difference."
    )
    data = {"commentary": commentary}
    updated, res = reconcile_numbers(data, payload)

    assert res.number_mismatch_flag is True
    assert NUMBER_REMOVED_PLACEHOLDER in updated["commentary"]
    assert "₹9,99,999" not in updated["commentary"]
    assert NUMBER_MISMATCH_WARNING in res.warnings
    assert "Actual spend was 100000.00" in updated["commentary"]


def test_reconcile_numbers_completely_discarded():
    payload = {"budget": "5000.00"}
    # Commentary contains only hallucinated figures
    commentary = "The team spent ₹88,000 on software. Another ₹99,000 was spent on consulting."
    data = {"commentary": commentary}
    updated, res = reconcile_numbers(data, payload)

    assert res.number_mismatch_flag is True
    assert res.completely_discarded is True


def test_reconcile_numbers_in_caveats_and_drivers():
    payload = {"variance": "1000.00"}
    data = {
        "commentary": "Variance is 1000.00 for the period.",
        "drivers": [
            {"label": "Unapproved travel of ₹75,000", "direction": "unfavourable", "evidence_ids": ["c-1"]}
        ],
        "caveats": ["Context includes ₹42,000 of miscellaneous charges."],
    }
    updated, res = reconcile_numbers(data, payload)
    assert res.number_mismatch_flag is True
    # Offending driver label replaced with placeholder
    assert updated["drivers"][0]["label"] == NUMBER_REMOVED_PLACEHOLDER
    # Offending caveat stripped
    assert len(updated["caveats"]) == 0


# ---------------------------------------------------------------------------
# 4. Provenance Tracking (§12)
# ---------------------------------------------------------------------------

def test_provenance_stamping():
    provenance = AIDraftProvenance(
        feature_code="PROMPT-01",
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        model="gpt-4o-2024-08-06",
        provider="azure",
        input_scope={"account": "5200", "period": "Sep-26"},
        confidence="medium",
    )
    draft_data = {"commentary": "Sample verified commentary."}
    stamped = stamp_ai_draft(draft_data, provenance)

    assert stamped["is_ai_draft"] is True
    assert stamped["stamp"] == AI_DRAFT_STAMP
    assert stamped["provenance"]["model"] == "gpt-4o-2024-08-06"
    assert stamped["provenance"]["prompt_version"] == "PROMPT-01.v1"
    assert stamped["data"]["commentary"] == "Sample verified commentary."


# ---------------------------------------------------------------------------
# 5. Usage Logging & Cost / Token Capping (§9)
# ---------------------------------------------------------------------------

def test_cost_calculation():
    config = AICapConfig(input_rate_per_1k=0.15, output_rate_per_1k=0.77)
    tracker = AIUsageTracker(config)
    # 1200 in, 220 out -> (1.2 * 0.15) + (0.22 * 0.77) = 0.18 + 0.1694 = 0.3494
    cost = tracker.calculate_estimated_cost(1200, 220)
    assert cost == Decimal("0.349400")


def test_cap_check_input_tokens_exceeded():
    config = AICapConfig(input_tokens_per_call=6000)
    tracker = AIUsageTracker(config)
    res = tracker.check_caps("PROMPT-01", estimated_input_tokens=6500)
    assert res.allowed is False
    assert res.cap_name == "input_tokens_per_call"
    assert res.outcome == "cap_exceeded"


def test_cap_check_hourly_calls_limit():
    config = AICapConfig(calls_per_hour=2)
    tracker = AIUsageTracker(config)
    tracker.record_usage("PROMPT-01", "v1", "modelA", "azure", 10, 100, 50, 150)
    tracker.record_usage("PROMPT-01", "v1", "modelA", "azure", 10, 100, 50, 150)

    res = tracker.check_caps("PROMPT-01")
    assert res.allowed is False
    assert res.cap_name == "calls_per_hour"
    assert res.current_usage == 2


def test_cap_check_monthly_tokens_and_cost():
    config = AICapConfig(monthly_tokens=1000, monthly_cost=10.0)
    tracker = AIUsageTracker(config)
    tracker.record_usage("PROMPT-01", "v1", "m", "p", 1, 800, 300, 200)

    res = tracker.check_caps("PROMPT-01")
    assert res.allowed is False
    assert res.cap_name == "monthly_tokens"
    assert res.reset_date is not None


def test_usage_logging_and_csv_export():
    tracker = AIUsageTracker()
    tracker.record_usage(
        feature_code="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        model="gpt-4o-2024-08-06",
        provider="azure",
        input_row_count=5,
        tokens_in=1000,
        tokens_out=200,
        latency_ms=450,
        outcome="ok",
    )
    csv_data = tracker.export_csv()
    assert "usage_id,occurred_at,feature_code" in csv_data
    assert "PROMPT-01.v1" in csv_data
    assert "gpt-4o-2024-08-06" in csv_data


# ---------------------------------------------------------------------------
# 6. Model Pinning and Fallbacks (§10)
# ---------------------------------------------------------------------------

def test_model_pinning_rejects_floating_aliases():
    with pytest.raises(ValueError, match="Floating model alias 'latest' is forbidden"):
        ModelPinningManager(pinned_model="latest")

    with pytest.raises(ValueError, match="Floating model alias 'gpt-4o-latest' is forbidden"):
        ModelPinningManager(pinned_model="gpt-4o-latest")


def test_model_pinning_execution_chain():
    manager = ModelPinningManager(
        pinned_model="gpt-4o-2024-08-06",
        fallbacks=["gpt-4o-mini-2024-07-18", "claude-3-5-sonnet-20241022"],
    )
    chain = manager.get_execution_chain()
    assert chain == [
        "gpt-4o-2024-08-06",
        "gpt-4o-mini-2024-07-18",
        "claude-3-5-sonnet-20241022",
        "rule_based",
    ]


# ---------------------------------------------------------------------------
# 7. End-to-End Guardrail Pipeline (§8.1)
# ---------------------------------------------------------------------------

def test_pipeline_success():
    pipeline = AIGuardrailPipeline()
    payload = {
        "actual": "10540000.00",
        "budget": "10000000.00",
        "variance_pct": "5.4%",
    }
    raw_response = {
        "commentary": "Spend is 5.4% over budget at 10540000.00 due to planned operational expansion.",
        "drivers": [
            {"label": "Expansion driver", "direction": "unfavourable", "evidence_ids": ["ev-1"]}
        ],
        "confidence": "high",
        "caveats": [],
    }

    stamped, prov, usage = pipeline.process_ai_output(
        raw_response=raw_response,
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        payload=payload,
        input_scope={"account": "5200"},
        allowed_evidence_ids=["ev-1"],
        tokens_in=1200,
        tokens_out=150,
        latency_ms=320,
    )

    assert stamped is not None
    assert stamped["stamp"] == AI_DRAFT_STAMP
    assert prov.status == "draft"
    assert not prov.number_mismatch_flag
    assert usage.outcome == "ok"


def test_pipeline_schema_failure_handled():
    pipeline = AIGuardrailPipeline()
    stamped, prov, usage = pipeline.process_ai_output(
        raw_response="not json at all",
        prompt_id="PROMPT-01",
        prompt_version="PROMPT-01.v1",
        payload={},
        input_scope={},
    )
    assert stamped is None
    assert prov.status == "rejected"
    assert usage.outcome == "schema_error"
