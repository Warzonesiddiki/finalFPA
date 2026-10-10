"""Unit tests for Phase 2 Calculation Foundation.

Tests trace to:
- docs/05_CALCULATION_SPEC.md §1 through §6
- Fixtures F1..F11, F14d
- Formulas CALC-003..006 (Period aggregations & windows)
- Formula CALC-007 (Canonical sign conventions)
- Formula CALC-010 (Variance)
- Formula CALC-011 (Variance % with null vs undefined states)
- Formula CALC-012 (Direction-aware favourability)
- Formula CALC-013 (Percentage points vs relative percent)
- Formula CALC-020..027, KPI-001..012 (Ratio and KPI library)
- Formula CALC-030..033 (Rounding, sum-of-rounded rule, scale, negative parentheses)
"""

from decimal import Decimal

import pytest

from app.engine.calc import (
    KPI,
    Direction,
    DisplayScale,
    Favourability,
    GroupingFormat,
    PeriodFact,
    RatioResult,
    RatioState,
    aggregate_mtd,
    aggregate_py_mtd,
    aggregate_py_ytd,
    aggregate_ttm,
    aggregate_ytd,
    calculate_budget_burn_pct,
    calculate_favourability,
    calculate_gross_margin_pct,
    calculate_kpi,
    calculate_mape_lite,
    calculate_opex_ratio,
    calculate_percentage_point_variance,
    calculate_pp_variance,
    calculate_revenue_growth_pct,
    calculate_variance,
    calculate_variance_pct_ratio,
    check_sum_of_rounded_discrepancy,
    format_currency,
    format_favourability,
    format_number,
    format_parentheses,
    format_percentage_points,
    get_account_direction,
    quantize_money,
)


class TestCanonicalVarianceAndFavourability:
    """Tests for CALC-010, CALC-011, CALC-012, and fixtures F1..F5."""

    def test_fixture_f1_revenue_favourable(self):
        """F1: Revenue line where actual > budget is favourable."""
        actual = Decimal("1080000.00")
        budget = Decimal("1000000.00")

        # Variance
        var = calculate_variance(actual, budget)
        assert var == Decimal("80000.00")

        # Variance % ratio
        res = calculate_variance_pct_ratio(actual, budget)
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.080000")
        assert res.display == "8.0%"

        # Direction and favourability
        direction = get_account_direction("revenue")
        assert direction == Direction.HIGHER_IS_FAVOURABLE

        fav = calculate_favourability(actual, budget, direction)
        assert fav == Favourability.FAVOURABLE
        assert format_favourability(fav, "table") == "Favourable (▲)"
        assert format_favourability(fav, "compact") == "Fav"

    def test_fixture_f2_expense_under_budget_favourable(self):
        """F2: Expense line where actual < budget is favourable (classic trap)."""
        actual = Decimal("355000.00")
        budget = Decimal("380000.00")

        var = calculate_variance(actual, budget)
        assert var == Decimal("-25000.00")

        res = calculate_variance_pct_ratio(actual, budget)
        assert res.state == RatioState.VALID
        assert res.value == Decimal("-0.065789")
        assert res.display == "-6.6%"

        direction = get_account_direction("expense")
        assert direction == Direction.LOWER_IS_FAVOURABLE

        fav = calculate_favourability(actual, budget, direction)
        assert fav == Favourability.FAVOURABLE
        assert format_favourability(fav, "table") == "Favourable (▲)"
        assert format_favourability(fav, "compact") == "Fav"

    def test_fixture_f3_expense_over_budget_unfavourable(self):
        """F3: Expense line where actual > budget is unfavourable."""
        actual = Decimal("245000.00")
        budget = Decimal("200000.00")

        var = calculate_variance(actual, budget)
        assert var == Decimal("45000.00")

        res = calculate_variance_pct_ratio(actual, budget)
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.225000")
        assert res.display == "22.5%"

        fav = calculate_favourability(actual, budget, Direction.LOWER_IS_FAVOURABLE)
        assert fav == Favourability.UNFAVOURABLE
        assert format_favourability(fav, "table") == "Unfavourable (▼)"
        assert format_favourability(fav, "compact") == "Adv"

    def test_fixture_f4_zero_budget_nonzero_actual(self):
        """F4: Budget = 0, Actual != 0 -> variance % is undefined ('n/a')."""
        actual = Decimal("15000.00")
        budget = Decimal("0.00")

        var = calculate_variance(actual, budget)
        assert var == Decimal("15000.00")

        res = calculate_variance_pct_ratio(actual, budget)
        assert res.state == RatioState.UNDEFINED
        assert res.value is None
        assert res.display == "n/a"

        fav = calculate_favourability(actual, budget, Direction.LOWER_IS_FAVOURABLE)
        assert fav == Favourability.UNFAVOURABLE

    def test_fixture_f5_zero_budget_and_zero_actual(self):
        """F5: Budget = 0, Actual = 0 -> variance % is null ('—'), neutral."""
        actual = Decimal("0.00")
        budget = Decimal("0.00")

        var = calculate_variance(actual, budget)
        assert var == Decimal("0.00")

        res = calculate_variance_pct_ratio(actual, budget)
        assert res.state == RatioState.NULL
        assert res.value is None
        assert res.display == "—"

        fav = calculate_favourability(actual, budget, Direction.LOWER_IS_FAVOURABLE)
        assert fav == Favourability.NEUTRAL
        assert format_favourability(fav, "compact") == "—"

    def test_balance_sheet_and_memo_are_always_neutral(self):
        """Balance sheet and statistical accounts always have neutral favourability."""
        for acc_type in ("asset", "liability", "equity", "memo", "statistical"):
            direction = get_account_direction(acc_type)
            assert direction == Direction.NEUTRAL
            fav = calculate_favourability(Decimal("100"), Decimal("50"), direction)
            assert fav == Favourability.NEUTRAL


class TestPeriodAggregations:
    """Tests for CALC-003 .. CALC-006, Fixtures F6, F7, F8."""

    @pytest.fixture
    def sample_facts(self):
        """Sample periods from F6, F7, and F8."""
        return [
            # FY25
            PeriodFact(
                fiscal_year=2025,
                period_number=7,
                net_amount=Decimal("950000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2025,
                period_number=8,
                net_amount=Decimal("960000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2025,
                period_number=9,
                net_amount=Decimal("970000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2025,
                period_number=10,
                net_amount=Decimal("900000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2025,
                period_number=11,
                net_amount=Decimal("920000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2025,
                period_number=12,
                net_amount=Decimal("1010000.00"),
                account_code="4000",
            ),
            # FY26
            PeriodFact(
                fiscal_year=2026,
                period_number=1,
                net_amount=Decimal("880000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=2,
                net_amount=Decimal("890000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=3,
                net_amount=Decimal("940000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=4,
                net_amount=Decimal("960000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=5,
                net_amount=Decimal("975000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=6,
                net_amount=Decimal("985000.00"),
                account_code="4000",
            ),
            # F6 / F7 FY26-P07, P08, P09
            PeriodFact(
                fiscal_year=2026,
                period_number=7,
                net_amount=Decimal("1080000.00"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=8,
                net_amount=Decimal("1020500.55"),
                account_code="4000",
            ),
            PeriodFact(
                fiscal_year=2026,
                period_number=9,
                net_amount=Decimal("995300.45"),
                account_code="4000",
            ),
        ]

    def test_aggregate_mtd(self, sample_facts):
        """MTD returns only selected period amount."""
        mtd = aggregate_mtd(sample_facts, fiscal_year=2026, period_number=9)
        assert mtd == Decimal("995300.45")

    def test_aggregate_ytd(self, sample_facts):
        """YTD returns sum of periods 1..9 of fiscal year 2026."""
        ytd = aggregate_ytd(sample_facts, fiscal_year=2026, period_number=9)
        # 880k+890k+940k+960k+975k+985k + 1080k + 1020500.55 + 995300.45
        expected = (
            Decimal("880000.00")
            + Decimal("890000.00")
            + Decimal("940000.00")
            + Decimal("960000.00")
            + Decimal("975000.00")
            + Decimal("985000.00")
            + Decimal("1080000.00")
            + Decimal("1020500.55")
            + Decimal("995300.45")
        )
        assert ytd == expected

    def test_aggregate_py_mtd_and_py_ytd(self, sample_facts):
        """PY MTD and PY YTD take prior fiscal year equivalents."""
        py_mtd = aggregate_py_mtd(sample_facts, fiscal_year=2026, period_number=9)
        assert py_mtd == Decimal("970000.00")

        py_ytd = aggregate_py_ytd(sample_facts, fiscal_year=2026, period_number=9)
        # FY25 periods 7, 8, 9 loaded
        assert py_ytd == Decimal("950000.00") + Decimal("960000.00") + Decimal("970000.00")

    def test_fixture_f7_ttm_rolling_12(self, sample_facts):
        """F7: 12 loaded periods sum to 11,555,801.00."""
        ttm_total, n, label = aggregate_ttm(sample_facts, fiscal_year=2026, period_number=9)
        assert n == 12
        assert label == "TTM (12 periods)"
        assert ttm_total == Decimal("11555801.00")

        # Average per period at full precision and quantized
        avg = ttm_total / Decimal(12)
        assert quantize_money(avg) == Decimal("962983.42")

    def test_ttm_partial_window(self, sample_facts):
        """Partial window label when fewer than 12 periods exist."""
        # For FY25-P09, only P07..P09 exist (3 periods)
        ttm_total, n, label = aggregate_ttm(sample_facts, fiscal_year=2025, period_number=9)
        assert n == 3
        assert label == "TTM (3 of 12 periods)"
        assert ttm_total == Decimal("2880000.00")


class TestRatioAndKPILibrary:
    """Tests for KPI-001..KPI-012, CALC-005, CALC-013, and Fixtures F9, F10, F11."""

    def test_fixture_f9_kpi_001_gross_margin_pct(self):
        """KPI-001: Gross Margin % = (Revenue - COGS) / Revenue."""
        res = calculate_gross_margin_pct(revenue="1080000.00", cogs="648000.00")
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.400000")
        assert res.display == "40.0%"

    def test_fixture_f9_kpi_002_opex_ratio(self):
        """KPI-002: Opex ratio = Opex / Revenue."""
        res = calculate_opex_ratio(opex="355000.00", revenue="1080000.00")
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.328704")
        assert res.display == "32.9%"

    def test_fixture_f9_kpi_003_budget_burn_pct(self):
        """KPI-003: Budget burn % = YTD actual / Annual budget."""
        res = calculate_budget_burn_pct(ytd_actual="3095801.00", annual_budget="12000000.00")
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.257983")
        assert res.display == "25.8%"

    def test_fixture_f9_kpi_004_revenue_growth_pct(self):
        """KPI-004: Revenue growth % = (Actual - PY) / |PY|."""
        res = calculate_revenue_growth_pct(actual="1080000.00", py_actual="950000.00")
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.136842")
        assert res.display == "13.7%"

    def test_fixture_f9_zero_denominator_guards(self):
        """F9 guards: revenue = 0 -> 'n/a'; revenue = 0 and cogs = 0 -> '—'."""
        div_zero = calculate_gross_margin_pct(revenue="0.00", cogs="50000.00")
        assert div_zero.state == RatioState.UNDEFINED
        assert div_zero.value is None
        assert div_zero.display == "n/a"

        both_zero = calculate_gross_margin_pct(revenue="0.00", cogs="0.00")
        assert both_zero.state == RatioState.NULL
        assert both_zero.value is None
        assert both_zero.display == "—"

    def test_fixture_f14d_kpi_006_mape_lite(self):
        """KPI-006: MAPE-lite forecast accuracy with zero actual period exclusion."""
        pairs = [
            (Decimal("1080000.00"), Decimal("1050000.00")),
            (Decimal("1020500.55"), Decimal("1032500.55")),
            (Decimal("995300.45"), Decimal("989300.45")),
            (Decimal("0.00"), Decimal("100000.00")),  # Excluded zero period
        ]
        res, excluded_zero_count = calculate_mape_lite(pairs)
        assert excluded_zero_count == 1
        assert res.state == RatioState.VALID
        assert res.value == Decimal("0.015188")
        assert res.display == "1.5%"

    def test_extended_kpis_007_to_012(self):
        """Verify KPI-007 through KPI-012 execution."""
        # KPI-007: Operating margin %
        kpi7 = calculate_kpi(
            KPI.KPI_007, operating_income=Decimal("200000"), revenue=Decimal("1000000")
        )
        assert isinstance(kpi7, RatioResult)
        assert kpi7.value == Decimal("0.200000")
        assert kpi7.display == "20.0%"

        # KPI-008: Net profit margin %
        kpi8 = calculate_kpi(KPI.KPI_008, net_income=Decimal("150000"), revenue=Decimal("1000000"))
        assert isinstance(kpi8, RatioResult)
        assert kpi8.value == Decimal("0.150000")
        assert kpi8.display == "15.0%"

        # KPI-009: COGS ratio %
        kpi9 = calculate_kpi(KPI.KPI_009, cogs=Decimal("600000"), revenue=Decimal("1000000"))
        assert isinstance(kpi9, RatioResult)
        assert kpi9.value == Decimal("0.600000")
        assert kpi9.display == "60.0%"

        # KPI-010: Expense growth %
        kpi10 = calculate_kpi(KPI.KPI_010, actual=Decimal("110000"), py_actual=Decimal("100000"))
        assert isinstance(kpi10, RatioResult)
        assert kpi10.value == Decimal("0.100000")
        assert kpi10.display == "10.0%"

        # KPI-011: Forecast variance %
        kpi11 = calculate_kpi(KPI.KPI_011, actual=Decimal("105000"), forecast=Decimal("100000"))
        assert isinstance(kpi11, RatioResult)
        assert kpi11.value == Decimal("0.050000")
        assert kpi11.display == "5.0%"

        # KPI-012: Percentage point variance
        kpi12 = calculate_kpi(KPI.KPI_012, actual_pct=Decimal("40.0"), budget_pct=Decimal("38.5"))
        assert kpi12 == Decimal("1.5")

    def test_fixture_f10_and_f11_percentage_points(self):
        """F10 & F11: Ratio variance must be percentage points (pp), not relative %."""
        # F10: 40.0% vs 38.5% = +1.5 pp
        pp10 = calculate_percentage_point_variance(Decimal("40.0"), Decimal("38.5"))
        assert pp10 == Decimal("1.5")
        assert format_percentage_points(pp10) == "+1.5 pp"

        # F11: -1.0% vs -4.0% = +3.0 pp (favourable improvement)
        pp11 = calculate_pp_variance(Decimal("-1.0"), Decimal("-4.0"))
        assert pp11 == Decimal("3.0")
        assert format_percentage_points(pp11) == "+3.0 pp"


class TestFormattingAndDisplayHelpers:
    """Tests for CALC-031, CALC-032, CALC-033: Scale, Indian grouping, Parentheses."""

    def test_indian_digit_grouping(self):
        """Indian digit grouping per §6.4: 30,95,801.00."""
        formatted = format_number(
            Decimal("3095801.00"),
            decimal_places=2,
            grouping=GroupingFormat.INDIAN,
        )
        assert formatted == "30,95,801.00"

    def test_international_digit_grouping(self):
        """International grouping: 3,095,801.00."""
        formatted = format_number(
            Decimal("3095801.00"),
            decimal_places=2,
            grouping=GroupingFormat.INTERNATIONAL,
        )
        assert formatted == "3,095,801.00"

    def test_parentheses_for_negatives(self):
        """Parentheses negative presentation per §6.4: (25,000.00)."""
        formatted = format_parentheses(Decimal("-25000.00"))
        assert formatted == "(25,000.00)"

        positive = format_parentheses(Decimal("25000.00"))
        assert positive == "25,000.00"

    def test_currency_scale_labels_and_values(self):
        """Display scale per §6.3: whole, thousands, lakhs."""
        val = Decimal("3095801.00")

        # Whole units: ₹ 30,95,801.00
        whole = format_currency(
            val, currency_symbol="₹", scale=DisplayScale.WHOLE, grouping=GroupingFormat.INDIAN
        )
        assert whole == "₹ 30,95,801.00"

        # Thousands: ₹ in thousands 3,095.80
        thousands = format_currency(
            val, currency_symbol="₹", scale=DisplayScale.THOUSANDS, grouping=GroupingFormat.INDIAN
        )
        assert thousands == "₹ in thousands 3,095.80"

        # Lakhs: ₹ in lakhs 30.96
        lakhs = format_currency(
            val, currency_symbol="₹", scale=DisplayScale.LAKHS, grouping=GroupingFormat.INDIAN
        )
        assert lakhs == "₹ in lakhs 30.96"

    def test_sum_of_rounded_footnote_trigger(self):
        """F6b: Discrepancy triggers mandatory footnote per CALC-031."""
        # 33.334% + 33.333% + 33.333% = 100.000%
        # Displayed at 1 dp: 33.3% + 33.3% + 33.3% = 99.9%, displayed total = 100.0%
        components = [Decimal("33.334"), Decimal("33.333"), Decimal("33.333")]
        total = Decimal("100.000")

        has_discrepancy, diff, footnote = check_sum_of_rounded_discrepancy(
            components, total, decimal_places=1
        )
        assert has_discrepancy is True
        assert diff == Decimal("0.1")
        assert footnote == "Components may not sum to the total due to rounding."
