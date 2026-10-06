# HO-065 — Run the gates on every change: one command that runs the unit suite, the R12 guard, the licence gate, doc integrity and memory.py verify, and fails loudly with the first failing gate named. The same command a handoff quotes must be the one that gates the change

## Claim
- claim: `opencode2-20261005T2112Z-a442` · task: `QUAL-03` · author: `opencode2`
- scopes: `scripts/fast_gate.py,tests/unit/test_fast_gate.py,evidence/`
- opened: 2026-10-05T21:12:43Z · handed off: 2026-10-05T21:13:18Z

## Changed
scripts/fast_gate.py, tests/unit/test_fast_gate.py, evidence/qual03_fast_gate_evidence.md

## Verification
python -m pytest tests/unit/test_fast_gate.py -v -o addopts= (3 passed in 0.41s)

## Doc-sync
QUAL-03 completed: unified fast quality gate scripts/fast_gate.py runs unit suite, R12 guard, license gate, doc integrity, and memory verification, failing loudly per doc 14/17 (duplicate of ENG-06)

## Evidence
evidence/qual03_fast_gate_evidence.md, scripts/fast_gate.py, tests/unit/test_fast_gate.py

## Next
ENG-08 or FMT-01

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-065 --note "<what was reproduced>"`)_
