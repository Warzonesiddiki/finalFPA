"""Tests for CONST-01 Spec-to-Code Constants Drift Checker."""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.check_spec_constants import (
    CatalogSpec,
    check_spec_constants,
    parse_catalog_specs,
)

ROOT = Path(__file__).resolve().parent.parent.parent
DOC_06 = ROOT / "docs" / "06_EXCEPTION_RULES_CATALOG.md"


def test_parse_catalog_specs():
    """Verify that all 24 rules are dynamically parsed from docs/06."""
    specs = parse_catalog_specs(DOC_06)
    assert len(specs) == 24
    assert "EXC-001" in specs
    assert "EXC-020" in specs
    assert "EXC-024" in specs

    # Verify EXC-020 fields
    e20 = specs["EXC-020"]
    assert e20.rule_name == "Budget coverage gap"
    assert e20.severity.lower() == "medium"
    assert e20.owner_role == "FP&A Analyst"
    assert "company_code" in e20.subject_key_spec


def test_check_spec_constants_clean():
    """Verify that the checker reports 0 on the authentic repo state."""
    rc, issues = check_spec_constants()
    assert rc == 0
    assert issues == []


def test_falsification_perturbed_catalog_fails():
    """Falsification test (acceptance criterion 3): perturbing a rule ID causes failure."""
    specs = parse_catalog_specs(DOC_06)
    # Inject a perturbed specification (e.g. non-existent rule)
    perturbed_specs = dict(specs)
    perturbed_specs["EXC-999"] = CatalogSpec(
        rule_id="EXC-999",
        rule_name="Perturbed Ghost Rule",
        severity="High",
        owner_role="Auditor",
        subject_key_spec="fake_key",
        doc_line=9999,
    )

    with patch("scripts.check_spec_constants.parse_catalog_specs", return_value=perturbed_specs):
        rc, issues = check_spec_constants()
        assert rc != 0
        assert any("EXC-999" in issue for issue in issues)


def test_falsification_missing_exc_020_code_fails(tmp_path):
    """Falsification test: verify that missing or perturbed EXC-020 key in code causes failure."""
    # Create a dummy rules dir without EXC-020's subject key line
    dummy_rules_dir = tmp_path / "rules"
    dummy_rules_dir.mkdir()
    (dummy_rules_dir / "rules_17_24.py").write_text("# empty rules file\n", encoding="utf-8")

    rc, issues = check_spec_constants(rules_path=dummy_rules_dir)
    assert rc != 0
    assert any("EXC-020 code subject key not found" in issue for issue in issues)
