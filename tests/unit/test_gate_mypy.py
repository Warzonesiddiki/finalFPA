"""TB-016 regression: mypy strict is configured for app/engine and wired into the gate.

Docs/17 §3.1 pins ``mypy --strict`` on ``engine/`` (standard mypy elsewhere) as
gate step 3. These tests assert the config and the wiring; the remaining
tree-wide debt is pre-existing and tabulated in the TB-016 handoff for lane
distribution, never fixed by weakening this contract.
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

#: Engine files TB-016 brought to strict-clean (each verified with zero errors).
STRICT_CLEAN = [
    "app/engine/ai/usage.py",
    "app/engine/exports/ppt_pack.py",
    "app/engine/exports/excel_pack.py",
    "app/engine/store/forecast_repo.py",
    "app/engine/store/import_repo.py",
    "app/engine/calc/math.py",
]


def _pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_mypy_config_strict_on_engine():
    """[tool.mypy] pins 3.12 with a strict override covering app.engine.*."""
    mypy_cfg = _pyproject()["tool"]["mypy"]
    assert mypy_cfg["python_version"] == "3.12"
    overrides = mypy_cfg["overrides"]
    engine = [o for o in overrides if o.get("module") == "app.engine.*"]
    assert engine, "strict override for app.engine.* is required (17 S3.1)"
    assert engine[0]["strict"] is True


def test_check_wires_mypy_engine_step():
    """scripts/check.py runs mypy on app/engine after the ruff steps."""
    src = (REPO_ROOT / "scripts" / "check.py").read_text(encoding="utf-8")
    assert "python -m mypy app/engine" in src
    assert src.index('"Ruff Lint"') < src.index('"Mypy Strict (app/engine)"')


@pytest.mark.skipif(
    importlib.util.find_spec("mypy") is None,
    reason="mypy not installed in this environment",
)
def test_mypy_tool_runs_today_and_fixed_files_are_clean():
    """The wired tool executes; the TB-016-fixed files report zero errors."""
    version = subprocess.run(
        [sys.executable, "-m", "mypy", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert version.returncode == 0, version.stderr
    assert "mypy" in version.stdout.lower()

    # Full-follow form, exactly like the gate: dependency errors may appear for
    # other files, so the assertion is scoped — zero error lines may reference
    # the six fixed files.
    probe = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental", *STRICT_CLEAN],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    output = (probe.stdout + probe.stderr).replace("\\", "/")
    offenders = [
        line
        for line in output.splitlines()
        if "error:" in line
        and any(
            line.startswith(f"app/engine/{stem}")
            for stem in (
                "ai/usage.py",
                "exports/ppt_pack.py",
                "exports/excel_pack.py",
                "store/forecast_repo.py",
                "store/import_repo.py",
                "calc/math.py",
            )
        )
    ]
    assert offenders == [], "\n".join(offenders)
