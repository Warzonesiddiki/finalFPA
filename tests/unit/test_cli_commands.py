"""Unit tests for app.cli.main commands (TB-027)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.cli.main import main


def test_cli_doctor(capsys):
    with patch("sys.argv", ["fpa-copilot", "doctor"]):
        main()
    out = capsys.readouterr().out
    assert "HEALTHY" in out


def test_cli_doctor_json(capsys):
    with patch("sys.argv", ["fpa-copilot", "doctor", "--json"]):
        main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "healthy"


def test_cli_bva(capsys):
    with patch("sys.argv", ["fpa-copilot", "bva", "--actual", "100.50", "--budget", "80.00"]):
        main()
    out = capsys.readouterr().out
    assert "Actual: 100.50" in out
    assert "Variance: 20.50" in out


def test_cli_validate_missing_file(capsys):
    with patch("sys.argv", ["fpa-copilot", "validate", "nonexistent.csv"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "File not found" in out


def test_cli_validate_missing_file_json(capsys):
    with patch("sys.argv", ["fpa-copilot", "validate", "nonexistent.csv", "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "error"


def test_cli_validate_success(capsys, tmp_path):
    f = tmp_path / "valid.csv"
    f.write_text("Voucher,Date,Account,Amount,Description\nV1,2026-01-01,1000,100.00,Test\n")

    mock_pre = MagicMock(file_name="valid.csv", sheet_names=["Sheet1"])
    mock_check = MagicMock(check_code="CHK-001", status="pass")
    mock_batch = MagicMock(is_balanced=True, loaded_count=1, quarantined_count=0, checks=[mock_check])

    with patch("app.engine.imports.prescan_file", return_value=mock_pre), \
         patch("app.engine.imports.parse_and_validate_csv", return_value=mock_batch), \
         patch("sys.argv", ["fpa-copilot", "validate", str(f)]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "File: valid.csv" in out


def test_cli_validate_unbalanced(capsys, tmp_path):
    f = tmp_path / "unbalanced.csv"
    f.write_text("dummy")

    mock_pre = MagicMock(file_name="unbalanced.csv", sheet_names=[])
    mock_batch = MagicMock(is_balanced=False, net_imbalance=50.00)

    with patch("app.engine.imports.prescan_file", return_value=mock_pre), \
         patch("app.engine.imports.parse_and_validate_csv", return_value=mock_batch), \
         patch("sys.argv", ["fpa-copilot", "validate", str(f), "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "blocked"


def test_cli_import_missing_file(capsys):
    with patch("sys.argv", ["fpa-copilot", "import", "nonexistent.csv"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "File not found" in out


def test_cli_import_unbalanced(capsys, tmp_path):
    f = tmp_path / "unbalanced.csv"
    f.write_text("dummy")

    mock_batch = MagicMock(is_balanced=False, net_imbalance=10.00)

    with patch("app.engine.imports.parse_csv_transactions", return_value=(mock_batch, [])), \
         patch("sys.argv", ["fpa-copilot", "import", str(f)]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "NOT BALANCED" in out


def test_cli_import_success(capsys, tmp_path):
    f = tmp_path / "valid.csv"
    f.write_text("dummy")

    mock_batch = MagicMock(is_balanced=True)
    mock_rows = [MagicMock()]

    with patch("app.engine.imports.parse_csv_transactions", return_value=(mock_batch, mock_rows)), \
         patch("app.engine.store.db.DatabaseManager"), \
         patch("app.engine.store.import_repo.ImportRepository.commit_batch", return_value="BATCH-001"), \
         patch("sys.argv", ["fpa-copilot", "import", str(f), "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["batchId"] == "BATCH-001"


def test_cli_forecast_success(capsys):
    mock_ws = MagicMock(scenario="base", lines=[1, 2], totals={"fy_landing": "1000.00"})

    with patch("app.engine.store.db.DatabaseManager"), \
         patch("app.engine.store.forecast_repo.ForecastRepository.generate_forecast", return_value=mock_ws), \
         patch("sys.argv", ["fpa-copilot", "forecast", "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["scenario"] == "base"


def test_cli_forecast_error(capsys):
    with patch("app.engine.store.db.DatabaseManager"), \
         patch("app.engine.store.forecast_repo.ForecastRepository.generate_forecast", side_effect=ValueError("Invalid scenario")), \
         patch("sys.argv", ["fpa-copilot", "forecast"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    out = capsys.readouterr().out
    assert "Forecast failed" in out


def test_cli_export_xlsx(capsys, tmp_path):
    out_file = tmp_path / "pack.xlsx"
    with patch("app.engine.exports.excel_pack.create_sample_pack_data"), \
         patch("app.engine.exports.excel_pack.export_excel_pack", side_effect=lambda p, d: p.write_bytes(b"dummy")), \
         patch("sys.argv", ["fpa-copilot", "export-xlsx", "--out", str(out_file), "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["bytes"] == 5


def test_cli_export_ppt(capsys, tmp_path):
    out_file = tmp_path / "deck.pptx"
    mock_prs = MagicMock(slides=[1, 2, 3, 4, 5, 6])
    with patch("app.engine.exports.ppt_pack.generate_powerpoint_deck", return_value=mock_prs), \
         patch("sys.argv", ["fpa-copilot", "export-ppt", "--out", str(out_file)]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "PPT deck written" in out


def test_cli_migrate(capsys):
    with patch("app.engine.store.db.DatabaseManager"), \
         patch("sys.argv", ["fpa-copilot", "migrate", "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"


def test_cli_report(capsys):
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = (42,)
    mock_db = MagicMock()
    mock_db.get_duckdb_connection.return_value = mock_conn

    with patch("app.engine.store.db.DatabaseManager", return_value=mock_db), \
         patch("sys.argv", ["fpa-copilot", "report", "--json"]), pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["rowCounts"]["FactActual"] == 42
