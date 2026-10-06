"""Re-seat `opencode` and add the three cards the board has no owner for.

`opencode`'s quota returned, so it leaves the `away` map and gets a *fresh* stream: its old one
(ENG-01, TB-029, TB-031, TB-032, TB-022) is spent or dependency-blocked, and handing it back its
own leftovers would be a demotion dressed as continuity.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "team" / "config.json"

OPENCODE_STREAM = [
    "GATE-FAST",     # P0 gate-tooling: the acceptance gate is fail-fast and hiding five bars
    "FMT-01",        # P1: 173 unformatted files / 1850 lint errors, measured before and after
    "CONST-01",      # P1: the one false-evidence pattern with no tool behind it
    "ENG-09",        # P1: reproducible release build on a clean tree
    "ENG-10",        # P1: structured logging with a run correlation id
    "QUAL-03",       # P1: one command that runs every gate on every change
    "TB-022",        # retained from its old stream; claimable again
]

NEW_CARDS = [
    (
        "GATE-FAST", "P0", "gate-tooling",
        "Make the acceptance gate stop hiding bars. scripts/check.py line 12 calls "
        "sys.exit(res.returncode) on the FIRST failed bar, so it is fail-fast: measured today it exits "
        "1 at Ruff Format Check and reports nothing after it, which makes the five docs/14 section 5.3 "
        "bars (recall 11/32, control 1 fired, High 6/18, 422 extras, 14 zero-coverage rules) "
        "INVISIBLE. They are not passing - nobody can tell, because the gate stopped. Change it so "
        "every bar runs, every bar reports its own exit code, and the process exits non-zero if ANY "
        "bar failed. Keep the per-bar numbers exactly as they are today; change only the control flow "
        "and the reporting. Acceptance: (1) `python scripts/check.py` reports all nine bars with an "
        "exit status each, not just the first failure; (2) its exit code is non-zero when any bar is "
        "red; (3) a test that provokes a single red bar shows every OTHER bar still reported; (4) the "
        "before/after bar table is pasted into the handoff, so the five currently-invisible bars are "
        "on the record with their real numbers. Do not fix any bar while doing this - a gate that "
        "reports honestly and is still red is worth more than one that reports less and is green."
    ),
    (
        "FMT-01", "P1", "gate-tooling",
        "Clear the formatting and lint debt that is now hiding a real gate behind it. Measured today: "
        "`python -m ruff format --check app scripts tests` reports 173 files that would be reformatted, "
        "and `python -m ruff check app scripts tests` reports 1850 errors. Formatting is mechanical: "
        "apply it, then re-measure both numbers and paste the before and after. For the lint errors, "
        "do NOT blanket-fix. Triage into (a) safe auto-fix, (b) needs judgement, (c) pre-existing debt "
        "worth leaving, and record the counts per bucket with the rule you used to decide. Note that "
        "the format failure is what currently stops scripts/check.py at its first bar, so clearing it "
        "will make five more acceptance bars visible - some of which will be red, and that is the "
        "point. Acceptance: both numbers measured before and after and pasted, every bucket accounted "
        "for, and no suppression or noqa added to make a count go down."
    ),
    (
        "CONST-01", "P1", "gate-tooling",
        "Build the check the false-evidence register says does not exist. The register "
        "(evidence/ops/false-evidence-register.md) names five rejection patterns; four have a tool "
        "behind them and one does not. The `HO-006` pattern is code shipping AHEAD of its catalogue "
        "row - DEC-057 orders spec-first, but docs/06 EXC-020 still declared subject key "
        "`entity_account_pair` while the code emitted `entity|account|P..`. It was caught by a human "
        "reading two files, and nothing on this board would have caught it. Build the checker: find "
        "the constants the spec catalogue declares, find what the code actually emits, and FAIL on a "
        "mismatch. Acceptance: (1) it finds the docs/06 EXC-020 mismatch above if that is still live, "
        "or reports it already fixed, either way with the line it read on each side; (2) it is derived "
        "from the spec at run time, not from a hard-coded list; (3) it ships with a falsification test "
        "that provokes its own failure by perturbing a value; (4) it is wired into "
        "`python scripts/check.py` as a new bar. If a whole class of constants turns out not to be "
        "machine-comparable, say so with the count and name it as a limit - a coverage number is a "
        "better answer than a checker that quietly skips what it cannot read."
    ),
]


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    # 1. opencode's quota returned.
    away = cfg.get("away", {})
    if "opencode" in away:
        away.pop("opencode")
        print("removed opencode from away")
    cfg["streams"]["opencode"] = OPENCODE_STREAM
    cfg["prefer"]["opencode"] = ["gate-tooling", "engine", "rules", "infra", "tests", "cli"]
    CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"opencode stream -> {OPENCODE_STREAM}")

    # 2. The three gap cards.
    for tid, prio, lane, title in NEW_CARDS:
        cmd = [sys.executable, str(ROOT / "scripts" / "team.py"), "task", "add",
               "--title", title, "--priority", prio, "--lane", lane, "--by", "buffy", "--tb", tid]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=ROOT)
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        if p.returncode:
            return p.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
