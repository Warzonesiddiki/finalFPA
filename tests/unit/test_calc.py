"""Unit tests for engine calc and CLI commands."""

from decimal import Decimal

from app.engine.calc import (
    calculate_variance,
    calculate_variance_pct,
    quantize_money,
)


def test_quantize_money():
    assert quantize_money("100.456") == Decimal("100.46")
    assert quantize_money("100.454") == Decimal("100.45")
    assert quantize_money(100) == Decimal("100.00")
    assert quantize_money(100.5) == Decimal("100.50")


def test_calculate_variance():
    actual = Decimal("1250000.50")
    budget = Decimal("1000000.00")
    variance = calculate_variance(actual, budget)
    assert variance == Decimal("250000.50")


def test_calculate_variance_pct():
    actual = Decimal("1250000.00")
    budget = Decimal("1000000.00")
    pct = calculate_variance_pct(actual, budget)
    assert pct == Decimal("25.00")


def test_calculate_variance_pct_zero_budget():
    actual = Decimal("50000.00")
    budget = Decimal("0.00")
    assert calculate_variance_pct(actual, budget) is None
