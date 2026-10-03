"""Canonical full-catalog rule batch (EXC-001..EXC-024) with de-duplication.

Single source of truth for "run every exception rule". The CLI
(`fpa exceptions --run`), the API (`POST /api/v1/exceptions/run`) and the perf
harness (`tests/perf/test_rules_perf.py`) all compose the batch from here, so no
caller can accidentally evaluate a rule twice.

WHY DE-DUPLICATION IS REQUIRED

The engine splits its evaluators across three modules by implementation history,
not by catalog rule:

- `BATCH_01_08_EVALUATORS` - 8 evaluators. Internally these carry FIVE catalog
  rules that a reader would not expect: `evaluate_exc_004` is catalog EXC-009,
  `evaluate_exc_005` is catalog EXC-012, `evaluate_exc_006` is catalog EXC-015,
  `evaluate_exc_007` is catalog EXC-017 and `evaluate_exc_008` is catalog EXC-018.
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
    Finding,
    RuleContext,
)
from app.engine.rules.rules_09_16 import BATCH_09_16_EVALUATORS
from app.engine.rules.rules_17_24 import BATCH_17_24_EVALUATORS

# doc-06 §2.9: "If any are unmet ... the run summary lists disabled rules with
# reasons; the rule is never approximated". A rule that cannot run must be
# REPORTED, never silently skipped -- an invisible skip is indistinguishable from
# a rule that correctly found nothing.
DISABLED_NOTICE_TEMPLATE = "Disabled - needs {dependency}"

# Catalog rule IDs that BATCH_09_16_EVALUATORS re-exports but which are already
# evaluated inside BATCH_01_08_EVALUATORS. These MUST be filtered out of a full
# run or their findings are raised twice.
_REEXPORTED_BY_01_08 = frozenset({
    "evaluate_exc_009",  # delegates to evaluate_exc_004
    "evaluate_exc_012",  # delegates to evaluate_exc_005
    "evaluate_exc_015",  # delegates to evaluate_exc_006
})

# Catalog IDs evaluated inside BATCH_01_08_EVALUATORS under engine-internal ids.
# Kept for reporting so a caller can show true catalog coverage.
_CATALOG_IDS_IN_01_08 = (
    "EXC-007",  # evaluate_exc_001 duplicate invoice
    "EXC-004",  # evaluate_exc_002 unmapped account
    "EXC-005",  # evaluate_exc_003 inactive cost centre
    "EXC-009",  # evaluate_exc_004 posting-date / period mismatch
    "EXC-012",  # evaluate_exc_005 negative expense
    "EXC-015",  # evaluate_exc_006 missing recurring cost
    "EXC-017",  # evaluate_exc_007 material unbudgeted spend
    "EXC-018",  # evaluate_exc_008 material variance
)


def build_full_rule_batch() -> Tuple[Any, ...]:
    """Return every catalog rule evaluator, each appearing exactly once.

    Composition (19 evaluators covering all 24 catalog rules):

    - 8 from `BATCH_01_08_EVALUATORS` (carries 8 catalog rules, see above)
    - 5 from `BATCH_09_16_EVALUATORS` after dropping the 3 re-exported wrappers
    - 6 from `BATCH_17_24_EVALUATORS` (catalog EXC-019..EXC-024)

    Returns a tuple so the batch is immutable and hashable by callers/tests.
    """
    batch_09_16 = tuple(
        ev
        for ev in BATCH_09_16_EVALUATORS
        if ev.__name__ not in _REEXPORTED_BY_01_08
    )
    return tuple(BATCH_01_08_EVALUATORS) + batch_09_16 + tuple(BATCH_17_24_EVALUATORS)


def catalog_rule_coverage() -> Dict[str, str]:
    """Map every catalog rule ID EXC-001..EXC-024 to the evaluator that runs it.

    Useful for the run summary and for asserting full coverage in tests.
    """
    coverage: Dict[str, str] = {}
    for catalog_id, evaluator in zip(_CATALOG_IDS_IN_01_08, BATCH_01_08_EVALUATORS):
        coverage[catalog_id] = evaluator.__name__
    for evaluator in build_full_rule_batch():
        coverage[evaluator.__name__.replace("evaluate_exc_", "EXC-")] = evaluator.__name__
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
    return None


def evaluate_all_rules_detailed(
    context: RuleContext,
    batch: Optional[Tuple[Callable, ...]] = None,
) -> RuleBatchResult:
    """Run the full de-duplicated catalog with per-rule fault isolation.

    This is the single entry point for a complete rule run. Two properties matter
    and both are load-bearing:

    1. A rule that raises is recorded with status `error`, its exception type and
       message captured, and the run CONTINUES. Losing 19 rules' worth of
       findings because one rule hit absent input is the defect DEF-024 closes.
    2. Nothing is swallowed. The original docstring promised "raises nothing and
       swallows nothing" while the implementation did neither usefully -- an
       exception propagated and destroyed the batch. Every failure now appears in
       `result.executions` with its reason, so a run that silently evaluated less
       than the full catalog is visible to the caller and to the run summary.

    doc-06 §2.9: a rule whose required input is unmet is `disabled` with the
    notice "Disabled - needs <input>", never approximated.
    """
    result = RuleBatchResult()
    evaluators = batch if batch is not None else build_full_rule_batch()

    for evaluator in evaluators:
        name = getattr(evaluator, "__name__", repr(evaluator))

        missing = _missing_required_dependency(evaluator, context)
        if missing is not None:
            result.executions.append(
                RuleExecution(
                    rule_name=name,
                    status=RuleExecutionStatus.DISABLED,
                    notice=DISABLED_NOTICE_TEMPLATE.format(dependency=missing),
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
    """Run the full de-duplicated catalog and return every finding.

    Kept as the findings-only convenience for existing callers. Fault isolation
    lives in `evaluate_all_rules_detailed`; this delegates to it so both paths
    behave identically and no caller can accidentally get the fragile version.

    Prefer `evaluate_all_rules_detailed` for anything user-facing: it also
    returns which rules errored or were disabled, which is what doc-06 §2.9
    requires the run summary to show.
    """
    return evaluate_all_rules_detailed(context).findings