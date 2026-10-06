"""TB-014 regression: the headless-engine boundary (docs/09 §4.1, docs/17 §3).

``app/engine/**`` may not import ``fastapi``, ``pywebview``, ``app.api``,
``app.desktop`` or ``app.jobs``. The gate runs ``lint-imports`` from
``scripts/check.py``; these tests pin the contract so it cannot be weakened
and prove the tree is clean even where import-linter is not installed.

Falsification: planting ``import fastapi`` in ``app/engine/calc/math.py``
breaks the contract as ``app.engine.calc.math -> fastapi`` (verified
2026-10-05 during TB-014; probe reverted byte-identical).
"""

import ast
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

#: The forbidden set, quoted from docs/09 §4.1 (TB-014 title repeats it verbatim).
FORBIDDEN_TOP = {"fastapi", "pywebview"}
FORBIDDEN_APP_SUBPACKAGES = {"app.api", "app.desktop", "app.jobs"}


def _contract() -> dict:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    contracts = pyproject["tool"]["importlinter"]["contracts"]
    matches = [c for c in contracts if c.get("type") == "forbidden"]
    assert matches, "no forbidden contract in [tool.importlinter]"
    return matches[0]


def test_engine_boundary_contract_matches_spec():
    """The lint-imports contract must forbid exactly the §4.1 set (never fewer)."""
    contract = _contract()
    assert "app.engine" in contract["source_modules"]
    assert set(contract["forbidden_modules"]) == (FORBIDDEN_TOP | FORBIDDEN_APP_SUBPACKAGES), (
        "weakening the forbidden set needs a spec change first (R1)"
    )


def _node_hit(path: Path, node: ast.AST) -> list[str]:
    """Forbidden-import hits for one Import/ImportFrom node (empty if clean)."""
    rel = path.relative_to(REPO_ROOT)
    if isinstance(node, ast.Import):
        return [
            f"{rel}:{node.lineno}: {a.name}"
            for a in node.names
            if a.name.split(".")[0] in FORBIDDEN_TOP or a.name in FORBIDDEN_APP_SUBPACKAGES
        ]
    if not isinstance(node, ast.ImportFrom) or node.level:
        return []  # relative imports are engine-internal by construction
    module = node.module or ""
    hits = []
    if module.split(".")[0] in FORBIDDEN_TOP or module in FORBIDDEN_APP_SUBPACKAGES:
        hits.append(f"{rel}:{node.lineno}: from {module}")
    elif module == "app":
        # `from app import api` form reconstructs to app.<name>.
        hits.extend(
            f"{rel}:{node.lineno}: from app import {a.name}"
            for a in node.names
            if f"app.{a.name.split('.')[0]}" in FORBIDDEN_APP_SUBPACKAGES
        )
    return hits


def _forbidden_imports_in_tree() -> list[str]:
    """Hermetic AST scan: every static import of the forbidden set under app/engine."""
    hits: list[str] = []
    for path in sorted((REPO_ROOT / "app" / "engine").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                hits.extend(_node_hit(path, node))
    return hits


def test_engine_tree_has_no_forbidden_imports():
    """No static import in app/engine touches the forbidden set."""
    assert _forbidden_imports_in_tree() == []


@pytest.mark.skipif(
    importlib.util.find_spec("importlinter") is None,
    reason="import-linter not installed in this environment",
)
def test_lint_imports_contract_kept():
    """The real gate tool agrees: contract KEPT on this tree (exit 0)."""
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports; raise SystemExit(lint_imports())",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "KEPT" in proc.stdout
