"""DEF-024: rule-batch fault containment.

DEF-024 root cause: `evaluate_all_rules` in `app/engine/rules/batch.py` called
each evaluator with no error handling, so a single evaluator that hit absent
required input propagated and destroyed the ENTIRE exception run -- every other
rule's findings were lost and the only evidence was a stack trace. Measured
before the fix: 11 of 20 evaluators raise on absent input. The docstring at the
time claimed "Raises nothing and swallows nothing", which described neither
behaviour: it raised, and it lost everything.

The fix has to satisfy two properties that pull against each other, and this
module exists to prove both hold:

  1. ISOLATION - one crashing rule must not cost the other 19 their findings.
  2. VISIBILITY - the failure must be RECORDED, never swallowed.

Property 2 is why these tests assert on the ERROR RECORD existing and carrying
the exception type and message, rather than merely asserting the batch returned.
A test that only checks "the batch completed" passes against an implementation
that discarded the failure outright -- which is the pre-DEF-024 defect wearing a
fix's clothing. The test named `test_one_recorded_failure_is_not_hidden_by_a_green_batch`
exists specifically to kill that variant.

doc-06 §2.9 is also pinned here: a rule whose required input is unmet is
`disabled` with the notice "Disabled - needs <input>", never approximated.

Mutation-tested. Reinstating the unguarded `findings.extend(evaluator(context))`
fails 3 of these; deleting the execution record fails 2 more; replacing the
disable path with a silent skip fails 3 more.
"""

from decimal import Decimal

from app.engine.rules.batch import (
    DISABLED_NOTICE_TEMPLATE,
    RuleExecutionStatus,
    build_full_rule_batch,
    evaluate_all_rules,
    evaluate_all_rules_detailed,
)
from app.engine.rules.rules_01_08 import Finding, RuleContext


class _Boom(RuntimeError):
    """Distinct type so the tests can assert the exception TYPE is captured."""


def _finding(rule_id="EXC-098", subject="test|1"):
    return Finding(
        rule_id=rule_id,
        rule_name="test rule",
        severity="Low",
        tier="exact",
        subject_key=subject,
        subject_display="test finding",
        amount_at_risk=Decimal("100.00"),
        period_id="FY26-P09",
        owner_role="Management Accountant",
        effective_threshold="none",
        detail="synthetic finding for DEF-024 containment test",
    )


def _ok_rule(name="evaluate_exc_test_ok"):
    def _rule(context):
        return [_finding(subject=f"test|{name}")]

    _rule.__name__ = name
    return _rule


def _boom_rule():
    def _rule(context):
        raise _Boom("required input 'master_recurring_costs' is absent")

    _rule.__name__ = "evaluate_exc_test_boom"
    return _rule


def _needs(attr, name, raises=True):
    """A rule declaring `attr` as a required input."""

    def _rule(context):
        if raises:
            raise AssertionError("must not be invoked: dependency unmet")
        return []

    _rule.__name__ = name
    _rule.REQUIRED_INPUTS = (attr,)
    return _rule


# --------------------------------------------------------------------------
# 1. Isolation
# --------------------------------------------------------------------------


def test_crash_does_not_cost_other_rules_their_findings():
    """ISOLATION. Pre-DEF-024 this raised out of evaluate_all_rules."""
    good_a, boom, good_b = _ok_rule("a"), _boom_rule(), _ok_rule("b")

    result = evaluate_all_rules_detailed(RuleContext(), batch=(good_a, boom, good_b))

    assert len(result.findings) == 2, (
        f"the two healthy rules must still produce their findings; got {len(result.findings)}"
    )
    assert {e.rule_name for e in result.ran_rules} == {"a", "b"}


def test_crash_is_recorded_not_swallowed():
    """VISIBILITY. The record must carry type AND message."""
    result = evaluate_all_rules_detailed(RuleContext(), batch=(_boom_rule(),))

    failed = result.failed_rules
    assert len(failed) == 1, "the failing rule must appear in the run summary"
    assert failed[0].rule_name == "evaluate_exc_test_boom"
    assert failed[0].status == RuleExecutionStatus.ERROR
    assert failed[0].error_type == "_Boom", (
        "the exception TYPE must be captured so a caller can triage without logs"
    )
    assert "master_recurring_costs" in (failed[0].error_message or "")


def test_one_recorded_failure_is_not_hidden_by_a_green_batch():
    """The assertion that kills `except Exception: pass`.

    That variant returns all findings from the healthy rules, so from the
    caller's side it looks like a clean run over the whole catalog. It is the
    most dangerous form of the fix because it converts a visible crash into
    invisible partial coverage.
    """
    result = evaluate_all_rules_detailed(RuleContext(), batch=(_ok_rule("a"), _boom_rule()))

    assert result.findings, "healthy rules did produce findings"
    assert result.failed_rules, (
        "findings were returned AND a rule crashed, yet the failure is invisible"
    )
    assert len(result.executions) == 2, "every rule must appear in the summary"


def test_one_execution_record_per_evaluator_no_rule_vanishes():
    batch = (_ok_rule("a"), _boom_rule(), _needs("budgets", "c"))
    result = evaluate_all_rules_detailed(RuleContext(), batch=batch)

    assert len(result.executions) == len(batch)
    assert {e.rule_name for e in result.executions} == {
        "a",
        "evaluate_exc_test_boom",
        "c",
    }


def test_status_partition_is_exhaustive_and_disjoint():
    """ok / error / disabled must account for every rule exactly once.

    A rule in two buckets, or in none, means the run summary lies about coverage.
    """
    batch = (_ok_rule("a"), _boom_rule(), _needs("budgets", "c"))
    result = evaluate_all_rules_detailed(RuleContext(), batch=batch)

    ok = {e.rule_name for e in result.ran_rules}
    bad = {e.rule_name for e in result.failed_rules}
    off = {e.rule_name for e in result.disabled_rules}

    assert ok == {"a"}
    assert bad == {"evaluate_exc_test_boom"}
    assert off == {"c"}
    assert not (ok & bad) and not (ok & off) and not (bad & off)


def test_disabled_and_errored_rules_stay_distinguishable():
    """A disabled rule is a correct decision; an errored rule is a defect.
    Collapsing them would let real faults hide behind a benign-sounding notice."""
    result = evaluate_all_rules_detailed(
        RuleContext(), batch=(_boom_rule(), _needs("budgets", "c"))
    )

    assert result.failed_rules[0].notice is None
    assert result.failed_rules[0].error_type == "_Boom"
    assert result.disabled_rules[0].error_type is None
    assert result.disabled_rules[0].notice


# --------------------------------------------------------------------------
# 2. doc-06 §2.9 -- disable with a notice, never approximate
# --------------------------------------------------------------------------


def test_unmet_required_dependency_disables_with_doc06_notice():
    """doc-06 §2.9: 'Rule is disabled for the run with the notice
    "Disabled - needs <input>" ... the rule is never approximated.'"""
    boom_if_run = _needs("master_recurring_costs", "needs_costs")
    result = evaluate_all_rules_detailed(RuleContext(), batch=(boom_if_run, _ok_rule("a")))

    disabled = result.disabled_rules
    assert len(disabled) == 1
    assert disabled[0].rule_name == "needs_costs"
    assert disabled[0].status == RuleExecutionStatus.DISABLED
    assert disabled[0].notice == DISABLED_NOTICE_TEMPLATE.format(
        dependency="master_recurring_costs"
    )
    # It raised if invoked, and it did not -- proving it was skipped, not caught.
    assert len(result.findings) == 1


def test_satisfied_dependency_runs_normally():
    rule = _needs("master_recurring_costs", "needs_costs", raises=False)
    context = RuleContext(master_recurring_costs=[{"vendor_id": "V1"}])

    result = evaluate_all_rules_detailed(context, batch=(rule,))

    assert len(result.ran_rules) == 1
    assert not result.disabled_rules
    assert not result.failed_rules


def test_empty_collection_counts_as_unmet():
    """`master_recurring_costs=[]` must disable, not run.

    Otherwise the rule iterates nothing and reports 'no exceptions found' on a
    run where it checked nothing -- a green result for zero coverage.
    """
    boom_if_run = _needs("master_recurring_costs", "needs_costs")
    result = evaluate_all_rules_detailed(
        RuleContext(master_recurring_costs=[]), batch=(boom_if_run,)
    )

    assert len(result.disabled_rules) == 1
    assert not result.ran_rules
    assert not result.failed_rules


# --------------------------------------------------------------------------
# 3. The real batch
# --------------------------------------------------------------------------


def test_real_batch_yields_one_record_per_rule():
    result = evaluate_all_rules_detailed(RuleContext())

    assert len(result.executions) == len(build_full_rule_batch()), (
        "every evaluator in the batch must appear in the run summary"
    )


def test_real_batch_does_not_error_on_an_empty_context():
    """An empty corpus must not make any rule raise.

    This is a regression pin for the DEF-024 premise. If a future change makes a
    rule crash on empty input, containment would hide it and this test is the only
    thing that surfaces it.
    """
    result = evaluate_all_rules_detailed(RuleContext())

    assert not result.failed_rules, "; ".join(
        f"{e.rule_name}: {e.error_type}: {e.error_message}" for e in result.failed_rules
    )


def test_batch_composition_is_still_deduplicated():
    """The containment change must not disturb composition."""
    names = [e.__name__ for e in build_full_rule_batch()]
    assert len(names) == len(set(names)), "an evaluator is composed twice"


def test_findings_only_helper_delegates_to_the_isolating_path():
    """`evaluate_all_rules` must not become a second, fragile implementation.

    If it re-derives its own loop, the containment guarantee silently applies to
    only one of the two entry points.
    """
    context = RuleContext()
    assert evaluate_all_rules(context) == evaluate_all_rules_detailed(context).findings
