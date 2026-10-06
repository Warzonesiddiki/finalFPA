"""Submit the LEAD-01 handoff (false-evidence register)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUMMARY = """LEAD-01 - the false-evidence register.

One row per rejected handoff with the pattern it failed on, so the pattern is visible instead of
recurring. It is a generator, not a document: a hand-written register is a snapshot that starts
lying the moment somebody is rejected, so the roster is derived on every run from the handoffs that
actually carry a `### Rejected by` block, and each one's evidence is re-audited *now* by
scripts/open_cited_lines.py.

    python scripts/false_evidence_register.py            # regenerate
    python scripts/false_evidence_register.py --check    # fail if stale, write nothing

MEASURED: 10 rejected handoffs, not 3

The card said "three of this session's rejects share one root cause". Reading every rejection block
on the board gives ten rejections and five patterns:

  A-hidden-blast-radius   4  HO-003, HO-010, HO-012, HO-013
  C-literal-generator     3  HO-031, HO-033, HO-035
  B-written-outside-scope 1  HO-025
  D-checker-cannot-fail   1  HO-004
  F-spec-code-drift       1  HO-006

The largest pattern is not the one LEAD-01 was written about. Hidden blast radius - `## Changed`
declaring one file while the claim window showed four to seven - has happened four times and was
caught by hand every time.

WHY IT IS A GENERATOR, AND WHAT IT REFUSES TO DO

  * An unclassified rejection is a hard error, not a silent omission. A new pattern nobody has
    looked at is exactly what the file exists to surface, so `build()` raises rather than omitting
    it. Guarded by test_unclassified_rejection_is_a_hard_error.
  * A pattern entry for a handoff that is not rejected is a row that can never recur;
    test_every_pattern_entry_exists_on_the_board fails on one.
  * The evidence verdict is re-measured, not remembered, and says "now", not "at rejection time".
    This mattered within minutes of building it: evidence/ux/a11y-keyboard.md was rewritten by
    hermes at 00:32, mid-generation, and the register now reports HO-031 as citing no source line
    where the rejected version had 43 fabricated ones. Five agents share one checkout.
  * The citation audit is applied ONLY to the C and D patterns. Running it over a hidden-blast-
    radius rejection yields a technically true and useless verdict - "the test file cites no source
    line" - so those read `n/a - not a citation failure`.
  * This file makes no file:line claim of its own, so open_cited_lines.py reports it as citing
    nothing. That is the correct verdict: every number in it is computed, not asserted. A register
    with hand-written figures would be the failure mode it exists to record.

THE HEADLINE FINDING, RESTATED

The three C rejections are one mistake made three times in one sitting, by an author who was not
trying to deceive anyone. The failure mode is the default shape of an audit written to be read
rather than re-run: a pre-written table printed to stdout, and an id string found somewhere in
docs/, are both indistinguishable from a measurement by exit code alone.

The generalised rule, now in the register: a generator whose output does not change when its input
changes is a printer, not a generator.

WHAT WOULD HAVE CAUGHT WHAT, RANKED BY HOW MANY REJECTIONS EACH STOPS ON FIRST RUN

  1. scripts/open_cited_lines.py (TB-105, shipped) - HO-031 on the spot; reports HO-033/HO-035 as
     citing no line at all.
  2. The `## Changed` vs claim-window rule (team.py check, TB-101) - HO-010, HO-012, HO-013 and
     part of HO-025, automatically. It currently WARNs; making it FAIL is the highest-value small
     change left in this register.
  3. The claim-window scan (TB-101) - the HO-025 case.
  4. A spec-to-code constant check - DOES NOT EXIST. The HO-006 pattern (code ahead of the
     catalogue DEC-057 requires) was caught by a human reading two files. Nothing on this board
     would have caught it, which is the honest reason LEAD-01 is a register and not a solved
     problem.
"""

CHANGED = """scripts/false_evidence_register.py
tests/unit/test_false_evidence_register.py
evidence/ops/false-evidence-register.md
"""

TESTS = """python -m pytest tests/unit/test_false_evidence_register.py -q  ->  14 passed
python -m pytest tests/unit/test_open_cited_lines.py tests/unit/test_false_evidence_register.py -q  ->  48 passed
python -m ruff check scripts/open_cited_lines.py scripts/false_evidence_register.py tests/unit/test_open_cited_lines.py tests/unit/test_false_evidence_register.py  ->  All checks passed
python -m mypy scripts/open_cited_lines.py scripts/false_evidence_register.py  ->  Success, no issues in 2 source files
python scripts/false_evidence_register.py --check  ->  current, exit 0
python scripts/check_doc_integrity.py  ->  PASSED
python scripts/license_gate.py  ->  exit 0, all six checks clean

14 tests. Falsification and drift guards rather than happy paths:
  test_unclassified_rejection_is_a_hard_error     - a new unclassified rejection must fail the build
  test_check_fails_when_the_register_is_stale     - --check must catch a drifted register
  test_every_pattern_entry_exists_on_the_board    - no pattern keyed on a handoff that is not rejected
  test_every_live_rejection_is_classified          - no rejection without a pattern
  test_the_three_rejections_share_one_pattern     - the register's headline, asserted not asserted-in-prose
  test_citation_audit_is_skipped_where_it_would_be_noise
  test_build_is_deterministic
"""

DOCSYNC = """docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-106 records LEAD-01; §5.13 adds the register and the generalised rule that a generator whose output does not change when its input changes is a printer, not a generator."""

EVIDENCE = """evidence/ops/false-evidence-register.md"""

NEXT = """buffy claims LEAD-02 (verification bottleneck: 20 handoffs waiting), which should make scripts/open_cited_lines.py a required reviewer command since it converts a `review` card into an evidence check in seconds rather than by hand.

Two things the board should pick up from this register, neither a card yet:
  * make an undeclared shipped file FAIL rather than WARN in team.py check - highest-value small change, would have caught four rejections mechanically
  * a spec-to-code constant check (docs/06 EXC-020 subject key vs the code) - the one pattern in the register with no tool behind it at all"""


def main() -> int:
    cmd = [
        sys.executable, str(ROOT / "scripts" / "team.py"), "handoff",
        "--claim", "buffy-20261005T1916Z-2c19",
        "--summary", SUMMARY,
        "--changed", CHANGED,
        "--tests", TESTS,
        "--docsync", DOCSYNC,
        "--evidence", EVIDENCE,
        "--next", NEXT,
        "--agent", "buffy",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=ROOT)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
