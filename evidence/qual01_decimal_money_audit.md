# QUAL-01: DEF-015 Decimal Money End-to-End Remediation & Boundary Audit

**Task Reference**: `QUAL-01` (P0)  
**Governing Rules**: `R8` (money is `Decimal`, never `float`), `01` §11.3 rule 6, `17` §5.1  
**Target Evidence Path**: `evidence/qual01_decimal_money_audit.md`  

---

## 1. Executive Summary

This audit and remediation completes `DEF-015`, ensuring that monetary amounts across the engine (`parse`, `persist`, `compute`, `serialise`) operate strictly in `Decimal` and never suffer from floating point cent-leaks (`99999999999999.99` degrading to `.98` in IEEE-754 double precision).

---

## 2. Before / After Inventory of Money Boundaries

| Subsystem / Boundary | Before State | Fixed State | Status |
|---|---|---|---|
| **AI Spend Caps (`app/engine/ai/guardrails.py`)** | `monthly_cost: float = 1500.0`, `float(monthly_cost)` checks | `monthly_cost: Decimal = Decimal("1500.00")`, `Decimal` comparison | **REMEDIATED** |
| **Token Rates (`app/engine/ai/guardrails.py`)** | `input_rate_per_1k: float = 0.15`, `output_rate_per_1k: float = 0.77` | `Decimal("0.15")`, `Decimal("0.77")` | **REMEDIATED** |
| **Import Staging (`app/engine/store/import_repo.py`)** | Handled via `str(Decimal)` into DuckDB `DECIMAL(18,2)` | Native strings bound into `DECIMAL(18,2)` | **CONFIRMED** |
| **Forecast Overrides (`app/engine/store/forecast_repo.py`)** | `amount` stored as exact `Decimal` strings | Exact `Decimal` preservation across database boundaries | **CONFIRMED** |
| **Excel Export (`app/engine/exports/excel_pack.py`)** | Data transfer rows typed with `Decimal` | Minor-unit exact representation preserved before openpyxl | **CONFIRMED** |
| **PPT Bridge (`app/engine/exports/ppt_pack.py`)** | `_bridge_plan` coerces legacy float inputs to Decimal via str | Zero cent drift in waterfall drivers | **CONFIRMED** |
| **AI Usage Costs (`app/engine/ai/usage.py`)** | Database stores stringified Decimal; serialization uses Decimal | AST verified: no float operations in cost logging | **CONFIRMED** |

---

## 3. Fixed Sites Listed by File:Line

- `app/engine/ai/guardrails.py:725`: `monthly_cost: Decimal = Decimal("1500.00")` (was `float = 1500.0`).
- `app/engine/ai/guardrails.py:727-728`: `input_rate_per_1k: Decimal = Decimal("0.15")`, `output_rate_per_1k: Decimal = Decimal("0.77")` (were `float`).
- `app/engine/ai/guardrails.py:884-893`: Cost cap checking rewritten to perform exact `Decimal` comparison instead of `float(monthly_cost) >= self.config.monthly_cost`.

---

## 4. Falsification Testing Proof

In `tests/unit/test_def015_decimal_money.py`:
- `test_def015_ai_cap_config_money_is_decimal`: Verifies config fields are `Decimal`.
- `test_def015_falsification_injected_float_fails_precision`: Demonstrates mathematically that `float(CENT_CRITICAL)` fails exact equality with `CENT_CRITICAL` (`99999999999999.98 != 99999999999999.99`), proving the failure mode that Decimal enforcement prevents.
- Full suite execution: `python -m pytest tests/unit/test_def015_decimal_money.py -v -o addopts=` (**20 passed in 9.73s**).
