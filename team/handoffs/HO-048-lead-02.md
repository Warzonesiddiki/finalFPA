# HO-048 — Verification is the bottleneck: 20 handoffs were waiting for a verifier while seats had claimable work. Design and land the fix - a verifier rotation, a verification queue with a service level, or splitting large cards so review is a small job. Acceptance: the mechanism in team/README.md plus the measured before/after wait time

## Claim
- claim: `buffy-20261005T1932Z-e0ce` · task: `LEAD-02` · author: `buffy`
- scopes: `team/README.md`, `scripts/verification_queue.py`, `tests/unit/test_verification_queue.py`, `evidence/ops/verification-bottleneck.md`
- opened: 2026-10-05T19:32:59Z · handed off: 2026-10-05T19:33:59Z

## Changed
scripts/verification_queue.py
tests/unit/test_verification_queue.py
team/README.md
evidence/ops/verification-bottleneck.md


## Verification
python -m pytest tests/unit/test_verification_queue.py -q  ->  14 passed
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


## Doc-sync
team/README.md section 6 gains 6.1 "Verification is a rotating duty, not a role (LEAD-02, TB-107)": the measured before-table, the one-sentence root cause left in place as the worked example, the four refusals, and the instruction to re-measure --stats rather than assume the fix worked.
docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-107 records LEAD-02.

## Evidence
evidence/ops/verification-bottleneck.md

## Next
Re-measure in an hour and fill in the realised wait time in team/README.md section 6.1 - that is the half of this card that cannot be finished today, and the README says so in place rather than leaving a number that will not be checked.

Two follow-ups the measurement justifies, neither a card yet:
  * make scripts/verification_queue.py --stats an input to the watchdog tick, so 92%-style concentration is detected while it is forming rather than after 26 handoffs have queued
  * the 8 oldest handoffs are all antigravity's, and antigravity is AWAY, so they can never be verified by rotation. Either the seats that covered its lane re-verify those cards, or they need a documented disposition. This is the part the rotation cannot fix by itself.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-048 --note "<what was reproduced>"`)_
