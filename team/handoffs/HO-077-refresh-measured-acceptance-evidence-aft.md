# HO-077 — Refresh measured acceptance evidence after count correction

## Claim
- claim: `opencode-20261006T1426Z-8f97` · task: `-` · author: `opencode`
- scopes: `evidence/acceptance_report.json`, `evidence/acceptance_report.md`
- opened: 2026-10-06T14:26:39Z · handed off: 2026-10-06T14:28:03Z

## Changed
evidence/acceptance_report.json; evidence/acceptance_report.md

## Verification
Re-evaluated the 24-rule set twice against the persisted throwaway DB from the full ordered-import run (50 findings, stability identical); recalculated seven-file corpus integrity and measured database row counts; write_reports output matches committed evidence byte-for-byte.

## Doc-sync
Evidence-only. The leader-owned README/STATE/docs/16 metrics and stale release dossier remain queued for owner reconciliation; no docs authority was modified.

## Evidence
evidence/acceptance_report.json; evidence/acceptance_report.md (BLOCKED; 037/039 0 committed, 040 0 committed, 041 2 committed; main GL 250482, bank 498, payroll 398).

## Next
Independent reviewer: reproduce from the current CLI on a fresh temp project (expected exit 2 / BLOCKED); leader to refresh STATE/docs/16/README and regenerate release readiness after fixture repair.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-077 --note "<what was reproduced>"`)_
