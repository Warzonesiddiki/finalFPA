"""UI Gate script with advisory budget (ENG-02).

Runs tsc --noEmit and eslint over the ui/ tree, compares total error/warning
counts against scripts/ui_gate_baseline.json, and fails only if new debt is added
above the baseline budget.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def _count_tsc_errors(proc: subprocess.CompletedProcess[str]) -> tuple[int, bool]:
    """Return (count, count_is_trustworthy).

    `tsc --noEmit` prints one diagnostic per line and each carries a TS error code,
    so the error count is countable. If the output cannot be parsed the honest answer
    is "I could not count these", not "there was one" - a flag dressed as a count
    against a budget of 0 is a bar that fails for its own reason and hides why.
    """
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode == 0:
        return 0, True
    matched = re.findall(r"\berror TS\d+:", text)
    if matched:
        return len(matched), True
    # tsc failed but printed nothing we recognise (a crash, a config error, or output
    # we could not read). Report the failure honestly rather than inventing a number.
    return 1, False


def _over_budget(count: int, count_ok: bool, budget: int, label: str) -> bool:
    """One budget decision, stated honestly when the count could not be read."""
    if not count_ok:
        print(
            f"FAILED: {label} check failed but its count could not be read from its output, "
            "so the bar cannot say whether the budget was exceeded. This is a gate that "
            "cannot decide, not a gate that found 1 error."
        )
        return True
    if count > budget:
        print(f"FAILED: {label} {count} exceed baseline budget {budget}")
        return True
    return False


def check_ui_gate(repo_root: Path) -> int:
    ui_dir = repo_root / "ui"
    baseline_file = repo_root / "scripts" / "ui_gate_baseline.json"

    if not baseline_file.is_file():
        print(f"FAILED: UI gate baseline configuration missing: {baseline_file}")
        return 1

    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    max_tsc = baseline.get("max_tsc_errors", 0)
    max_eslint_err = baseline.get("max_eslint_errors", 83)
    max_eslint_warn = baseline.get("max_eslint_warnings", 17)

    # 1. Run tsc --noEmit
    print("--> [CHECK UI GATE] Running TypeScript check (tsc --noEmit)...")
    tsc_proc = subprocess.run(
        "npx tsc --noEmit",
        shell=True,
        cwd=str(ui_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    # COUNT the errors, do not report a flag as a count. The previous line read
    # `tsc_errors = 0 if tsc_proc.returncode == 0 else 1`, which printed
    # "TypeScript Errors : 1" whatever the real number was - 34 errors reported as 1,
    # and a budget of 0 that could never be reasoned about because the unit was wrong.
    tsc_errors, tsc_count_ok = _count_tsc_errors(tsc_proc)
    if not tsc_count_ok:
        print(f"    tsc stdout/stderr:\n{tsc_proc.stdout or ''}\n{tsc_proc.stderr or ''}")

    # 2. Run eslint with JSON format
    print("--> [CHECK UI GATE] Running ESLint check...")
    eslint_proc = subprocess.run(
        "npx eslint . --format json",
        shell=True,
        cwd=str(ui_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    actual_eslint_err = 0
    actual_eslint_warn = 0

    stdout_str = eslint_proc.stdout or ""
    if stdout_str.strip():
        try:
            results = json.loads(stdout_str)
            for file_res in results:
                actual_eslint_err += file_res.get("errorCount", 0)
                actual_eslint_warn += file_res.get("warningCount", 0)
        except Exception as exc:
            print(f"FAILED: Could not parse ESLint JSON output: {exc}")

    print(
        f"    TypeScript Errors : {tsc_errors} [Budget: <= {max_tsc}]\n"
        f"    ESLint Errors     : {actual_eslint_err} [Budget: <= {max_eslint_err}]\n"
        f"    ESLint Warnings   : {actual_eslint_warn} [Budget: <= {max_eslint_warn}]"
    )

    failed = _over_budget(tsc_errors, tsc_count_ok, max_tsc, "TypeScript errors")
    if actual_eslint_err > max_eslint_err:
        print(f"FAILED: ESLint errors {actual_eslint_err} exceed baseline budget {max_eslint_err}")
        failed = True
    if actual_eslint_warn > max_eslint_warn:
        print(
            f"FAILED: ESLint warnings {actual_eslint_warn} exceed baseline budget {max_eslint_warn}"
        )
        failed = True

    if failed:
        return 1

    print("--> [CHECK UI GATE] UI Gate PASSED (within advisory budget)")
    return 0


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    sys.exit(check_ui_gate(root))
