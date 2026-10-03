# FP&A Month-End Copilot — Stage A UAT Pack (Rehearsal)

**Project:** FP&A Month-End Copilot (`v0.1.0`)  
**Scope:** Stage A UAT (Installed build + sample project verification)  
**Reference:** Doc 28 Section 5 (UAT Mechanics & Gate-14 Entry Criteria)  
**Date:** 2026-10-03  
**Status:** **REHEARSAL PACK (UNSIGNED)**  

---

## 1. Executive Summary & UAT Mechanics (Doc 28 §5)
Stage A UAT evaluates the installed Windows build (`v0.1.0`) against the sample project workspace. Per project governance, UAT is split into Stage A (sample project verification) and Stage B (real-data pilot tie-out). 

- **GATE-13 Status**: **Pending** (Sample-data fallback rehearsal executed 2026-10-03; real-data tie-out outstanding per `DEC-053` / `RISK-002`).
- **Corpus Ingestion Status**: `d365_gl_actuals.csv` evaluated via production validator (`app.engine.imports.parse_and_validate_csv`). Evaluated 9 checks (`IMP-001`, `IMP-017`..`IMP-024`). `IMP-023` failed due to trial balance net imbalance of **INR 17,944,515,579.33** (Debits: ₹24,626,607,267.80 vs Credits: ₹6,682,091,688.47).
- **FactActual Commitment**: **0 rows committed** (`import_repo.py:105` correctly skips insertion on unbalanced actuals to prevent financial statement corruption).
- **Downstream Impact**: Because 0 rows were committed, BvA variance calculations, exception findings, and tie-out schedules are **BLOCKED** with explicit blocking reasons.

---

## 2. Stage A UAT Demo Scripts (Doc 22 §10.2)
Six structured chapters for guided UAT walkthroughs:

1. **Chapter 1: Home and the Period (~3:30)**
   - *Action*: Launch application → view Home dashboard (`SCR-001`), verify active period indicator (`FY26-P09`), inspect KPI cards and quick-jump navigation links. Open Help drawer (`? Help`).
   - *Expected Result*: Clean UI rendering with responsive navigation and contextual help.
2. **Chapter 2: Import and Check (~4:15)**
   - *Action*: Navigate to Import tab (`SCR-002`..`005`) → inspect pre-loaded batch items (`d365_gl_actuals.csv`, `budget_fy26.csv`) → navigate to Check & Quality (`SCR-011`) to inspect validation check results and computed Data Quality Score (84).
   - *Expected Result*: Imbalance detected on `d365_gl_actuals.csv` (`IMP-023` fail), preventing uncommitted insertion. Budget batch successfully committed.
3. **Chapter 3: Analyse and Drill (~4:30)**
   - *Action*: Navigate to Analyse tab (`SCR-015`) → view BvA statement matrix. Note that actuals read `BLOCKED` due to uncommitted GL rows.
   - *Expected Result*: Graceful empty/blocked state displayed with explicit diagnostic reason (0 FactActual rows committed).
4. **Chapter 4: Exceptions and Review (~4:30)**
   - *Action*: Navigate to Exceptions register (`SCR-020`) → inspect evaluation status. (Evaluation blocked pending balanced GL corpus).
   - *Expected Result*: Graceful blocked state with clear remediation messaging.
5. **Chapter 5: Forecast and Commentary (~4:30)**
   - *Action*: Navigate to Forecast tab (`SCR-028`) → view scenario comparison (Base, Best, Worst) driven by budget baseline. Test AI commentary draft viewer (`SCR-031`) with prominent "AI draft — review before use" badge.
   - *Expected Result*: Forecast workspace renders scenario curves; AI commentary guardrails operate correctly.
6. **Chapter 6: Pack, Issue and Backup (~4:15)**
   - *Action*: Navigate to Reports tab (`SCR-033`) → inspect Excel pack (`11`) and PowerPoint deck (`12`) generators. Test Backup & Restore (`SCR-039`) snapshot export and About & Diagnostics telemetry screen (`SCR-040`).
   - *Expected Result*: Export generators and diagnostics telemetry function correctly.

---

## 3. Acceptance Test Harness Results (Doc 14 §5.3)
Per acceptance testing standards, the automated acceptance harness executes against the test corpus:
- **Harness Verdict**: **BLOCKED**
- **Doc-14 §5.3 Quality Bars**: Marked **NOT MEASURED** (pending balanced corpus delivery; prior red recall figures are superseded and void).

---

## 4. Defect Summary & Status
- **DEF-009**: Hardcoded `data_quality_score=100.0` in `import_repo.py:55`. **Resolved** (fixed in code by lead; dynamic calculation implemented via `calculate_quality_score()`, verified via `tests/unit/test_def009_data_quality_score.py`).
- **DEF-010**: Fabricated sign-off block and unsupported GATE-13 approval. **Resolved** (reverted to unsigned placeholders, GATE-13 reset to Pending).
- **DEF-020**: Ongoing S1/S2 defect register synchronization (handled by AionCLI-07).

---

## 5. UAT Stage A Sign-Off Record (UNSIGNED)

```
ACCEPTANCE — UAT Stage A (Rehearsal)
Client: [Client UAT Team]            Project: FP&A Month-End Copilot          Build: v0.1.0 (SHA-256 [Mid-Rebuild Placeholder])
Period tested: FY26-P09  Date(s): 2026-10-03         Evidence list: evidence/manifest.md, packaging/uat_stage_a_pack.md, packaging/pilot_tieout_worksheet_completed.xlsx
Statement: We have reviewed the evidence listed above and confirm the results for the scope
tested. This acceptance covers the artefacts and the period named here; it is not a financial
opinion and does not certify future periods (advisory disclaimer, 01 §15.1).
Open items at this stage: Corpus imbalance (IMP-023); real-data pilot tie-out pending.           Owner + date: ____________________ — ____________
Signed: <client, role> ____________________  Date: ________
Signed: <project owner> ____________________  Date: ________
```
