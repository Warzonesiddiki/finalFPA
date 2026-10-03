# FP&A Month-End Copilot — Session Handover (2026-10-03, 19:40)

## VERIFIED STATE — measured, not asserted

```
pytest                       exit 0, 711 tests collected, 0 FAILED, 0 ERROR
scripts/acceptance.py        exit 2, "ACCEPTANCE: BLOCKED", bars NOT MEASURED
DimAccount                   19 rows
docs/18                      55 DEC rows
docs/28                      19 DEF ids referenced
```

Run these yourself before trusting any of it:

    pytest -p no:cacheprovider -q
    python scripts/acceptance.py

## THE ONE THING THAT MATTERS

**Not one of the 18 closed defects was caught by a failing test.**

Every single one was found by reading bytes or running a validator, through a
suite that stayed green the entire time. The 711 passing tests are not what is
holding this project together. The invariants are.

Corollary you must internalise before writing any code: **a green result that
proves nothing is worse than no result**, because it certifies something nobody
verified. Rejected examples from this session:

- a "regression guard" that was a verbatim duplicate of the assertion above it
- a corpus-integrity test that passed with the very account it guards deleted
- an exception-handler "hardening" that turned every 404 into a 500
- my own mutation harness reporting OK on mutations that caused collection errors
- me racing two mutation runs on one file, leaving a mutation in place

## Standard: prove the control catches the defect it claims to catch

Any new guard must be mutation-proven before it counts as done. Two harnesses
exist as reference implementations:

    python tools/mut024.py                                  # 5 mutations, all caught
    tests/unit/test_def024_rule_containment.py              # 13 tests

Harness rules learned the hard way: assert the mutation actually applied; restore
in a `finally`; verify the restore byte-identical; never run two instances
concurrently (they race and leave a mutation in place). `tools/mut024.py` takes a
lock file for this reason.

## CRITICAL PATH — corpus swap, in this order

`scripts/acceptance.py` exits 2 because `d365_gl_actuals.csv` is unbalanced, so
zero rows commit and every planted exception is unreachable.

    net_imbalance = 17,944,515,579.33   debit 24,626,607,267.80
                                     credit  6,682,091,688.47
    failing check IMP-023 of 9, data_quality_score=84, 0 of 250,037 rows landed

- Committed corpus is STILL THE OLD ONE: `sample-data/d365_gl_actuals.csv`,
  50,610,576 bytes, mtime 02-10-2026. **Not swapped.**
- Rebuilt double-entry corpus sits in `temp_sample_data_def019/`, 49,758,720
  bytes, mtime 03-10-2026 18:00. Residual there is 8,944,299.00.
- Rollback point: `backups/pre_def019_20261003_153000/`, SHA-256
  `2C791E5F270BC4D974F64F0078E84F5D9A33A47E8004986363B36A30342789C3`

Do: snapshot with a hash manifest → swap → paste raw acceptance output.

**Do not tune a threshold, rule, or fixture to move a number.** Report whatever
the bars ARE. If a threshold is genuinely wrong, quote the owning spec line and
propose — the lead rules, never self-approve. A worse-looking acceptance bar is
worth more than a good-looking one that cannot be trusted.

## Rulings already made — do not re-litigate

- **Seed is 42**, not 20260101. `doc-14 §5.2` amended. Committed corpus is
  byte-reproducible at seed 42.
- **The 17.9B suspense plug on 1999 is RULED OUT.** `evaluate_exc_024` reads
  `suspense_accounts={'1999','9999','SUSPENSE'}` at a 100,000 floor, so a plug of
  that size reads as a genuine residual. Option (B) double-entry rebuild adopted.
- **Do NOT balance the planted vouchers.** EXC-023 sums per voucher, so balancing
  P23 would silence the exception it exists to detect.
- **`5999-TEMP` must stay out of `DimAccount`.** It is plant P4; seeding it would
  stop the unmapped-account exception firing. Encoded as an expected-unmapped
  entry with its plant reference, never a silent exclusion.
- **`1010`/`1200`/`2000`/`1020` are seeded** with `statement_line` = `Balance
  Sheet / <line>`. Do NOT use `Balance Sheet / Suspense` for them — 1010 is not
  suspense, and that label would invite a future reader to treat it as one.
  `doc-03 §3.2` has the impact note.
- **DEF-009 = acceptance-harness absence** (`docs/28` is authoritative). The
  data-quality-score defect was renumbered **DEF-021**.
- **DEC-046 duplicate → renumbered DEC-054**, traced into `docs/20 §6.6`.
- **GATE-13 remains Pending.** Sample-data rehearsal ran 2026-10-03; real-data
  tie-out outstanding.

## OPEN DEFECTS

| id | what | status |
|---|---|---|
| DEF-012 | doc-14 §4 TST-* catalogue severed (244 ids untagged) | OPEN |
| DEF-018 | PPT exporter never reads its template; ERR-EXP-014 absent | OPEN |
| DEF-022 | doc-integrity gate: `scripts/check_doc_integrity.py` **does not exist** | OPEN, never started |
| DEF-029 | regression test for the 404→500 handler regression | OPEN |

**New finding, unfiled: `DEF-013` is NOT in `docs/28`.** It appears only in
`evidence/`, `docs/OPEN_QUESTIONS_AND_DOUBTS_DETAILED.md` and
`evidence/s1_consolidated_register.md`. A defect with a mutation-verified
regression test (`tests/unit/test_def013_guard_vacuous_asserts.py`) is missing
from the authoritative log — so it cannot be governed, tracked, or seen by
whoever picks up the handoff. This is exactly the DEF-020 failure mode recurring.
Register it, or state precisely why it should not be. (`DEF-020` is correctly
absent — it was a renumbering task, not a defect.)

## CLOSED THIS SESSION — with evidence

| id | root cause | proof |
|---|---|---|
| DEF-024 | `evaluate_all_rules` had no error handling; one rule crashing killed all 19 — total loss of the exception screen | `tools/mut024.py` 5/5 caught |
| DEF-026 | `1010`/`1200`/`2000` absent from `DimAccount`; EXC-002 fired on ~125,000 legitimate offsetting legs | 4/4 mutations caught |
| DEF-027 | E2E journey green but mislabelled — claimed `ERR-VAL-001`, asserted `ERR-API-401` | 2/2 mutations caught |
| DEF-028 | `1020` (499 bank-ledger rows) absent from `DimAccount` | seeded, suite green |
| DEF-029 | Stacked `StarletteHTTPException` handler called `exc.errors()`, which `HTTPException` lacks → every 404 became 500 | 1/1 mutation caught |

DEF-024 implementation, in `app/engine/rules/batch.py`:
`evaluate_all_rules_detailed()` records `status=error` with exception type and
message and CONTINUES; doc-06 §2.9 disable-with-notice via `REQUIRED_INPUTS`;
`evaluate_all_rules` delegates so there is one implementation.
The critical case is the **fake fix** — `except Exception: pass` still returns all
healthy findings, so it converts a visible crash into invisible partial coverage.
A test exists specifically to kill it.

## KNOWN TRAPS

- **`tests/integration/test_dim_account_integrity.py` hardcodes
  `C:\Users\Tahir\...`.** Non-portable. Confirm whether it silently SKIPS rather
  than fails — a silent skip is worse than a failure.
- **Catalog-vs-engine rule ID offset.** `5999-TEMP` is planted as catalog
  `EXC-004` but the engine runs `evaluate_exc_002`. This silently moved recall
  25.0% → 9.4%. **Nobody has yet enumerated every other plant with this offset.**
  If several are mislabelled, every recall/precision figure is wrong. This is the
  highest-value unverified item on the board.
- **Frontend GAP-3 (unfixed).** `Number()` on JSON money in `ui/src`
  (`BvaMatrixTable.tsx`, `DrillModal.tsx`). Likely larger exposure than the
  backend float bugs. Money is Decimal; **AI never computes money.**
- **`scripts/build.py` stops before step 8.** `SHA256SUMS-0.1.0.txt` missing,
  portable zip stuck as `.tmp`. Three docs cite the missing file. Automation
  exists (`sha256_of`, `write_checksums`) so this is a control-flow failure.
- **15 `.xlsx` excluded from the corpus fingerprint** — openpyxl embeds wall-clock
  `dcterms:created`. Documented, not worked around.
- Message transport is unreliable: `team_send_message` drops messages after 3
  attempts and PAUSES the teammate. Use `team_interrupt_agent`. Keep messages
  short; long ones correlate with drops.

## OWNER DECISIONS STILL UNANSWERED

1. Build the budget loader / keep vendor-keyed rules out of v1? (loader unlocks 4
   rules; paths exist)
2. Accept an unsigned pilot with a documented SmartScreen walkthrough?

## TEAM STATE

Lead: OpenCode (`01a0fc81-81e2-7d53-bd41-6f2666466da4`). Roster was 11, six were
removed mid-session; three teammates remain. Tool surface flapped repeatedly and
the CLI fallback returns `TEAM_CLI_ENV_MISSING`, so **if a teammate reports
receiving no work, suspect transport before idleness.**

## FIRST THREE ACTIONS

1. Enumerate every catalog-vs-engine plant offset. If the labels are wrong, every
   acceptance number we would report is wrong.
2. Register `DEF-013` in `docs/28`, or state why not.
3. Swap the corpus and get **real** `doc-14 §5.3` bars. Report them as they are.
