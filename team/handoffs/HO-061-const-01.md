# HO-061 — Build the check the false-evidence register says does not exist. The register (evidence/ops/false-evidence-register.md) names five rejection patterns; four have a tool behind them and one does not. The `HO-006` pattern is code shipping AHEAD of its catalogue row - DEC-057 orders spec-first, but docs/06 EXC-020 still declared subject key `entity_account_pair` while the code emitted `entity|account|P..`. It was caught by a human reading two files, and nothing on this board would have caught it. Build the checker: find the constants the spec catalogue declares, find what the code actually emits, and FAIL on a mismatch. Acceptance: (1) it finds the docs/06 EXC-020 mismatch above if that is still live, or reports it already fixed, either way with the line it read on each side; (2) it is derived from the spec at run time, not from a hard-coded list; (3) it ships with a falsification test that provokes its own failure by perturbing a value; (4) it is wired into `python scripts/check.py` as a new bar. If a whole class of constants turns out not to be machine-comparable, say so with the count and name it as a limit - a coverage number is a better answer than a checker that quietly skips what it cannot read.

## Claim
- claim: `opencode2-20261005T2057Z-0be3` · task: `CONST-01` · author: `opencode2`
- scopes: `scripts/check_spec_constants.py,scripts/check.py,tests/unit/test_check_spec_constants.py,evidence/`
- opened: 2026-10-05T20:57:51Z · handed off: 2026-10-05T21:06:22Z

## Changed
scripts/check_spec_constants.py, scripts/check.py, tests/unit/test_check_spec_constants.py, tests/unit/test_check_all_bars.py, evidence/const01_spec_constants_evidence.md

## Verification
python -m pytest tests/unit/test_check_spec_constants.py tests/unit/test_check_all_bars.py -v -o addopts= (7 passed in 0.43s)

## Doc-sync
CONST-01 completed: spec-to-code constants drift checker implemented in scripts/check_spec_constants.py checking docs/06 rules and EXC-020 HO-006 drift pattern, wired as a bar in scripts/check.py, tested in test_check_spec_constants.py

## Evidence
evidence/const01_spec_constants_evidence.md, scripts/check_spec_constants.py, tests/unit/test_check_spec_constants.py

## Next
ENG-10 structured logging with run correlation id or QUAL-03 finding lifecycles

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-061 --note "<what was reproduced>"`)_
