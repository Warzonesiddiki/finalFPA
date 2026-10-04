from app.engine.rules.batch import (
    build_full_rule_batch,
    catalog_rule_coverage,
    evaluate_all_rules,
)
from app.engine.rules.rules_01_08 import RuleContext

EXPECTED_CATALOG_RULE_COVERAGE = {
    "EXC-001": "evaluate_catalog_exc_001",
    "EXC-002": "evaluate_catalog_exc_002",
    "EXC-003": "evaluate_catalog_exc_003",
    "EXC-004": "evaluate_exc_002",
    "EXC-005": "evaluate_exc_003",
    "EXC-006": "evaluate_catalog_exc_006",
    "EXC-007": "evaluate_exc_001",
    "EXC-008": "evaluate_catalog_exc_008",
    "EXC-009": "evaluate_exc_004",
    "EXC-010": "evaluate_exc_010",
    "EXC-011": "evaluate_exc_011",
    "EXC-012": "evaluate_exc_005",
    "EXC-013": "evaluate_exc_013",
    "EXC-014": "evaluate_exc_014",
    "EXC-015": "evaluate_exc_006",
    "EXC-016": "evaluate_exc_016",
    "EXC-017": "evaluate_exc_007",
    "EXC-018": "evaluate_exc_008",
    "EXC-019": "evaluate_exc_019",
    "EXC-020": "evaluate_exc_020",
    "EXC-021": "evaluate_exc_021",
    "EXC-022": "evaluate_exc_022",
    "EXC-023": "evaluate_exc_023",
    "EXC-024": "evaluate_exc_024",
}


def test_build_full_rule_batch():
    batch = build_full_rule_batch()
    assert isinstance(batch, tuple)
    assert len(batch) == 24


def test_catalog_rule_coverage_uses_catalog_ids_not_engine_id_aliases():
    """Catalog coverage must not infer catalog IDs from legacy evaluator names."""
    assert catalog_rule_coverage() == EXPECTED_CATALOG_RULE_COVERAGE


def test_evaluate_all_rules():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[],
        budgets={},
        config={},
    )
    findings = evaluate_all_rules(ctx)
    assert isinstance(findings, list)
