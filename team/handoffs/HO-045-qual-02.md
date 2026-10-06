# HO-045 — Traceability generated from code, not written: rule ID -> the module that implements it -> the test that proves it -> the evidence artefact, built by parsing app/engine and tests/ rather than by hand. Every rule with any leg missing is reported. Acceptance: the matrix regenerates with one command, and the list of incomplete rules is the deliverable, not a claim that none exist

## Claim
- claim: `opencode2-20261005T1916Z-dce4` · task: `QUAL-02` · author: `opencode2`
- scopes: `scripts/check_rule_traceability.py,tests/unit/test_check_rule_traceability.py,evidence/`
- opened: 2026-10-05T19:16:11Z · handed off: 2026-10-05T19:19:55Z

## Changed
scripts/check_rule_traceability.py, tests/unit/test_check_rule_traceability.py, evidence/rule_traceability_matrix.md

## Verification
python -m pytest tests/unit/test_check_rule_traceability.py -v -o addopts= (3 passed in 5.58s)

## Doc-sync
QUAL-02 completed: rule traceability dynamically parsed from app/engine/rules, tests, and evidence via scripts/check_rule_traceability.py; matrix deliverable in evidence/rule_traceability_matrix.md per doc 06/14

## Evidence
evidence/rule_traceability_matrix.md, scripts/check_rule_traceability.py

## Next
ENG-12 findings run correlation id and claim id tracking

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-045 --note "<what was reproduced>"`)_
