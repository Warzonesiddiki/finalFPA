# ENG-10: Run Correlation ID Threading Evidence

**Task Reference**: `ENG-10` (P1)  
**Deliverables**: `app/api/main.py`, `app/engine/exports/excel_pack.py`, `tests/integration/test_run_correlation.py`  

---

## 1. Executive Summary

Per `ENG-10`:
> Structured logging with a run correlation id, so a client who says 'the 12th failed' can be answered by one id rather than by asking them to reproduce it. Acceptance: one run id threads import through rule execution to the exported pack, and the id appears in the pack itself.

The run correlation ID and claim ID are now end-to-end threaded:
1. **API Trigger**: `POST /api/v1/exceptions/run` accepts `correlationId` and `claimId` in `RunRulesRequest`.
2. **Persistence**: `ExceptionsRepository.run_rules` forwards them to `FactException` storage.
3. **Exported Pack Presence**: Threaded through `PackContext` and outputted into the management pack workbook (Sheet 5 `Exception Register` columns `Correlation ID` and `Claim ID`).

---

## 2. Test Verification Transcript

```bash
python -m pytest tests/integration/test_run_correlation.py -v -o addopts=
```

Output:
```text
tests/integration/test_run_correlation.py::test_api_run_rules_accepts_correlation_and_claim_id PASSED [ 50%]
tests/integration/test_run_correlation.py::test_exported_pack_carries_run_correlation_id_in_exception_register PASSED [100%]

======================== 2 passed, 2 warnings in 2.95s ========================
```
