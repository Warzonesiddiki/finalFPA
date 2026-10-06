"""Record LEAD-03 into the continuity layer and render."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(args: list[str]) -> int:
    proc = subprocess.run([PY, str(ROOT / "scripts" / "memory.py"), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=ROOT)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


ENTRIES: list[list[str]] = [
    ["add", "--kind", "state", "--ref", "evidence/ops/lead-03-citation-audit.md",
     "--text",
     "LEAD-03 done: scripts/open_cited_lines.py opens the file:line citations a report makes, "
     "prints the real line, and fails when a report claims something absent from the line it cites. "
     "34 tests; exit 0 only when every sampled citation resolved and every claim token was present. "
     "Handoff HO-043."],
    ["learn", "--topic", "trap",
     "--text",
     "A file:line citation is not evidence until the line is opened. Measured on HO-031: all four "
     "cited files real, all four line numbers in range, all four lines carrying none of the claimed "
     "attributes. Existence plus range is not a check."],
    ["learn", "--topic", "trap",
     "--text",
     "aria- occurs 0 times across all 60 .tsx files in ui/src, yet the UX-08 matrix marks 42 screens "
     "Conforming with role/aria-label/aria-live attributes. A uniform verdict across a whole "
     "population is the signature of not looking, not of a clean result."],
    ["learn", "--topic", "gate",
     "--text",
     "A gate that can only fail proves nothing. Ship one fixture that must pass and one that must "
     "fail with the same shape; guard both with a test. Also: a row whose line was never opened must "
     "never print 'all present' - absence of evidence read as evidence is a false green."],
    ["learn", "--topic", "process",
     "--text",
     "Run a new checker over its own output before shipping it. Two defects in scripts/open_cited_lines.py "
     "surfaced only that way: fenced code blocks were scanned, so a document quoting an audit failed its "
     "own tool; and two claims on one report line each got checked against both citations."],
    ["learn", "--topic", "windows",
     "--text",
     "Windows console is cp1252: reconfigure sys.stdout/sys.stderr to utf-8 in any CLI that prints "
     "markdown or non-ASCII. Use ASCII markers in output rather than arrows or ellipsis."],
]


def main() -> int:
    rc = 0
    for entry in ENTRIES:
        rc |= run(entry)
    print("--- render ---")
    rc |= run(["render"])
    print("--- verify ---")
    return run(["verify"]) or rc


if __name__ == "__main__":
    raise SystemExit(main())
