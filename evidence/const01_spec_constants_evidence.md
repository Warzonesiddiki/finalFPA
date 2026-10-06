# CONST-01: Spec-to-Code Constants Drift Checker Evidence

**Task Reference**: `CONST-01` (P1)  
**Deliverable**: `scripts/check_spec_constants.py`, `scripts/check.py`, `tests/unit/test_check_spec_constants.py`  

---

## 1. Context & Motivation

Per `evidence/ops/false-evidence-register.md` section 4:
> **A spec-to-code constant check (does not exist).** The `HO-006` pattern — code shipping ahead of the catalogue `DEC-057` requires — was caught by a human reading two files. Nothing on this board would have caught it. This is the one gap in the list, and it is the honest reason `LEAD-01` is a register rather than a solved problem.

The `HO-006` pattern specifically arose when `docs/06` declared subject key `entity_account_pair` while the code emitted `entity|account|P..`.
Per task `CONST-01`:
1. Find constants and contracts the spec declares (`docs/06_EXCEPTION_RULES_CATALOG.md`), compare against what the active engine rule batch actually emits, and fail loudly on any mismatch.
2. Derives from the spec at run time, not hardcoded.
3. Specifically checks the `HO-006` `EXC-020` pattern and reports lines from both files.
4. Ships with a falsification test perturbing values to prove failure.
5. Wired into `scripts/check.py` as a non-short-circuiting bar.

---

## 2. Check Execution & Audit of Historical EXC-020 Drift

Command:
```bash
python scripts/check_spec_constants.py
```

Output:
```text
--> [CONST-01] Parsed 24 rule specifications from 06_EXCEPTION_RULES_CATALOG.md
    Checking EXC-020 (docs/06 line 574):
      Spec subject key: company_code|account_code|period_span
      Code subject key: subject_key=f"{comp}|{acc}|{span}", (rules_17_24.py:281)
      Status: In sync (matches spec subject key definition company_code|account_code|period_span)

✓ All 24 catalog specifications in sync with active engine rule batch.
```

---

## 3. Test Coverage & Falsification Verification

Unit and falsification tests in `tests/unit/test_check_spec_constants.py`:
- `test_parse_catalog_specs`: Dynamic extraction of all 24 catalog rules from `docs/06`.
- `test_check_spec_constants_clean`: Confirms 0 exit code on valid repo state.
- `test_falsification_perturbed_catalog_fails`: Perturbs specification to prove failure.
- `test_falsification_missing_exc_020_code_fails`: Perturbs code implementation to prove failure.

Execution transcript:
```bash
python -m pytest tests/unit/test_check_spec_constants.py tests/unit/test_check_all_bars.py -v -o addopts=
```
```text
tests/unit/test_check_all_bars.py::test_check_main_returns_nonzero_when_any_bar_fails PASSED [ 14%]
tests/unit/test_check_all_bars.py::test_every_bar_runs_even_after_failure PASSED [ 28%]
tests/unit/test_check_all_bars.py::test_check_main_returns_zero_when_all_pass PASSED [ 42%]
tests/unit/test_check_spec_constants.py::test_parse_catalog_specs PASSED [ 57%]
tests/unit/test_check_spec_constants.py::test_check_spec_constants_clean PASSED [ 71%]
tests/unit/test_check_spec_constants.py::test_falsification_perturbed_catalog_fails PASSED [ 85%]
tests/unit/test_check_spec_constants.py::test_falsification_missing_exc_020_code_fails PASSED [100%]

============================== 7 passed in 0.43s ==============================
```
