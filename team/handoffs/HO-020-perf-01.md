# HO-020 — Per-rule timing baseline: measure where the suite spends its time (per module, per rule batch) and record the numbers in evidence/perf/baseline.md so later optimisation claims are measured, not asserted

## Claim
- claim: `antigravity-20261005T1245Z-7839` · task: `PERF-01` · author: `antigravity`
- scopes: `evidence/perf/baseline.md`
- opened: 2026-10-05T12:45:03Z · handed off: 2026-10-05T12:53:51Z

## Changed
evidence/perf/baseline.md: measured and documented full per-rule timing baseline across 24 deduplicated evaluators on 250k-row fixture (250,040 rows, 65.51s, 845 MB peak memory, 388 findings), batch-level module breakdown, unit test durations (89 tests in 1.98s), and identified top 4 hotspots accounting for 55.2% of runtime

## Verification
pytest -m perf tests/perf/test_rules_perf.py (measured 65.51s run, 845 MB memory); pytest --durations=0 tests/unit/test_rules_*.py (89 passed in 1.98s); per-test module benchmarks

## Doc-sync
Aligned with doc 14 NFR-005 and NFR-007 baseline requirements; provides empirical targets for TB-020

## Evidence
evidence/perf/baseline.md

## Next
Peer verification by freebuff2/buffy; input to TB-020 performance optimization

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-020 --note "<what was reproduced>"`)_

### Verified by `hermes` — 2026-10-05T21:36:04Z
Reproduced: 3 perf tests passed (124.77s); 89 unit tests passed (1.19s). Hardware context: local environment.
