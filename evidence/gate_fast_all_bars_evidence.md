# GATE-FAST: Acceptance Gate Stop Hiding Bars Evidence

**Task Reference**: `GATE-FAST` (P0)
**Deliverable**: `scripts/check.py` (control flow + reporting), `tests/unit/test_check_all_bars.py`
**Table re-measured**: 2026-10-08 by `opencode`, on `58955bb` + the test additions in HO-080.

---

## 1. Context & Motivation

Previously, `scripts/check.py` line 12 called `sys.exit(res.returncode)` on the **first** failing bar.
Because the Ruff Format check exited 1 on historical drift, all subsequent verification bars were
short-circuited and completely hidden from view.
Per task `GATE-FAST` and `DOC-03`/`TB-108`:
1. Every bar must run and measure its real exit status.
2. Every bar must report its individual exit code in a clear summary table.
3. The overall process exits non-zero if ANY bar failed.
4. Falsification tests verify that failing one bar does not prevent execution and reporting of all
   subsequent bars.

The control-flow change is unchanged since HO-056 and was verified there by a reviewer probe
(`BARS EXECUTED: 15 | TABLE ROWS: 16 | RETURN CODE: 1`). This revision exists because HO-056's
reviewer rejected the previous table in this file: six of its fifteen rows were wrong and three
said `PASS / PROBE`, a status that appears nowhere in `scripts/check.py`. **`PROBE` is deleted.
Every row below is either a captured exit code with its command, or is labelled not measured.**

---

## 2. Measured bar table — 2026-10-08

**How it was measured.** `python scripts/check.py` was started once, on this tree, with the repo venv
first on `PATH` (`run_command` invokes the literal `python`, so without that every bar fails for a
missing-tool reason). It did not finish: the 90-minute budget was exhausted inside bar 13. Bars
1-10, 14-16 were therefore re-run individually with the **exact command strings from
`scripts/check.py` `main()`**, each with `PATH=/home/user/.venv/bin:$PATH PYTHONUTF8=1`, and their
exit codes and wall times captured. Raw logs: `scratch/gate_bars/barNN.log`, driver
`scratch/arena_gate_bars.sh`, gate log `scratch/arena_gatefast_full_run.log`.

Environment: Linux sandbox (not the project's Windows host), Python 3.11.2, ruff 0.6-line config from
`pyproject.toml`, mypy 2.4.0, Node 22.22.3, 2 CPU / 4 GB RAM. Two rows below are environment
artefacts on this box and are labelled as such — they are not code verdicts.

| # | Check bar | Exit | Wall | Measured result (raw) |
|---:|:---|:---:|:---:|:---|
| 1 | Ruff Format Check | 1 | <1 s | `186 files would be reformatted, 60 files already formatted` |
| 2 | Ruff Lint | 1 | <1 s | `Found 1951 errors. [*] 1598 fixable with the --fix option` |
| 3 | Mypy Strict (app/engine) | 1 | 1 s | `Found 139 errors in 26 files (checked 60 source files)` (mypy 2.4.0; the project pins >=1.11) |
| 4 | UI Gate Check (ESLint (ui) + tsc --noEmit) | 1 | 12 s | As committed: `sh: 1: tsc: Permission denied` — `ui/node_modules/.bin/*` are tracked at mode 644, so on any POSIX checkout tsc never runs. After `chmod +x` (environment fix, reverted): `npx tsc --noEmit` exits non-zero with **34 errors** — 18x TS2307, 11x TS2497, 5x TS7006; 5 of the TS2307s are `Cannot find module 'lucide-react'` because the committed `lucide-react@1.49.0` has no `dist/`. The bar prints `TypeScript Errors : 1` because `scripts/check_ui_gate.py:38` is `tsc_errors = 0 if tsc_proc.returncode == 0 else 1` — a flag, not a count. Raw: `scratch/gate_bars/bar04_tsc_full.log` |
| 5 | OpenAPI Contract Drift Check | 1 | 1 s | `RuntimeError: ERROR: OpenAPI schema drift detected!` preceded by `UserWarning: Duplicate Operation ID api_list_exceptions_api_v1_exceptions_get` — `app/api/main.py` registers `GET /api/v1/exceptions` twice (`def api_list_exceptions` at 1218 and again at 1415) |
| 6 | Doc Integrity and Link Check | 0 | <1 s | `PASSED: All markdown links valid and cross-project IDs consistent!` |
| 7 | Test Catalogue Traceability Check | 1 | <1 s | `[ERROR] Unknown TST identifiers ... TST-RUL-02B in tests/unit/test_rules_01_08.py:test_exc_002_unmapped_cost_center_raised` (309 valid ids loaded, 45 marker refs over 35 ids) |
| 8 | 500-LOC Code-Health Check | 0 | <1 s | `--> [CHECK] Line-count check PASSED (all files <= 500 LOC or justified)` |
| 9 | Spec-to-Code Constants Drift Check | 0 | <1 s | `[OK] All 24 catalog specifications in sync with active engine rule batch.` |
| 10 | Engine-Boundary Import Rule (lint-imports) | 0 | <1 s | `Analyzed 114 files, 439 dependencies. Contracts: 1 kept, 0 broken.` |
| 11 | Pytest Fast Suite with Coverage | **not measured** | aborted at 62 min | `pytest tests -m "not perf" --cov=app` reached ~6 % of collected tests in 62 min at 99 % CPU / 1.2 GB RSS and was aborted. The cost is not the suite: `tests/unit/test_acceptance_determinism.py` carries the full acceptance corpus ingest in a module-scoped fixture and is **not** marked `perf` — measured standalone at 722.28 s (setup alone 648.35 s) *without* coverage tracing. The exit code of the aborted process (143) is an operator abort, not a verdict. Raw: `scratch/arena_gatefast_full_run.log`, `scratch/arena_determinism_probe.log` |
| 12 | NFR-014 Split Coverage Bars | 1 (**invalid row**) | — | Printed `Backend coverage 0.00% is below threshold 75.0%` / `Domain engines coverage 0.00% ...`. That is not a coverage measurement: `enforce_coverage_gates` calls `coverage.Coverage().load()`, which reads the `.coverage` data file that aborted bar 11 never wrote (`.coverage` does not exist on this tree). The committed `coverage.xml` says `line-rate="0.8835"`. See §4 — a missing measurement is reported as a 0 % shortfall |
| 13 | Pytest Performance Suite | **not measured** | aborted at 23 min | `pytest tests -m "perf"` ran 23 min, 6 tests reported (`...FF.` — two failures visible) before the gate's 90-minute budget expired. The perf tests assert wall-clock budgets (`tests/perf/test_import_benchmark.py:97` NFR-002 <= 60.0 s), so it was deliberately not run concurrently with bar 11 to avoid a false failure |
| 14 | CLI Doctor Health Check | 0 | 1 s | `{"status":"healthy","version":"0.1.0","engine":"ready"}` |
| 15 | Vite/TypeScript UI Build Check | 127 | <1 s | **Environment artefact.** The bar is `cmd.exe /c "npm run build --prefix ui"`; `bash: line 1: cmd.exe: command not found`. This bar cannot be measured on Linux at all, and its red is not a UI verdict |
| 16 | License & Provenance Gate | 0 | <1 s | `PASSED: all six checks clean (Addon 6 v2 §11 + doc 15 step 4a).` |

**Tally of what is measurable here:** 13 of 16 rows measured — 6 PASS (6, 8, 9, 10, 14, 16),
7 FAIL (1, 2, 3, 4, 5, 7, 15). Of those 7, two are environment artefacts of this Linux sandbox
(15 entirely; 4 partly) and row 12's FAIL is an artefact of row 11's abort. The reds that are real
statements about this tree are **1, 2, 3, 5, 7** plus the TypeScript errors behind 4.

---

## 3. Test Verification Transcript (re-measured 2026-10-08)

```bash
PYTHONUTF8=1 python -m pytest tests/unit/test_check_all_bars.py -v
```

Output:
```text
tests/unit/test_check_all_bars.py::test_check_main_returns_nonzero_when_any_bar_fails PASSED
tests/unit/test_check_all_bars.py::test_every_bar_runs_even_after_failure PASSED
tests/unit/test_check_all_bars.py::test_check_main_returns_zero_when_all_pass PASSED
tests/unit/test_check_all_bars.py::test_failure_branch_prints_its_tally_on_a_cp1252_console PASSED
tests/unit/test_check_all_bars.py::test_the_cp1252_guard_actually_rejects_the_old_marker PASSED

============================== 5 passed in 0.04s ===============================
```

The two new tests close HO-056 blocker B: `test_failure_branch_prints_its_tally_on_a_cp1252_console`
runs the **failure branch** of `main()` against a stdout whose `write` encodes to cp1252 and raises,
and asserts both the `[FAIL] Validation Gate FAILED` line and the `1/16 bars failed` tally survive.
`test_the_cp1252_guard_actually_rejects_the_old_marker` is the falsification of that guard: it asserts
the fake console really does raise on the U+274C marker HO-056 rejected, so the guard cannot silently
become a StringIO.

Lint/format delta of that edit, measured apples-to-apples with `--stdin-filename` so the same config
applies:

```bash
git show HEAD:tests/unit/test_check_all_bars.py | python -m ruff check --stdin-filename tests/unit/test_check_all_bars.py -
# Found 4 errors.   (F401 subprocess, sys, MagicMock, pytest)
python -m ruff check tests/unit/test_check_all_bars.py --output-format=concise
# Found 2 errors.   (F401 subprocess, MagicMock — both pre-existing)
python -m ruff format --diff tests/unit/test_check_all_bars.py   # 3 hunks, all inside the 3 pre-existing tests
```

---

## 4. What this measurement says that the old table could not

1. **The gate cannot be run to completion on this machine.** One `python scripts/check.py`
   invocation exhausted a 90-minute budget inside bar 13, and never reached its own summary table.
   A gate that cannot finish is not reported less honestly — it is not run at all, which is the
   failure GATE-FAST exists to end. The cause is measurable: bar 11 runs the whole `-m "not perf"`
   suite under coverage, and that suite contains acceptance-corpus tests that are not marked `perf`.
2. **`PROBE` is gone.** Three rows previously carried a status the gate never produced. Two of those
   three rows are now labelled *not measured* with the reason and the wall time at which they were
   abandoned.
3. **Two reporting defects surfaced, neither fixed here** (both are one-file, one-line changes and
   both belong to other claims): `scripts/check_ui_gate.py:38` reports a pass/fail flag as an error
   *count* against a budget of 0, and `scripts/check.py` `enforce_coverage_gates` reports "no
   coverage data loaded" as a `0.00 %` shortfall — the same disease as this card: a number that is
   not a measurement.
4. **Windows-only bar on a shared repo.** Bar 15 hard-codes `cmd.exe`, so on any POSIX checkout it
   fails with exit 127 before `npm` is reached. Either gate it on `sys.platform` or shell out to
   `npm` directly.
5. **Tracked `ui/node_modules` is not installable as shipped.** `ui/node_modules/.bin/*` are
   committed at mode 644 (no exec bit) and `lucide-react` is committed without its `dist/`, so
   `tsc` cannot resolve it. On Windows the `.cmd` shims hide the first problem; on POSIX the UI gate
   bar dies before reading a single TypeScript verdict.

Measurement caveat: this tree had exactly one writer during the run (this claim), unlike the
2026-10-05 reading taken while three seats were editing. It is still a reading of one machine at one
moment, not a constant — the sandbox is 2 CPU / 4 GB, which is smaller than the project host.
