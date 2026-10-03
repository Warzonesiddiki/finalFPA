# UAT Dry-Run Execution Transcript (TST-UAT-01..06)

**Document Reference**: `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §5.2, `docs/14_TESTING_QA_PLAN.md` §12.4  
**Date**: 2026-10-03  
**Runner**: `pytest` and `scripts/run_uat_dry_run.py`  
**Host Environment**: Windows 11 x86_64, Python 3.14.7  
**Status**: **ALL 6 SCRIPTS PASSED (100%)**

---

## 1. Pytest Test Suite Execution (`tests/uat/test_uat_dry_run.py`)

Command executed:
```powershell
python -m pytest tests/uat/test_uat_dry_run.py -v
```

Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Tahir\Documents\GitHub\finalFPA
configfile: pyproject.toml
plugins: anyio-4.15.1, cov-7.1.0
collected 6 items

tests\uat\test_uat_dry_run.py::test_tst_uat_01_reproduce_month_bva PASSED [ 16%]
tests\uat\test_uat_dry_run.py::test_tst_uat_02_tie_out_and_ppt_parity PASSED [ 33%]
tests\uat\test_uat_dry_run.py::test_tst_uat_03_exception_wording_and_verdicts PASSED [ 50%]
tests\uat\test_uat_dry_run.py::test_tst_uat_04_training_walkthrough_doc22 PASSED [ 66%]
tests\uat\test_uat_dry_run.py::test_tst_uat_05_cold_start_client_pass PASSED [ 83%]
tests\uat\test_uat_dry_run.py::test_tst_uat_06_go_live_rehearsal_deliverables PASSED [100%]

============================== 6 passed in 3.38s ==============================
```

---

## 2. CLI Rehearsal Harness Execution (`scripts/run_uat_dry_run.py`)

Command executed:
```powershell
python scripts/run_uat_dry_run.py
```

Output:
```text
===========================================================================
FP&A MONTH-END COPILOT - UAT DRY-RUN EXECUTION REPORT (SAMPLE DATA)
Document reference: docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md §5.2 / Doc 14 §12.4
Mode: Dry-Run Rehearsal (Analyst simulated, no client sign-off)
===========================================================================

[SCRIPT 1] TST-UAT-01: Reproducing one month manual BvA...
  Account 5100 (Salaries & Direct Wages): Actual=5,200,000.00, Expected=5,200,000.00, Diff=0.00
  Account 5500 (Software & Cloud Subscriptions): Actual=1,600,000.00, Expected=1,600,000.00, Diff=0.00
  Account 4000 (Product Sales Revenue): Actual=12,500,000.00, Expected=12,500,000.00, Diff=0.00

[SCRIPT 2] TST-UAT-02: Generating Excel Pack and PPT Deck...
  Excel Pack: Management_Pack_UAT_FY26-P09.xlsx (exists: True)
  PPT Deck: Management_Deck_UAT_FY26-P09.pptx (exists: True, 6 slides)
  Revenue parity: Excel=12,500,000.00 vs Engine=12,500,000.00 (Diff: 0.00)

[SCRIPT 3] TST-UAT-03: Reviewing exception wording and verdicts...
  Exception rows reviewed: 3
  Misleading findings detected (S1/S2): 0

[SCRIPT 4] TST-UAT-04: Verifying training walkthrough in Doc 22...
  Required task markers verified: ['T-01', 'T-02', 'T-05', 'T-10', 'T-15', 'T-20', 'T-21']
  Missing tasks: []

[SCRIPT 5] TST-UAT-05: Cold-start clean machine initialization...
  Fresh DB created at: C:\Users\Tahir\AppData\Local\Temp\fpa_uat_run_...\fresh_machine
  DuckDB exists: True | SQLite exists: True
  DuckDB tables initialized: 11

[SCRIPT 6] TST-UAT-06: Verifying go-live rehearsal deliverables...
  Deliverable named_hypercare_roster: EXISTS
  Deliverable fallback_execution_runbook: EXISTS
  Deliverable client_delivery_manifest: EXISTS
  Deliverable prefilled_sign_off_records: EXISTS
  Deliverable nightly_e2e_runbook: EXISTS

===========================================================================
UAT DRY-RUN SUMMARY MATRIX
===========================================================================
[PASS] TST-UAT-01: Analyst reproduces one month manual BvA | Diff: 0.00 across all accounts
[PASS] TST-UAT-02: Tie-out worksheet: BvA totals, key accounts, exceptions vs PPT deck | Diff: 0.00 cross-artifact numerical discrepancy
[PASS] TST-UAT-03: Accounting-owner review of exception wording and verdicts | Diff: 0 misleading findings
[PASS] TST-UAT-04: Training walkthrough using only Doc 22 (End User Guide) | Diff: 0 missing flow instructions
[PASS] TST-UAT-05: Cold-start client pass on clean filesystem | Diff: 0 missing initialization schemas
[PASS] TST-UAT-06: Go-live rehearsal deliverables verification | Diff: 0 missing governance / ops artifacts
===========================================================================
```
