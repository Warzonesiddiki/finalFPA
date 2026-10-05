"""Engine core calculations and money maths per 05_CALCULATION_SPEC.md.

Owns:
- Canonical sign conventions (Variance = Actual - Budget, net = debit - credit)
- MTD, YTD, PY MTD, PY YTD, and TTM period aggregations (CALC-003 .. CALC-006)
- Direction-aware favourability (CALC-012)
- Percentage points vs percent (CALC-013)
- Ratio and KPI library with zero denominator guards (CALC-020 .. CALC-027, KPI-001 .. KPI-012)
- Rounding, display scale, negative parentheses formatting and currency display helpers (CALC-030 .. CALC-033)
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

# Precision and constant definitions per CALC-007, CALC-030
ZERO = Decimal("0.00")
ZERO_6DP = Decimal("0.000000")
TWO_PLACES = Decimal("0.01")
ONE_PLACE = Decimal("0.1")
SIX_PLACES = Decimal("0.000001")
ONE_HUNDRED = Decimal("100")


class RatioState(str, Enum):
    """Ratio computation outcome states per §4.2 and §5.1."""

    VALID = "valid"
    NULL = "null"  # 0/0: nothing to compare -> displayed as "—"
    UNDEFINED = "undefined"  # x/0: division by zero -> displayed as "n/a"


class Direction(str, Enum):
    """Direction-aware favourability line direction per CALC-012."""

    HIGHER_IS_FAVOURABLE = "higher_is_favourable"
    LOWER_IS_FAVOURABLE = "lower_is_favourable"
    NEUTRAL = "neutral"


class Favourability(str, Enum):
    """Favourability outcome per CALC-012."""

    FAVOURABLE = "favourable"
    UNFAVOURABLE = "unfavourable"
    NEUTRAL = "neutral"


class DisplayScale(int, Enum):
    """Display scale divisor per CALC-032."""

    WHOLE = 1
    THOUSANDS = 1_000
    LAKHS = 100_000
    CRORES = 10_000_000
    MILLIONS = 1_000_000


class NegativeFormat(str, Enum):
    """Negative number presentation format per CALC-033."""

    PARENTHESES = "parentheses"
    MINUS = "minus"
    BOTH = "both"


class GroupingFormat(str, Enum):
    """Digit grouping format per CALC-033."""

    INTERNATIONAL = "international"
    INDIAN = "indian"


class KPI(str, Enum):
    """KPI register per §5.2 and extended KPI library (KPI-001 .. KPI-012)."""

    KPI_001 = "KPI-001"  # Gross margin %
    KPI_002 = "KPI-002"  # Operating expense ratio
    KPI_003 = "KPI-003"  # Budget burn %
    KPI_004 = "KPI-004"  # Revenue growth % (YoY)
    KPI_005 = "KPI-005"  # Variance % (per line)
    KPI_006 = "KPI-006"  # Forecast accuracy (MAPE-lite)
    KPI_007 = "KPI-007"  # Operating margin %
    KPI_008 = "KPI-008"  # Net profit margin %
    KPI_009 = "KPI-009"  # COGS ratio %
    KPI_010 = "KPI-010"  # Expense growth % (YoY)
    KPI_011 = "KPI-011"  # Forecast variance %
    KPI_012 = "KPI-012"  # Percentage point change / variance


@dataclass(frozen=True)
class RatioResult:
    """Result of a guarded ratio computation per §4.2 and §5.1."""

    value: Decimal | None  # Stored at 6 decimal places if valid, None if null/undefined
    state: RatioState
    display: str  # Formatted display string ("40.0%", "—", "n/a")
    description: str = ""

    @property
    def is_valid(self) -> bool:
        return self.state == RatioState.VALID

    @property
    def is_null(self) -> bool:
        return self.state == RatioState.NULL

    @property
    def is_undefined(self) -> bool:
        return self.state == RatioState.UNDEFINED


@dataclass(frozen=True)
class PeriodFact:
    """Fact record for period aggregations per §2.3."""

    fiscal_year: int
    period_number: int
    net_amount: Decimal
    account_code: str | None = None


@dataclass(frozen=True)
class PeriodAggregations:
    """Aggregate window totals for a selected period per CALC-003 .. CALC-006."""

    mtd: Decimal
    ytd: Decimal
    py_mtd: Decimal
    py_ytd: Decimal
    ttm: Decimal
    ttm_periods_count: int
    ttm_label: str


# ---------------------------------------------------------------------------
# Core Quantization & Arithmetic Helpers
# ---------------------------------------------------------------------------


def quantize_money(amount: Decimal | str | int | float) -> Decimal:
    """Quantize money to 2 decimal places using half-up rounding per §6.1."""
    if isinstance(amount, float):
        amount = str(amount)
    return Decimal(amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def quantize_ratio(ratio: Decimal | str | int | float) -> Decimal:
    """Quantize ratio/rate to 6 decimal places using half-up rounding per §6.1."""
    if isinstance(ratio, float):
        ratio = str(ratio)
    return Decimal(ratio).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def quantize_percent(pct: Decimal | str | int | float) -> Decimal:
    """Quantize percentage to 1 decimal place using half-up rounding per §6.1."""
    if isinstance(pct, float):
        pct = str(pct)
    return Decimal(pct).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)


def safe_divide(
    numerator: Decimal | str | int | float,
    denominator: Decimal | str | int | float,
    abs_denominator: bool = False,
    is_percentage_display: bool = True,
) -> RatioResult:
    """Guarded divide implementing §4.2 and §5.1.

    Rules:
    - If denominator > 0 (or != 0): compute ratio at 6 dp.
    - If denominator == 0 and numerator == 0: null -> displayed as "—".
    - If denominator == 0 and numerator != 0: undefined -> displayed as "n/a".
    """
    if isinstance(numerator, float):
        numerator = str(numerator)
    if isinstance(denominator, float):
        denominator = str(denominator)

    num = Decimal(numerator)
    den = Decimal(denominator)

    if abs_denominator:
        den = abs(den)

    if den == Decimal("0"):
        if num == Decimal("0"):
            return RatioResult(value=None, state=RatioState.NULL, display="—")
        return RatioResult(value=None, state=RatioState.UNDEFINED, display="n/a")

    ratio = quantize_ratio(num / den)
    if is_percentage_display:
        display = format_percent(ratio)
    else:
        display = f"{ratio.quantize(ONE_PLACE, rounding=ROUND_HALF_UP)}×"

    return RatioResult(value=ratio, state=RatioState.VALID, display=display)


# ---------------------------------------------------------------------------
# Variance Calculations (CALC-010, CALC-011, CALC-013)
# ---------------------------------------------------------------------------


def calculate_variance(
    actual: Decimal | str | int | float, budget: Decimal | str | int | float
) -> Decimal:
    """Canonical variance = Actual - Budget per CALC-010."""
    act = quantize_money(actual)
    bud = quantize_money(budget)
    return quantize_money(act - bud)


def calculate_variance_pct(actual: Decimal, budget: Decimal) -> Decimal | None:
    """Variance % = (Actual - Budget) / |Budget| quantized to 2 dp percentage.

    Maintains backwards compatibility with existing engine callers.
    Returns None if budget == 0.
    """
    if budget == ZERO:
        return None
    variance = actual - budget
    pct = (variance / abs(budget)) * ONE_HUNDRED
    return pct.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_variance_pct_ratio(
    actual: Decimal | str | int | float,
    budget: Decimal | str | int | float,
) -> RatioResult:
    """Full-spec CALC-011 variance ratio with 6 dp precision and zero-budget guard states."""
    act = Decimal(str(actual) if isinstance(actual, float) else actual)
    bud = Decimal(str(budget) if isinstance(budget, float) else budget)
    variance = act - bud
    return safe_divide(variance, bud, abs_denominator=True, is_percentage_display=True)


def calculate_percentage_point_variance(
    actual_pct: Decimal | str | int | float,
    budget_pct: Decimal | str | int | float,
) -> Decimal:
    """Percentage point variance = Actual % - Budget % per CALC-013.

    Must never be expressed as a relative percentage of a percentage.
    """
    act = Decimal(str(actual_pct) if isinstance(actual_pct, float) else actual_pct)
    bud = Decimal(str(budget_pct) if isinstance(budget_pct, float) else budget_pct)
    return act - bud


def calculate_pp_variance(
    actual_pct: Decimal | str | int | float,
    budget_pct: Decimal | str | int | float,
) -> Decimal:
    """Alias for calculate_percentage_point_variance."""
    return calculate_percentage_point_variance(actual_pct, budget_pct)


# ---------------------------------------------------------------------------
# Direction-Aware Favourability (CALC-012)
# ---------------------------------------------------------------------------


def get_account_direction(account_type: str) -> Direction:
    """Derive direction from account type per §4.3."""
    clean = account_type.strip().lower()
    if clean in ("revenue", "income", "sales"):
        return Direction.HIGHER_IS_FAVOURABLE
    if clean in ("expense", "opex", "cogs", "cost of goods sold", "direct cost"):
        return Direction.LOWER_IS_FAVOURABLE
    if clean in (
        "asset",
        "liability",
        "equity",
        "balance_sheet",
        "balance sheet",
        "memo",
        "statistical",
    ):
        return Direction.NEUTRAL
    return Direction.NEUTRAL


def calculate_favourability(
    actual: Decimal | str | int | float,
    budget: Decimal | str | int | float,
    direction: Direction | str = Direction.HIGHER_IS_FAVOURABLE,
) -> Favourability:
    """Calculate direction-aware favourability per CALC-012.

    Rules:
    - higher_is_favourable: actual > budget -> Fav, actual < budget -> Unfav, equal -> Neutral
    - lower_is_favourable: actual < budget -> Fav, actual > budget -> Unfav, equal -> Neutral
    - neutral: always Neutral
    """
    act = Decimal(str(actual) if isinstance(actual, float) else actual)
    bud = Decimal(str(budget) if isinstance(budget, float) else budget)

    dir_enum = Direction(direction) if isinstance(direction, str) else direction

    if dir_enum == Direction.NEUTRAL:
        return Favourability.NEUTRAL

    if act == bud:
        return Favourability.NEUTRAL

    if dir_enum == Direction.HIGHER_IS_FAVOURABLE:
        return Favourability.FAVOURABLE if act > bud else Favourability.UNFAVOURABLE

    if dir_enum == Direction.LOWER_IS_FAVOURABLE:
        return Favourability.FAVOURABLE if act < bud else Favourability.UNFAVOURABLE

    return Favourability.NEUTRAL


def format_favourability(fav: Favourability | str, style: str = "table") -> str:
    """Format favourability with text and symbol per §4.3.

    favourability is never colour-only:
    - table: "Favourable (▲)", "Unfavourable (▼)", "Neutral"
    - compact / excel: "Fav", "Adv", "—"
    - simple: "Favourable", "Unfavourable", "Neutral"
    """
    val = Favourability(fav) if isinstance(fav, str) else fav
    if style == "table":
        if val == Favourability.FAVOURABLE:
            return "Favourable (▲)"
        if val == Favourability.UNFAVOURABLE:
            return "Unfavourable (▼)"
        return "Neutral"
    if style in ("compact", "excel"):
        if val == Favourability.FAVOURABLE:
            return "Fav"
        if val == Favourability.UNFAVOURABLE:
            return "Adv"
        return "—"
    # simple
    return val.value.capitalize()


# ---------------------------------------------------------------------------
# Period Aggregations: MTD, YTD, PY MTD, PY YTD, TTM (CALC-003 .. CALC-006)
# ---------------------------------------------------------------------------


def aggregate_mtd(
    facts: Iterable[PeriodFact],
    fiscal_year: int,
    period_number: int,
    account_code: str | None = None,
) -> Decimal:
    """MTD = sum(net_amount) where period_id = P per CALC-003."""
    total = ZERO
    for f in facts:
        if f.fiscal_year == fiscal_year and f.period_number == period_number:
            if account_code is None or f.account_code == account_code:
                total += f.net_amount
    return quantize_money(total)


def aggregate_ytd(
    facts: Iterable[PeriodFact],
    fiscal_year: int,
    period_number: int,
    account_code: str | None = None,
) -> Decimal:
    """YTD = sum(net_amount) where fiscal_year = Y and period_number <= P per CALC-004."""
    total = ZERO
    for f in facts:
        if f.fiscal_year == fiscal_year and f.period_number <= period_number:
            if account_code is None or f.account_code == account_code:
                total += f.net_amount
    return quantize_money(total)


def aggregate_py_mtd(
    facts: Iterable[PeriodFact],
    fiscal_year: int,
    period_number: int,
    account_code: str | None = None,
) -> Decimal:
    """PY MTD = sum(net_amount) where fiscal_year = Y - 1 and period_number = P per CALC-005."""
    total = ZERO
    for f in facts:
        if f.fiscal_year == (fiscal_year - 1) and f.period_number == period_number:
            if account_code is None or f.account_code == account_code:
                total += f.net_amount
    return quantize_money(total)


def aggregate_py_ytd(
    facts: Iterable[PeriodFact],
    fiscal_year: int,
    period_number: int,
    account_code: str | None = None,
) -> Decimal:
    """PY YTD = sum(net_amount) where fiscal_year = Y - 1 and period_number <= P per CALC-005."""
    total = ZERO
    for f in facts:
        if f.fiscal_year == (fiscal_year - 1) and f.period_number <= period_number:
            if account_code is None or f.account_code == account_code:
                total += f.net_amount
    return quantize_money(total)


def aggregate_ttm(
    facts: Iterable[PeriodFact],
    fiscal_year: int,
    period_number: int,
    account_code: str | None = None,
    max_periods: int = 12,
    periods_per_year: int = 12,
) -> tuple[Decimal, int, str]:
    """TTM / rolling 12 = sum over the last min(12, n) periods ending at P per CALC-006.

    Returns (ttm_total, loaded_periods_count, window_label).
    """
    target_idx = (fiscal_year * periods_per_year) + (period_number - 1)

    period_totals: dict[tuple[int, int], Decimal] = {}
    for f in facts:
        if account_code is not None and f.account_code != account_code:
            continue
        key = (f.fiscal_year, f.period_number)
        period_totals[key] = period_totals.get(key, ZERO) + f.net_amount

    # Collect up to max_periods backwards
    loaded_periods: list[tuple[int, int]] = []
    for offset in range(max_periods):
        curr_idx = target_idx - offset
        y = curr_idx // periods_per_year
        p = (curr_idx % periods_per_year) + 1
        if (y, p) in period_totals:
            loaded_periods.append((y, p))

    n = len(loaded_periods)
    total = sum((period_totals[k] for k in loaded_periods), ZERO)
    quantized_total = quantize_money(total)

    if n == max_periods:
        label = f"TTM ({max_periods} periods)"
    else:
        label = f"TTM ({n} of {max_periods} periods)"

    return quantized_total, n, label


def calculate_period_aggregations(
    facts: Iterable[PeriodFact],
    fiscal_year: int,
    period_number: int,
    account_code: str | None = None,
    periods_per_year: int = 12,
) -> PeriodAggregations:
    """Calculate all standard period aggregations at once per §2.3."""
    fact_list = list(facts)
    mtd = aggregate_mtd(fact_list, fiscal_year, period_number, account_code)
    ytd = aggregate_ytd(fact_list, fiscal_year, period_number, account_code)
    py_mtd = aggregate_py_mtd(fact_list, fiscal_year, period_number, account_code)
    py_ytd = aggregate_py_ytd(fact_list, fiscal_year, period_number, account_code)
    ttm_total, ttm_n, ttm_label = aggregate_ttm(
        fact_list,
        fiscal_year,
        period_number,
        account_code,
        max_periods=12,
        periods_per_year=periods_per_year,
    )

    return PeriodAggregations(
        mtd=mtd,
        ytd=ytd,
        py_mtd=py_mtd,
        py_ytd=py_ytd,
        ttm=ttm_total,
        ttm_periods_count=ttm_n,
        ttm_label=ttm_label,
    )


# ---------------------------------------------------------------------------
# Ratio and KPI Library (KPI-001 .. KPI-012)
# ---------------------------------------------------------------------------


def calculate_gross_margin_pct(
    revenue: Decimal | str | int | float,
    cogs: Decimal | str | int | float,
) -> RatioResult:
    """KPI-001: Gross margin % = (Revenue - COGS) / Revenue."""
    rev = Decimal(str(revenue) if isinstance(revenue, float) else revenue)
    cost = Decimal(str(cogs) if isinstance(cogs, float) else cogs)
    gross_profit = rev - cost
    return safe_divide(gross_profit, rev)


def calculate_opex_ratio(
    opex: Decimal | str | int | float,
    revenue: Decimal | str | int | float,
) -> RatioResult:
    """KPI-002: Operating expense ratio = Opex / Revenue."""
    op = Decimal(str(opex) if isinstance(opex, float) else opex)
    rev = Decimal(str(revenue) if isinstance(revenue, float) else revenue)
    return safe_divide(op, rev)


def calculate_budget_burn_pct(
    ytd_actual: Decimal | str | int | float,
    annual_budget: Decimal | str | int | float,
) -> RatioResult:
    """KPI-003: Budget burn % = YTD actual / Annual budget."""
    act = Decimal(str(ytd_actual) if isinstance(ytd_actual, float) else ytd_actual)
    bud = Decimal(str(annual_budget) if isinstance(annual_budget, float) else annual_budget)
    return safe_divide(act, bud)


def calculate_revenue_growth_pct(
    actual: Decimal | str | int | float,
    py_actual: Decimal | str | int | float,
) -> RatioResult:
    """KPI-004: Revenue growth % (YoY) = (Actual - PY actual) / |PY actual|."""
    act = Decimal(str(actual) if isinstance(actual, float) else actual)
    py = Decimal(str(py_actual) if isinstance(py_actual, float) else py_actual)
    diff = act - py
    return safe_divide(diff, py, abs_denominator=True)


def calculate_line_variance_pct(
    actual: Decimal | str | int | float,
    budget: Decimal | str | int | float,
) -> RatioResult:
    """KPI-005: Line variance % = (Actual - Budget) / |Budget|."""
    return calculate_variance_pct_ratio(actual, budget)


def calculate_forecast_accuracy_ratio(
    actual: Decimal | str | int | float,
    forecast: Decimal | str | int | float,
) -> RatioResult:
    """KPI-006: Single-period forecast accuracy (MAPE-lite component) = |Actual - Forecast| / |Actual|."""
    act = Decimal(str(actual) if isinstance(actual, float) else actual)
    fc = Decimal(str(forecast) if isinstance(forecast, float) else forecast)
    abs_err = abs(act - fc)
    return safe_divide(abs_err, act, abs_denominator=True)


def calculate_mape_lite(
    period_pairs: Sequence[tuple[Decimal | str | int | float, Decimal | str | int | float]],
) -> tuple[RatioResult, int]:
    """CALC-069 / KPI-006: MAPE-lite over period series.

    Formula: mean( |actual - forecast| / |actual| ) over periods where actual != 0.
    Periods with actual == 0 are excluded and counted in the report.
    Returns (RatioResult, zero_actual_excluded_count).
    """
    terms: list[Decimal] = []
    zero_actual_count = 0

    for act_raw, fc_raw in period_pairs:
        act = Decimal(str(act_raw) if isinstance(act_raw, float) else act_raw)
        fc = Decimal(str(fc_raw) if isinstance(fc_raw, float) else fc_raw)
        if act == Decimal("0"):
            zero_actual_count += 1
            continue
        term = quantize_ratio(abs(act - fc) / abs(act))
        terms.append(term)

    if not terms:
        if zero_actual_count > 0:
            return RatioResult(
                value=None, state=RatioState.UNDEFINED, display="n/a"
            ), zero_actual_count
        return RatioResult(value=None, state=RatioState.NULL, display="—"), zero_actual_count

    mean_mape = quantize_ratio(sum(terms) / Decimal(len(terms)))
    return (
        RatioResult(value=mean_mape, state=RatioState.VALID, display=format_percent(mean_mape)),
        zero_actual_count,
    )


def calculate_operating_margin_pct(
    operating_income: Decimal | str | int | float,
    revenue: Decimal | str | int | float,
) -> RatioResult:
    """KPI-007: Operating margin % = Operating Income / Revenue."""
    oi = Decimal(str(operating_income) if isinstance(operating_income, float) else operating_income)
    rev = Decimal(str(revenue) if isinstance(revenue, float) else revenue)
    return safe_divide(oi, rev)


def calculate_net_profit_margin_pct(
    net_income: Decimal | str | int | float,
    revenue: Decimal | str | int | float,
) -> RatioResult:
    """KPI-008: Net profit margin % = Net Income / Revenue."""
    ni = Decimal(str(net_income) if isinstance(net_income, float) else net_income)
    rev = Decimal(str(revenue) if isinstance(revenue, float) else revenue)
    return safe_divide(ni, rev)


def calculate_cogs_ratio(
    cogs: Decimal | str | int | float,
    revenue: Decimal | str | int | float,
) -> RatioResult:
    """KPI-009: COGS ratio % = COGS / Revenue."""
    cost = Decimal(str(cogs) if isinstance(cogs, float) else cogs)
    rev = Decimal(str(revenue) if isinstance(revenue, float) else revenue)
    return safe_divide(cost, rev)


def calculate_expense_growth_pct(
    actual: Decimal | str | int | float,
    py_actual: Decimal | str | int | float,
) -> RatioResult:
    """KPI-010: Expense growth % (YoY) = (Actual - PY actual) / |PY actual|."""
    act = Decimal(str(actual) if isinstance(actual, float) else actual)
    py = Decimal(str(py_actual) if isinstance(py_actual, float) else py_actual)
    diff = act - py
    return safe_divide(diff, py, abs_denominator=True)


def calculate_forecast_variance_pct(
    actual: Decimal | str | int | float,
    forecast: Decimal | str | int | float,
) -> RatioResult:
    """KPI-011: Forecast variance % = (Actual - Forecast) / |Forecast|."""
    act = Decimal(str(actual) if isinstance(actual, float) else actual)
    fc = Decimal(str(forecast) if isinstance(forecast, float) else forecast)
    diff = act - fc
    return safe_divide(diff, fc, abs_denominator=True)


def calculate_kpi(kpi_id: KPI | str, **kwargs: Any) -> RatioResult | Decimal:
    """Unified entry point for the KPI registry (KPI-001 .. KPI-012)."""
    kpi_enum = KPI(kpi_id) if isinstance(kpi_id, str) else kpi_id

    if kpi_enum == KPI.KPI_001:
        return calculate_gross_margin_pct(kwargs["revenue"], kwargs["cogs"])
    if kpi_enum == KPI.KPI_002:
        return calculate_opex_ratio(kwargs["opex"], kwargs["revenue"])
    if kpi_enum == KPI.KPI_003:
        return calculate_budget_burn_pct(kwargs["ytd_actual"], kwargs["annual_budget"])
    if kpi_enum == KPI.KPI_004:
        return calculate_revenue_growth_pct(kwargs["actual"], kwargs["py_actual"])
    if kpi_enum == KPI.KPI_005:
        return calculate_line_variance_pct(kwargs["actual"], kwargs["budget"])
    if kpi_enum == KPI.KPI_006:
        if "period_pairs" in kwargs:
            res, _ = calculate_mape_lite(kwargs["period_pairs"])
            return res
        return calculate_forecast_accuracy_ratio(kwargs["actual"], kwargs["forecast"])
    if kpi_enum == KPI.KPI_007:
        return calculate_operating_margin_pct(kwargs["operating_income"], kwargs["revenue"])
    if kpi_enum == KPI.KPI_008:
        return calculate_net_profit_margin_pct(kwargs["net_income"], kwargs["revenue"])
    if kpi_enum == KPI.KPI_009:
        return calculate_cogs_ratio(kwargs["cogs"], kwargs["revenue"])
    if kpi_enum == KPI.KPI_010:
        return calculate_expense_growth_pct(kwargs["actual"], kwargs["py_actual"])
    if kpi_enum == KPI.KPI_011:
        return calculate_forecast_variance_pct(kwargs["actual"], kwargs["forecast"])
    if kpi_enum == KPI.KPI_012:
        return calculate_percentage_point_variance(kwargs["actual_pct"], kwargs["budget_pct"])

    raise ValueError(f"Unknown KPI ID: {kpi_id}")


# ---------------------------------------------------------------------------
# Formatting and Display Helpers (CALC-013, CALC-030 .. CALC-033)
# ---------------------------------------------------------------------------


def _format_digits_grouped(digits_str: str, grouping: GroupingFormat) -> str:
    """Group digit string according to International or Indian standards."""
    if len(digits_str) <= 3:
        return digits_str

    if grouping == GroupingFormat.INDIAN:
        last3 = digits_str[-3:]
        rest = digits_str[:-3]
        parts: list[str] = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        return ",".join(parts) + "," + last3

    # International (standard 3-digit chunks)
    parts = []
    rest = digits_str
    while len(rest) > 3:
        parts.insert(0, rest[-3:])
        rest = rest[:-3]
    if rest:
        parts.insert(0, rest)
    return ",".join(parts)


def format_number(
    amount: Decimal | str | int | float,
    decimal_places: int = 2,
    grouping: GroupingFormat = GroupingFormat.INTERNATIONAL,
    negative_format: NegativeFormat = NegativeFormat.PARENTHESES,
    include_plus: bool = False,
) -> str:
    """Format numeric value with digit grouping, decimals, and negative style per §6.1, §6.4."""
    if isinstance(amount, float):
        amount = str(amount)
    dec = Decimal(amount)

    target_unit = Decimal("10") ** -decimal_places if decimal_places > 0 else Decimal("1")
    rounded = dec.quantize(target_unit, rounding=ROUND_HALF_UP)

    is_negative = rounded < 0
    abs_dec = abs(rounded)

    parts = f"{abs_dec:.{decimal_places}f}".split(".")
    integer_part = parts[0]
    fraction_part = ("." + parts[1]) if len(parts) > 1 else ""

    grouped_int = _format_digits_grouped(integer_part, grouping)
    formatted_abs = grouped_int + fraction_part

    if is_negative:
        if negative_format in (NegativeFormat.PARENTHESES, NegativeFormat.BOTH):
            return f"({formatted_abs})"
        return f"-{formatted_abs}"

    if rounded > 0 and include_plus:
        return f"+{formatted_abs}"

    return formatted_abs


def format_currency(
    amount: Decimal | str | int | float,
    currency_symbol: str = "₹",
    scale: DisplayScale = DisplayScale.WHOLE,
    negative_format: NegativeFormat = NegativeFormat.PARENTHESES,
    grouping: GroupingFormat = GroupingFormat.INDIAN,
    decimal_places: int = 2,
) -> str:
    """Format currency string adhering to CALC-032 (scale) and CALC-033 (negatives).

    Examples:
    - Whole: '₹ 30,95,801.00'
    - Thousands: '₹ in thousands 3,095.80'
    - Lakhs: '₹ in lakhs 30.96'
    - Parentheses: '(25,000.00)'
    """
    if isinstance(amount, float):
        amount = str(amount)
    dec = Decimal(amount)

    scale_divisor = Decimal(scale.value)
    scaled_dec = dec / scale_divisor

    # Determine scale label
    if scale == DisplayScale.WHOLE:
        prefix = f"{currency_symbol}".strip()
    elif scale == DisplayScale.THOUSANDS:
        prefix = f"{currency_symbol} in thousands".strip()
    elif scale == DisplayScale.LAKHS:
        prefix = f"{currency_symbol} in lakhs".strip()
    elif scale == DisplayScale.CRORES:
        prefix = f"{currency_symbol} in crores".strip()
    elif scale == DisplayScale.MILLIONS:
        prefix = f"{currency_symbol} in millions".strip()
    else:
        prefix = f"{currency_symbol}".strip()

    num_str = format_number(
        scaled_dec,
        decimal_places=decimal_places,
        grouping=grouping,
        negative_format=negative_format,
        include_plus=False,
    )

    if not prefix:
        return num_str
    return f"{prefix} {num_str}"


def format_parentheses(
    amount: Decimal | str | int | float,
    decimal_places: int = 2,
    grouping: GroupingFormat = GroupingFormat.INTERNATIONAL,
) -> str:
    """Format negative number with parentheses per CALC-033: e.g. '(25,000.00)'."""
    return format_number(
        amount,
        decimal_places=decimal_places,
        grouping=grouping,
        negative_format=NegativeFormat.PARENTHESES,
        include_plus=False,
    )


def format_percent(
    value: Decimal | str | int | float | None,
    decimal_places: int = 1,
    include_sign: bool = False,
) -> str:
    """Format 6 dp ratio as a percentage string (e.g. 0.080000 -> '8.0%') per §6.1."""
    if value is None or str(value).strip() in ("—", "None"):
        return "—"
    if str(value).strip() == "n/a":
        return "n/a"

    if isinstance(value, float):
        value = str(value)
    dec = Decimal(value)

    # Multiply ratio by 100 to get percentage value
    pct_val = dec * ONE_HUNDRED
    target_unit = Decimal("10") ** -decimal_places
    rounded = pct_val.quantize(target_unit, rounding=ROUND_HALF_UP)

    is_negative = rounded < 0
    abs_dec = abs(rounded)
    abs_str = f"{abs_dec:.{decimal_places}f}%"

    if is_negative:
        return f"-{abs_str}"
    if rounded > 0 and include_sign:
        return f"+{abs_str}"
    return abs_str


def format_percentage_points(
    value: Decimal | str | int | float,
    decimal_places: int = 1,
    include_sign: bool = True,
) -> str:
    """Format percentage points difference per CALC-013: e.g. '+1.5 pp'."""
    if isinstance(value, float):
        value = str(value)
    dec = Decimal(value)

    target_unit = Decimal("10") ** -decimal_places
    rounded = dec.quantize(target_unit, rounding=ROUND_HALF_UP)

    is_negative = rounded < 0
    abs_dec = abs(rounded)
    abs_str = f"{abs_dec:.{decimal_places}f} pp"

    if is_negative:
        return f"-{abs_str}"
    if rounded > 0 and include_sign:
        return f"+{abs_str}"
    return abs_str


def check_sum_of_rounded_discrepancy(
    components: Sequence[Decimal | str | int | float],
    total: Decimal | str | int | float,
    decimal_places: int = 2,
) -> tuple[bool, Decimal, str | None]:
    """Check sum-of-rounded rule and return mandatory footnote per CALC-031.

    Rule: If |Σ(displayed components) - displayed total| > 0:
    footnote = "Components may not sum to the total due to rounding."
    """
    target_unit = Decimal("10") ** -decimal_places
    sum_displayed = sum(
        Decimal(str(c) if isinstance(c, float) else c).quantize(target_unit, rounding=ROUND_HALF_UP)
        for c in components
    )
    displayed_total = Decimal(str(total) if isinstance(total, float) else total).quantize(
        target_unit, rounding=ROUND_HALF_UP
    )

    discrepancy = abs(sum_displayed - displayed_total)
    if discrepancy > 0:
        return True, discrepancy, "Components may not sum to the total due to rounding."
    return False, ZERO, None
