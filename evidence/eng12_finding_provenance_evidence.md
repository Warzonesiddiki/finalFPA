# ENG-12: Findings Claim & Run Provenance Evidence

**Task Reference**: `ENG-12` (P1)  
**Deliverable**: Schema update (`schema_sqlite.sql`, `db.py`), Exception repository updates (`exceptions_repo.py`), Excel export (`excel_pack.py`), and test suite (`tests/unit/test_finding_provenance.py`).  

---

## 1. Executive Summary

Per task `ENG-12`, findings now explicitly respect and record the claim context and execution run that produced them:
- Each raised finding stores `correlation_id` (run correlation ID) and `claim_id` (team claim ID / batch ID).
- When a client or auditor asks *"which close / run did this come from"*, the record provides a definitive answer rather than an estimate.
- The claim is safely closed after the finding is raised; no lifecycle dependency remains on the claim booting after it.
- Exported artifacts (specifically Excel Management Pack Sheet 5 `Exception Register`) include dedicated columns for `Correlation ID` and `Claim ID`.

---

## 2. Changes Made by File

1. **`app/engine/store/schema_sqlite.sql`**:
   - Added `correlation_id TEXT` and `claim_id TEXT` columns to `FactException`.
2. **`app/engine/store/db.py`**:
   - Added migration handlers to automatically execute `ALTER TABLE FactException ADD COLUMN correlation_id TEXT` and `claim_id TEXT` on existing project stores.
3. **`app/engine/store/exceptions_repo.py`**:
   - Updated `ExceptionListItem` to include `correlation_id` and `claim_id`.
   - Updated `ExceptionsRepository.run_rules(...)` to accept optional `correlation_id` and `claim_id` parameters, generating defaults if omitted.
   - Updated `INSERT INTO FactException` to persist `correlation_id` and `claim_id`.
   - Updated `list_exceptions` and `get_exception_detail` to project both provenance fields.
4. **`app/engine/exports/excel_pack.py`**:
   - Added `correlation_id` and `claim_id` to dataclass `ExceptionRow`.
   - Updated `build_sheet_exception_register` (Sheet 5) to include `Correlation ID` and `Claim ID` columns in the styled table header and rows.
5. **`tests/unit/test_finding_provenance.py`**:
   - Authored tests verifying that `correlation_id` and `claim_id` are stored, retrieved, and exported into the final `.xlsx` workbook.
   - Included a falsification test asserting failure when either provenance ID is missing.

---

## 3. Test Verification Transcript

```bash
python -m pytest tests/unit/test_finding_provenance.py -v -o addopts=
```

Output:
```text
tests/unit/test_finding_provenance.py::test_finding_stores_and_returns_correlation_and_claim_id PASSED [ 33%]
tests/unit/test_finding_provenance.py::test_exported_excel_pack_carries_correlation_and_claim_id PASSED [ 66%]
tests/unit/test_finding_provenance.py::test_falsification_missing_ids_fail_assertion PASSED [100%]

======================== 3 passed, 1 warning in 1.22s ========================
```
