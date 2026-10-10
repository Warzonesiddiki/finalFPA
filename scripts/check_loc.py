"""Line-count check script per 09_TECHNICAL_ARCHITECTURE.md §15.3 and doc 17 S3.1.

Enforces that no Python source file under app/ exceeds 500 LOC without an explicit
justification note in its header or entry in the named allowlist.
"""

import sys
from pathlib import Path

MAX_LOC = 500

# Allowlist naming explicit reasons for pre-existing domain engines >500 LOC
# if header does not contain a justification note.
ALLOWLIST_REASONS = {
    "app/api/main.py": "FastAPI REST API router and route handler definitions",
    "app/engine/errors.py": "Centralized error catalog and exception code mapping",
    "app/engine/ai/client.py": "LLM client provider, prompt assembly, and response parsing",
    "app/engine/ai/guardrails.py": "AI guardrails, input redaction, and schema validators",
    "app/engine/calc/math.py": "P&L calculation engine, variance formulas, and KPI computations",
    "app/engine/exports/excel_pack.py": "Excel pack generator implementing 7 spec sheets",
    "app/engine/exports/ppt_pack.py": "PowerPoint deck generator with template layout engine",
    "app/engine/forecast/methods.py": "Forecast methods (run-rate, trailing avg, remaining budget)",
    "app/engine/forecast/scenarios.py": "Forecast scenario evaluation and override mechanics",
    "app/engine/imports/hardening.py": "File import prescan, encoding detection, and structural checks",
    "app/engine/imports/parser.py": "Multi-format CSV/XLSX parser and row validator",
    "app/engine/imports/vendor_budget_loader.py": "Vendor budget and payroll data importer",
    "app/engine/rules/acceptance.py": "Acceptance test runner and rule verification engine",
    "app/engine/rules/rules_01_08.py": "Exception rule evaluators EXC-001 through EXC-008",
    "app/engine/rules/rules_09_16.py": "Exception rule evaluators EXC-009 through EXC-016",
    "app/engine/rules/rules_17_24.py": "Exception rule evaluators EXC-017 through EXC-024",
    "app/engine/rules/rules_catalog_001_008.py": "Rules catalog evaluator definitions for EXC-001..EXC-008",
    "app/engine/store/analytics_repo.py": "Analytics data repository and aggregation queries",
    "app/engine/store/exceptions_repo.py": "Exception register repository and persistence",
    "app/engine/store/forecast_repo.py": "Forecast version repository and line item persistence",
    "app/engine/store/import_repo.py": "Import batch repository and transaction staging",
    "app/engine/store/mapping_repo.py": "Account and cost center mapping repository",
    "app/engine/store/reports_repo.py": "Report generation repository and SQL queries",
}


def check_line_counts(app_dir: Path) -> int:
    violations = []

    for py_file in sorted(app_dir.rglob("*.py")):
        rel_path = py_file.relative_to(app_dir.parent).as_posix()
        lines = py_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        loc = len(lines)

        if loc > MAX_LOC:
            header = "\n".join(lines[:50]).lower()
            has_justification = "justification" in header

            if not has_justification and rel_path not in ALLOWLIST_REASONS:
                violations.append((rel_path, loc))

    if violations:
        print(
            f"FAILED: {len(violations)} file(s) exceed {MAX_LOC} LOC without justification header or allowlist reason:"
        )
        for path, loc in violations:
            print(f"  - {path}: {loc} LOC")
        return 1

    print(f"--> [CHECK] Line-count check PASSED (all files <= {MAX_LOC} LOC or justified)")
    return 0


if __name__ == "__main__":
    root_app = Path(__file__).parent.parent / "app"
    sys.exit(check_line_counts(root_app))
