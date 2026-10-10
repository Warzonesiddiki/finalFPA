"""Unit tests for Forecast Scenarios and Accuracy Evaluation Engine.

Per docs/07_FORECAST_METHODS_SPEC.md §6-§10 and docs/05_CALCULATION_SPEC.md §9.2.
"""

from decimal import Decimal

from app.engine.forecast.scenarios import (
    FactForecastRow,
    FactForecastVersion,
    ForecastVersionStatus,
    ScenarioGenerator,
    calculate_absolute_error,
    calculate_signed_error,
    evaluate_forecast_accuracy,
)


def test_scenario_adjustment_math():
    """CALC-065: base * (1 + adj)."""
    gen = ScenarioGenerator()
    base_row = FactForecastRow(
        period_id=1,
        account_id=101,
        amount=Decimal("100000.00"),
        account_group="revenue",
    )
    # Generate best (+5% revenue) and worst (-5% revenue)
    best_ver = gen.generate_scenario(
        base_lines=[base_row],
        scenario_id="best",
        version_no=1,
        period_generated_for=1,
    )
    assert len(best_ver.lines) == 1
    assert best_ver.lines[0].amount == Decimal("105000.00")

    worst_ver = gen.generate_scenario(
        base_lines=[base_row],
        scenario_id="worst",
        version_no=1,
        period_generated_for=1,
    )
    assert worst_ver.lines[0].amount == Decimal("95000.00")


def test_forecast_version_lifecycle():
    """Draft -> Locked -> Superseded state transitions."""
    v = FactForecastVersion(
        forecast_version_id="VER-001",
        version_no=1,
        scenario_id="base",
        period_generated_for=9,
        status=ForecastVersionStatus.DRAFT,
    )
    assert v.status == ForecastVersionStatus.DRAFT
    assert not v.is_locked

    v.lock(locked_by="Lead Analyst")
    assert v.status == ForecastVersionStatus.LOCKED
    assert v.is_locked
    assert v.locked_by == "Lead Analyst"

    v.supersede()
    assert v.status == ForecastVersionStatus.SUPERSEDED


def test_forecast_accuracy_calculations():
    """CALC-066 through CALC-069 formulas."""
    actual = Decimal("105000.00")
    forecast = Decimal("100000.00")

    # Signed error = actual - forecast = 5,000
    err = calculate_signed_error(actual, forecast)
    assert err == Decimal("5000.00")

    # Absolute error = 5,000
    abs_err = calculate_absolute_error(actual, forecast)
    assert abs_err == Decimal("5000.00")

    # Accuracy evaluate
    pairs = [
        ("FY26-P01", Decimal("100000.00"), Decimal("95000.00")),
        ("FY26-P02", Decimal("120000.00"), Decimal("130000.00")),
    ]
    report = evaluate_forecast_accuracy(pairs)
    assert report is not None
    assert report.periods_compared == 2
    assert report.signed_bias == Decimal("-2500.00")  # (+5000 + -10000)/2 = -2500
