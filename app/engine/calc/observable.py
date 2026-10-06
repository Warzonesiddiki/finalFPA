"""Observable calculations for the twelve critical FP&A analyst numbers (ENG-07).

Provides structured data objects for the twelve canonical financial quantities
defined in docs/05_CALCULATION_SPEC.md and docs/08_UI_UX_SPEC.md.
Each function returns an ObservableNumber instance tracking its exact Decimal value,
all Decimal inputs, formula identifier, and calculation hops without rounding drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence

from app.engine.calc.math import (
    calculate_variance,
    calculate_variance_pct,
    calculate_favourability,
    calculate_percentage_point_variance,
    calculate_gross_margin_pct,
    calculate_budget_burn_pct,
    calculate_mape_lite,
    quantize_money,
    Direction,
    Favourability,
)
from app.engine.calc.quality_score import (
    calculate_quality_score,
    create_f12_fixture_checks,
    QualityScoreResult,
)


@dataclass(frozen=True)
class ObservableHop:
    """Represents an observable processing or arithmetic hop in the pipeline."""
    name: str
    hop_type: str  # e.g. "ingest", "store", "compute", "export"
    detail: str


@dataclass(frozen=True)
class ObservableNumber:
    """Structured data container representing an observable financial quantity."""
    id: int
    name: str
    formula_id: str
    value: Decimal | Favourability | QualityScoreResult
    inputs: Dict[str, Any]
    hops: List[ObservableHop]
    display: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert observable number to structured JSON-serializable dictionary."""
        val = self.value
        if isinstance(val, Favourability):
            val_repr = val.value
        elif isinstance(val, QualityScoreResult):
            val_repr = val.score
        elif isinstance(val, Decimal):
            val_repr = str(val)
        else:
            val_repr = str(val)

        return {
            "id": self.id,
            "name": self.name,
            "formula_id": self.formula_id,
            "value": val_repr,
            "inputs": {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in self.inputs.items()
            },
            "hops": [{"name": h.name, "type": h.hop_type, "detail": h.detail} for h in self.hops],
            "display": self.display,
        }


def observe_number_1_tb_balance(debits: Decimal, credits: Decimal) -> ObservableNumber:
    """1. Trial Balance Net Sum: debits - credits = 0.00 (CALC-071)."""
    assert isinstance(debits, Decimal), "Inputs must be Decimal"
    assert isinstance(credits, Decimal), "Inputs must be Decimal"
    net = debits - credits
    return ObservableNumber(
        id=1,
        name="Trial Balance Net Sum",
        formula_id="CALC-071",
        value=net,
        inputs={"debits": debits, "credits": credits},
        hops=[
            ObservableHop("Ingest", "ingest", "CSV line parsed to Decimal without float cast"),
            ObservableHop("Analytical Store", "store", "DuckDB DECIMAL(18,2) exact representation"),
            ObservableHop("Balance Verification", "compute", f"Debit ({debits}) − Credit ({credits}) = {net}"),
        ],
        display=f"Net: {net:+.2f}",
    )


def observe_number_2_net_amount(debit: Decimal, credit: Decimal) -> ObservableNumber:
    """2. Net Amount Line Calculation: debit - credit (CALC-007)."""
    assert isinstance(debit, Decimal), "Inputs must be Decimal"
    assert isinstance(credit, Decimal), "Inputs must be Decimal"
    net = debit - credit
    return ObservableNumber(
        id=2,
        name="Net Amount Line Calculation",
        formula_id="CALC-007",
        value=net,
        inputs={"debit": debit, "credit": credit},
        hops=[
            ObservableHop("Ingest", "ingest", "Quantized money Decimal preservation"),
            ObservableHop("Compute", "compute", f"Debit ({debit}) − Credit ({credit}) = {net}"),
            ObservableHop("Export", "export", "Excel/PPT pack minor unit preservation"),
        ],
        display=f"Net: {net:+.2f}",
    )


def observe_number_3_variance(actual: Decimal, budget: Decimal) -> ObservableNumber:
    """3. Variance: actual - budget (CALC-010)."""
    assert isinstance(actual, Decimal), "Inputs must be Decimal"
    assert isinstance(budget, Decimal), "Inputs must be Decimal"
    var = calculate_variance(actual, budget)
    return ObservableNumber(
        id=3,
        name="Variance (Actual − Budget)",
        formula_id="CALC-010",
        value=var,
        inputs={"actual": actual, "budget": budget},
        hops=[
            ObservableHop("Actuals Staging", "store", "FactActual aggregation"),
            ObservableHop("Budget Staging", "store", "FactBudget aggregation"),
            ObservableHop("Variance Arithmetic", "compute", f"Actual ({actual}) − Budget ({budget}) = {var}"),
        ],
        display=f"Variance: {var:+.2f}",
    )


def observe_number_4_variance_pct(actual: Decimal, budget: Decimal) -> ObservableNumber:
    """4. Variance %: (actual - budget) / |budget| (CALC-011 / KPI-005)."""
    assert isinstance(actual, Decimal), "Inputs must be Decimal"
    assert isinstance(budget, Decimal), "Inputs must be Decimal"
    var_pct = calculate_variance_pct(actual, budget)
    assert var_pct is not None
    return ObservableNumber(
        id=4,
        name="Variance % (Absolute Denominator)",
        formula_id="CALC-011",
        value=var_pct,
        inputs={"actual": actual, "budget": budget},
        hops=[
            ObservableHop("Variance Delta", "compute", f"Delta = {actual - budget}"),
            ObservableHop("Denominator Absolute", "compute", f"|Budget| = {abs(budget)}"),
            ObservableHop("Ratio Compute", "compute", f"Variance % = {var_pct}%"),
        ],
        display=f"{var_pct:+.2f}%",
    )


def observe_number_5_favourability(
    actual: Decimal, budget: Decimal, direction: Direction = Direction.HIGHER_IS_FAVOURABLE
) -> ObservableNumber:
    """5. Favourability Direction (CALC-012)."""
    assert isinstance(actual, Decimal), "Inputs must be Decimal"
    assert isinstance(budget, Decimal), "Inputs must be Decimal"
    fav = calculate_favourability(actual, budget, direction=direction)
    return ObservableNumber(
        id=5,
        name="Favourability Direction",
        formula_id="CALC-012",
        value=fav,
        inputs={"actual": actual, "budget": budget, "direction": direction.value},
        hops=[
            ObservableHop("Actual vs Budget", "store", f"Actual={actual}, Budget={budget}"),
            ObservableHop("Direction Evaluation", "compute", f"Direction={direction.value} -> {fav.value}"),
        ],
        display=f"{fav.value} (▲)" if fav == Favourability.FAVOURABLE else f"{fav.value} (▼)",
    )


def observe_number_6_percentage_points(actual_pct: Decimal, budget_pct: Decimal) -> ObservableNumber:
    """6. Percentage Points difference: actual_pct - budget_pct (CALC-013)."""
    assert isinstance(actual_pct, Decimal), "Inputs must be Decimal"
    assert isinstance(budget_pct, Decimal), "Inputs must be Decimal"
    pp = calculate_percentage_point_variance(actual_pct, budget_pct)
    return ObservableNumber(
        id=6,
        name="Percentage Points (pp)",
        formula_id="CALC-013",
        value=pp,
        inputs={"actual_pct": actual_pct, "budget_pct": budget_pct},
        hops=[
            ObservableHop("Ratio Scale", "compute", f"Actual GM={actual_pct}%, Budget GM={budget_pct}%"),
            ObservableHop("Point Arithmetic", "compute", f"{actual_pct} − {budget_pct} = {pp} pp"),
        ],
        display=f"{pp:+.1f} pp",
    )


def observe_number_7_bridge_residual(
    opening: Decimal, drivers: Sequence[Decimal], residual: Decimal
) -> ObservableNumber:
    """7. Bridge Waterfall Tie-Out & Residual (CALC-042 / DEC-065)."""
    assert isinstance(opening, Decimal), "Inputs must be Decimal"
    assert isinstance(residual, Decimal), "Inputs must be Decimal"
    total_drivers = sum(drivers, Decimal("0.00"))
    closing = opening + total_drivers + residual
    return ObservableNumber(
        id=7,
        name="Bridge Waterfall Tie-Out & Residual",
        formula_id="CALC-042",
        value=closing,
        inputs={"opening": opening, "drivers": list(drivers), "residual": residual},
        hops=[
            ObservableHop("Opening Anchor", "store", f"Opening={opening}"),
            ObservableHop("Driver Summation", "compute", f"Drivers={total_drivers}"),
            ObservableHop("Residual Plug", "compute", f"Unexplained Residual={residual}"),
            ObservableHop("Closing Total", "compute", f"Closing Total={closing}"),
        ],
        display=f"Closing: {closing:.2f}",
    )


def observe_number_8_dq_score(fixture_checks: Optional[List[Dict[str, Any]]] = None) -> ObservableNumber:
    """8. Data Quality Score: 100-pt system (CALC-050)."""
    checks = fixture_checks if fixture_checks is not None else create_f12_fixture_checks()
    res = calculate_quality_score(checks)
    score_dec = Decimal(str(res.score))
    return ObservableNumber(
        id=8,
        name="Data Quality Score (100-pt)",
        formula_id="CALC-050",
        value=res,
        inputs={"checks_count": len(checks), "total_deductions": Decimal(str(res.total_deductions))},
        hops=[
            ObservableHop("Check Evaluation", "compute", f"{len(checks)} checks evaluated"),
            ObservableHop("Deduction Tally", "compute", f"Total deductions={res.total_deductions}"),
            ObservableHop("Score Normalization", "compute", f"Final Score={res.score}/100"),
        ],
        display=f"{res.score}/100 DQ Score",
    )


def observe_number_9_gross_margin(revenue: Decimal, cogs: Decimal) -> ObservableNumber:
    """9. Gross Margin %: (Revenue - COGS) / Revenue (KPI-001)."""
    assert isinstance(revenue, Decimal), "Inputs must be Decimal"
    assert isinstance(cogs, Decimal), "Inputs must be Decimal"
    ratio_res = calculate_gross_margin_pct(revenue, cogs)
    assert ratio_res.value is not None
    return ObservableNumber(
        id=9,
        name="Gross Margin %",
        formula_id="KPI-001",
        value=ratio_res.value,
        inputs={"revenue": revenue, "cogs": cogs},
        hops=[
            ObservableHop("Gross Profit Delta", "compute", f"Revenue ({revenue}) − COGS ({cogs}) = {revenue - cogs}"),
            ObservableHop("Revenue Ratio", "compute", f"Ratio = {ratio_res.value}"),
        ],
        display=f"{ratio_res.display} GM",
    )


def observe_number_10_budget_burn(ytd_actual: Decimal, annual_budget: Decimal) -> ObservableNumber:
    """10. Budget Burn %: YTD Actual / Annual Budget (KPI-004)."""
    assert isinstance(ytd_actual, Decimal), "Inputs must be Decimal"
    assert isinstance(annual_budget, Decimal), "Inputs must be Decimal"
    ratio_res = calculate_budget_burn_pct(ytd_actual, annual_budget)
    assert ratio_res.value is not None
    return ObservableNumber(
        id=10,
        name="Budget Burn %",
        formula_id="KPI-004",
        value=ratio_res.value,
        inputs={"ytd_actual": ytd_actual, "annual_budget": annual_budget},
        hops=[
            ObservableHop("YTD Cumulative", "store", f"YTD Actual={ytd_actual}"),
            ObservableHop("Annual Target", "store", f"Annual Budget={annual_budget}"),
            ObservableHop("Burn Ratio", "compute", f"Ratio = {ratio_res.value}"),
        ],
        display=f"{ratio_res.display} Budget Burn",
    )


def observe_number_11_mape_lite(
    period_pairs: Sequence[tuple[Decimal, Decimal]]
) -> ObservableNumber:
    """11. Forecast Accuracy MAPE-lite: mean(|actual - fc| / |actual|) (CALC-069 / KPI-006)."""
    for act, fc in period_pairs:
        assert isinstance(act, Decimal) and isinstance(fc, Decimal), "All period pairs must be Decimal"
    ratio_res, excluded = calculate_mape_lite(period_pairs)
    assert ratio_res.value is not None
    return ObservableNumber(
        id=11,
        name="Forecast Accuracy MAPE-lite",
        formula_id="CALC-069",
        value=ratio_res.value,
        inputs={"period_pairs": [[p[0], p[1]] for p in period_pairs], "excluded_zero_actuals": excluded},
        hops=[
            ObservableHop("Absolute Forecast Error", "compute", "Error per period computed"),
            ObservableHop("Mean Error Aggregate", "compute", f"Mean MAPE = {ratio_res.value}"),
        ],
        display=f"{ratio_res.display} Forecast Error",
    )


def observe_number_12_rounding_footnote(
    unrounded_components: Sequence[Decimal],
) -> ObservableNumber:
    """12. Sum-of-Rounded Discrepancy Footnote (CALC-031)."""
    for c in unrounded_components:
        assert isinstance(c, Decimal), "All unrounded components must be Decimal"
    total_unrounded = sum(unrounded_components, Decimal("0"))
    displayed_components = [round(c, 2) for c in unrounded_components]
    sum_of_displayed = sum(displayed_components, Decimal("0"))
    displayed_total = round(total_unrounded, 2)
    discrepancy = abs(sum_of_displayed - displayed_total)

    is_footnote_required = discrepancy > Decimal("0")
    return ObservableNumber(
        id=12,
        name="Sum-of-Rounded Discrepancy Footnote",
        formula_id="CALC-031",
        value=discrepancy,
        inputs={
            "unrounded_components": list(unrounded_components),
            "displayed_components": displayed_components,
            "displayed_total": displayed_total,
            "sum_of_displayed": sum_of_displayed,
        },
        hops=[
            ObservableHop("Raw Line Summation", "compute", f"Unrounded Total = {total_unrounded}"),
            ObservableHop("Displayed Rows Sum", "compute", f"Sum of Displayed = {sum_of_displayed}"),
            ObservableHop("Discrepancy Evaluation", "compute", f"Discrepancy = {discrepancy} (Footnote: {is_footnote_required})"),
        ],
        display=f"Discrepancy: {discrepancy} (Footnote {'Required' if is_footnote_required else 'Not Needed'})",
    )


def get_twelve_observable_numbers() -> List[ObservableNumber]:
    """Retrieve all twelve observable financial numbers with canonical defaults."""
    return [
        observe_number_1_tb_balance(Decimal("10800000.00"), Decimal("10800000.00")),
        observe_number_2_net_amount(Decimal("150000.50"), Decimal("0.00")),
        observe_number_3_variance(Decimal("10800000.00"), Decimal("10000000.00")),
        observe_number_4_variance_pct(Decimal("10800000.00"), Decimal("10000000.00")),
        observe_number_5_favourability(Decimal("10800000.00"), Decimal("10000000.00"), Direction.HIGHER_IS_FAVOURABLE),
        observe_number_6_percentage_points(Decimal("40.0"), Decimal("38.5")),
        observe_number_7_bridge_residual(Decimal("15770000.00"), [Decimal("250000.00"), Decimal("125000.00")], Decimal("500000.00")),
        observe_number_8_dq_score(),
        observe_number_9_gross_margin(Decimal("1000000.00"), Decimal("600000.00")),
        observe_number_10_budget_burn(Decimal("2580000.00"), Decimal("10000000.00")),
        observe_number_11_mape_lite([(Decimal("100000.00"), Decimal("95000.00"))]),
        observe_number_12_rounding_footnote([Decimal("10.004"), Decimal("10.004")]),
    ]
