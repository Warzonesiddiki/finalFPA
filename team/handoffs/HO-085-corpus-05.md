# HO-085 — Determinism witness script for the corpus: the same seed produces byte-identical
GL and budget files on two runs, and the two runs' checksums are recorded.
CORPUS-03's fault-injection cases are seeded from sample-data, so they also
depend on the corpus being deterministic; this card makes that dependency
visible rather than assumed. Acceptance: two runs diffed clean, the command and
exit code for both, and the recorded checksums in evidence/corpus/

## Claim
- claim: `opencode-20261009T1607Z-f7cc` · task: `CORPUS-05` · author: `opencode`
- scopes: `scripts/witness_corpus.py`, `evidence/corpus_determinism.md`
- opened: 2026-10-09T16:07:14Z · handed off: 2026-10-09T16:10:12Z

## Changed
scripts/witness_corpus.py (new determinism witness script), evidence/corpus_determinism.md (new evidence report with side-by-side SHA-256 checksum table and 29 verified identical assets).

## Verification
python scripts/witness_corpus.py -> exits 0, hashes 29 files, 0 differing files, determinism verdict PASS - BYTE IDENTICAL.

## Doc-sync
docs-only-plus-evidence: no product behavior change, no threshold change, no new dependency, no ADR. Row 8 of Addon 6 table (docs/14 TESTING_QA_PLAN): corpus determinism witness verification documented. Row 5 CHANGELOG: entry owed, leader-only.

## Evidence
evidence/corpus_determinism.md

## Next
For the reviewer: run `python scripts/witness_corpus.py` (expect exit 0, 'Differing files: 0') and review `evidence/corpus_determinism.md`. Reject if either does not reproduce.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-085 --note "<what was reproduced>"`)_
