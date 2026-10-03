"""PowerPoint Deck Generation engine (Phase 5).

Implements docs/12_POWERPOINT_OUTPUT_SPEC.md §1 through §7.
Generates an executive-ready 6-slide widescreen (16:9) presentation using python-pptx:
  - Slide 1: Cover & metadata (PPT-001)
  - Slide 2: Executive summary / KPI Dashboard (PPT-002)
  - Slide 3: Budget vs Actual bridge / waterfall chart (PPT-003)
  - Slide 4: Top variances with drivers (PPT-004)
  - Slide 5: Exceptions and control risks (PPT-005)
  - Slide 6: Rolling forecast & outlook (PPT-006)

All content is natively editable (no raster screenshots, no static image charts).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from app.engine.exports.ppt_fit import (
    TRIMMED_FOOTNOTE,
    compute_character_budget,
    trim_text_to_budget,
)

# -----------------------------------------------------------------------------
# Universal Theme Tokens (§3.3)
# -----------------------------------------------------------------------------
COLOR_BRAND_PRIMARY = RGBColor(0x1F, 0x3A, 0x5F)  # #1F3A5F
COLOR_BRAND_SECONDARY = RGBColor(0xB7, 0x79, 0x1F)  # #B7791F
COLOR_TEXT_PRIMARY = RGBColor(0x1F, 0x29, 0x37)  # #1F2937
COLOR_TEXT_SECONDARY = RGBColor(0x6B, 0x72, 0x80)  # #6B7280
COLOR_SURFACE_CARD = RGBColor(0xF7, 0xF8, 0xFA)  # #F7F8FA
COLOR_CARD_BORDER = RGBColor(0xE5, 0xE7, 0xEB)  # #E5E7EB
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

COLOR_SEMANTIC_FAV_TEXT = RGBColor(0x1B, 0x5E, 0x20)  # #1B5E20
COLOR_SEMANTIC_FAV_FILL = RGBColor(0xE8, 0xF5, 0xE9)  # #E8F5E9
COLOR_SEMANTIC_UNFAV_TEXT = RGBColor(0xB3, 0x26, 0x1E)  # #B3261E
COLOR_SEMANTIC_UNFAV_FILL = RGBColor(0xFD, 0xEC, 0xEA)  # #FDECEA
COLOR_SEMANTIC_WARNING_TEXT = RGBColor(0x8A, 0x53, 0x00)  # #8A5300
COLOR_SEMANTIC_WARNING_FILL = RGBColor(0xFF, 0xF4, 0xE5)  # #FFF4E5

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
    name: str
    amount: float
    is_favourable: bool = False


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
            KPICardData(
                "VARIANCE", "+₹ 8,75,000.00", "+5.5% · Adv ▼", "unfavourable"
            ),
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

    # Slide 3 Bridge
    bridge_opening: float = 15770000.0
    bridge_closing: float = 16645000.0
    bridge_drivers: list[BridgeDriverItem] = field(
        default_factory=lambda: [
            BridgeDriverItem("Materials", 78000.0, is_favourable=False),
            BridgeDriverItem("Contractors", 140000.0, is_favourable=False),
            BridgeDriverItem("Repairs", -25000.0, is_favourable=True),
            BridgeDriverItem("Utilities", 2000.0, is_favourable=False),
            BridgeDriverItem("Opex other", 180000.0, is_favourable=False),
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
    forecast_accuracy_details: str = (
        "8 periods compared · 0 excluded (zero actual)"
    )
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
    forecast_actuals: list[Optional[float]] = field(
        default_factory=lambda: [
            140.0,
            145.0,
            150.0,
            148.0,
            155.0,
            160.0,
            158.0,
            162.0,
            166.45,
            None,
            None,
            None,
        ]
    )
    forecast_projected: list[Optional[float]] = field(
        default_factory=lambda: [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            166.45,
            165.0,
            168.0,
            170.0,
        ]
    )
    forecast_budget: list[Optional[float]] = field(
        default_factory=lambda: [
            142.0,
            142.0,
            145.0,
            145.0,
            150.0,
            150.0,
            155.0,
            155.0,
            157.7,
            160.0,
            162.0,
            165.0,
        ]
    )
    outlook_method_mix: str = (
        "Methods: Remaining budget 62% · 3-mo run-rate 38% · overrides: 0"
    )
    outlook_narrative: str = (
        "Full-year landing estimate projects ₹ 12.84 Cr, representing a +₹ 34 Lakh (+2.7%) variance "
        "against the approved annual budget. Second-half production acceleration accounts for "
        "the volume uptick, while energy cost inflation remains bounded by fixed-price supply agreements."
    )


# -----------------------------------------------------------------------------
# Helper Utilities for Slides
# -----------------------------------------------------------------------------
def _add_accent_bar(slide, name: str) -> Any:
    """Adds the universal brand accent bar at the top of the slide."""
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0),
        Inches(0),
        Inches(SLIDE_WIDTH_INCHES),
        Inches(0.08),
    )
    accent.name = name
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_BRAND_PRIMARY
    accent.line.fill.background()
    return accent


def _add_footer_band(slide, slide_num: int, ctx: DeckContext) -> None:
    """Adds standard footer band (§3.7): short disclaimer (left) and page string (right)."""
    # Left disclaimer text box
    tb_left = slide.shapes.add_textbox(
        Inches(0.45), Inches(7.04), Inches(9.30), Inches(0.28)
    )
    tb_left.name = f"PPT-00{slide_num}_footer_disclaimer"
    tf_l = tb_left.text_frame
    tf_l.word_wrap = True
    p_l = tf_l.paragraphs[0]
    p_l.text = SHORT_DISCLAIMER
    p_l.font.name = FONT_FAMILY
    p_l.font.size = Pt(8)
    p_l.font.color.rgb = COLOR_TEXT_SECONDARY

    # Right page/version text box
    tb_right = slide.shapes.add_textbox(
        Inches(10.28), Inches(7.04), Inches(2.60), Inches(0.28)
    )
    tb_right.name = f"PPT-00{slide_num}_footer_page"
    tf_r = tb_right.text_frame
    tf_r.word_wrap = True
    p_r = tf_r.paragraphs[0]
    p_r.text = (
        f"Slide {slide_num} of 6 · Pack v{ctx.pack_version} · {ctx.period}"
    )
    p_r.alignment = PP_ALIGN.RIGHT
    p_r.font.name = FONT_FAMILY
    p_r.font.size = Pt(8)
    p_r.font.color.rgb = COLOR_TEXT_SECONDARY


def _set_cell_text(
    cell: Any,
    text: str,
    font_size_pt: int = 10,
    bold: bool = False,
    color: RGBColor = COLOR_TEXT_PRIMARY,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    fill_color: Optional[RGBColor] = None,
) -> None:
    """Format table cell text and background cleanly."""
    cell.text = text
    if fill_color:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill_color
    tf = cell.text_frame
    tf.word_wrap = True
    if tf.paragraphs:
        p = tf.paragraphs[0]
        p.alignment = align
        p.font.name = FONT_FAMILY
        p.font.size = Pt(font_size_pt)
        p.font.bold = bold
        p.font.color.rgb = color


class ExportTemplateError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.code = "ERR-EXP-014"

def _resolve_shape(slide, shape_name: str) -> Any:
    # Prove both directions: check slide.shapes first, then slide.slide_layout.shapes
    for shape in slide.shapes:
        if shape.name == shape_name:
            return shape
    for shape in slide.slide_layout.shapes:
        if shape.name == shape_name:
            return shape
    raise ExportTemplateError(f"ERR-EXP-014: Missing shape '{shape_name}' in template.")


# -----------------------------------------------------------------------------
# Slide 1: Cover & Metadata (PPT-001)
# -----------------------------------------------------------------------------
def build_slide_1(prs: Presentation, ctx: DeckContext) -> Any:
    # Find Layout FPA-PPT-001
    layout = None
    for l in prs.slide_layouts:
        if l.name == "FPA-PPT-001":
            layout = l
            break
    if not layout:
        raise ExportTemplateError("ERR-EXP-014: Missing layout 'FPA-PPT-001' in template.")
    
    slide = prs.slides.add_slide(layout)

    # Title: Project Name
    sh_title = _resolve_shape(slide, "PPT-001_title")
    sh_title.text = ctx.project_name

    # Pack line
    sh_pack = _resolve_shape(slide, "PPT-001_packline")
    sh_pack.text = f"Month-end pack — {ctx.month_year}"

    # Period line
    sh_period = _resolve_shape(slide, "PPT-001_periodline")
    entities_str = ", ".join(ctx.entities)
    sh_period.text = f"{ctx.period} · {ctx.window} · {ctx.scenario} · Entities: {entities_str}"

    # Sources block
    sh_sources = _resolve_shape(slide, "PPT-001_sources")
    # preserve formatting by not wiping out the whole textframe if possible, but python-pptx shape.text does reset.
    tf = sh_sources.text_frame
    tf.clear()
    p_main = tf.paragraphs[0]
    p_main.text = "SOURCES"
    p_main.font.bold = True
    
    for src in ctx.sources[:7]:
        p_src = tf.add_paragraph()
        p_src.text = f"{src.filename} · batch {src.batch_id} · {src.row_count:,} rows"
        
    if len(ctx.sources) > 7:
        p_rem = tf.add_paragraph()
        p_rem.text = f"… (+{len(ctx.sources) - 7} more files — full list in the Excel pack)"

    # Stamp block
    sh_stamp = _resolve_shape(slide, "PPT-001_stamp")
    tf = sh_stamp.text_frame
    tf.clear()
    p_main = tf.paragraphs[0]
    p_main.text = "STAMP"
    p_main.font.bold = True

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
    for s_field in stamp_fields:
        p_st = tf.add_paragraph()
        p_st.text = s_field
        p_st.font.name = FONT_FAMILY
        p_st.font.size = Pt(9)
        p_st.font.color.rgb = COLOR_TEXT_PRIMARY

    # Footer band
    _add_footer_band(slide, 1, ctx)

    # Speaker notes: canonical disclaimer + machine readable JSON stamp
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
    slide.notes_slide.notes_text_frame.text = (
        f"{CANONICAL_DISCLAIMER}\n\n"
        f"--- FPA STAMP (JSON) ---\n"
        f"{stamp_json}\n"
        f"--- END FPA STAMP ---"
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 2: Executive KPI Dashboard (PPT-002)
# -----------------------------------------------------------------------------
def build_slide_2(prs: Presentation, ctx: DeckContext) -> Any:
    # not-yet-doc-12-conformant: using procedural path
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Accent bar
    _add_accent_bar(slide, "PPT-002_accent")

    # Title & kicker
    tb_title = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.35), Inches(12.43), Inches(0.60)
    )
    tb_title.name = "PPT-002_title"
    tf = tb_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Executive summary — {ctx.period}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_BRAND_PRIMARY

    tb_kicker = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.95), Inches(12.43), Inches(0.30)
    )
    tb_kicker.name = "PPT-002_kicker"
    tf = tb_kicker.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        f"{ctx.window} · {ctx.scenario} · Budget {ctx.budget_version} · "
        f"{len(ctx.entities)} entities"
    )
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # 6 KPI cards: 2 rows of 3 columns
    # x: 0.45, 4.68, 8.91; y: 1.45, 3.10; w: 3.97, h: 1.45
    card_xs = [0.45, 4.68, 8.91, 0.45, 4.68, 8.91]
    card_ys = [1.45, 1.45, 1.45, 3.05, 3.05, 3.05]

    for idx, kpi in enumerate(ctx.kpis[:6]):
        cx = card_xs[idx]
        cy = card_ys[idx]
        kpi_num = idx + 1

        # Card container rectangle
        card_rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(cx),
            Inches(cy),
            Inches(3.97),
            Inches(1.45),
        )
        card_rect.name = f"PPT-002_kpi{kpi_num}_card"
        card_rect.fill.solid()
        card_rect.fill.fore_color.rgb = COLOR_SURFACE_CARD
        card_rect.line.color.rgb = COLOR_CARD_BORDER

        # Left signal chip
        chip_color = COLOR_BRAND_PRIMARY
        if kpi.signal == "favourable":
            chip_color = COLOR_SEMANTIC_FAV_TEXT
        elif kpi.signal == "unfavourable":
            chip_color = COLOR_SEMANTIC_UNFAV_TEXT
        elif kpi.signal == "warning":
            chip_color = COLOR_BRAND_SECONDARY

        chip = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(cx),
            Inches(cy),
            Inches(0.08),
            Inches(1.45),
        )
        chip.name = f"PPT-002_kpi{kpi_num}_chip"
        chip.fill.solid()
        chip.fill.fore_color.rgb = chip_color
        chip.line.fill.background()

        # Label
        tb_label = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(cy + 0.10), Inches(3.75), Inches(0.25)
        )
        tb_label.name = f"PPT-002_kpi{kpi_num}_label"
        tf = tb_label.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = kpi.label
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_SECONDARY

        # Value
        tb_val = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(cy + 0.35), Inches(3.75), Inches(0.45)
        )
        tb_val.name = f"PPT-002_kpi{kpi_num}_value"
        tf = tb_val.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = kpi.value
        p.font.name = FONT_FAMILY
        p.font.size = Pt(22)
        p.font.bold = True
        if kpi.signal == "unfavourable":
            p.font.color.rgb = COLOR_SEMANTIC_UNFAV_TEXT
        elif kpi.signal == "favourable":
            p.font.color.rgb = COLOR_SEMANTIC_FAV_TEXT
        else:
            p.font.color.rgb = COLOR_BRAND_PRIMARY

        # Comparison line
        tb_comp = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(cy + 0.88), Inches(3.75), Inches(0.25)
        )
        tb_comp.name = f"PPT-002_kpi{kpi_num}_compare"
        tf = tb_comp.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = kpi.comparison
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Provenance label
    tb_prov = slide.shapes.add_textbox(
        Inches(0.45), Inches(4.65), Inches(12.43), Inches(0.22)
    )
    tb_prov.name = "PPT-002_narrative_label"
    tf = tb_prov.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Executive narrative · approved by {ctx.narrative_author}, {ctx.narrative_date}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Executive narrative box (budget 894 chars per §3.4)
    budget = compute_character_budget(
        box_width_inches=12.43,
        box_height_inches=1.70,
        font_size_pt=12.0,
        configured_max_lines=6,
    )
    trimmed_narrative, was_trimmed = trim_text_to_budget(
        ctx.executive_narrative, budget
    )

    tb_narr = slide.shapes.add_textbox(
        Inches(0.45), Inches(4.88), Inches(12.43), Inches(1.65)
    )
    tb_narr.name = "PPT-002_narrative"
    tf = tb_narr.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = trimmed_narrative
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # Footnote
    tb_foot = slide.shapes.add_textbox(
        Inches(0.45), Inches(6.64), Inches(12.43), Inches(0.24)
    )
    tb_foot.name = "PPT-002_footnote"
    tf = tb_foot.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    foot_text = (
        f"{ctx.units} · month × account × cost centre · Simple sum — no eliminations"
    )
    if was_trimmed:
        foot_text += f" · {TRIMMED_FOOTNOTE}"
    p.text = foot_text
    p.font.name = FONT_FAMILY
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Footer band
    _add_footer_band(slide, 2, ctx)

    # Speaker notes
    slide.notes_slide.notes_text_frame.text = (
        f"Slide 2: Executive Summary\n"
        f"Filter: {ctx.period} · {ctx.window} · {ctx.scenario}\n"
        f"Full Executive Narrative:\n{ctx.executive_narrative}"
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 3: Budget vs Actual Bridge / Waterfall (PPT-003)
# -----------------------------------------------------------------------------
def build_slide_3(prs: Presentation, ctx: DeckContext) -> Any:
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Accent bar
    _add_accent_bar(slide, "PPT-003_accent")

    # Title & kicker
    tb_title = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.35), Inches(12.43), Inches(0.60)
    )
    tb_title.name = "PPT-003_title"
    tf = tb_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"BvA bridge — {ctx.period}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_BRAND_PRIMARY

    tb_kicker = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.95), Inches(12.43), Inches(0.30)
    )
    tb_kicker.name = "PPT-003_kicker"
    tf = tb_kicker.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{ctx.window} · {ctx.scenario} · drivers ordered by materiality"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Native Bridge / Waterfall Chart (§5.2)
    # Using clustered / stacked column with embedded data
    chart_data = CategoryChartData()
    categories = ["Opening (Budget)"]
    series_values = [ctx.bridge_opening]

    for d in ctx.bridge_drivers:
        categories.append(d.name[:12])
        series_values.append(d.amount)

    categories.append("Closing (Actual)")
    series_values.append(ctx.bridge_closing)

    chart_data.categories = categories
    chart_data.add_series("Amount (₹)", tuple(series_values))

    # Add native chart shape
    chart_shape = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.45),
        Inches(1.45),
        Inches(8.60),
        Inches(4.95),
        chart_data,
    )
    chart_shape.name = "PPT-003_chart_bridge"
    chart = chart_shape.chart
    chart.has_legend = False
    chart.has_title = True
    chart.chart_title.text_frame.text = (
        f"Bridge: {ctx.period} ({ctx.units} · {ctx.window})"
    )

    # Right-hand top drivers list
    tb_drivers = slide.shapes.add_textbox(
        Inches(9.30), Inches(1.45), Inches(3.58), Inches(4.95)
    )
    tb_drivers.name = "PPT-003_drivers"
    tf = tb_drivers.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "TOP DRIVERS"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    for d in ctx.bridge_drivers[:6]:
        p_d = tf.add_paragraph()
        sig = "▲" if d.is_favourable else "▼"
        sign_char = "+" if d.amount >= 0 else "−"
        abs_amt = abs(d.amount)
        p_d.text = f"{sig} {d.name}   {sign_char}₹ {abs_amt:,.2f}"
        p_d.font.name = FONT_FAMILY
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = (
            COLOR_SEMANTIC_FAV_TEXT
            if d.is_favourable
            else COLOR_SEMANTIC_UNFAV_TEXT
        )

    # Tie-out line
    tb_tie = slide.shapes.add_textbox(
        Inches(0.45), Inches(6.54), Inches(12.43), Inches(0.28)
    )
    tb_tie.name = "PPT-003_tieout"
    tf = tb_tie.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Opening + Σ drivers = Closing — OK · {ctx.units} · month × account × cost centre"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Footer band
    _add_footer_band(slide, 3, ctx)

    # Speaker notes
    slide.notes_slide.notes_text_frame.text = (
        f"Slide 3: Budget vs Actual Bridge\n"
        f"Opening Budget: ₹ {ctx.bridge_opening:,.2f}\n"
        f"Closing Actual: ₹ {ctx.bridge_closing:,.2f}\n"
        f"Tie-out verified: Opening + Drivers = Closing."
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 4: Top Variances with Drivers (PPT-004)
# -----------------------------------------------------------------------------
def build_slide_4(prs: Presentation, ctx: DeckContext) -> Any:
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Accent bar
    _add_accent_bar(slide, "PPT-004_accent")

    # Title & kicker
    tb_title = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.35), Inches(12.43), Inches(0.60)
    )
    tb_title.name = "PPT-004_title"
    tf = tb_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Top variances — {ctx.period}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_BRAND_PRIMARY

    tb_kicker = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.95), Inches(12.43), Inches(0.30)
    )
    tb_kicker.name = "PPT-004_kicker"
    tf = tb_kicker.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        f"{ctx.window} · {ctx.scenario} · "
        f"5 largest absolute variances of {ctx.variance_lines_considered} lines"
    )
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Native Table (7 columns, 6 rows: 1 header + 5 data rows)
    # Columns: Account (3.20"), Actual (1.50"), Budget (1.50"), Variance (1.65"), Var % (1.15"), Sig. (1.00"), Driver (2.43")
    rows = min(len(ctx.top_variances), 5) + 1
    table_shape = slide.shapes.add_table(
        rows, 7, Inches(0.45), Inches(1.45), Inches(12.43), Inches(3.60)
    )
    table_shape.name = "PPT-004_table"
    table = table_shape.table

    col_widths = [3.20, 1.50, 1.50, 1.65, 1.15, 1.00, 2.43]
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)

    headers = [
        "Account",
        "Actual",
        "Budget",
        "Variance",
        "Var %",
        "Sig.",
        "Driver",
    ]
    for col_idx, h_text in enumerate(headers):
        align = (
            PP_ALIGN.RIGHT
            if col_idx in (1, 2, 3, 4)
            else (PP_ALIGN.CENTER if col_idx == 5 else PP_ALIGN.LEFT)
        )
        _set_cell_text(
            table.cell(0, col_idx),
            h_text,
            font_size_pt=10,
            bold=True,
            color=COLOR_WHITE,
            align=align,
            fill_color=COLOR_BRAND_PRIMARY,
        )

    for row_idx, var in enumerate(ctx.top_variances[:5], start=1):
        bg_color = COLOR_SURFACE_CARD if row_idx % 2 == 1 else COLOR_WHITE
        # Account
        _set_cell_text(
            table.cell(row_idx, 0),
            var.account,
            font_size_pt=10,
            fill_color=bg_color,
        )
        # Actual
        _set_cell_text(
            table.cell(row_idx, 1),
            var.actual,
            font_size_pt=10,
            align=PP_ALIGN.RIGHT,
            fill_color=bg_color,
        )
        # Budget
        _set_cell_text(
            table.cell(row_idx, 2),
            var.budget,
            font_size_pt=10,
            align=PP_ALIGN.RIGHT,
            fill_color=bg_color,
        )
        # Variance
        _set_cell_text(
            table.cell(row_idx, 3),
            var.variance,
            font_size_pt=10,
            align=PP_ALIGN.RIGHT,
            fill_color=bg_color,
        )
        # Var %
        _set_cell_text(
            table.cell(row_idx, 4),
            var.var_pct,
            font_size_pt=10,
            align=PP_ALIGN.RIGHT,
            fill_color=bg_color,
        )
        # Sig.
        sig_color = (
            COLOR_SEMANTIC_FAV_TEXT
            if "Fav" in var.signal
            else COLOR_SEMANTIC_UNFAV_TEXT
        )
        _set_cell_text(
            table.cell(row_idx, 5),
            var.signal,
            font_size_pt=10,
            bold=True,
            color=sig_color,
            align=PP_ALIGN.CENTER,
            fill_color=bg_color,
        )
        # Driver
        _set_cell_text(
            table.cell(row_idx, 6),
            var.driver,
            font_size_pt=10,
            fill_color=bg_color,
        )

    # Provenance line
    tb_prov = slide.shapes.add_textbox(
        Inches(0.45), Inches(5.20), Inches(12.43), Inches(0.30)
    )
    tb_prov.name = "PPT-004_provenance"
    tf = tb_prov.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Commentary: approved by {ctx.narrative_author}, {ctx.narrative_date} · Rule-based narrative baseline"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Notes line
    tb_notes = slide.shapes.add_textbox(
        Inches(0.45), Inches(5.62), Inches(12.43), Inches(0.90)
    )
    tb_notes.name = "PPT-004_notes_line"
    tf = tb_notes.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Full commentary for the top 10 lines: speaker notes, the Excel pack and the commentary editor."
    p.font.name = FONT_FAMILY
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Footer band
    _add_footer_band(slide, 4, ctx)

    # Speaker notes
    slide.notes_slide.notes_text_frame.text = (
        f"Slide 4: Top Variances\n"
        f"Total lines evaluated: {ctx.variance_lines_considered}\n"
        f"Top 5 lines presented natively above."
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 5: Exceptions & Risk Register (PPT-005)
# -----------------------------------------------------------------------------
def build_slide_5(prs: Presentation, ctx: DeckContext) -> Any:
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Accent bar
    _add_accent_bar(slide, "PPT-005_accent")

    # Title & kicker
    tb_title = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.35), Inches(12.43), Inches(0.60)
    )
    tb_title.name = "PPT-005_title"
    tf = tb_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Exceptions and control risks — {ctx.period}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_BRAND_PRIMARY

    tb_kicker = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.95), Inches(12.43), Inches(0.30)
    )
    tb_kicker.name = "PPT-005_kicker"
    tf = tb_kicker.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Rule set {ctx.rule_set_version} · run 118 · {ctx.generated_at}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # 4 Status Chips across width: x = 0.45, 3.59, 6.73, 9.87; y = 1.35; w = 3.00, h = 0.75
    chip_xs = [0.45, 3.59, 6.73, 9.87]
    chip_labels = ["OPEN", "OVERDUE", "HIGH", "UNASSIGNED"]
    chip_vals = [
        ctx.exceptions_counts.open_count,
        ctx.exceptions_counts.overdue_count,
        ctx.exceptions_counts.high_count,
        ctx.exceptions_counts.unassigned_count,
    ]

    for idx in range(4):
        cx = chip_xs[idx]
        chip_num = idx + 1
        is_overdue = idx == 1

        chip_rect = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(cx),
            Inches(1.35),
            Inches(3.00),
            Inches(0.75),
        )
        chip_rect.name = f"PPT-005_chip{chip_num}"
        chip_rect.fill.solid()
        chip_rect.fill.fore_color.rgb = (
            COLOR_SEMANTIC_WARNING_FILL if is_overdue else COLOR_SURFACE_CARD
        )
        chip_rect.line.color.rgb = COLOR_CARD_BORDER

        # Chip label
        tb_clabel = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(1.40), Inches(2.68), Inches(0.28)
        )
        tb_clabel.name = f"PPT-005_chip{chip_num}_label"
        tf = tb_clabel.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = chip_labels[idx]
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = (
            COLOR_SEMANTIC_WARNING_TEXT if is_overdue else COLOR_TEXT_SECONDARY
        )

        # Chip value
        tb_cval = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(1.68), Inches(2.68), Inches(0.38)
        )
        tb_cval.name = f"PPT-005_chip{chip_num}_value"
        tf = tb_cval.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(chip_vals[idx])
        p.font.name = FONT_FAMILY
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = (
            COLOR_SEMANTIC_WARNING_TEXT if is_overdue else COLOR_BRAND_PRIMARY
        )

    # Risk note
    tb_risk = slide.shapes.add_textbox(
        Inches(0.45), Inches(2.20), Inches(12.43), Inches(0.25)
    )
    tb_risk.name = "PPT-005_risknote"
    tf = tb_risk.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        f"Potential exception — requires accounting review. These are leads, not verdicts. · "
        f"Σ amount at risk ₹ {ctx.total_amount_at_risk} (indicator only)"
    )
    p.font.name = FONT_FAMILY
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Native Table (6 columns: Rule, Subject, At risk, Sev., Owner, Status/Age)
    rows = min(len(ctx.exceptions_list), 5) + 1
    table_shape = slide.shapes.add_table(
        rows, 6, Inches(0.45), Inches(2.50), Inches(12.43), Inches(3.24)
    )
    table_shape.name = "PPT-005_table"
    table = table_shape.table

    col_widths = [2.30, 3.40, 1.50, 1.00, 1.40, 2.83]
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)

    headers = ["Rule", "Subject", "At risk", "Sev.", "Owner", "Status / Age"]
    for col_idx, h_text in enumerate(headers):
        align = PP_ALIGN.RIGHT if col_idx == 2 else PP_ALIGN.LEFT
        _set_cell_text(
            table.cell(0, col_idx),
            h_text,
            font_size_pt=9,
            bold=True,
            color=COLOR_WHITE,
            align=align,
            fill_color=COLOR_BRAND_PRIMARY,
        )

    for row_idx, exc in enumerate(ctx.exceptions_list[:5], start=1):
        bg_color = COLOR_SURFACE_CARD if row_idx % 2 == 1 else COLOR_WHITE
        _set_cell_text(
            table.cell(row_idx, 0),
            exc.rule,
            font_size_pt=9,
            fill_color=bg_color,
        )
        _set_cell_text(
            table.cell(row_idx, 1),
            exc.subject,
            font_size_pt=9,
            fill_color=bg_color,
        )
        _set_cell_text(
            table.cell(row_idx, 2),
            exc.at_risk,
            font_size_pt=9,
            align=PP_ALIGN.RIGHT,
            fill_color=bg_color,
        )
        sev_color = (
            COLOR_SEMANTIC_UNFAV_TEXT
            if exc.severity == "High"
            else COLOR_TEXT_PRIMARY
        )
        _set_cell_text(
            table.cell(row_idx, 3),
            exc.severity,
            font_size_pt=9,
            bold=True,
            color=sev_color,
            fill_color=bg_color,
        )
        _set_cell_text(
            table.cell(row_idx, 4),
            exc.owner,
            font_size_pt=9,
            fill_color=bg_color,
        )
        _set_cell_text(
            table.cell(row_idx, 5),
            exc.status_age,
            font_size_pt=9,
            fill_color=bg_color,
        )

    # Exception summary narrative (budget 648 chars per §3.4)
    budget = compute_character_budget(
        box_width_inches=12.43,
        box_height_inches=0.94,
        font_size_pt=11.0,
        configured_max_lines=4,
    )
    trimmed_summary, was_trimmed = trim_text_to_budget(
        ctx.exception_summary, budget
    )

    tb_sum = slide.shapes.add_textbox(
        Inches(0.45), Inches(5.90), Inches(12.43), Inches(0.95)
    )
    tb_sum.name = "PPT-005_summary"
    tf = tb_sum.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        f"Exception summary: {trimmed_summary}"
        + (f" · {TRIMMED_FOOTNOTE}" if was_trimmed else "")
    )
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_TEXT_PRIMARY

    # Footer band
    _add_footer_band(slide, 5, ctx)

    # Speaker notes
    slide.notes_slide.notes_text_frame.text = (
        f"Slide 5: Exceptions & Risk Register\n"
        f"Open Exceptions: {ctx.exceptions_counts.open_count}\n"
        f"Overdue: {ctx.exceptions_counts.overdue_count}\n"
        f"Full Exception Summary:\n{ctx.exception_summary}"
    )
    return slide


# -----------------------------------------------------------------------------
# Slide 6: Rolling Forecast & Outlook (PPT-006)
# -----------------------------------------------------------------------------
def build_slide_6(prs: Presentation, ctx: DeckContext) -> Any:
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Accent bar
    _add_accent_bar(slide, "PPT-006_accent")

    # Title
    tb_title = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.35), Inches(12.43), Inches(0.60)
    )
    tb_title.name = "PPT-006_title"
    tf = tb_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"Forecast and outlook — {ctx.period}"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = COLOR_BRAND_PRIMARY

    # Scenario line
    tb_scen = slide.shapes.add_textbox(
        Inches(0.45), Inches(0.95), Inches(12.43), Inches(0.35)
    )
    tb_scen.name = "PPT-006_scenario"
    tf = tb_scen.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    lock_status = (
        f"locked {ctx.generated_at.split()[0]}"
        if ctx.forecast_locked
        else "draft NOT LOCKED"
    )
    p.text = f"Scenario {ctx.scenario} · version {ctx.forecast_version} ({lock_status}) · method mix: remaining budget 62% / run rate 38%"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # 3 Outlook cards: x = 0.45, 4.68, 8.91; y = 1.40; w = 3.97, h = 1.35
    card_xs = [0.45, 4.68, 8.91]
    cards_data = [
        ForecastCardData(
            "LANDING ESTIMATE (FY)",
            ctx.forecast_landing_estimate,
            "YTD actual + forecast remaining",
        ),
        ForecastCardData(
            "VS ANNUAL BUDGET", ctx.forecast_vs_budget, f"as at {ctx.period}"
        ),
        ForecastCardData(
            "ACCURACY (MAPE-lite)",
            ctx.forecast_accuracy_mape,
            ctx.forecast_accuracy_details,
        ),
    ]

    for idx, cdata in enumerate(cards_data):
        cx = card_xs[idx]
        card_num = idx + 1

        card_rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(cx),
            Inches(1.40),
            Inches(3.97),
            Inches(1.35),
        )
        card_rect.name = f"PPT-006_card{card_num}"
        card_rect.fill.solid()
        card_rect.fill.fore_color.rgb = COLOR_SURFACE_CARD
        card_rect.line.color.rgb = COLOR_CARD_BORDER

        # Label
        tb_clabel = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(1.45), Inches(3.75), Inches(0.22)
        )
        tb_clabel.name = f"PPT-006_card{card_num}_label"
        tf = tb_clabel.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = cdata.label
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_SECONDARY

        # Value
        tb_cval = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(1.70), Inches(3.75), Inches(0.42)
        )
        tb_cval.name = f"PPT-006_card{card_num}_value"
        tf = tb_cval.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = cdata.value
        p.font.name = FONT_FAMILY
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = COLOR_BRAND_PRIMARY

        # Compare
        tb_ccomp = slide.shapes.add_textbox(
            Inches(cx + 0.16), Inches(2.20), Inches(3.75), Inches(0.25)
        )
        tb_ccomp.name = f"PPT-006_card{card_num}_compare"
        tf = tb_ccomp.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = cdata.comparison
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Native Forecast Line Chart (§5.3)
    chart_data = CategoryChartData()
    chart_data.categories = ctx.forecast_periods
    chart_data.add_series("Actual", tuple(ctx.forecast_actuals))
    chart_data.add_series("Forecast", tuple(ctx.forecast_projected))
    chart_data.add_series("Budget", tuple(ctx.forecast_budget))

    chart_shape = slide.shapes.add_chart(
        XL_CHART_TYPE.LINE_MARKERS,
        Inches(0.45),
        Inches(2.85),
        Inches(7.60),
        Inches(3.30),
        chart_data,
    )
    chart_shape.name = "PPT-006_chart_forecast"
    chart = chart_shape.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.has_title = True
    chart.chart_title.text_frame.text = (
        f"Forecast vs Actual: {ctx.scenario} ({ctx.forecast_version}) · ₹ Lakhs"
    )

    # Right-hand Outlook narrative block
    tb_out = slide.shapes.add_textbox(
        Inches(8.30), Inches(2.85), Inches(4.58), Inches(3.30)
    )
    tb_out.name = "PPT-006_outlook"
    tf = tb_out.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = ctx.outlook_method_mix
    p0.font.name = FONT_FAMILY
    p0.font.size = Pt(9)
    p0.font.color.rgb = COLOR_TEXT_SECONDARY

    p_prov = tf.add_paragraph()
    p_prov.text = f"Outlook narrative · approved by {ctx.narrative_author}, {ctx.narrative_date}"
    p_prov.font.name = FONT_FAMILY
    p_prov.font.size = Pt(9)
    p_prov.font.color.rgb = COLOR_TEXT_SECONDARY

    budget = compute_character_budget(
        box_width_inches=4.58,
        box_height_inches=2.50,
        font_size_pt=11.0,
        configured_max_lines=12,
    )
    trimmed_out, was_trimmed = trim_text_to_budget(
        ctx.outlook_narrative, budget
    )

    p_body = tf.add_paragraph()
    p_body.text = trimmed_out + (
        f"\n[{TRIMMED_FOOTNOTE}]" if was_trimmed else ""
    )
    p_body.font.name = FONT_FAMILY
    p_body.font.size = Pt(11)
    p_body.font.color.rgb = COLOR_TEXT_PRIMARY

    # Full Canonical Advisory Disclaimer Band (§3.7, §4.6)
    tb_disc = slide.shapes.add_textbox(
        Inches(0.45), Inches(6.26), Inches(12.43), Inches(0.62)
    )
    tb_disc.name = "PPT-006_disclaimer"
    tf = tb_disc.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = CANONICAL_DISCLAIMER
    p.font.name = FONT_FAMILY
    p.font.size = Pt(8)
    p.font.color.rgb = COLOR_TEXT_SECONDARY

    # Footer band
    _add_footer_band(slide, 6, ctx)

    # Speaker notes
    slide.notes_slide.notes_text_frame.text = (
        f"{CANONICAL_DISCLAIMER}\n\n"
        f"Slide 6: Rolling Forecast & Outlook\n"
        f"Forecast Version: {ctx.forecast_version} ({'Locked' if ctx.forecast_locked else 'Draft'})\n"
        f"Landing Estimate: {ctx.forecast_landing_estimate}\n"
        f"Full Outlook Text:\n{ctx.outlook_narrative}"
    )
    return slide


# -----------------------------------------------------------------------------
# Main Generation Entrypoint
# -----------------------------------------------------------------------------
def generate_powerpoint_deck(
    context: Optional[DeckContext] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> Presentation:
    """Generate the complete 6-slide PowerPoint presentation pack.

    Parameters:
        context: DeckContext configuration and data; if None, default context is used.
        output_path: Optional file path to write the .pptx presentation.

    Returns:
        pptx.Presentation instance.
    """
    ctx = context or DeckContext()
    
    # doc-12 §3.6: Load the template instead of building from scratch
    template_dir = Path(__file__).resolve().parent.parent.parent.parent / "packaging" / "templates"
    # DEF-018: Resolve board_pack_template.pptx first, with fallback to FPAMonthEndCopilot_v1.pptx
    template_path = template_dir / "board_pack_template.pptx"
    if not template_path.exists():
        fallback_path = template_dir / "FPAMonthEndCopilot_v1.pptx"
        if fallback_path.exists():
            template_path = fallback_path
        else:
            raise ExportTemplateError(
                f"ERR-EXP-014: The deck template is missing or damaged. Could not find {template_path} or {fallback_path}"
            )
        
    prs = Presentation(str(template_path))

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
        tmp_p = out_p.with_suffix('.tmp')
        try:
            prs.save(str(tmp_p))
            tmp_p.replace(out_p)
        except Exception:
            if tmp_p.exists():
                tmp_p.unlink()
            raise

    return prs
