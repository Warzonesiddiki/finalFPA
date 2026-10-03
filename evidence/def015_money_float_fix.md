# DEF-015 Money-Path Float Remediation Report

**Document Reference**: `docs/06_CALCULATION_ENGINE_RULES.md` §2.1 (Decimal Precision)  
**Date**: 2026-10-03  
**Auditor / Roles**: AionCLI-02 (Backend Fixes) & AionCLI-03 (Forecast/AI Fixes)  
**Scope**: Backend precision pipeline audit, targeted remediation, and regression testing.

---

## 1. Executive Summary

This task remediated the most serious correctness class error in the FP&A backend: the conversion of `Decimal` monetary amounts to floating-point representations prior to persistence or calculation, causing precision loss (cent leak) at high magnitudes (e.g., `99,999,999,999,999.99` representing as `.98`).

In coordination with AionCLI-03, the following modules were remediated:
1. `app/engine/store/import_repo.py`: Removed naive `float()` casting of `debit`, `credit`, `net_amount`, and `budget` before dispatch to DuckDB. DuckDB properly bounds strings and native `Decimal` parameters directly into `DECIMAL(18,2)`.
2. `app/engine/exports/excel_pack.py`: Upgraded internal Dataclass type annotations from `float` to `Decimal` (`BvARow`, `PLRow`, `TransactionRow`, etc.) to maintain precision in the Python abstraction before handing off to the `openpyxl` library (which legitimately serializes to `IEEE 754` format per Excel standards).

Regression tests were added to mathematically prove survival of strings like `99999999999999.99` across the module boundaries.

---

## 2. Remediation Details (AionCLI-02 Scope)

### 2.1 `app/engine/store/import_repo.py`
**Problem (L149, L209-211 approx):** 
```python
float(tx.net_amount if tx.net_amount else tx.debit),
float(tx.debit),
float(tx.credit),
float(tx.net_amount),
```
**Fix implemented:** Cast explicitly to `str(...)` preserving exact textual representation of the parsed `Decimal`. DuckDB interprets bounded string parameters perfectly into `DECIMAL(18,2)`.

### 2.2 `app/engine/exports/excel_pack.py`
**Problem:** `BvARow` and other output data transfer objects explicitly typed `actual: float`, `budget: float`, coercing `Decimal` values down to float before `openpyxl` instantiation.
**Fix implemented:** Converted 15+ relevant attributes to use Python's `Decimal` type globally within `excel_pack.py` internal structures.

---

## 3. Regression Coverage Prove-Out

The suite now contains targeted numerical checks blocking floats on these paths:
- `test_def015_import_repo_money_float` (`tests/unit/test_import_repo.py`): Creates a corpus with `99999999999999.99`, commits to the database, extracts via `duckdb` connection directly, and calls standard `assert res[X] == Decimal('99999999999999.99')` catching the `.98` rounding error. (Passes successfully).
- `test_def015_excel_pack_money_float` (`tests/unit/test_def015_excel_pack.py`): Evaluates Excel pack row structures maintaining direct `isinstance(val, Decimal)` status through to `export_excel_pack` API boundaries. (Passes successfully).

---

## 4. GAP-3 Exposure Documentation (React UI)

**FINDING: New-04's GAP-3 condition is VERIFIED and represents a widespread architectural exposure.**

The backend effectively quarantines `IEEE 754` through strict `Decimal(18,2)` handling and serializes API payloads as raw JSON strings (e.g. `{"actualAmount": "12500000.00"}`). 

However, the React frontend completely circumvents this protection. Code inspection surfaces patterns similar to:
```typescript
// ui/src/components/analyze/BvaMatrixTable.tsx L60-62
const totalActual = items.reduce((sum, it) => sum + Number(it.actualAmount || 0), 0)
const totalBudget = items.reduce((sum, it) => sum + Number(it.budgetAmount || 0), 0)
const totalVariance = totalActual - totalBudget
```

**Risk Assessment:**
- **Magnitude**: High.
- **Why**: Javascript does not natively support `Decimal` math; `Number` is an `IEEE 754` double-precision float. Total lines aggregating heavily nested arrays of sub-account ledgers using standard functional accumulator reduction are continuously susceptible to accumulative cent loss (`0.1 + 0.2 = 0.30000000000000004`).
- **Required Re-scoping Action**: Introduce deterministic precision packages to the React UI (e.g. `decimal.js` or `bignumber.js`) for mathematical total accumulators, and leave Javascript `Number` casting primarily for UI elements displaying purely visual formats or localized formaters rather than cumulative row aggregates. This scope vastly exceeds backend remediation and mandates an explicit post-freeze patch schedule.