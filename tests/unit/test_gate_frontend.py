"""TB-017 regression: eslint + tsc --noEmit run in the gate and today confirm they run.

Docs/17 §3.2 pins ESLint with the React/hooks rules and ``tsc --noEmit`` in
``scripts/check``. These tests assert the npm scripts, the flat config, the
gate wiring, and that both tools execute (tsc is green on the tree today;
eslint reports pre-existing debt tabulated in the TB-017 handoff, so the live
eslint assertion only proves the tool runs — never a clean tree).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = REPO_ROOT / "ui"


def _ui_scripts() -> dict:
    return json.loads((UI_ROOT / "package.json").read_text(encoding="utf-8"))["scripts"]


def test_ui_lint_and_typecheck_scripts_exist():
    """ui/package.json exposes lint (eslint .) and typecheck (tsc --noEmit)."""
    scripts = _ui_scripts()
    assert scripts["lint"] == "eslint ."
    assert scripts["typecheck"] == "tsc --noEmit"


def test_eslint_flat_config_bans_any():
    """eslint.config.js exists with the React/hooks plugins and the any ban."""
    src = (UI_ROOT / "eslint.config.js").read_text(encoding="utf-8")
    assert "react-hooks" in src
    assert "react-refresh" in src
    assert "@typescript-eslint/no-explicit-any" in src


def test_check_wires_eslint_and_tsc_after_mypy():
    """scripts/check.py runs the UI lint and typecheck steps."""
    src = (REPO_ROOT / "scripts" / "check.py").read_text(encoding="utf-8")
    assert "npm run lint --prefix ui" in src
    assert "npm run typecheck --prefix ui" in src
    assert src.index('"Mypy Strict (app/engine)"') < src.index('"ESLint (ui)"')


def _node_bin(name: str) -> Path:
    # On Windows the extensionless shims are not executable; prefer .cmd.
    ordered = [f"{name}.cmd", name] if sys.platform == "win32" else [name, f"{name}.cmd"]
    for leaf in ordered:
        candidate = UI_ROOT / "node_modules" / ".bin" / leaf
        if candidate.exists():
            return candidate
    pytest.skip(f"{name} not installed under ui/node_modules")


def test_eslint_tool_runs_today():
    """eslint executes against the tree (exit code only proves it ran)."""
    eslint = _node_bin("eslint")
    proc = subprocess.run(
        [str(eslint), "--version"],
        cwd=UI_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().startswith("v"), proc.stdout

    probe = subprocess.run(
        [str(eslint), "src/api/types.ts"],
        cwd=UI_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    combined = probe.stdout + probe.stderr
    assert "no-explicit-any" in combined or "problem" in combined, (
        "eslint must actually analyse files, not pass vacuously"
    )


def test_tsc_tool_runs_today():
    """tsc --noEmit executes; today it is green on the tree."""
    tsc = _node_bin("tsc")
    if shutil.which("node") is None:
        pytest.skip("node is not on PATH")
    proc = subprocess.run(
        [str(tsc), "--noEmit", "-p", "tsconfig.json"],
        cwd=UI_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
