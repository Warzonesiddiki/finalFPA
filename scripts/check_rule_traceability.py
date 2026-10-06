#!/usr/bin/env python3
"""Check end-to-end rule traceability generated directly from codebase (QUAL-02).

Parses app/engine/rules, tests/, and evidence/ dynamically to map:
Rule ID (EXC-001..EXC-024) -> Implementing Module/Evaluator -> Proving Test -> Evidence Artifact.

Outputs an objective matrix and lists any rules with missing legs as the deliverable.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "app" / "engine" / "rules"
TESTS_DIR = ROOT / "tests"
EVIDENCE_DIR = ROOT / "evidence"
EVIDENCE_OUT = ROOT / "evidence" / "rule_traceability_matrix.md"

ALL_RULE_IDS = [f"EXC-{i:03d}" for i in range(1, 25)]


@dataclass
class RuleTraceabilityRow:
    rule_id: str
    implementing_module: Optional[str]
    evaluator_func: Optional[str]
    proving_test_file: Optional[str]
    test_function: Optional[str]
    evidence_artifact: Optional[str]
    is_complete: bool
    missing_legs: List[str]


def scan_implementations(rules_dir: Path) -> Dict[str, Tuple[str, str]]:
    """Scan app/engine/rules AST to find where each EXC rule is implemented."""
    rule_map: Dict[str, Tuple[str, str]] = {}

    for py_file in sorted(rules_dir.glob("*.py")):
        if py_file.name.startswith("__"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        rel_module = py_file.relative_to(ROOT).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                fn_name = node.name
                doc = ast.get_docstring(node) or ""
                fn_code = fn_name.lower()

                # Look for EXC-xxx citations in function name, docstring, or body
                found_rules: Set[str] = set(re.findall(r"EXC-\d{3}", doc, re.IGNORECASE))
                found_rules.update(re.findall(r"EXC-\d{3}", fn_name, re.IGNORECASE))

                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Constant) and isinstance(subnode.value, str):
                        for m in re.findall(r"EXC-\d{3}", subnode.value, re.IGNORECASE):
                            found_rules.add(m.upper())

                for r_id in found_rules:
                    r_upper = r_id.upper()
                    if r_upper in ALL_RULE_IDS and r_upper not in rule_map:
                        rule_map[r_upper] = (rel_module, fn_name)

    return rule_map


def scan_tests(tests_dir: Path) -> Dict[str, Tuple[str, str]]:
    """Scan tests/ AST to find tests proving each EXC rule."""
    test_map: Dict[str, Tuple[str, str]] = {}

    for py_file in sorted(tests_dir.rglob("*.py")):
        if py_file.name.startswith("__"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        rel_test = py_file.relative_to(ROOT).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                fn_name = node.name
                doc = ast.get_docstring(node) or ""

                found_rules: Set[str] = set(re.findall(r"EXC-\d{3}", doc, re.IGNORECASE))
                found_rules.update(re.findall(r"EXC-\d{3}", fn_name, re.IGNORECASE))

                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Constant) and isinstance(subnode.value, str):
                        for m in re.findall(r"EXC-\d{3}", subnode.value, re.IGNORECASE):
                            found_rules.add(m.upper())

                for r_id in found_rules:
                    r_upper = r_id.upper()
                    if r_upper in ALL_RULE_IDS and r_upper not in test_map:
                        test_map[r_upper] = (rel_test, fn_name)

    return test_map


def scan_evidence(evidence_dir: Path) -> Dict[str, str]:
    """Scan evidence/ for markdown/json files citing each EXC rule."""
    evidence_map: Dict[str, str] = {}

    for doc_file in sorted(evidence_dir.rglob("*")):
        if not doc_file.is_file() or doc_file.suffix not in (".md", ".json", ".txt"):
            continue
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel_ev = doc_file.relative_to(ROOT).as_posix()
        for r_id in set(re.findall(r"EXC-\d{3}", content, re.IGNORECASE)):
            r_upper = r_id.upper()
            if r_upper in ALL_RULE_IDS and r_upper not in evidence_map:
                evidence_map[r_upper] = rel_ev

    return evidence_map


def build_traceability_matrix() -> List[RuleTraceabilityRow]:
    """Build the end-to-end traceability matrix for EXC-001..EXC-024."""
    impl_map = scan_implementations(RULES_DIR)
    test_map = scan_tests(TESTS_DIR)
    ev_map = scan_evidence(EVIDENCE_DIR)

    rows: List[RuleTraceabilityRow] = []

    for r_id in ALL_RULE_IDS:
        impl = impl_map.get(r_id)
        test = test_map.get(r_id)
        ev = ev_map.get(r_id)

        missing = []
        if not impl:
            missing.append("implementation")
        if not test:
            missing.append("test")
        if not ev:
            missing.append("evidence")

        row = RuleTraceabilityRow(
            rule_id=r_id,
            implementing_module=impl[0] if impl else None,
            evaluator_func=impl[1] if impl else None,
            proving_test_file=test[0] if test else None,
            test_function=test[1] if test else None,
            evidence_artifact=ev,
            is_complete=len(missing) == 0,
            missing_legs=missing,
        )
        rows.append(row)

    return rows


def generate_traceability_report(rows: List[RuleTraceabilityRow]) -> str:
    """Generate markdown report of the rule traceability matrix."""
    complete_count = sum(1 for r in rows if r.is_complete)
    incomplete_rows = [r for r in rows if not r.is_complete]

    lines = [
        "# Rule Traceability Matrix (QUAL-02)",
        "",
        "> **Task Reference:** `QUAL-02` (P0)  ",
        "> **Governing Spec:** `docs/06_EXCEPTION_RULES_CATALOG.md` & `docs/14_TESTING_QA_PLAN.md`  ",
        "> **Target Evidence Path:** `evidence/rule_traceability_matrix.md`  ",
        "> **Generated From Codebase:** Dynamically parsed from `app/engine/rules/`, `tests/`, and `evidence/`  ",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Catalog Rules:** {len(rows)} (`EXC-001` .. `EXC-024`)",
        f"- **Fully Traceable Rules:** {complete_count} of {len(rows)} ({complete_count / len(rows) * 100:.1f}%)",
        f"- **Rules with Missing Legs:** {len(incomplete_rows)} of {len(rows)}",
        "",
        "---",
        "",
        "## Incomplete Rules Deliverable (Rules with Missing Legs)",
        "",
    ]

    if incomplete_rows:
        lines.append("| Rule ID | Missing Legs | Current Implementation | Current Test | Current Evidence |")
        lines.append("|---|---|---|---|---|")
        for r in incomplete_rows:
            missing_str = ", ".join(r.missing_legs)
            impl_str = f"`{r.implementing_module}` ({r.evaluator_func})" if r.implementing_module else "*Missing*"
            test_str = f"`{r.proving_test_file}` ({r.test_function})" if r.proving_test_file else "*Missing*"
            ev_str = f"`{r.evidence_artifact}`" if r.evidence_artifact else "*Missing*"
            lines.append(f"| `{r.rule_id}` | **{missing_str}** | {impl_str} | {test_str} | {ev_str} |")
    else:
        lines.append("All 24 rules are 100% complete across implementation, test, and evidence legs.")

    lines.extend([
        "",
        "---",
        "",
        "## Complete Traceability Matrix (24 Rules)",
        "",
        "| Rule ID | Implementation Module | Proving Test | Evidence Artifact | Status |",
        "|---|---|---|---|---|",
    ])

    for r in rows:
        impl_str = f"`{r.implementing_module}`" if r.implementing_module else "—"
        test_str = f"`{r.proving_test_file}`" if r.proving_test_file else "—"
        ev_str = f"`{r.evidence_artifact}`" if r.evidence_artifact else "—"
        status_str = "✅ Complete" if r.is_complete else f"⚠️ Missing ({', '.join(r.missing_legs)})"
        lines.append(f"| `{r.rule_id}` | {impl_str} | {test_str} | {ev_str} | {status_str} |")

    lines.append("")
    lines.append("*Generated dynamically by `scripts/check_rule_traceability.py`.*")
    return "\n".join(lines) + "\n"


def main():
    rows = build_traceability_matrix()
    report = generate_traceability_report(rows)
    EVIDENCE_OUT.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_OUT.write_text(report, encoding="utf-8")
    print(f"Generated {EVIDENCE_OUT} ({sum(1 for r in rows if r.is_complete)}/24 complete).")


if __name__ == "__main__":
    main()
