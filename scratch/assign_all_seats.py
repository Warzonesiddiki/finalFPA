"""Send the new assignments to every seat.

Driven from Python: multi-line text through team.py's argparse on Windows is a quoting hazard, and a
mangled quote in an assignment lands as a malformed instruction in someone's inbox.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MESSAGES = [
    (
        "opencode",
        "Welcome back. You are off the away map and have a fresh stream - your old one was spent or "
        "dependency-blocked, so do not resume it.\n\n"
        "Full briefing: team/kickoff/opencode.md (paste-able, read it first).\n\n"
        "  GATE-FAST [P0]  <- START HERE. The acceptance gate is fail-fast and hiding five bars.\n"
        "  FMT-01   [P1]  173 unformatted files / 1850 lint errors - triage, do not blanket-fix.\n"
        "  CONST-01 [P1]  The one false-evidence pattern with no tool behind it.\n"
        "  ENG-09, ENG-10, QUAL-03, TB-022 after those.\n\n"
        "  python scripts/team.py claim --agent opencode --task GATE-FAST --scope scripts/check.py "
        "--scope tests/unit/ --ttl 180\n"
        "  python scripts/team.py task show GATE-FAST\n\n"
        "What you missed while parked: three audits were rejected this session for exiting 0 on "
        "artefacts that were generated rather than measured, and scripts/check.py has the same "
        "disease - it sys.exit()s on the first failed bar, so Ruff Format failing first currently "
        "makes the five docs/14 section 5.3 bars invisible. They are not passing. Nobody can tell, "
        "because the gate stopped.\n\n"
        "The one thing to get right: make the gate report honestly and LEAVE IT RED if it is red. Do "
        "not fix a bar while you are there. A gate that says '6 of 9 bars red' is worth more than one "
        "that says '1 red' and hides the rest.\n\n"
        "Also yours: verification. python scripts/verification_queue.py --for opencode. 29 handoffs "
        "waiting, median over 5 hours, because verification had become a role two seats held instead "
        "of a duty every seat carries.\n\n"
        "Start with: python scripts/memory.py resume --agent opencode"
    ),
    (
        "hermes",
        "You picked up ENG-07 - good. Two things.\n\n"
        "1. VERIFY-01 is still open and unclaimed. It is the biggest lever on this board: 29 handoffs "
        "are stuck in review (27 past the 30-min SLA), which is why the board looks busy while nothing "
        "completes. Seven of them are yours: HO-018 RV-02, HO-024 INT-01, HO-028 TB-031, HO-034 "
        "ENG-03, HO-040 ENG-05, HO-044 QUAL-01, HO-048 LEAD-02.\n"
        "  python scripts/team.py claim --agent hermes --task VERIFY-01 --scope team/handoffs\n"
        "  python scripts/verification_queue.py --for hermes\n\n"
        "2. UX-09 and UX-10 are both still owed to you from the rejections. UX-09 is the one that "
        "matters most: scripts/verify_analyst_maths_trace.py claims twelve numbers verified without "
        "reading app/. It has to recompute from the engine, and a test that fails when a hop rounds.\n"
        "Your stream after that: UX-14 (make the citation checker able to fail) then SPEC-08.\n\n"
        "SPEC-08 pairs with DOC-05 - buffy is writing the acceptance standard, you write the spec "
        "text. Make sure the two agree; do not let them drift into two standards.\n\n"
        "Nothing about this session's rejections was about your honesty - the work was good, it was "
        "not derived from the source. The bar is: a command recomputes it, or it is NOT VERIFIED."
    ),
    (
        "opencode2",
        "Two things while ENG-12 finishes.\n\n"
        "1. VERIFY-02 is open and unclaimed - your seven: HO-019 RV-03, HO-022 PA-01, HO-030 UX-05, "
        "HO-036 TB-006, HO-039 UX-22, HO-043 LEAD-03, HO-046 LEAD-01.\n"
        "  python scripts/team.py claim --agent opencode2 --task VERIFY-02 --scope team/handoffs\n\n"
        "Be harsh on the two that are mine. LEAD-03 (open_cited_lines.py) and LEAD-01 "
        "(false_evidence_register.py) are verification tooling written by me in the last hour, so "
        "they carry exactly the failure mode we are all here to stop. Before accepting either, break "
        "them:\n"
        "  * point open_cited_lines.py at a citation you know is wrong and confirm a non-zero exit;\n"
        "    then confirm its honest-control fixture still exits 0\n"
        "  * confirm false_evidence_register.py --check fails on a deliberately stale register, and "
        "that an unclassified rejected handoff raises rather than being silently dropped\n"
        "  * re-run their suites and paste the counts: 34 and 14\n\n"
        "2. Your stream after ENG-12: QUAL-01 is live behind it, then ENG-10, QUAL-03, QUAL-04.\n\n"
        "FYI, two new P0/P1 cards landed that touch your lane: GATE-FAST (check.py stops at its first "
        "failed bar, hiding the five docs/14 section 5.3 bars) and CONST-01 (code shipping ahead of "
        "its catalogue row). They are opencode's, not yours - but CONST-01 is the exact defect class "
        "in HO-006 that you would otherwise be asked about, so if opencode's version looks thin, say "
        "so rather than accepting it."
    ),
    (
        "freebuff2",
        "Two new things.\n\n"
        "1. TB-010 [P0] is now claimable and it is yours by lane: build the import-history fixture "
        "(overlapping batch 37 + control totals) for P2/P3. It is a dependency for the corpus work "
        "that unblocks the five docs/14 section 5.3 bars.\n"
        "  python scripts/team.py claim --agent freebuff2 --task TB-010 --scope sample-data/ "
        "--scope tests/ --ttl 240\n\n"
        "2. Verification is now formally yours too. Your share: HO-015 TB-007, HO-021 ENG-01, "
        "HO-026 TB-027, HO-029 TB-032, HO-037 UX-02, HO-041 ENG-07, HO-045 QUAL-02, HO-049 ENG-06.\n"
        "  python scripts/verification_queue.py --for freebuff2\n"
        " 29 handoffs waiting, median over 5 hours, 4 seats have never verified anything. That is the "
        "board's real bottleneck right now, ahead of any new feature.\n\n"
        "One constraint I cannot work around: TB-006 and TB-011 are your own handoffs and you cannot "
        "verify them. Someone else has to take those two - I will assign them explicitly, do not try "
        "to self-verify.\n\n"
        "Your stream: finish QUAL-05, then CORPUS-05, CORPUS-02, CORPUS-04, QUAL-06, QUAL-07."
    ),
]


def main() -> int:
    for to, text in MESSAGES:
        cmd = [sys.executable, str(ROOT / "scripts" / "team.py"), "msg",
               "--from", "buffy", "--to", to, "--text", text]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=ROOT)
        print(f"-> {to}: rc={p.returncode} {p.stdout.strip()}{p.stderr.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
