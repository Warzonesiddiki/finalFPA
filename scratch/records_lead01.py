"""Record LEAD-01 in CHANGELOG.md and STATE.md (leader-only records)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHANGELOG = (
    "- **The false-evidence register: one row per rejected handoff, generated so it cannot go stale "
    "(`scripts/false_evidence_register.py`, `TB-106`/`LEAD-01`):** `TB-104` rejected three audits and "
    "asked for a register so the pattern would be visible instead of recurring. Reading every "
    "rejection block on the board found **10 rejected handoffs and 5 patterns** - and the largest "
    "pattern was *not* the one the card was written about: **hidden blast radius** (`## Changed` "
    "listing one file while the claim window showed four to seven) occurred **4 times** and was "
    "caught by hand every time, against 3 for the literal generators. It is a generator rather than "
    "a document because a hand-written register is a snapshot that starts lying the moment somebody "
    "is rejected: the roster is derived from the handoffs that actually carry a `### Rejected by` "
    "block, each one's evidence is re-audited at generation time by `scripts/open_cited_lines.py`, "
    "and `--check` fails if it has drifted. Three deliberate refusals, each covered by a test - an "
    "unclassified rejection is a hard error rather than a silent omission; a pattern entry keyed on a "
    "handoff that was never rejected is a row that can never recur; and a verdict where none applies "
    "is worse than `n/a`, since running a citation audit over a blast-radius rejection yields the "
    "technically true and entirely useless \"the test file cites no source line\". The generalised "
    "rule it records: **a generator whose output does not change when its input changes is a "
    "printer, not a generator**. 14 tests.\n"
)

STATE_TASK = (
    "FALSE-EVIDENCE REGISTER LANDED (TB-106 / LEAD-01): one row per rejected handoff with the "
    "pattern it failed on - generated, not written, because a hand-written register is a snapshot "
    "that starts lying the moment somebody is rejected. scripts/false_evidence_register.py derives "
    "the roster from the handoffs that actually carry a '### Rejected by' block, re-audits each "
    "one's evidence NOW via scripts/open_cited_lines.py, and --check fails if it has drifted. "
    "MEASURED: 10 rejected handoffs, 5 patterns - and the largest is NOT the one the card was "
    "written about. Hidden blast radius ('## Changed' listing 1 file while the claim window showed "
    "4-7) occurred 4 TIMES (HO-003/010/012/013) and was caught by hand every time; literal "
    "generators 3 (HO-031/033/035); written-outside-scope, checker-cannot-fail and spec-code-drift "
    "1 each. THREE DELIBERATE REFUSALS: an unclassified rejection is a HARD ERROR not a silent "
    "omission; a pattern entry keyed on a handoff that was never rejected is a row that can never "
    "recur; and a verdict where none applies is worse than n/a - a citation audit over a "
    "blast-radius rejection yields 'the test file cites no source line', true and useless. Five "
    "agents share one checkout, which mattered within minutes: hermes rewrote "
    "evidence/ux/a11y-keyboard.md at 00:32 mid-generation, so the register now reports HO-031 as "
    "citing no source line where the rejected version had 43 fabricated ones - every column says "
    "NOW, not 'at rejection time'. Rule recorded: a generator whose output does not change when its "
    "input changes is a printer, not a generator. RANKED BY WHAT WOULD HAVE CAUGHT THE MOST: "
    "open_cited_lines.py (shipped) stops HO-031 outright; the '## Changed' vs claim-window rule "
    "(shipped, TB-101) stops 4 but currently only WARNs - making it FAIL is the highest-value "
    "small change left; a spec-to-code constant check for HO-006 DOES NOT EXIST and was caught by a "
    "human reading two files, which is the honest reason LEAD-01 is a register and not a solved "
    "problem. docs/33 gains TB-106 and §5.13. "
)

STATE_GATE = (
    "- LEAD-01: `python -m pytest tests/unit/test_false_evidence_register.py -q` -> 14 passed; "
    "`python -m pytest tests/unit/test_open_cited_lines.py "
    "tests/unit/test_false_evidence_register.py -q` -> 48 passed, exit 0; `ruff check` on all four "
    "new files -> All checks passed; `mypy scripts/open_cited_lines.py "
    "scripts/false_evidence_register.py` -> Success, 0 errors in 2 source files; "
    "`python scripts/false_evidence_register.py --check` -> current, exit 0 "
)


def main() -> int:
    log = ROOT / "CHANGELOG.md"
    text = log.read_text(encoding="utf-8")
    anchor = "- **The citation opener:"
    assert anchor in text, "CHANGELOG anchor missing"
    log.write_text(text.replace(anchor, CHANGELOG + anchor, 1), encoding="utf-8")

    state = ROOT / "STATE.md"
    lines = state.read_text(encoding="utf-8").split("\n")
    out = []
    for line in lines:
        if line.startswith("TASK: "):
            out.append("TASK: " + STATE_TASK + line[len("TASK: "):])
        elif line.startswith("LAST_GATE: "):
            out.append("LAST_GATE: " + STATE_GATE + line[len("LAST_GATE: "):])
        else:
            out.append(line)
    state.write_text("\n".join(out), encoding="utf-8")
    print("CHANGELOG.md and STATE.md updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
