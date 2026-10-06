"""Record the stale-evidence correction in the continuity layer."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENTRIES: list[list[str]] = [
    ["learn", "--topic", "trap",
     "--text",
     "A captured command result goes stale the moment a teammate edits the file it measured. "
     "evidence/ops/lead-03-citation-audit.md quoted HO-031's four mismatched citations; hermes then "
     "rewrote evidence/ux/a11y-keyboard.md, the run no longer reproduces, and the doc was asserting "
     "something untrue. Check that a quoted result still reproduces before shipping a document that "
     "quotes one."],
    ["learn", "--topic", "process",
     "--text",
     "Do not transcribe an old command output from memory into an evidence document, even when the "
     "transcription is believed accurate - that is the same fabrication TB-105 exists to catch, "
     "buried in the very file whose job is to be trustworthy. evidence/ux/a11y-keyboard.md is "
     "untracked in git, so the pre-rewrite version was unrecoverable; the honest fix was to report "
     "only the current state and cite HO-031's '### Rejected by' block for the history."],
    ["learn", "--topic", "process",
     "--text",
     "An exit code that stays non-zero after a fix is not a bug. HO-031 exits 1 both as four "
     "mismatched citations and, after the rewrite, as 'cites no file:line at all'. Rewriting a "
     "fabricated table into an honest NOT AUDITED gap is progress, not completion - the gate should "
     "keep saying so until something is actually measured."],
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
