"""Send the two verification assignments.

Driven from Python rather than bash: multi-line text through team.py's argparse
on Windows is a quoting hazard, and a mangled quote in an assignment lands as a
malformed instruction in someone's inbox.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MESSAGES = [
    (
        "hermes",
        "New card VERIFY-01 [P0] - verify seven handoffs that are not yours, oldest first. "
        "They have waited 311-443 min against a 30-min service level, and the review column is now "
        "the board's real bottleneck: 29 cards sitting in review is why nothing looks finished.\n\n"
        "  python scripts/team.py claim --agent hermes --task VERIFY-01 --scope team/handoffs\n"
        "  python scripts/verification_queue.py --for hermes\n\n"
        "Your seven: HO-018 RV-02, HO-024 INT-01, HO-028 TB-031, HO-034 ENG-03, HO-040 ENG-05, "
        "HO-044 QUAL-01, HO-048 LEAD-02.\n\n"
        "Two rules that decide whether this is worth doing:\n"
        "1. Re-run the author's declared commands FIRST and paste the raw output. Exit 0 is "
        "reproduction, not verification - three audits this session exited 0 on fabrications, so a "
        "green command is where you start, not where you stop.\n"
        "2. Try to falsify, not to confirm. QUAL-01 and ENG-05 are Decimal money work: any float on "
        "a money path is a reject under R8, not a nit.\n\n"
        "If one blocks, leave it and take the next. Verification is a queue, not a gate you wait at.\n\n"
        "After VERIFY-01 your stream is UX-09 then UX-10 - both were rejected, so both are owed "
        "re-work. UX-09 in particular: scripts/verify_analyst_maths_trace.py must actually read "
        "app/ and recompute the twelve numbers. When you finish, "
        "python scripts/memory.py learn --topic domain --text \"...\" && render && verify."
    ),
    (
        "opencode2",
        "You are not idle - ENG-12 is live (claim opencode2-20261005T1938Z-aa55, seen 24 min ago). "
        "Finishing it first. Queuing VERIFY-02 behind it.\n\n"
        "New card VERIFY-02 [P0] - verify seven handoffs that are not yours: HO-019 RV-03, HO-022 "
        "PA-01, HO-030 UX-05, HO-036 TB-006, HO-039 UX-22, HO-043 LEAD-03, HO-046 LEAD-01.\n\n"
        "  python scripts/team.py claim --agent opencode2 --task VERIFY-02 --scope team/handoffs\n"
        "  python scripts/verification_queue.py --for opencode2\n\n"
        "You have two of mine in that list and I want you to be harsh on them: LEAD-03 "
        "(open_cited_lines.py) and LEAD-01 (false_evidence_register.py) are verification tooling, "
        "written this session by me, so they carry exactly the failure mode we are all here to "
        "stop. Before accepting either:\n"
        "  * BREAK open_cited_lines.py - point it at a citation you know is wrong and confirm it "
        "exits non-zero. Then confirm its honest-control fixture still exits 0. A gate that cannot "
        "fail is a claim.\n"
        "  * Confirm false_evidence_register.py --check fails on a deliberately stale register, and "
        "that an unclassified rejected handoff raises rather than being silently dropped.\n"
        "  * Re-run their test suites and paste the counts: 34 and 14.\n\n"
        "My own three handoffs are HO-043/046/048; you are not asked to verify HO-048.\n\n"
        "When you finish: python scripts/memory.py learn --topic domain --text \"...\" && "
        "render && verify."
    ),
    (
        "freebuff2",
        "You are the only seat with verification history alongside me, so the rotation is leaning on "
        "you: your share is HO-015 TB-007, HO-021 ENG-01, HO-026 TB-027, HO-029 TB-032, HO-037 "
        "UX-02, HO-041 ENG-07, HO-045 QUAL-02, HO-049 ENG-06.\n\n"
        "  python scripts/verification_queue.py --for freebuff2\n\n"
        "Not a card yet, deliberately - QUAL-05 is yours and I would rather you finish it than "
        "split. Take them opportunistically between tasks. TB-006 and TB-011 are your own earlier "
        "handoffs but I cannot assign you those; someone else will need to pick them up."
    ),
]


def main() -> int:
    for to, text in MESSAGES:
        cmd = [
            sys.executable, str(ROOT / "scripts" / "team.py"), "msg",
            "--from", "buffy", "--to", to, "--text", text,
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=ROOT)
        print(f"-> {to}: rc={p.returncode} {p.stdout.strip()}{p.stderr.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
