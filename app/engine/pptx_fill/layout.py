# Adapted from https://github.com/Whatsonyourmind/deckforge @ ae71696f763f85b79f7f94d85484234f57f93f63 (MIT) — ADP-003 —
"""Adaptive overflow cascade: shrink, reflow, split — behind a flag, default off.

Copied and edited from ``src/deckforge/layout/overflow.py`` of the pinned upstream commit,
which handles text that outgrows its box with a three-step cascade: reduce the font by a
step until a floor, re-measure with a narrower width so the text wraps harder, and only
then split the content across continuation slides.

Divergences from upstream (docs/32 row ``ADP-003``, ``DEC-064``):

* the cascade is re-expressed against python-pptx shapes instead of upstream's own IR.
  Upstream takes resolved positions, a layout-solver result, a theme and a text measurer,
  and re-solves after every step; here it measures a real shape with
  ``app.engine.exports.ppt_fit.compute_character_budget`` — the same budget maths docs/12
  §3.4 already defines — and rewrites that shape's runs, so no solver, no font files and
  no pydantic theme objects are needed;
* ``kiwisolver``, ``PIL`` and the rest of upstream's layout package are not copied
  (docs/09 ADR-001 has none of them as runtime dependencies);
* the upstream cascade mutates a model and returns a new one. This version mutates the
  shape it is given and reports what it did, so it composes with the rest of the pipeline.

**Why it ships off.** docs/12 §3.4 makes the character-budget trim the canonical,
always-on path, and §3.6 forbids runtime layout construction. Turning the cascade on would
change slide geometry at generation time, which the spec does not yet describe, so this
module is inert until a §3.4 amendment says otherwise (``ADR-013``). The R12 relationship is
deliberate: the trim path is the spec path, this is an opt-in complement to it, not a
second implementation of it. Set ``FPA_PPT_OVERFLOW_CASCADE=1`` to enable it.
"""

from __future__ import annotations

import os
from typing import Any, NamedTuple

from pptx.util import Pt

from app.engine.exports.ppt_fit import compute_character_budget

#: Environment switch for the cascade. Off unless explicitly set to a truthy value.
CASCADE_FLAG_ENV = "FPA_PPT_OVERFLOW_CASCADE"

_TRUTHY = {"1", "true", "yes", "on"}

#: Floor the cascade will not shrink below (§3.4 keeps body copy readable at 8 pt).
MIN_BODY_FONT_PT = 8.0
#: Headings stop shrinking earlier — a smaller heading is unreadable, not tight.
MIN_HEADING_FONT_PT = 14.0
#: Points removed per iteration.
FONT_REDUCTION_STEP_PT = 1.0
#: Iterations before the cascade gives up and asks for a split.
MAX_ITERATIONS = 5
#: Fraction of the current width used for the reflow re-measure.
REFLOW_WIDTH_RATIO = 0.9
#: Height tolerance in inches before a region counts as overflowing.
OVERFLOW_TOLERANCE_IN = 0.01


class CascadeResult(NamedTuple):
    """What the cascade did to one shape."""

    shape_name: str
    font_pt: float | None
    overflowed: bool
    split_needed: bool


def cascade_enabled() -> bool:
    """True when ``FPA_PPT_OVERFLOW_CASCADE`` is set to a truthy value."""
    return os.environ.get(CASCADE_FLAG_ENV, "").strip().lower() in _TRUTHY


def _run_font_pt(run: Any, default_pt: float) -> float:
    size = run.font.size
    return size.pt if size is not None else default_pt


def shape_box_inches(shape: Any) -> tuple[float, float]:
    """The shape's width and height in inches, or ``(0.0, 0.0)`` when unset."""
    if shape.width is None or shape.height is None:
        return 0.0, 0.0
    return shape.width.inches, shape.height.inches


def measure_lines(shape: Any, font_pt: float, max_lines: int, width_inches: float) -> int:
    """How many lines ``shape``'s text needs at ``font_pt`` in ``width_inches``."""
    text = shape.text_frame.text if shape.has_text_frame else ""
    if not text:
        return 0
    height_in, _ = shape_box_inches(shape)
    chars_per_line = max(1, int(width_inches * 72 / (0.50 * font_pt)))
    lines = 0
    for paragraph in text.split("\n"):
        lines += max(1, -(-len(paragraph) // chars_per_line))
    budget = compute_character_budget(
        box_width_inches=max(0.1, width_inches),
        box_height_inches=max(0.1, height_in),
        font_size_pt=font_pt,
        configured_max_lines=max(1, max_lines * lines),
    )
    return lines if len(text) <= budget else lines + 1


def detect_overflow(shape: Any, font_pt: float, max_lines: int) -> bool:
    """True when ``shape``'s text needs more room than its frame allows."""
    width_in, height_in = shape_box_inches(shape)
    if height_in <= 0:
        return False
    lines = measure_lines(shape, font_pt, max_lines, width_in)
    line_height_in = 1.22 * font_pt / 72.0
    return (lines * line_height_in) > (height_in + OVERFLOW_TOLERANCE_IN)


def _is_heading(shape: Any) -> bool:
    return "title" in shape.name or "subtitle" in shape.name


def _shrink_runs(shape: Any, step_pt: float, floor_pt: float) -> bool:
    """Reduce every run's font by ``step_pt``, stopping at ``floor_pt``."""
    changed = False
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            current = _run_font_pt(run, 18.0)
            reduced = max(current - step_pt, floor_pt)
            if reduced < current:
                run.font.size = Pt(reduced)
                changed = True
    return changed


def handle_overflow(
    shape: Any,
    max_lines: int = 12,
    step_pt: float = FONT_REDUCTION_STEP_PT,
    max_iterations: int = MAX_ITERATIONS,
) -> CascadeResult:
    """Run the three-step cascade against one shape.

    Returns the result without touching the shape when the cascade is disabled, so a
    caller can invoke it unconditionally.
    """
    if not cascade_enabled():
        return CascadeResult(shape.name, None, False, False)

    floor = MIN_HEADING_FONT_PT if _is_heading(shape) else MIN_BODY_FONT_PT
    font_pt = floor
    for run in _iter_runs(shape):
        font_pt = _run_font_pt(run, font_pt)
        break

    for _ in range(max_iterations):
        if not detect_overflow(shape, font_pt, max_lines):
            return CascadeResult(shape.name, font_pt, False, False)
        if font_pt <= floor:
            break
        new_font = max(font_pt - step_pt, floor)
        _shrink_runs(shape, step_pt, floor)
        font_pt = new_font

    if not detect_overflow(shape, font_pt, max_lines):
        return CascadeResult(shape.name, font_pt, False, False)

    # Reflow: give the text a narrower measure so it wraps harder and needs less height.
    width_in, _ = shape_box_inches(shape)
    if width_in > 0:
        shape.width = int(shape.width * REFLOW_WIDTH_RATIO)
        if not detect_overflow(shape, font_pt, max_lines):
            return CascadeResult(shape.name, font_pt, False, False)

    # Still overflowing: the caller is told a split is owed. Splitting is not done here —
    # it changes the slide count, which is a §2.1 contract decision, not a layout one.
    return CascadeResult(shape.name, font_pt, True, True)


def _iter_runs(shape: Any) -> Any:
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            yield run
