# HO-076 — Acceptance report committed-row count precision fix

## Claim
- claim: `opencode-20261006T1426Z-0143` · task: `-` · author: `opencode`
- scopes: `app/engine/rules/acceptance.py`, `tests/unit/test_acceptance_history.py`
- opened: 2026-10-06T14:26:39Z · handed off: 2026-10-06T14:27:56Z

## Changed
app/engine/rules/acceptance.py; tests/unit/test_acceptance_history.py

## Verification
pytest tests/unit/test_acceptance_history.py tests/unit/test_team_changed_paths.py -q -> 19 passed; test_balanced_but_rejected_general_ledger_blocks_complete_acceptance_measurement asserts parsed 110 vs committed 0; ruff check/format for new test -> clean; compileall + diff --check -> clean.

## Doc-sync
No spec behavior changed; this makes the acceptance report's Loaded column match the measured commit semantics of docs/04 §12 and DEC-056.

## Evidence
evidence/acceptance_report.md now shows history 037/039/040 loaded 0, 041 loaded 2; core actuals 250482/498/398. JSON retains parsed_loaded_count separately.

## Next
Independent reviewer: check source_file_name mapping uses basename as stored in FactActual; rerun acceptance report and verify the visible Loaded numbers match the database counts.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-076 --note "<what was reproduced>"`)_
