# HO-044 — DEF-015, and it is the last S1 that can reach a client number: money must be Decimal end to end. Find every place an amount crosses a boundary (parse, persist, compute, serialise) while still being a float, fix it, and add a test that fails if a float ever touches an amount again. Acceptance: the count before and after, the fixed sites listed by file:line, and a test that is proven to fail on an injected float

## Claim
- claim: `opencode2-20261005T1901Z-30e5` · task: `QUAL-01` · author: `opencode2`
- scopes: `app/engine/,tests/unit/test_def015_decimal_money.py,evidence/`
- opened: 2026-10-05T19:01:40Z · handed off: 2026-10-05T19:15:27Z

## Changed
app/engine/ai/guardrails.py, tests/unit/test_def015_decimal_money.py, evidence/qual01_decimal_money_audit.md

## Verification
python -m pytest tests/unit/test_def015_decimal_money.py -v -o addopts= (20 passed in 9.73s)

## Doc-sync
QUAL-01 completed: DEF-015 Decimal money audited end-to-end; app/engine/ai/guardrails.py spend caps and rates coerced to Decimal; test_def015_decimal_money.py expanded with falsification test proving injected float cent leak

## Evidence
evidence/qual01_decimal_money_audit.md, tests/unit/test_def015_decimal_money.py

## Next
ENG-12 findings run correlation id and claim id tracking

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-044 --note "<what was reproduced>"`)_
