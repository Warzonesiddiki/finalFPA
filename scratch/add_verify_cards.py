"""Add the two verification-drain cards, with disjoint handoff sets.

The sets come from `scripts/verification_queue.py` so they are the rotation's own
proposal, not a guess. Each card names its handoffs explicitly, because "verify
something" is not a task and a verifier who picks their own targets will pick the
easy ones.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMON = (
    "Acceptance: every handoff named below carries a `### Verified by` block naming a DIFFERENT "
    "agent from its author, and each block states what was actually re-run plus the raw result. "
    "A handoff that does not reproduce is rejected with the command that failed, not softened. "
    "Start with the oldest. If one blocks you, leave it for the next verifier and move on - "
    "verification is a queue, not a gate you wait at. Close the card only when its list is empty."
)

HERMES = (
    "Drain your share of the verification backlog: verify these seven handoffs, none of them yours - "
    "RV-02/HO-018, INT-01/HO-024, TB-031/HO-028, ENG-03/HO-034, ENG-05/HO-040, QUAL-01/HO-044, "
    "LEAD-02/HO-048. They have waited 311-443 minutes against a 30-minute service level. "
    "NOTE: QUAL-01 and ENG-05 are Decimal money work - R8 means any float path is a reject, not a "
    "nit. Run the author's own declared commands first and paste the output before reading anything "
    "else; if the command exits 0, the work still has not been verified, only reproduced. "
    + COMMON
)

OPENCODE2 = (
    "Drain your share of the verification backlog: verify these seven handoffs, none of them yours - "
    "RV-03/HO-019, PA-01/HO-022, UX-05/HO-030, TB-006/HO-036, UX-22/HO-039, LEAD-03/HO-043, "
    "LEAD-01/HO-046. They have waited 41-440 minutes against a 30-minute service level. "
    "NOTE: LEAD-03 and LEAD-01 are verification tooling. Before accepting either, BREAK one - point "
    "`open_cited_lines.py` at a citation you know is wrong and watch it exit non-zero, and confirm "
    "`false_evidence_register.py --check` fails on a deliberately stale register. A checker that "
    "cannot fail is a claim, not a checker, and these two were written to be falsifiable. "
    + COMMON
)

CARDS = [
    ("VERIFY-01", "P0", "verification", HERMES),
    ("VERIFY-02", "P0", "verification", OPENCODE2),
]


def main() -> int:
    for tid, prio, lane, title in CARDS:
        cmd = [
            sys.executable, str(ROOT / "scripts" / "team.py"), "task", "add",
            "--title", title,
            "--priority", prio,
            "--lane", lane,
            "--by", "buffy",
            "--tb", tid,
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=ROOT)
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        if p.returncode:
            return p.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
