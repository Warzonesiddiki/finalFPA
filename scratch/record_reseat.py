"""Record the opencode re-seating and the three new gap cards."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENTRIES: list[list[str]] = [
    ["add", "--kind", "state", "--ref", "team/kickoff/opencode.md",
     "--text",
     "opencode's quota returned mid-session. Removed from team/config.json away map, given a FRESH "
     "stream (GATE-FAST, FMT-01, CONST-01, ENG-09, ENG-10, QUAL-03, TB-022) rather than its spent "
     "one, and sent a return briefing at team/kickoff/opencode.md. opencode2 keeps its lane - the two "
     "seats are not merged."],
    ["add", "--kind", "decision",
     "--text",
     "Three gap cards created because the board had no owner for them: GATE-FAST [P0] (scripts/"
     "check.py sys.exit()s on the first failed bar, hiding the five docs/14 section 5.3 bars), "
     "FMT-01 (173 unformatted files, 1850 lint errors, triaged not blanket-fixed), CONST-01 (the "
     "HO-006 pattern - code shipping ahead of its catalogue row - which is the only false-evidence "
     "pattern with no tool behind it). All given to opencode's gate-tooling lane."],
    ["learn", "--topic", "process",
     "--text",
     "When a seat returns after being parked, give it a FRESH stream, not its old one. Its old cards "
     "are spent or reassigned, and handing them back is a demotion dressed as continuity. The "
     "briefing should also say what it missed while parked - opencode needed to know three audits "
     "had been rejected for exiting 0 on generated artefacts, because that changes how it works."],
]


def run(args: list[str]) -> int:
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "memory.py"), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p.returncode


def main() -> int:
    rc = 0
    for e in ENTRIES:
        rc |= run(e)
    print("--- render ---")
    rc |= run(["render"])
    print("--- verify ---")
    return run(["verify"]) or rc


if __name__ == "__main__":
    raise SystemExit(main())
