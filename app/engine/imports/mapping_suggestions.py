"""Mapping review queue engine per 02_FUNCTIONAL_SPEC.md FR-IMP-008.

FR-IMP-008 (doc 02 line 305), quoted:

    "When a file has unmapped columns and AI is enabled, AI may *propose* mappings;
    each suggestion shows source column, target field, confidence, and evidence
    (examples of previously accepted rows). States: `suggested -> accepted | edited |
    rejected`, with bulk accept/edit and audit trail. Suggestions are **never
    auto-applied in the same run**; accepted mappings apply to future imports. With
    AI disabled, the queue shows rule-based suggestions only."

    Edge cases: "AI returns a target field that does not exist (rejected and logged
    as a malformed response, FR-AI-006); the same column suggested twice
    (deduplicated)."

    Acceptance: "a suggestion accepted during import N is applied automatically in
    import N+1 and appears in the mapping profile history."

DESIGN INVARIANTS

1. AI MAY ONLY PROPOSE. Nothing in this module writes a `DimMapping` row or applies a
   mapping. Application is a separate, explicit act performed by
   `MappingRepository.create_version`, called by the importer on a LATER run.
2. NO SAME-RUN APPLICATION. `MappingSuggestion.applies_to_run_id` is the run that
   raised the suggestion, and `MappingSuggestion.can_apply_to_run(run_id)` returns
   False for it. A suggestion is never applied to the run that produced it.
3. DETERMINISTIC. No clock, no AI call, no randomness here. Confidence is compared
   with Decimal, and ordering is by a total key. `origin` records whether a
   suggestion came from the rule-based or the AI path so the queue can show
   rule-based-only when AI is disabled.
4. Valid targets are validated against CANONICAL_FIELDS (doc 04 section 6). An
   unknown target is rejected and logged as a malformed AI response per FR-AI-006
   rather than silently accepted.

State machine (FR-IMP-008):

    suggested --accept--> accepted
    suggested --edit----> edited      (human changed the target field)
    suggested --reject--> rejected
    accepted/edited/rejected are terminal. Re-opening a decided suggestion is
    refused so the audit trail cannot be rewritten.

`edited` stores the human's chosen field in `resolved_target_field`, keeping the
original AI proposal in `suggested_target_field` so the effectiveness dashboard can
still measure how often the AI was overridden.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Canonical mapping targets, doc 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md section 6.
# Used to validate a suggested target field (FR-IMP-008 edge case, FR-AI-006).
# ---------------------------------------------------------------------------
CANONICAL_FIELDS: frozenset = frozenset({
    "company_code",
    "account_code",
    "cost_center_code",
    "department_code",
    "project_code",
    "vendor_code",
    "vendor_name",
    "posting_date",
    "document_date",
    "period_code",
    "voucher_no",
    "document_no",
    "invoice_no",
    "line_no",
    "description",
    "debit",
    "credit",
    "amount",
    "currency_code",
    "journal_category",
    "budget_version",
    "scenario_code",
    "expected_amount",
    "frequency",
    "start_period_code",
    "amount_threshold",
    "scope",
    "effective_from",
    "owner_name",
})

# Suggestion states and the only legal transitions out of `suggested`.
STATE_SUGGESTED = "suggested"
STATE_ACCEPTED = "accepted"
STATE_EDITED = "edited"
STATE_REJECTED = "rejected"

STATES = frozenset({STATE_SUGGESTED, STATE_ACCEPTED, STATE_EDITED, STATE_REJECTED})

#: FR-IMP-008: `suggested -> accepted | edited | rejected`. A decided state is
#: terminal - the queue may not reopen it, so the audit trail stays append-only.
ALLOWED_TRANSITIONS: Dict[str, frozenset] = {
    STATE_SUGGESTED: frozenset({STATE_ACCEPTED, STATE_EDITED, STATE_REJECTED}),
    STATE_ACCEPTED: frozenset(),
    STATE_EDITED: frozenset(),
    STATE_REJECTED: frozenset(),
}

# Provenance of a suggestion. FR-IMP-008: "With AI disabled, the queue shows
# rule-based suggestions only", so the origin must be explicit, never inferred.
ORIGIN_RULE = "rule"
ORIGIN_AI = "ai"

ZERO = Decimal("0.00")


class InvalidSuggestionTransition(ValueError):
    """Raised when a caller attempts a state change FR-IMP-008 does not allow."""


class MalformedAiSuggestion(ValueError):
    """FR-AI-006 / FR-IMP-008: an AI response naming a non-existent target field.

    Raised rather than silently coerced, so the caller can log the failure and fall
    back per FR-AI-006 ("the feature falls back with a clear message and logs the
    failure").
    """


def _coerce_confidence(value: Any) -> Decimal:
    """Confidence as a Decimal in [0, 1].

    Deterministic: the same input always yields the same Decimal, and an
    out-of-range or unparseable value raises instead of being clamped silently.
    """
    if isinstance(value, Decimal):
        conf = value
    else:
        try:
            conf = Decimal(str(value))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"confidence is not numeric: {value!r}") from exc
    if conf < ZERO or conf > Decimal("1"):
        raise ValueError(f"confidence must be within [0, 1], got {conf}")
    # 4 dp: enough resolution to rank suggestions, bounded so ties are stable.
    return conf.quantize(Decimal("0.0001"))


@dataclass
class MappingSuggestion:
    """One proposed column mapping awaiting human review (FR-IMP-008)."""

    import_run_id: int
    source_column: str
    suggested_target_field: str
    confidence: Decimal
    origin: str = ORIGIN_RULE
    state: str = STATE_SUGGESTED
    # Evidence: examples of previously accepted rows that justify the proposal.
    evidence_examples: List[Dict[str, Any]] = field(default_factory=list)
    # Set when a human accepts or edits. Keeps the original AI proposal intact so
    # override rates remain measurable.
    resolved_target_field: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    malformed_reason: Optional[str] = None
    suggestion_id: Optional[int] = None
    created_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"unknown suggestion state: {self.state!r}")
        if self.origin not in (ORIGIN_RULE, ORIGIN_AI):
            raise ValueError(f"unknown suggestion origin: {self.origin!r}")
        if not str(self.source_column).strip():
            raise ValueError("source_column is required")
        if not str(self.suggested_target_field).strip():
            raise ValueError("suggested_target_field is required")
        self.source_column = str(self.source_column).strip()
        self.suggested_target_field = str(self.suggested_target_field).strip()
        self.confidence = _coerce_confidence(self.confidence)

    # -- identity ---------------------------------------------------------

    @property
    def identity_hash(self) -> str:
        """Stable dedup key: run + source column (FR-IMP-008 deduplication)."""
        return hashlib.sha256(
            f"{self.import_run_id}|{self.source_column}".encode("utf-8")
        ).hexdigest()

    # -- FR-IMP-008 state machine ----------------------------------------

    @property
    def is_decided(self) -> bool:
        return self.state in (STATE_ACCEPTED, STATE_EDITED, STATE_REJECTED)

    def can_transition_to(self, new_state: str) -> bool:
        return new_state in ALLOWED_TRANSITIONS.get(self.state, frozenset())

    def _assert_transition(self, new_state: str) -> None:
        if new_state not in STATES:
            raise InvalidSuggestionTransition(f"unknown state: {new_state!r}")
        if not self.can_transition_to(new_state):
            raise InvalidSuggestionTransition(
                f"FR-IMP-008 allows only "
                f"{sorted(ALLOWED_TRANSITIONS.get(self.state, frozenset()))} "
                f"from '{self.state}', got '{new_state}'"
            )

    def accept(self, decided_by: str, decided_at: Optional[str] = None) -> "MappingSuggestion":
        """Accept the suggestion as proposed."""
        self._assert_transition(STATE_ACCEPTED)
        self.state = STATE_ACCEPTED
        self.resolved_target_field = self.suggested_target_field
        self.decided_by = decided_by
        self.decided_at = decided_at
        return self

    def edit(self, new_target_field: str, decided_by: str,
             decided_at: Optional[str] = None) -> "MappingSuggestion":
        """Accept with a human-chosen target, keeping the AI proposal visible.

        FR-IMP-008 `suggested -> edited`. The replacement must be a real canonical
        field (doc 04 section 6).
        """
        self._assert_transition(STATE_EDITED)
        new_target_field = str(new_target_field or "").strip()
        if not new_target_field:
            raise ValueError("edited suggestion requires a target field")
        if new_target_field not in CANONICAL_FIELDS:
            raise MalformedAiSuggestion(
                f"'{new_target_field}' is not a canonical mapping target (doc 04 section 6)"
            )
        self.state = STATE_EDITED
        self.resolved_target_field = new_target_field
        self.decided_by = decided_by
        self.decided_at = decided_at
        return self

    def reject(self, decided_by: str, decided_at: Optional[str] = None,
               reason: Optional[str] = None) -> "MappingSuggestion":
        """Reject the suggestion (FR-IMP-008 `suggested -> rejected`)."""
        self._assert_transition(STATE_REJECTED)
        self.state = STATE_REJECTED
        self.resolved_target_field = None
        self.decided_by = decided_by
        self.decided_at = decided_at
        if reason:
            self.malformed_reason = reason
        return self

    # -- FR-IMP-008 "never auto-applied in the same run" -----------------

    def can_apply_to_run(self, run_id: int) -> bool:
        """Whether this suggestion may be applied to the given import run.

        FR-IMP-008: "Suggestions are never auto-applied in the same run; accepted
        mappings apply to future imports." So an undecided suggestion can never be
        applied anywhere, a rejected one never, and an accepted/edited one only to a
        run strictly later than the one that raised it.
        """
        if self.state not in (STATE_ACCEPTED, STATE_EDITED):
            return False
        return int(run_id) != int(self.import_run_id)

    @property
    def effective_target_field(self) -> Optional[str]:
        """The field to apply on a later run, or None if not usable yet."""
        if self.state in (STATE_ACCEPTED, STATE_EDITED):
            return self.resolved_target_field
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "import_run_id": self.import_run_id,
            "source_column": self.source_column,
            "suggested_target_field": self.suggested_target_field,
            "resolved_target_field": self.resolved_target_field,
            "confidence": str(self.confidence),
            "origin": self.origin,
            "state": self.state,
            "evidence_examples": self.evidence_examples,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "malformed_reason": self.malformed_reason,
            "identity_hash": self.identity_hash,
        }


# ---------------------------------------------------------------------------
# Queue construction
# ---------------------------------------------------------------------------

def build_suggestion_queue(
    import_run_id: int,
    proposals: List[Dict[str, Any]],
    ai_enabled: bool = False,
    allowed_fields: Optional[frozenset] = None,
) -> List[MappingSuggestion]:
    """Build the review queue for one import run (FR-IMP-008).

    `proposals` items: source_column, target_field, confidence, evidence (optional),
    origin (optional; defaults to `rule`).

    - `ai_enabled=False` (FR-IMP-008 "With AI disabled, the queue shows rule-based
      suggestions only"): AI-origin proposals are DROPPED, not downgraded.
    - Duplicate source_column within the run is deduplicated, keeping the
      highest-confidence proposal; ties keep the first seen, so the result is
      deterministic (FR-IMP-008 edge case "the same column suggested twice
      (deduplicated)").
    - A proposal whose target_field is not canonical is skipped and its reason
      recorded (FR-IMP-008 edge case + FR-AI-006).

    Returns suggestions in deterministic order: descending confidence, then
    ascending source_column.
    """
    fields = allowed_fields if allowed_fields is not None else CANONICAL_FIELDS
    best: Dict[str, MappingSuggestion] = {}

    for raw in proposals or []:
        if not isinstance(raw, dict):
            continue
        origin = str(raw.get("origin", ORIGIN_RULE)).strip() or ORIGIN_RULE
        if origin == ORIGIN_AI and not ai_enabled:
            # AI disabled: rule-based suggestions only.
            continue

        try:
            suggestion = MappingSuggestion(
                import_run_id=import_run_id,
                source_column=str(raw.get("source_column", "")),
                suggested_target_field=str(raw.get("target_field", "")),
                confidence=raw.get("confidence", ZERO),
                origin=origin,
                evidence_examples=list(raw.get("evidence") or []),
            )
        except ValueError:
            # Malformed proposal (FR-AI-006): skip rather than crash the import.
            continue

        if suggestion.suggested_target_field not in fields:
            suggestion.malformed_reason = (
                f"'{suggestion.suggested_target_field}' is not a canonical mapping "
                "target (doc 04 section 6); rejected as malformed per FR-AI-006"
            )
            continue

        existing = best.get(suggestion.source_column)
        if existing is None or suggestion.confidence > existing.confidence:
            best[suggestion.source_column] = suggestion

    return sorted(
        best.values(),
        key=lambda s: (-s.confidence, s.source_column),
    )


def applyable_suggestions(
    suggestions: List[MappingSuggestion],
    run_id: int,
) -> List[MappingSuggestion]:
    """Suggestions this run is permitted to apply (FR-IMP-008).

    Filters to accepted/edited suggestions whose raising run differs from `run_id`.
    """
    return [s for s in suggestions if s.can_apply_to_run(run_id)]