"""Update STATE.md and docs/SESSION_LOG.md for LEAD-03 (leader-only records)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATE_TASK = (
    "CITATION OPENER LANDED (TB-105 / LEAD-03): the TB-104 rejection was made by a human opening "
    "four cited lines by hand; that step is now `scripts/open_cited_lines.py`. It finds the "
    "file:line citations a report makes, opens each one, prints the line that is actually there, and "
    "compares the backticked key=\"value\" claims sitting beside the citation against it. --handoff "
    "HO-nnn follows a handoff to its evidence; --limit 0 sweeps every citation; --context N, --json. "
    "Exit 0 requires every sampled citation resolved AND every claim token on its cited line; a "
    "report citing NO source line fails rather than passing vacuously. RESULTS ON THE REJECTED TRIO: "
    "HO-031 exit 1 - four files real, four line numbers in range, four lines carrying none of the "
    "claimed attributes; and DEEPER THAN THE ORIGINAL REJECTION, 'aria-' occurs 0 times across all "
    "60 .tsx files in ui/src, so the 42 'Conforming' verdicts assert role/aria-label/aria-live "
    "attributes that exist nowhere and every screen in that matrix is in fact NOT AUDITED. HO-033 "
    "exit 1 - names app/engine/calc/math.py on all twelve rows, never a line number. HO-035 exit 1 "
    "- cites no source file at all. TWO FIXTURES, because a gate that can only fail proves nothing: "
    "evidence/ops/lead-03-control-fixture.md exit 1 (real file, in-range non-blank line reading "
    "LOCK_TIMEOUT = 60.0, wrong claim - precisely what an existence-and-range check passes) and "
    "lead-03-honest-control.md exit 0, identical in shape. 34 tests, five of them falsification or "
    "false-green guards; the load-bearing one is test_passing_report_fails_when_the_cited_line_"
    "changes, i.e. the HO-031 rejection turned into an assertion. THE TOOL CAUGHT TWO DEFECTS IN "
    "ITS OWN AUTHOR: a FILE_MISSING row printed 'absent: none - all present', a false green for a "
    "line never opened; and fenced code blocks were scanned, so a document quoting an audit failed "
    "its own tool. Stated limit: it proves a claim is ON a line, not that the line is the RIGHT line "
    "for the claim - that still needs a reader. docs/33 gains TB-105 and §5.12. "
)

STATE_GATE = (
    "- LEAD-03: `python -m pytest tests/unit/test_open_cited_lines.py -q` -> 34 passed, 3 "
    "consecutive runs; `python -m pytest tests/unit/test_memory.py "
    "tests/unit/test_team_changed_paths.py tests/unit/test_team_watchdog.py "
    "tests/unit/test_open_cited_lines.py -q` -> 93 passed, exit 0; `ruff check "
    "scripts/open_cited_lines.py tests/unit/test_open_cited_lines.py` -> All checks passed; `mypy "
    "scripts/open_cited_lines.py` -> Success, 0 errors; `python scripts/open_cited_lines.py "
    "evidence/ops/lead-03-citation-audit.md --limit 0` -> exit 0 (the evidence doc is green under "
    "its own tool) "
)

SESSION_ADDENDUM = """
## Addendum 6 — LEAD-03: the citation opener, and what it found beyond the four lines

**Card:** `LEAD-03` (P1, verification lane) · **claim:** `buffy-20261005T1841Z-f219` ·
**handoff:** `HO-043` · **records:** `TB-105`, `docs/33` §5.12

### Why this card exists

`TB-104` rejected three audits. The step that caught them was a human opening four cited lines by
hand — a check that worked, done once, by accident, and not repeatable. `LEAD-03` is that step as a
command.

```
python scripts/open_cited_lines.py <report.md>            # four citations, the default
python scripts/open_cited_lines.py <report.md> --limit 0  # sweep every citation
python scripts/open_cited_lines.py --handoff HO-nnn       # follow a handoff to its evidence
python scripts/open_cited_lines.py <report.md> --context 2 --json
```

It finds the `file:line` citations a report makes, opens each one, prints the line that is actually
there, and compares the backticked `key="value"` claims sitting beside the citation against that
line. Exit `0` requires that every sampled citation resolved **and** every claim token is on its
cited line. A report that cites **no** source line fails, because a document with no citations has
measured nothing.

### What it found on the rejected trio

| Handoff | Evidence | Exit | What the command found |
|---|---|---|---|
| `HO-031` | `evidence/ux/a11y-keyboard.md` | 1 | 4 files real, 4 line numbers in range, 4 lines carrying none of the claimed attributes |
| `HO-033` | `evidence/ux/numbers-trace.md` | 1 | cites no line — names `app/engine/calc/math.py` on all twelve rows |
| `HO-035` | `evidence/ux/error-catalogue.md` | 1 | cites no source file at all |

`ui/src/main.tsx:145`, the first citation, is
`{activeTab === 'home' && 'Executive Month-End Overview (SCR-001)'}`. The row claims
`role="main"` and `aria-label="Home Overview"`.

### The finding beyond the spot-checks

The `TB-104` rejection opened four lines by hand. The command counted the whole population:
**`aria-` occurs 0 times across all 60 `.tsx` files in `ui/src`.**

So the 42 `Conforming` verdicts are not mis-cited readings of a real implementation. They assert
`role="main"`, `aria-label="…"` and `aria-live="polite"` attributes that exist nowhere in the UI.
Every screen in that matrix is in fact **`NOT AUDITED`** — which is precisely what the rejection
demanded and what the code shows. A uniform verdict across an entire population is the signature of
not looking.

### A gate that can only fail proves nothing

Two fixtures ship under `evidence/ops/`, identical in shape and differing only in whether the claim
is true. The false one's row `FAKE-003` is the load-bearing case: real file, in-range line,
non-blank line reading `LOCK_TIMEOUT = 60.0`, wrong claim. A checker confirming existence and range
would pass it — which is exactly what `verify_audit_citations.py` did. The honest control returns
green, guarded by a test, because a gate tightened until everything fails looks strict and measures
nothing.

Both fixtures cite `scripts/memory.py` and `ui/src` constants rather than lines inside a file under
active development. The first draft cited `scripts/open_cited_lines.py:83` and described it as
"blank"; the next edit to that script made the description false. A fixture that drifts into a false
claim is a fixture that starts lying — the exact failure this card exists to stop.

### Two defects the tool found in its own author

Both surfaced only by running it over its own output, which is why that run is worth doing:

1. **A false green.** A `FILE_MISSING` row printed `absent: none — all present`, because the
   missing-claim list was empty for want of having read anything. Absence of evidence rendering as
   evidence. Now `not checked — the cited line was never opened`, guarded by
   `test_unopened_line_never_reports_all_present`.
2. **Quoted evidence read as claims.** Fenced code blocks were scanned, so
   `evidence/ops/lead-03-citation-audit.md` failed its own tool on its own captured output. Fences
   are now skipped; inline code spans deliberately are not, since a backticked `path:line` in prose
   or a table is the claim under test. Writing this document's two claims as a single sentence then
   made each citation carry both claims, and it failed again — restated one claim per line, it is
   green.

### The limit, stated plainly

The command proves a claim is **on** a line. It cannot prove the line is the **right** line for the
claim — that still takes a reader. It removes the possibility of an unchecked claim, not the
possibility of a wrong one. Only backticked `key="value"` pairs are treated as claims; a row whose
only backticked text is a screen id is reported `cited only, nothing checked` and the run ends
`INCONCLUSIVE`, because inventing a claim would manufacture failures in honest reports.

### Gates

```
pytest tests/unit/test_open_cited_lines.py -q                      -> 34 passed (3 consecutive runs)
pytest test_memory + test_team_changed_paths + test_team_watchdog
       + test_open_cited_lines -q                                  -> 93 passed, exit 0
ruff check scripts/open_cited_lines.py tests/unit/...              -> All checks passed
mypy scripts/open_cited_lines.py                                   -> Success, 0 errors
scripts/check_doc_integrity.py                                     -> exit 0, 113 markdown files
scripts/license_gate.py                                            -> exit 0, all six checks
scripts/open_cited_lines.py evidence/ops/lead-03-citation-audit.md --limit 0 -> exit 0
```

Follow-on: `LEAD-01` (false-evidence register) can now cite measured counts rather than
impressions; `LEAD-02` (verification bottleneck) should make this a required reviewer command.
"""


def main() -> int:
    state = (ROOT / "STATE.md").read_text(encoding="utf-8")
    lines = state.split("\n")
    out = []
    for line in lines:
        if line.startswith("TASK: "):
            out.append("TASK: " + STATE_TASK + line[len("TASK: "):])
        elif line.startswith("LAST_GATE: "):
            out.append("LAST_GATE: " + STATE_GATE + line[len("LAST_GATE: "):])
        else:
            out.append(line)
    (ROOT / "STATE.md").write_text("\n".join(out), encoding="utf-8")

    log = ROOT / "docs" / "SESSION_LOG.md"
    text = log.read_text(encoding="utf-8").rstrip("\n")
    log.write_text(text + "\n" + SESSION_ADDENDUM, encoding="utf-8")
    print("STATE.md and docs/SESSION_LOG.md updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
