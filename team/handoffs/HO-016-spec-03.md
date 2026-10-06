# HO-016 — Threshold conformance: every numeric threshold, tolerance and default in 06 and 14 (500000 floors, coverage pct, min_coverage_gap_periods, tolerances) compared against the code and config defaults; each mismatch is a row with clause, code:line, value in code, value in spec, verdict. Output evidence/spec/threshold-conformance.md

## Claim
- claim: `opencode-20261005T1228Z-4fd2` · task: `SPEC-03` · author: `opencode`
- scopes: `evidence/spec/threshold-conformance.md`
- opened: 2026-10-05T12:28:28Z · handed off: 2026-10-05T12:32:48Z

## Changed
evidence/spec/threshold-conformance.md

## Verification
audit produced 30 rows: verdicts 19 MATCH/2 PARTIAL/8 MISMATCH/1 runtime-verified; EXC-021 dual/single match 2.5M/500k (Indian grouping); EXC-022 missing entity-mean x1.5 gate; EXC-024 flat 100k floor vs spec budget-scaled threshold + missing movement branch

## Doc-sync
Addon6-S8 N/A (conformance audit, no code change). Follow-up needs owner decision via docs/18: either align code to spec floors (raise flat 50000/100000 defaults) or spec-change.

## Evidence
evidence/spec/threshold-conformance.md

## Next
buffy reads and decides R1/ingest to docs/18; antigravity may cross-verify any rows they own; then open ENG-02 (align code thresholds) on my queue

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-016 --note "<what was reproduced>"`)_

### Verified by `antigravity` — 2026-10-05T12:39:25Z
Cross-verified all 30 audit rows in evidence/spec/threshold-conformance.md against docs/06 and engine rules code. Confirmed 19 MATCH, 2 PARTIAL, 8 MISMATCH, 1 RUNTIME; all 8 flat-rupee vs budget-scaled floor mismatches (EXC-001, 005, 010, 013, 014, 022, 024) and missing branches independently verified against code lines.
