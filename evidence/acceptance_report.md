# Planted-exception acceptance report

**Verdict: PASS**

- Period: `FY26-P09`  |  as_of (injected, no clock): `2026-11-12`
- Findings raised: 50  |  elapsed: 23.8s
- Measurable: yes
- Harness: doc 14 §5.2, run by `scripts/acceptance`

## Bars (doc 14 §5.3)

| Bar | Requirement | Measured | Result |
|---|---|---|---|
| Planted-exception recall | >= 29 of 32 (>= 90 % of the 32 raises) | 32/32 = 100.0 % | PASS |
| Control precision | 0 of 8 controls may raise | 0 fired | PASS |
| High-severity recall | 18 of 18 High plantings found | 18/18 | PASS |
| Extra findings | a rule with > 3 unexplained findings is tuned or documented before the gate | 17 extra across 9 rule(s); over threshold: none | PASS |
| Stability | two consecutive runs produce identical raise sets | identical | PASS |
| Rule catalog coverage | all 24 catalog rules are wired into the batch composer | 24/24 wired | PASS |
| Zero-coverage rules | every rule with a planted case raises at least one finding | 0 rule(s) with zero coverage | PASS |

## Per-rule recall (doc 14 §5.4)

| Rule | Evaluator | Plantings | Detected | Recall | Controls | Controls fired | Findings | Extras |
|---|---|---|---|---|---|---|---|---|
| EXC-001 | `evaluate_catalog_exc_001` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-002 | `evaluate_catalog_exc_002` | 3 | 3 | 100.0 % | 0 | 0 | 4 | 1 |
| EXC-003 | `evaluate_catalog_exc_003` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-004 | `evaluate_exc_002` | 2 | 2 | 100.0 % | 0 | 0 | 2 | 0 |
| EXC-005 | `evaluate_exc_003` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-006 | `evaluate_catalog_exc_006` | 1 | 1 | 100.0 % | 0 | 0 | 2 | 1 |
| EXC-007 | `evaluate_exc_001` | 2 | 2 | 100.0 % | 1 | 0 | 5 | 2 |
| EXC-008 | `evaluate_catalog_exc_008` | 1 | 1 | 100.0 % | 1 | 0 | 1 | 0 |
| EXC-009 | `evaluate_exc_004` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-010 | `evaluate_exc_010` | 2 | 2 | 100.0 % | 0 | 0 | 2 | 0 |
| EXC-011 | `evaluate_exc_011` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-012 | `evaluate_exc_005` | 1 | 1 | 100.0 % | 1 | 0 | 1 | 0 |
| EXC-013 | `evaluate_exc_013` | 2 | 2 | 100.0 % | 1 | 0 | 2 | 0 |
| EXC-014 | `evaluate_exc_014` | 1 | 1 | 100.0 % | 0 | 0 | 4 | 3 |
| EXC-015 | `evaluate_exc_006` | 2 | 2 | 100.0 % | 1 | 0 | 2 | 0 |
| EXC-016 | `evaluate_exc_016` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-017 | `evaluate_exc_007` | 1 | 1 | 100.0 % | 0 | 0 | 2 | 1 |
| EXC-018 | `evaluate_exc_008` | 1 | 1 | 100.0 % | 2 | 0 | 3 | 2 |
| EXC-019 | `evaluate_exc_019` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-020 | `evaluate_exc_020` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-021 | `evaluate_exc_021` | 2 | 2 | 100.0 % | 1 | 0 | 5 | 3 |
| EXC-022 | `evaluate_exc_022` | 1 | 1 | 100.0 % | 0 | 0 | 3 | 2 |
| EXC-023 | `evaluate_exc_023` | 1 | 1 | 100.0 % | 0 | 0 | 3 | 2 |
| EXC-024 | `evaluate_exc_024` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |

## Controls result (must be 0 of 8)

No control raised.

## Miss list

None.

## Extra findings (false-positive log reference)

17 extra finding(s) by rule: `{'EXC-002': 1, 'EXC-006': 1, 'EXC-007': 2, 'EXC-014': 3, 'EXC-017': 1, 'EXC-018': 2, 'EXC-021': 3, 'EXC-022': 2, 'EXC-023': 2}`

No false-positive log is committed in this repository, so every extra is UNEXPLAINED, not justified.

## Corpus integrity (doc 28 §5.0 criterion 4)

| File | Source type | Gate | Recorded | Rows | Loaded | Debit | Credit | Net | Failed checks | DQ score |
|---|---|---|---|---|---|---|---|---|---|---|
| import_history/01_bank_batch_037.csv | actuals_d365 | journal exact debit=credit (04 §12/IMP-023) | committed | 4 | 4 | 95500.00 | 95500.00 | 0.00 | none | 100 |
| import_history/02_gl_batch_039.xlsx | actuals_d365 | journal exact debit=credit (04 §12/IMP-023) | committed | 110 | 110 | 18399650.00 | 18399650.00 | 0.00 | none | 93 |
| d365_gl_actuals.csv | actuals_d365 | journal exact debit=credit (04 §12/IMP-023) | committed | 250503 | 250503 | 15672231601.81 | 15672231601.81 | 0.00 | none | 100 |
| bank_ledger_actuals.csv | actuals_procurement | sub-ledger net reconciliation (DEC-056/IMP-023; tolerance ₹500.00) | committed | 498 | 498 | 6606745.00 | 6606745.00 | 0.00 | none | 100 |
| payroll_procurement_actuals.csv | actuals_procurement | sub-ledger net reconciliation (DEC-056/IMP-023; tolerance ₹500.00) | committed | 398 | 398 | 0.00 | 0.00 | 0.00 | none | 100 |
| import_history/03_bank_batch_040.csv | actuals_procurement | sub-ledger net reconciliation (DEC-056/IMP-023; tolerance ₹500.00) | committed | 10 | 10 | 743400.00 | 743400.00 | 0.00 | none | 100 |
| import_history/04_bank_batch_041.csv | actuals_procurement | sub-ledger net reconciliation (DEC-056/IMP-023; tolerance ₹500.00) | committed | 2 | 2 | 1000000.00 | 999650.00 | 350.00 | none | 92 |

`DQ score` is computed by `calculate_quality_score()` (`DEF-021`); it is no longer the literal 100 that every batch used to report.

## Divergences and stated assumptions

- Answer key row outside P1..P32 and not counted as a planting: INJ-01 EXC-SEC-14 Raised (this is the prompt-injection fixture, not one of the 40).

## Checksum scope (doc 14 §5.2 step 1, amended 2026-10-06)

- Fingerprinted: **56 data artefact(s)** across `.csv`, `.json`, `.xlsx`.
  SHA-256 values, keyed by relative path, are included in `acceptance_report.json` under `checksum_scope.sha256`.
- Excluded: **0 recognized data artefact(s)**.
  - paths are relative to the sample dir; test_scale/ holds second copies of templates and malformed fixtures, counted as separate paths; the history acceptance sidecar is included

## Stated assumptions

- **Run date.** Doc 14 §5.2 step 2 says only "with default thresholds, every rule enabled" and names no run date. The answer key's P11 note ("Posting on 30-Nov-2026 is 18 days ahead of run date") implies `as_of=2026-11-12`, which is used. No clock is read (doc 06 line 195).
- **Generator checksum.** The report records the actual SHA-256 of each recognized corpus data artifact and does not assert against a committed golden digest, because no canonical manifest is committed. The generator reproducibility test is separate; a recorded fingerprint is not a claim that this acceptance run regenerated the data.
- **Seed.** Doc 14 §5.2 step 1 was amended 2026-10-03 from `--seed 20260101` to `--seed 42`. The committed corpus was generated at seed 42 and audit New-06 reproduced it byte-exactly; the previously documented seed was never used.
- **CLI name.** Doc 14 §5.2 says "run by `scripts/acceptance`". This repository names scripts with a `.py` suffix (`build.py`, `check.py`), so the entry point is `scripts/acceptance.py`.
