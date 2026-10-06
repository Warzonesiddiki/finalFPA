"""Record the verification assignments and the fail-fast finding."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENTRIES: list[list[str]] = [
    ["add", "--kind", "decision", "--ref", "team/taskboard.md",
     "--text",
     "Speed lever chosen: verification, not new feature work. 29 cards were stuck in review (27 "
     "over the 30-min SLA) which is why the board looked busy while nothing completed. Created "
     "VERIFY-01 (hermes) and VERIFY-02 (opencode2) with DISJOINT handoff sets drawn from "
     "scripts/verification_queue.py so nobody verifies the same thing twice. opencode2 was NOT idle "
     "- it had a live ENG-12 claim - so its duty was queued behind it rather than assigned."],
    ["learn", "--topic", "gate",
     "--text",
     "scripts/check.py calls sys.exit(res.returncode) on the FIRST failed bar (line 12), so it is "
     "fail-fast: a new red bar hides every bar after it. Measured 2026-10-05: Ruff Format fails "
     "first, so the five docs/14 section 5.3 bars are currently invisible. A fail-fast gate answers "
     "'which bar failed', not 'how many are red', and only the second is decision-relevant for a "
     "ship call. scripts/release_dossier.py deliberately does not short-circuit."],
    ["learn", "--topic", "gate",
     "--text",
     "scripts/ruff format --check is red across the tree: 173 files would be reformatted, and "
     "ruff check reports 1850 errors. Both pre-existing. Always scope a lint claim to your own "
     "files before reporting it, or a clean contribution gets buried in a repo-wide red."],
    ["learn", "--topic", "process",
     "--text",
     "A readiness dossier is the most dangerous document in a repo: read at ship time, written while "
     "the answer is 'not yet', and shelved unchanged for weeks. Generate it from live gate runs and "
     "give it a --check, exactly as the false-evidence register (TB-106)."],
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
