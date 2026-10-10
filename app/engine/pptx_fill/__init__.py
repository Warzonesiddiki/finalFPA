# Adapted from https://github.com/m3dev/pptx-template @ dc448cb1203443e503a558846dc1ce4c4b7ada3d (Apache-2.0) — ADP-001 —
"""Template-fill engine for the FP&A month-end deck.

``docs/12_POWERPOINT_OUTPUT_SPEC.md`` §3.6 requires the deck to be produced by copying
``packaging/templates/FPAMonthEndCopilot_v1.pptx`` and filling the shapes it already
contains — never by constructing slides from scratch. This package is that fill engine.

Three modules, each from an adopted upstream source (docs/32 ``ADP-001``…``ADP-003``):

* :mod:`~app.engine.pptx_fill.core` — resolves the template, its layouts and the named
  shapes, promotes a layout's shapes onto the slide so each slide owns editable shapes,
  and removes slides or shapes;
* :mod:`~app.engine.pptx_fill.patterns` — the fill verbs: text into a shape, a matrix into
  a table, categories and series into a chart, all preserving template formatting;
* :mod:`~app.engine.pptx_fill.layout` — the overflow cascade, flag-gated and off by default.

:mod:`~app.engine.pptx_fill.ppt_spec` holds the shape contract and the canonical write
order §3.6 names.
"""

from app.engine.pptx_fill.core import (
    FALLBACK_TEMPLATE_NAME,
    PRIMARY_TEMPLATE_NAME,
    TemplateShapeError,
    add_slide_from_layout,
    default_template_dir,
    has_shape,
    layout_shape_names,
    open_template,
    promote_layout_shapes,
    remove_shape,
    remove_slide,
    resolve_layout,
    resolve_shape,
    resolve_template_path,
    set_value_axis,
    shape_names,
)
from app.engine.pptx_fill.patterns import (
    TextStyle,
    fill_table,
    replace_chart_data,
    select_charts,
    select_tables,
    select_text_shapes,
    set_cell_text,
    set_notes,
    set_text,
)
from app.engine.pptx_fill.ppt_spec import (
    DECK_SLIDES,
    SHAPE_CONTRACT,
    SLIDE_LAYOUTS,
    SLIDE_SHAPE_ORDER,
    contract_names,
    fill_order,
    layout_for,
)

__all__ = [
    "DECK_SLIDES",
    "FALLBACK_TEMPLATE_NAME",
    "PRIMARY_TEMPLATE_NAME",
    "SHAPE_CONTRACT",
    "SLIDE_LAYOUTS",
    "SLIDE_SHAPE_ORDER",
    "TextStyle",
    "TemplateShapeError",
    "add_slide_from_layout",
    "contract_names",
    "default_template_dir",
    "fill_order",
    "fill_table",
    "has_shape",
    "layout_for",
    "layout_shape_names",
    "open_template",
    "promote_layout_shapes",
    "remove_shape",
    "remove_slide",
    "replace_chart_data",
    "resolve_layout",
    "resolve_shape",
    "resolve_template_path",
    "select_charts",
    "select_tables",
    "select_text_shapes",
    "set_cell_text",
    "set_notes",
    "set_text",
    "set_value_axis",
    "shape_names",
]
