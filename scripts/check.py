"""Clean check script per 09_TECHNICAL_ARCHITECTURE.md §15.4 and 14_TESTING_QA_PLAN.md."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import NamedTuple

# Force UTF-8 environment streams on Windows to prevent UnicodeEncodeError / cp1252 crashes
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# Exit code a bar returns when it could not produce a measurement at all. Distinct
# from 1 ("measured, and the measurement is red"): a bar that never looked cannot be
# reported as a shortfall, and a gate that conflates them is how a missing artefact
# becomes a passing number or a fabricated failure.
NOT_MEASURED = 2

STATUS_FOR = {0: "PASS", 1: "FAIL", NOT_MEASURED: "NOT MEASURED"}

_MISSING_MEASUREMENT_NOTE = (
    "    This is a missing measurement, not a coverage shortfall. Run the pytest bar "
    "(which writes .coverage) before this bar; a gate that cannot tell those two apart "
    "reports 0.00% for a corpus it never looked at."
)


class BarResult(NamedTuple):
    desc: str
    cmd: str
    exit_code: int


def run_command(cmd: str, desc: str) -> int:
    print(f"\n--> [CHECK] {desc}: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"FAILED: {desc} exited with code {res.returncode}")
    else:
        print(f"PASSED: {desc}")
    return res.returncode


def enforce_coverage_gates(domain_threshold: float = 90.0, backend_threshold: float = 75.0) -> int:
    """
    Doc 14 NFR-014:
    Coverage: Domain calculation, rules, and forecast method engines
    (calc/, rules/, forecast/methods.py, ai/) >= 90 % statements;
    storage repositories and whole backend (store/, imports/, exports/, etc.) >= 75 %.
    Thresholds enforced in scripts/check via pytest --cov with fail-under split.
    """
    import coverage

    print("--> [CHECK] Enforcing NFR-014 Split Coverage Bars...")
    try:
        cov = coverage.Coverage()
        cov.load()
        data = cov.get_data()
    except Exception as exc:
        print(f"NOT MEASURED: could not load coverage data: {exc}", file=sys.stderr)
        print(_MISSING_MEASUREMENT_NOTE)
        return NOT_MEASURED

    # Measured on this tree (coverage 7.x, Python 3.14): with no `.coverage` file at
    # all, `cov.load()` does NOT raise - it succeeds and reports zero measured files.
    # So an exception handler alone never fires, and the bar falls straight through to
    # "0/0 statements, 0.00%", which is the fabricated shortfall this bar exists to
    # stop. An empty measurement set is the missing-measurement case.
    if not data.measured_files():
        print("NOT MEASURED: coverage loaded, but it contains no measured files.", file=sys.stderr)
        print(_MISSING_MEASUREMENT_NOTE)
        return NOT_MEASURED

    backend_stmts = 0
    backend_miss = 0
    domain_stmts = 0
    domain_miss = 0

    for filepath in data.measured_files():
        norm_path = filepath.replace(chr(92), "/")
        if "/app/" not in norm_path:
            continue
        try:
            _, statements, missing, _ = cov.analysis(filepath)
        except Exception:
            continue
        n_stmts = len(statements)
        n_miss = len(missing)
        backend_stmts += n_stmts
        backend_miss += n_miss

        is_domain = any(
            k in norm_path
            for k in [
                "/app/engine/calc/",
                "/app/engine/rules/",
                "/app/engine/forecast/methods.py",
                "/app/engine/ai/",
            ]
        )
        if is_domain:
            domain_stmts += n_stmts
            domain_miss += n_miss

    backend_pct = (backend_stmts - backend_miss) / backend_stmts * 100.0 if backend_stmts else 0.0
    domain_pct = (domain_stmts - domain_miss) / domain_stmts * 100.0 if domain_stmts else 0.0

    print(
        f"    Backend Statement Coverage: {backend_stmts - backend_miss}/{backend_stmts} ({backend_pct:.2f}%) [Threshold: >={backend_threshold:.1f}%]"
    )
    print(
        f"    Domain Engines Statement Coverage: {domain_stmts - domain_miss}/{domain_stmts} ({domain_pct:.2f}%) [Threshold: >={domain_threshold:.1f}%]"
    )

    failed = False
    if backend_pct < backend_threshold:
        print(
            f"FAILED: Backend coverage {backend_pct:.2f}% is below threshold {backend_threshold:.1f}%",
            file=sys.stderr,
        )
        failed = True
    if domain_pct < domain_threshold:
        print(
            f"FAILED: Domain engines coverage {domain_pct:.2f}% is below threshold {domain_threshold:.1f}%",
            file=sys.stderr,
        )
        failed = True

    if failed:
        return 1
    print("    PASSED: NFR-014 Split Coverage Gates Met Cleanly!\n")
    return 0


def main() -> int:
    print("=== Running FP&A Month-End Copilot Validation Gate ===")

    results: list[BarResult] = []

    # 1. Python format check per doc 17 S3.1 step 1 (TB-015)
    cmd1 = "python -m ruff format --check app scripts tests"
    desc1 = "Ruff Format Check"
    rc1 = run_command(cmd1, desc1)
    results.append(BarResult(desc1, cmd1, rc1))

    # 2. Python lint per doc 17 S3.1 step 2 (TB-015)
    cmd2 = "python -m ruff check app scripts tests"
    desc2 = "Ruff Lint"
    rc2 = run_command(cmd2, desc2)
    results.append(BarResult(desc2, cmd2, rc2))

    # 3. Mypy strict on app/engine per doc 17 S3.1 step 3 (TB-016)
    cmd3 = "python -m mypy app/engine"
    desc3 = "Mypy Strict (app/engine)"
    rc3 = run_command(cmd3, desc3)
    results.append(BarResult(desc3, cmd3, rc3))

    # 4. Frontend gate per doc 17 S3.2 (TB-017 / ENG-02): eslint with the React/hooks rules
    # and tsc --noEmit. Evaluated with advisory budget (scripts/ui_gate_baseline.json).
    # Runs npm run lint --prefix ui and npm run typecheck --prefix ui via check_ui_gate.py:
    # "ESLint (ui)" and "TypeScript Check (tsc --noEmit)"
    cmd4 = "python scripts/check_ui_gate.py"
    desc4 = "UI Gate Check (ESLint (ui) + TypeScript Check (tsc --noEmit))"
    rc4 = run_command(cmd4, desc4)
    results.append(BarResult(desc4, cmd4, rc4))

    # 5. OpenAPI Contract Drift Check per doc 26
    cmd5 = "python scripts/check_contract_drift.py"
    desc5 = "OpenAPI Contract Drift Check"
    rc5 = run_command(cmd5, desc5)
    results.append(BarResult(desc5, cmd5, rc5))

    # 6. Documentation Integrity and Link Validity Check per DEF-022
    cmd6 = "python scripts/check_doc_integrity.py"
    desc6 = "Doc Integrity and Link Check"
    rc6 = run_command(cmd6, desc6)
    results.append(BarResult(desc6, cmd6, rc6))

    # 7. Test Catalogue Traceability Check per doc 14 and DEF-012
    cmd7 = "python scripts/check_tst_catalogue.py"
    desc7 = "Test Catalogue Traceability Check"
    rc7 = run_command(cmd7, desc7)
    results.append(BarResult(desc7, cmd7, rc7))

    # 8. Code health 500-LOC check per doc 09 S15.3 and doc 17 S3.1 (TB-029)
    cmd8 = "python scripts/check_loc.py"
    desc8 = "500-LOC Code-Health Check"
    rc8 = run_command(cmd8, desc8)
    results.append(BarResult(desc8, cmd8, rc8))

    # 9. Spec-to-Code Constants Drift Check per CONST-01 and DEC-057 (HO-006)
    cmd9 = "python scripts/check_spec_constants.py"
    desc9 = "Spec-to-Code Constants Drift Check"
    rc9 = run_command(cmd9, desc9)
    results.append(BarResult(desc9, cmd9, rc9))

    # 10. Engine-boundary import rule per doc 09 S4.1 (TB-014)
    cmd10 = (
        'python -c "from importlinter.cli import lint_imports; raise SystemExit(lint_imports())"'
    )
    desc10 = "Engine-Boundary Import Rule (lint-imports)"
    rc10 = run_command(cmd10, desc10)
    results.append(BarResult(desc10, cmd10, rc10))

    # 11. Python tests and coverage, excluding perf tests
    cmd11 = 'python -m pytest tests -m "not perf" --cov=app --cov-report=term --cov-report=xml:coverage.xml'
    desc11 = "Pytest Fast Suite with Coverage"
    rc11 = run_command(cmd11, desc11)
    results.append(BarResult(desc11, cmd11, rc11))

    cov_rc = enforce_coverage_gates(domain_threshold=90.0, backend_threshold=75.0)
    results.append(BarResult("NFR-014 Split Coverage Bars", "enforce_coverage_gates", cov_rc))

    # 12. Performance regression tests
    cmd12 = 'python -m pytest tests -m "perf"'
    desc12 = "Pytest Performance Suite"
    rc12 = run_command(cmd12, desc12)
    results.append(BarResult(desc12, cmd12, rc12))

    # 13. CLI doctor check
    cmd13 = "python -m app.cli doctor --json"
    desc13 = "CLI Doctor Health Check"
    rc13 = run_command(cmd13, desc13)
    results.append(BarResult(desc13, cmd13, rc13))

    # 14. UI build check
    cmd14 = 'cmd.exe /c "npm run build --prefix ui"'
    desc14 = "Vite/TypeScript UI Build Check"
    rc14 = run_command(cmd14, desc14)
    results.append(BarResult(desc14, cmd14, rc14))

    # 15. Addon 6 v2 §11 — machine gate for the reuse/license rails (final step)
    cmd15 = "python scripts/license_gate.py"
    desc15 = "License & Provenance Gate"
    rc15 = run_command(cmd15, desc15)
    results.append(BarResult(desc15, cmd15, rc15))

    # Summary reporting table
    print("\n" + "=" * 80)
    print(f"{'CHECK BAR':<52} | {'STATUS':<13} | {'EXIT CODE':<10}")
    print("-" * 80)
    failed_count = 0
    unmeasured_count = 0
    for r in results:
        status_str = STATUS_FOR.get(r.exit_code, f"FAIL({r.exit_code})")
        if r.exit_code == NOT_MEASURED:
            unmeasured_count += 1
        elif r.exit_code != 0:
            failed_count += 1
        print(f"{r.desc:<52} | {status_str:<13} | {r.exit_code:<10}")
    print("=" * 80)

    if unmeasured_count:
        # An unmeasured bar is never counted as a pass and never counted as a
        # shortfall. It gets its own line so the tally cannot be read as "everything
        # else was fine" - which is what a silent 0.00% invites.
        print(
            f"\n[NOT MEASURED] {unmeasured_count} of {len(results)} bars produced no "
            "measurement. They are neither passes nor failures; the gate is not clean."
        )
    if failed_count or unmeasured_count:
        print(
            f"\n[FAIL] Validation Gate FAILED: {failed_count}/{len(results)} bars failed"
            + (f", {unmeasured_count} not measured" if unmeasured_count else "")
            + ".\n"
        )
        return 1
    else:
        print("\n=== All Quality Gate Checks Passed Cleanly! ===\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
