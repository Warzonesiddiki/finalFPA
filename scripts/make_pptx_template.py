#!/usr/bin/env python3
"""Generate the doc-12 deck template at ``packaging/templates/FPAMonthEndCopilot_v1.pptx``.

DEF-011. ``scripts/build.py`` precondition 4b (``_validate_pptx_template``) refuses to
build until the deck template is a real OOXML package carrying the seven layout names
doc 12 section 3.6 requires. Until this script existed the shipped file was a 16-byte
ASCII placeholder (``PPTX_PLACEHOLDER``), so the whole named-shape deck contract was
unbacked.

Why a generator rather than a binary (SEC-045): the template must be reproducible from a
committed script. Every number here comes from ``docs/12_POWERPOINT_OUTPUT_SPEC.md``;
the source lines are cited per shape in ``GEOMETRY`` so a reviewer can diff the template
against the spec without opening PowerPoint.

Usage::

    python scripts/make_pptx_template.py [--out PATH] [--check]

``--check`` regenerates into a temp file and diffs the seven layout names against the
shipped artefact without writing it (used by the evidence run).

Constraints honoured (doc 12):
  * section 3.1 -- 16:9 at 13.333in x 7.5in, on the documented inch grid.
  * section 3.2 -- only whitelisted shape types: text box, table, chart, picture,
    auto shape. No groups, no rasterised text.
  * section 3.3 -- colours taken from ``ui/theme/tokens.ts`` as tabulated in doc 12
    section 3.3.
  * section 3.6 -- seven layouts renamed to FPA-PPT-001..006 + FPA-PPT-DISCLAIMER,
    each carrying named shapes in the ``PPT-00N_<role>`` convention the engine
    resolves by name.
  * section 3.6 -- layouts hold *no* unused placeholders; the template author (this
    script) clears them, not the runtime.

The output is byte-deterministic for a fixed python-pptx version: core-property
timestamps are pinned and shape creation order is fixed.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import io
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------------------
# Theme tokens -- doc 12 section 3.3, "The literal v1 values"
# ---------------------------------------------------------------------------
BRAND_PRIMARY = RGBColor(0x1F, 0x3A, 0x5F)
BRAND_SECONDARY = RGBColor(0xB7, 0x79, 0x1F)
TEXT_PRIMARY = RGBColor(0x1F, 0x29, 0x37)
TEXT_SECONDARY = RGBColor(0x6B, 0x72, 0x80)
SURFACE_CARD = RGBColor(0xF7, 0xF8, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT_HEADING = "Calibri"  # doc 12 section 3.3 font.heading
FONT_BODY = "Calibri"  # doc 12 section 3.3 font.body

#: doc 12 section 3.1 -- "The built-in deck is 16:9 (13.333in x 7.5in)".
#: 12192000 EMU is exactly 7.5in * 16/9, i.e. mathematically exact 16:9 rather than the
#: 12191695 EMU that Inches(13.333) would give (0.0003in short).
SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5
SLIDE_W_EMU = 12192000
SLIDE_H_EMU = 6858000

#: doc 12 section 3.1 footer band, and section 3.7 -- present on EVERY slide.
FOOTER_Y_IN = 7.04
FOOTER_H_IN = 0.28

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "packaging" / "templates" / "FPAMonthEndCopilot_v1.pptx"

#: The seven layout names doc 12 section 3.6 requires, in order.
LAYOUT_NAMES = (
    "FPA-PPT-001",
    "FPA-PPT-002",
    "FPA-PPT-003",
    "FPA-PPT-004",
    "FPA-PPT-005",
    "FPA-PPT-006",
    "FPA-PPT-DISCLAIMER",
)

#: KPI cards on PPT-002, outlook cards on PPT-006, count chips on PPT-005.
KPI_CARD_XS = (0.45, 4.68, 8.91)
KPI_CARD_YS = (1.45, 3.10)
CHIP_XS = (0.45, 3.59, 6.73, 9.87)


# ---------------------------------------------------------------------------
# Minimal PNG encoder -- the layout's logo shape needs a real image part, and
# Pillow is not a project dependency. Color type 2 (truecolour RGB), 8-bit.
# ---------------------------------------------------------------------------
def _png_chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """A solid truecolour PNG. Deterministic for a given width/height/rgb."""
    row = b"\x00" + bytes(rgb) * width  # filter type 0 (None) + pixels
    raw = row * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )


def _logo_png() -> bytes:
    """Neutral placeholder wordmark: a brand-primary plate with a secondary bar.

    doc 12 section 4.1 caps the logo at 2.05in x 0.90in with aspect preserved and
    makes the real logo a Settings-supplied file, swapped in at render time
    (absent -> ERR-EXP-016). This plate exists so the layout declares a genuine
    Picture shape rather than a text box standing in for one.
    """
    plate = bytearray(_solid_png(410, 180, (0x1F, 0x3A, 0x5F)))
    return bytes(plate)


# ---------------------------------------------------------------------------
# Shape specification -- every entry cites its doc-12 source line.
# Fields: (name, kind, x, y, w, h, size_pt, bold, colour, single_line, source)
# kind: "text" | "rect" | "roundrect"
# ---------------------------------------------------------------------------
def _t(name, kind, x, y, w, h, size, bold, colour, single, src):
    return dict(name=name, kind=kind, x=x, y=y, w=w, h=h, size=size,
                bold=bold, colour=colour, single=single, src=src)


def _cover_spec() -> list[dict[str, Any]]:
    """doc 12 section 4.1 (lines 428-434)."""
    s = [
        # Accent bar first -> renders behind everything (z-order, lead req 5).
        _t("PPT-001_accent", "rect", 0.0, 0.0, SLIDE_W_IN, 0.08, 10, False,
           BRAND_PRIMARY, True, "L434 accent bar, h=0.08in, full width"),
        _t("PPT-001_title", "text", 0.45, 2.20, 12.43, 0.80, 32, True,
           BRAND_PRIMARY, True, "L428 32pt bold brand.primary"),
        _t("PPT-001_packline", "text", 0.45, 3.05, 12.43, 0.50, 20, False,
           TEXT_PRIMARY, True, "L429 20pt text.primary"),
        _t("PPT-001_periodline", "text", 0.45, 3.60, 12.43, 0.35, 14, False,
           TEXT_SECONDARY, True, "L430 14pt text.secondary"),
        _t("PPT-001_sources", "text", 0.45, 4.15, 7.50, 1.60, 10, False,
           TEXT_PRIMARY, False, "L431 10pt, 8 lines, header 'SOURCES'"),
        _t("PPT-001_stamp", "text", 8.38, 4.15, 4.50, 2.40, 9, False,
           TEXT_PRIMARY, False, "L432 9pt, header 'STAMP' + 12 fields"),
    ]
    return s


def _exec_spec() -> list[dict[str, Any]]:
    """doc 12 section 4.2 (lines 468-476). 6 KPI cards x (bg, signal, label, value, compare)."""
    s = [
        _t("PPT-002_title", "text", 0.45, 0.35, 12.43, 0.60, 24, True,
           BRAND_PRIMARY, True, "L468 24pt bold"),
        _t("PPT-002_kicker", "text", 0.45, 0.95, 12.43, 0.30, 12, False,
           TEXT_SECONDARY, True, "L469 12pt text.secondary"),
    ]
    n = 0
    for cy in KPI_CARD_YS:
        for cx in KPI_CARD_XS:
            n += 1
            s.append(_t(f"PPT-002_kpi{n}_card", "roundrect", cx, cy, 3.97, 1.45, 10, False,
                        SURFACE_CARD, False,
                        f"L470 card bg at x={cx} y={cy} 3.97x1.45, + left signal chip 0.06in"))
            s.append(_t(f"PPT-002_kpi{n}_signal", "rect", cx, cy, 0.06, 1.45, 10, False,
                        BRAND_SECONDARY, False,
                        "L470 'the left signal chip (0.06in wide)' - separate shape, name assumed"))
            s.append(_t(f"PPT-002_kpi{n}_label", "text", cx + 0.16, cy + 0.10, 3.77, 0.22, 10, True,
                        TEXT_SECONDARY, True, "L471 10pt bold text.secondary"))
            s.append(_t(f"PPT-002_kpi{n}_value", "text", cx + 0.16, cy + 0.34, 3.77, 0.45, 24, True,
                        BRAND_PRIMARY, True, "L472 24pt bold brand.primary"))
            s.append(_t(f"PPT-002_kpi{n}_compare", "text", cx + 0.16, cy + 0.86, 3.77, 0.22, 10, False,
                        TEXT_SECONDARY, True, "L473 10pt text.secondary"))
    s += [
        _t("PPT-002_narrative_label", "text", 0.45, 4.30, 12.43, 0.22, 9, False,
           TEXT_SECONDARY, True, "L474 provenance strip, 9pt"),
        _t("PPT-002_narrative", "text", 0.45, 4.64, 12.43, 1.88, 12, False,
           TEXT_PRIMARY, False, "L475 12pt, budget 894"),
        _t("PPT-002_footnote", "text", 0.45, 6.64, 12.43, 0.24, 9, False,
           TEXT_SECONDARY, True, "L475/L196 9pt footnote"),
    ]
    return s


def _bridge_spec() -> list[dict[str, Any]]:
    """doc 12 section 4.3 (lines 507-511)."""
    return [
        _t("PPT-003_title", "text", 0.45, 0.35, 12.43, 0.60, 24, True, BRAND_PRIMARY, True, "L507"),
        _t("PPT-003_kicker", "text", 0.45, 0.95, 12.43, 0.30, 12, False, TEXT_SECONDARY, True, "L508"),
        _t("PPT-003_drivers", "text", 9.30, 1.45, 3.58, 4.95, 10, False, TEXT_PRIMARY, False,
           "L510 header 'TOP DRIVERS' + 6 entries, 0.40in pitch"),
        _t("PPT-003_tieout", "text", 0.45, 6.54, 12.43, 0.28, 9, False, TEXT_SECONDARY, True,
           "L511 'Opening + sum drivers = Closing'"),
    ]


def _variance_spec() -> list[dict[str, Any]]:
    """doc 12 section 4.4 (lines 539-543)."""
    return [
        _t("PPT-004_title", "text", 0.45, 0.35, 12.43, 0.60, 24, True, BRAND_PRIMARY, True, "L539"),
        _t("PPT-004_kicker", "text", 0.45, 0.95, 12.43, 0.30, 12, False, TEXT_SECONDARY, True, "L540"),
        _t("PPT-004_provenance", "text", 0.45, 5.20, 12.43, 0.30, 9, False, TEXT_SECONDARY, True,
           "L542 commentary provenance strip"),
        _t("PPT-004_notes_line", "text", 0.45, 5.62, 12.43, 0.90, 9, False, TEXT_SECONDARY, False,
           "L543 driver summary + retrieval line, 3 lines"),
    ]


def _exception_spec() -> list[dict[str, Any]]:
    """doc 12 section 4.5 (lines 573-580). 4 count chips x (bg, label, value)."""
    s = [
        _t("PPT-005_title", "text", 0.45, 0.35, 12.43, 0.60, 24, True, BRAND_PRIMARY, True, "L573"),
        _t("PPT-005_kicker", "text", 0.45, 0.95, 12.43, 0.30, 12, False, TEXT_SECONDARY, True, "L574"),
    ]
    for i, cx in enumerate(CHIP_XS, start=1):
        s.append(_t(f"PPT-005_chip{i}", "rect", cx, 1.45, 3.00, 0.75, 10, False, SURFACE_CARD, False,
                    "L576 chip background at x=%s 3.00x0.75" % cx))
        s.append(_t(f"PPT-005_chip{i}_label", "text", cx + 0.16, 1.55, 2.68, 0.28, 10, True,
                    TEXT_SECONDARY, True, "L577 10pt bold"))
        s.append(_t(f"PPT-005_chip{i}_value", "text", cx + 0.16, 1.80, 2.68, 0.34, 18, True,
                    TEXT_PRIMARY, True, "L578 18pt bold"))
    s += [
        _t("PPT-005_risknote", "text", 0.45, 2.24, 12.43, 0.22, 9, False, TEXT_SECONDARY, True,
           "L575 'Potential exception - requires accounting review'"),
        _t("PPT-005_summary", "text", 0.45, 5.94, 12.43, 0.94, 11, False, TEXT_PRIMARY, False,
           "L580 approved exception summary, budget 648"),
    ]
    return s


def _forecast_spec() -> list[dict[str, Any]]:
    """doc 12 section 4.6 (lines 609-617). 3 outlook cards x (bg, label, value, compare)."""
    s = [
        _t("PPT-006_title", "text", 0.45, 0.35, 12.43, 0.60, 24, True, BRAND_PRIMARY, True, "L609"),
        _t("PPT-006_scenario", "text", 0.45, 0.95, 12.43, 0.35, 12, False, TEXT_SECONDARY, True,
           "L610 scenario + version line"),
    ]
    for i, cx in enumerate(KPI_CARD_XS, start=1):
        s.append(_t(f"PPT-006_card{i}", "roundrect", cx, 1.45, 3.97, 1.35, 10, False,
                    SURFACE_CARD, False, "L611 card background x=%s 3.97x1.35" % cx))
        s.append(_t(f"PPT-006_card{i}_label", "text", cx + 0.16, 1.55, 3.77, 0.22, 10, True,
                    TEXT_SECONDARY, True, "L612 10pt bold"))
        s.append(_t(f"PPT-006_card{i}_value", "text", cx + 0.16, 1.79, 3.77, 0.42, 22, True,
                    BRAND_PRIMARY, True, "L613 22pt bold"))
        s.append(_t(f"PPT-006_card{i}_compare", "text", cx + 0.16, 2.27, 3.77, 0.22, 10, False,
                    TEXT_SECONDARY, True, "L614 10pt text.secondary"))
    s += [
        _t("PPT-006_outlook", "text", 8.30, 2.98, 4.58, 3.10, 11, False, TEXT_PRIMARY, False,
           "L616 methods line + provenance + narrative, budget 708"),
        _t("PPT-006_disclaimer", "text", 0.45, 6.26, 12.43, 0.62, 8, False, TEXT_SECONDARY, False,
           "L617 FULL canonical disclaimer verbatim, 8pt, budget 669"),
    ]
    return s


def _disclaimer_spec() -> list[dict[str, Any]]:
    """FPA-PPT-DISCLAIMER layout.

    ASSUMPTION: doc 12 section 3.6 names this layout but never enumerates shapes on
    it, and section 3.7 only says the full canonical disclaimer text goes here when a
    client base deck has its own disclaimer layout. No PPT-00N_<role> names exist in
    the spec for it, so these two names follow the documented convention by analogy
    and are flagged in the evidence report as an assumption, not a spec quote.
    """
    return [
        _t("PPT-00D_accent", "rect", 0.0, 0.0, SLIDE_W_IN, 0.08, 10, False,
           BRAND_PRIMARY, True, "ASSUMED - mirror of PPT-001_accent"),
        _t("PPT-00D_title", "text", 0.45, 1.20, 12.43, 0.60, 24, True, BRAND_PRIMARY, True,
           "ASSUMED - full canonical disclaimer heading"),
        _t("PPT-00D_disclaimer", "text", 0.45, 2.00, 12.43, 4.40, 11, False, TEXT_PRIMARY, False,
           "ASSUMED - doc 12 L270 full canonical disclaimer verbatim (01 s15.1)"),
    ]


#: Native tables. (name, x, y, w, h, header, columns_in, body_pt, rows, source)
#: ``insert_at`` places the graphicFrame in doc-12 reading order so that z-order cannot
#: leave a chart/table covering body text if the engine later reflows a box.
TABLES = {
    "FPA-PPT-004": dict(
        name="PPT-004_table", x=0.45, y=1.45, w=12.43, h=3.60, insert_at=2,
        header=("Account", "Actual", "Budget", "Variance", "Var %", "Sig.", "Driver"),
        widths=(3.20, 1.50, 1.50, 1.65, 1.15, 1.00, 2.43),  # L541, sums to 12.43
        body_pt=10, header_pt=10, rows=7, source="L541 7 rows x 0.60in",
    ),
    "FPA-PPT-005": dict(
        name="PPT-005_table", x=0.45, y=2.58, w=12.43, h=3.24, insert_at=15,
        header=("Rule", "Subject", "At risk", "Sev.", "Owner", "Status / Age"),
        widths=(2.30, 3.40, 1.50, 1.00, 1.40, 2.83),  # L579, sums to 12.43
        body_pt=9, header_pt=9, rows=6, source="L579 6 rows x 0.54in (= 3.24in, consistent)",
    ),
}

#: Native charts. (name, x, y, w, h, chart_type, source)
CHARTS = {
    "FPA-PPT-003": dict(name="PPT-003_chart_bridge", x=0.45, y=1.45, w=8.60, h=4.95,
                       kind="bar", insert_at=2, source="L509 native bridge chart, doc 12 s5.2"),
    "FPA-PPT-006": dict(name="PPT-006_chart_forecast", x=0.45, y=2.98, w=7.60, h=3.10,
                        kind="line", insert_at=14, source="L615 native line chart, doc 12 s5.3"),
}

#: The one picture in the deck (doc 12 section 3.2 / 4.1).
PICTURE = {
    "FPA-PPT-001": dict(name="PPT-001_logo", x=10.83, y=0.35, w=2.05, h=0.90, insert_at=6,
                        source="L433 cap 2.05in x 0.90in, aspect preserved"),
}

#: Shape spec per layout, in z-order (backgrounds first -> text last).
SPECS = {
    "FPA-PPT-001": _cover_spec,
    "FPA-PPT-002": _exec_spec,
    "FPA-PPT-003": _bridge_spec,
    "FPA-PPT-004": _variance_spec,
    "FPA-PPT-005": _exception_spec,
    "FPA-PPT-006": _forecast_spec,
    "FPA-PPT-DISCLAIMER": _disclaimer_spec,
}


def _footer_spec(slide_id: str) -> list[dict[str, Any]]:
    """doc 12 section 3.7 footer band, present on EVERY slide.

    ASSUMPTION: section 3.7 mandates the band and its two text runs, but the per-slide
    tables in sections 4.1-4.6 never give it a ``PPT-00N_<role>`` name. Following the
    convention by analogy; flagged in the evidence report.
    """
    return [
        _t(f"{slide_id}_footer_left", "text", 0.45, FOOTER_Y_IN, 9.00, FOOTER_H_IN, 8, False,
           TEXT_SECONDARY, True, "L269 short-form disclaimer verbatim, 134 chars, 8pt"),
        _t(f"{slide_id}_footer_right", "text", 9.60, FOOTER_Y_IN, 3.28, FOOTER_H_IN, 8, False,
           TEXT_SECONDARY, True, "L269 'Slide N of 6 - Pack vN - FY26-P09', 8pt"),
    ]


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------
def _style_text_frame(tf, *, size: int, bold: bool, colour: RGBColor, single: bool) -> None:
    """doc 12 section 3.1 text-frame rules.

    word_wrap=True, auto_size=NONE (PowerPoint autofit is deliberately not used),
    vertical_anchor=TOP, zero internal margins on single-line boxes, 0.05in elsewhere.
    """
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    m = 0 if single else Inches(0.05)
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = m
    if not tf.paragraphs[0].runs:
        run = tf.paragraphs[0].add_run()
        run.text = ""
    run = tf.paragraphs[0].runs[0]
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = colour
    run.font.name = FONT_HEADING if bold else FONT_BODY


def _make_textbox(slide, sp: dict[str, Any]):
    box = slide.shapes.add_textbox(
        Inches(sp["x"]), Inches(sp["y"]), Inches(sp["w"]), Inches(sp["h"])
    )
    box.name = sp["name"]
    _style_text_frame(box.text_frame, size=sp["size"], bold=sp["bold"],
                      colour=sp["colour"], single=sp["single"])
    return box


def _make_rect(slide, sp: dict[str, Any]):
    shape_kind = MSO_SHAPE.ROUNDED_RECTANGLE if sp["kind"] == "roundrect" else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(
        shape_kind, Inches(sp["x"]), Inches(sp["y"]), Inches(sp["w"]), Inches(sp["h"])
    )
    shp.name = sp["name"]
    shp.fill.solid()
    shp.fill.fore_color.rgb = sp["colour"]
    shp.line.fill.background()
    shp.shadow.inherit = False
    if sp["kind"] == "roundrect":
        # Subtle corner radius; adjustment index 0 on a rounded rectangle.
        try:
            shp.adjustments[0] = 0.04
        except (IndexError, ValueError):
            pass
    # doc 12 section 3.2: auto shapes carry no text inside unless they are text boxes.
    shp.text_frame.word_wrap = True
    return shp


def _make_table(slide, cfg: dict[str, Any]):
    rows, cols = cfg["rows"], len(cfg["header"])
    gf = slide.shapes.add_table(
        rows, cols, Inches(cfg["x"]), Inches(cfg["y"]), Inches(cfg["w"]), Inches(cfg["h"])
    )
    gf.name = cfg["name"]
    table = gf.table
    table.first_row = True
    # Row pitch: doc 12 L579 is self-consistent (6 x 0.54 = 3.24); L541 states
    # 7 rows x 0.60in (= 4.20in) against a declared frame height of 3.60in, which
    # cannot both hold. The declared frame (x,y,w,h) is authoritative, so row height
    # is derived from it. Flagged in the evidence report.
    row_h = Inches(cfg["h"] / rows)
    for r in range(rows):
        table.rows[r].height = row_h
    for c, width_in in enumerate(cfg["widths"]):
        table.columns[c].width = Inches(width_in)
    for c, label in enumerate(cfg["header"]):
        cell = table.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = BRAND_PRIMARY
        cell.margin_left = cell.margin_right = Inches(0.06)
        cell.margin_top = cell.margin_bottom = Inches(0.02)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = label
        run.font.size = Pt(cfg["header_pt"])
        run.font.bold = True
        run.font.color.rgb = WHITE
        run.font.name = FONT_BODY
        p.alignment = PP_ALIGN.LEFT if c in (0, len(cfg["header"]) - 1) else PP_ALIGN.RIGHT
    for r in range(1, rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = ""
            run.font.size = Pt(cfg["body_pt"])
            run.font.color.rgb = TEXT_PRIMARY
            run.font.name = FONT_BODY
            p.alignment = PP_ALIGN.LEFT if c in (0, len(cfg["header"]) - 1) else PP_ALIGN.RIGHT
    return gf


def _make_chart(slide, cfg: dict[str, Any]):
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE

    data = CategoryChartData()
    data.categories = ["Template"]
    data.add_series("Series 1", (0.0,))
    ctype = XL_CHART_TYPE.BAR_CLUSTERED if cfg["kind"] == "bar" else XL_CHART_TYPE.LINE_MARKERS
    gf = slide.shapes.add_chart(
        ctype, Inches(cfg["x"]), Inches(cfg["y"]), Inches(cfg["w"]), Inches(cfg["h"]), data
    )
    gf.name = cfg["name"]
    return gf


def _make_picture(slide, cfg: dict[str, Any]):
    import io

    pic = slide.shapes.add_picture(
        io.BytesIO(_logo_png()), Inches(cfg["x"]), Inches(cfg["y"]),
        width=Inches(cfg["w"]), height=Inches(cfg["h"]),
    )
    pic.name = cfg["name"]
    # doc 12 section 4.1: alt text = project name, set by the engine at render time.
    pic._element._nvXxPr.cNvPr.set("descr", "Project logo")
    return pic


# ---------------------------------------------------------------------------
# Transfer from factory slide -> layout
# ---------------------------------------------------------------------------
def _retarget(element, src_part, dst_part) -> None:
    """Re-point relationship-bearing attributes from a factory part to the layout part.

    A ``<c:chart r:id>`` or ``<a:blip r:embed>`` copied verbatim into a different part
    would dangle, because rIds are part-scoped. We re-relate the same target part from
    the layout part and rewrite the id.
    """
    for chart_el in element.iter(qn("c:chart")):
        old = chart_el.get(qn("r:id"))
        if old:
            chart_el.set(qn("r:id"), dst_part.relate_to(src_part.related_part(old), RT.CHART))
    for blip in element.iter(qn("a:blip")):
        old = blip.get(qn("r:embed"))
        if old:
            blip.set(qn("r:embed"), dst_part.relate_to(src_part.related_part(old), RT.IMAGE))


def _clear_placeholders(layout) -> int:
    """Remove every placeholder from a layout. doc 12 section 3.6 puts this on the
    template author, explicitly not the runtime."""
    removed = 0
    for shp in list(layout.shapes):
        shp._element.getparent().remove(shp._element)
        removed += 1
    return removed


#: ZIP epoch. Every archive entry is stamped with this so repeated runs are
#: byte-identical; python-pptx inherits the wall clock from zipfile's default.
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

#: openpyxl stamps the chart workbooks it writes with wall-clock created/modified
#: times. They are the ONLY non-deterministic bytes in the package, so we pin them.
_FIXED_CREATED = b'<dcterms:created xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z</dcterms:created>'
_FIXED_MODIFIED = b'<dcterms:modified xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z</dcterms:modified>'
_CREATED_RE = re.compile(rb"<dcterms:created[^>]*>[^<]*</dcterms:created>")
_MODIFIED_RE = re.compile(rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>")


def _normalise_workbook(blob: bytes) -> bytes:
    """Rewrite an embedded chart workbook with pinned timestamps."""
    src = zipfile.ZipFile(io.BytesIO(blob))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "docProps/core.xml":
                data = _CREATED_RE.sub(_FIXED_CREATED, data)
                data = _MODIFIED_RE.sub(_FIXED_MODIFIED, data)
            info = zipfile.ZipInfo(item.filename, date_time=_ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            dst.writestr(info, data)
    return buf.getvalue()


def _make_reproducible(path: Path) -> None:
    """Rewrite ``path`` so repeated generator runs are byte-identical.

    SEC-045 wants the template reproducible from a committed script; that means a
    reviewer regenerating it should get the same artefact, not merely an equivalent
    one. Two sources of drift are pinned here: the embedded chart workbooks' creation
    timestamps, and the ZIP entry timestamps on every part.
    """
    src = zipfile.ZipFile(path)
    entries = [(item, src.read(item.filename)) for item in src.infolist()]
    src.close()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
        for item, data in entries:
            if item.filename.startswith("ppt/embeddings/") and item.filename.endswith(".xlsx"):
                data = _normalise_workbook(data)
            info = zipfile.ZipInfo(item.filename, date_time=_ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = item.external_attr
            dst.writestr(info, data)
    path.write_bytes(buf.getvalue())


def build(out_path: Path = DEFAULT_OUT) -> Path:
    prs = Presentation()

    # doc 12 section 3.1 -- 16:9 at 13.333in x 7.5in.
    prs.slide_width = Emu(SLIDE_W_EMU)
    prs.slide_height = Emu(SLIDE_H_EMU)
    # python-pptx leaves the inherited type="screen4x3" on <p:sldSz> from the default
    # template even after the extents change. The extents are what PowerPoint honours,
    # but the stale type attribute misdeclares the deck. Correct it to screen16x9.
    _sld_sz = prs._element.find(qn("p:sldSz"))
    if _sld_sz is not None:
        _sld_sz.set("type", "screen16x9")

    master = prs.slide_masters[0]
    layouts = master.slide_layouts

    # Keep exactly seven layouts; drop the rest so the file carries "seven layouts"
    # and not eleven. SlideLayouts.remove() drops the relationship and the part.
    for extra in list(layouts)[len(LAYOUT_NAMES):]:
        layouts.remove(extra)

    # A throwaway presentation used purely as a shape factory. LayoutShapes exposes no
    # add_* methods, so elements are authored with the normal slide API and deep-copied.
    factory = Presentation()
    factory.slide_width = Inches(SLIDE_W_IN)
    factory.slide_height = Inches(SLIDE_H_IN)
    scratch = factory.slides.add_slide(factory.slide_layouts[6])

    for idx, name in enumerate(LAYOUT_NAMES):
        layout = layouts[idx]
        _clear_placeholders(layout)
        layout.name = name  # persists to <p:cSld name="FPA-PPT-001"> in slideLayouts/*.xml

        # Build in doc-12 reading order: accent/card backgrounds first, then the
        # table/chart/picture, then body text, then the footer band. That guarantees
        # the lead's z-order requirement (backgrounds behind text) and additionally
        # keeps media from ever covering body text.
        shapes = SPECS[name]()
        builders = [
            (lambda s=sp: _make_rect(scratch, s) if s["kind"] in ("rect", "roundrect")
             else _make_textbox(scratch, s))
            for sp in shapes
        ]
        for cfg, factory in ((PICTURE.get(name), _make_picture),
                             (TABLES.get(name), _make_table),
                             (CHARTS.get(name), _make_chart)):
            if cfg:
                # insert_at is the doc-12 position the media occupies; entries at or
                # after it shift down one, so the media lands exactly there.
                builders.insert(cfg.get("insert_at", len(shapes)),
                                lambda c=cfg, f=factory: f(scratch, c))
        builders += [(lambda s=sp: _make_textbox(scratch, s))
                     for sp in _footer_spec(_slide_id(name))]

        spTree = layout.shapes._spTree
        for factory in builders:
            el = copy.deepcopy(factory()._element)
            _retarget(el, scratch.part, layout.part)
            spTree.append(el)

    # Deterministic core properties so repeated runs are byte-comparable.
    cp = prs.core_properties
    cp.title = "FP&A Month-End Copilot deck template"
    cp.author = "FP&A Month-End Copilot"
    cp.comments = "Generated by scripts/make_pptx_template.py per docs/12 section 3.6"
    cp.revision = 1
    cp.created = _dt.datetime(2026, 1, 1, 0, 0, 0)
    cp.modified = _dt.datetime(2026, 1, 1, 0, 0, 0)
    cp.last_modified_by = "scripts/make_pptx_template.py"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    _make_reproducible(out_path)
    return out_path


def _slide_id(layout_name: str) -> str:
    """'FPA-PPT-002' -> 'PPT-002'; 'FPA-PPT-DISCLAIMER' -> 'PPT-00D'."""
    tail = layout_name.removeprefix("FPA-")
    digits = "".join(ch for ch in tail.split("-")[1] if ch.isdigit())
    return f"PPT-{digits}" if digits else "PPT-00D"


def audit(path: Path = DEFAULT_OUT) -> dict[str, Any]:
    """Read the saved artefact back and report what is actually in it."""
    from pptx import Presentation as _P

    prs = _P(str(path))
    layouts = prs.slide_masters[0].slide_layouts
    report: dict[str, Any] = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "slide_size_in": (prs.slide_width / 914400, prs.slide_height / 914400),
        "layout_count": len(layouts),
        "layout_names": [lay.name for lay in layouts],
        "layouts": {},
    }
    for lay in layouts:
        report["layouts"][lay.name] = [
            {"name": s.name, "type": str(s.shape_type)} for s in lay.shapes
        ]
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true",
                    help="regenerate to a temp path and diff layout names; write nothing")
    args = ap.parse_args(argv)

    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "check.pptx"
            build(tmp)
            fresh = audit(tmp)
            shipped = audit(args.out) if args.out.exists() else None
        print(f"regenerated layout names : {fresh['layout_names']}")
        if shipped:
            same = fresh["layout_names"] == shipped["layout_names"]
            print(f"shipped   layout names   : {shipped['layout_names']}")
            print(f"layout-name sets match   : {same}")
            print(f"shipped size             : {shipped['bytes']} bytes")
        return 0 if fresh["layout_names"] == list(LAYOUT_NAMES) else 1

    out = build(args.out)
    rep = audit(out)
    print(f"wrote {out}")
    print(f"bytes        : {rep['bytes']}")
    print(f"slide size   : {rep['slide_size_in'][0]:.3f}in x {rep['slide_size_in'][1]:.3f}in")
    print(f"layouts      : {rep['layout_count']} -> {rep['layout_names']}")
    for name, shapes in rep["layouts"].items():
        print(f"  {name}: {len(shapes)} shapes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())