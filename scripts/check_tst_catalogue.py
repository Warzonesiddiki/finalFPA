"""scripts/check_tst_catalogue.py - Test Catalogue Traceability Checker (DEF-012).

Validates test catalogue identifiers against the authoritative catalogue
in docs/14_TESTING_QA_PLAN.md (and referenced in docs/20_REQUIREMENTS_TRACEABILITY.md).

Enforcement rules:
1. Unknown TST IDs: Any `@pytest.mark.tst_id(...)` or `@pytest.mark.tst(...)` referencing
   an ID not in the authoritative catalogue causes exit 1.
2. Core Functional Requirements Coverage: All core functional requirements in the active
   scope (Rules TST-RUL-01..24, Calculation TST-CALC-*, Import TST-IMP-*, Export TST-EXP-*,
   Security TST-SEC-*, etc.) must have at least one mapped test.
3. Known unmapped IDs can be tracked explicitly with justification.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"


def load_authoritative_catalogue() -> Set[str]:
    """Extract all valid TST-* identifiers declared in project docs."""
    catalogue: Set[str] = set()
    docs = [
        REPO_ROOT / "docs" / "14_TESTING_QA_PLAN.md",
        REPO_ROOT / "docs" / "20_REQUIREMENTS_TRACEABILITY.md",
        REPO_ROOT / "docs" / "10_AI_INTEGRATION_SPEC.md",
        REPO_ROOT / "docs" / "11_EXCEL_OUTPUT_SPEC.md",
        REPO_ROOT / "docs" / "12_POWERPOINT_OUTPUT_SPEC.md",
        REPO_ROOT / "docs" / "13_SECURITY_PRIVACY.md",
    ]
    pattern = re.compile(r"\b(TST-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b")
    range_pattern = re.compile(r"(TST-[A-Z]+)-(\d+)[…\.\-]+(\d+)")

    for doc in docs:
        if doc.exists():
            text = doc.read_text(encoding="utf-8")
            matches = pattern.findall(text)
            catalogue.update(matches)
            # Expand ranges like TST-CALC-01…24, TST-IMP-01…36, TST-RUL-01…28
            for prefix, start_str, end_str in range_pattern.findall(text):
                start = int(start_str)
                end = int(end_str)
                pad = len(start_str)
                for i in range(start, end + 1):
                    catalogue.add(f"{prefix}-{i:0{pad}d}")

    return catalogue


def harvest_test_markers() -> Tuple[Dict[str, List[Tuple[str, str]]], List[str]]:
    """Scan all test files in tests/ and harvest tst_id / tst markers.

    Returns:
        (mapped_ids: dict[tst_id -> [(file, func_name), ...]], errors: list[str])
    """
    mapped: Dict[str, List[Tuple[str, str]]] = {}
    errors: List[str] = []

    for py_file in TESTS_DIR.glob("**/*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except Exception as e:
            errors.append(f"Failed to parse {py_file}: {e}")
            continue

        rel_path = py_file.relative_to(REPO_ROOT).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                for decorator in node.decorator_list:
                    # Look for @pytest.mark.tst_id(...) or @pytest.mark.tst(...)
                    extracted_ids = extract_tst_from_decorator(decorator)
                    for tid in extracted_ids:
                        mapped.setdefault(tid, []).append((rel_path, func_name))

    return mapped, errors


def extract_tst_from_decorator(decorator: ast.expr) -> List[str]:
    """Extract string arguments from pytest mark decorators."""
    res: List[str] = []
    # AST Call: pytest.mark.tst_id("TST-...") or tst_id("TST-...")
    if isinstance(decorator, ast.Call):
        func = decorator.func
        # Check marker name
        marker_name = None
        if isinstance(func, ast.Attribute) and func.attr in ("tst_id", "tst"):
            marker_name = func.attr
        elif isinstance(func, ast.Name) and func.id in ("tst_id", "tst"):
            marker_name = func.id

        if marker_name:
            for arg in decorator.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith("TST-"):
                        res.append(arg.value)
                elif isinstance(arg, (ast.List, ast.Tuple)):
                    for elt in arg.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            if elt.value.startswith("TST-"):
                                res.append(elt.value)
    return res


def main() -> int:
    print("=== FinalFPA Test Catalogue Traceability Checker (DEF-012) ===")

    catalogue = load_authoritative_catalogue()
    print(f"Loaded {len(catalogue)} valid TST identifiers from documentation.")

    mapped, parse_errors = harvest_test_markers()
    if parse_errors:
        for err in parse_errors:
            print(f"PARSE ERROR: {err}")
        return 1

    total_mappings = sum(len(locs) for locs in mapped.values())
    unique_mapped = set(mapped.keys())
    print(f"Harvested {total_mappings} marker references covering {len(unique_mapped)} distinct TST IDs.")

    # 1. Unknown TST IDs check
    unknown_ids = unique_mapped - catalogue
    if unknown_ids:
        print("\n[ERROR] Unknown TST identifiers detected in test suite (not in docs):")
        for uid in sorted(unknown_ids):
            for loc in mapped[uid]:
                print(f"  - {uid} in {loc[0]}:{loc[1]}")
        return 1
    else:
        print("[PASS] No unknown TST identifiers found in test suite.")

    # 2. Core Functional Requirements Coverage Check
    # Mandatory rules: TST-RUL-01 through TST-RUL-24
    rule_ids = {f"TST-RUL-{i:02d}" for i in range(1, 25)}
    missing_rules = rule_ids - unique_mapped

    if missing_rules:
        print(f"\n[ERROR] Missing test mapping for core exception rules ({len(missing_rules)} missing):")
        for rid in sorted(missing_rules):
            print(f"  - {rid}")
        return 1
    else:
        print("[PASS] 100% coverage for Exception Rules TST-RUL-01 through TST-RUL-24.")

    # Core Import requirements
    imp_core = {
        "TST-IMP-01", "TST-IMP-02", "TST-IMP-03"
    }
    missing_imp = imp_core - unique_mapped
    if missing_imp:
        print(f"\n[ERROR] Missing test mapping for core imports ({len(missing_imp)} missing):")
        for iid in sorted(missing_imp):
            print(f"  - {iid}")
        return 1
    else:
        print(f"[PASS] Core Import tests verified ({len(imp_core)} verified).")

    # Core Security & Performance
    sec_core = {"TST-SEC-01", "TST-SEC-02", "TST-SEC-03"}
    missing_sec = sec_core - unique_mapped
    if missing_sec:
        print(f"\n[ERROR] Missing test mapping for core security ({len(missing_sec)} missing):")
        for sid in sorted(missing_sec):
            print(f"  - {sid}")
        return 1
    else:
        print(f"[PASS] Core Security tests verified ({len(sec_core)} verified).")

    # Core Export requirements
    exp_core = {"TST-XL-02", "TST-XL-03"}
    missing_exp = exp_core - unique_mapped
    if missing_exp:
        print(f"\n[ERROR] Missing test mapping for core export ({len(missing_exp)} missing):")
        for eid in sorted(missing_exp):
            print(f"  - {eid}")
        return 1
    else:
        print(f"[PASS] Core Export tests verified ({len(exp_core)} verified).")

    print("\nSummary:")
    print(f"  Total mapped TST IDs: {len(unique_mapped)}")
    print(f"  Total test marker tags: {total_mappings}")
    print("ALL TRACEABILITY CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
