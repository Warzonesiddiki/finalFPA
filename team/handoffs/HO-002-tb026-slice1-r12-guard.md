# HO-002 — `TB-026` slice 1: the `R12` single-implementation guard for the engine

## Claim
- claim: `buffy-20261005T1054Z-6691` · task: `TB-026` (forced past dep `TB-016`, reason logged in the claim)
  · author: `buffy`
- scopes: `tests/unit/test_engine_common.py`, `evidence/tb026/`
- opened: 2026-10-05T10:54Z · handed off: 2026-10-05T11:00Z

## Changed
- `tests/unit/test_engine_common.py` — **new**, 6 tests: an `ast` walk of `app/engine` that fails on any
  capability defined twice outside a documented allowlist, plus pinned single-home assertions for
  `quantize_money`, `period_end_from_id`, `resolve_as_of_date` and `normalise_invoice_no`, an
  allowlist-accuracy test, and a non-vacuity test (so a broken glob cannot pass silently).
- `evidence/tb026/survey.md` — **new**: the measurement that showed the money/period helpers are *already*
  consolidated, the two genuine duplicates found, and what is deliberately owed.
- No product code changed. `app/engine/dedupe/blocking.py` was mutated and restored during verification
  (byte-checked).

## Verification
- `python -m pytest tests/unit/test_engine_common.py -q -o addopts=""` → **6 passed**.
- Mutation check: a second `count_distinct` appended to `app/engine/dedupe/blocking.py` → **1 failed**, message
  naming both locations (`blocking.py:86`, `blocking.py:98`); after restore → **6 passed** again.
- `python -m pytest tests/unit/test_dedupe.py -q -o addopts=""` → 41 passed (confirming the restore).
- `python scripts/team.py check` → PASS (0 fail) after the new test.

## Doc-sync
- Addon 6 §8: `33` (`TB-026` slice-1 status lives in this handoff + `evidence/tb026/survey.md`);
  `CHANGELOG` + `STATE` entry owed before release; **no** adoption (no `ADP`/`THIRD_PARTY_NOTICES`/`15`),
  **no** FR change (`20` not touched), `docs/14` coverage row owed if the new test changes the coverage tier.
- Behaviour change: **none** — the new file is a test.

## Evidence
- `evidence/tb026/survey.md`

## Next
1. `antigravity`: reproduce the 6-pass run and the mutation catch, then append a verification block here.
2. Slice 2 (needs `TB-016`/`TB-014` first): one shared subject-key digest helper replacing 12 ad-hoc
   `hashlib.sha256` call sites.
3. `opencode`: the two allowlisted `FOLLOW-UP` duplicates (`split_sentences`, `check_banned_phrases`).

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above, pastes the raw result, then
`python scripts/team.py verify --task TB-026 --by <agent> --handoff HO-002 --note "<what was reproduced>"`)_
### Verified by `antigravity` — 2026-10-05T11:13:00Z
Reproduced 6 passed in test_engine_common.py; mutation check reproduced (second count_distinct caused failure at blocking.py:86 and 98); restored clean state reproduced 6 passed and 41 passed in test_dedupe.py.

### Verified by `antigravity` — 2026-10-05T11:40:22Z
reproduced: 6 passed in test_engine_common.py; mutation check verified duplicate count_distinct fails
