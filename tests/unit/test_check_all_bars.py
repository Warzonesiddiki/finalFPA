"""Tests for GATE-FAST: non-short-circuiting check.py behavior."""

import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import scripts.check as check_mod

ROOT = Path(__file__).resolve().parent.parent.parent


def test_check_main_returns_nonzero_when_any_bar_fails():
    """Verify that main() exits non-zero if any single bar fails."""
    # Mock run_command so the first check (Ruff Format) fails with exit code 1, but others pass
    def fake_run(cmd: str, desc: str) -> int:
        if "ruff format" in cmd:
            return 1
        return 0

    with patch.object(check_mod, "run_command", side_effect=fake_run), \
         patch.object(check_mod, "enforce_coverage_gates", return_value=0), \
         patch("sys.exit"):
        rc = check_mod.main()
        assert rc != 0, "main() must return non-zero when a bar fails"


def test_every_bar_runs_even_after_failure(capsys):
    """Verify that every bar is executed and reported, even if earlier bars fail."""
    executed_commands = []

    def tracking_run(cmd: str, desc: str) -> int:
        executed_commands.append(desc)
        # Fail the very first command
        if len(executed_commands) == 1:
            return 1
        return 0

    with patch.object(check_mod, "run_command", side_effect=tracking_run), \
         patch.object(check_mod, "enforce_coverage_gates", return_value=0):
        rc = check_mod.main()
        assert rc != 0

    captured = capsys.readouterr().out
    # Assert that all subsequent bars still ran
    assert "Ruff Lint" in executed_commands
    assert "Mypy Strict (app/engine)" in executed_commands
    assert "UI Gate Check (ESLint (ui) + TypeScript Check (tsc --noEmit))" in executed_commands
    assert "Doc Integrity and Link Check" in executed_commands
    assert "500-LOC Code-Health Check" in executed_commands
    assert "Spec-to-Code Constants Drift Check" in executed_commands
    assert "License & Provenance Gate" in executed_commands

    # Assert that summary table reported all bars
    assert "CHECK BAR" in captured
    assert "STATUS" in captured
    assert "EXIT CODE" in captured
    assert "Validation Gate FAILED" in captured


def test_check_main_returns_zero_when_all_pass():
    """Verify that main() returns 0 when all bars succeed."""
    with patch.object(check_mod, "run_command", return_value=0), \
         patch.object(check_mod, "enforce_coverage_gates", return_value=0):
        rc = check_mod.main()
        assert rc == 0


class _Cp1252Stdout:
    """Fake cp1252 console.

    ``write`` encodes eagerly, so any character cp1252 cannot represent raises
    ``UnicodeEncodeError`` exactly where the real Windows console would. This is
    the gap HO-056 blocker B named: the existing tests capture stdout into a
    StringIO, where a non-ASCII marker encodes fine, so they could not see the
    crash that killed the failure branch of ``scripts/check.py``.
    """

    encoding = "cp1252"

    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def write(self, s: str) -> int:
        data = s.encode("cp1252")  # raises on unencodable chars, by construction
        self.buffer.write(data)
        return len(s)

    def flush(self) -> None:
        pass

    def text(self) -> str:
        return self.buffer.getvalue().decode("cp1252")


def test_failure_branch_prints_its_tally_on_a_cp1252_console(monkeypatch):
    """A red gate must still report how many bars failed on a cp1252 console.

    Regression for HO-056 blocker B: the failure branch used to print a U+274C
    marker, which raised ``UnicodeEncodeError`` on the project's default Windows
    console. The bar table had printed and the exit code was still 1, but the
    process died by crash instead of ``return 1``, so the "N/15 bars failed"
    tally was never seen. Every character on the failure path must therefore be
    cp1252-encodable, and the tally must be present.
    """
    executed: list[str] = []

    def tracking_run(cmd: str, desc: str) -> int:
        executed.append(desc)
        # Fail the first bar only: this is the failure branch, not the pass one.
        return 1 if len(executed) == 1 else 0

    fake = _Cp1252Stdout()
    monkeypatch.setattr(sys, "stdout", fake)
    with (
        patch.object(check_mod, "run_command", side_effect=tracking_run),
        patch.object(check_mod, "enforce_coverage_gates", return_value=0),
    ):
        rc = check_mod.main()

    assert rc == 1, "one red bar must still return non-zero"
    out = fake.text()
    assert "Validation Gate FAILED" in out
    # The table has one row more than there are run_command bars: the NFR-014
    # split-coverage bar is appended straight from enforce_coverage_gates. The
    # tally counts TABLE ROWS, so it must be 1/16 here, not 1/15 - the off-by-one
    # that made six rows of the first GATE-FAST evidence table wrong.
    rows = [ln for ln in out.splitlines() if " | PASS " in ln or " | FAIL " in ln]
    assert len(rows) == len(executed) + 1
    assert len([ln for ln in rows if " | FAIL " in ln]) == 1
    assert f"1/{len(rows)} bars failed" in out, (
        "the tally must survive a cp1252 console, not die with the print"
    )
    for desc in executed:
        assert desc in out


def test_the_cp1252_guard_actually_rejects_the_old_marker():
    """Falsification of the guard above: it must be able to fail.

    If this stops raising, ``_Cp1252Stdout`` has become a StringIO and the test
    above is decorative - it would pass with the emoji marker put back.
    """
    fake = _Cp1252Stdout()
    with pytest.raises(UnicodeEncodeError):
        fake.write("\u274c Validation Gate FAILED: 1/16 bars failed.")
