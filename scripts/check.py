"""Clean check script per 09_TECHNICAL_ARCHITECTURE.md §15.4 and 14_TESTING_QA_PLAN.md."""

import subprocess
import sys


def run_command(cmd: str, desc: str) -> None:
    print(f"--> [CHECK] {desc}: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"FAILED: {desc} exited with code {res.returncode}")
        sys.exit(res.returncode)


def enforce_coverage_gates(domain_threshold: float = 90.0, backend_threshold: float = 75.0) -> None:
    """
    Doc 14 NFR-014:
    Coverage: Domain calculation, rules, and forecast method engines
    (calc/, rules/, forecast/methods.py, ai/) >= 90 % statements;
    storage repositories and whole backend (store/, imports/, exports/, etc.) >= 75 %.
    Thresholds enforced in scripts/check via pytest --cov with fail-under split.
    """
    import coverage

    print("--> [CHECK] Enforcing NFR-014 Split Coverage Bars...")
    cov = coverage.Coverage()
    cov.load()
    data = cov.get_data()

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

    print(f"    Backend Statement Coverage: {backend_stmts - backend_miss}/{backend_stmts} ({backend_pct:.2f}%) [Threshold: >={backend_threshold:.1f}%]")
    print(f"    Domain Engines Statement Coverage: {domain_stmts - domain_miss}/{domain_stmts} ({domain_pct:.2f}%) [Threshold: >={domain_threshold:.1f}%]")

    failed = False
    if backend_pct < backend_threshold:
        print(f"FAILED: Backend coverage {backend_pct:.2f}% is below threshold {backend_threshold:.1f}%", file=sys.stderr)
        failed = True
    if domain_pct < domain_threshold:
        print(f"FAILED: Domain engines coverage {domain_pct:.2f}% is below threshold {domain_threshold:.1f}%", file=sys.stderr)
        failed = True

    if failed:
        sys.exit(1)
    print("    PASSED: NFR-014 Split Coverage Gates Met Cleanly!\n")


def main() -> None:
    print("=== Running FP&A Month-End Copilot Validation Gate ===")

    # OpenAPI Contract Drift Check per doc 26
    run_command("python scripts/check_contract_drift.py", "OpenAPI Contract Drift Check")

    # Documentation Integrity and Link Validity Check per DEF-022
    run_command("python scripts/check_doc_integrity.py", "Doc Integrity and Link Check")

    # Test Catalogue Traceability Check per doc 14 and DEF-012
    run_command("python scripts/check_tst_catalogue.py", "Test Catalogue Traceability Check")

    # Python tests and coverage, excluding perf tests, for the fast gate.
    #
    # DOUBLE quotes, not single: this runs through cmd.exe via shell=True, and
    # cmd.exe does not strip single quotes, so `-m 'not perf'` passes the literal
    # token `perf'` to pytest and it dies with
    # "ERROR: file or directory not found: perf'" (exit 4).
    #
    # Doc 14 NFR-014:
    # "Coverage: Domain calculation, rules, and forecast method engines
    # (calc/, rules/, forecast/methods.py, ai/) >= 90 % statements;
    # storage repositories and whole backend (store/, imports/, exports/, etc.) >= 75 %"
    run_command('python -m pytest tests -m "not perf" --cov=app --cov-report=term --cov-report=xml:coverage.xml', "Pytest Fast Suite with Coverage")
    enforce_coverage_gates(domain_threshold=90.0, backend_threshold=75.0)

    # Performance regression tests, invoked explicitly so the NFR timings are
    # measured against a quiet machine (doc 14 section 13.1 keeps the full form
    # for the release/gate run).
    run_command('python -m pytest tests -m "perf"', "Pytest Performance Suite")

    # CLI doctor check
    run_command("python -m app.cli doctor --json", "CLI Doctor Health Check")

    # UI build check
    run_command("cmd.exe /c \"npm run build --prefix ui\"", "Vite/TypeScript UI Build Check")

    print("=== All Quality Gate Checks Passed Cleanly! ===")


if __name__ == "__main__":
    main()
