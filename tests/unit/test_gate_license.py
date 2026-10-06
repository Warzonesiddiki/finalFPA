"""Tests for the Addon 6 v2 licence gate's CHECK 6 (doc 15 step 4a).

The point of this file is falsification: a gate that cannot fail proves nothing, so
both directions are exercised - the real tree passes, and a tree whose notices file
has lost an adopted-source section fails naming the ADP id.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import license_gate  # noqa: E402


def test_check_6_passes_on_this_tree():
    """Every adopted source cited by a shipped `Adapted from` header reaches the payload."""
    violations: list[str] = []
    assert license_gate.check_6_payload_notices(violations, ROOT) == 0
    assert violations == []


def test_check_6_fails_when_an_adopted_notice_is_missing(tmp_path):
    """Falsification: strip the WS- sections from the notices file and the gate must
    complain about the ADP id that is cited in shipped code but no longer shipped."""
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "app" / "engine").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "build.py", root / "scripts" / "build.py")
    # a notices file that lost every adopted-source section
    (root / "THIRD_PARTY_NOTICES.md").write_text(
        "# THIRD-PARTY NOTICES\n\n## Runtime dependencies\n\nnothing here\n", encoding="utf-8"
    )
    # shipped code that still carries the provenance header
    (root / "app" / "engine" / "copy.py").write_text(
        "# Adapted from https://example.invalid/x @ deadbeef (Apache-2.0) - ADP-001 - modified\n"
        "VALUE = 1\n",
        encoding="utf-8",
    )
    sys.modules.pop("build", None)
    sys.path.insert(0, str(root / "scripts"))
    try:
        violations: list[str] = []
        assert license_gate.check_6_payload_notices(violations, root) == 1
        assert any("ADP-001" in v for v in violations), violations
    finally:
        sys.path.remove(str(root / "scripts"))
        sys.modules.pop("build", None)


def test_gate_main_runs_six_checks(capsys):
    """The gate must actually execute CHECK 6 (and the other five) end to end."""
    assert license_gate.main() == 0
    out = capsys.readouterr().out
    for n in range(1, 7):
        assert f"CHECK {n}" in out, out
