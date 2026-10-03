"""
Unit tests for Exception Owner Auto-Assign Resolver (per doc 06 & task requirements).
Covers mapping hits, misses (unassigned without false guessing), and manual override precedence.
"""

import pytest
from app.engine.exceptions.owner_resolver import resolve_exception_owner


def test_owner_resolver_cost_centre_hit():
    # Step 1: Cost Centre CC-100 maps to Ramesh Kumar
    name, role, manual = resolve_exception_owner(
        rule_id="EXC-001",
        cost_center_code="CC-100",
        account_code="9999",
        rule_default_role="FP&A Analyst",
    )
    assert name == "Ramesh Kumar"
    assert "Cost Centre Owner" in role
    assert manual is False


def test_owner_resolver_account_prefix_hit():
    # Step 2: Account prefix 54 maps to Pooja Deshmukh (GL Accountant)
    name, role, manual = resolve_exception_owner(
        rule_id="EXC-002",
        cost_center_code="CC-999",  # unknown cost centre
        account_code="5400",
        rule_default_role="FP&A Analyst",
    )
    assert name == "Pooja Deshmukh"
    assert "GL Accountant" in role
    assert manual is False


def test_owner_resolver_rule_default_role_hit():
    # Step 3: Rule default role hit when cost centre & account prefix unknown
    name, role, manual = resolve_exception_owner(
        rule_id="EXC-003",
        cost_center_code="CC-999",
        account_code="9999",
        rule_default_role="Accounts Payable",
    )
    assert name == "Vikram Patel"
    assert "Accounts Payable" in role
    assert manual is False


def test_owner_resolver_miss_returns_unassigned():
    # Step 6: Misses return Unassigned with no false owner guesses
    name, role, manual = resolve_exception_owner(
        rule_id="EXC-999",
        cost_center_code=None,
        account_code=None,
        rule_default_role="Unassigned",
    )
    assert name == "Unassigned"
    assert role == "Unassigned"
    assert manual is False


def test_owner_resolver_manual_override_precedence():
    # Manual override takes absolute precedence over auto-assign mapping
    name, role, manual = resolve_exception_owner(
        rule_id="EXC-001",
        cost_center_code="CC-100",
        account_code="5400",
        rule_default_role="FP&A Analyst",
        manual_override_owner="Custom Manager",
    )
    assert name == "Custom Manager"
    assert manual is True
