"""Unit test for scripts/check_ui_gate.py (ENG-02)."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.check_ui_gate import check_ui_gate


def test_check_ui_gate_success(tmp_path):
    # Setup mock structure
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    baseline_file = scripts_dir / "ui_gate_baseline.json"
    baseline_file.write_text(json.dumps({
        "max_tsc_errors": 0,
        "max_eslint_errors": 10,
        "max_eslint_warnings": 5
    }))

    mock_tsc = MagicMock(returncode=0, stdout="", stderr="")
    mock_eslint_json = json.dumps([
        {"errorCount": 5, "warningCount": 2}
    ])
    mock_eslint = MagicMock(returncode=1, stdout=mock_eslint_json, stderr="")

    with patch("subprocess.run", side_effect=[mock_tsc, mock_eslint]):
        res = check_ui_gate(tmp_path)
        assert res == 0


def test_check_ui_gate_exceed_budget(tmp_path):
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()

    baseline_file = scripts_dir / "ui_gate_baseline.json"
    baseline_file.write_text(json.dumps({
        "max_tsc_errors": 0,
        "max_eslint_errors": 5,
        "max_eslint_warnings": 2
    }))

    mock_tsc = MagicMock(returncode=0, stdout="", stderr="")
    mock_eslint_json = json.dumps([
        {"errorCount": 10, "warningCount": 2}
    ])
    mock_eslint = MagicMock(returncode=1, stdout=mock_eslint_json, stderr="")

    with patch("subprocess.run", side_effect=[mock_tsc, mock_eslint]):
        res = check_ui_gate(tmp_path)
        assert res == 1
