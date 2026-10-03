"""Shared rupee-sign (Rs.) helper for user-facing output paths (D-20).

The answer key, rule details and money formatting embed U+20B9 RUPEE SIGN,
which Windows cp1252 consoles cannot encode. Every user-facing output path
(console print, report files, Excel/PPT exports) must therefore prove it
handles the glyph: files round-trip as UTF-8, and console writes never raise.

Import from tests as::

    from tests.helpers_utf8 import RUPEE_SIGN, assert_utf8_file_roundtrip
"""

from __future__ import annotations

from pathlib import Path

#: U+20B9, the glyph cp1252 cannot encode (proved by ``test_rupee_is_unencodable_in_cp1252``).
RUPEE_SIGN = "\u20b9"

#: Representative user-facing strings carrying the glyph.
RUPEE_SAMPLES: tuple[str, ...] = (
    f"{RUPEE_SIGN}500 tolerance",
    f"Var +{RUPEE_SIGN}540000.00 (+5.4%)",
    f"{RUPEE_SIGN} 1,05,40,000.00",
)


def assert_rupee_present(text: str) -> str:
    """Guard that a sample actually carries the glyph (anti-vacuous)."""
    assert RUPEE_SIGN in text, "sample lost the rupee sign; test is vacuous"
    return text


def assert_cp1252_cannot_encode(text: str = RUPEE_SIGN) -> None:
    """Document WHY the console guard exists: cp1252 cannot encode Rs."""
    try:
        text.encode("cp1252")
    except UnicodeEncodeError:
        return
    raise AssertionError("cp1252 encoded the rupee sign; D-20 guard rationale gone")


def assert_utf8_file_roundtrip(tmp_path: Path, text: str) -> Path:
    """Write ``text`` as UTF-8 under ``tmp_path`` and prove it round-trips.

    Covers the file half of every user-facing output path
    (``write_reports`` already uses ``encoding="utf-8"``; Excel/PPT writers
    must meet the same bar).
    """
    assert_rupee_present(text)
    path = tmp_path / "rupee_roundtrip.txt"
    path.write_text(text, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == text
    assert RUPEE_SIGN in path.read_text(encoding="utf-8")
    return path
