# Evidence: Stage A UAT Pack Verification

**Date:** 2026-10-03  
**Auditor / Agent:** AionCLI-05  
**Scope:** Verification evidence supporting `packaging/uat_stage_a_pack.md`  

---

## 1. Corpus Imbalance Verification
- **Target File:** `sample-data/d365_gl_actuals.csv`
- **Validation Execution:** `app.engine.imports.parse_and_validate_csv('sample-data/d365_gl_actuals.csv')`
- **Evaluated Checks:** 9 checks run (`IMP-001`, `IMP-017`..`IMP-024`)
- **Check Failure:** `IMP-023` (Debit = Credit check failed)
- **Total Debits:** INR 24,626,607,267.80
- **Total Credits:** INR 6,682,091,688.47
- **Net Imbalance:** INR 17,944,515,579.33
- **Calculated Data Quality Score:** 84 (raw 83.606..., guarantee held, deducted for failed high-severity check `IMP-023`)
- **FactActual Commitment:** 0 rows (`import_repo.py:105` skips DB insert when `is_balanced` is False for `actuals_d365`)

---

## 2. Downstream Blocked Status Verification
- **BvA Financial Statements:** Blocked (0 FactActual rows committed).
- **Exceptions Register:** Blocked (no transactional rows available for evaluation).
- **Tie-Out Schedules:** Blocked (app output cells read BLOCKED with reason).

---

## 3. Acceptance Test Harness Evidence
- **Harness Verdict:** **BLOCKED**
- **Doc-14 §5.3 Quality Bars:** **NOT MEASURED** (pending balanced corpus; all prior ungrounded recall metrics superseded).

---

## 4. Prior UAT Figures Void Notice
- `tests/uat/test_uat_dry_run.py:72` hardcoded Decimal literals and did not open the corpus.
- Ground truth Account 4000 FY26-P09 IN01 actual: 190,778,680.37 (not 12,500,000.00).
- All prior dry-run figures derived from test literals are marked void.

---

## 5. Deck Parity Void Notice
- `ppt_pack.py` does not inspect the underlying template.
- `ERR-EXP-014` does not exist in the catalog.
- Deck parity is not asserted.

---

## 6. Build & Sign-off State
- **Installer Build:** Mid-rebuild following asset substitution; not presented as final.
- **Sign-off Status:** Pre-filled template left UNSIGNED with blank signature and date fields per project governance.
