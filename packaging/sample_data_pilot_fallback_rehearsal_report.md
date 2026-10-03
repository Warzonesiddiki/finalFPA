# SAMPLE-DATA PILOT FALLBACK REHEARSAL REPORT (`RISK-002`)

**Project:** FP&A Month-End Copilot  
**Date:** 2026-10-02  
**Reference:** Risk Register `RISK-002`, Roadmap Gate `GATE-13`, Open Question `OQ-014`  
**Status:** Rehearsed & Verified (Read-Only Rehearsal)  

---

## 1. Rehearsal Overview
Per `RISK-002` ("The sanitized real month never arrives"), when client real-month D365 GL exports are delayed or blocked by security review, the pilot executes using the frozen sample-data corpus (`d365_gl_actuals.csv`, `bank_ledger_actuals.csv`, `payroll_procurement_actuals.csv`, `budget_fy26.csv`) coupled with an explicit, formal limitation note.

---

## 2. End-to-End Rehearsal Steps & Results

| Step | Action & Component | Result & Evidence | Status |
|---|---|---|---|
| **1. Import Sample Month** | Import `sample-data/d365_gl_actuals.csv` through 7-step wizard & import repository | File parsed successfully, checksum generated, row counts recorded | **PASS** |
| **2. Validate Dataset** | Run 32-check validation catalog (`IMP-001..032`) and control-total reconciliation | Validation report generated; imbalanced batch quarantine / review rules honored per spec | **PASS** |
| **3. Budget vs Actuals (BvA)** | Aggregate BvA via analytics engine (`GET /api/v1/bva`) | Department and account variances computed with deterministic Decimal math | **PASS** |
| **4. Exception Rules** | Execute deduplicated 24-rule exception batch (`EXC-001..EXC-024`) | Findings registered with correct severity badges and aging buckets | **PASS** |
| **5. Forecast Refresh** | Run forecast engine methods (run-rate, trailing average, remaining budget) & Scenarios | Base/Best/Worst scenarios computed and locked-actuals indicator verified | **PASS** |
| **6. Pack Issuance** | Generate Excel pack (`excel_pack`) and PowerPoint deck (`ppt_pack`) | Artefacts generated matching engine values exactly in cross-harness test | **PASS** |
| **7. Tie-Out Worksheet** | Populate pilot tie-out template with sample data results & formal limitation notice | Worksheet signed off with explicit sample-not-real limitation notice | **PASS** |

---

## 3. Official Limitation Wording (`RISK-002`)

The following limitation notice is embedded prominently in the header of the pilot tie-out worksheet (`pilot_tieout_worksheet_template.xlsx`), executive summaries, and handover packs:

> **PILOT FALLBACK LIMITATION NOTICE (`RISK-002` / `OQ-014`):**  
> *"This pilot run and associated tie-out worksheets use synthetic sample data (`d365_gl_actuals.csv`, `budget_fy26.csv`) rather than sanitized real client month-end data. All figures, variances, exception findings, and forecast scenarios presented herein are illustrative and intended solely for software validation, UAT familiarization, and workflow rehearsal. They do not constitute a formal production sign-off or audit conclusion until sanitized real client data is successfully ingested, reconciled, and tied out."*

---
*End of Sample-Data Pilot Fallback Rehearsal Report.*
