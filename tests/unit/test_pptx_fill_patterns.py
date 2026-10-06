"""Tests for the template-fill engine ``app.engine.pptx_fill`` (docs/12 §3.6, §3.7, §5.2, §5.3).

Written from the contract rather than from the code, as ``E13`` requires for the adopted
sources: upstream WS-10 ships no tests, so every behaviour asserted here comes from a
docs/12 clause or from an ``ADP-nnn`` divergence note. The strongest of these is
``test_set_text_preserves_template_run_formatting`` — it pins the behaviour that makes
the whole adoption worthwhile, and the one that is easy to lose to a future "simplify".
"""

from __future__ import annotations

import zipfile

import pytest
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from app.engine.pptx_fill import (
    DECK_SLIDES,
    SHAPE_CONTRACT,
    SLIDE_LAYOUTS,
    SLIDE_SHAPE_ORDER,
    TemplateShapeError,
    TextStyle,
    add_slide_from_layout,
    contract_names,
    default_template_dir,
    fill_order,
    fill_table,
    has_shape,
    layout_for,
    layout_shape_names,
    open_template,
    promote_layout_shapes,
    remove_shape,
    remove_slide,
    replace_chart_data,
    resolve_layout,
    resolve_shape,
    resolve_template_path,
    select_charts,
    select_tables,
    select_text_shapes,
    set_cell_text,
    set_notes,
    set_text,
    set_value_axis,
    shape_names,
)
from app.engine.pptx_fill.core import FALLBACK_TEMPLATE_NAME, PRIMARY_TEMPLATE_NAME

TEMPLATE = default_template_dir() / FALLBACK_TEMPLATE_NAME

_C_SPPR = "{http://schemas.openxmlformats.org/drawingml/2006/chart}spPr"


def _sppr_xml(series) -> str:
    """The ``<c:spPr>`` block of a chart series — its authored line/fill styling."""
    node = series._element.find(_C_SPPR)
    assert node is not None, "template series must carry authored shape properties"
    return node.xml


# ---------------------------------------------------------------------------
# The shape contract (§3.6)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("slide_id", DECK_SLIDES)
def test_every_contract_shape_exists_on_its_layout(slide_id):
    """§3.6: a missing name means a damaged template, so all names must resolve."""
    prs = open_template()
    on_layout = set(layout_shape_names(prs, layout_for(slide_id)))
    assert not contract_names(slide_id) - on_layout


def test_layout_name_matches_the_declared_mapping():
    """Each slide id maps to its own layout, and layouts are distinct."""
    assert set(SLIDE_LAYOUTS.values()) >= {layout_for(s) for s in DECK_SLIDES}
    assert len({layout_for(s) for s in DECK_SLIDES}) == len(DECK_SLIDES)


def test_all_seven_template_layouts_resolve():
    """§3.6 declares seven layouts; all must resolve, including the §6 disclaimer layout."""
    prs = open_template()
    assert len(prs.slide_layouts) == 7
    for layout_name in SLIDE_LAYOUTS.values():
        assert resolve_layout(prs, layout_name) is not None


def test_disclaimer_layout_is_the_seventh_and_is_not_a_deck_slide():
    """§3.7 routes the full disclaimer to the last slide in built-in mode (§6 for base decks)."""
    assert len(SLIDE_LAYOUTS) == 7
    assert len(DECK_SLIDES) == 6
    assert SLIDE_LAYOUTS["PPT-00D"] == "FPA-PPT-DISCLAIMER"
    assert "PPT-00D" not in SHAPE_CONTRACT


def test_fill_order_is_title_first_and_footer_last():
    """§3.6 fixes the write order; the footer band always comes last."""
    for slide_id in DECK_SLIDES:
        order = list(fill_order(slide_id))
        assert order[0] == f"{slide_id}_title"
        assert order[-2:] == [
            f"{slide_id}_footer_left",
            f"{slide_id}_footer_right",
        ]


def test_contract_is_append_only_in_shape_count():
    """A regression guard on the contract itself: the deck's shape totals."""
    totals = {s: len(contract_names(s)) for s in DECK_SLIDES}
    assert totals == {
        "PPT-001": 9,
        "PPT-002": 37,
        "PPT-003": 7,
        "PPT-004": 7,
        "PPT-005": 19,
        "PPT-006": 16,
    }


def test_layout_with_zero_shapes_raises():
    """A layout that does not exist is a damaged template (ERR-EXP-014)."""
    prs = open_template()
    with pytest.raises(TemplateShapeError, match="ERR-EXP-014"):
        resolve_layout(prs, "FPA-PPT-NOPE")


# ---------------------------------------------------------------------------
# Template resolution (§3.6, §6.1)
# ---------------------------------------------------------------------------
def test_resolve_prefers_primary_then_falls_back(tmp_path):
    (tmp_path / FALLBACK_TEMPLATE_NAME).write_bytes(b"fallback")
    assert resolve_template_path(tmp_path) == tmp_path / FALLBACK_TEMPLATE_NAME

    (tmp_path / PRIMARY_TEMPLATE_NAME).write_bytes(b"primary")
    assert resolve_template_path(tmp_path) == tmp_path / PRIMARY_TEMPLATE_NAME


def test_resolve_raises_when_no_template_exists(tmp_path):
    with pytest.raises(TemplateShapeError, match="ERR-EXP-014"):
        resolve_template_path(tmp_path)


def test_shipped_template_is_found_by_default():
    """The resolver finds the template that ships with the app."""
    assert resolve_template_path().exists()


# ---------------------------------------------------------------------------
# Promoting layout shapes onto the slide (§3.6)
# ---------------------------------------------------------------------------
def test_promoted_slide_owns_every_layout_shape():
    """§3.6: the deck is a filled copy — the shapes live on the slide, editable."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])
    layout_names = {s.name for s in slide.slide_layout.shapes}
    slide_names = {s.name for s in slide.shapes}
    assert layout_names == slide_names
    assert len(slide.shapes) == 37


def test_promoted_shapes_keep_the_template_geometry_and_position():
    """§3.6: geometry and z-order come from the template and are never re-authored."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])
    layout_geometry = {
        s.name: (s.left, s.top, s.width, s.height) for s in slide.slide_layout.shapes
    }
    slide_geometry = {s.name: (s.left, s.top, s.width, s.height) for s in slide.shapes}
    assert slide_geometry == layout_geometry
    # Z-order is the layout's order, preserved.
    assert [s.name for s in slide.shapes] == [s.name for s in slide.slide_layout.shapes]


def test_promote_layout_shapes_can_be_called_directly():
    """The verb is usable on a slide added without it."""
    prs = open_template()
    slide = prs.slides.add_slide(resolve_layout(prs, SLIDE_LAYOUTS["PPT-001"]))
    assert len(slide.shapes) == 0
    promote_layout_shapes(slide)
    assert len(slide.shapes) == 9


def test_resolve_shape_prefers_the_slide_over_the_layout():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    found = resolve_shape(slide, "PPT-001_title")
    assert found.name == "PPT-001_title"
    assert found in list(slide.shapes)


def test_resolve_shape_raises_for_unknown_name():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    with pytest.raises(TemplateShapeError, match="ERR-EXP-014"):
        resolve_shape(slide, "PPT-001_does_not_exist")
    assert has_shape(slide, "PPT-001_title") is True
    assert has_shape(slide, "PPT-001_does_not_exist") is False


def test_shape_names_covers_slide_and_layout_without_duplicates():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    names = shape_names(slide)
    assert len(names) == len(set(names))
    assert "PPT-003_chart_bridge" in names


# ---------------------------------------------------------------------------
# The text verb — template formatting must survive the write
# ---------------------------------------------------------------------------
def test_set_text_preserves_template_run_formatting():
    """Writing into an existing run keeps the size, weight, colour and typeface.

    Assigning to ``text_frame.text`` instead rebuilds the run and drops its ``rPr``,
    which silently discards everything docs/12 §3.3 specifies for that shape. This is
    the regression the adoption exists to prevent.
    """
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])
    title = resolve_shape(slide, "PPT-002_title")

    before_run = title.text_frame.paragraphs[0].runs[0]
    expected_size = before_run.font.size
    expected_bold = before_run.font.bold
    expected_rgb = before_run.font.color.rgb

    set_text(title, "Executive summary — FY26-P09")

    run = title.text_frame.paragraphs[0].runs[0]
    assert run.text == "Executive summary — FY26-P09"
    assert run.font.size == expected_size
    assert run.font.bold == expected_bold
    assert run.font.color.rgb == expected_rgb
    assert run.font.name == "Calibri"


def test_set_text_multi_line_inherits_first_paragraph_formatting():
    """Extra paragraphs are cloned from the first, so they carry the same styling."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    sources = resolve_shape(slide, "PPT-001_sources")
    set_text(sources, ["SOURCES", "one.xlsx · batch 1 · 10 rows", "two.csv · batch 2 · 5 rows"])

    paragraphs = sources.text_frame.paragraphs
    assert [p.text for p in paragraphs] == [
        "SOURCES",
        "one.xlsx · batch 1 · 10 rows",
        "two.csv · batch 2 · 5 rows",
    ]
    sizes = {p.runs[0].font.size for p in paragraphs}
    assert len(sizes) == 1


def test_set_text_applies_per_line_styles():
    """A ``None`` style leaves that line as the template authored it.

    Extra paragraphs are cloned from the first *before* any style is applied, so a
    sibling line's override never leaks into a line that did not ask for it.
    """
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    sources = resolve_shape(slide, "PPT-001_sources")
    template_bold = sources.text_frame.paragraphs[0].runs[0].font.bold
    assert template_bold is False  # the template ships the block unbolded

    set_text(
        sources,
        ["SOURCES", "row"],
        styles=[TextStyle(bold=True), None],
    )
    runs = [p.runs[0] for p in sources.text_frame.paragraphs]
    assert runs[0].font.bold is True
    assert runs[1].font.bold is template_bold


def test_multi_line_cloning_happens_before_styles_are_applied():
    """Cloning from an already-styled first line would restyle the body silently."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])
    narrative = resolve_shape(slide, "PPT-002_narrative")
    set_text(narrative, ["big", "small"], style=TextStyle(bold=True))
    assert [p.runs[0].font.bold for p in narrative.text_frame.paragraphs] == [True, True]


def test_set_text_overrides_size_colour_and_alignment():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    tieout = resolve_shape(slide, "PPT-003_tieout")
    set_text(tieout, "aligned right", style=TextStyle(size_pt=7, bold=True, align=PP_ALIGN.RIGHT))
    paragraph = tieout.text_frame.paragraphs[0]
    assert paragraph.runs[0].font.size == Pt(7)
    assert paragraph.runs[0].font.bold is True
    assert paragraph.alignment == PP_ALIGN.RIGHT


def test_set_text_drops_surplus_paragraphs_and_runs():
    """Writing fewer lines than the frame holds must not leave stale text behind."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    sources = resolve_shape(slide, "PPT-001_sources")
    set_text(sources, ["a", "b", "c", "d"])
    assert len(sources.text_frame.paragraphs) == 4
    set_text(sources, ["only one"])
    assert sources.text_frame.text == "only one"


def test_set_text_creates_a_run_when_the_frame_has_none():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    sources = resolve_shape(slide, "PPT-001_sources")
    tf = sources.text_frame
    tf.clear()
    for run in list(tf.paragraphs[0].runs):
        run._r.getparent().remove(run._r)
    set_text(sources, "rebuilt")
    assert tf.text == "rebuilt"


def test_set_text_accepts_a_text_frame_directly():
    """Chart titles are text frames, not shapes."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    chart = resolve_shape(slide, "PPT-003_chart_bridge").chart
    set_text(chart.chart_title.text_frame, "Bridge title")
    assert chart.chart_title.text_frame.text == "Bridge title"


# ---------------------------------------------------------------------------
# The table verb
# ---------------------------------------------------------------------------
def test_fill_table_writes_a_matrix_and_keeps_template_geometry():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-004"])
    shape = resolve_shape(slide, "PPT-004_table")
    widths_before = [c.width for c in shape.table.columns]
    heights_before = [r.height for r in shape.table.rows]

    fill_table(
        shape,
        [["Account", "Actual"], ["5600 Repairs", "355,000.00"], ["5300 Materials", "618,000.00"]],
        cell_styles={(1, 1): TextStyle(align=PP_ALIGN.RIGHT)},
        row_fills={1: None},
    )

    assert shape.table.cell(0, 0).text == "Account"
    assert shape.table.cell(2, 0).text == "5300 Materials"
    assert shape.table.cell(1, 1).text == "355,000.00"
    assert shape.table.cell(1, 1).text_frame.paragraphs[0].alignment == PP_ALIGN.RIGHT
    # §3.6 — the template owns geometry; filling must not resize anything.
    assert [c.width for c in shape.table.columns] == widths_before
    assert [r.height for r in shape.table.rows] == heights_before


def test_fill_table_ignores_rows_and_columns_beyond_the_template():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-004"])
    shape = resolve_shape(slide, "PPT-004_table")
    rows_before = len(shape.table.rows)
    cols_before = len(shape.table.columns)

    fill_table(shape, [["x"] * 12 for _ in range(20)])

    assert len(shape.table.rows) == rows_before
    assert len(shape.table.columns) == cols_before


def test_fill_table_renders_none_as_empty_and_applies_row_fills():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-004"])
    shape = resolve_shape(slide, "PPT-004_table")
    fill_table(shape, [["Account"], [None]], row_fills={1: None})
    assert shape.table.cell(1, 0).text == ""
    assert shape.table.cell(1, 0).fill.type is not None


def test_fill_table_header_row_uses_header_style():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-005"])
    shape = resolve_shape(slide, "PPT-005_table")
    fill_table(
        shape,
        [["Rule"], ["R-01"]],
        header=True,
        header_style=TextStyle(bold=True),
        cell_style=TextStyle(bold=False),
    )
    runs = [
        shape.table.rows[i].cells[0].text_frame.paragraphs[0].runs[0] for i in (0, 1)
    ]
    assert runs[0].font.bold is True
    assert runs[1].font.bold is False


def test_set_cell_text_applies_a_fill_colour():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-004"])
    cell = resolve_shape(slide, "PPT-004_table").table.cell(1, 0)
    set_cell_text(cell, "5600 Repairs", style=TextStyle(bold=True), fill_color=RGBColor(0xEE, 0xEE, 0xEE))
    assert cell.text == "5600 Repairs"
    assert cell.text_frame.paragraphs[0].runs[0].font.bold is True
    assert cell.fill.fore_color.rgb == RGBColor(0xEE, 0xEE, 0xEE)


# ---------------------------------------------------------------------------
# The chart verb (§5.2, §5.3)
# ---------------------------------------------------------------------------
def test_replace_chart_data_keeps_chart_type_and_series_formatting():
    """The template pre-styles every series; pushing data must not restyle them."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-006"])
    shape = resolve_shape(slide, "PPT-006_chart_forecast")
    before_type = shape.chart.chart_type
    before_sppr = [_sppr_xml(s) for s in shape.chart.plots[0].series]

    replace_chart_data(
        shape,
        ["P01", "P02", "P03"],
        [("Actual", (1.0, 2.0, 3.0)), ("Forecast", (None, 2.1, 3.1)), ("Budget", (1.1, 2.2, 3.2))],
    )

    plot = shape.chart.plots[0]
    assert shape.chart.chart_type == before_type
    assert [s.name for s in plot.series] == ["Actual", "Forecast", "Budget"]
    # Every series keeps the exact shape properties the template authored: the
    # Actual/Forecast line colours and the Budget dash pattern survive the data write.
    assert [_sppr_xml(s) for s in plot.series] == before_sppr


def test_replace_chart_data_preserves_gaps_as_empty_points():
    """§5.3: the gap between closed and forecast periods stays visible."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-006"])
    shape = resolve_shape(slide, "PPT-006_chart_forecast")
    replace_chart_data(
        shape,
        ["P01", "P02", "P03"],
        [("Actual", (1.0, 2.0, None)), ("Forecast", (None, 2.1, 3.0)), ("Budget", (1.1, 2.2, 3.3))],
    )
    plot = shape.chart.plots[0]
    actual = list(plot.series[0].values)
    forecast = list(plot.series[1].values)
    assert actual[2] is None
    assert forecast[0] is None
    assert forecast[1] == 2.1


def test_replace_chart_data_writes_the_title_and_toggles_the_legend():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    shape = resolve_shape(slide, "PPT-003_chart_bridge")
    replace_chart_data(
        shape,
        ["A", "B"],
        [("base", (0, 1)), ("amount", (1, 2))],
        title="Bridge: FY26-P09",
        legend=False,
    )
    assert shape.chart.chart_type.name == "COLUMN_STACKED"
    assert shape.chart.chart_title.text_frame.text == "Bridge: FY26-P09"
    assert shape.chart.has_legend is False


def test_replace_chart_data_accepts_none_categories():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-006"])
    shape = resolve_shape(slide, "PPT-006_chart_forecast")
    replace_chart_data(shape, [None, "P02"], [("Actual", (1, 2))])
    # python-pptx reads an empty <c:v/> back as None, so assert on the XML it wrote:
    # the slot is present and blank, and no literal "None" reaches the file.
    chart_xml = shape.chart._chartSpace.xml
    assert "<c:v/>" in chart_xml
    assert ">None<" not in chart_xml
    assert [c.label for c in shape.chart.plots[0].categories][1] == "P02"


def test_set_value_axis_pins_the_scale():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    chart = resolve_shape(slide, "PPT-003_chart_bridge").chart
    set_value_axis(chart, maximum=18000000.0, minimum=0.0)
    axis = chart.value_axis
    assert axis.maximum_scale == 18000000.0
    assert axis.minimum_scale == 0.0


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------
def test_remove_shape_deletes_by_name_and_reports_whether_it_found_one():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    assert remove_shape(slide, "PPT-003_drivers") is True
    assert "PPT-003_drivers" not in [s.name for s in slide.shapes]
    assert remove_shape(slide, "PPT-003_drivers") is False


def test_remove_slide_drops_the_slide_and_its_relationship():
    prs = open_template()
    keep = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    drop = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])
    rids_before = len(prs.part.rels)
    remove_slide(prs, drop)
    assert len(prs.slides) == 1
    assert prs.slides[0] is keep
    assert len(prs.part.rels) < rids_before


def test_removal_survives_save_and_reopen(tmp_path):
    prs = open_template()
    add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-002"])
    remove_slide(prs, prs.slides[1])
    out = tmp_path / "trimmed.pptx"
    prs.save(str(out))
    assert len(Presentation(str(out)).slides) == 1


# ---------------------------------------------------------------------------
# Shape selection helpers
# ---------------------------------------------------------------------------
def test_selectors_partition_the_promoted_shapes():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-004"])
    assert len(select_text_shapes(slide)) == 6
    assert len(select_tables(slide)) == 1
    assert select_charts(slide) == []


def test_select_charts_finds_both_template_charts():
    prs = open_template()
    bridge = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-003"])
    forecast = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-006"])
    assert [s.name for s in select_charts(bridge)] == ["PPT-003_chart_bridge"]
    assert [s.name for s in select_charts(forecast)] == ["PPT-006_chart_forecast"]


def test_set_notes_writes_the_speaker_notes():
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    set_notes(slide, "line one\nline two")
    assert slide.notes_slide.notes_text_frame.text == "line one\nline two"


# ---------------------------------------------------------------------------
# Round trip: the promoted deck must be a valid, self-contained package
# ---------------------------------------------------------------------------
def test_promoted_deck_survives_save_and_reopen_with_its_parts(tmp_path):
    """Chart and image parts must belong to the slide that uses them, not the layout."""
    prs = open_template()
    for slide_id in DECK_SLIDES:
        slide = add_slide_from_layout(prs, SLIDE_LAYOUTS[slide_id])
        for name in SLIDE_SHAPE_ORDER[slide_id]:
            shape = resolve_shape(slide, name)
            if shape.has_chart:
                replace_chart_data(
                    shape,
                    ["c1", "c2"],
                    [("base", (0, 1)), ("amount", (1, 2))] if "003" in slide_id
                    else [("Actual", (1, 2)), ("Forecast", (None, 2)), ("Budget", (3, 4))],
                )
            elif shape.has_text_frame:
                set_text(shape, name)

    out = tmp_path / "deck.pptx"
    prs.save(str(out))

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        chart_parts = [n for n in archive.namelist() if n.startswith("ppt/charts/chart")]
        # One chart part per chart shape — charts are duplicated per slide, never shared.
        assert len(chart_parts) == 2
        assert len(set(chart_parts)) == 2
        content_types = archive.read("[Content_Types].xml").decode("utf-8")
        assert "chart+xml" in content_types
        assert "spreadsheetml.sheet" in content_types

    reopened = Presentation(str(out))
    assert len(reopened.slides) == len(DECK_SLIDES)
    for slide_id, slide in zip(DECK_SLIDES, reopened.slides, strict=False):
        present = {s.name for s in slide.shapes}
        assert not contract_names(slide_id) - present


def test_promoted_logo_picture_relates_to_the_slide(tmp_path):
    """The cover logo's image relationship must be re-pointed at the slide."""
    prs = open_template()
    slide = add_slide_from_layout(prs, SLIDE_LAYOUTS["PPT-001"])
    out = tmp_path / "logo.pptx"
    prs.save(str(out))
    reopened = Presentation(str(out))
    logo = next(s for s in reopened.slides[0].shapes if s.name == "PPT-001_logo")
    assert logo.shape_type == MSO_SHAPE_TYPE.PICTURE
    assert logo.image.blob


# ---------------------------------------------------------------------------
# TST-PPT-08 — determinism
# ---------------------------------------------------------------------------
def test_two_runs_from_the_same_context_produce_identical_slide_xml():
    """§3.6 determinism: the same context yields the same slide XML, run to run."""

    def slide_xml():
        prs = open_template()
        for slide_id in DECK_SLIDES:
            slide = add_slide_from_layout(prs, SLIDE_LAYOUTS[slide_id])
            for name in SLIDE_SHAPE_ORDER[slide_id]:
                shape = resolve_shape(slide, name)
                if shape.has_chart:
                    replace_chart_data(
                        shape,
                        ["c1", "c2", "c3"],
                        [("base", (0, 1, 2)), ("amount", (1, 2, 3))]
                        if "003" in slide_id
                        else [("Actual", (1, 2, 3)), ("Forecast", (None, 2, 3)), ("Budget", (4, 5, 6))],
                        title="t",
                        legend=False,
                    )
                elif shape.has_table:
                    fill_table(shape, [[name]])
                elif shape.has_text_frame:
                    set_text(shape, name)
        return [slide._element.xml for slide in prs.slides]

    assert slide_xml() == slide_xml()


def test_add_slide_from_layout_uses_the_named_layout():
    prs = open_template()
    for slide_id in DECK_SLIDES:
        slide = add_slide_from_layout(prs, SLIDE_LAYOUTS[slide_id])
        assert slide.slide_layout.name == SLIDE_LAYOUTS[slide_id]