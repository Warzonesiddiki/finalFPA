"""D-15 part 2: floor-raising tests for app/engine/calc/math.py.

Targets previously uncovered lines/branches with concrete spec values
(CALC-003..013, CALC-020..027, CALC-030..033, KPI-001..012).
"""

from decimal import Decimal

import pytest

from app.engine.calc.math import (
    KPI,
    DisplayScale,
    Favourability,
    GroupingFormat,
    NegativeFormat,
    PeriodFact,
    RatioResult,
    RatioState,
    aggregate_mtd,
    aggregate_ttm,
    aggregate_ytd,
    calculate_expense_growth_pct,
    calculate_favourability,
    calculate_forecast_accuracy_ratio,
    calculate_kpi,
    calculate_line_variance_pct,
    calculate_mape_lite,
    calculate_period_aggregations,
    calculate_pp_variance,
    calculate_revenue_growth_pct,
    calculate_variance_pct_ratio,
    check_sum_of_rounded_discrepancy,
    format_currency,
    format_favourability,
    format_number,
    format_percent,
    format_percentage_points,
    get_account_direction,
    quantize_percent,
    quantize_ratio,
    safe_divide,
)


class TestRatioResultStates:
    def test_is_valid_is_null_is_undefined(self):
        valid = RatioResult(value=Decimal("0.400000"), state=RatioState.VALID, display="40.0%")
        assert valid.is_valid is True
        assert valid.is_null is False
        assert valid.is_undefined is False

        null = RatioResult(value=None, state=RatioState.NULL, display="—")
        assert null.is_valid is False
        assert null.is_null is True
        assert null.is_undefined is False

        undef = RatioResult(value=None, state=RatioState.UNDEFINED, display="n/a")
        assert undef.is_valid is False
        assert undef.is_null is False
        assert undef.is_undefined is True


class TestQuantizers:
    def test_quantize_ratio_float_input(self):
        # CALC-030: float input coerced via str to avoid binary artefacts
        assert quantize_ratio(0.1) == Decimal("0.100000")
        assert quantize_ratio("0.123456789") == Decimal("0.123457")

    def test_quantize_percent_all_input_types(self):
        # CALC-030: percentages stored at 1 dp, half-up
        assert quantize_percent("5.44") == Decimal("5.4")
        assert quantize_percent("5.45") == Decimal("5.5")
        assert quantize_percent(5.45) == Decimal("5.5")
        assert quantize_percent(5) == Decimal("5.0")
        assert quantize_percent(Decimal("5.44")) == Decimal("5.4")


class TestSafeDivideEdges:
    def test_float_inputs(self):
        res = safe_divide(1.5, 2.0)
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.750000")
        assert res.display == "75.0%"

    def test_non_percentage_display_uses_multiplier(self):
        res = safe_divide(3, 2, is_percentage_display=False)
        assert res.state == RatioState.VALID
        assert res.value == Decimal("1.500000")
        assert res.display == "1.5×"

    def test_negative_py_uses_absolute_denominator(self):
        # Expense growth off a negative PY base (credit balance): 210000 / |-100000|
        res = calculate_expense_growth_pct(actual="110000", py_actual="-100000")
        assert res.state == RatioState.VALID
        assert res.value == Decimal("2.100000")
        assert res.display == "210.0%"

    def test_revenue_growth_negative_py(self):
        res = calculate_revenue_growth_pct(actual="50000", py_actual="-100000")
        assert res.value == Decimal("1.500000")


class TestDirectionAndFavourability:
    def test_direction_case_and_whitespace_insensitive(self):
        assert get_account_direction("  REVENUE ") == "higher_is_favourable"
        assert get_account_direction("Income") == "higher_is_favourable"
        assert get_account_direction("Cost of Goods Sold") == "lower_is_favourable"
        assert get_account_direction("OPEX") == "lower_is_favourable"
        assert get_account_direction("Balance Sheet") == "neutral"

    def test_unknown_account_type_is_neutral(self):
        assert get_account_direction("mystery-xyz-999") == "neutral"

    def test_string_direction_inputs(self):
        assert (
            calculate_favourability("120", "100", "higher_is_favourable")
            == Favourability.FAVOURABLE
        )
        assert (
            calculate_favourability("90", "100", "lower_is_favourable") == Favourability.FAVOURABLE
        )
        assert (
            calculate_favourability("100", "100", "higher_is_favourable") == Favourability.NEUTRAL
        )

    def test_defensive_fallback_direction_returns_neutral(self):
        # Non-enum direction falls through to the defensive neutral return
        assert calculate_favourability(100, 50, direction=None) == Favourability.NEUTRAL
        assert calculate_favourability(50, 100, direction=None) == Favourability.NEUTRAL


class TestFormatFavourability:
    def test_table_neutral(self):
        assert format_favourability(Favourability.NEUTRAL, "table") == "Neutral"

    def test_simple_style_from_enum_and_string(self):
        assert format_favourability(Favourability.FAVOURABLE, "simple") == "Favourable"
        assert format_favourability("unfavourable", "simple") == "Unfavourable"
        assert format_favourability("neutral", "simple") == "Neutral"

    def test_excel_style(self):
        assert format_favourability(Favourability.FAVOURABLE, "excel") == "Fav"
        assert format_favourability(Favourability.UNFAVOURABLE, "excel") == "Adv"
        assert format_favourability(Favourability.NEUTRAL, "excel") == "—"


class TestAggregationAccountFilter:
    @pytest.fixture
    def mixed_facts(self):
        return [
            PeriodFact(
                fiscal_year=2026, period_number=9, net_amount=Decimal("100.00"), account_code="4000"
            ),
            PeriodFact(
                fiscal_year=2026, period_number=9, net_amount=Decimal("999.00"), account_code="5000"
            ),
            PeriodFact(
                fiscal_year=2026, period_number=8, net_amount=Decimal("200.00"), account_code="4000"
            ),
        ]

    def test_mtd_account_filter(self, mixed_facts):
        assert aggregate_mtd(mixed_facts, 2026, 9, account_code="4000") == Decimal("100.00")
        assert aggregate_mtd(mixed_facts, 2026, 9, account_code="5000") == Decimal("999.00")
        assert aggregate_mtd(mixed_facts, 2026, 9) == Decimal("1099.00")

    def test_ytd_account_filter(self, mixed_facts):
        assert aggregate_ytd(mixed_facts, 2026, 9, account_code="4000") == Decimal("300.00")
        assert aggregate_ytd(mixed_facts, 2026, 9, account_code="NOPE") == Decimal("0.00")

    def test_ttm_account_filter(self, mixed_facts):
        total, n, label = aggregate_ttm(mixed_facts, 2026, 9, account_code="4000")
        assert total == Decimal("300.00")
        assert n == 2
        total_all, n_all, _ = aggregate_ttm(mixed_facts, 2026, 9)
        assert total_all == Decimal("1299.00")
        assert n_all == 2  # two distinct loaded periods (P08, P09)
        assert label.startswith("TTM (")


class TestCalculatePeriodAggregations:
    def test_all_windows_at_once(self):
        facts = [
            PeriodFact(
                fiscal_year=2025, period_number=1, net_amount=Decimal("100.00"), account_code="4000"
            ),
            PeriodFact(
                fiscal_year=2025, period_number=2, net_amount=Decimal("100.00"), account_code="4000"
            ),
            PeriodFact(
                fiscal_year=2025,
                period_number=3,
                net_amount=Decimal("1000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026, period_number=1, net_amount=Decimal("100.00"), account_code="4000"
            ),
            PeriodFact(
                fiscal_year=2026, period_number=2, net_amount=Decimal("200.00"), account_code="4000"
            ),
            PeriodFact(
                fiscal_year=2026, period_number=3, net_amount=Decimal("300.00"), account_code="4000"
            ),
        ]
        agg = calculate_period_aggregations(facts, fiscal_year=2026, period_number=3)
        assert agg.mtd == Decimal("300.00")
        assert agg.ytd == Decimal("600.00")
        assert agg.py_mtd == Decimal("1000.00")
        assert agg.py_ytd == Decimal("1200.00")
        # Only 3 periods loaded (FY25-P03 is 12 offsets back, outside the window)
        assert agg.ttm == Decimal("600.00")
        assert agg.ttm_periods_count == 3
        assert agg.ttm_label == "TTM (3 of 12 periods)"

    def test_account_scoped_aggregations(self):
        facts = [
            PeriodFact(
                fiscal_year=2026, period_number=3, net_amount=Decimal("300.00"), account_code="4000"
            ),
            PeriodFact(
                fiscal_year=2026, period_number=3, net_amount=Decimal("700.00"), account_code="5000"
            ),
        ]
        agg = calculate_period_aggregations(
            facts, fiscal_year=2026, period_number=3, account_code="4000"
        )
        assert agg.mtd == Decimal("300.00")
        assert agg.ytd == Decimal("300.00")


class TestKpiRegistryDispatch:
    def test_kpi_001_through_006(self):
        r1 = calculate_kpi(KPI.KPI_001, revenue="1080000.00", cogs="648000.00")
        assert r1.value == Decimal("0.400000")
        assert r1.display == "40.0%"

        r2 = calculate_kpi("KPI-002", opex="355000.00", revenue="1080000.00")
        assert r2.value == Decimal("0.328704")

        r3 = calculate_kpi(KPI.KPI_003, ytd_actual="3095801.00", annual_budget="12000000.00")
        assert r3.value == Decimal("0.257983")

        r4 = calculate_kpi(KPI.KPI_004, actual="1080000.00", py_actual="950000.00")
        assert r4.value == Decimal("0.136842")

        r5 = calculate_kpi(KPI.KPI_005, actual="1080000.00", budget="1000000.00")
        assert r5.value == Decimal("0.080000")
        assert r5.display == "8.0%"

        r6 = calculate_kpi(KPI.KPI_006, actual="105000", forecast="100000")
        assert r6.value == Decimal("0.047619")
        assert r6.display == "4.8%"

    def test_kpi_006_period_pairs_path(self):
        pairs = [
            (Decimal("1080000.00"), Decimal("1050000.00")),
            (Decimal("1020500.55"), Decimal("1032500.55")),
        ]
        res = calculate_kpi(KPI.KPI_006, period_pairs=pairs)
        assert res.state == RatioState.VALID

    def test_line_variance_and_forecast_accuracy_direct(self):
        assert calculate_line_variance_pct("1080000.00", "1000000.00").value == Decimal("0.080000")
        fa = calculate_forecast_accuracy_ratio("105000", "100000")
        assert fa.value == Decimal("0.047619")

    def test_variance_ratio_float_inputs(self):
        res = calculate_variance_pct_ratio(1080000.0, 1000000.0)
        assert res.value == Decimal("0.080000")

    def test_pp_variance_float_inputs(self):
        assert calculate_pp_variance(40.0, 38.5) == Decimal("1.5")

    def test_unknown_kpi_raises(self):
        # Non-str, non-KPI input falls through the registry to the guard raise
        with pytest.raises(ValueError, match="Unknown KPI ID: 999"):
            calculate_kpi(999, revenue="1")

    def test_mape_lite_empty_is_null(self):
        res, excluded = calculate_mape_lite([])
        assert res.state == RatioState.NULL
        assert res.display == "—"
        assert excluded == 0

    def test_mape_lite_all_zero_actuals_is_undefined(self):
        res, excluded = calculate_mape_lite([(Decimal("0"), Decimal("100"))])
        assert res.state == RatioState.UNDEFINED
        assert res.display == "n/a"
        assert excluded == 1


class TestNumberFormattingEdges:
    def test_small_amounts_no_grouping(self):
        assert format_number(Decimal("999.99")) == "999.99"
        assert format_number(Decimal("999.99"), grouping=GroupingFormat.INDIAN) == "999.99"
        assert format_number(Decimal("12.50"), grouping=GroupingFormat.INDIAN) == "12.50"

    def test_indian_grouping_crore_scale(self):
        assert (
            format_number(Decimal("12345678"), grouping=GroupingFormat.INDIAN) == "1,23,45,678.00"
        )

    def test_float_input(self):
        assert format_number(3095801.456) == "3,095,801.46"

    def test_negative_minus_format(self):
        assert format_number(-25000, negative_format=NegativeFormat.MINUS) == "-25,000.00"

    def test_negative_both_format_uses_parentheses(self):
        assert format_number(-25000, negative_format=NegativeFormat.BOTH) == "(25,000.00)"

    def test_include_plus(self):
        assert format_number(25000, include_plus=True) == "+25,000.00"
        assert format_number(0, include_plus=True) == "0.00"

    def test_zero_decimal_places(self):
        assert format_number("1234.5", decimal_places=0) == "1,235"
        assert format_number("1234.4", decimal_places=0) == "1,234"


class TestCurrencyFormattingEdges:
    def test_float_input(self):
        assert format_currency(25000.0, currency_symbol="₹") == "₹ 25,000.00"

    def test_crores_scale(self):
        assert (
            format_currency(Decimal("3095801.00"), currency_symbol="₹", scale=DisplayScale.CRORES)
            == "₹ in crores 0.31"
        )

    def test_millions_scale(self):
        assert (
            format_currency(Decimal("3095801.00"), currency_symbol="₹", scale=DisplayScale.MILLIONS)
            == "₹ in millions 3.10"
        )

    def test_empty_symbol_returns_bare_number(self):
        assert format_currency(Decimal("25000"), currency_symbol="") == "25,000.00"


class TestPercentFormattingEdges:
    def test_none_and_placeholders(self):
        assert format_percent(None) == "—"
        assert format_percent("—") == "—"
        assert format_percent("n/a") == "n/a"

    def test_float_input(self):
        assert format_percent(0.084) == "8.4%"

    def test_include_sign(self):
        assert format_percent("0.08", include_sign=True) == "+8.0%"
        assert format_percent("-0.066", include_sign=True) == "-6.6%"

    def test_percentage_points_float_input(self):
        assert format_percentage_points(1.56) == "+1.6 pp"
        assert format_percentage_points(-2.345, decimal_places=2) == "-2.35 pp"

    def test_sum_of_rounded_no_discrepancy_value(self):
        has_disc, diff, note = check_sum_of_rounded_discrepancy(
            [Decimal("10.12"), Decimal("20.35")], Decimal("30.47"), 2
        )
        assert has_disc is False
        assert diff == Decimal("0.00")
        assert note is None

    def test_sum_of_rounded_float_inputs(self):
        has_disc, diff, note = check_sum_of_rounded_discrepancy([10.12, 20.35], 30.47, 2)
        assert has_disc is False
        assert note is None
