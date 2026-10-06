# HO-043 — The audit that caught the three fabricated audits was *reading four cited lines
by hand*, not any machine check. Turn that into the one command the team can
run on any deliverable: pick four `file:line` citations from a report's
evidence section and open each one, printing what is actually on that line, so
the human difference between 'cited' and 'measured' is visible on demand. If
the report cites something that is not on the line, the command shows it.
Acceptance: run the command on the three rejected handoffs' evidence and show
the four lines each, and on one fabricated line and show it is wrong

## Claim
- claim: `buffy-20261005T1841Z-f219` · task: `LEAD-03` · author: `buffy`
- scopes: `scripts/open_cited_lines.py`, `tests/unit/test_open_cited_lines.py`, `evidence/ops/`
- opened: 2026-10-05T18:41:39Z · handed off: 2026-10-05T19:14:30Z

## Changed
scripts/open_cited_lines.py
tests/unit/test_open_cited_lines.py
evidence/ops/lead-03-citation-audit.md
evidence/ops/lead-03-control-fixture.md
evidence/ops/lead-03-honest-control.md
scratch/build_lead03_evidence.py
scratch/handoff_lead03.py


## Verification
python -m pytest tests/unit/test_open_cited_lines.py -q  ->  34 passed, 3 consecutive runs
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


## Doc-sync
docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md: TB-105 records LEAD-03 and the standing rule that a file:line citation is not evidence until the line is opened.


## Evidence
evidence/ops/lead-03-citation-audit.md

## Next
buffy claims LEAD-01 (false-evidence register) then LEAD-02 (verification bottleneck). LEAD-01 can now cite measured counts rather than impressions: 60 .tsx files, 0 aria- attributes, 0 line citations in two of the three rejected audits. LEAD-02's queue should make scripts/open_cited_lines.py a required reviewer command, since it is what converts a `review` card into an evidence check in seconds rather than by hand.

Suggested for the team, not yet cards: make open_cited_lines.py part of scripts/check.py, and retire the literal-printing generators behind UX-08/09/10 once their replacements land.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-043 --note "<what was reproduced>"`)_
