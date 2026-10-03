# Sample-Data Pilot Fallback Execution Runbook (`RISK-002`)

> **Quoted from Fallback Tree & Rehearsal Report (`packaging/sample_data_pilot_fallback_rehearsal_report.md`)**:
> *"When real client month exports are delayed past the T-3 threshold and the Project Owner + Client Executive Sponsor approve activation, the pilot executes using the frozen sample-data corpus coupled with the formal limitation note."*

---

## 1. Prerequisites & Approval
* **Trigger condition:** T-3 arrival check failed (`OQ-014` unreceived).
* **Authorization:** Written approval recorded from Project Owner and Client Executive Sponsor.
* **Corpus verification:** Confirm presence of `sample-data/d365_gl_actuals.csv`, `sample-data/budget_fy26.csv`, and feeder CSVs.

---

## 2. Step-by-Step Execution Sequence

| Step | Action / Command | Verification | Limitation Notice / Notes |
|---|---|---|---|
| **1. Initialize Project** | Launch FP&A Month-End Copilot; create a new pilot project workspace. | Workspace initialized in `%LOCALAPPDATA%` without lock contention. | Ensure project name clearly indicates `[PILOT-FALLBACK]`. |
| **2. Import Sample Corpus** | Ingest `sample-data/d365_gl_actuals.csv` and feeder CSVs through the 7-step import wizard (`04`). | Batch status transitions to `COMMITTED`; control totals match baseline expectations. | Verify import execution logs. |
| **3. Run Validation & 32 Checks** | Execute validation checks (`IMP-001..032`) via API / UI. | All checks pass or quarantine rules correctly handle flagged rows. | — |
| **4. Compute BvA & Exceptions** | Trigger Budget vs Actuals aggregation (`GET /api/v1/bva`) and 24-rule exception evaluation (`EXC-001..024`). | Variances and exception findings populate with exact Decimal precision. | — |
| **5. Generate Forecast & Scenarios** | Run forecast engine methods (run-rate, trailing average, remaining budget) & Scenarios (`07`). | Base/Best/Worst scenarios computed and locked-actuals indicator verified. | — |
| **6. Issue Output Packs** | Generate Excel pack (`excel_pack`) and PowerPoint deck (`ppt_pack`). | Artefacts generated successfully without serialization errors. | Affix **Pilot Fallback Limitation Notice** to cover page. |
| **7. Complete Tie-Out Worksheet** | Populate pilot tie-out worksheet template (`28` §4.4) with execution results. | Worksheet verified and signed off by pilot lead. | Explicitly note sample-data usage per `RISK-002`. |

---

## 3. Rollback & Contingency Criteria
* **Rollback Trigger:** If any unhandled exception or data corruption occurs during sample import, abort current workspace.
* **Rollback Action:** Delete temporary workspace folder in `%LOCALAPPDATA%`, re-clone clean database template, and re-run Step 1.
