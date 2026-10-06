# ENG-05: Decision Statement on Hard-Coded Generators

Per task `ENG-05`, the four scripts that emitted hard-coded tables (`scripts/audit_accessibility_matrix.py`, `scripts/verify_analyst_maths_trace.py`, `scripts/generate_error_catalogue.py`, and `scripts/generate_screen_conformance_matrix.py`) were evaluated for whether they should read their subject at run time or be deleted.

---

## 1. Scripts Deleted

### `scripts/audit_accessibility_matrix.py`
- **Action Taken:** **DELETED**
- **Rationale:** The script originally printed a 109-line markdown table containing hard-coded assertions about 43 screens without parsing a single `.tsx` component file (e.g. asserting `ui/src/main.tsx:145` had ARIA roles when it was just an `<h1>` heading). Accessibility cannot be audited by printing a pre-written static string. Legitimate a11y testing is handled through axe-core, Playwright e2e keyboard tests, or real static analysis. Emitting a static table provided false assurance.

### `scripts/generate_screen_conformance_matrix.py`
- **Action Taken:** **DELETED**
- **Rationale:** The script held a static tuple array of 43 screens with hardcoded line numbers, API endpoints, and statuses. It did not dynamically inspect React routes, ASTs, or OpenAPI routes. Screen conformance must be proven by actual tests and route contract checkers, not a script that writes out a pre-baked table.

---

## 2. Scripts Refactored to Read Runtime Subjects

### `scripts/generate_error_catalogue.py`
- **Action Taken:** **REFACTORED TO DYNAMIC ENGINE EXECUTION**
- **Rationale:** The project maintains a centralized single source of truth for all application error codes in `app.engine.errors` (`get_error_catalog()`). The script was refactored to remove all hard-coded error lists (`ERROR_CATALOGUE_DATA`) and dynamically import and iterate `get_error_catalog()`. It now outputs `evidence/ux/error-catalogue.md` directly from the runtime engine catalog (77 error codes across 11 families).

### `scripts/verify_analyst_maths_trace.py`
- **Action Taken:** **REFACTORED TO DYNAMIC ENGINE EXECUTION**
- **Rationale:** The twelve critical analyst numbers (`CALC-nnn` and `KPI-nnn`) have concrete canonical implementations in `app.engine.calc.math` and `app.engine.calc.quality_score`. The script was refactored to dynamically import and invoke the real calculation functions (`calculate_variance`, `calculate_variance_pct`, `calculate_favourability`, `calculate_percentage_point_variance`, `calculate_gross_margin_pct`, `calculate_budget_burn_pct`, `calculate_mape_lite`, `calculate_quality_score`, `quantize_money`, `format_currency`). It verifies calculations live without hardcoded equations.

---

## 3. Falsification & Regression Testing

The test suite in `tests/unit/test_retire_hardcoded_generators.py`:
1. Asserts that the deleted scripts (`audit_accessibility_matrix.py` and `generate_screen_conformance_matrix.py`) do not exist.
2. Asserts that `generate_error_catalogue.py` imports `app.engine.errors.get_error_catalog`, contains no static `ERROR_CATALOGUE_DATA` list, and dynamically responds to injected runtime catalog updates.
3. Asserts that `verify_analyst_maths_trace.py` imports and executes calculation routines from `app.engine.calc.math` and `app.engine.calc.quality_score`.
