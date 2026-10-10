"""CLI smoke tests for `fpa exceptions --run`.

`fpa exceptions --run` is the entrypoint named as the NFR-007 measurement target in
14_TESTING_QA_PLAN.md line 85. These tests assert the wiring is correct without
running the full 250k-row scale fixture - the timing assertion lives in
tests/perf/test_rules_perf.py (marked `perf`).

The critical property: the CLI must go through the de-duplicated batch of
implemented evaluators in app.engine/rules.batch, so catalog EXC-009 / EXC-012 /
EXC-015 are not evaluated twice and their findings are not raised twice. The
coverage report must also expose any catalog IDs without an evaluator.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from app.engine.rules import build_full_rule_batch, catalog_rule_coverage
from app.engine.rules.rules_01_08 import RuleContext

# ---------------------------------------------------------------------------
# Batch composition - the de-duplication guarantee
# ---------------------------------------------------------------------------


def test_full_batch_has_no_duplicate_evaluators():
    """Every implemented evaluator appears once in the composed batch."""
    batch = build_full_rule_batch()
    names = [ev.__name__ for ev in batch]
    assert len(names) == len(set(names)), f"duplicate evaluator: {names}"


def test_full_batch_excludes_the_three_reexported_rules():
    """EXC-009 / EXC-012 / EXC-015 come from the 01-08 batch only.

    BATCH_09_16_EVALUATORS re-exports them as evaluate_exc_009/012/015, which
    delegate to evaluate_exc_004/005/006 already present in BATCH_01_08_EVALUATORS.
    Including both would raise every finding for those three rules twice.
    """
    names = {ev.__name__ for ev in build_full_rule_batch()}
    for reexported in ("evaluate_exc_009", "evaluate_exc_012", "evaluate_exc_015"):
        assert reexported not in names

    # Their real implementations are present exactly once.
    for real in ("evaluate_exc_004", "evaluate_exc_005", "evaluate_exc_006"):
        assert real in names


def test_full_batch_wires_all_catalog_rules():
    batch_coverage = catalog_rule_coverage()
    missing = [f"EXC-{i:03d}" for i in range(1, 25) if f"EXC-{i:03d}" not in batch_coverage]

    assert len(batch_coverage) == 24
    assert not missing, f"catalog rules without evaluators: {missing}"


def test_dedup_is_stable_across_calls():
    """The composer is pure - repeated calls yield the same batch."""
    first = [ev.__name__ for ev in build_full_rule_batch()]
    second = [ev.__name__ for ev in build_full_rule_batch()]
    assert first == second


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_project(tmp_path, monkeypatch):
    """Point DatabaseManager at a throwaway project dir.

    Without this the CLI opens the real default project's analytics.duckdb, which
    DuckDB locks exclusively - so the test would either mutate the user's project or
    fail with an IOException when another process (or a teammate's pytest run) holds
    the file. Mirrors the DatabaseManager(tmp_path) convention used elsewhere in
    tests/integration and tests/unit.
    """
    import app.engine.store.db as db_mod

    monkeypatch.setattr(db_mod, "DEFAULT_PROJECT_DIR", tmp_path)
    return tmp_path


def test_cli_exceptions_run_smoke(capsys, monkeypatch, isolated_project):
    """`fpa exceptions --run --json` executes end to end and reports the batch size."""
    from app.cli.main import main

    monkeypatch.setattr(
        "sys.argv",
        ["fpa-copilot", "exceptions", "run", "--period", "FY26-P09", "--json"],
    )
    main()

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert payload["rulesRun"] == 24
    assert payload["catalogRulesCovered"] == 24
    assert payload["period"] == "FY26-P09"
    assert payload["totalFindings"] >= 0
    assert payload["elapsedSeconds"] >= 0


def test_cli_exceptions_run_uses_default_as_of_from_period(capsys, monkeypatch, isolated_project):
    """With no --as-of, the run date comes from the period, not a hardcoded date."""
    from app.cli.main import main

    monkeypatch.setattr(
        "sys.argv",
        ["fpa-copilot", "exceptions", "run", "--period", "FY26-P09", "--json"],
    )
    main()
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    # Same summary keys as the explicit-as_of run; the as_of itself is not echoed,
    # so assert the run completed against FY26-P09 without a caller-supplied date.
    assert payload["period"] == "FY26-P09"
    assert payload["rulesRun"] == 24


def test_cli_exceptions_run_accepts_explicit_as_of(capsys, monkeypatch, isolated_project):
    """An explicit --as-of is honoured and still reports the same batch shape."""
    from app.cli.main import main

    monkeypatch.setattr(
        "sys.argv",
        [
            "fpa-copilot",
            "exceptions",
            "run",
            "--period",
            "FY26-P09",
            "--as-of",
            "2026-10-05",
            "--json",
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["rulesRun"] == 24
    assert payload["totalFindings"] >= 0


def test_cli_exceptions_no_subcommand_prints_usage(capsys, monkeypatch):
    """`fpa exceptions` with no subcommand is a usage message, not a crash."""
    from app.cli.main import main

    monkeypatch.setattr("sys.argv", ["fpa-copilot", "exceptions"])
    main()
    assert "fpa exceptions run" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Findings are not duplicated by the wiring
# ---------------------------------------------------------------------------


def test_deduplicated_run_does_not_duplicate_rule_findings():
    """Two different EXC-009/012/015 rules must not each produce twin findings.

    Runs the whole deduplicated batch over a small synthetic set and asserts no two
    findings share an identity_hash - which is what double-evaluation would cause.
    """
    from app.engine.rules import evaluate_all_rules

    class _Tx:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    base = dict(
        source_row_ref="row_x",
        voucher_no="VCH-X",
        posting_date="2026-09-10",
        company_code="IN01",
        account_code="5100",
        cost_center_code="CC-100",
        project_code=None,
        vendor_code="V-001",
        invoice_no="INV-1",
        description="d",
        debit=Decimal("1000.00"),
        credit=Decimal("0.00"),
        net_amount=Decimal("1000.00"),
        currency_code="INR",
        document_date=None,
    )
    ctx = RuleContext(transactions=[_Tx(**base)], period_id="FY26-P09")

    findings = evaluate_all_rules(ctx)
    hashes = [f.identity_hash for f in findings]
    assert len(hashes) == len(set(hashes)), (
        "duplicate identity_hash in a deduplicated run - a rule was evaluated twice"
    )


def test_evaluate_all_rules_matches_manual_iteration():
    """evaluate_all_rules() is exactly the manual loop over the batch."""
    from app.engine.rules import evaluate_all_rules

    class _Tx:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    tx = _Tx(
        source_row_ref="row_y",
        voucher_no="VCH-Y",
        posting_date="2026-09-11",
        company_code="IN01",
        account_code="5200",
        cost_center_code="CC-101",
        project_code=None,
        vendor_code="V-002",
        invoice_no="INV-2",
        description="d",
        debit=Decimal("2500.00"),
        credit=Decimal("0.00"),
        net_amount=Decimal("2500.00"),
        currency_code="INR",
        document_date=None,
    )
    ctx = RuleContext(transactions=[tx], period_id="FY26-P09")

    manual = []
    for ev in build_full_rule_batch():
        manual.extend(ev(ctx))

    assert [f.identity_hash for f in evaluate_all_rules(ctx)] == [f.identity_hash for f in manual]
