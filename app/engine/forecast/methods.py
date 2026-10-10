"""Forecast methods implementation per 07_FORECAST_METHODS_SPEC.md and 05_CALCULATION_SPEC.md.

Implements:
- Method 1: Locked actuals for closed periods (CALC-060)
- Method 2: Remaining-budget spread method (CALC-061)
- Method 3: Run-rate method (average of last N actual months) (CALC-062)
- Method 4: 3-month trailing average (CALC-063)
- Manual override with mandatory reason logging (CALC-064)
- Scenario adjustments (CALC-065)
- Forecast accuracy metrics (CALC-066 ... CALC-069)
- Method eligibility and three-level resolution cascade (doc 07 §4, §5)
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

from app.engine.calc.math import ZERO, quantize_money

logger = logging.getLogger(__name__)

SIX_PLACES = Decimal("0.000001")
TWO_PLACES = Decimal("0.01")


def quantize_rate(rate: Decimal | str | int | float) -> Decimal:
    """Quantize to 6 decimal places for stored rates/intermediate values per 05 §6.1."""
    if isinstance(rate, float):
        rate = str(rate)
    return Decimal(rate).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


class ForecastMethod(str, Enum):
    """Forecast method codes per 03_DATA_DICTIONARY DimMethod and 07_FORECAST_METHODS_SPEC."""

    LOCKED_ACTUALS = "locked_actuals"
    REMAINING_BUDGET = "remaining_budget"
    RUN_RATE = "run_rate"
    AVG_3M = "avg_3m"
    MANUAL = "manual"


class Scenario(str, Enum):
    """Forecast scenarios per 07_FORECAST_METHODS_SPEC §6."""

    BASE = "base"
    BEST = "best"
    WORST = "worst"


@dataclass
class PeriodActual:
    """Loaded actual for a period."""

    period_code: str
    amount: Decimal
    is_closed: bool = True
    has_actuals: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))


@dataclass
class ManualOverride:
    """Manual override record per CALC-064 and doc 07 §9.

    Enforces mandatory reason string per FR-FC-006.
    """

    period_code: str
    amount: Decimal
    reason: str
    author: str = "system"
    old_value: Decimal | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.reason or not self.reason.strip():
            raise ValueError(
                "Manual override requires a mandatory non-empty reason (FR-FC-006 / CALC-064)."
            )
        self.reason = self.reason.strip()
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))


@dataclass
class ForecastResult:
    """A generated forecast period line per 03_DATA_DICTIONARY §4.3 (FactForecast)."""

    period_code: str
    amount: Decimal  # Displayed (2 dp)
    amount_stored: Decimal  # Stored full precision / 6 dp
    method: ForecastMethod
    scenario: Scenario = Scenario.BASE
    is_manual_override: bool = False
    override_reason: str | None = None
    driver_ref: dict[str, Any] = field(default_factory=dict)
    is_closed_period: bool = False
    flag: str | None = None


# -----------------------------------------------------------------------------
# Method 1: Locked Actuals (CALC-060)
# -----------------------------------------------------------------------------


def calc_locked_actuals(
    actuals: Sequence[PeriodActual],
    target_period: str | None = None,
    scenario: Scenario = Scenario.BASE,
) -> ForecastResult:
    """Method 1: Locked actuals per CALC-060, doc 07 §4 and Fixture F14e.

    Closed periods are locked to actuals. If no actuals exist in a closed period,
    it is treated as 0 and flagged in the summary as 'no actuals'.
    When used as a forecast projection into an open period (e.g., F14e),
    it takes the last locked actual.
    """
    if not actuals:
        return ForecastResult(
            period_code=target_period or "UNKNOWN",
            amount=Decimal("0.00"),
            amount_stored=Decimal("0.000000"),
            method=ForecastMethod.LOCKED_ACTUALS,
            scenario=scenario,
            is_closed_period=True,
            flag="no actuals",
            driver_ref={"status": "no actuals loaded"},
        )

    # Check if target period matches an existing closed period actual
    if target_period is not None:
        matching = [a for a in actuals if a.period_code == target_period]
        if matching:
            match = matching[0]
            if not match.has_actuals:
                return ForecastResult(
                    period_code=match.period_code,
                    amount=Decimal("0.00"),
                    amount_stored=Decimal("0.000000"),
                    method=ForecastMethod.LOCKED_ACTUALS,
                    scenario=scenario,
                    is_closed_period=True,
                    flag="no actuals",
                    driver_ref={"period": match.period_code, "has_actuals": False},
                )
            amt = match.amount
            return ForecastResult(
                period_code=match.period_code,
                amount=quantize_money(amt),
                amount_stored=Decimal(str(amt)),
                method=ForecastMethod.LOCKED_ACTUALS,
                scenario=scenario,
                is_closed_period=match.is_closed,
                driver_ref={"period": match.period_code, "locked_actual": str(amt)},
            )

    # If projecting into an open period (F14e), use the last locked actual
    last_actual = actuals[-1]
    last_amt = last_actual.amount
    return ForecastResult(
        period_code=target_period or last_actual.period_code,
        amount=quantize_money(last_amt),
        amount_stored=Decimal(str(last_amt)),
        method=ForecastMethod.LOCKED_ACTUALS,
        scenario=scenario,
        is_closed_period=False,
        driver_ref={
            "source_period": last_actual.period_code,
            "locked_actual": str(last_amt),
        },
    )


# -----------------------------------------------------------------------------
# Method 2: Remaining-Budget Method (CALC-061)
# -----------------------------------------------------------------------------


def calc_remaining_budget(
    annual_budget: Decimal | str | int | float,
    actuals: Sequence[Decimal | PeriodActual],
    remaining_periods: Sequence[str] | int,
    scenario: Scenario = Scenario.BASE,
) -> list[ForecastResult]:
    """Method 2: Remaining-budget spread per CALC-061 and Fixture F14a.

    remaining = annual_budget - sum(actuals in loaded periods)
    each remaining period gets remaining / k where k = number of remaining open periods.
    Guards:
    - k = 0 (year complete) -> returns empty list (no forecast rows generated).
    - negative remaining -> spread as computed (visible over-spend signal, never clamped).
    """
    annual_budget_dec = Decimal(str(annual_budget))

    actual_values = [
        item.amount if isinstance(item, PeriodActual) else Decimal(str(item)) for item in actuals
    ]
    consumed_actuals = sum(actual_values, ZERO)
    remaining = annual_budget_dec - consumed_actuals

    if isinstance(remaining_periods, int):
        k = remaining_periods
        period_codes = [f"P{i + 1}" for i in range(k)]
    else:
        period_codes = list(remaining_periods)
        k = len(period_codes)

    if k <= 0:
        return []

    per_period_stored = remaining / Decimal(k)
    per_period_display = quantize_money(per_period_stored)

    driver_ref = {
        "annual_budget": str(annual_budget_dec),
        "consumed_actuals": str(consumed_actuals),
        "remaining_budget": str(remaining),
        "remaining_periods_count": k,
        "remaining_periods": period_codes,
    }

    results = []
    for code in period_codes:
        results.append(
            ForecastResult(
                period_code=code,
                amount=per_period_display,
                amount_stored=per_period_stored,
                method=ForecastMethod.REMAINING_BUDGET,
                scenario=scenario,
                driver_ref=driver_ref,
            )
        )
    return results


# -----------------------------------------------------------------------------
# Method 3: Run-Rate Method (CALC-062)
# -----------------------------------------------------------------------------


def calc_run_rate(
    actuals: Sequence[Decimal | PeriodActual],
    n: int = 3,
    remaining_periods: Sequence[str] | int = 1,
    scenario: Scenario = Scenario.BASE,
    clamp: bool = True,
) -> tuple[list[ForecastResult], str | None]:
    """Method 3: Run-rate per CALC-062 and Fixture F14b.

    avg = sum(net_amount over last N loaded actual periods) / N
    Guards:
    - N <= 0: raises ValueError ("Run-rate window N must be > 0").
    - len(actuals) == 0: ineligible ("Needs at least N loaded actual periods").
    - N > loaded periods: clamped to loaded count with a visible notice if clamp=True.
    """
    if n <= 0:
        raise ValueError("Run-rate window N must be greater than 0.")

    if not actuals:
        raise ValueError("Needs at least N loaded actual periods.")

    loaded_count = len(actuals)
    notice = None

    if loaded_count < n:
        if clamp:
            effective_n = loaded_count
            notice = f"Run-rate window clamped from {n} to {effective_n} loaded periods."
        else:
            raise ValueError(f"Needs at least {n} loaded actual periods.")
    else:
        effective_n = n

    window_actuals = actuals[-effective_n:]
    window_values = [
        item.amount if isinstance(item, PeriodActual) else Decimal(str(item))
        for item in window_actuals
    ]
    window_period_codes = [
        item.period_code if isinstance(item, PeriodActual) else f"ACT-{i + 1}"
        for i, item in enumerate(window_actuals)
    ]

    total_sum = sum(window_values, ZERO)
    avg_stored = total_sum / Decimal(effective_n)
    avg_display = quantize_money(avg_stored)

    if isinstance(remaining_periods, int):
        period_codes = [f"P{i + 1}" for i in range(remaining_periods)]
    else:
        period_codes = list(remaining_periods)

    driver_ref = {
        "months": window_period_codes,
        "avg_basis": "net_amount",
        "sum": str(total_sum),
        "window_n": effective_n,
        "requested_n": n,
        "clamped": notice is not None,
    }

    results = []
    for code in period_codes:
        results.append(
            ForecastResult(
                period_code=code,
                amount=avg_display,
                amount_stored=avg_stored,
                method=ForecastMethod.RUN_RATE,
                scenario=scenario,
                driver_ref=driver_ref,
                flag=notice,
            )
        )
    return results, notice


# -----------------------------------------------------------------------------
# Method 4: 3-Month Trailing Average (CALC-063)
# -----------------------------------------------------------------------------


def calc_avg_3m(
    actuals: Sequence[Decimal | PeriodActual],
    remaining_periods: Sequence[str] | int = 1,
    scenario: Scenario = Scenario.BASE,
    clamp: bool = True,
) -> tuple[list[ForecastResult], str | None]:
    """Method 4: 3-month trailing average per CALC-063 and Fixture F14f.

    Identical arithmetic to CALC-062 with N = 3 fixed.
    Intentional duplication of arithmetic, not implementation.
    """
    results, notice = calc_run_rate(
        actuals=actuals,
        n=3,
        remaining_periods=remaining_periods,
        scenario=scenario,
        clamp=clamp,
    )
    for res in results:
        res.method = ForecastMethod.AVG_3M
    return results, notice


# -----------------------------------------------------------------------------
# Manual Override Handling (CALC-064)
# -----------------------------------------------------------------------------


def calc_manual_override(
    override: ManualOverride | dict[str, Any],
    scenario: Scenario = Scenario.BASE,
) -> ForecastResult:
    """Manual override per CALC-064, doc 07 §9, and Fixture F14g.

    Enforces mandatory non-empty reason logging per FR-FC-006.
    """
    if isinstance(override, dict):
        period_code = override["period_code"]
        amount = Decimal(str(override["amount"]))
        reason = override.get("reason", "")
        author = override.get("author", "system")
        old_value = (
            Decimal(str(override["old_value"])) if override.get("old_value") is not None else None
        )
        rec = ManualOverride(
            period_code=period_code,
            amount=amount,
            reason=reason,
            author=author,
            old_value=old_value,
        )
    else:
        rec = override

    amount_dec = rec.amount
    amount_display = quantize_money(amount_dec)

    logger.info(
        "Forecast manual override applied: period=%s, amount=%s, reason=%s, author=%s",
        rec.period_code,
        amount_display,
        rec.reason,
        rec.author,
    )

    driver_ref = {
        "override_amount": str(amount_dec),
        "reason": rec.reason,
        "author": rec.author,
        "old_value": str(rec.old_value) if rec.old_value is not None else None,
        "applied_at": rec.created_at.isoformat(),
    }

    return ForecastResult(
        period_code=rec.period_code,
        amount=amount_display,
        amount_stored=amount_dec,
        method=ForecastMethod.MANUAL,
        scenario=scenario,
        is_manual_override=True,
        override_reason=rec.reason,
        driver_ref=driver_ref,
    )


# -----------------------------------------------------------------------------
# Scenario Adjustment (CALC-065)
# -----------------------------------------------------------------------------


def apply_scenario_adjustment(
    base_result: ForecastResult,
    adjustment_pct: Decimal | str | float,
    scenario: Scenario,
) -> ForecastResult:
    """Scenario adjustment per CALC-065 and Fixture F14c.

    forecast = base * (1 + adjustment_pct)
    Applied only to forecast rows, never to actuals or budget.
    """
    adj_dec = Decimal(str(adjustment_pct))
    factor = Decimal("1") + adj_dec

    adjusted_stored = base_result.amount_stored * factor
    adjusted_display = quantize_money(adjusted_stored)

    new_driver_ref = dict(base_result.driver_ref)
    new_driver_ref["scenario_adjustment_pct"] = str(adj_dec)
    new_driver_ref["base_amount_stored"] = str(base_result.amount_stored)

    return ForecastResult(
        period_code=base_result.period_code,
        amount=adjusted_display,
        amount_stored=adjusted_stored,
        method=base_result.method,
        scenario=scenario,
        is_manual_override=base_result.is_manual_override,
        override_reason=base_result.override_reason,
        driver_ref=new_driver_ref,
        is_closed_period=base_result.is_closed_period,
        flag=base_result.flag,
    )


# -----------------------------------------------------------------------------
# Forecast Accuracy Metrics (CALC-066 … CALC-069)
# -----------------------------------------------------------------------------


def calc_signed_error(actual: Decimal | str | float, forecast: Decimal | str | float) -> Decimal:
    """Signed error per CALC-066: actual - forecast.

    Canonical direction: positive = actual exceeded forecast.
    """
    return quantize_money(Decimal(str(actual)) - Decimal(str(forecast)))


def calc_absolute_error(actual: Decimal | str | float, forecast: Decimal | str | float) -> Decimal:
    """Absolute error per CALC-067: |actual - forecast|."""
    return quantize_money(abs(Decimal(str(actual)) - Decimal(str(forecast))))


def calc_signed_bias(signed_errors: Sequence[Decimal | str | float]) -> Decimal:
    """Signed bias per CALC-068: mean(signed error) over the compared periods."""
    if not signed_errors:
        return Decimal("0.00")
    total = sum((Decimal(str(e)) for e in signed_errors), ZERO)
    return quantize_money(total / Decimal(len(signed_errors)))


def calc_mape_lite(
    pairs: Sequence[tuple[Decimal | str | float, Decimal | str | float]],
) -> tuple[Decimal, int]:
    """MAPE-lite per CALC-069 and Fixture F14d.

    mean( |actual - forecast| / |actual| ) over periods where actual != 0.
    Periods with actual == 0 are excluded and counted.
    Returns (mape_lite_ratio, excluded_count).
    """
    terms = []
    excluded_count = 0

    for act_raw, fct_raw in pairs:
        act = Decimal(str(act_raw))
        fct = Decimal(str(fct_raw))
        if act == ZERO:
            excluded_count += 1
            continue
        term = abs(act - fct) / abs(act)
        terms.append(term)

    if not terms:
        return Decimal("0.000000"), excluded_count

    mean_mape = sum(terms, ZERO) / Decimal(len(terms))
    return quantize_rate(mean_mape), excluded_count


# -----------------------------------------------------------------------------
# Method Eligibility and Resolution (doc 07 §4.1, §5)
# -----------------------------------------------------------------------------


def check_method_eligibility(
    method: ForecastMethod,
    has_budget: bool,
    actual_periods_count: int,
    remaining_periods_count: int,
    n: int = 3,
) -> tuple[bool, str | None]:
    """Check method eligibility per doc 07 §4.1 guard table.

    Returns (is_eligible, hint_if_ineligible).
    """
    if method == ForecastMethod.MANUAL:
        return True, None

    if method == ForecastMethod.REMAINING_BUDGET:
        if not has_budget:
            return False, "Disabled: No budget exists for the account."
        if remaining_periods_count <= 0:
            return False, "Disabled for the line when the year is complete (k = 0)."
        return True, None

    if method == ForecastMethod.RUN_RATE:
        if actual_periods_count < n:
            return False, f"Needs at least {n} loaded actual periods."
        return True, None

    if method == ForecastMethod.AVG_3M:
        if actual_periods_count < 3:
            return False, "Needs at least 3 loaded actual periods."
        return True, None

    if method == ForecastMethod.LOCKED_ACTUALS:
        return True, None

    return False, "Unknown method."


def resolve_method(
    line_pinned_method: ForecastMethod | None = None,
    account_group_method: ForecastMethod | None = None,
    project_default_method: ForecastMethod = ForecastMethod.RUN_RATE,
    has_budget: bool = True,
    actual_periods_count: int = 3,
    remaining_periods_count: int = 3,
    run_rate_n: int = 3,
    has_manual_override: bool = False,
) -> tuple[ForecastMethod | None, str]:
    """Three-level resolution cascade per doc 07 §5 and §4.1 fallback order.

    Priority:
    1. Line-level override (pinned method)
    2. Account-group setting
    3. Project default
    4. Fallback (remaining_budget)

    If the resolved method is ineligible, fallback order:
    manual (if override exists) -> remaining_budget (if budget exists) -> None (flagged as insufficient history).
    """
    candidate = (
        line_pinned_method
        or account_group_method
        or project_default_method
        or ForecastMethod.REMAINING_BUDGET
    )

    eligible, hint = check_method_eligibility(
        method=candidate,
        has_budget=has_budget,
        actual_periods_count=actual_periods_count,
        remaining_periods_count=remaining_periods_count,
        n=run_rate_n,
    )

    if eligible:
        return candidate, f"Resolved via priority cascade: {candidate.value}"

    # Fallback order per doc 07 §4.1:
    if has_manual_override:
        return ForecastMethod.MANUAL, "Fallback to manual override (candidate ineligible)"

    if has_budget and remaining_periods_count > 0:
        return (
            ForecastMethod.REMAINING_BUDGET,
            f"Fallback to remaining_budget ({candidate.value} ineligible: {hint})",
        )

    return None, f"Not forecast - insufficient history ({candidate.value} ineligible: {hint})"
