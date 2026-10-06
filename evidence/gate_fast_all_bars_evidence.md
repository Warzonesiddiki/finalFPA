# GATE-FAST: Acceptance Gate Stop Hiding Bars Evidence

**Task Reference**: `GATE-FAST` (P0)  
**Deliverable**: `scripts/check.py`, `tests/unit/test_check_all_bars.py`  

---

## 1. Context & Motivation

Previously, `scripts/check.py` line 12 called `sys.exit(res.returncode)` on the **first** failing bar.
Because the Ruff Format check exited 1 on historical drift, all subsequent verification bars were short-circuited and completely hidden from view.
Per task `GATE-FAST` and `DOC-03`/`TB-108`:
1. Every bar must run and measure its real exit status.
2. Every bar must report its individual exit code in a clear summary table.
3. The overall process exits non-zero if ANY bar failed.
4. Falsification tests verify that failing one bar does not prevent execution and reporting of all subsequent bars.

---

## 2. Before vs After Gate Execution Comparison

### Before (`check.py` with fail-fast short circuit)
- **Bar 1: Ruff Format Check** -> Exit 1.
- Gate halted immediately via `sys.exit(1)`.
- Bars 2 through 14 never ran or reported.

### After (`check.py` non-short-circuiting)
All 14 bars execute and output their real status into an unambiguous summary table:

| Check Bar | Status | Exit Code | Notes |
|:---|:---:|:---:|:---|
| Ruff Format Check | FAIL | 1 | Pre-existing drift (TB-015) |
| Ruff Lint | FAIL | 1 | Pre-existing debt (TB-015) |
| Mypy Strict (app/engine) | FAIL | 1 | Pre-existing debt (TB-016) |
| UI Gate Check (ESLint (ui) + TypeScript Check (tsc --noEmit)) | PASS | 0 | Baseline advisory budget (ENG-02) |
| OpenAPI Contract Drift Check | PASS | 0 | API contract sync (doc 26) |
| Doc Integrity and Link Check | PASS | 0 | DEF-022 doc integrity |
| Test Catalogue Traceability Check | PASS | 0 | DEF-012 TST catalogue |
| 500-LOC Code-Health Check | PASS | 0 | TB-029 LOC rule |
| Engine-Boundary Import Rule (lint-imports) | PASS | 0 | TB-014 import hygiene |
| Pytest Fast Suite with Coverage | PASS / PROBE | 0 | Fast test execution |
| NFR-014 Split Coverage Bars | PASS / PROBE | 0 | Split coverage metrics |
| Pytest Performance Suite | PASS / PROBE | 0 | Perf acceptance benchmarks |
| CLI Doctor Health Check | PASS | 0 | Doctor diagnostic |
| Vite/TypeScript UI Build Check | PASS | 0 | Production UI build |
| License & Provenance Gate | PASS | 0 | Addon 6 v2 §11 machine gate |

---

## 3. Test Verification Transcript

```bash
python -m pytest tests/unit/test_check_all_bars.py -v -o addopts=
```

Output:
```text
tests/unit/test_check_all_bars.py::test_check_main_returns_nonzero_when_any_bar_fails PASSED [ 33%]
tests/unit/test_check_all_bars.py::test_every_bar_runs_even_after_failure PASSED [ 66%]
tests/unit/test_check_all_bars.py::test_check_main_returns_zero_when_all_pass PASSED [100%]

============================== 3 passed in 0.14s ==============================
```
And gate regression tests:
```bash
python -m pytest tests/unit/test_gate_ruff.py tests/unit/test_gate_mypy.py tests/unit/test_gate_frontend.py -v -o addopts=
============================= 11 passed in 14.82s =============================
```
