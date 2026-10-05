"""PowerPoint Deck Generation engine (Phase 5).

Implements docs/12_POWERPOINT_OUTPUT_SPEC.md §1 through §7.
Generates an executive-ready 6-slide widescreen (16:9) presentation using python-pptx:
  - Slide 1: Cover & metadata (PPT-001)
  - Slide 2: Executive summary / KPI Dashboard (PPT-002)
  - Slide 3: Budget vs Actual bridge / waterfall chart (PPT-003)
  - Slide 4: Top variances with drivers (PPT-004)
  - Slide 5: Exceptions and control risks (PPT-005)
  - Slide 6: Rolling forecast & outlook (PPT-006)

The deck is a *filled copy* of ``packaging/templates/FPAMonthEndCopilot_v1.pptx``
(docs/12 §3.6, `DEF-018`): geometry, colours, fonts, chart types and z-order all come
from the template, and this module only writes text and data into the shapes the template
already names. The fill itself is delegated to ``app.engine.pptx_fill`` (``ADP-001``…
``ADP-003``); this module holds the deck's data contract and its per-slide content.

All content is natively editable (no raster screenshots, no static image charts).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.presentation import Presentation as PresentationObject
from pptx.util import Inches

from app.engine.calc.math import quantize_money
from app.engine.exports.ppt_fit import (
    TRIMMED_FOOTNOTE,
    compute_character_budget,
    trim_text_to_budget,
)
from app.engine.pptx_fill import (
    TemplateShapeError,
    TextStyle,
    add_slide_from_layout,
    fill_table,
    open_template,
    replace_chart_data,
    resolve_shape,
    set_notes,
    set_text,
    shape_names,
)
from app.engine.pptx_fill.layout import handle_overflow
from app.engine.pptx_fill.ppt_spec import SLIDE_LAYOUTS


# -----------------------------------------------------------------------------
# Universal Theme Tokens (§3.3)
# -----------------------------------------------------------------------------
def _rgb(red: int, green: int, blue: int) -> Any:
    """Typed boundary over pptx's untyped RGBColor constructor.

    python-pptx ships no type stubs (no types-python-pptx on PyPI), so the
    untyped constructor is called exactly once, here — 17 §3.1 permits a
    ``type: ignore`` with a reason comment (this comment), never a bare escape.
    """
    # python-pptx ships no type stubs (no types-python-pptx on PyPI): the untyped
    # constructor is called exactly once, here — 17 §3.1 permits a type: ignore
    # with a reason comment (this comment), never a bare escape.
    return RGBColor(red, green, blue)  # type: ignore[no-untyped-call]  # reason: pptx has no stubs; single documented boundary


COLOR_BRAND_PRIMARY = _rgb(0x1F, 0x3A, 0x5F)  # #1F3A5F
COLOR_BRAND_SECONDARY = _rgb(0xB7, 0x79, 0x1F)  # #B7791F
COLOR_TEXT_PRIMARY = _rgb(0x1F, 0x29, 0x37)  # #1F2937
COLOR_TEXT_SECONDARY = _rgb(0x6B, 0x72, 0x80)  # #6B7280
COLOR_SURFACE_CARD = _rgb(0xF7, 0xF8, 0xFA)  # #F7F8FA
COLOR_CARD_BORDER = _rgb(0xE5, 0xE7, 0xEB)  # #E5E7EB
COLOR_WHITE = _rgb(0xFF, 0xFF, 0xFF)

COLOR_SEMANTIC_FAV_TEXT = _rgb(0x1B, 0x5E, 0x20)  # #1B5E20
COLOR_SEMANTIC_FAV_FILL = _rgb(0xE8, 0xF5, 0xE9)  # #E8F5E9
COLOR_SEMANTIC_UNFAV_TEXT = _rgb(0xB3, 0x26, 0x1E)  # #B3261E
COLOR_SEMANTIC_UNFAV_FILL = _rgb(0xFD, 0xEC, 0xEA)  # #FDECEA
COLOR_SEMANTIC_WARNING_TEXT = _rgb(0x8A, 0x53, 0x00)  # #8A5300
COLOR_SEMANTIC_WARNING_FILL = _rgb(0xFF, 0xF4, 0xE5)  # #FFF4E5

FONT_FAMILY = "Calibri"

# Geometry & Constants (§3.1)
SLIDE_WIDTH_INCHES = 13.333
SLIDE_HEIGHT_INCHES = 7.5

CANONICAL_DISCLAIMER = (
    "Advisory tool — not professional advice. FP&A Month-End Copilot is an analysis aid. "
    "It highlights potential exceptions, variances, and trends for review. It does not provide "
    "audit, accounting, tax, or legal advice, and it does not guarantee that every error, "
    "misstatement, or irregularity will be detected. All figures, flags, and AI-generated drafts "
    "must be reviewed by a qualified accountant before any business decision, filing, or "
    "external reporting. The tool never posts, approves, or alters accounting records, and "
    "it never replaces professional judgement."
)

SHORT_DISCLAIMER = (
    "Potential exceptions only — advisory tool, not professional advice. "
    "Review by a qualified accountant required. Figures may be revised."
)


# -----------------------------------------------------------------------------
# Input Data Models (§2.2, §4)
# -----------------------------------------------------------------------------
@dataclass
class SourceBatchItem:
    filename: str
    batch_id: int
    row_count: int


@dataclass
class KPICardData:
    label: str
    value: str
    comparison: str
    signal: str = "neutral"  # 'neutral', 'favourable', 'unfavourable', 'warning'


@dataclass
class BridgeDriverItem:
    """One bridge step. Amount is money: Decimal per 17 §5.1 (DEF-015).

    Float inputs are coerced via str (the ``quantize_money`` recovery pattern),
    never via ``Decimal(some_float)``, so sample-data float literals land on
    their intended 2 dp value instead of their binary expansion.
    """

    name: str
    amount: Decimal
    is_favourable: bool = False

    def __post_init__(self) -> None:
        self.amount = quantize_money(self.amount)


@dataclass
class VarianceRow:
    account: str
    actual: str
    budget: str
    variance: str
    var_pct: str
    signal: str
    driver: str


@dataclass
class ExceptionCounts:
    open_count: int = 14
    overdue_count: int = 2
    high_count: int = 3
    unassigned_count: int = 2


@dataclass
class ExceptionRow:
    rule: str
    subject: str
    at_risk: str
    severity: str
    owner: str
    status_age: str


@dataclass
class ForecastCardData:
    label: str
    value: str
    comparison: str


@dataclass
class DeckContext:
    project_name: str = "Alpha Industries Pvt Ltd"
    period: str = "FY26-P09"
    month_year: str = "September 2026"
    window: str = "MTD"
    scenario: str = "Base"
    entities: list[str] = field(default_factory=lambda: ["IN01", "IN02"])
    budget_version: str = "FY26-Approved"
    forecast_version: str = "Base v3"
    forecast_locked: bool = True
    pack_version: int = 3
    issued: bool = False
    generated_at: str = "01-10-2026 14:22"
    app_version: str = "0.9.0"
    rule_set_version: str = "2026-09-30"
    units: str = "₹ whole units"
    grouping: str = "Indian (lakh/crore)"

    # Slide 1 sources and stamp
    sources: list[SourceBatchItem] = field(
        default_factory=lambda: [
            SourceBatchItem("D365 GL Sep-26.xlsx", 1041, 96412),
            SourceBatchItem("Payroll Sep-26.csv", 1042, 1204),
            SourceBatchItem("Procurement Sep-26.xlsx", 1043, 31880),
        ]
    )

    # Slide 2 KPIs
    kpis: list[KPICardData] = field(
        default_factory=lambda: [
            KPICardData("ACTUAL", "₹ 1,66,45,000.00", "vs PY +12.4%"),
            KPICardData("BUDGET", "₹ 1,57,70,000.00", "as budgeted"),
            KPICardData("VARIANCE", "+₹ 8,75,000.00", "+5.5% · Adv ▼", "unfavourable"),
            KPICardData("GROSS MARGIN %", "40.0%", "vs budget +1.2 pp"),
            KPICardData("BUDGET BURN %", "25.8%", "YTD vs annual"),
            KPICardData(
                "EXCEPTIONS OPEN",
                "14 · 2 overdue",
                "3 high priority",
                "warning",
            ),
        ]
    )
    executive_narrative: str = (
        "September landed 5.5% above budget, driven by repairs and third-party contractor costs. "
        "Material costs experienced pressure due to spot steel price fluctuations. "
        "Gross margin remains resilient at 40.0% (+1.2 pp vs approved budget)."
    )
    narrative_author: str = "A. Sharma"
    narrative_date: str = "01-10-2026"

    # Slide 3 Bridge (money: Decimal per 17 §5.1, DEF-015)
    bridge_opening: Decimal = Decimal("15770000.00")
    bridge_closing: Decimal = Decimal("16645000.00")
    bridge_drivers: list[BridgeDriverItem] = field(
        default_factory=lambda: [
            BridgeDriverItem("Materials", Decimal("78000.00"), is_favourable=False),
            BridgeDriverItem("Contractors", Decimal("140000.00"), is_favourable=False),
            BridgeDriverItem("Repairs", Decimal("-25000.00"), is_favourable=True),
            BridgeDriverItem("Utilities", Decimal("2000.00"), is_favourable=False),
            BridgeDriverItem("Opex other", Decimal("180000.00"), is_favourable=False),
        ]
    )

    # Slide 4 Top Variances
    top_variances: list[VarianceRow] = field(
        default_factory=lambda: [
            VarianceRow(
                "5600 Contractors",
                "9,60,000.00",
                "8,20,000.00",
                "+1,40,000.00",
                "+17.1%",
                "Adv ▼",
                "Third-party engineering engagement extended",
            ),
            VarianceRow(
                "5300 Raw Materials",
                "6,18,000.00",
                "5,40,000.00",
                "+78,000.00",
                "+14.4%",
                "Adv ▼",
                "Steel price increase absorbed in Q3 batches",
            ),
            VarianceRow(
                "5200 Factory Repairs",
                "3,55,000.00",
                "3,80,000.00",
                "-25,000.00",
                "-6.6%",
                "Fav ▲",
                "Two scheduled overhauls deferred to Q4",
            ),
            VarianceRow(
                "5800 Utilities & Fuel",
                "2,12,000.00",
                "2,10,000.00",
                "+2,000.00",
                "+1.0%",
                "Adv ▼",
                "Peak tariff adjustment on night shift line",
            ),
            VarianceRow(
                "5900 General Opex",
                "4,90,000.00",
                "3,10,000.00",
                "+1,80,000.00",
                "+58.1%",
                "Adv ▼",
                "Annual regulatory audit & legal advisory fees",
            ),
        ]
    )
    variance_lines_considered: int = 41

    # Slide 5 Exceptions
    exceptions_counts: ExceptionCounts = field(default_factory=ExceptionCounts)
    exceptions_list: list[ExceptionRow] = field(
        default_factory=lambda: [
            ExceptionRow(
                "Dup. invoice",
                "V-00931 / INV-2026-88",
                "45,000.00",
                "High",
                "Rahul",
                "Open · 4 d",
            ),
            ExceptionRow(
                "Cut-off mismatch",
                "V-00412 / 29-Sep-26",
                "3,20,000.00",
                "High",
                "Aarti",
                "In rev · 6 d",
            ),
            ExceptionRow(
                "Round amount",
                "V-01004 / Office Supplies",
                "1,00,000.00",
                "Med",
                "Aarti",
                "Open · 1 d",
            ),
            ExceptionRow(
                "Split purchase",
                "PO-8821 / PO-8822",
                "95,000.00",
                "Med",
                "Rahul",
                "Open · 12 d (Overdue)",
            ),
            ExceptionRow(
                "Dormant vendor",
                "V-00109 / Inactive Co",
                "22,500.00",
                "Low",
                "Unassigned",
                "Open · 3 d",
            ),
        ]
    )
    total_amount_at_risk: str = "5,82,500.00"
    exception_summary: str = (
        "Exception review highlights duplicate vendor invoicing in batch 1041 and "
        "period cut-off timing differences in goods receipt notes. Overdue investigation "
        "cases have been flagged for AP supervisor remediation."
    )

    # Slide 6 Forecast
    forecast_landing_estimate: str = "₹ 12,84,00,000.00"
    forecast_vs_budget: str = "+₹ 34,00,000.00 (+2.7%)"
    forecast_accuracy_mape: str = "1.5% · bias +8k"
    forecast_accuracy_details: str = "8 periods compared · 0 excluded (zero actual)"
    forecast_periods: list[str] = field(
        default_factory=lambda: [
            "P01",
            "P02",
            "P03",
            "P04",
            "P05",
            "P06",
            "P07",
            "P08",
            "P09",
            "P10",
            "P11",
            "P12",
        ]
    )
    forecast_actuals: list[Decimal | None] = field(
        default_factory=lambda: [
            Decimal("140.00"),
            Decimal("145.00"),
            Decimal("150.00"),
            Decimal("148.00"),
            Decimal("155.00"),
            Decimal("160.00"),
            Decimal("158.00"),
            Decimal("162.00"),
            Decimal("166.45"),
            None,
            None,
            None,
        ]
    )
    forecast_projected: list[Decimal | None] = field(
        default_factory=lambda: [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            Decimal("166.45"),
            Decimal("165.00"),
            Decimal("168.00"),
            Decimal("170.00"),
        ]
    )
    forecast_budget: list[Decimal | None] = field(
        default_factory=lambda: [
            Decimal("142.00"),
            Decimal("142.00"),
            Decimal("145.00"),
            Decimal("145.00"),
            Decimal("150.00"),
            Decimal("150.00"),
            Decimal("155.00"),
            Decimal("155.00"),
            Decimal("157.70"),
            Decimal("160.00"),
            Decimal("162.00"),
            Decimal("165.00"),
        ]
    )
    outlook_method_mix: str = "Methods: Remaining budget 62% · 3-mo run-rate 38% · overrides: 0"
    outlook_narrative: str = (
        "Full-year landing estimate projects ₹ 12.84 Cr, representing a +₹ 34 Lakh (+2.7%) variance "
        "against the approved annual budget. Second-half production acceleration accounts for "
        "the volume uptick, while energy cost inflation remains bounded by fixed-price supply agreements."
    )

    def __post_init__(self) -> None:
        # DEF-015: money fields are Decimal end-to-end (17 §5.1). Coerce so a
        # caller passing floats (e.g. legacy sample literals) lands on the
        # intended 2 dp value via str, never on the binary expansion.
        self.bridge_opening = quantize_money(self.bridge_opening)
        self.bridge_closing = quantize_money(self.bridge_closing)
        for attr in ("forecast_actuals", "forecast_projected", "forecast_budget"):
            setattr(
                self,
                attr,
                [None if v is None else quantize_money(v) for v in getattr(self, attr)],
            )


# -----------------------------------------------------------------------------
# Helper Utilities for Slides
# -----------------------------------------------------------------------------
#: ERR-EXP-014 lives with the fill engine that raises it (one implementation, R12).
#: Kept exported here because callers catch ``ExportTemplateError``.
ExportTemplateError = TemplateShapeError

#: Semantic text/fill colours per KPI signal (§3.3).
SIGNAL_TEXT_COLORS = {
    "favourable": COLOR_SEMANTIC_FAV_TEXT,
    "unfavourable": COLOR_SEMANTIC_UNFAV_TEXT,
    "warning": COLOR_SEMANTIC_WARNING_TEXT,
    "neutral": COLOR_BRAND_PRIMARY,
}
SIGNAL_FILL_COLORS = {
    "favourable": COLOR_SEMANTIC_FAV_FILL,
    "unfavourable": COLOR_SEMANTIC_UNFAV_FILL,
    "warning": COLOR_SEMANTIC_WARNING_FILL,
    "neutral": COLOR_SURFACE_CARD,
}


def _fill_footer(slide: Any, slide_num: int, ctx: DeckContext) -> None:
    """Fill the standard footer band (§3.7) into the template's own footer shapes.

    Left carries the short-form disclaimer, right the page/version string; both are
    already positioned and styled at 8 pt secondary by the template.
    """
    prefix = f"PPT-{slide_num:03d}"
    set_text(resolve_shape(slide, f"{prefix}_footer_left"), SHORT_DISCLAIMER)
    set_text(
        resolve_shape(slide, f"{prefix}_footer_right"),
        f"Slide {slide_num} of 6 · Pack v{ctx.pack_version} · {ctx.period}",
        style=TextStyle(align=PP_ALIGN.RIGHT),
    )


def _signal_style(signal: str) -> TextStyle:
    """Run override that recolours a shape to the semantics of its signal (§3.3)."""
    return TextStyle(color=SIGNAL_TEXT_COLORS.get(signal, COLOR_BRAND_PRIMARY))


def _resolve_shape(slide: Any, shape_name: str) -> Any:
    """Resolve a named template shape (ERR-EXP-014 when absent). See §3.6."""
    return resolve_shape(slide, shape_name)


def _slide_shape_names(slide: Any) -> list[str]:
    """Every shape name available on the slide — used by the contract tests."""
    return shape_names(slide)


def _trim_prose(
    text: str,
    width_inches: float,
    height_inches: float,
    font_pt: float,
    max_lines: int,
) -> tuple[str, bool]:
    """Trim prose to its §3.4 character budget.

    Returns the text to write and whether trimming occurred, so the caller can put the
    untrimmed text in the speaker notes (§3.7) and add the trimmed-for-space footnote.
    """
    budget = compute_character_budget(
        box_width_inches=width_inches,
        box_height_inches=height_inches,
        font_size_pt=font_pt,
        configured_max_lines=max_lines,
    )
    return trim_text_to_budget(text, budget)


def _write_prose(
    shape: Any,
    text: str,
    width_inches: float,
    height_inches: float,
    font_pt: float,
    max_lines: int,
) -> tuple[str, bool]:
    """Trim prose to its §3.4 budget, write it, then run the opt-in overflow cascade.

    The cascade runs *after* the write so it measures what the slide actually carries.
    Returns the text written and whether trimming occurred.
    """
    trimmed, was_trimmed = _trim_prose(text, width_inches, height_inches, font_pt, max_lines)
    set_text(shape, trimmed)
    # Flag-gated and off by default (ADR-013); a no-op unless FPA_PPT_OVERFLOW_CASCADE is set.
    handle_overflow(shape, max_lines=max_lines)
    return trimmed, was_trimmed


# -----------------------------------------------------------------------------
# Slide 1: Cover & Metadata (PPT-001)
# -----------------------------------------------------------------------------
def build_slide_1(prs: PresentationObject, ctx: DeckContext) -> Any:
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])

    set_text(_resolve_shape(slide, "PPT-001_title"), ctx.project_name)
    set_text(_resolve_shape(slide, "PPT-001_packline"), f"Month-end pack — {ctx.month_year}")

    entities_str = ", ".join(ctx.entities)
    set_text(
        _resolve_shape(slide, "PPT-001_periodline"),
        f"{ctx.period} · {ctx.window} · {ctx.scenario} · Entities: {entities_str}",
    )

    # Source-files block: up to 7 rows, then a count of the remainder (§3.7).
    source_lines = [
        f"{s.filename} · batch {s.batch_id} · {s.row_count:,} rows" for s in ctx.sources[:7]
    ]
    if len(ctx.sources) > 7:
        source_lines.append(f"… (+{len(ctx.sources) - 7} more files — full list in the Excel pack)")
    set_text(
        _resolve_shape(slide, "PPT-001_sources"),
        ["SOURCES", *source_lines],
        styles=[TextStyle(bold=True), *([None] * len(source_lines))],
    )

    stamp_fields = [
        f"Project:      {ctx.project_name}",
        f"Period:       {ctx.period} ({ctx.window})",
        f"Generated:    {ctx.generated_at}",
        f"Pack:         v{ctx.pack_version} ({'issued' if ctx.issued else 'unissued draft'})",
        f"Budget ver:   {ctx.budget_version}",
        f"Forecast ver: {ctx.forecast_version} ({'locked' if ctx.forecast_locked else 'draft'})",
        f"Units:        {ctx.units}",
        f"Batch IDs:    {', '.join(str(s.batch_id) for s in ctx.sources)}",
    ]
    set_text(
        _resolve_shape(slide, "PPT-001_stamp"),
        ["STAMP", *stamp_fields],
        styles=[TextStyle(bold=True), *([None] * len(stamp_fields))],
    )

    _fill_footer(slide, 1, ctx)

    # Speaker notes: canonical disclaimer + machine readable JSON stamp (TST-PPT-09)
    stamp_dict = {
        "schema": "fpa.ppt.stamp.v1",
        "slide": "PPT-001",
        "generated_at": ctx.generated_at,
        "project": ctx.project_name,
        "entities": ctx.entities,
        "periods": [ctx.period],
        "window": ctx.window,
        "scenario": ctx.scenario,
        "budget_version": ctx.budget_version,
        "forecast_version": ctx.forecast_version,
        "forecast_locked": ctx.forecast_locked,
        "pack_version": ctx.pack_version,
        "issued": ctx.issued,
        "app_version": ctx.app_version,
        "units": ctx.units,
        "sources": [s.batch_id for s in ctx.sources],
    }
    stamp_json = json.dumps(stamp_dict, indent=2)
    set_notes(
        slide,
        f"{CANONICAL_DISCLAIMER}\n\n--- FPA STAMP (JSON) ---\n{stamp_json}\n--- END FPA STAMP ---",
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 2: Executive KPI Dashboard (PPT-002)
# -----------------------------------------------------------------------------
def build_slide_2(prs: PresentationObject, ctx: DeckContext) -> Any:
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])

    set_text(_resolve_shape(slide, "PPT-002_title"), f"Executive summary — {ctx.period}")
    set_text(
        _resolve_shape(slide, "PPT-002_kicker"),
        f"{ctx.window} · {ctx.scenario} · Budget {ctx.budget_version} · "
        f"{len(ctx.entities)} entities",
    )

    # The template carries six KPI blocks laid out 3x2; each is filled by name.
    for idx, kpi in enumerate(ctx.kpis[:6]):
        kpi_num = idx + 1
        signal = kpi.signal
        fill = SIGNAL_FILL_COLORS.get(signal, COLOR_SURFACE_CARD)
        chip = _resolve_shape(slide, f"PPT-002_kpi{kpi_num}_signal")
        chip.fill.solid()
        chip.fill.fore_color.rgb = SIGNAL_TEXT_COLORS.get(signal, COLOR_BRAND_PRIMARY)
        card = _resolve_shape(slide, f"PPT-002_kpi{kpi_num}_card")
        card.fill.solid()
        card.fill.fore_color.rgb = fill

        set_text(_resolve_shape(slide, f"PPT-002_kpi{kpi_num}_label"), kpi.label)
        set_text(
            _resolve_shape(slide, f"PPT-002_kpi{kpi_num}_value"),
            kpi.value,
            style=_signal_style(signal),
        )
        set_text(_resolve_shape(slide, f"PPT-002_kpi{kpi_num}_compare"), kpi.comparison)

    set_text(
        _resolve_shape(slide, "PPT-002_narrative_label"),
        f"Executive narrative · approved by {ctx.narrative_author}, {ctx.narrative_date}",
    )

    narrative_shape = _resolve_shape(slide, "PPT-002_narrative")
    trimmed_narrative, was_trimmed = _write_prose(
        narrative_shape,
        ctx.executive_narrative,
        width_inches=narrative_shape.width.inches,
        height_inches=narrative_shape.height.inches,
        font_pt=12.0,
        max_lines=6,
    )

    foot_text = f"{ctx.units} · month × account × cost centre · Simple sum — no eliminations"
    if was_trimmed:
        foot_text += f" · {TRIMMED_FOOTNOTE}"
    set_text(_resolve_shape(slide, "PPT-002_footnote"), foot_text)

    _fill_footer(slide, 2, ctx)

    set_notes(
        slide,
        f"Slide 2: Executive Summary\n"
        f"Filter: {ctx.period} · {ctx.window} · {ctx.scenario}\n"
        f"Full Executive Narrative:\n{ctx.executive_narrative}",
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 3: Budget vs Actual Bridge / Waterfall (PPT-003)
# -----------------------------------------------------------------------------
def _bridge_plan(
    ctx: DeckContext, max_drivers: int = 6
) -> tuple[list[str], list[Decimal], list[Decimal], Decimal]:
    """Categories plus the two stacked series that draw a bridge (docs/12 §5.2).

    The pinned python-pptx has no waterfall chart type, so the template ships the
    stacked-column fallback: an invisible ``base`` series lifts each step to its
    cumulative height and the visible ``amount`` series carries the step itself. The
    opening and closing bars start at zero and span the whole column.

    A bridge must land on the closing total, so when the supplied drivers do not sum to
    it the shortfall is shown as its own ``Other`` step rather than being absorbed
    silently — §3.7's "the gap is visible and truthful, never interpolated".

    DEF-015: every step is money, so the arithmetic is Decimal end-to-end
    (17 §5.1 — no ``float()``, no ``round()`` on money, no epsilon comparison).
    python-pptx accepts Decimal series values, so no conversion is needed on the
    way into the chart.

    Returns ``(categories, base, amount, residual)`` where ``residual`` is the amount the
    drivers failed to explain (``Decimal("0.00")`` when they tie out exactly).
    """
    ordered = sorted(ctx.bridge_drivers, key=lambda d: abs(d.amount), reverse=True)
    drivers = ordered[:max_drivers]
    opening = quantize_money(ctx.bridge_opening)
    closing = quantize_money(ctx.bridge_closing)
    residual = quantize_money(closing - opening - sum((d.amount for d in drivers), Decimal("0.00")))

    steps = list(drivers)
    if residual != 0:
        steps.append(BridgeDriverItem("Other", residual, is_favourable=residual < 0))

    categories = ["Opening (Budget)"]
    base = [Decimal("0.00")]
    amount = [opening]

    running = opening
    for driver in steps:
        categories.append(driver.name[:12])
        base.append(quantize_money(running))
        amount.append(quantize_money(driver.amount))
        running = quantize_money(running + driver.amount)

    categories.append("Closing (Actual)")
    base.append(Decimal("0.00"))
    amount.append(closing)
    return categories, base, amount, residual


def build_slide_3(prs: PresentationObject, ctx: DeckContext) -> Any:
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])

    set_text(_resolve_shape(slide, "PPT-003_title"), f"BvA bridge — {ctx.period}")
    set_text(
        _resolve_shape(slide, "PPT-003_kicker"),
        f"{ctx.window} · {ctx.scenario} · drivers ordered by materiality",
    )

    categories, base, amount, residual = _bridge_plan(ctx)
    replace_chart_data(
        _resolve_shape(slide, "PPT-003_chart_bridge"),
        categories,
        [("base", base), ("amount", amount)],
        title=f"Bridge: {ctx.period} ({ctx.units} · {ctx.window})",
        legend=False,
    )

    ordered_drivers = sorted(ctx.bridge_drivers, key=lambda d: abs(d.amount), reverse=True)[:6]
    driver_lines = [
        f"{'▲' if d.is_favourable else '▼'} {d.name}   "
        f"{'+' if d.amount >= 0 else '−'}₹ {abs(d.amount):,.2f}"
        for d in ordered_drivers
    ]
    driver_styles: list[TextStyle | None] = [
        TextStyle(bold=True, color=COLOR_TEXT_SECONDARY),
        *(
            TextStyle(
                color=COLOR_SEMANTIC_FAV_TEXT if d.is_favourable else COLOR_SEMANTIC_UNFAV_TEXT
            )
            for d in ordered_drivers
        ),
    ]
    if residual != 0:
        driver_lines.append(
            f"{'▼' if residual >= 0 else '▲'} Other (unexplained)   "
            f"{'+' if residual >= 0 else '−'}₹ {abs(residual):,.2f}"
        )
        driver_styles.append(TextStyle(color=COLOR_TEXT_PRIMARY))
    set_text(
        _resolve_shape(slide, "PPT-003_drivers"),
        ["TOP DRIVERS", *driver_lines],
        styles=driver_styles,
    )

    if residual == 0:
        tie_text = "Opening + Σ drivers = Closing — OK"
    else:
        tie_text = (
            f"Opening + Σ drivers + Other = Closing — OK "
            f"(Other = {residual:+,.2f}, unexplained by the driver set)"
        )
    set_text(
        _resolve_shape(slide, "PPT-003_tieout"),
        f"{tie_text} · {ctx.units} · month × account × cost centre",
    )

    _fill_footer(slide, 3, ctx)

    set_notes(
        slide,
        f"Slide 3: Budget vs Actual Bridge\n"
        f"Opening Budget: ₹ {ctx.bridge_opening:,.2f}\n"
        f"Closing Actual: ₹ {ctx.bridge_closing:,.2f}\n"
        f"Tie-out verified: Opening + Drivers = Closing.",
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 4: Top Variances with Drivers (PPT-004)
# -----------------------------------------------------------------------------
def build_slide_4(prs: PresentationObject, ctx: DeckContext) -> Any:
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-004"])

    set_text(_resolve_shape(slide, "PPT-004_title"), f"Top variances — {ctx.period}")
    set_text(
        _resolve_shape(slide, "PPT-004_kicker"),
        f"{ctx.window} · {ctx.scenario} · "
        f"5 largest absolute variances of {ctx.variance_lines_considered} lines",
    )

    # The template's table is 7 columns x 6 rows (header + top 5); widths and the
    # header banding are authored in the template, so only values are written here.
    headers = ["Account", "Actual", "Budget", "Variance", "Var %", "Sig.", "Driver"]
    rows: list[list[str]] = [headers]
    rows += [
        [v.account, v.actual, v.budget, v.variance, v.var_pct, v.signal, v.driver]
        for v in ctx.top_variances[:5]
    ]
    rows += [[""] * 7 for _ in range(max(0, 6 - len(rows)))]

    cell_styles: dict[tuple[int, int], TextStyle | None] = {}
    row_fills: dict[int, Any] = {}
    for row_index, var in enumerate(ctx.top_variances[:5], start=1):
        row_fills[row_index] = COLOR_SURFACE_CARD if row_index % 2 == 1 else COLOR_WHITE
        for column_index in (1, 2, 3, 4):
            cell_styles[(row_index, column_index)] = TextStyle(align=PP_ALIGN.RIGHT)
        cell_styles[(row_index, 5)] = TextStyle(
            bold=True,
            align=PP_ALIGN.CENTER,
            color=COLOR_SEMANTIC_FAV_TEXT if "Fav" in var.signal else COLOR_SEMANTIC_UNFAV_TEXT,
        )

    fill_table(
        _resolve_shape(slide, "PPT-004_table"),
        rows,
        header=False,
        cell_styles=cell_styles,
        row_fills=row_fills,
    )

    set_text(
        _resolve_shape(slide, "PPT-004_provenance"),
        f"Commentary: approved by {ctx.narrative_author}, {ctx.narrative_date} · "
        f"Rule-based narrative baseline",
    )
    set_text(
        _resolve_shape(slide, "PPT-004_notes_line"),
        "Full commentary for the top 10 lines: speaker notes, the Excel pack and the commentary editor.",
    )

    _fill_footer(slide, 4, ctx)

    set_notes(
        slide,
        f"Slide 4: Top Variances\n"
        f"Total lines evaluated: {ctx.variance_lines_considered}\n"
        f"Top 5 lines presented natively above.",
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 5: Exceptions & Risk Register (PPT-005)
# -----------------------------------------------------------------------------
def build_slide_5(prs: PresentationObject, ctx: DeckContext) -> Any:
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-005"])

    set_text(_resolve_shape(slide, "PPT-005_title"), f"Exceptions and control risks — {ctx.period}")
    set_text(
        _resolve_shape(slide, "PPT-005_kicker"),
        f"Rule set {ctx.rule_set_version} · run 118 · {ctx.generated_at}",
    )

    counts = ctx.exceptions_counts
    chip_labels = ["OPEN", "OVERDUE", "HIGH", "UNASSIGNED"]
    chip_vals = [
        counts.open_count,
        counts.overdue_count,
        counts.high_count,
        counts.unassigned_count,
    ]
    for idx in range(4):
        chip_num = idx + 1
        is_overdue = idx == 1
        chip = _resolve_shape(slide, f"PPT-005_chip{chip_num}")
        chip.fill.solid()
        chip.fill.fore_color.rgb = COLOR_SEMANTIC_WARNING_FILL if is_overdue else COLOR_SURFACE_CARD
        label_style = TextStyle(
            bold=True,
            color=COLOR_SEMANTIC_WARNING_TEXT if is_overdue else None,
        )
        value_style = TextStyle(
            bold=True,
            color=COLOR_SEMANTIC_WARNING_TEXT if is_overdue else COLOR_BRAND_PRIMARY,
        )
        set_text(
            _resolve_shape(slide, f"PPT-005_chip{chip_num}_label"),
            chip_labels[idx],
            style=label_style,
        )
        set_text(
            _resolve_shape(slide, f"PPT-005_chip{chip_num}_value"),
            str(chip_vals[idx]),
            style=value_style,
        )

    set_text(
        _resolve_shape(slide, "PPT-005_risknote"),
        f"Potential exception — requires accounting review. These are leads, not verdicts. · "
        f"Σ amount at risk ₹ {ctx.total_amount_at_risk} (indicator only)",
    )

    headers = ["Rule", "Subject", "At risk", "Sev.", "Owner", "Status / Age"]
    rows: list[list[str]] = [headers]
    rows += [
        [e.rule, e.subject, e.at_risk, e.severity, e.owner, e.status_age]
        for e in ctx.exceptions_list[:5]
    ]
    rows += [[""] * 6 for _ in range(max(0, 6 - len(rows)))]

    cell_styles: dict[tuple[int, int], TextStyle | None] = {}
    row_fills: dict[int, Any] = {}
    for row_index, exc in enumerate(ctx.exceptions_list[:5], start=1):
        row_fills[row_index] = COLOR_SURFACE_CARD if row_index % 2 == 1 else COLOR_WHITE
        cell_styles[(row_index, 2)] = TextStyle(align=PP_ALIGN.RIGHT)
        cell_styles[(row_index, 3)] = TextStyle(
            bold=True,
            color=COLOR_SEMANTIC_UNFAV_TEXT if exc.severity == "High" else COLOR_TEXT_PRIMARY,
        )

    fill_table(
        _resolve_shape(slide, "PPT-005_table"),
        rows,
        header=False,
        cell_styles=cell_styles,
        row_fills=row_fills,
    )

    summary_shape = _resolve_shape(slide, "PPT-005_summary")
    trimmed_summary, was_trimmed = _write_prose(
        summary_shape,
        f"Exception summary: {ctx.exception_summary}",
        width_inches=summary_shape.width.inches,
        height_inches=summary_shape.height.inches,
        font_pt=11.0,
        max_lines=4,
    )
    if was_trimmed:
        set_text(summary_shape, f"{trimmed_summary} · {TRIMMED_FOOTNOTE}")

    _fill_footer(slide, 5, ctx)

    set_notes(
        slide,
        f"Slide 5: Exceptions & Risk Register\n"
        f"Open Exceptions: {ctx.exceptions_counts.open_count}\n"
        f"Overdue: {ctx.exceptions_counts.overdue_count}\n"
        f"Full Exception Summary:\n{ctx.exception_summary}",
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 6: Rolling Forecast & Outlook (PPT-006)
# -----------------------------------------------------------------------------
def build_slide_6(prs: PresentationObject, ctx: DeckContext) -> Any:
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-006"])

    set_text(_resolve_shape(slide, "PPT-006_title"), f"Forecast and outlook — {ctx.period}")
    lock_status = (
        f"locked {ctx.generated_at.split()[0]}" if ctx.forecast_locked else "draft NOT LOCKED"
    )
    set_text(
        _resolve_shape(slide, "PPT-006_scenario"),
        f"Scenario {ctx.scenario} · version {ctx.forecast_version} ({lock_status}) · "
        f"method mix: remaining budget 62% / run rate 38%",
    )

    cards_data = [
        ForecastCardData(
            "LANDING ESTIMATE (FY)",
            ctx.forecast_landing_estimate,
            "YTD actual + forecast remaining",
        ),
        ForecastCardData("VS ANNUAL BUDGET", ctx.forecast_vs_budget, f"as at {ctx.period}"),
        ForecastCardData(
            "ACCURACY (MAPE-lite)",
            ctx.forecast_accuracy_mape,
            ctx.forecast_accuracy_details,
        ),
    ]
    for idx, cdata in enumerate(cards_data, start=1):
        set_text(_resolve_shape(slide, f"PPT-006_card{idx}_label"), cdata.label)
        set_text(_resolve_shape(slide, f"PPT-006_card{idx}_value"), cdata.value)
        set_text(_resolve_shape(slide, f"PPT-006_card{idx}_compare"), cdata.comparison)

    # Native line chart with markers (§5.3). The gap between closed and forecast
    # periods stays visible: actuals stop, the forecast series starts, nothing bridges.
    replace_chart_data(
        _resolve_shape(slide, "PPT-006_chart_forecast"),
        ctx.forecast_periods,
        [
            ("Actual", ctx.forecast_actuals),
            ("Forecast", ctx.forecast_projected),
            ("Budget", ctx.forecast_budget),
        ],
        title=f"Forecast vs Actual: {ctx.scenario} ({ctx.forecast_version}) · ₹ Lakhs",
        legend=True,
    )

    outlook_shape = _resolve_shape(slide, "PPT-006_outlook")
    outlook_lines = [
        ctx.outlook_method_mix,
        f"Outlook narrative · approved by {ctx.narrative_author}, {ctx.narrative_date}",
        _trim_prose(
            ctx.outlook_narrative,
            width_inches=outlook_shape.width.inches,
            height_inches=outlook_shape.height.inches,
            font_pt=11.0,
            max_lines=12,
        )[0],
    ]
    if outlook_lines[2] != ctx.outlook_narrative:
        outlook_lines[2] += f"\n[{TRIMMED_FOOTNOTE}]"
    set_text(
        outlook_shape,
        outlook_lines,
        styles=[
            TextStyle(size_pt=9, color=COLOR_TEXT_SECONDARY),
            TextStyle(size_pt=9, color=COLOR_TEXT_SECONDARY),
            None,
        ],
    )
    # Flag-gated and off by default (ADR-013); runs against the final three lines.
    handle_overflow(outlook_shape, max_lines=12)

    set_text(_resolve_shape(slide, "PPT-006_disclaimer"), CANONICAL_DISCLAIMER)

    _fill_footer(slide, 6, ctx)

    set_notes(
        slide,
        f"{CANONICAL_DISCLAIMER}\n\n"
        f"Slide 6: Rolling Forecast & Outlook\n"
        f"Forecast Version: {ctx.forecast_version} ({'Locked' if ctx.forecast_locked else 'Draft'})\n"
        f"Landing Estimate: {ctx.forecast_landing_estimate}\n"
        f"Full Outlook Text:\n{ctx.outlook_narrative}",
    )
    return slide


# -----------------------------------------------------------------------------
# Main Generation Entrypoint
# -----------------------------------------------------------------------------
def generate_powerpoint_deck(
    context: DeckContext | None = None,
    output_path: str | Path | None = None,
) -> PresentationObject:
    """Generate the complete 6-slide PowerPoint presentation pack.

    Parameters:
        context: DeckContext configuration and data; if None, default context is used.
        output_path: Optional file path to write the .pptx presentation.

    Returns:
        pptx.Presentation instance — a filled copy of the committed template.
    """
    ctx = context or DeckContext()

    # docs/12 §3.6 + DEF-018: open the template and fill it — never build from scratch.
    # The resolver prefers a client base deck and falls back to the shipped template.
    # open_template() is annotated with pptx's factory-as-type in pptx_fill (out of
    # lane here); the cast pins the real Presentation class for this module.
    prs: PresentationObject = open_template()

    # Configure 16:9 widescreen dimensions (§3.1)
    prs.slide_width = Inches(SLIDE_WIDTH_INCHES)
    prs.slide_height = Inches(SLIDE_HEIGHT_INCHES)

    # Build the 6 contract slides in exact order
    build_slide_1(prs, ctx)
    build_slide_2(prs, ctx)
    build_slide_3(prs, ctx)
    build_slide_4(prs, ctx)
    build_slide_5(prs, ctx)
    build_slide_6(prs, ctx)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        tmp_p = out_p.with_suffix(".tmp")
        try:
            prs.save(str(tmp_p))
            tmp_p.replace(out_p)
        except Exception:
            if tmp_p.exists():
                tmp_p.unlink()
            raise

    return prs
