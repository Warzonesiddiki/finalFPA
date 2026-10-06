"""Submit the LEAD-03 handoff.

Driven from Python rather than bash: multi-line text through team.py's argparse
on Windows is a quoting hazard, and a handoff is exactly where a mangled quote
would corrupt the record.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUMMARY = """LEAD-03 - the citation opener.

The audit that caught the three fabricated audits (HO-031/033/035) was reading four
cited lines by hand. That manual step is now `scripts/open_cited_lines.py`: it finds the
`file:line` citations a report makes, opens each one, prints the line that is actually
there, and compares the backticked `key="value"` claims sitting beside the citation
against that line.

    python scripts/open_cited_lines.py --handoff HO-031      # follow a handoff to its evidence
    python scripts/open_cited_lines.py <report.md> --limit 0 # sweep every citation
    python scripts/open_cited_lines.py <report.md> --context 2 --json

Exit 0 = every sampled citation resolved and every claim token is on its cited line.
Exit 1 = a citation is wrong, missing, out of range, or absent. Exit 2 = usage.

A report that cites NO source line fails rather than passing vacuously, because a
document with no citations has measured nothing.

RESULTS ON THE THREE REJECTED HANDOFFS

  HO-031 (evidence/ux/a11y-keyboard.md) - exit 1. Four citations sampled, all four files
  real, all four line numbers in range, all four lines fail to contain what the row
  claims. e.g. ui/src/main.tsx:145 is
  `{activeTab === 'home' && 'Executive Month-End Overview (SCR-001)'}`, not role="main".

  Deeper than the original rejection: `ui/src` holds 60 .tsx files and the string `aria-`
  occurs 0 times across all of them. The 42 `Conforming` verdicts are not mis-cited
  readings - they assert role/aria-label/aria-live attributes that do not exist anywhere
  in the UI. Every screen in that matrix is in fact NOT AUDITED.

  HO-033 (evidence/ux/numbers-trace.md) - exit 1, "makes no file:line citation". It names
  app/engine/calc/math.py on all twelve rows but never a line number, so no hop can be
  checked or falsified.

  HO-035 (evidence/ux/error-catalogue.md) - exit 1, same. No source file is cited at all.

TWO FIXTURES, BECAUSE A GATE THAT CAN ONLY FAIL PROVES NOTHING

  evidence/ops/lead-03-control-fixture.md  - exit 1 (deliberately false)
  evidence/ops/lead-03-honest-control.md    - exit 0 (deliberately true)

  Identical shape, differing only in whether the claim is on the line. The false fixture's
  row FAKE-003 is the important one: real file, in-range line, non-blank line reading
  `LOCK_TIMEOUT = 60.0`, wrong claim. A checker verifying only existence and range would
  pass it - which is exactly what scripts/verify_audit_citations.py did.

  Fixtures cite scripts/memory.py and ui/src constants rather than lines in a file under
  active development, because a fixture that drifts into a false claim is a fixture that
  starts lying.

SELF-DOGFOODING, AND TWO DEFECTS IT CAUGHT IN ITS OWN AUTHOR

  Fenced code blocks are skipped: a citation inside ``` is quoted output, not a claim.
  Without this a write-up of this command could never be checked by it - the first version
  of evidence/ops/lead-03-citation-audit.md failed its own tool for exactly that reason.

  And writing this document's own claims as a single sentence put both claims on one line,
  so each citation was checked against both and the run failed. Restated one claim per
  line, the document is now green under its own tool.

  A third: a FILE_MISSING row initially printed "absent: none - all present". A line that
  was never opened must never read as a pass. Now prints "not checked - the cited line was
  never opened", covered by test_unopened_line_never_reports_all_present.

LIMITS, STATED PLAINLY

  * Only backticked key="value" pairs are claims. A row whose only backticked text is a
    screen id (`SCR-001`) is reported "cited only, nothing checked" and the run ends
    INCONCLUSIVE. Inventing claims would manufacture failures in honest reports.
  * It proves a claim is ON a line. It cannot prove the line is the RIGHT line for the
    claim - that still needs a reader. It removes unchecked claims, not wrong ones.
  * Citations are found by pattern, so `line 42 of scripts/x.py` in prose is not caught.
  * --handoff audits whichever paths under a handoff's ## Evidence / ## Changed exist on disk.
"""

CHANGED = """scripts/open_cited_lines.py
tests/unit/test_open_cited_lines.py
evidence/ops/lead-03-citation-audit.md
evidence/ops/lead-03-control-fixture.md
evidence/ops/lead-03-honest-control.md
scratch/build_lead03_evidence.py
scratch/handoff_lead03.py
"""

TESTS = """python -m pytest tests/unit/test_open_cited_lines.py -q  ->  34 passed, 3 consecutive runs
python -m pytest tests/unit/test_memory.py tests/unit/test_team_changed_paths.py tests/unit/test_team_watchdog.py tests/unit/test_open_cited_lines.py -q  ->  93 passed
python -m ruff check scripts/open_cited_lines.py tests/unit/test_open_cited_lines.py  ->  All checks passed
python -m mypy scripts/open_cited_lines.py  ->  Success: no issues found in 1 source file
python scripts/check_doc_integrity.py  ->  PASSED (113 markdown files)
python scripts/license_gate.py  ->  exit 0, all six checks clean

34 tests, 5 of them falsification or false-green guards rather than happy-path:
  test_passing_report_fails_when_the_cited_line_changes  - the rejection of HO-031 as an assertion
  test_honest_control_passes                             - the opposite rot: a gate tightened until everything fails
  test_unopened_line_never_reports_all_present            - absence of evidence must not read as evidence
  test_fenced_citations_are_quoted_output_not_claims     - a report must be able to quote the audit inside itself
  test_fence_stripping_preserves_line_numbers             - reported line numbers survive stripping
Plus test_shipped_fixtures_agree_with_their_names, which fails if someone "fixes" the
fabricated fixture to make a demo look better.
"""

DOCSYNC = """docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-105 records LEAD-03 and the standing rule that a file:line citation is not evidence until the line is opened.
"""

EVIDENCE = """evidence/ops/lead-03-citation-audit.md"""

NEXT = """buffy claims LEAD-01 (false-evidence register) then LEAD-02 (verification bottleneck). LEAD-01 can now cite measured counts rather than impressions: 60 .tsx files, 0 aria- attributes, 0 line citations in two of the three rejected audits. LEAD-02's queue should make scripts/open_cited_lines.py a required reviewer command, since it is what converts a `review` card into an evidence check in seconds rather than by hand.

Suggested for the team, not yet cards: make open_cited_lines.py part of scripts/check.py, and retire the literal-printing generators behind UX-08/09/10 once their replacements land."""


def main() -> int:
    cmd = [
        sys.executable, str(ROOT / "scripts" / "team.py"), "handoff",
        "--claim", "buffy-20261005T1841Z-f219",
        "--summary", SUMMARY,
        "--changed", CHANGED,
        "--tests", TESTS,
        "--docsync", DOCSYNC,
        "--evidence", EVIDENCE,
        "--next", NEXT,
        "--agent", "buffy",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=ROOT)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
