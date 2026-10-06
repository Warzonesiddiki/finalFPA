"""Append the LEAD-01 addendum to docs/SESSION_LOG.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADDENDUM = """
## Addendum 7 — LEAD-01: the false-evidence register, and the pattern I did not expect

**Card:** `LEAD-01` (P0, verification lane) · **claim:** `buffy-20261005T1916Z-2c19` ·
**handoff:** `HO-046` · **records:** `TB-106`, `docs/33` §5.13

### The card, and what measuring it found

`LEAD-01` asked for "one row per rejected handoff with the pattern it failed on", and said three of
the session's rejects share one root cause. It did not say how many rejections there were.

Reading every `### Rejected by` block on the board: **10 rejected handoffs, 5 patterns.**

| Pattern | Count | Handoffs |
|---|---|---|
| `A-hidden-blast-radius` | **4** | `HO-003`, `HO-010`, `HO-012`, `HO-013` |
| `C-literal-generator` | 3 | `HO-031`, `HO-033`, `HO-035` |
| `B-written-outside-scope` | 1 | `HO-025` |
| `D-checker-cannot-fail` | 1 | `HO-004` |
| `F-spec-code-drift` | 1 | `HO-006` |

The most frequent pattern is not the one the card was written about. `## Changed` listing one file
while the claim window showed four to seven has happened **four times**, and every one was caught by
a human reading the claim window. The three literal-generator rejections were the same mistake made
three times in one sitting by an author who was not trying to deceive anyone.

The lesson is about method, not blame: **count the failures before writing the rule about them.** A
card scoped to a pattern I already believed was dominant would have shipped a register organised
around the wrong row.

### Generated, not written

`scripts/false_evidence_register.py` derives the roster from the handoffs that actually carry a
`### Rejected by` block, re-audits each one's evidence *at generation time* through
`scripts/open_cited_lines.py`, and `--check` fails when it has drifted. A hand-written register is a
snapshot that starts lying the moment somebody is rejected.

Three refusals, because each is a way this kind of file rots:

1. **An unclassified rejection is a hard error.** `build()` raises. A new pattern nobody has looked
   at is exactly what the file exists to surface; omitting it quietly reduces the register to the
   patterns we already knew about.
2. **A pattern entry keyed on a handoff that was never rejected** is a row that can never recur, so
   `test_every_pattern_entry_exists_on_the_board` fails on one.
3. **A verdict where no verdict applies is worse than `n/a`.** Running the citation audit over a
   blast-radius rejection produces "the test file cites no source line" — true, and useless. The
   first draft of the generator did exactly this and printed that verdict for six of ten rows.

### Five agents, one checkout

The first generated roster said `HO-031` cited **43 fabricated lines**. Twelve minutes later it said
**zero**. Nothing had changed in the generator: `hermes` had rewritten
`evidence/ux/a11y-keyboard.md` at 00:32, converting every `Conforming` row to `NOT AUDITED` and
`FAIL (No ARIA)` — exactly what the `TB-104` rejection demanded, and independent confirmation of the
`aria-` = 0 finding in `TB-105`.

The lesson is not to distrust the measurement; it is to label it. Every such column now says
**now**, not *at rejection time*, and the register states the distinction in the table footnote. A
rejection records a pattern; a re-measurement records whether the artefact has moved since. Two
different claims, and conflating them is how a register starts asserting things that are no longer
true.

### The rule it records

> A generator whose output does not change when its input changes is a printer, not a generator.

### What would have caught what

Ranked by how many rejections each stops on first run — the only ranking that decides what to build
next:

1. **`scripts/open_cited_lines.py`** (`TB-105`, shipped) — stops `HO-031` outright, reports
   `HO-033`/`HO-035` as citing no line at all.
2. **The `## Changed` vs claim-window rule** (`team.py check`, shipped in `TB-101`) — stops four
   rejections automatically. It currently **WARNs**. Making an undeclared shipped file **FAIL** is
   the highest-value small change left in this register.
3. **The claim-window scan** (`TB-101`) — stops `HO-025`.
4. **A spec-to-code constant check** — **does not exist.** The `HO-006` pattern, code shipping ahead
   of the catalogue `DEC-057` requires, was caught by a human reading two files. Nothing on this
   board would have caught it. That is the honest reason `LEAD-01` is a register rather than a
   solved problem.

### Gates

```
pytest tests/unit/test_false_evidence_register.py -q                  -> 14 passed
pytest tests/unit/test_open_cited_lines.py
       tests/unit/test_false_evidence_register.py -q                   -> 48 passed, exit 0
ruff check (all four new files)                                        -> All checks passed
mypy scripts/open_cited_lines.py scripts/false_evidence_register.py    -> Success, 0 errors
python scripts/false_evidence_register.py --check                     -> current, exit 0
python scripts/check_doc_integrity.py                                  -> exit 0
python scripts/license_gate.py                                         -> exit 0, all six checks
```
"""


def main() -> int:
    log = ROOT / "docs" / "SESSION_LOG.md"
    text = log.read_text(encoding="utf-8").rstrip("\n")
    if "Addendum 7" in text:
        print("Addendum 7 already present; not appending twice")
        return 0
    log.write_text(text + "\n" + ADDENDUM, encoding="utf-8")
    print("docs/SESSION_LOG.md: Addendum 7 appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
