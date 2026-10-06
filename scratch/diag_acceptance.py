"""Diagnostic: dump actual findings per rule vs the answer key.

Read-only investigation aid for the doc 14 section 5.3 bars. Writes nothing
except a throwaway project dir under %TEMP%.
"""

from __future__ import annotations

import collections
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.engine.rules.acceptance import (  # noqa: E402
    build_acceptance_context,
    load_answer_key,
    _catalog_id,
)
from app.engine.rules.batch import (  # noqa: E402
    build_full_rule_batch,
    catalog_rule_coverage,
)


def main() -> None:
    raises, controls, all_rows = load_answer_key()
    expected = collections.defaultdict(set)
    for row in raises:
        expected[row["rule_id"]].add(row["subject_key"])
    control_keys = {row["subject_key"] for row in controls}

    tmp = Path(tempfile.mkdtemp(prefix="fpa_diag_"))
    ctx = build_acceptance_context(tmp)
    batch = build_full_rule_batch()

    coverage = catalog_rule_coverage()
    rev = {v: k for k, v in coverage.items()}

    actual: dict[str, list] = collections.defaultdict(list)
    exec_status: dict[str, str] = {}
    for ev in batch:
        name = ev.__name__
        try:
            produced = ev(ctx)
        except Exception as exc:  # noqa: BLE001
            exec_status[name] = f"ERROR {type(exc).__name__}: {exc}"
            continue
        exec_status[name] = f"ok n={len(produced)}"
        for f in produced:
            actual[_catalog_id(f)].append(f)

    print("=== per-rule ===")
    for rule in sorted(expected):
        ev_name = coverage.get(rule, "?")
        got = actual.get(rule, [])
        got_keys = [getattr(f, "subject_key", None) for f in got]
        hit = expected[rule] & set(got_keys)
        miss = expected[rule] - set(got_keys)
        extra = [k for k in got_keys if k not in expected[rule] and k not in control_keys]
        ctrl = [k for k in got_keys if k in control_keys]
        print(
            f"{rule} ev={ev_name} status={exec_status.get(ev_name, 'MISSING')} "
            f"expected={len(expected[rule])} hit={len(hit)} miss={sorted(miss)} "
            f"findings={len(got)} extras={len(extra)} ctrl_fired={sorted(ctrl)}"
        )
        if extra:
            print(f"    sample extras: {extra[:6]}")

    print()
    print("=== rules with findings but no plantings ===")
    for rule in sorted(actual):
        if rule not in expected:
            keys = [getattr(f, "subject_key", None) for f in actual[rule]]
            print(f"{rule}: {len(keys)} findings, sample={keys[:5]}")

    print()
    print("=== registered evaluators not resolving to a catalog rule ===")
    for ev in batch:
        print(f"  {ev.__name__} -> {rev.get(ev.__name__, '?')}  {exec_status.get(ev.__name__)}")

    print()
    print("=== expected keys not produced by ANY rule ===")
    produced_all = {getattr(f, "subject_key", None) for fs in actual.values() for f in fs}
    for row in raises:
        if row["subject_key"] not in produced_all:
            print(f"  MISS {row['planting_id']} {row['rule_id']} {row['subject_key']}")

    print()
    print("=== controls fired by any rule ===")
    for k in sorted(control_keys & produced_all):
        print(f"  CONTROL FIRED {k}")


if __name__ == "__main__":
    main()
