"""Character budget computation and text trimming engine for PowerPoint exports.

Implements the universal contract from docs/12_POWERPOINT_OUTPUT_SPEC.md §3.4.
"""

from __future__ import annotations

import math
import re
from typing import Tuple

AVG_ADVANCE: float = 0.50
TRIMMED_FOOTNOTE: str = (
    "Trimmed for space — full text in the Excel pack and the commentary editor."
)


def compute_character_budget(
    box_width_inches: float,
    box_height_inches: float,
    font_size_pt: float,
    configured_max_lines: int,
    slack_lines: int = 3,
) -> int:
    """Compute character budget deterministically from geometry and font size.

    Formula (§3.4):
        chars_per_line = floor(box_width_inches * 72 / (AVG_ADVANCE * font_size_pt))
        line_height_in = 1.22 * font_size_pt / 72
        lines_available = floor(box_height_inches / line_height_in)
        design_max_lines = min(max(1, lines_available - slack_lines), configured_max_lines)
        budget_chars = chars_per_line * design_max_lines
    """
    chars_per_line = math.floor(
        (box_width_inches * 72.0) / (AVG_ADVANCE * font_size_pt)
    )
    line_height_in = 1.22 * font_size_pt / 72.0
    lines_available = math.floor(box_height_inches / line_height_in)
    effective_slack = min(slack_lines, max(0, lines_available - 1))
    design_max_lines = min(
        max(1, lines_available - effective_slack), configured_max_lines
    )
    budget_chars = chars_per_line * design_max_lines
    return max(1, budget_chars)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences while keeping delimiters with preceding sentences."""
    if not text:
        return []
    # Split on period, semicolon, newline, or em-dash boundary
    pattern = r"(?<=[.;\n])\s+|(?<=\s—\s)\s*|(?<=—)\s*"
    parts = re.split(pattern, text.strip())
    return [p.strip() for p in parts if p.strip()]


def trim_text_to_budget(text: str, budget: int) -> Tuple[str, bool]:
    """Trim prose text deterministically to fit within character budget.

    Returns (trimmed_text, was_trimmed).
    Follows §3.4 prioritized trimming order:
    1. Drop whole trailing sentences while over budget.
    2. Drop least material sentence if still over budget.
    3. Truncate at word boundary with ' …' if a single sentence exceeds budget.
    """
    if len(text) <= budget:
        return text, False

    sentences = split_sentences(text)
    if not sentences:
        return text[: max(0, budget - 2)] + " …", True

    # 1. Drop whole trailing sentences
    while sentences and sum(len(s) + 1 for s in sentences) - 1 > budget:
        if len(sentences) == 1:
            break
        sentences.pop()

    candidate = " ".join(sentences)
    if len(candidate) <= budget:
        return candidate, True

    # 2. If single sentence still exceeds budget: word boundary truncation
    words = candidate.split()
    trimmed_words: list[str] = []
    for word in words:
        potential = " ".join(trimmed_words + [word]) + " …"
        if len(potential) <= budget:
            trimmed_words.append(word)
        else:
            break

    if trimmed_words:
        return " ".join(trimmed_words) + " …", True
    return candidate[: max(0, budget - 2)] + " …", True
