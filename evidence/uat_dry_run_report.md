# UAT Dry-Run Rehearsal Report (TST-UAT-01..06)

**Document Reference**: `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §5.2, `docs/14_TESTING_QA_PLAN.md` §12.4  
**Date**: 2026-10-03  
**Auditor / Role**: AionCLI-02 (FP&A Lead Analyst simulation)  
**Execution Context**: Hermetic sample project workspace (`FY26-P09` / `IN01`)  
**Scope**: 6 UAT Acceptance Scripts (`TST-UAT-01` through `TST-UAT-06`)  
**Status**: **ALL 6 SCRIPTS PASSED (100%)**  
**Disclaimer**: **INTERNAL DRY-RUN REHEARSAL ONLY — NO CLIENT SIGN-OFF**  

---

## 1. Executive Summary

As required by **Doc 28 §5.2** and **Doc 14 §12.4**, this UAT dry-run rehearses the complete end-user acceptance sequence against the sample project prior to client-attended UAT (`GATE-14`). The simulated analyst reproduced one month's manual Budget vs. Actual (BvA) in the application, generated both the Excel management pack and PowerPoint presentation deck, and performed a strict tie-out diffing the engine authority against exported artifacts and baseline expectations.

### Consolidated Result: **6 / 6 SCRIPTS PASSED (100%)**
- **TST-UAT-01 (Manual BvA Reproduction)**: **PASS** (Numerical diff: `0.00` across all accounts)
- **TST-UAT-02 (Tie-Out Worksheet & PPT Parity)**: **PASS** (Cross-artifact diff: `0.00`; 0 classified divergences)
- **TST-UAT-03 (Exception Wording & Verdicts Review)**: **PASS** (Zero misleading findings / `0` S1/S2 defects)
- **TST-UAT-04 (Training Walkthrough via Doc 22)**: **PASS** (All month-end tasks `T-01` through `T-21` verified)
- **TST-UAT-05 (Cold-Start Client Pass)**: **PASS** (Clean filesystem bootstrap initialized all tables without prior state)
- **TST-UAT-06 (Go-Live Rehearsal Deliverables)**: **PASS** (All release governance, roster, runbook, and manifest artifacts verified)

---

## 2. Per-Script Findings & Evidence

### 2.1 TST-UAT-01: Manual BvA Reproduction
- Reproduced period: `FY26-P09` (March 2026) for entity `IN01`.
- Account 4000 (Revenue): 12,500,000.00 INR vs Budget 12,000,000.00 INR (Diff: 0.00).
- Account 5100 (Salaries & Wages): 5,200,000.00 INR vs Budget 5,000,000.00 INR (Diff: 0.00).
- Account 5500 (Software Subscriptions): 1,600,000.00 INR vs Budget 1,500,000.00 INR (Diff: 0.00).
- Net EBITDA impact: 5,700,000.00 INR (Diff: 0.00).
- Detailed diff register: [`uat_bva_diffs.md`](uat_bva_diffs.md).

### 2.2 TST-UAT-02: Tie-Out Worksheet & PPT Parity
- Generated `Management_Pack_UAT_FY26-P09.xlsx` and `Management_Deck_UAT_FY26-P09.pptx`.
- Complete cross-artifact match between openpyxl and python-pptx outputs: exact `0.00` difference.
- Difference classification per Doc 28 §4.3: Spec bug: 0; Mapping error: 0; Client data: 0; Rounding: 0.00.
- Detailed cross-artifact report: [`uat_deck_parity.md`](uat_deck_parity.md).

### 2.3 TST-UAT-03: Exception Wording and Verdicts
- Exception engine audited across all active rules (Doc 10 catalog).
- All explanations are deterministic, referencing exact thresholds and account codes.
- Zero misleading findings; 0 S1/S2 issues.

### 2.4 TST-UAT-04: Training Walkthrough via Doc 22
- Validated that month-end workflow tasks T-01 through T-21 in `docs/22_END_USER_GUIDE.md` map to application screens.
- Confirmed screen flow: Workspace -> Ingestion -> Reconcile -> BvA -> Exceptions -> Forecast -> Export -> Close.

### 2.5 TST-UAT-05: Cold-Start Client Pass
- Fresh directory initialization bootstrapped schemas cleanly in < 1.8s.
- 11 analytical tables verified operational in DuckDB and SQLite.

### 2.6 TST-UAT-06: Go-Live Rehearsal Deliverables
- Confirmed existence and readiness of all 5 operational artifacts:
  1. `packaging/named_hypercare_roster.md`
  2. `packaging/fallback_execution_runbook.md`
  3. `packaging/client_delivery_package_manifest.md`
  4. `packaging/prefilled_sign_off_records.md`
  5. `packaging/nightly_e2e_runbook.md`

---

## 3. Test Evidence References

- **Automated Pytest Suite**: `tests/uat/test_uat_dry_run.py` (6 passed in 3.38s)
- **CLI Rehearsal Runner**: `scripts/run_uat_dry_run.py`
- **Full Execution Transcript**: [`uat_dry_run_transcript.md`](uat_dry_run_transcript.md)
- **BvA Diff Register**: [`uat_bva_diffs.md`](uat_bva_diffs.md)
- **Deck Parity Report**: [`uat_deck_parity.md`](uat_deck_parity.md)

---

## 4. Acceptance Status

**INTERNAL DRY-RUN REHEARSAL ONLY**. Client sign-off (`GATE-14`) will take place during the scheduled pilot review session upon delivery of sanitized real-month files (`OQ-014`) or approved fallback execution.
