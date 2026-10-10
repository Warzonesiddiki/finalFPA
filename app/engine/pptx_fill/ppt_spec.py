# Adapted from https://github.com/m3dev/pptx-template @ dc448cb1203443e503a558846dc1ce4c4b7ada3d (Apache-2.0) — ADP-001 —
"""The deck's shape contract and the canonical order shapes are written in.

``docs/12_POWERPOINT_OUTPUT_SPEC.md`` §3.6 requires two things of the engine: every shape
is resolved by name, and those shapes are written in a fixed order — title, kicker, body
blocks top-to-bottom and left-to-right, then charts, then tables, then cards, then the
accent bar, then the logo, then the footer — so the saved XML is stable between runs
(``TST-PPT-08``). ``SLIDE_SHAPE_ORDER`` below is that order, declared per slide.

Upstream keeps no such list: it discovers shapes by walking each slide for whatever it
finds. That is exactly what §3.6 rules out, so the order is declared here instead and
asserted against the committed template by ``tests/unit/test_pptx_fill_patterns.py``.

A block's container shape is listed before the text it carries, so a card's background
fill is written before the label, value and comparison that sit on top of it. This is the
*fill* order; z-order is authored once in the template and never re-ordered at runtime.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

#: Layout each slide is built from (§3.6 — seven layouts).
SLIDE_LAYOUTS: Mapping[str, str] = {
    "PPT-001": "FPA-PPT-001",
    "PPT-002": "FPA-PPT-002",
    "PPT-003": "FPA-PPT-003",
    "PPT-004": "FPA-PPT-004",
    "PPT-005": "FPA-PPT-005",
    "PPT-006": "FPA-PPT-006",
    "PPT-00D": "FPA-PPT-DISCLAIMER",
}

#: The deck's six slides, in presentation order (§2.1).
#:
#: Six, not seven: ``FPA-PPT-DISCLAIMER`` is the seventh layout and is not a slide. §3.7 routes the
#: full canonical disclaimer to the **last slide** (``PPT-006``) in built-in mode, "with a client base
#: deck that has its own disclaimer layout, the text goes there instead (§6)". So the seventh layout
#: is the target for base-deck mode (§6) and for converting this template into a client's, and a
#: six-slide acceptance is asserted on the generated slides in base-deck mode (§2.1). Its shapes are
#: therefore resolvable (see :func:`~app.engine.pptx_fill.core.resolve_layout`) but carry no data here.
DECK_SLIDES: Sequence[str] = (
    "PPT-001",
    "PPT-002",
    "PPT-003",
    "PPT-004",
    "PPT-005",
    "PPT-006",
)


def _kpi_block(prefix: str, count: int) -> tuple[str, ...]:
    return tuple(
        f"{prefix}_kpi{n}_{role}"
        for n in range(1, count + 1)
        for role in ("card", "signal", "label", "value", "compare")
    )


def _chip_block(prefix: str, count: int) -> tuple[str, ...]:
    # The chip container is listed before its label and value: its fill is data-driven
    # (an overdue chip is tinted), so the engine writes it rather than the template.
    return tuple(
        f"{prefix}_chip{n}_{role}".rstrip("_")
        for n in range(1, count + 1)
        for role in ("", "label", "value")
    )


def _card_block(prefix: str, count: int) -> tuple[str, ...]:
    return tuple(
        f"{prefix}_card{n}_{role}"
        for n in range(1, count + 1)
        for role in ("label", "value", "compare")
    )


def _footer(prefix: str) -> tuple[str, ...]:
    return (f"{prefix}_footer_left", f"{prefix}_footer_right")


#: Canonical write order per slide. Every name here must exist on that slide's layout.
SLIDE_SHAPE_ORDER: Mapping[str, Sequence[str]] = {
    "PPT-001": (
        "PPT-001_title",
        "PPT-001_packline",
        "PPT-001_periodline",
        "PPT-001_sources",
        "PPT-001_stamp",
        "PPT-001_accent",
        "PPT-001_logo",
        *_footer("PPT-001"),
    ),
    "PPT-002": (
        "PPT-002_title",
        "PPT-002_kicker",
        *_kpi_block("PPT-002", 6),
        "PPT-002_narrative_label",
        "PPT-002_narrative",
        "PPT-002_footnote",
        *_footer("PPT-002"),
    ),
    "PPT-003": (
        "PPT-003_title",
        "PPT-003_kicker",
        "PPT-003_chart_bridge",
        "PPT-003_drivers",
        "PPT-003_tieout",
        *_footer("PPT-003"),
    ),
    "PPT-004": (
        "PPT-004_title",
        "PPT-004_kicker",
        "PPT-004_table",
        "PPT-004_provenance",
        "PPT-004_notes_line",
        *_footer("PPT-004"),
    ),
    "PPT-005": (
        "PPT-005_title",
        "PPT-005_kicker",
        *_chip_block("PPT-005", 4),
        "PPT-005_risknote",
        "PPT-005_table",
        "PPT-005_summary",
        *_footer("PPT-005"),
    ),
    "PPT-006": (
        "PPT-006_title",
        "PPT-006_scenario",
        *_card_block("PPT-006", 3),
        "PPT-006_chart_forecast",
        "PPT-006_outlook",
        "PPT-006_disclaimer",
        *_footer("PPT-006"),
    ),
}

#: Names a layout must expose, as a set, for assertions against the committed template.
SHAPE_CONTRACT: Mapping[str, frozenset[str]] = {
    slide_id: frozenset(names) for slide_id, names in SLIDE_SHAPE_ORDER.items()
}


def fill_order(slide_id: str) -> Sequence[str]:
    """The names written for ``slide_id``, in canonical order."""
    return SLIDE_SHAPE_ORDER[slide_id]


def contract_names(slide_id: str) -> frozenset[str]:
    """Set of names the layout for ``slide_id`` must carry."""
    return SHAPE_CONTRACT[slide_id]


def layout_for(slide_id: str) -> str:
    """The layout name ``slide_id`` is built from."""
    return SLIDE_LAYOUTS[slide_id]


#: Semantic colour token per KPI signal (§3.3). Kept as token names so the engine never
#: has to restate what red, green and amber mean for a client house style (§6.1).
SIGNAL_TOKENS: Mapping[str, str] = {
    "favourable": "semantic.favourable",
    "unfavourable": "semantic.unfavourable",
    "warning": "semantic.warning",
    "neutral": "brand.primary",
}
