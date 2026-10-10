"""Unit tests for check_rule_traceability.py (QUAL-02).

Validates that rule traceability is computed dynamically from codebase parsing,
reports missing legs, and regenerates with one command.
"""

from scripts.check_rule_traceability import (
    ALL_RULE_IDS,
    RuleTraceabilityRow,
    build_traceability_matrix,
    generate_traceability_report,
)


def test_traceability_matrix_covers_all_24_rules():
    rows = build_traceability_matrix()
    assert len(rows) == 24
    rule_ids = [r.rule_id for r in rows]
    assert rule_ids == ALL_RULE_IDS


def test_traceability_matrix_dynamic_structure():
    rows = build_traceability_matrix()
    for row in rows:
        assert isinstance(row, RuleTraceabilityRow)
        assert row.rule_id.startswith("EXC-")
        if row.is_complete:
            assert row.implementing_module is not None
            assert row.proving_test_file is not None
            assert row.evidence_artifact is not None
            assert len(row.missing_legs) == 0
        else:
            assert len(row.missing_legs) > 0


def test_traceability_report_generation():
    rows = build_traceability_matrix()
    report = generate_traceability_report(rows)
    assert "# Rule Traceability Matrix (QUAL-02)" in report
    assert "EXC-001" in report
    assert "EXC-024" in report
