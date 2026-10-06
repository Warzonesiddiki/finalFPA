# HO-075 — Record measured acceptance result after adding ordered history imports

## Claim
- claim: `opencode-20261006T1408Z-f228` · task: `-` · author: `opencode`
- scopes: `evidence/acceptance_report.json`, `evidence/acceptance_report.md`
- opened: 2026-10-06T14:08:58Z · handed off: 2026-10-06T14:25:24Z

## Changed
evidence/acceptance_report.json; evidence/acceptance_report.md

## Verification
Remeasured the rule set on the persisted throwaway DB from the complete ordered-import run (50 findings, 21 expected matches); recomputed current corpus integrity across all 7 files; applied attach_corpus_gate/apply_blocked_state; wrote via acceptance.write_reports; copied byte-exactly.

## Doc-sync
Evidence-only update; docs/14 §5.2 and docs/28 §5.0 already define ordered history imports and the loaded/validated corpus entry condition. Leader-owned status docs and release dossier remain stale.

## Evidence
evidence/acceptance_report.json; evidence/acceptance_report.md

## Next
Independent reviewer should run scripts/acceptance.py on the final code; expected BLOCKED (exit 2) until history files 037/039/040 are repaired. Reconcile README/STATE/docs/16 and regenerate release-readiness-dossier after review.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-075 --note "<what was reproduced>"`)_
