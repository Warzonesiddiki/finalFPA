"""Unit tests for forecast methods per 07_FORECAST_METHODS_SPEC.md and 05_CALCULATION_SPEC.md.

Verifies:
- Method 1: Locked actuals for closed periods (CALC-060, Fixture F14e)
- Method 2: Remaining-budget spread method (CALC-061, Fixture F14a)
- Method 3: Run-rate method (CALC-062, Fixture F14b)
- Method 4: 3-month trailing average (CALC-063, Fixture F14f)
- Manual override handling with mandatory reason logging (CALC-064, Fixture F14g)
- Scenario adjustments (CALC-065, Fixture F14c)
- Accuracy metrics (CALC-066 ... CALC-069, Fixture F14d)
- Method eligibility and resolution cascade (doc 07 §4.1, §5)
"""

from decimal import Decimal
import pytest

from app.engine.forecast.methods import (
    ForecastMethod,
    Scenario,
    PeriodActual,
    ManualOverride,
    calc_locked_actuals,
    calc_remaining_budget,
    calc_run_rate,
    calc_avg_3m,
    calc_manual_override,
    apply_scenario_adjustment,
    calc_signed_error,
    calc_absolute_error,
    calc_signed_bias,
    calc_mape_lite,
    check_method_eligibility,
    resolve_method,
)


# -----------------------------------------------------------------------------
# Golden Fixture F14a: Remaining-budget spread (CALC-061)
# -----------------------------------------------------------------------------

def test_f14a_remaining_budget_spread():
    """Verify Fixture F14a: Annual budget 12M, actuals P01-P09 9.3M, remaining 2.7M / 3 = 900,000.00."""
    annual_budget = Decimal("12000000.00")
    # P01-P09 total = 9,300,000.00
    actuals = [Decimal("9300000.00")]
    open_periods = ["FY26-P10", "FY26-P11", "FY26-P12"]

    results = calc_remaining_budget(
        annual_budget=annual_budget,
        actuals=actuals,
        remaining_periods=open_periods,
    )

    assert len(results) == 3
    for r in results:
        assert r.amount == Decimal("900000.00")
        assert r.amount_stored == Decimal("900000.00")
        assert r.method == ForecastMethod.REMAINING_BUDGET
        assert r.driver_ref["annual_budget"] == "12000000.00"
        assert r.driver_ref["consumed_actuals"] == "9300000.00"
        assert r.driver_ref["remaining_budget"] == "2700000.00"


def test_remaining_budget_guards():
    """Verify remaining budget edge cases: k=0 (year complete) and negative remaining (overspend)."""
    # k = 0 -> no rows generated
    res_k0 = calc_remaining_budget(Decimal("100000.00"), [Decimal("50000.00")], [])
    assert res_k0 == []

    # Negative remaining (overspend signal) -> spread as computed, never clamped
    res_neg = calc_remaining_budget(Decimal("10000.00"), [Decimal("16000.00")], ["P11", "P12"])
    assert len(res_neg) == 2
    assert res_neg[0].amount == Decimal("-3000.00")
    assert res_neg[1].amount == Decimal("-3000.00")


# -----------------------------------------------------------------------------
# Golden Fixture F14b: Run-rate last 3 actual months (CALC-062)
# -----------------------------------------------------------------------------

def test_f14b_run_rate_last_3_months():
    """Verify Fixture F14b: Last 3 actuals sum 3,095,801.00 / 3 -> 1,031,933.67 per period."""
    actuals = [
        PeriodActual("FY26-P07", Decimal("1080000.00")),
        PeriodActual("FY26-P08", Decimal("1020500.55")),
        PeriodActual("FY26-P09", Decimal("995300.45")),
    ]
    open_periods = ["FY26-P10", "FY26-P11", "FY26-P12"]

    results, notice = calc_run_rate(
        actuals=actuals,
        n=3,
        remaining_periods=open_periods,
    )

    assert notice is None
    assert len(results) == 3
    for r in results:
        assert r.amount == Decimal("1031933.67")
        assert r.method == ForecastMethod.RUN_RATE
        assert r.driver_ref["months"] == ["FY26-P07", "FY26-P08", "FY26-P09"]
        assert r.driver_ref["sum"] == "3095801.00"


def test_run_rate_guards_and_clamping():
    """Verify run-rate clamping when loaded periods < N, and rejection when N <= 0 or no actuals."""
    # N > loaded periods: clamped with visible notice
    actuals = [PeriodActual("FY26-P01", Decimal("100.00")), PeriodActual("FY26-P02", Decimal("200.00"))]
    results, notice = calc_run_rate(actuals, n=3, remaining_periods=["FY26-P03"], clamp=True)
    assert notice is not None
    assert "clamped from 3 to 2" in notice
    assert results[0].amount == Decimal("150.00")

    # Ineligible when clamp=False and loaded < N
    with pytest.raises(ValueError, match="Needs at least 3 loaded actual periods"):
        calc_run_rate(actuals, n=3, clamp=False)

    # N <= 0 invalid
    with pytest.raises(ValueError, match="window N must be greater than 0"):
        calc_run_rate(actuals, n=0)

    # Empty actuals
    with pytest.raises(ValueError, match="Needs at least N loaded actual periods"):
        calc_run_rate([], n=3)


# -----------------------------------------------------------------------------
# Golden Fixture F14c: Scenario adjustment (CALC-065)
# -----------------------------------------------------------------------------

def test_f14c_scenario_adjustment():
    """Verify Fixture F14c: Base forecast 1,031,933.666... adjusted by +5% revenue -> 1,083,530.35."""
    base_actuals = [
        PeriodActual("FY26-P07", Decimal("1080000.00")),
        PeriodActual("FY26-P08", Decimal("1020500.55")),
        PeriodActual("FY26-P09", Decimal("995300.45")),
    ]
    base_results, _ = calc_run_rate(base_actuals, n=3, remaining_periods=["FY26-P10"])
    base_p10 = base_results[0]

    # Best scenario (+5% revenue)
    best_p10 = apply_scenario_adjustment(
        base_result=base_p10,
        adjustment_pct=Decimal("0.05"),
        scenario=Scenario.BEST,
    )

    assert best_p10.amount == Decimal("1083530.35")
    assert best_p10.scenario == Scenario.BEST
    assert best_p10.driver_ref["scenario_adjustment_pct"] == "0.05"


# -----------------------------------------------------------------------------
# Golden Fixture F14d: Forecast accuracy metrics (CALC-066 … CALC-069)
# -----------------------------------------------------------------------------

def test_f14d_accuracy_metrics():
    """Verify Fixture F14d: Signed error, absolute error, signed bias +8,000.00, MAPE-lite 1.5%."""
    # Rows from fixture table:
    # P07: Forecast 1,050,000.00, Actual 1,080,000.00 -> error +30,000.00
    # P08: Forecast 1,032,500.55, Actual 1,020,500.55 -> error -12,000.00
    # P09: Forecast 989,300.45, Actual 995,300.45 -> error +6,000.00
    p07_err = calc_signed_error(Decimal("1080000.00"), Decimal("1050000.00"))
    p08_err = calc_signed_error(Decimal("1020500.55"), Decimal("1032500.55"))
    p09_err = calc_signed_error(Decimal("995300.45"), Decimal("989300.45"))

    assert p07_err == Decimal("30000.00")
    assert p08_err == Decimal("-12000.00")
    assert p09_err == Decimal("6000.00")

    assert calc_absolute_error(Decimal("1080000.00"), Decimal("1050000.00")) == Decimal("30000.00")
    assert calc_absolute_error(Decimal("1020500.55"), Decimal("1032500.55")) == Decimal("12000.00")
    assert calc_absolute_error(Decimal("995300.45"), Decimal("989300.45")) == Decimal("6000.00")

    # Signed bias = (+30,000 - 12,000 + 6,000) / 3 = +8,000.00
    bias = calc_signed_bias([p07_err, p08_err, p09_err])
    assert bias == Decimal("8000.00")

    # MAPE-lite = (0.027778 + 0.011759 + 0.006028) / 3 = 0.015188 -> 1.5%
    pairs = [
        (Decimal("1080000.00"), Decimal("1050000.00")),
        (Decimal("1020500.55"), Decimal("1032500.55")),
        (Decimal("995300.45"), Decimal("989300.45")),
    ]
    mape_lite, excluded = calc_mape_lite(pairs)
    assert excluded == 0
    assert mape_lite == Decimal("0.015188")
    # Displayed at 1 dp percentage: 1.5%
    display_pct = (mape_lite * Decimal("100")).quantize(Decimal("0.1"))
    assert display_pct == Decimal("1.5")


def test_mape_lite_zero_actual_exclusion():
    """Verify that periods with actual == 0 are excluded and counted per CALC-069."""
    pairs = [
        (Decimal("1000.00"), Decimal("900.00")),  # 10% error
        (Decimal("0.00"), Decimal("500.00")),     # zero actual -> excluded
    ]
    mape_lite, excluded = calc_mape_lite(pairs)
    assert excluded == 1
    assert mape_lite == Decimal("0.100000")


# -----------------------------------------------------------------------------
# Golden Fixture F14e: Locked actuals (CALC-060)
# -----------------------------------------------------------------------------

def test_f14e_locked_actuals():
    """Verify Fixture F14e: Closed periods P07-P09 locked to actuals; P10 forecast = last locked actual (P09) -> 995,300.45."""
    closed_actuals = [
        PeriodActual("FY26-P07", Decimal("1080000.00"), is_closed=True),
        PeriodActual("FY26-P08", Decimal("1020500.55"), is_closed=True),
        PeriodActual("FY26-P09", Decimal("995300.45"), is_closed=True),
    ]

    # For closed period P08, returns locked actual 1,020,500.55
    res_p08 = calc_locked_actuals(closed_actuals, target_period="FY26-P08")
    assert res_p08.amount == Decimal("1020500.55")
    assert res_p08.is_closed_period is True

    # For open period P10, projects last locked actual (P09 = 995,300.45)
    res_p10 = calc_locked_actuals(closed_actuals, target_period="FY26-P10")
    assert res_p10.amount == Decimal("995300.45")
    assert res_p10.period_code == "FY26-P10"
    assert res_p10.driver_ref["source_period"] == "FY26-P09"


def test_locked_actuals_no_actuals_flag():
    """Verify closed period with no actuals is treated as 0 and flagged as 'no actuals' per CALC-060."""
    period_no_actuals = [PeriodActual("FY26-P01", Decimal("0.00"), is_closed=True, has_actuals=False)]
    res = calc_locked_actuals(period_no_actuals, target_period="FY26-P01")
    assert res.amount == Decimal("0.00")
    assert res.flag == "no actuals"


# -----------------------------------------------------------------------------
# Golden Fixture F14f: 3-month trailing average (CALC-063)
# -----------------------------------------------------------------------------

def test_f14f_avg_3m():
    """Verify Fixture F14f: (1,080,000.00 + 1,020,500.55 + 995,300.45) / 3 = 1,031,933.67."""
    actuals = [
        PeriodActual("FY26-P07", Decimal("1080000.00")),
        PeriodActual("FY26-P08", Decimal("1020500.55")),
        PeriodActual("FY26-P09", Decimal("995300.45")),
    ]
    results, notice = calc_avg_3m(actuals, remaining_periods=["FY26-P10", "FY26-P11", "FY26-P12"])

    assert notice is None
    assert len(results) == 3
    for r in results:
        assert r.amount == Decimal("1031933.67")
        assert r.method == ForecastMethod.AVG_3M


# -----------------------------------------------------------------------------
# Golden Fixture F14g: Manual override (CALC-064)
# -----------------------------------------------------------------------------

def test_f14g_manual_override():
    """Verify Fixture F14g: User enters 1,100,000.00 for P10 with mandatory reason."""
    override = ManualOverride(
        period_code="FY26-P10",
        amount=Decimal("1100000.00"),
        reason="Management pipeline upside expected in Q4",
        author="FD",
    )
    result = calc_manual_override(override)

    assert result.period_code == "FY26-P10"
    assert result.amount == Decimal("1100000.00")
    assert result.method == ForecastMethod.MANUAL
    assert result.is_manual_override is True
    assert result.override_reason == "Management pipeline upside expected in Q4"
    assert result.driver_ref["author"] == "FD"


def test_manual_override_mandatory_reason_enforced():
    """Verify that a manual override without a reason or with blank reason is strictly rejected."""
    with pytest.raises(ValueError, match="mandatory non-empty reason"):
        ManualOverride(period_code="FY26-P10", amount=Decimal("1000.00"), reason="")

    with pytest.raises(ValueError, match="mandatory non-empty reason"):
        ManualOverride(period_code="FY26-P10", amount=Decimal("1000.00"), reason="   ")

    with pytest.raises(ValueError, match="mandatory non-empty reason"):
        calc_manual_override({"period_code": "FY26-P10", "amount": "1000.00", "reason": ""})


# -----------------------------------------------------------------------------
# Resolution Cascade and Eligibility (doc 07 §4.1, §5)
# -----------------------------------------------------------------------------

def test_resolution_cascade_priorities():
    """Verify 3-level resolution: Line pin > Account group > Project default > Fallback."""
    # Line pin wins
    m, _ = resolve_method(
        line_pinned_method=ForecastMethod.MANUAL,
        account_group_method=ForecastMethod.AVG_3M,
        project_default_method=ForecastMethod.RUN_RATE,
    )
    assert m == ForecastMethod.MANUAL

    # Account group wins over project default
    m, _ = resolve_method(
        line_pinned_method=None,
        account_group_method=ForecastMethod.AVG_3M,
        project_default_method=ForecastMethod.RUN_RATE,
        actual_periods_count=3,
    )
    assert m == ForecastMethod.AVG_3M

    # Project default wins when no group/line setting
    m, _ = resolve_method(
        line_pinned_method=None,
        account_group_method=None,
        project_default_method=ForecastMethod.RUN_RATE,
        actual_periods_count=3,
    )
    assert m == ForecastMethod.RUN_RATE


def test_resolution_fallback_on_insufficient_history():
    """Verify fallback order when method is ineligible: manual -> remaining_budget -> not forecast."""
    # Run rate selected with only 1 period history -> falls back to remaining_budget
    m, reason = resolve_method(
        project_default_method=ForecastMethod.RUN_RATE,
        actual_periods_count=1,
        has_budget=True,
        remaining_periods_count=3,
    )
    assert m == ForecastMethod.REMAINING_BUDGET
    assert "Fallback to remaining_budget" in reason

    # No budget either -> not forecast
    m, reason = resolve_method(
        project_default_method=ForecastMethod.RUN_RATE,
        actual_periods_count=1,
        has_budget=False,
        remaining_periods_count=3,
    )
    assert m is None
    assert "Not forecast - insufficient history" in reason
