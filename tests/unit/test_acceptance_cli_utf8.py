"""D-20 regression: cp1252 console must not mask exit 2 as exit 1.

``scripts/acceptance.py:82`` printed the markdown report with a bare
``print``. The report embeds U+20B9 (answer-key notes, rule details), which
cp1252 cannot encode, so the print raised ``UnicodeEncodeError`` and the
process exited 1 instead of the designed 2 (BLOCKED).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import scripts.acceptance as cli
from app.engine.rules.acceptance import AcceptanceReport
from tests.helpers_utf8 import (
    RUPEE_SAMPLES,
    assert_cp1252_cannot_encode,
    assert_utf8_file_roundtrip,
)


def test_rupee_is_unencodable_in_cp1252():
    assert_cp1252_cannot_encode(RUPEE_SAMPLES[0])


def test_rupee_file_output_roundtrips_utf8(tmp_path: Path):
    assert_utf8_file_roundtrip(tmp_path, RUPEE_SAMPLES[1])


class _Cp1252Stdout:
    """Fake cp1252 console: ``write`` raises on Rs., ``buffer`` accepts bytes."""

    encoding = "cp1252"

    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def write(self, s: str) -> int:
        s.encode("cp1252")  # raises UnicodeEncodeError on Rs. by construction
        return len(s)

    def flush(self) -> None:
        pass


def test_blocked_exit_code_survives_cp1252_console(monkeypatch):
    """BLOCKED stays exit 2 even when the console cannot encode Rs."""
    report = AcceptanceReport(
        verdict="BLOCKED",
        blocked_reasons=[f"GL unbalanced, variance {RUPEE_SAMPLES[0]}"],
    )
    monkeypatch.setattr(cli, "run_acceptance", lambda **kw: report)

    fake = _Cp1252Stdout()
    monkeypatch.setattr(sys, "stdout", fake)
    # Keep stderr real so the PYTHONUTF8 hint (if any) does not pollute `fake`.
    rc = cli.main([])
    assert rc == cli.EXIT_BLOCKED == 2
    assert fake.buffer.getvalue(), "nothing reached the console fallback buffer"
