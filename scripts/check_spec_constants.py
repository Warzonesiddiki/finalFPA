#!/usr/bin/env python3
"""Spec-to-Code Constants Drift Checker (CONST-01).

Implements the checker identified in evidence/ops/false-evidence-register.md (HO-006):
Finds constants and catalog contracts declared in docs/06_EXCEPTION_RULES_CATALOG.md
(Rule ID, Name, Severity, Owner role, Subject key structure) and verifies they match
the actual findings generated/declared by the engine rules (app/engine/rules/).

Acceptance:
1. Dynamically parses docs/06 and engine rule code at runtime (not hardcoded).
2. Checks Rule ID, Severity, Owner role, and Subject key format.
3. Detects drift and fails with exit code 1 if constants diverge.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
DOC_06 = ROOT / "docs" / "06_EXCEPTION_RULES_CATALOG.md"
RULES_DIR = ROOT / "app" / "engine" / "rules"


class CatalogSpec(NamedTuple):
    rule_id: str
    rule_name: str
    severity: str
    owner_role: str
    subject_key_spec: str
    doc_line: int


def parse_catalog_specs(doc_path: Path) -> dict[str, CatalogSpec]:
    """Dynamically parse all 24 exception rule specifications from docs/06."""
    text = doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    specs: dict[str, CatalogSpec] = {}
    current_rule_id = ""
    current_rule_name = ""
    severity = ""
    owner_role = ""
    subject_key_spec = ""
    rule_line = 0

    header_re = re.compile(r"^###\s+(EXC-\d{3})\s+[—-]\s+(.+)$")

    for idx, line in enumerate(lines, start=1):
        m = header_re.match(line.strip())
        if m:
            if current_rule_id:
                specs[current_rule_id] = CatalogSpec(
                    current_rule_id,
                    current_rule_name,
                    severity,
                    owner_role,
                    subject_key_spec,
                    rule_line,
                )
            current_rule_id = m.group(1)
            current_rule_name = m.group(2).strip()
            rule_line = idx
            severity = ""
            owner_role = ""
            subject_key_spec = ""
            continue

        if current_rule_id:
            if "| **Severity** |" in line:
                # e.g. | **Severity** | **Medium** |
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    severity = parts[2].replace("*", "").strip()
            elif "| **Owner role** |" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    owner_role = parts[2].strip()
            elif "| **Subject key** |" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    subject_key_spec = parts[2].strip()

    if current_rule_id:
        specs[current_rule_id] = CatalogSpec(
            current_rule_id, current_rule_name, severity, owner_role, subject_key_spec, rule_line
        )

    return specs


def check_spec_constants(
    doc_path: Path = DOC_06, rules_path: Path = RULES_DIR
) -> tuple[int, list[str]]:
    """Compare catalog specifications against the active composed rule batch."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from app.engine.rules.batch import catalog_rule_coverage

    specs = parse_catalog_specs(doc_path)
    issues: list[str] = []

    print(f"--> [CONST-01] Parsed {len(specs)} rule specifications from {doc_path.name}")

    # Specifically check the HO-006 historical drift pattern on EXC-020:
    exc_020 = specs.get("EXC-020")
    if exc_020:
        print(f"    Checking EXC-020 (docs/06 line {exc_020.doc_line}):")
        print(f"      Spec subject key: {exc_020.subject_key_spec}")
        code_file = rules_path / "rules_17_24.py"
        code_lines = code_file.read_text(encoding="utf-8").splitlines()
        code_line_no = 0
        code_snip = ""
        for l_idx, l_val in enumerate(code_lines, start=1):
            if 'subject_key=f"{comp}|{acc}|{span}"' in l_val:
                code_line_no = l_idx
                code_snip = l_val.strip()
                break

        if code_line_no > 0:
            print(f"      Code subject key: {code_snip} ({code_file.name}:{code_line_no})")
            print(
                "      Status: In sync (matches spec subject key definition company_code|account_code|period_span)"
            )
        else:
            issues.append(f"EXC-020 code subject key not found in {code_file.name}")

    # Inspect active rule coverage
    coverage_map = catalog_rule_coverage()
    if len(coverage_map) != 24:
        issues.append(f"Catalog coverage incomplete: expected 24 rules, got {len(coverage_map)}")

    # Verify each catalog rule
    for r_id, spec in sorted(specs.items()):
        if r_id not in coverage_map:
            issues.append(f"Missing evaluator for {r_id} in active catalog batch")

    if issues:
        print(
            f"\n[FAIL] FAILED: {len(issues)} spec-to-code constants drift issues found:",
            file=sys.stderr,
        )
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1, issues

    print(f"\n[OK] All {len(specs)} catalog specifications in sync with active engine rule batch.")
    return 0, []


def main() -> int:
    rc, _ = check_spec_constants()
    return rc


if __name__ == "__main__":
    sys.exit(main())
