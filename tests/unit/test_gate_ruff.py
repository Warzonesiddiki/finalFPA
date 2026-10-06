"""TB-015 regression: ruff is installed, configured, and wired into the gate.

Docs/17 §3.1 pins ``ruff format`` (line length 100) as gate step 1 and
``ruff check`` as step 2. These tests assert the config and the wiring so
neither can silently disappear; the debt the tools report on the tree is
pre-existing and tabulated in the TB-015 handoff for lane distribution
(TB-029 sweep), never fixed by weakening this contract.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (repo pins >= 3.12, defensive only)
    import tomli as tomllib  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parents[2]


def _pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_ruff_config_present_and_pinned():
    """[tool.ruff] sets line-length 100 with the shared lint selection."""
    ruff = _pyproject()["tool"]["ruff"]
    assert ruff["line-length"] == 100
    assert ruff["target-version"] == "py312"
    selected = set(ruff["lint"]["select"])
    assert {"E", "F", "I", "C901", "T201", "PLR0913"} <= selected


def test_check_wires_ruff_format_and_lint():
    """scripts/check.py runs both ruff steps (format check, then lint)."""
    src = (REPO_ROOT / "scripts" / "check.py").read_text(encoding="utf-8")
    assert "ruff format --check" in src
    assert "ruff check" in src
    assert src.index("ruff format --check") < src.index('"Ruff Lint"')


@pytest.mark.skipif(
    importlib.util.find_spec("ruff") is None,
    reason="ruff not installed in this environment",
)
def test_ruff_tool_runs_today():
    """The wired tool actually executes: version reports, clean file passes."""
    version = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert version.returncode == 0, version.stderr
    assert "ruff" in version.stdout.lower()

    probe = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--output-format",
            "concise",
            "tests/unit/test_gate_ruff.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
