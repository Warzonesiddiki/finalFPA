# Planted-exception acceptance report

**Verdict: FAIL**

- Period: `FY26-P09`  |  as_of (injected, no clock): `2026-11-12`
- Findings raised: 45  |  elapsed: 92.0s
- Measurable: yes
- Harness: doc 14 §5.2, run by `scripts/acceptance`

## Bars (doc 14 §5.3)

| Bar | Requirement | Measured | Result |
|---|---|---|---|
| Planted-exception recall | >= 29 of 32 (>= 90 % of the 32 raises) | 21/32 = 65.6 % | **FAIL** |
| Control precision | 0 of 8 controls may raise | 0 fired | PASS |
| High-severity recall | 18 of 18 High plantings found | 10/18 | **FAIL** |
| Extra findings | a rule with > 3 unexplained findings is tuned or documented before the gate | 24 extra across 7 rule(s); over threshold: ['EXC-017', 'EXC-021', 'EXC-022'] | **FAIL** |
| Stability | two consecutive runs produce identical raise sets | identical | PASS |
| Rule catalog coverage | all 24 catalog rules are wired into the batch composer | 24/24 wired | PASS |
| Zero-coverage rules | every rule with a planted case raises at least one finding | 7 rule(s) with zero coverage | **FAIL** |

## Per-rule recall (doc 14 §5.4)

| Rule | Evaluator | Plantings | Detected | Recall | Controls | Controls fired | Findings | Extras |
|---|---|---|---|---|---|---|---|---|
| EXC-001 **ZERO-COVERAGE** | `evaluate_catalog_exc_001` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-002 **ZERO-COVERAGE** | `evaluate_catalog_exc_002` | 3 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-003 **ZERO-COVERAGE** | `evaluate_catalog_exc_003` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-004 | `evaluate_exc_002` | 2 | 2 | 100.0 % | 0 | 0 | 2 | 0 |
| EXC-005 | `evaluate_exc_003` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-006 | `evaluate_catalog_exc_006` | 1 | 1 | 100.0 % | 0 | 0 | 2 | 1 |
| EXC-007 | `evaluate_exc_001` | 2 | 2 | 100.0 % | 1 | 0 | 2 | 0 |
| EXC-008 | `evaluate_catalog_exc_008` | 1 | 1 | 100.0 % | 1 | 0 | 1 | 0 |
| EXC-009 **ZERO-COVERAGE** | `evaluate_exc_004` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-010 **ZERO-COVERAGE** | `evaluate_exc_010` | 2 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-011 | `evaluate_exc_011` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-012 | `evaluate_exc_005` | 1 | 1 | 100.0 % | 1 | 0 | 1 | 0 |
| EXC-013 **ZERO-COVERAGE** | `evaluate_exc_013` | 2 | 0 | 0.0 % | 1 | 0 | 0 | 0 |
| EXC-014 | `evaluate_exc_014` | 1 | 1 | 100.0 % | 0 | 0 | 2 | 1 |
| EXC-015 | `evaluate_exc_006` | 2 | 2 | 100.0 % | 1 | 0 | 2 | 0 |
| EXC-016 **ZERO-COVERAGE** | `evaluate_exc_016` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-017 | `evaluate_exc_007` | 1 | 1 | 100.0 % | 0 | 0 | 7 | 6 |
| EXC-018 | `evaluate_exc_008` | 1 | 1 | 100.0 % | 2 | 0 | 4 | 3 |
| EXC-019 | `evaluate_exc_019` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-020 | `evaluate_exc_020` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |
| EXC-021 | `evaluate_exc_021` | 2 | 2 | 100.0 % | 1 | 0 | 9 | 7 |
| EXC-022 | `evaluate_exc_022` | 1 | 1 | 100.0 % | 0 | 0 | 5 | 4 |
| EXC-023 | `evaluate_exc_023` | 1 | 1 | 100.0 % | 0 | 0 | 3 | 2 |
| EXC-024 | `evaluate_exc_024` | 1 | 1 | 100.0 % | 0 | 0 | 1 | 0 |

## Controls result (must be 0 of 8)

No control raised.

## Miss list

| Planting | Rule | Severity | Subject key | Notes |
|---|---|---|---|---|
| P1 | EXC-001 | High | `batch_041|bank_ledger` | Unbalanced bank-ledger file loaded under a ₹500 tolerance (variance ₹350.00) |
| P2 | EXC-002 | High | `IN01|VCH-2026-0915-001|1` | Re-export overlaps batch 37 on voucher line 1 |
| P2 | EXC-002 | High | `IN01|VCH-2026-0915-001|2` | Re-export overlaps batch 37 on voucher line 2 |
| P2 | EXC-002 | High | `IN01|VCH-2026-0915-002|1` | Re-export overlaps batch 37 on voucher line 3 |
| P3 | EXC-003 | High | `batch_039|gl_control_total` | Control-total variance: supplied ₹18400000.00 vs loaded ₹18399650.00 |
| P9 | EXC-009 | High | `batch_040|row_00882` | 9 October-dated rows declare source period FY26-P09 |
| P10 | EXC-010 | High | `V-00412|INV-89101` | Document dated 29-Sep posted 05-Oct (potential cut-off issue) |
| P10 | EXC-010 | High | `V-00276|INV-89045` | Document dated 28-Sep posted 03-Oct (potential cut-off issue) |
| P13 | EXC-013 | Medium | `IN01|5600|CC-140` | Spend spike 4.1x trailing 3-month baseline (deviation ₹141000.00) |
| P13 | EXC-013 | Medium | `IN01|6300|CC-120` | Spend spike 3.2x trailing 3-month baseline |
| P16 | EXC-016 | Medium | `IN01|6100|CC-120` | Expected month-end accrual pattern on account 6100 absent in P09 |

## Extra findings (false-positive log reference)

24 extra finding(s) by rule: `{'EXC-017': 6, 'EXC-022': 4, 'EXC-021': 7, 'EXC-018': 3, 'EXC-006': 1, 'EXC-023': 2, 'EXC-014': 1}`

No false-positive log is committed in this repository, so every extra is UNEXPLAINED, not justified.

## Corpus integrity (doc 28 §5.0 criterion 4)

| File | Source type | Gate | Recorded | Rows | Loaded | Debit | Credit | Net | Failed checks | DQ score |
|---|---|---|---|---|---|---|---|---|---|---|
| d365_gl_actuals.csv | actuals_d365 | enforced (doc 04 §12/IMP-023, every source type) | committed | 250482 | 250482 | 15681538388.70 | 15681538388.70 | 0.00 | none | 100 |
| bank_ledger_actuals.csv | actuals_procurement | enforced (doc 04 §12/IMP-023, every source type) | committed | 498 | 498 | 6606745.00 | 6606745.00 | 0.00 | none | 100 |
| payroll_procurement_actuals.csv | actuals_procurement | enforced (doc 04 §12/IMP-023, every source type) | committed | 398 | 398 | 0.00 | 0.00 | 0.00 | none | 100 |

`DQ score` is computed by `calculate_quality_score()` (`DEF-021`); it is no longer the literal 100 that every batch used to report.

## Divergences and stated assumptions

- Answer key row outside P1..P32 and not counted as a planting: INJ-01 EXC-SEC-14 Raised (this is the prompt-injection fixture, not one of the 40).

## Checksum scope (doc 14 §5.2 step 1, amended 2026-10-03)

- Fingerprinted (byte-reproducible): **22 CSV file(s)**.
- Excluded from the fingerprint: **33 `.xlsx` file(s)**.
  - paths are relative to the sample dir; test_scale/ holds a second copy of the template and malformed fixtures and is counted once per distinct path
  - `.xlsx`: openpyxl embeds a wall-clock dcterms:created in docProps/core.xml, so the hash changes on every generation.

  A SHA-256 manifest covering the excluded files would fail by construction, so they are excluded and the exclusion is recorded rather than asserted around. Known limitation; closing it means normalising `dcterms:created` in the generator.

## Stated assumptions

- **Run date.** Doc 14 §5.2 step 2 says only "with default thresholds, every rule enabled" and names no run date. The answer key's P11 note ("Posting on 30-Nov-2026 is 18 days ahead of run date") implies `as_of=2026-11-12`, which is used. No clock is read (doc 06 line 195).
- **Generator checksum.** Doc 14 §5.2 step 1 says the run "asserts the generator's own checksum". `generate_sample_data.py` emits none and none is committed, so checksums are computed and RECORDED as a run-to-run fingerprint, not asserted against a constant. Scope is the CSV corpus only - see the Checksum scope section above for why the 15 `.xlsx` files are excluded.
- **Seed.** Doc 14 §5.2 step 1 was amended 2026-10-03 from `--seed 20260101` to `--seed 42`. The committed corpus was generated at seed 42 and audit New-06 reproduced it byte-exactly; the previously documented seed was never used.
- **CLI name.** Doc 14 §5.2 says "run by `scripts/acceptance`". This repository names scripts with a `.py` suffix (`build.py`, `check.py`), so the entry point is `scripts/acceptance.py`.
