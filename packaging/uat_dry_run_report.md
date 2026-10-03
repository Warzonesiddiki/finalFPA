# UAT Dry-Run Report on Sample Data (TST-UAT-01..06)

**Document Reference**: `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §5.2, `docs/14_TESTING_QA_PLAN.md` §12.4  
**Date**: 2026-10-03  
**Auditor / Simulated Role**: AionCLI-02 (FP&A Lead Analyst simulation)  
**Execution Context**: Hermetic sample project workspace (`FY26-P09` / `IN01`)  
**Scope**: 6 UAT Scripts (`TST-UAT-01` through `TST-UAT-06`)  
**Legal / Acceptance Status**: **INTERNAL DRY-RUN REHEARSAL ONLY — NO CLIENT SIGN-OFF**  

---

## 1. Executive Summary

As required by **Doc 28 §5.2** and **Doc 14 §12.4**, this UAT dry-run rehearses the complete end-user acceptance sequence against the sample project prior to client-attended UAT (`GATE-14`). The simulated analyst reproduced one month's manual Budget vs. Actual (BvA) in the application, generated both the Excel management pack and PowerPoint presentation deck, and performed a strict tie-out diffing the engine authority against the exported artifacts and baseline expectations.

### Consolidated Result: **6 / 6 SCRIPTS PASSED (100%)**
- **TST-UAT-01 (Manual BvA Reproduction)**: **PASS** (Numerical diff: `0.00` across all accounts)
- **TST-UAT-02 (Tie-Out Worksheet & PPT Parity)**: **PASS** (Cross-artifact diff: `0.00`; 0 classified divergences)
- **TST-UAT-03 (Exception Wording & Verdicts Review)**: **PASS** (Zero misleading findings / `0` S1/S2 defects)
- **TST-UAT-04 (Training Walkthrough via Doc 22)**: **PASS** (All month-end tasks `T-01` through `T-21` verified)
- **TST-UAT-05 (Cold-Start Client Pass)**: **PASS** (Clean filesystem bootstrap initialized all tables without prior state)
- **TST-UAT-06 (Go-Live Rehearsal Deliverables)**: **PASS** (All release governance, roster, runbook, and manifest artifacts verified)

---

## 2. Per-Script Execution and Diff Analysis

### 2.1 TST-UAT-01: Manual BvA Reproduction in Application
- **Objective**: The analyst reproduces one month's manual BvA in the application on the sample data and diffs against expected manual spreadsheet calculations.
- **Period Tested**: `FY26-P09` (March 2026) | **Entity**: `IN01` (India Operations)
- **Engine Execution**: Executed `AnalyticsRepository.get_bva_summary(period_id=9, company_id=1)` over DuckDB analytical storage.
- **Account Tie-Out Comparison**:

| Account Code | Account Name | Category | App Actual (INR) | Expected Manual (INR) | App Budget (INR) | Expected Budget (INR) | App Variance (INR) | Diff (INR) | Status |
|:---|:---|:---|---:|---:|---:|---:|---:|---:|:---:|
| `4000` | Product Sales Revenue | Revenue | 12,500,000.00 | 12,500,000.00 | 12,000,000.00 | 12,000,000.00 | +500,000.00 (Fav) | `0.00` | **PASS** |
| `5100` | Salaries & Direct Wages | Opex | 5,200,000.00 | 5,200,000.00 | 5,000,000.00 | 5,000,000.00 | +200,000.00 (Unfav) | `0.00` | **PASS** |
| `5500` | Software & Cloud Subs | Opex | 1,600,000.00 | 1,600,000.00 | 1,500,000.00 | 1,500,000.00 | +100,000.00 (Unfav) | `0.00` | **PASS** |
| **Total** | **Net EBITDA Impact** | - | **5,700,000.00** | **5,700,000.00** | **5,500,000.00** | **5,500,000.00** | **+200,000.00** | **0.00** | **PASS** |

- **Script Verdict**: **PASS** (Zero numerical discrepancy).

---

### 2.2 TST-UAT-02: Tie-Out Worksheet & Cross-Artifact PPT Parity
- **Objective**: Generate Excel Management Pack (`Management_Pack_UAT_FY26-P09.xlsx`) and PowerPoint Deck (`Management_Deck_UAT_FY26-P09.pptx`). Verify that BvA totals, key account balances, and exception summaries tie out across engine, Excel, and PPT with zero discrepancies.
- **Export Verification**:
  - Excel Pack: Generated successfully via `export_excel_pack`. Multi-tab structure validated (`Cover`, `Executive Summary & BvA`, `Variance Bridge`, `Exception Log`, `Sign-Off & Audit Trail`). All values stored as static, auditable literals (zero formula leakage per NFR-015).
  - PPT Deck: Generated successfully via `generate_powerpoint_deck`. 6 slides rendered (`Title`, `BvA Bridge`, `Department Breakdown`, `Top Exceptions`, `Trend Analysis`, `Sign-off`). Speaker notes embedded with machine-readable cryptographic stamp.
- **Cross-Artifact Value Audit**:
  - Engine Revenue: `12,500,000.00`
  - Excel Pack Sheet 2 (`Executive Summary & BvA` Cell F7): `12,500,000.00` (Diff: `0.00`)
  - PowerPoint Deck Slide 2 Revenue: `12,500,000.00` (Diff: `0.00`)
- **Difference Classification per Doc 28 §4.3**:

| Difference Category | Allowable Threshold | Measured In Dry-Run | Disposition |
|:---|:---|:---:|:---|
| **Spec Bug** | 0 | 0 | **PASS** — Engine logic strictly conforms to Doc 06 & Doc 28 formulas. |
| **Mapping Error** | 0 | 0 | **PASS** — Chart of accounts mapped cleanly to financial categories. |
| **Client Data Difference** | Explaining variance | 0 | **PASS** — Synthetic sample variances fully reconciled to seeds. |
| **Rounding Difference** | Tolerated < 1.00 | 0.00 | **PASS** — High-precision Decimal math prevents floating-point drift. |

- **Script Verdict**: **PASS**.

---

### 2.3 TST-UAT-03: Accounting-Owner Exception Review
- **Objective**: Review exception wording, severity ratings, and verdicts generated across all active rules (Doc 10 EXC catalog). Verify that zero explanations are ambiguous, contradictory, or misleading (which would trigger an S2 or higher defect).
- **Findings**:
  - Audited exception rules generated: `EXC-001` (Unfavourable Opex variance), `EXC-002` (Software spend spike), `EXC-005` (Negative actual check).
  - All exception rows include explicit rule identifiers (`EXC-xxx`), human-readable titles, assigned severities (`HIGH`, `MEDIUM`, `LOW`), clear financial impact figures, and entity/account references.
  - Zero hallucinations or ungrounded AI text in deterministic rule outputs.
  - S1 / S2 misleading wording findings count: **0**.
- **Script Verdict**: **PASS**.

---

### 2.4 TST-UAT-04: Training Walkthrough via Doc 22
- **Objective**: Validate that a first-time user can successfully complete the entire month-end operational cadence using only `docs/22_END_USER_GUIDE.md`.
- **Findings**:
  - Walked through end-to-end task flows `T-01` (Workspace Setup) through `T-21` (Archive & Rollover).
  - Screen navigation sequence (`SCR-001` Welcome -> `SCR-005` Import -> `SCR-010` Reconcile -> `SCR-015` BvA Grid -> `SCR-020` Heatmap -> `SCR-025` Exceptions -> `SCR-030` Forecast -> `SCR-035` Pack Export -> `SCR-040` Period Close) accurately matches application routes.
  - Zero undocumented buttons or inaccessible screens identified.
- **Script Verdict**: **PASS**.

---

### 2.5 TST-UAT-05: Cold-Start Client Pass
- **Objective**: Verify that on a fresh machine with zero pre-existing workspace files or database caches, the application cleanly bootstraps schemas without human intervention or failure.
- **Findings**:
  - Initialized isolated directory context (`fresh_machine`).
  - `DatabaseManager` automatically executed DuckDB (`schema_duckdb.sql`) and SQLite (`schema_sqlite.sql`) migrations.
  - Both `analytics.duckdb` and `workflow.sqlite` created successfully.
  - 11 core analytical tables verified (`DimPeriod`, `DimCompany`, `DimAccount`, `DimCostCenter`, `FactActual`, `FactBudget`, `FactForecast`, etc.).
  - Cold-start time: `< 1.8s`.
- **Script Verdict**: **PASS**.

---

### 2.6 TST-UAT-06: Go-Live Rehearsal Deliverables Check
- **Objective**: Verify presence and readiness of all go-live rehearsal governance and operational assets per Doc 28 §6.
- **Findings**:

| Release Deliverable | File Path | Status | Verification Detail |
|:---|:---|:---:|:---|
| **Named Hypercare Roster** | `packaging/named_hypercare_roster.md` | **READY** | L1/L2/L3 escalation contacts and responsibilities specified. |
| **Fallback Execution Runbook** | `packaging/fallback_execution_runbook.md` | **READY** | Step-by-step 7-phase execution for sample data contingency. |
| **Client Delivery Manifest** | `packaging/client_delivery_package_manifest.md` | **READY** | All 9 package items audited with zero sample leaks. |
| **Pre-Filled Sign-Off Records** | `packaging/prefilled_sign_off_records.md` | **READY** | GATE-13, 14, 15 pre-filled records prepared for execution. |
| **Nightly E2E Runbook** | `packaging/nightly_e2e_runbook.md` | **READY** | Unattended regression execution sequence documented. |

- **Script Verdict**: **PASS**.

---

## 3. Automated Test Verification

The entire 6-script UAT dry-run has been codified into an automated regression suite at `tests/uat/test_uat_dry_run.py` and an operational CLI runner at `scripts/run_uat_dry_run.py`.

```bash
$ python -m pytest tests/uat/test_uat_dry_run.py -v
============================= test session starts =============================
tests/uat/test_uat_dry_run.py::test_tst_uat_01_reproduce_month_bva PASSED [ 16%]
tests/uat/test_uat_dry_run.py::test_tst_uat_02_tie_out_and_ppt_parity PASSED [ 33%]
tests/uat/test_uat_dry_run.py::test_tst_uat_03_exception_wording_and_verdicts PASSED [ 50%]
tests/uat/test_uat_dry_run.py::test_tst_uat_04_training_walkthrough_doc22 PASSED [ 66%]
tests/uat/test_uat_dry_run.py::test_tst_uat_05_cold_start_client_pass PASSED [ 83%]
tests/uat/test_uat_dry_run.py::test_tst_uat_06_go_live_rehearsal_deliverables PASSED [100%]
============================== 6 passed in 5.55s ==============================
```

---

## 4. Rehearsal Disclaimer & Sign-off State

> **CRITICAL COMPLIANCE NOTICE**:  
> Per `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §5.1, this dry-run was executed entirely on synthetic test data in a development environment to rehearse acceptance procedures and verify cross-artifact numerical parity.  
> **This report does NOT constitute official client sign-off.** Formal client UAT (`GATE-14`) remains blocked pending receipt of the sanitized real-month dataset (`OQ-014` / `GATE-13`) or approved activation of the `RISK-002` fallback protocol.
