# Planted-exception acceptance report

**Verdict: BLOCKED**

> **The doc 14 §5.3 bars were NOT MEASURED.** The corpus precondition (doc 28 §5.0 entry criterion 4) is not met, so no facts exist for the rules to fire on. The figures in the per-rule table below are printed for diagnosis only and are **not** a §5.3 result. This run is neither a pass nor a rule-logic failure - it is BLOCKED.

- Period: `FY26-P09`  |  as_of (injected, no clock): `2026-11-12`
- Findings raised: 158  |  elapsed: 0.1s
- Measurable: NO - see BLOCKED REASONS
- Harness: doc 14 §5.2, run by `scripts/acceptance`

## BLOCKED REASONS (corpus precondition)

- BLOCKED - doc 28 §5.0 entry criterion 4 ('Sample data corpus (250k rows) loaded and validated') is not met for the general ledger d365_gl_actuals.csv: source_type=actuals_d365, total_debit=24626607267.80, total_credit=6682091688.47, net_imbalance=17944515579.33, is_balanced=False, failing check(s)=IMP-023 of 9 run, data_quality_score=84, and 0 of 250037 parsed rows landed in FactActual. Doc 04 §12 / IMP-023 rejects the file and import_repo.py:111 gates exactly this source_type, so NO facts exist for the rules to fire on. Every planted case lives in this file, so the doc 14 §5.3 bars are NOT MEASURED. This is a corpus precondition failure, not a rule-logic result.

## Bars (doc 14 §5.3)

_Not measured - corpus precondition failed. See BLOCKED REASONS above._

| Bar | Requirement | Measured | Result |
|---|---|---|---|
| Planted-exception recall | >= 29 of 32 (>= 90 % of the 32 raises) | NOT MEASURED | _NOT MEASURED_ |
| Control precision | 0 of 8 controls may raise | NOT MEASURED | _NOT MEASURED_ |
| High-severity recall | 18 of 18 High plantings found | NOT MEASURED | _NOT MEASURED_ |
| Extra findings | a rule with > 3 unexplained findings is tuned or documented before the gate | NOT MEASURED | _NOT MEASURED_ |
| Stability | two consecutive runs produce identical raise sets | NOT MEASURED | _NOT MEASURED_ |
| Rule catalog coverage | all 24 catalog rules are wired into the batch composer | NOT MEASURED | _NOT MEASURED_ |
| Zero-coverage rules | every rule with a planted case raises at least one finding | NOT MEASURED | _NOT MEASURED_ |

## Per-rule recall (doc 14 §5.4) - DIAGNOSTIC ONLY, NOT A BAR RESULT

## Per-rule recall (doc 14 §5.4)

| Rule | Evaluator | Plantings | Detected | Recall | Controls | Controls fired | Findings | Extras |
|---|---|---|---|---|---|---|---|---|
| EXC-001 **ZERO-COVERAGE** | `evaluate_exc_001` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-002 **ZERO-COVERAGE** | `evaluate_exc_002` | 3 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-003 **ZERO-COVERAGE** | `evaluate_exc_003` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-004 **ZERO-COVERAGE** | `evaluate_exc_004` | 2 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-005 **ZERO-COVERAGE** | `evaluate_exc_005` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-006 **ZERO-COVERAGE** | `evaluate_exc_006` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-007 **ZERO-COVERAGE** | `evaluate_exc_007` | 2 | 0 | 0.0 % | 1 | 0 | 0 | 0 |
| EXC-008 **ZERO-COVERAGE** | `evaluate_exc_008` | 1 | 0 | 0.0 % | 1 | 0 | 0 | 0 |
| EXC-009 **ZERO-COVERAGE** | `evaluate_exc_004` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-010 **ZERO-COVERAGE** | `evaluate_exc_010` | 2 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-011 **ZERO-COVERAGE** | `evaluate_exc_011` | 1 | 0 | 0.0 % | 0 | 0 | 103 | 71 |
| EXC-012 **ZERO-COVERAGE** | `evaluate_exc_005` | 1 | 0 | 0.0 % | 1 | 0 | 0 | 0 |
| EXC-013 **ZERO-COVERAGE** | `evaluate_exc_013` | 2 | 0 | 0.0 % | 1 | 0 | 0 | 0 |
| EXC-014 **ZERO-COVERAGE** | `evaluate_exc_014` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-015 | `evaluate_exc_006` | 2 | 2 | 100.0 % | 1 | 1 | 3 | 0 |
| EXC-016 **ZERO-COVERAGE** | `evaluate_exc_016` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-017 **ZERO-COVERAGE** | `evaluate_exc_007` | 1 | 0 | 0.0 % | 0 | 0 | 1 | 1 |
| EXC-018 | `evaluate_exc_008` | 1 | 1 | 100.0 % | 2 | 1 | 50 | 48 |
| EXC-019 **ZERO-COVERAGE** | `evaluate_exc_019` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-020 **ZERO-COVERAGE** | `evaluate_exc_020` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-021 **ZERO-COVERAGE** | `evaluate_exc_021` | 2 | 0 | 0.0 % | 1 | 0 | 0 | 0 |
| EXC-022 **ZERO-COVERAGE** | `evaluate_exc_022` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |
| EXC-023 **ZERO-COVERAGE** | `evaluate_exc_023` | 1 | 0 | 0.0 % | 0 | 0 | 1 | 1 |
| EXC-024 **ZERO-COVERAGE** | `evaluate_exc_024` | 1 | 0 | 0.0 % | 0 | 0 | 0 | 0 |

## Controls result (must be 0 of 8)

| Planting | Rule | Subject key | Notes |
|---|---|---|---|
| P32 | EXC-015 | `V-00118|Security_Services` | Precision control: recurring charge posted within 10% tolerance (8% below expected) |
| P30 | EXC-018 | `IN01|5200|CC-110` | Precision control: F13c ₹900000 variance but +2.25% is below 5.0% threshold (AND-test fails) |

## Miss list

| Planting | Rule | Severity | Subject key | Notes |
|---|---|---|---|---|
| P1 | EXC-001 | High | `batch_041|bank_ledger` | Unbalanced bank-ledger file loaded under a ₹500 tolerance (variance ₹350.00) |
| P2 | EXC-002 | High | `IN01|VCH-2026-0915-001|1` | Re-export overlaps batch 37 on voucher line 1 |
| P2 | EXC-002 | High | `IN01|VCH-2026-0915-001|2` | Re-export overlaps batch 37 on voucher line 2 |
| P2 | EXC-002 | High | `IN01|VCH-2026-0915-002|1` | Re-export overlaps batch 37 on voucher line 3 |
| P3 | EXC-003 | High | `batch_039|gl_control_total` | Control-total variance: supplied ₹18400000.00 vs loaded ₹18399650.00 |
| P4 | EXC-004 | Medium | `account|5999-TEMP` | 6 rows post to unmapped placeholder account 5999-TEMP |
| P4 | EXC-004 | Medium | `cost_center|CC-999` | Cost centre CC-999 appears in 2 rows with no master record |
| P5 | EXC-005 | Low | `cost_center|CC-950` | CC-950 (marked inactive from FY26-P06) receives 4 postings in P09 |
| P6 | EXC-006 | Medium | `entity|IN02` | Entity IN02 has ₹450000.00 YTD actuals and no FY26 budget lines |
| P7 | EXC-007 | High | `V-00931|INV-88213` | Duplicate invoice INV-88213 posted on 14-Sep and 18-Sep |
| P7 | EXC-007 | High | `V-00412|INV-91004` | Duplicate invoice INV-91004 posted on 20-Sep and 24-Sep |
| P8 | EXC-008 | Medium | `IN01|5300|2026-09-22|12500.00` | Same ₹12500.00 debit in vouchers VCH-007 and VCH-009 |
| P9 | EXC-009 | High | `batch_040|row_00882` | 9 October-dated rows declare source period FY26-P09 |
| P10 | EXC-010 | High | `V-00412|INV-89101` | Document dated 29-Sep posted 05-Oct (potential cut-off issue) |
| P10 | EXC-010 | High | `V-00276|INV-89045` | Document dated 28-Sep posted 03-Oct (potential cut-off issue) |
| P11 | EXC-011 | Medium | `IN01|VCH-2026-0930-021` | Posting on 30-Nov-2026 is 18 days ahead of run date |
| P12 | EXC-012 | Medium | `IN01|5400|CC-110` | Unusual negative expense credits ₹680000.00 offset only ₹120000.00 (17.6%) |
| P13 | EXC-013 | Medium | `IN01|5600|CC-140` | Spend spike 4.1x trailing 3-month baseline (deviation ₹141000.00) |
| P13 | EXC-013 | Medium | `IN01|6300|CC-120` | Spend spike 3.2x trailing 3-month baseline |
| P14 | EXC-014 | Medium | `V-00276|5800` | Salary vendor V-00276 posts to never-used Marketing account 5800 |
| P16 | EXC-016 | Medium | `IN01|6100|CC-120` | Expected month-end accrual pattern on account 6100 absent in P09 |
| P17 | EXC-017 | High | `IN01|5450|CC-160` | New cost centre CC-160 has ₹840000.00 spend with zero FY26 budget line |
| P19 | EXC-019 | Medium | `IN01|5500|CC-130` | Cumulative spend at 88% annual budget by P09 with YTD +14.3% overrun |
| P20 | EXC-020 | Medium | `IN01|5450|P07-P09` | Budget coverage gap: budget exists P01-P06 but missing P07-P09 |
| P21 | EXC-021 | High | `IN01|VCH-2026-0920-004` | Single voucher ₹650000.00 crosses single approval threshold (₹500000.00) |
| P21 | EXC-021 | High | `IN01|VCH-2026-0925-003` | Single voucher ₹2750000.00 crosses dual approval threshold (₹2500000.00) |
| P22 | EXC-022 | Low | `IN01|VCH-2026-0929-014` | Round manual journal ₹1500000.00 at 3.6x entity mean round journal |
| P23 | EXC-023 | High | `IN01|VCH-2026-0912-004` | Voucher imbalance: debits ₹45000.00 vs credits ₹40000.00 (difference ₹5000.00) |
| P24 | EXC-024 | High | `IN01|1999|suspense` | Suspense account residual ₹1240000.00 with ₹980000.00 unsettled movement |

## Extra findings (false-positive log reference)

121 extra finding(s) by rule: `{'EXC-018': 48, 'EXC-011': 71, 'EXC-017': 1, 'EXC-023': 1}`

No false-positive log is committed in this repository, so every extra is UNEXPLAINED, not justified.

## Corpus integrity (doc 28 §5.0 criterion 4)

| File | Source type | Gate | Recorded | Rows | Loaded | Debit | Credit | Net | Failed checks | DQ score |
|---|---|---|---|---|---|---|---|---|---|---|
| d365_gl_actuals.csv | actuals_d365 | enforced (doc 04 §12/IMP-023) | rejected | 250037 | 250037 | 24626607267.80 | 6682091688.47 | 17944515579.33 | IMP-023 | 84 |
| bank_ledger_actuals.csv | actuals_procurement | WARNING-ONLY in code (doc 04 §12 says reject) | rejected | 499 | 499 | 7997971.00 | 4855017.00 | 3142954.00 | IMP-023 | 84 |
| payroll_procurement_actuals.csv | actuals_procurement | WARNING-ONLY in code (doc 04 §12 says reject) | rejected | 399 | 399 | 17146821.00 | 0.00 | 17146821.00 | IMP-023 | 84 |

`DQ score` is computed by `calculate_quality_score()` (`DEF-021`); it is no longer the literal 100 that every batch used to report.

## Divergences and stated assumptions

- Answer key row outside P1..P32 and not counted as a planting: INJ-01 EXC-SEC-14 Raised (this is the prompt-injection fixture, not one of the 40).
- Sub-ledger bank_ledger_actuals.csv is unbalanced (net=3142954.00, failing check(s)=IMP-023) yet 499 of 499 parsed rows landed in FactActual. Doc 04 §12 and IMP-023 state the reject unconditionally; import_repo.py:111 gates only source_type='actuals_d365' and its comment cites '04 §2.2 & §10', which are the source-type table and the confirm step and state no sub-ledger exemption. The batch row is also RECORDED as status='rejected' from is_balanced alone, so the audit metadata disagrees with the analytic store. Not scored as a blocker here; owner ruling required (DEF-010).
- Sub-ledger payroll_procurement_actuals.csv is unbalanced (net=17146821.00, failing check(s)=IMP-023) yet 399 of 399 parsed rows landed in FactActual. Doc 04 §12 and IMP-023 state the reject unconditionally; import_repo.py:111 gates only source_type='actuals_d365' and its comment cites '04 §2.2 & §10', which are the source-type table and the confirm step and state no sub-ledger exemption. The batch row is also RECORDED as status='rejected' from is_balanced alone, so the audit metadata disagrees with the analytic store. Not scored as a blocker here; owner ruling required (DEF-010).

## Checksum scope (doc 14 §5.2 step 1, amended 2026-10-03)

- Fingerprinted (byte-reproducible): **19 CSV file(s)**.
- Excluded from the fingerprint: **32 `.xlsx` file(s)**.
  - paths are relative to the sample dir; test_scale/ holds a second copy of the template and malformed fixtures and is counted once per distinct path
  - `.xlsx`: openpyxl embeds a wall-clock dcterms:created in docProps/core.xml, so the hash changes on every generation.

  A SHA-256 manifest covering the excluded files would fail by construction, so they are excluded and the exclusion is recorded rather than asserted around. Known limitation; closing it means normalising `dcterms:created` in the generator.

## Stated assumptions

- **Run date.** Doc 14 §5.2 step 2 says only "with default thresholds, every rule enabled" and names no run date. The answer key's P11 note ("Posting on 30-Nov-2026 is 18 days ahead of run date") implies `as_of=2026-11-12`, which is used. No clock is read (doc 06 line 195).
- **Generator checksum.** Doc 14 §5.2 step 1 says the run "asserts the generator's own checksum". `generate_sample_data.py` emits none and none is committed, so checksums are computed and RECORDED as a run-to-run fingerprint, not asserted against a constant. Scope is the CSV corpus only - see the Checksum scope section above for why the 15 `.xlsx` files are excluded.
- **Seed.** Doc 14 §5.2 step 1 was amended 2026-10-03 from `--seed 20260101` to `--seed 42`. The committed corpus was generated at seed 42 and audit New-06 reproduced it byte-exactly; the previously documented seed was never used.
- **CLI name.** Doc 14 §5.2 says "run by `scripts/acceptance`". This repository names scripts with a `.py` suffix (`build.py`, `check.py`), so the entry point is `scripts/acceptance.py`.
