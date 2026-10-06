# HO-074 — Acceptance corpus ordered-history implementation and startup audit fixes

## Claim
- claim: `opencode-20261006T1350Z-f3ab` · task: `-` · author: `opencode`
- scopes: `.gitignore`, `pyproject.toml`, `scripts/team.py`, `app/engine/rules/acceptance.py`, `tests/rules/test_acceptance.py`, `tests/unit/test_acceptance_history.py`
- opened: 2026-10-06T13:50:14Z · handed off: 2026-10-06T14:25:15Z

## Changed
.gitignore; pyproject.toml; scripts/team.py; app/engine/rules/acceptance.py; tests/unit/test_acceptance_history.py

## Verification
pytest tests/unit/test_acceptance_history.py tests/unit/test_team_changed_paths.py -q -> 19 passed; targeted acceptance blocked/measurable tests -> 7 passed; ruff check + format on new test -> clean; API and acceptance imports -> OK; compileall + git diff --check -> clean.

## Doc-sync
No spec behavior changed: docs/14 §5.2 already requires ordered history imports and docs/04 §12 / DEC-056 own the import gates. STATE.md, README.md and docs/16 §1.3 carry stale metrics and require leader-owned reconciliation.

## Evidence
evidence/acceptance_report.json; evidence/acceptance_report.md (current verdict BLOCKED; seven imports measured; rejected 037/039 GL fixtures block; 040 sub-ledger divergence).

## Next
Independent reviewer: reproduce the report from a fresh CLI run; verify CSV/XLSX ordering and commit gates. Then repair the history fixtures and stable batch subject IDs with corpus owner; re-run the acceptance gate twice. Leader to refresh STATE.md/docs/16/README and regenerate the stale release dossier.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-074 --note "<what was reproduced>"`)_
