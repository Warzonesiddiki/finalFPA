"""Unit tests for the unified fast gate script (ENG-06)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.fast_gate import GATE_STEPS, run_fast_gate

ROOT = Path(__file__).resolve().parent.parent.parent


def test_gate_steps_definition():
    """Verify that all mandatory gate steps are declared."""
    step_names = [s.name for s in GATE_STEPS]
    assert "Unit Tests & R12 Guard" in step_names
    assert "License & Provenance Gate" in step_names
    assert "Documentation Integrity Check" in step_names
    assert "Continuity Memory Verification" in step_names


def test_fast_gate_success():
    """Verify fast gate returns 0 when all steps succeed."""
    mock_res = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_res):
        exit_code = run_fast_gate()
        assert exit_code == 0


def test_fast_gate_fails_loudly():
    """Verify fast gate halts and returns non-zero code on failure."""
    mock_res = MagicMock(returncode=1)
    with patch("subprocess.run", return_value=mock_res):
        exit_code = run_fast_gate()
        assert exit_code != 0
