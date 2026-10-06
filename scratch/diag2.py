"""Diagnostic v2: per-evaluator timing with immediate flush.

Builds the acceptance context once, then times each evaluator individually so a
pathological rule is identifiable. Read-only; writes only a temp project dir.
"""

from __future__ import annotations

import collections
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def log(*a):
    print(*a, flush=True)


def main() -> None:
    from app.engine.rules.acceptance import (
        build_acceptance_context,
        load_answer_key,
        run_rules,
    )
    from app.engine.rules.batch import catalog_rule_coverage

    t0 = time.perf_counter()
    raises, controls, _ = load_answer_key()
    log(f"[{time.perf_counter()-t0:7.1f}s] answer key: {len(raises)} raises, {len(controls)} controls")

    tmp = Path(tempfile.mkdtemp(prefix="fpa_diag2_"))
    t1 = time.perf_counter()
    ctx = build_acceptance_context(tmp)
    log(f"[{time.perf_counter()-t1:7.1f}s] context built: "
        f"tx={len(ctx.transactions)} batches={len(ctx.import_batches)} "
        f"budgets={len(ctx.budgets)} annual={len(ctx.annual_budgets)}")

    from app.engine.rules.batch import evaluate_all_rules_detailed
    t2 = time.perf_counter()
    result = evaluate_all_rules_detailed(ctx)
    log(f"[{time.perf_counter()-t2:7.1f}s] batch run: {len(result.findings)} findings")
    for ex in result.executions:
        log(f"    {ex.status:9s} {ex.rule_name:32s} n={ex.finding_count} "
            f"{ex.notice or ''}{ex.error_type or ''} {ex.error_message or ''}")

    coverage = catalog_rule_coverage()
    actual: dict[str, list] = collections.defaultdict(list)
    for f in result.findings:
        actual[getattr(f, "catalog_rule_id", None) or f.rule_id].append(f)

    expected = collections.defaultdict(set)
    for row in raises:
        expected[row["rule_id"]].add(row["subject_key"])
    control_keys = {row["subject_key"] for row in controls}
    produced_all = {getattr(f, "subject_key", None) for f in result.findings}

    log("")
    log("=== per-rule ===")
    for rule in sorted(expected):
        got = actual.get(rule, [])
        got_keys = [getattr(f, "subject_key", None) for f in got]
        hit = expected[rule] & set(got_keys)
        miss = expected[rule] - set(got_keys)
        extra = [k for k in got_keys if k not in expected[rule] and k not in control_keys]
        ctrl = [k for k in got_keys if k in control_keys]
        log(f"{rule} ({coverage.get(rule,'?')}) exp={len(expected[rule])} hit={len(hit)} "
            f"findings={len(got)} extras={len(extra)} ctrl={sorted(ctrl)}")
        if miss:
            log(f"    MISS: {sorted(miss)}")
        if extra:
            log(f"    EXTRA sample: {extra[:5]}")

    log("")
    log("=== expected keys produced by NO rule ===")
    for row in raises:
        if row["subject_key"] not in produced_all:
            log(f"  MISS {row['planting_id']} {row['rule_id']} {row['subject_key']}")

    log("")
    log("=== controls fired ===")
    for k in sorted(control_keys & produced_all):
        log(f"  {k}")


if __name__ == "__main__":
    main()
