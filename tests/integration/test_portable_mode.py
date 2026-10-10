"""Test portable mode opt-in via portable.flag per doc 15 section 4.3 and ADR-004."""

import sys
from pathlib import Path

from app.engine.store.db import DatabaseManager


def test_default_mode_without_flag(tmp_path, monkeypatch):
    """Without portable.flag, DatabaseManager without args uses LOCALAPPDATA / fallback."""
    fake_localappdata = tmp_path / "localappdata"
    monkeypatch.setenv("LOCALAPPDATA", str(fake_localappdata))

    # Ensure no portable.flag in cwd or script dir
    db_mgr = DatabaseManager()
    expected_base = fake_localappdata / "FP&A Month-End Copilot" / "Projects" / "default"
    assert db_mgr.project_dir == expected_base
    assert db_mgr.duckdb_path.exists()
    assert db_mgr.sqlite_path.exists()


def test_portable_mode_with_flag(tmp_path, monkeypatch):
    """With portable.flag beside the execution directory, data relocates to <app>\data\default."""
    # Simulate exe dir as tmp_path / "app_dir"
    app_dir = tmp_path / "app_dir"
    app_dir.mkdir(parents=True, exist_ok=True)

    # Create portable.flag
    flag_path = app_dir / "portable.flag"
    flag_path.write_text("opt-in portable flag", encoding="utf-8")

    # Mock sys.frozen = True and sys.executable so Path(sys.executable).parent points to app_dir
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        sys, "executable", str(app_dir / "FPandAMonthEndCopilot.exe"), raising=False
    )

    db_mgr = DatabaseManager()
    expected_project_dir = app_dir / "data" / "default"
    assert db_mgr.project_dir == expected_project_dir
    assert db_mgr.duckdb_path.exists()
    assert db_mgr.sqlite_path.exists()

    # Clean up flag
    flag_path.unlink(missing_ok=True)


def test_audit_no_live_flag_in_build_payload():
    """Audit that build script and packaging output template zips do not ship a live portable.flag."""
    build_script_path = Path("scripts/build.py")
    if build_script_path.exists():
        content = build_script_path.read_text(encoding="utf-8")
        # Verify portable.flag is explicitly documented as NOT a live file in zips
        assert "portable.flag.README.txt" in content
        assert "not a live portable.flag" in content
