"""Submit the LEAD-02 handoff (verification rotation)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUMMARY = """LEAD-02 - verification is a rotating duty, not a role.

THE MEASUREMENT, which is worse than the card claimed

The card said "20 handoffs were waiting for a verifier while seats had claimable work". Measured:

  handoffs handed off, never verified   26
  median wait                            317 min (5.3 h)
  max wait                               417 min
  over a 30-min service level            20
  distinct verifiers                     2   - antigravity (11), buffy (1)
  load concentration                     92%
  seats that never verified anything     4 of 6 - freebuff2, hermes, opencode, opencode2

THE ROOT CAUSE IS ONE SENTENCE

team/README.md section 6 carried: "The default reviewer for money-path changes is `antigravity`".
Naming a default reviewer turned verification into a ROLE held by the longest-tenured seat rather
than a DUTY every seat carries. It then behaved like a role - the work concentrated, and when that
seat's quota ended on 2026-10-05 the function did not redistribute to the four seats that had never
verified anything. Not a discipline problem, not a throughput problem: one sentence assigning a duty
to a person, and a person running out of quota.

I left the sentence in place and documented it as the example, because deleting it would lose the
reason the rule exists.

THE MECHANISM

  python scripts/verification_queue.py              # queue, oldest first, with wait times
  python scripts/verification_queue.py --for <seat> # what this seat should verify next
  python scripts/verification_queue.py --stats      # load and concentration
  python scripts/verification_queue.py --json      # for the watchdog

Assignment is least-recently-verified first, and it refuses four things, each because breaking it
produced a real failure here:

  1. never an AWAY seat - assigning to antigravity looks like fair rotation and produces nothing
  2. never the author - team.py verify requires a different agent, so the queue must not propose
     what the tool forbids
  3. never the same two people twice running - plain oldest-first FIFO keeps the concentration
     exactly where it is; LRU on VERIFIER recency is what breaks it
  4. never a verdict with no service level - --sla (default 30 min, matching the watchdog's
     threshold) turns "late" into a number

And one exclusion that materially changed the number: a REJECTED handoff is not in the queue. It is
waiting for its author to re-do the work, not for a verifier. Counting those would have inflated the
bottleneck from 26 to 36 and hidden the real one.

Over today's backlog the rotation proposes 7 / 7 / 7 / 6 across the four active seats, against 92%
on two seats - one of which has no quota.

THE AFTER-NUMBER IS DELIBERATELY NOT CLAIMED

The mechanism landed minutes before this measurement. What is measurable now is the PROPOSED
distribution, not a realised wait time. The median only falls once seats actually drain the queue.
Re-measure with --stats and record the real figure in team/README.md section 6.1, which says so in
place. Writing "verification wait reduced from 317 min to X" before X exists would be precisely the
habit TB-105 and TB-106 exist to stop, in the same session that wrote them.

The duty itself lands in team/README.md section 6.1: verification is a duty every active seat
carries, nobody is the default reviewer, and seats drain the queue before claiming new work.
"""

CHANGED = """scripts/verification_queue.py
tests/unit/test_verification_queue.py
team/README.md
evidence/ops/verification-bottleneck.md
"""

TESTS = """python -m pytest tests/unit/test_verification_queue.py -q  ->  14 passed
ruff check scripts/verification_queue.py tests/unit/test_verification_queue.py  ->  All checks passed
mypy scripts/verification_queue.py  ->  0 errors in scripts/verification_queue.py (the 27 remaining are
        scripts/team.py's pre-existing ENG-01 baseline, now visible because this file imports it)
python scripts/verification_queue.py --stats  ->  26 waiting, median 317 min, 2 verifiers, 92% concentrated
python scripts/check_doc_integrity.py  ->  PASSED
python scripts/license_gate.py  ->  exit 0, all six checks clean
python scripts/team.py check  ->  PASS, 0 fail, 40 warn, 131 tasks, exit 0

14 tests. The refusals and the spread are what is tested, not the arithmetic:
  test_away_seat_is_never_eligible      - all three ineligibility reasons, and that a different seat is eligible
  test_never_assigns_to_the_author
  test_never_assigns_to_an_away_seat     - six handoffs, no seat may receive any
  test_no_eligible_seat_yields_no_assignment  - the falsification case: one seat wrote the only
        handoff, and the queue reports "no eligible seat" rather than proposing a self-verification
  test_rotation_spreads_across_seats    - 12 handoffs over 4 seats, max-min spread must be <= 1
  test_never_verified_seat_is_preferred - the seat that has verified nothing goes first
  test_queue_excludes_rejected_handoffs - and why: a rejection waits for its author, not a verifier
  test_sla_breach_is_marked
  test_stats_flag_concentration
  test_proposal_is_deterministic
"""

DOCSYNC = """team/README.md section 6 gains 6.1 "Verification is a rotating duty, not a role (LEAD-02, TB-107)": the measured before-table, the one-sentence root cause left in place as the worked example, the four refusals, and the instruction to re-measure --stats rather than assume the fix worked.
docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-107 records LEAD-02."""

EVIDENCE = """evidence/ops/verification-bottleneck.md"""

NEXT = """Re-measure in an hour and fill in the realised wait time in team/README.md section 6.1 - that is the half of this card that cannot be finished today, and the README says so in place rather than leaving a number that will not be checked.

Two follow-ups the measurement justifies, neither a card yet:
  * make scripts/verification_queue.py --stats an input to the watchdog tick, so 92%-style concentration is detected while it is forming rather than after 26 handoffs have queued
  * the 8 oldest handoffs are all antigravity's, and antigravity is AWAY, so they can never be verified by rotation. Either the seats that covered its lane re-verify those cards, or they need a documented disposition. This is the part the rotation cannot fix by itself."""


def main() -> int:
    cmd = [
        sys.executable, str(ROOT / "scripts" / "team.py"), "handoff",
        "--claim", "buffy-20261005T1932Z-e0ce",
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
