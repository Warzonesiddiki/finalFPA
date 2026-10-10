# Revert handler — `team.py release --done` refused when no handoff exists

Defects fixed by this revert handler:

1. `release --done` used to succeed on a claim that had **no handoff at all**, silently clearing the
   claim and leaving the task with no record of any reviewable deliverable. That is the inverse of the
   protocol: `--done` is the path for "work is done **and** handed off and reviewed", not "discard the
   claim and pretend nothing happened".
2. The refusal path also did not emit a usable message, so a caller could not tell whether the refusal
   was about a missing handoff or a missing review.

What changed:
- `release --done` now FAILS fast when no handoff file exists for the claim, with a message that names
  both the claim and the missing handoff path.
- The refusal message now says what is missing, not just that the release was refused.

Verification:
- `python scripts/team.py release --claim <id> --done` on a claim with no handoff now exits non-zero and
  prints the missing-handoff message.
- A claim that **has** a handoff still releases normally when the handoff is in the reviewed/done state.

Accompanying work note:
- This revert handler is part of the release-guard fix; the prior buggy behavior was recorded as a defect
  in the team's defect register and is covered by a regression test elsewhere in `tests/unit/`.
