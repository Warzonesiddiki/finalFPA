"""Correct the recorded verification-queue test count from 14 to 18.

Four CLI tests were added during the completion check, so every record that
described the queue as "14 tests" became stale the moment they landed.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NOTE = (
    " (14 at handoff; 18 after the completion check added four `--for` CLI tests — "
    "the path a seat actually types, and the one where the AWAY refusal has to survive)"
)

EDITS = [
    (
        "docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md",
        "14 tests, including the falsification case where one seat wrote the only handoff and the "
        "queue reports *no eligible seat* rather than proposing a self-verification |",
        "18 tests" + NOTE + ", including the falsification case where one seat wrote the only "
        "handoff and the queue reports *no eligible seat* rather than proposing a self-verification |",
    ),
    (
        "CHANGELOG.md",
        "14 tests, including the case where one seat wrote the only handoff and the queue reports *no "
        "eligible seat* rather than proposing a self-verification.",
        "18 tests" + NOTE + ", including the case where one seat wrote the only handoff and the "
        "queue reports *no eligible seat* rather than proposing a self-verification.",
    ),
    (
        "docs/SESSION_LOG.md",
        "pytest tests/unit/test_verification_queue.py -q                      -> 14 passed",
        "pytest tests/unit/test_verification_queue.py -q                      -> 18 passed",
    ),
    (
        "STATE.md",
        "- LEAD-02: `python -m pytest tests/unit/test_verification_queue.py -q` -> 14 passed;",
        "- LEAD-02: `python -m pytest tests/unit/test_verification_queue.py -q` -> 18 passed "
        "(14 at handoff + 4 `--for` CLI tests added at the completion check);",
    ),
    (
        "STATE.md",
        "test_team_changed_paths + test_team_watchdog) -> 121 passed, exit 0;",
        "test_team_changed_paths + test_team_watchdog) -> 125 passed, exit 0;",
    ),
]


def main() -> int:
    for rel, old, new in EDITS:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        if old not in text:
            print(f"MISS {rel}: {old[:60]!r}")
            return 1
        p.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"ok   {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
