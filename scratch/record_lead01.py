"""Record LEAD-01 into the continuity layer and render."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> int:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "memory.py"), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=ROOT)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


ENTRIES: list[list[str]] = [
    ["add", "--kind", "state", "--ref", "evidence/ops/false-evidence-register.md",
     "--text",
     "LEAD-01 done: the false-evidence register, generated not written. 10 rejected handoffs, 5 "
     "patterns. The largest pattern is hidden blast radius (4), not the literal generators (3) the "
     "card was written about. Handoff HO-046, records TB-106 and docs/33 section 5.13."],
    ["learn", "--topic", "process",
     "--text",
     "Count the failures before writing the rule about them. LEAD-01 was scoped to 'three rejects "
     "share a root cause'; reading every rejection block on the board found 10 rejections and 5 "
     "patterns, and the most frequent one (hidden blast radius, 4) was not the subject of the card."],
    ["learn", "--topic", "gate",
     "--text",
     "A register must be generated or it is a snapshot that starts lying. Three refusals keep it "
     "honest: an unclassified rejection is a hard error not a silent omission; a pattern entry "
     "keyed on a handoff that was never rejected is a row that can never recur; and a verdict where "
     "no verdict applies is worse than n/a (running a citation audit over a blast-radius rejection "
     "yields 'the test file cites no source line' - true and useless)."],
    ["learn", "--topic", "process",
     "--text",
     "Five agents share one checkout, so an 'as it stands now' measurement can change mid-task. "
     "evidence/ux/a11y-keyboard.md was rewritten by hermes while the LEAD-01 register was being "
     "built, turning HO-031 from 43 fabricated citations into zero. Any register column must say "
     "NOW, not 'at rejection time'."],
    ["learn", "--topic", "gate",
     "--text",
     "Generalised rule from TB-104: a generator whose output does not change when its input changes "
     "is a printer, not a generator."],
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
