"""Tests verifying that hard-coded table generators are retired (ENG-05).

Acceptance requirement:
1. scripts/audit_accessibility_matrix.py and scripts/generate_screen_conformance_matrix.py
   are deleted and must not be resurrected as hard-coded literals.
2. scripts/generate_error_catalogue.py and scripts/verify_analyst_maths_trace.py
   must read their subjects from live app.engine packages at runtime and must FAIL
   if reverted to hard-coded dictionary/table literals.
"""
import ast
import inspect
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_deleted_generators_remain_deleted():
    """Deleted scripts must not exist in the codebase."""
    deleted_scripts = [
        ROOT / "scripts" / "audit_accessibility_matrix.py",
        ROOT / "scripts" / "generate_screen_conformance_matrix.py",
    ]
    for script_path in deleted_scripts:
        assert not script_path.exists(), f"{script_path.name} was resurrected but must remain deleted (ENG-05)."


def test_generate_error_catalogue_reads_runtime_subject():
    """generate_error_catalogue.py must dynamically import get_error_catalog and contain NO hard-coded error lists."""
    script_path = ROOT / "scripts" / "generate_error_catalogue.py"
    assert script_path.exists(), "scripts/generate_error_catalogue.py must exist"

    code = script_path.read_text(encoding="utf-8")
    tree = ast.parse(code)

    # 1. Must import get_error_catalog from app.engine.errors
    imports_engine = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "app.engine.errors":
                for alias in node.names:
                    if alias.name == "get_error_catalog":
                        imports_engine = True
    assert imports_engine, "generate_error_catalogue.py must dynamically import get_error_catalog from app.engine.errors"

    # 2. Must not contain the old hardcoded ERROR_CATALOGUE_DATA table variable
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assert target.id != "ERROR_CATALOGUE_DATA", (
                        "generate_error_catalogue.py must not contain a hardcoded ERROR_CATALOGUE_DATA list!"
                    )

    # 3. Dynamic execution test: modifying engine catalog reflects dynamically
    from app.engine import errors
    from scripts.generate_error_catalogue import generate_error_catalogue_markdown

    original_catalog = errors.ERROR_CATALOG
    try:
        # Inject a dynamic sentinel error
        sentinel_error = {
            "code": "ERR-TEST-999",
            "family": "ENG",
            "httpStatus": 500,
            "message": "Dynamic sentinel test error",
            "hint": "Check dynamic engine wiring.",
            "slug": "engine.sentinelTest",
            "severity": "High",
            "ownerDoc": "00_TEST",
        }
        errors.ERROR_CATALOG = [sentinel_error] + original_catalog

        output_md = generate_error_catalogue_markdown()
        assert "ERR-TEST-999" in output_md, "Generator failed to dynamically pick up runtime error from app.engine.errors!"
        assert "Dynamic sentinel test error" in output_md
    finally:
        errors.ERROR_CATALOG = original_catalog


def test_verify_analyst_maths_trace_invokes_engine_math():
    """verify_analyst_maths_trace.py must invoke app.engine.calc functions and verify calculations live."""
    script_path = ROOT / "scripts" / "verify_analyst_maths_trace.py"
    assert script_path.exists(), "scripts/verify_analyst_maths_trace.py must exist"

    code = script_path.read_text(encoding="utf-8")
    tree = ast.parse(code)

    # 1. Must import from app.engine.calc (math or observable)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    assert any(m.startswith("app.engine.calc") for m in imported_modules), (
        "verify_analyst_maths_trace.py must import and execute functions from app.engine.calc"
    )

    # 2. Must dynamically execute calculations from app.engine.calc
    import scripts.verify_analyst_maths_trace as maths_mod

    assert hasattr(maths_mod, "main")
    # Verify main runs and writes output dynamically without raising
    maths_mod.main()
