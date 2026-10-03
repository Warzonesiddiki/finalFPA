import pytest
from app.engine.rules.batch import (
    build_full_rule_batch,
    catalog_rule_coverage,
    evaluate_all_rules,
)
from app.engine.rules.rules_01_08 import RuleContext

def test_build_full_rule_batch():
    batch = build_full_rule_batch()
    assert isinstance(batch, tuple)
    assert len(batch) > 0

def test_catalog_rule_coverage():
    cov = catalog_rule_coverage()
    assert isinstance(cov, dict)
    assert "EXC-001" in cov or len(cov) > 0

def test_evaluate_all_rules():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[],
        budgets={},
        config={}
    )
    findings = evaluate_all_rules(ctx)
    assert isinstance(findings, list)
