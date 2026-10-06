"""Submit the DOC-03 handoff (release-readiness dossier)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUMMARY = """DOC-03 - the release-readiness dossier, generated from live gate runs.

One page the owner can read to decide ship or not. Every gate carries its REAL exit status measured
at generation time; open decisions carry their blast radius; the licence posture carries the git
SHA; the known limits are numbers. No adjectives, and every line is traceable to the command printed
beside it.

    python scripts/release_dossier.py --slow   # regenerate, all nine gates
    python scripts/release_dossier.py --check   # fail if it no longer matches the machine

A hand-written readiness dossier is the most dangerous document in this repo: it is read at ship
time, it gets composed while the answer is "not yet", and it then sits on the shelf saying "not yet"
for weeks after the answer changes. So it is generated, and `--check` exists for the same reason the
false-evidence register has one (TB-106).

MEASURED RESULT - 3 of 9 gates red

  green  LICENCE 0 (8.2s) | DOC-INTEGRITY 0 (0.6s) | MEMORY 0 (0.2s) | EVID-REGISTER 0 (1.0s)
  green  TEAM-CHECK 0 (301.8s) | UNIT 0 (472.6s)
  RED    RUFF-LINT exit 1 | RUFF-FORMAT exit 1 | ACCEPTANCE exit 1

The full unit suite is green. Both ruff reds are pre-existing and repo-wide, not introduced by the
cards landing this session - every new file is ruff-clean and was checked individually.

THE FINDING THAT MATTERS MOST: THE ACCEPTANCE GATE IS FAIL-FAST

scripts/check.py line 12 calls `sys.exit(res.returncode)` on the FIRST failed bar. Measured this
pass it exits 1 at Ruff Format Check and reports nothing after it - so the five docs/14 section 5.3
bars (recall 11/32, control 1 fired, High 6/18, 422 extras, 14 zero-coverage rules) are currently
INVISIBLE. They are not passing. Nobody can tell, because the gate stopped.

A fail-fast gate answers "which bar failed first". A ship decision needs "how many are red". Those
are different questions and only the second one is decision-relevant. This generator therefore never
short-circuits, and says so in its own output: the red count above is the true number of red
conditions, not the number before the first failure.

This is the same shape as the fabricated audits in TB-104 - one uniform verdict standing in for a
population that was never examined.

ALSO MEASURED, AND WORTH THE OWNER'S ATTENTION

  * evidence/open_decisions.md declares 18 tracked open decisions and lists 2. The register does not
    deliver its own count.
  * 173 files would be reformatted by `ruff format`; `ruff check` reports 1850 errors. Both
    pre-existing. Worth noting that ruff format being red is what currently masks the five
    acceptance bars behind it.
  * 8 handoffs authored by `antigravity` are unreachable by any verification rotation: that seat is
    AWAY and cannot verify its own work.

WHAT THE DOSSIER DELIBERATELY DOES NOT DO

It reports gate exit status, not gate adequacy. A gate that exits 0 proves only that it ran, and
three audits this session exited 0 on fabrications. The dossier says so in section 7 rather than
implying full coverage, and it is explicit that skipped gates are not passing gates.
"""

CHANGED = """scripts/release_dossier.py
tests/unit/test_release_dossier.py
evidence/release-readiness-dossier.md
"""

TESTS = """python -m pytest tests/unit/test_release_dossier.py -q  ->  11 passed
python -m pytest tests/unit -q  ->  green, measured at 472.6s inside the dossier's own UNIT gate
ruff check scripts/release_dossier.py tests/unit/test_release_dossier.py  ->  All checks passed
mypy scripts/release_dossier.py  ->  0 errors in that file
python scripts/release_dossier.py --check  ->  current, exit 0
python scripts/check_doc_integrity.py  ->  exit 0

11 tests. The load-bearing one is the claim the whole document rests on:
  test_every_gate_runs_even_after_one_fails  - a red first gate must not hide the three behind it
  test_red_count_is_reported_not_just_first_failure
  test_skipped_gates_are_not_counted_as_passing
  test_the_fail_fast_trap_is_stated
  test_open_decision_count_gap_is_reported
  test_check_fails_on_a_stale_dossier
"""

DOCSYNC = """docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-108 records DOC-03 and the fail-fast finding on scripts/check.py."""

EVIDENCE = """evidence/release-readiness-dossier.md"""

NEXT = """The acceptance gate's fail-fast short-circuit is now the highest-value small fix on the board: make check.py run every bar and report each exit code, so the five docs/14 5.3 bars become visible again. That is a real card and nobody has it.

Second: 173 files unformatted and 1850 lint errors is debt that has been sitting long enough that it now hides a real gate behind it. Formatting is mechanical and can be one card with a measured before/after; the lint debt should be triaged, not blanket-fixed."""


def main() -> int:
    cmd = [
        sys.executable, str(ROOT / "scripts" / "team.py"), "handoff",
        "--claim", "buffy-20261005T2004Z-217d",
        "--summary", SUMMARY,
        "--changed", CHANGED,
        "--tests", TESTS,
        "--docsync", DOCSYNC,
        "--evidence", EVIDENCE,
        "--next", NEXT,
        "--agent", "buffy",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p.returncode


if __name__ == "__main__":
    raise SystemExit(main())
