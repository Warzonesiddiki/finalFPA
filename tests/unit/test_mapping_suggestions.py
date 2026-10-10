"""Mapping review queue tests per 02_FUNCTIONAL_SPEC.md FR-IMP-008.

Covers the state machine (`suggested -> accepted | edited | rejected`), the
no-same-run-application guarantee, dedup, the AI-disabled rule-based-only
behaviour, and malformed-response handling (FR-AI-006).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.engine.imports.mapping_suggestions import (
    CANONICAL_FIELDS,
    ORIGIN_AI,
    ORIGIN_RULE,
    STATE_ACCEPTED,
    STATE_EDITED,
    STATE_REJECTED,
    STATE_SUGGESTED,
    InvalidSuggestionTransition,
    MalformedAiSuggestion,
    MappingSuggestion,
    applyable_suggestions,
    build_suggestion_queue,
)
from app.engine.store.db import DatabaseManager
from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository


def make_suggestion(
    column="Gross Amount",
    target="amount",
    confidence="0.82",
    run_id=100,
    origin=ORIGIN_RULE,
) -> MappingSuggestion:
    return MappingSuggestion(
        import_run_id=run_id,
        source_column=column,
        suggested_target_field=target,
        confidence=Decimal(confidence),
        origin=origin,
        evidence_examples=[{"source": "Gross Amount", "target": "amount", "value": "1234.00"}],
    )


@pytest.fixture
def repo(tmp_path) -> MappingSuggestionRepository:
    return MappingSuggestionRepository(DatabaseManager(tmp_path))


# ---------------------------------------------------------------------------
# State machine: suggested -> accepted | edited | rejected
# ---------------------------------------------------------------------------


def test_initial_state_is_suggested():
    assert make_suggestion().state == STATE_SUGGESTED
    assert not make_suggestion().is_decided


def test_accept_transition():
    s = make_suggestion()
    s.accept("Aarti", decided_at="2026-09-30T10:00:00")
    assert s.state == STATE_ACCEPTED
    assert s.resolved_target_field == "amount"
    assert s.decided_by == "Aarti"
    assert s.is_decided


def test_edit_transition_keeps_original_proposal():
    """FR-IMP-008 `suggested -> edited`: the AI proposal stays visible.

    Keeping suggested_target_field intact is what lets the effectiveness dashboard
    measure how often a human overrode the suggestion.
    """
    s = make_suggestion(target="amount")
    s.edit("debit", "Aarti", decided_at="2026-09-30T10:00:00")
    assert s.state == STATE_EDITED
    assert s.resolved_target_field == "debit"
    assert s.suggested_target_field == "amount"


def test_edit_rejects_non_canonical_target():
    """FR-AI-006: an unknown target field is malformed, never silently accepted."""
    s = make_suggestion()
    with pytest.raises(MalformedAiSuggestion):
        s.edit("not_a_real_field", "Aarti")
    assert s.state == STATE_SUGGESTED  # unchanged


def test_reject_transition():
    s = make_suggestion()
    s.reject("Aarti", reason="wrong column entirely")
    assert s.state == STATE_REJECTED
    assert s.resolved_target_field is None
    assert s.malformed_reason == "wrong column entirely"


def test_decided_states_are_terminal():
    """A decided suggestion cannot be reopened - the audit trail is append-only."""
    for action in ("accept", "reject"):
        s = make_suggestion()
        if action == "accept":
            s.accept("Aarti")
        else:
            s.reject("Aarti")
        with pytest.raises(InvalidSuggestionTransition):
            s.accept("Someone-Else")
        with pytest.raises(InvalidSuggestionTransition):
            s.reject("Someone-Else")


def test_illegal_transition_raises_with_allowed_set():
    s = make_suggestion()
    with pytest.raises(InvalidSuggestionTransition) as exc:
        s.state = STATE_ACCEPTED
        s.edit("debit", "Aarti")
    assert "edited" in str(exc.value)


def test_unknown_state_rejected_at_construction():
    with pytest.raises(ValueError):
        MappingSuggestion(
            import_run_id=1,
            source_column="X",
            suggested_target_field="amount",
            confidence=Decimal("0.5"),
            state="maybe",
        )


def test_confidence_must_be_within_unit_interval():
    for bad in ("1.5", "-0.1"):
        with pytest.raises(ValueError):
            make_suggestion(confidence=bad)


# ---------------------------------------------------------------------------
# FR-IMP-008: never auto-applied in the same run
# ---------------------------------------------------------------------------


def test_suggestion_never_applies_to_its_own_run():
    s = make_suggestion(run_id=100)
    s.accept("Aarti")
    assert not s.can_apply_to_run(100)


def test_accepted_suggestion_applies_to_a_later_run():
    """FR-IMP-008 acceptance: accepted in import N, applied in import N+1."""
    s = make_suggestion(run_id=100)
    s.accept("Aarti")
    assert s.can_apply_to_run(101)
    assert s.effective_target_field == "amount"


def test_undecided_or_rejected_suggestion_never_applies():
    undecided = make_suggestion(run_id=100)
    assert not undecided.can_apply_to_run(101)
    assert undecided.effective_target_field is None

    rejected = make_suggestion(run_id=100)
    rejected.reject("Aarti")
    assert not rejected.can_apply_to_run(101)
    assert rejected.effective_target_field is None


def test_applyable_suggestions_filters_same_run():
    a = make_suggestion(column="A", run_id=100)
    a.accept("Aarti")
    b = make_suggestion(column="B", run_id=100)
    b.reject("Aarti")
    c = make_suggestion(column="C", run_id=99)
    c.accept("Aarti")

    got = applyable_suggestions([a, b, c], run_id=100)
    assert [s.source_column for s in got] == ["C"]


# ---------------------------------------------------------------------------
# Queue construction: dedup, AI-disabled, malformed
# ---------------------------------------------------------------------------


def test_duplicate_column_is_deduplicated_keeping_highest_confidence():
    """FR-IMP-008 edge case: "the same column suggested twice (deduplicated)"."""
    queue = build_suggestion_queue(
        import_run_id=1,
        proposals=[
            {"source_column": "Amt", "target_field": "amount", "confidence": "0.40"},
            {"source_column": "Amt", "target_field": "debit", "confidence": "0.95"},
            {"source_column": "Amt", "target_field": "credit", "confidence": "0.70"},
        ],
    )
    assert len(queue) == 1
    assert queue[0].confidence == Decimal("0.9500")
    assert queue[0].suggested_target_field == "debit"


def test_queue_ordering_is_deterministic():
    proposals = [
        {"source_column": "B", "target_field": "amount", "confidence": "0.50"},
        {"source_column": "A", "target_field": "amount", "confidence": "0.50"},
        {"source_column": "C", "target_field": "amount", "confidence": "0.90"},
    ]
    first = [(s.source_column, str(s.confidence)) for s in build_suggestion_queue(1, proposals)]
    second = [(s.source_column, str(s.confidence)) for s in build_suggestion_queue(1, proposals)]
    assert first == second
    # Descending confidence, then ascending column.
    assert [c for c, _ in first] == ["C", "A", "B"]


def test_ai_disabled_shows_rule_based_suggestions_only():
    """FR-IMP-008: "With AI disabled, the queue shows rule-based suggestions only"."""
    proposals = [
        {
            "source_column": "RuleCol",
            "target_field": "amount",
            "confidence": "0.9",
            "origin": ORIGIN_RULE,
        },
        {
            "source_column": "AiCol",
            "target_field": "debit",
            "confidence": "0.9",
            "origin": ORIGIN_AI,
        },
    ]
    without_ai = build_suggestion_queue(1, proposals, ai_enabled=False)
    assert [s.source_column for s in without_ai] == ["RuleCol"]

    with_ai = build_suggestion_queue(1, proposals, ai_enabled=True)
    assert {s.source_column for s in with_ai} == {"RuleCol", "AiCol"}


def test_unknown_target_field_is_dropped_as_malformed():
    """FR-IMP-008 edge case: AI returns a target that does not exist -> rejected."""
    queue = build_suggestion_queue(
        1,
        [
            {"source_column": "Good", "target_field": "amount", "confidence": "0.8"},
            {"source_column": "Bad", "target_field": "hallucinated_field", "confidence": "0.8"},
        ],
    )
    assert [s.source_column for s in queue] == ["Good"]


def test_canonical_fields_are_validated():
    assert "amount" in CANONICAL_FIELDS
    assert "account_code" in CANONICAL_FIELDS
    assert "not_a_field" not in CANONICAL_FIELDS


# ---------------------------------------------------------------------------
# Persistence + audit trail
# ---------------------------------------------------------------------------


def test_enqueue_persists_and_dedupes_across_calls(repo):
    queue = build_suggestion_queue(
        7, [{"source_column": "Amt", "target_field": "amount", "confidence": "0.9"}]
    )
    first = repo.enqueue(queue)
    second = repo.enqueue(queue)
    assert first[0].suggestion_id == second[0].suggestion_id
    assert repo.list_suggestions()["total"] == 1


def test_decision_writes_audit_trail(repo):
    s = repo.enqueue(
        build_suggestion_queue(
            7, [{"source_column": "Amt", "target_field": "amount", "confidence": "0.9"}]
        )
    )[0]
    repo.decide(s.suggestion_id, "accept", "Aarti")
    audit = repo.get_audit_trail(s.suggestion_id)
    assert len(audit) == 1
    assert audit[0]["from_state"] == STATE_SUGGESTED
    assert audit[0]["to_state"] == STATE_ACCEPTED
    assert audit[0]["actor"] == "Aarti"


def test_illegal_decision_writes_no_audit_row(repo):
    s = repo.enqueue(
        build_suggestion_queue(
            7, [{"source_column": "Amt", "target_field": "amount", "confidence": "0.9"}]
        )
    )[0]
    repo.decide(s.suggestion_id, "accept", "Aarti")
    with pytest.raises(InvalidSuggestionTransition):
        repo.decide(s.suggestion_id, "reject", "Someone")
    assert len(repo.get_audit_trail(s.suggestion_id)) == 1
    assert repo.get_suggestion(s.suggestion_id).state == STATE_ACCEPTED


def test_bulk_decide_reports_applied_and_skipped(repo):
    queued = repo.enqueue(
        build_suggestion_queue(
            7,
            [
                {"source_column": "A", "target_field": "amount", "confidence": "0.9"},
                {"source_column": "B", "target_field": "debit", "confidence": "0.8"},
                {"source_column": "C", "target_field": "credit", "confidence": "0.7"},
            ],
        )
    )
    ids = [s.suggestion_id for s in queued]
    result = repo.bulk_decide(ids, "accept", "Aarti")
    assert result["applied"] == ids
    assert result["skipped"] == []

    # Second pass: all are now terminal, so all are skipped and reported.
    again = repo.bulk_decide(ids, "accept", "Aarti")
    assert again["applied"] == []
    assert len(again["skipped"]) == 3


def test_bulk_edit_applies_per_item_targets(repo):
    queued = repo.enqueue(
        build_suggestion_queue(
            7,
            [
                {"source_column": "A", "target_field": "amount", "confidence": "0.9"},
                {"source_column": "B", "target_field": "amount", "confidence": "0.8"},
            ],
        )
    )
    a_id, b_id = [s.suggestion_id for s in queued]
    result = repo.bulk_decide(
        [a_id, b_id], "edit", "Aarti", new_targets={a_id: "debit", b_id: "credit"}
    )
    assert result["applied"] == [a_id, b_id]
    assert repo.get_suggestion(a_id).resolved_target_field == "debit"
    assert repo.get_suggestion(b_id).resolved_target_field == "credit"


def test_bulk_edit_skips_invalid_target_without_aborting_others(repo):
    queued = repo.enqueue(
        build_suggestion_queue(
            7,
            [
                {"source_column": "A", "target_field": "amount", "confidence": "0.9"},
                {"source_column": "B", "target_field": "amount", "confidence": "0.8"},
            ],
        )
    )
    a_id, b_id = [s.suggestion_id for s in queued]
    result = repo.bulk_decide(
        [a_id, b_id], "edit", "Aarti", new_targets={a_id: "debit", b_id: "bogus_field"}
    )
    assert result["applied"] == [a_id]
    assert len(result["skipped"]) == 1


# ---------------------------------------------------------------------------
# No-same-run application at the query level (the import read path)
# ---------------------------------------------------------------------------


def test_repo_applyable_excludes_same_run(repo):
    same_run = repo.enqueue(
        build_suggestion_queue(
            7, [{"source_column": "SameRun", "target_field": "amount", "confidence": "0.9"}]
        )
    )[0]
    prior_run = repo.enqueue(
        build_suggestion_queue(
            6, [{"source_column": "PriorRun", "target_field": "debit", "confidence": "0.9"}]
        )
    )[0]
    repo.decide(same_run.suggestion_id, "accept", "Aarti")
    repo.decide(prior_run.suggestion_id, "accept", "Aarti")

    applyable = repo.applyable_for_run(7)
    assert [s.source_column for s in applyable] == ["PriorRun"]


def test_count_by_state(repo):
    repo.enqueue(
        build_suggestion_queue(
            7,
            [
                {"source_column": "A", "target_field": "amount", "confidence": "0.9"},
                {"source_column": "B", "target_field": "debit", "confidence": "0.8"},
            ],
        )
    )
    counts = repo.count_by_state(7)
    assert counts.get(STATE_SUGGESTED) == 2
    assert counts.get(STATE_ACCEPTED) is None


def test_list_filters_by_origin_and_state(repo):
    repo.enqueue(
        build_suggestion_queue(
            7,
            [
                {
                    "source_column": "R",
                    "target_field": "amount",
                    "confidence": "0.9",
                    "origin": ORIGIN_RULE,
                },
                {
                    "source_column": "AI",
                    "target_field": "debit",
                    "confidence": "0.8",
                    "origin": ORIGIN_AI,
                },
            ],
            ai_enabled=True,
        )
    )
    ai_only = repo.list_suggestions(origin=ORIGIN_AI)
    assert [i["source_column"] for i in ai_only["items"]] == ["AI"]

    suggested = repo.list_suggestions(state=STATE_SUGGESTED)
    assert suggested["total"] == 2
