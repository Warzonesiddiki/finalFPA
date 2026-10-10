"""D-15 part 2: floor-raising tests for app/engine/ai/guardrails.py.

Targets previously uncovered lines/branches with concrete spec values
(AI spec §5, §8, §9, §10, §12).
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.engine.ai.guardrails import (
    AI_DRAFT_STAMP,
    NUMBER_REMOVED_PLACEHOLDER,
    AICapConfig,
    AIDraftProvenance,
    AIGuardrailPipeline,
    AISchemaValidationError,
    AIUsageTracker,
    CapExceededException,
    FactAIUsage,
    ModelPinningManager,
    check_sentence_numbers,
    check_word_counts,
    extract_payload_numbers,
    reconcile_numbers,
    reconcile_text_numbers,
    sanitize_fields,
    split_sentences,
    validate_evidence_ids,
    validate_json_schema,
)


def _valid_p1_commentary(**overrides):
    data = {
        "commentary": "Repairs and maintenance is 5.4% above budget for Sep-26, driven mainly by repairs.",
        "drivers": [
            {
                "label": "Single repair posting",
                "direction": "unfavourable",
                "evidence_ids": ["c-1"],
            }
        ],
        "confidence": "high",
        "caveats": [],
    }
    data.update(overrides)
    return data


class TestCapExceededException:
    def test_attributes(self):
        exc = CapExceededException("Monthly cap hit", "monthly_tokens", 2000, 1000)
        assert str(exc) == "Monthly cap hit"
        assert exc.cap_name == "monthly_tokens"
        assert exc.current_usage == 2000
        assert exc.limit == 1000


class TestValidateJsonSchemaEdges:
    def test_unknown_schema_id_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown prompt schema identifier: NOPE"):
            validate_json_schema({}, "NOPE")

    def test_inline_dict_schema_passthrough(self):
        data = validate_json_schema({"a": 1}, {"type": "object"})
        assert data == {"a": 1}

    def test_plain_fence_without_json_tag(self):
        raw = "```\n" + '{"a": 1}' + "\n```"
        assert validate_json_schema(raw, {"type": "object"}) == {"a": 1}

    def test_non_str_non_dict_raises(self):
        with pytest.raises(AISchemaValidationError, match="Expected str or dict"):
            validate_json_schema(12345, "PROMPT-01")

    def test_trailing_text_rejected(self):
        with pytest.raises(AISchemaValidationError, match="Invalid JSON response"):
            validate_json_schema('{"a": 1} trailing garbage', {"type": "object"})


class TestSanitizeFields:
    def test_non_commentary_prompt_passthrough(self):
        data = {"suggestions": [{"source_column": "A"}]}
        assert sanitize_fields("PROMPT-02", data) == data
        assert sanitize_fields("PROMPT-01", {"drivers": []}) == {"drivers": []}

    def test_markdown_headers_and_bullets_stripped(self):
        data = {"commentary": "## Variance Review\n- item one"}
        cleaned = sanitize_fields("PROMPT-01", data)
        assert cleaned["commentary"] == "Variance Review - item one"


class TestValidateEvidenceIdsGroupsAndItems:
    def test_groups_strip_unknown_and_engine_count_wins(self):
        data = {
            "groups": [
                {
                    "theme": "Duplicates",
                    "count": 99,  # stale AI count; engine recomputes
                    "severity_max": "high",
                    "exception_ids": ["ex-1", "bad-9"],
                    "note": "Two postings",
                }
            ]
        }
        updated, mismatch, stripped = validate_evidence_ids(data, ["ex-1"])
        assert mismatch is True
        assert stripped == ["bad-9"]
        assert updated["groups"][0]["exception_ids"] == ["ex-1"]
        assert updated["groups"][0]["count"] == 1

    def test_groups_all_valid_keeps_count(self):
        data = {
            "groups": [
                {
                    "theme": "T",
                    "count": 5,
                    "severity_max": "low",
                    "exception_ids": ["ex-1", "ex-2"],
                    "note": "n",
                }
            ]
        }
        updated, mismatch, stripped = validate_evidence_ids(data, ["ex-1", "ex-2"])
        assert mismatch is False
        assert stripped == []
        assert updated["groups"][0]["count"] == 2

    def test_items_referenced_strips_unknown(self):
        data = {"items_referenced": ["ex-1", "ghost-7"]}
        updated, mismatch, stripped = validate_evidence_ids(data, ["ex-1"])
        assert mismatch is True
        assert stripped == ["ghost-7"]
        assert updated["items_referenced"] == ["ex-1"]

    def test_items_referenced_all_valid(self):
        data = {"items_referenced": ["ex-1"]}
        updated, mismatch, stripped = validate_evidence_ids(data, ["ex-1"])
        assert mismatch is False
        assert updated["items_referenced"] == ["ex-1"]


class TestExtractPayloadNumbers:
    def test_decimal_int_float_and_containers(self):
        payload = {
            "ratio": Decimal("5.4"),
            "count": 7,
            "rate": 2.5,
            "pair": (1, 2),
            "bag": {3, 4},
            "nested": [{"x": Decimal("10")}],
        }
        numbers = extract_payload_numbers(payload)
        for expected in ("5.4", "7", "2.5", "1", "2", "3", "4", "10"):
            assert Decimal(expected) in numbers

    def test_non_numeric_string_yields_nothing(self):
        assert extract_payload_numbers("no digits here") == set()

    def test_none_payload_yields_empty(self):
        assert extract_payload_numbers(None) == set()

    def test_zero_has_no_scaled_variants_crash(self):
        numbers = extract_payload_numbers({"v": 0})
        assert Decimal("0") in numbers


class TestSentenceAndWordChecks:
    def test_split_sentences_blank_input(self):
        assert split_sentences("  \n   ") == []

    def test_split_multiline(self):
        assert split_sentences("First line.\nSecond line.") == ["First line.", "Second line."]

    def test_reconcile_empty_text_early_return(self):
        res = reconcile_text_numbers("   ", {Decimal("1")})
        assert res.number_mismatch_flag is False
        assert res.completely_discarded is False
        assert res.reconciled_text == "   "
        assert res.total_sentences_count == 0

    def test_tolerance_match_avoids_false_positive(self):
        # 10.54005 is within 0.0001 of allowed 10.54 (float rounding guard)
        valid, offending = check_sentence_numbers("Value was 10.54005 million.", {Decimal("10.54")})
        assert valid is True
        assert offending == []

    def test_clear_mismatch_flagged(self):
        valid, offending = check_sentence_numbers("Value was 99.99 million.", {Decimal("10.54")})
        assert valid is False
        assert offending == ["99.99"]

    def test_word_count_match_no_warning(self):
        mismatch, warnings = check_word_counts("Three rows were posted.", {Decimal("3")})
        assert mismatch is False
        assert warnings == []

    def test_word_count_mismatch_warns_not_strips(self):
        mismatch, warnings = check_word_counts("Three rows were posted.", {Decimal("4")})
        assert mismatch is True
        assert len(warnings) == 1
        assert "three rows" in warnings[0]

    def test_word_count_two_items(self):
        mismatch, warnings = check_word_counts("Two items need review.", {Decimal("5")})
        assert mismatch is True
        assert "two items" in warnings[0]


class TestReconcileNumbersFields:
    def test_body_markdown_reconciled(self):
        payload = {"budget": "5000", "actual": "5200"}
        data = {
            "subject_line": "Sep-26 close: 1 item for review",
            "body_markdown": "Budget is 5000 and actual is 5200. An extra 99999 was unrecorded.",
            "items_referenced": ["ex-1"],
            "confidence": "high",
        }
        updated, res = reconcile_numbers(data, payload)
        assert res.number_mismatch_flag is True
        assert "99999" not in updated["body_markdown"]
        assert NUMBER_REMOVED_PLACEHOLDER in updated["body_markdown"]
        assert "Budget is 5000 and actual is 5200." in updated["body_markdown"]

    def test_summary_clean_passes(self):
        payload = {"total": "7"}
        data = {
            "summary": "Seven exceptions are open and the total count is 7 for review now.",
            "groups": [],
            "review_order": [],
            "confidence": "high",
        }
        updated, res = reconcile_numbers(data, payload)
        assert res.number_mismatch_flag is False
        assert NUMBER_REMOVED_PLACEHOLDER not in updated["summary"]

    def test_summary_hallucinated_flagged(self):
        payload = {"total": "7"}
        data = {
            "summary": "Total is 7 for the period. A further 424242 was written off.",
            "groups": [],
            "review_order": [],
            "confidence": "high",
        }
        updated, res = reconcile_numbers(data, payload)
        assert res.number_mismatch_flag is True
        assert NUMBER_REMOVED_PLACEHOLDER in updated["summary"]

    def test_no_text_field_returns_empty_result(self):
        data = {"suggestions": []}
        updated, res = reconcile_numbers(data, {"a": 1})
        assert res.number_mismatch_flag is False
        assert res.reconciled_text == ""
        assert updated == data

    def test_valid_caveat_preserved(self):
        payload = {"variance": "1000"}
        data = {
            "commentary": "Variance is 1000 for the period.",
            "caveats": ["Reviewed against the 1000 limit."],
        }
        updated, res = reconcile_numbers(data, payload)
        assert res.number_mismatch_flag is False
        assert updated["caveats"] == ["Reviewed against the 1000 limit."]

    def test_valid_driver_label_preserved(self):
        payload = {"amount": "450000"}
        data = {
            "commentary": "Spend is 450000 for the period.",
            "drivers": [
                {
                    "label": "Posting of 450000 confirmed",
                    "direction": "unfavourable",
                    "evidence_ids": ["c-1"],
                }
            ],
        }
        updated, res = reconcile_numbers(data, payload)
        assert res.number_mismatch_flag is False
        assert updated["drivers"][0]["label"] == "Posting of 450000 confirmed"


class TestFactAIUsage:
    def test_to_dict_stringifies_cost(self):
        entry = FactAIUsage(
            usage_id="ai_abc123",
            occurred_at="2026-09-01T00:00:00+00:00",
            feature_code="PROMPT-01",
            model="gpt-4o-2024-08-06",
            prompt_version="PROMPT-01.v1",
            input_row_count=5,
            tokens_in=1000,
            tokens_out=200,
            estimated_cost=Decimal("0.304000"),
            latency_ms=450,
            outcome="ok",
        )
        d = entry.to_dict()
        assert d["estimated_cost"] == "0.304000"
        assert d["usage_id"] == "ai_abc123"
        assert d["provider"] == "azure"


class TestUsageTrackerEdges:
    def test_hourly_ignores_malformed_and_stale_entries(self):
        tracker = AIUsageTracker(AICapConfig(calls_per_hour=100))
        tracker.record_usage("PROMPT-01", "v1", "m", "azure", 1, 10, 5, 50)
        tracker.logs[0].occurred_at = "not-a-timestamp"
        stale_ts = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        tracker.record_usage("PROMPT-01", "v1", "m", "azure", 1, 10, 5, 50, timestamp=stale_ts)
        assert tracker.get_hourly_call_count() == 0

    def test_monthly_excludes_prior_month_and_malformed(self):
        tracker = AIUsageTracker()
        now = datetime.now(UTC)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prior_ts = (first_of_month - timedelta(days=1)).isoformat()
        tracker.record_usage("PROMPT-01", "v1", "m", "azure", 1, 800, 300, 200, timestamp=prior_ts)
        tracker.record_usage("PROMPT-01", "v1", "m", "azure", 1, 800, 300, 200)
        tracker.logs[0].occurred_at = "garbage"
        tokens, cost = tracker.get_monthly_usage(now)
        assert tokens == 1100
        assert cost == tracker.calculate_estimated_cost(800, 300)

    def test_december_reset_date_rolls_year(self):
        tracker = AIUsageTracker()
        dec = datetime(2026, 12, 15, 12, 0, 0, tzinfo=UTC)
        res = tracker.check_caps("PROMPT-01", now=dec)
        assert res.allowed is True
        assert res.outcome == "ok"
        # Force the monthly-tokens branch in December to observe the rolled reset date
        tight = AIUsageTracker(AICapConfig(monthly_tokens=1))
        dec_ts = datetime(2026, 12, 2, 10, 0, 0, tzinfo=UTC).isoformat()
        tight.record_usage("PROMPT-01", "v1", "m", "azure", 1, 800, 300, 200, timestamp=dec_ts)
        blocked = tight.check_caps("PROMPT-01", now=dec)
        assert blocked.allowed is False
        assert blocked.cap_name == "monthly_tokens"
        assert blocked.reset_date == "2027-01-01"

    def test_monthly_cost_cap_blocks_when_tokens_do_not(self):
        config = AICapConfig(monthly_tokens=10**9, monthly_cost=0.000001)
        tracker = AIUsageTracker(config)
        tracker.record_usage("PROMPT-01", "v1", "m", "azure", 1, 800, 300, 200)
        res = tracker.check_caps("PROMPT-01")
        assert res.allowed is False
        assert res.cap_name == "monthly_cost"
        assert res.reset_date is not None
        assert "₹" in res.message

    def test_caps_allowed_path(self):
        tracker = AIUsageTracker()
        res = tracker.check_caps("PROMPT-01", estimated_input_tokens=100)
        assert res.allowed is True
        assert res.cap_name is None
        assert res.outcome == "ok"


class TestModelPinningEdges:
    def test_fallbacks_capped_at_three(self):
        manager = ModelPinningManager(
            pinned_model="gpt-4o-2024-08-06",
            fallbacks=["fb-1-v1", "fb-2-v1", "fb-3-v1", "fb-4-v1"],
        )
        assert manager.fallbacks == ["fb-1-v1", "fb-2-v1", "fb-3-v1"]
        assert manager.get_execution_chain()[-1] == "rule_based"

    def test_latest_suffix_and_case_rejected(self):
        with pytest.raises(ValueError, match="Floating model alias"):
            ModelPinningManager(pinned_model="my-model-latest")
        with pytest.raises(ValueError, match="Floating model alias"):
            ModelPinningManager(pinned_model="LATEST")
        with pytest.raises(ValueError, match="Floating model alias"):
            ModelPinningManager(pinned_model="gpt-4o-2024-08-06", fallbacks=["current"])


class TestPipelineBranches:
    def test_evidence_mismatch_and_banned_phrase_in_pipeline(self):
        pipeline = AIGuardrailPipeline()
        payload = {"actual": "100", "budget": "90", "variance": "10"}
        raw = _valid_p1_commentary(
            commentary="Variance is 10 against budget 90 and this looks wrong in timing.",
            drivers=[
                {
                    "label": "Variance driver",
                    "direction": "unfavourable",
                    "evidence_ids": ["ev-1", "ghost-9"],
                }
            ],
        )
        stamped, prov, usage = pipeline.process_ai_output(
            raw_response=raw,
            prompt_id="PROMPT-01",
            prompt_version="PROMPT-01.v1",
            payload=payload,
            input_scope={"account": "5200"},
            allowed_evidence_ids=["ev-1"],
        )
        assert stamped is not None
        assert prov.evidence_mismatch_flag is True
        assert prov.banned_phrases_detected == ["wrong"]
        assert prov.confidence == "low"  # evidence mismatch forces low confidence
        assert any("Unknown evidence IDs stripped: ghost-9" in w for w in prov.warnings)
        assert any("Banned verdict language detected" in w for w in prov.warnings)
        assert usage.outcome == "ok"

    def test_completely_discarded_pipeline_rejects(self):
        pipeline = AIGuardrailPipeline()
        payload = {"budget": "5000"}
        raw = _valid_p1_commentary(
            commentary="The team spent 88000 on software. Another 99000 went to consulting.",
        )
        stamped, prov, usage = pipeline.process_ai_output(
            raw_response=raw,
            prompt_id="PROMPT-01",
            prompt_version="PROMPT-01.v1",
            payload=payload,
            input_scope={"account": "5200"},
        )
        assert stamped is None
        assert prov.status == "rejected"
        assert usage.outcome == "ok"

    def test_provenance_stamp_contents(self):
        prov = AIDraftProvenance(
            feature_code="PROMPT-04",
            prompt_id="PROMPT-04",
            prompt_version="PROMPT-04.v1",
            model="gpt-4o-2024-08-06",
            provider="azure",
            input_scope={"period": "Sep-26"},
        )
        assert prov.stamp == AI_DRAFT_STAMP
        assert prov.status == "draft"
        assert prov.draft_id.startswith("draft_")
        d = prov.to_dict()
        assert d["feature_code"] == "PROMPT-04"
