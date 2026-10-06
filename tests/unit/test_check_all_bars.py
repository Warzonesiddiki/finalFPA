"""Tests for GATE-FAST: non-short-circuiting check.py behavior."""

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
