"""DEF-024 mutation harness.

Each mutation reinstates a specific WRONG implementation of
`app/engine/rules/batch.py` and asserts that `tests/unit/test_def024_rule_containment.py`
FAILS. A mutation that leaves the suite green means the tests cannot see that
defect, which makes them decorative rather than load-bearing.

Two rules this harness obeys, both learned the hard way:

  1. It asserts the mutation actually changed the file before testing it. A
     mutation that silently fails to apply reports the guard is strong when it
     proved nothing -- the same false confidence as an unrun test.
  2. It restores the target in a `finally` and verifies the restore is
     byte-identical at the end. Never run two instances of this concurrently
     against the same checkout: they will race and leave a mutation in place.

Usage:  python tools/mut024.py
"""

import os
import pathlib
import re
import subprocess
import sys

TARGET = pathlib.Path("app/engine/rules/batch.py")
TESTS = ["tests/unit/test_def024_rule_containment.py"]
LOCK = pathlib.Path("tools/.mut024.lock")


def run_tests():
    # -B / PYTHONDONTWRITEBYTECODE stop a stale .pyc from masking a mutation.
    r = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", *TESTS, "-p", "no:cacheprovider",
         "-q", "--tb=no"],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    out = r.stdout + r.stderr
    failed = re.findall(r"(\d+) failed", out)
    if failed:
        return r.returncode, f"exit={r.returncode} {failed[-1]} failed"
    passed = re.findall(r"(\d+) passed", out)
    if passed:
        return r.returncode, f"exit={r.returncode} {passed[-1]} passed"
    # A mutation that breaks collection still means the tests cannot pass on this
    # code, but it must be labelled honestly rather than as "0 failed".
    return r.returncode, f"exit={r.returncode} NO-TEST-OUTPUT"


def mutations(orig):
    """(label, mutated_source, expect_tests_to_fail) triples."""

    # M2: reinstate the original unguarded loop -- one crash destroys the batch.
    m2 = re.sub(
        r"        try:\n            produced = evaluator\(context\)\n"
        r"        except Exception as exc:.*?\n            continue\n",
        "        produced = evaluator(context)\n",
        orig, flags=re.S,
    )

    # M3: the FAKE FIX. Containment retained, failure swallowed with no record.
    # This is the most dangerous shape: every healthy rule still returns its
    # findings, so the caller sees what looks like a complete run.
    m3 = re.sub(
        r"        except Exception as exc:  # noqa: BLE001.*?\n            continue\n",
        "        except Exception:  # FAKE FIX: swallowed\n            continue\n",
        orig, flags=re.S,
    )

    # M4: containment intact and a record present, but the exception detail is
    # dropped -- the run summary says "failed" without saying why.
    m4 = orig.replace(
        "                    error_type=type(exc).__name__,\n"
        "                    error_message=str(exc),\n",
        "", 1,
    )

    # M5: doc-06 §2.9 disable path neutralised, so a rule with an unmet
    # required dependency gets approximated instead of disabled.
    m5 = orig.replace(
        "        missing = _missing_required_dependency(evaluator, context)",
        "        missing = None  # dependency check disabled", 1,
    )

    # M6: the findings-only helper re-implemented as its own fragile loop,
    # bypassing the isolation path entirely.
    m6 = orig.replace(
        "    return evaluate_all_rules_detailed(context).findings",
        "    out = []\n"
        "    for ev in build_full_rule_batch():\n"
        "        out.extend(ev(context))\n"
        "    return out",
        1,
    )

    return [
        ("M2 original unguarded loop", m2, True),
        ("M3 fake fix: swallow, no record", m3, True),
        ("M4 record present, detail dropped", m4, True),
        ("M5 doc-06 2.9 disable neutralised", m5, True),
        ("M6 helper bypasses isolation", m6, True),
    ]


def main():
    if LOCK.exists():
        sys.exit(f"refusing to run: {LOCK} exists -- another instance is active")
    LOCK.write_text("active")

    orig = TARGET.read_text(encoding="utf-8")
    rows = []
    try:
        code, detail = run_tests()
        rows.append(("M1 baseline unmutated", detail,
                     "OK" if code == 0 else "UNEXPECTED"))

        for label, mutated, expect_fail in mutations(orig):
            if mutated == orig:
                rows.append((label, "MUTATION DID NOT APPLY", "BROKEN"))
                continue
            TARGET.write_text(mutated, encoding="utf-8")
            try:
                code, detail = run_tests()
            finally:
                TARGET.write_text(orig, encoding="utf-8")
            ok = (code != 0) == expect_fail
            rows.append((label, detail, "OK" if ok else "NOT CAUGHT"))
    finally:
        LOCK.unlink(missing_ok=True)

    restored = TARGET.read_text(encoding="utf-8") == orig
    w = max(len(r[0]) for r in rows)
    print("=" * (w + 30))
    for label, detail, verdict in rows:
        print(f"  {label:<{w}}  {detail:<14} {verdict}")
    print("=" * (w + 30))
    print(f"  restored byte-identical: {restored}")
    if not all(r[2] == "OK" for r in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
