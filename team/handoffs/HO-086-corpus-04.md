# HO-086 — A data-quality report on sample-data itself: rows, entities, periods, currency mix, missing fields and the residual per entity-month, generated not typed. Acceptance: the report regenerates from the corpus with one command and every figure traces to a query

## Claim
- claim: `opencode-20261009T1611Z-0dc2` · task: `CORPUS-04` · author: `opencode`
- scopes: `scripts/corpus_data_quality_report.py`, `evidence/corpus_data_quality.md`
- opened: 2026-10-09T16:11:51Z · handed off: 2026-10-09T16:14:44Z

## Changed
scripts/corpus_data_quality_report.py (new data-quality report generator script), evidence/corpus_data_quality.md (new data-quality report with full dimensional and trial balance breakdown).

## Verification
python scripts/corpus_data_quality_report.py -> exits 0, successfully analyzes 250,503 GL rows and writes evidence/corpus_data_quality.md.

## Doc-sync
docs-only-plus-evidence: no product behavior change, no threshold change, no new dependency, no ADR. Row 8 of Addon 6 table (docs/14 TESTING_QA_PLAN): corpus data-quality report verification documented. Row 5 CHANGELOG: entry owed, leader-only.

## Evidence
evidence/corpus_data_quality.md

## Next
For the reviewer: run `python scripts/corpus_data_quality_report.py` (expect exit 0) and review `evidence/corpus_data_quality.md`. Reject if either does not reproduce.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-086 --note "<what was reproduced>"`)_
