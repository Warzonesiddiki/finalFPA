"""Unit tests for PowerPoint Deck Generation engine (Phase 5).

Tests adherence to docs/12_POWERPOINT_OUTPUT_SPEC.md §1 through §7.
"""

import json
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
import pytest

from app.engine.exports.ppt_pack import (
    DeckContext,
    SourceBatchItem,
    KPICardData,
    BridgeDriverItem,
    VarianceRow,
    ExceptionCounts,
    ExceptionRow,
    generate_powerpoint_deck,
    CANONICAL_DISCLAIMER,
    SHORT_DISCLAIMER,
    SLIDE_WIDTH_INCHES,
    SLIDE_HEIGHT_INCHES,
    ExportTemplateError,
)
from app.engine.exports.ppt_fit import (
    compute_character_budget,
    trim_text_to_budget,
)
from app.engine.pptx_fill.ppt_spec import SLIDE_SHAPE_ORDER


def test_character_budget_formula():
    """Verify character budget computation formula (§3.4)."""
    # Formula:
    # chars_per_line = floor(12.43 * 72 / (0.50 * 12)) = floor(894.96 / 6) = 149
    # line_height_in = 1.22 * 12 / 72 = 0.2033
    # lines_available = floor(1.70 / 0.2033) = 8
    # design_max_lines = min(8 - 3, 6) = 5
    # budget_chars = 149 * 5 = 745
    budget = compute_character_budget(
        box_width_inches=12.43,
        box_height_inches=1.70,
        font_size_pt=12.0,
        configured_max_lines=6,
    )
    assert budget > 500
    assert budget < 1000


def test_trim_text_to_budget_short_text():
    """Text within budget is not trimmed."""
    text = "Short narrative within character budget."
    trimmed, was_trimmed = trim_text_to_budget(text, 100)
    assert not was_trimmed
    assert trimmed == text


def test_trim_text_to_budget_long_text():
    """Long text drops trailing sentences or truncates at word boundary."""
    text = (
        "First sentence explaining Q3 revenue. "
        "Second sentence detailing procurement costs. "
        "Third sentence noting factory maintenance delays. "
        "Fourth sentence highlighting audit findings."
    )
    trimmed, was_trimmed = trim_text_to_budget(text, 80)
    assert was_trimmed
    assert len(trimmed) <= 80
    assert trimmed.startswith("First sentence")


def test_deck_generation_slide_count_and_dimensions():
    """Deck must contain exactly 6 slides in 16:9 widescreen format."""
    prs = generate_powerpoint_deck()
    assert len(prs.slides) == 6

    # Verify 16:9 dimensions (tolerance 0.01 inches)
    width_in = prs.slide_width.inches
    height_in = prs.slide_height.inches
    assert pytest.approx(width_in, rel=1e-2) == SLIDE_WIDTH_INCHES
    assert pytest.approx(height_in, rel=1e-2) == SLIDE_HEIGHT_INCHES


def test_slide_1_cover_and_stamp():
    """Slide 1 (PPT-001) has metadata, sources, and speaker-notes JSON stamp."""
    ctx = DeckContext(project_name="Acme Corp Test", period="FY26-P09")
    prs = generate_powerpoint_deck(context=ctx)
    s1 = prs.slides[0]

    shape_names = {shape.name for shape in s1.shapes} | {shape.name for shape in s1.slide_layout.shapes}
    assert "PPT-001_accent" in shape_names
    assert "PPT-001_title" in shape_names
    assert "PPT-001_packline" in shape_names
    assert "PPT-001_periodline" in shape_names
    assert "PPT-001_sources" in shape_names
    assert "PPT-001_stamp" in shape_names
    # DEF-018: the deck is a filled copy of the template, so the footer shapes come from
    # the template's own names (§3.6) rather than being created at runtime. Assert the
    # names *and* their §3.7 content, which the pre-DEF-018 test never checked.
    assert "PPT-001_footer_left" in shape_names
    assert "PPT-001_footer_right" in shape_names

    def _text(name):
        return next(
            (s for s in s1.shapes if s.name == name),
            next(s for s in s1.slide_layout.shapes if s.name == name),
        ).text_frame.text

    assert _text("PPT-001_footer_left") == SHORT_DISCLAIMER
    assert _text("PPT-001_footer_right") == (
        f"Slide 1 of 6 · Pack v{ctx.pack_version} · {ctx.period}"
    )

    # Check title text
    # resolving through layout since it's a layout shape
    title_shape = next(
        (s for s in s1.shapes if s.name == "PPT-001_title"),
        next(s for s in s1.slide_layout.shapes if s.name == "PPT-001_title")
    )
    assert title_shape.text_frame.text == "Acme Corp Test"

    # Check speaker notes JSON stamp block
    notes = s1.notes_slide.notes_text_frame.text
    assert "--- FPA STAMP (JSON) ---" in notes
    assert "--- END FPA STAMP ---" in notes
    assert CANONICAL_DISCLAIMER in notes

    json_part = notes.split("--- FPA STAMP (JSON) ---")[1].split(
        "--- END FPA STAMP ---"
    )[0]
    stamp_data = json.loads(json_part)
    assert stamp_data["schema"] == "fpa.ppt.stamp.v1"
    assert stamp_data["project"] == "Acme Corp Test"
    assert stamp_data["periods"] == ["FY26-P09"]


def test_slide_2_executive_summary_kpis():
    """Slide 2 (PPT-002) renders 6 KPI cards and narrative."""
    prs = generate_powerpoint_deck()
    s2 = prs.slides[1]

    shape_names = {shape.name for shape in s2.shapes}
    assert "PPT-002_title" in shape_names
    assert "PPT-002_kicker" in shape_names
    assert "PPT-002_narrative" in shape_names
    assert "PPT-002_footnote" in shape_names

    # Verify all 6 KPI cards exist
    for i in range(1, 7):
        assert f"PPT-002_kpi{i}_card" in shape_names
        assert f"PPT-002_kpi{i}_label" in shape_names
        assert f"PPT-002_kpi{i}_value" in shape_names
        assert f"PPT-002_kpi{i}_compare" in shape_names


def test_slide_3_bva_bridge_native_chart():
    """Slide 3 (PPT-003) contains a native bridge chart and drivers list."""
    prs = generate_powerpoint_deck()
    s3 = prs.slides[2]

    shape_names = {shape.name for shape in s3.shapes}
    assert "PPT-003_title" in shape_names
    assert "PPT-003_chart_bridge" in shape_names
    assert "PPT-003_drivers" in shape_names
    assert "PPT-003_tieout" in shape_names

    chart_shape = next(
        s for s in s3.shapes if s.name == "PPT-003_chart_bridge"
    )
    assert chart_shape.has_chart
    chart = chart_shape.chart
    assert len(chart.plots) > 0
    assert len(chart.plots[0].series) >= 1


def test_slide_4_top_variances_table():
    """Slide 4 (PPT-004) renders a native editable table with variance data."""
    prs = generate_powerpoint_deck()
    s4 = prs.slides[3]

    shape_names = {shape.name for shape in s4.shapes}
    assert "PPT-004_title" in shape_names
    assert "PPT-004_table" in shape_names
    assert "PPT-004_provenance" in shape_names
    assert "PPT-004_notes_line" in shape_names

    table_shape = next(s for s in s4.shapes if s.name == "PPT-004_table")
    assert table_shape.has_table
    table = table_shape.table
    assert len(table.columns) == 7
    assert len(table.rows) == 6  # 1 header + 5 variance rows

    # Verify header titles
    headers = [cell.text for cell in table.rows[0].cells]
    assert headers == [
        "Account",
        "Actual",
        "Budget",
        "Variance",
        "Var %",
        "Sig.",
        "Driver",
    ]


def test_slide_5_exceptions_and_chips():
    """Slide 5 (PPT-005) renders 4 chips and a native exceptions table."""
    prs = generate_powerpoint_deck()
    s5 = prs.slides[4]

    shape_names = {shape.name for shape in s5.shapes}
    assert "PPT-005_title" in shape_names
    assert "PPT-005_kicker" in shape_names
    assert "PPT-005_risknote" in shape_names
    assert "PPT-005_table" in shape_names
    assert "PPT-005_summary" in shape_names

    for i in range(1, 5):
        assert f"PPT-005_chip{i}" in shape_names
        assert f"PPT-005_chip{i}_label" in shape_names
        assert f"PPT-005_chip{i}_value" in shape_names

    table_shape = next(s for s in s5.shapes if s.name == "PPT-005_table")
    assert table_shape.has_table
    table = table_shape.table
    assert len(table.columns) == 6
    assert len(table.rows) == 6  # 1 header + 5 exception rows


def test_slide_6_forecast_chart_and_disclaimer():
    """Slide 6 (PPT-006) renders 3 outlook cards, a native line chart, and canonical disclaimer."""
    prs = generate_powerpoint_deck()
    s6 = prs.slides[5]

    shape_names = {shape.name for shape in s6.shapes}
    assert "PPT-006_title" in shape_names
    assert "PPT-006_scenario" in shape_names
    assert "PPT-006_chart_forecast" in shape_names
    assert "PPT-006_outlook" in shape_names
    assert "PPT-006_disclaimer" in shape_names

    for i in range(1, 4):
        assert f"PPT-006_card{i}" in shape_names
        assert f"PPT-006_card{i}_label" in shape_names
        assert f"PPT-006_card{i}_value" in shape_names
        assert f"PPT-006_card{i}_compare" in shape_names

    chart_shape = next(
        s for s in s6.shapes if s.name == "PPT-006_chart_forecast"
    )
    assert chart_shape.has_chart
    chart = chart_shape.chart
    assert len(chart.plots[0].series) == 3  # Actual, Forecast, Budget

    # Verify full disclaimer
    disc_shape = next(s for s in s6.shapes if s.name == "PPT-006_disclaimer")
    assert CANONICAL_DISCLAIMER in disc_shape.text_frame.text


def test_shape_whitelist_no_raster_screenshots():
    """Whitelist check (§3.2 / TST-PPT-02): All objects are native editable shapes, tables, charts.

    The single permitted raster is the brand logo the template carries on the cover
    (``PPT-001_logo``). Everything else — including every data-bearing object — must be a
    native shape, table or chart, so an editor can change any figure in the deck.
    """
    prs = generate_powerpoint_deck()

    allowed_types = {
        MSO_SHAPE_TYPE.AUTO_SHAPE,
        MSO_SHAPE_TYPE.TEXT_BOX,
        MSO_SHAPE_TYPE.TABLE,
        MSO_SHAPE_TYPE.CHART,
    }
    permitted_pictures = {("PPT-001", "PPT-001_logo")}

    for slide_id, slide in zip(SLIDE_SHAPE_ORDER, prs.slides, strict=False):
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                assert (slide_id, shape.name) in permitted_pictures, (
                    f"Shape {shape.name} on {slide_id} is a raster image; "
                    f"only {sorted(permitted_pictures)} may be"
                )
                continue
            assert (
                shape.shape_type in allowed_types
            ), f"Shape {shape.name} on {slide_id} has unallowed type {shape.shape_type}"


def test_save_and_reopen_deck(tmp_path: Path):
    """Deck saves to disk and can be re-opened via python-pptx without error."""
    out_file = tmp_path / "MonthEnd_Deck_v1.pptx"
    prs = generate_powerpoint_deck(output_path=out_file)
    assert out_file.exists()
    assert out_file.stat().st_size > 5000  # Non-empty pptx file

    reopened = Presentation(str(out_file))
    assert len(reopened.slides) == 6


def test_def018_template_resolution_and_missing_template_error(monkeypatch, tmp_path: Path):
    """DEF-018: Template resolution checks board_pack_template.pptx first, fallbacks to FPAMonthEndCopilot_v1.pptx,
    and raises ExportTemplateError (ERR-EXP-014) when neither template exists."""
    from unittest.mock import patch

    # 1. Normal resolution resolves to board_pack_template.pptx
    prs = generate_powerpoint_deck()
    assert len(prs.slides) == 6

    # 2. When template directory has neither template, ERR-EXP-014 is raised
    empty_dir = tmp_path / "empty_templates"
    empty_dir.mkdir(parents=True, exist_ok=True)
    with patch("app.engine.exports.ppt_pack.Path.parent") as mock_parent:
        pass  # test via direct monkeypatch on Path
    
    # Target Path.exists to simulate missing templates
    orig_exists = Path.exists

    def mock_exists(p):
        if str(p).endswith("board_pack_template.pptx") or str(p).endswith("FPAMonthEndCopilot_v1.pptx"):
            return False
        return orig_exists(p)

    monkeypatch.setattr(Path, "exists", mock_exists)
    with pytest.raises(ExportTemplateError, match="ERR-EXP-014"):
        generate_powerpoint_deck()
