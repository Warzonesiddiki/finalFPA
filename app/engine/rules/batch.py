"""Canonical de-duplicated batch of implemented exception-rule evaluators.

Single source of truth for the rules composed by the CLI (`fpa exceptions
--run`), the API (`POST /api/v1/exceptions/run`) and the perf harness
(`tests/perf/test_rules_perf.py`). `catalog_rule_coverage()` reports only the
catalog IDs backed by registered evaluator callables; it never fabricates aliases.

WHY DE-DUPLICATION IS REQUIRED

The engine splits its evaluators across implementation modules by history,
not by catalog rule:

- `BATCH_CATALOG_001_008_EVALUATORS` contains the five catalog evaluators that
  had no implementation: EXC-001, EXC-002, EXC-003, EXC-006 and EXC-008.
- `BATCH_01_08_EVALUATORS` - 8 legacy evaluators. Their engine IDs do not line
  up with catalog IDs: `evaluate_exc_001` is catalog EXC-007,
  `evaluate_exc_002` is catalog EXC-004, `evaluate_exc_003` is catalog EXC-005,
  `evaluate_exc_004` is catalog EXC-009, `evaluate_exc_005` is catalog EXC-012,
  `evaluate_exc_006` is catalog EXC-015, `evaluate_exc_007` is catalog EXC-017
  and `evaluate_exc_008` is catalog EXC-018.
- `BATCH_09_16_EVALUATORS` - re-exposes catalog EXC-009, EXC-012 and EXC-015 as
  `evaluate_exc_009` / `evaluate_exc_012` / `evaluate_exc_015`, which delegate to
  the `evaluate_exc_004/005/006` implementations above.
- `BATCH_17_24_EVALUATORS` - catalog EXC-019..EXC-024. It deliberately EXCLUDES
  catalog EXC-017 / EXC-018, with the comment that including them "would
  double-raise findings for plantings P17 / P18".

So naively concatenating `BATCH_01_08_EVALUATORS` + `BATCH_09_16_EVALUATORS`
evaluates three rules twice and emits duplicate findings. `build_full_rule_batch()`
below is the only supported composition.

Determinism: this module holds no state and reads no clock. Evaluation order is
the fixed tuple order below, so output is reproducible run to run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.engine.rules.rules_01_08 import (
    BATCH_01_08_EVALUATORS,
    RULES_REGISTRY,
    Finding,
    RuleContext,
)
from app.engine.rules.rules_09_16 import BATCH_09_16_EVALUATORS
from app.engine.rules.rules_17_24 import BATCH_17_24_EVALUATORS
from app.engine.rules.rules_catalog_001_008 import (
    BATCH_CATALOG_001_008_EVALUATORS,
    CATALOG_RULES_001_008_REGISTRY,
)

# doc-06 §2.9: "If any are unmet ... the run summary lists disabled rules with
# reasons; the rule is never approximated". A rule that cannot run must be
# REPORTED, never silently skipped -- an invisible skip is indistinguishable from
# a rule that correctly found nothing.
DISABLED_NOTICE_TEMPLATE = "Disabled - needs {dependency}"

# Catalog rule IDs that BATCH_09_16_EVALUATORS re-exports but which are already
# evaluated inside BATCH_01_08_EVALUATORS. These MUST be filtered out of the
# composed batch or their findings are raised twice.
_REEXPORTED_BY_01_08 = frozenset({
    "evaluate_exc_009",  # delegates to evaluate_exc_004
    "evaluate_exc_012",  # delegates to evaluate_exc_005
    "evaluate_exc_015",  # delegates to evaluate_exc_006
})


def build_full_rule_batch() -> Tuple[Any, ...]:
    """Return each currently implemented evaluator exactly once.

    Composition (24 evaluator callables):

    - 5 explicit catalog evaluators for EXC-001, EXC-002, EXC-003, EXC-006 and
      EXC-008 from `BATCH_CATALOG_001_008_EVALUATORS`
    - 8 legacy evaluators from `BATCH_01_08_EVALUATORS` (catalog mappings come
      from `RULES_REGISTRY`)
    - 5 from `BATCH_09_16_EVALUATORS` after dropping the 3 re-exported wrappers
    - 6 from `BATCH_17_24_EVALUATORS` (catalog EXC-019..EXC-024)

    Every catalog ID EXC-001..EXC-024 now has one evaluator. Coverage is derived
    from explicit registries for the legacy and newly added evaluators; only the
    catalog-numbered later modules use their evaluator suffixes.

    Returns a tuple so the batch is immutable and hashable by callers/tests.
    """
    batch_09_16 = tuple(
        ev
        for ev in BATCH_09_16_EVALUATORS
        if ev.__name__ not in _REEXPORTED_BY_01_08
    )
    return (
        tuple(BATCH_CATALOG_001_008_EVALUATORS)
        + tuple(BATCH_01_08_EVALUATORS)
        + batch_09_16
        + tuple(BATCH_17_24_EVALUATORS)
    )


def catalog_rule_coverage() -> Dict[str, str]:
    """Map implemented catalog IDs to their real evaluator names.

    Legacy evaluators in `rules_01_08` use engine IDs that differ from their
    catalog IDs, so their mapping comes from `RULES_REGISTRY`. The newly added
    early catalog evaluators also have an explicit registry. The later modules
    use catalog-numbered evaluator names. Missing catalog IDs are never
    fabricated from a legacy engine ID.
    """
    legacy_catalog_ids = {
        entry["evaluator"]: entry["catalog_id"]
        for entry in RULES_REGISTRY
    }
    early_catalog_ids = {
        entry["evaluator"]: entry["catalog_id"]
        for entry in CATALOG_RULES_001_008_REGISTRY
    }
    coverage: Dict[str, str] = {}
    for evaluator in build_full_rule_batch():
        if evaluator in BATCH_01_08_EVALUATORS:
            try:
                catalog_id = legacy_catalog_ids[evaluator]
            except KeyError as exc:
                raise ValueError(
                    f"Legacy evaluator {evaluator.__name__} has no catalog ID in RULES_REGISTRY"
                ) from exc
        elif evaluator in BATCH_CATALOG_001_008_EVALUATORS:
            try:
                catalog_id = early_catalog_ids[evaluator]
            except KeyError as exc:
                raise ValueError(
                    f"Catalog evaluator {evaluator.__name__} has no ID in its registry"
                ) from exc
        else:
            prefix = "evaluate_exc_"
            if not evaluator.__name__.startswith(prefix):
                raise ValueError(f"Unrecognized rule evaluator: {evaluator.__name__}")
            suffix = evaluator.__name__[len(prefix):]
            if not suffix.isdecimal():
                raise ValueError(f"Unrecognized rule evaluator: {evaluator.__name__}")
            catalog_id = f"EXC-{int(suffix):03d}"

        if catalog_id in coverage:
            raise ValueError(
                f"Multiple evaluators registered for {catalog_id}: "
                f"{coverage[catalog_id]} and {evaluator.__name__}"
            )
        coverage[catalog_id] = evaluator.__name__

    return dict(sorted(coverage.items()))


class RuleExecutionStatus:
    """Per-rule run outcome. Strings, not an Enum, so they serialise plainly."""

    OK = "ok"
    ERROR = "error"          # the rule raised; the failure is RECORDED, not hidden
    DISABLED = "disabled"    # doc-06 §2.9 unmet required dependency


@dataclass(frozen=True)
class RuleExecution:
    """Outcome of one evaluator in a batch run.

    DEF-024: 11 of 20 evaluators crashed when their required input was absent.
    Because `evaluate_all_rules` let the exception propagate, one missing input
    destroyed the entire exception screen -- all findings from every other rule
    were lost, and the run surfaced only a stack trace. This record is what
    makes the failure visible instead.
    """

    rule_name: str
    status: str
    finding_count: int = 0
    notice: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class RuleBatchResult:
    """Findings plus a per-rule execution record for the run summary."""

    findings: List[Finding] = field(default_factory=list)
    executions: List[RuleExecution] = field(default_factory=list)

    @property
    def failed_rules(self) -> List[RuleExecution]:
        return [e for e in self.executions if e.status == RuleExecutionStatus.ERROR]

    @property
    def disabled_rules(self) -> List[RuleExecution]:
        return [e for e in self.executions if e.status == RuleExecutionStatus.DISABLED]

    @property
    def ran_rules(self) -> List[RuleExecution]:
        return [e for e in self.executions if e.status == RuleExecutionStatus.OK]


def _missing_required_dependency(evaluator: Callable, context: RuleContext) -> Optional[str]:
    """Return the name of an unmet required input for `evaluator`, else None.

    Evaluators may declare `REQUIRED_INPUTS` (a tuple of attribute names on the
    context). Anything declared and absent means the rule is disabled per doc-06
    §2.9 -- it is NEVER approximated, and the caller receives a notice naming the
    missing input. Evaluators that declare nothing are assumed self-contained and
    are simply run.
    """
    for attr in getattr(evaluator, "REQUIRED_INPUTS", ()) or ():
        if getattr(context, attr, None) in (None, (), [], {}, ""):
            return attr

    for attr, minimum_count in (getattr(evaluator, "REQUIRED_INPUT_COUNTS", {}) or {}).items():
        value = getattr(context, attr, None)
        try:
            count = len(value) if value is not None else 0
        except TypeError:
            count = 0
        if count < minimum_count:
            return attr

    return None


def evaluate_all_rules_detailed(
    context: RuleContext,
    batch: Optional[Tuple[Callable, ...]] = None,
) -> RuleBatchResult:
    """Run the de-duplicated batch of implemented evaluators with fault isolation.

    This is the single entry point for a complete composed-batch run. It does not
    imply that every catalog ID has an evaluator; `catalog_rule_coverage()` and
    the acceptance gate report catalog omissions separately. Two properties
    matter and both are load-bearing:

    1. A rule that raises is recorded with status `error`, its exception type and
       message captured, and the run CONTINUES. Losing 23 rules' worth of
       findings because one rule hit absent input is the defect DEF-024 closes.
    2. Nothing is swallowed. The original docstring promised "raises nothing and
       swallows nothing" while the implementation did neither usefully -- an
       exception propagated and destroyed the batch. Every failure now appears in
       `result.executions` with its reason, so a configured evaluator that fails
       cannot be mistaken for one that correctly found nothing.

    doc-06 §2.9: a rule whose required input is unmet is `disabled` with the
    notice "Disabled - needs <input>", never approximated.
    """
    result = RuleBatchResult()
    evaluators = batch if batch is not None else build_full_rule_batch()

    for evaluator in evaluators:
        name = getattr(evaluator, "__name__", repr(evaluator))

        missing = _missing_required_dependency(evaluator, context)
        if missing is not None:
            notices = getattr(evaluator, "REQUIRED_INPUT_NOTICES", {}) or {}
            notice = notices.get(missing, DISABLED_NOTICE_TEMPLATE.format(dependency=missing))
            result.executions.append(
                RuleExecution(
                    rule_name=name,
                    status=RuleExecutionStatus.DISABLED,
                    notice=notice,
                )
            )
            continue

        try:
            produced = evaluator(context)
        except Exception as exc:  # noqa: BLE001 - recorded, never discarded
            result.executions.append(
                RuleExecution(
                    rule_name=name,
                    status=RuleExecutionStatus.ERROR,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
            continue

        result.findings.extend(produced)
        result.executions.append(
            RuleExecution(
                rule_name=name,
                status=RuleExecutionStatus.OK,
                finding_count=len(produced),
            )
        )

    return result


def evaluate_all_rules(context: RuleContext) -> List[Finding]:
    """Run the implemented de-duplicated batch and return every finding.

    Kept as the findings-only convenience for existing callers. Fault isolation
    lives in `evaluate_all_rules_detailed`; this delegates to it so both paths
    behave identically and no caller can accidentally get the fragile version.

    Prefer `evaluate_all_rules_detailed` for anything user-facing: it also
    returns which configured rules errored or were disabled, which is what
    doc-06 §2.9 requires the run summary to show. Catalog coverage is reported
    separately by `catalog_rule_coverage()`.
    """
    return evaluate_all_rules_detailed(context).findings
