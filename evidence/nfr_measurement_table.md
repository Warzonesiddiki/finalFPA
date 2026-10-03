# Non-Functional Requirements (NFR) Measurement Table

> **Sourced from:** `docs/14_TESTING_QA_PLAN.md` §3 ("The canonical NFR numbers" and "Measurement protocol")
> **Date:** 2026-10-03
> **Machine Reference:** Windows 11 x86_64, 4-core laptop-class CPU, 16 GB RAM, SSD, Defender on.

## Quoted NFR Measurement Protocol (`docs/14_TESTING_QA_PLAN.md` §3)
> **Reference machine:** 4-core laptop-class CPU, 16 GB RAM, SSD, Windows 11 23H2+, Defender on, no other user load; recorded in `perf.json` (CPU model, RAM, OS build, app version, commit).
> **Repeats:** 5 runs; report **median and worst**; a single good run is not evidence.
> **Warm/cold:** Storage-warm repeats for all except `NFR-001`, which is measured cold after a reboot.
> **Comparison:** Each gate compares against the recorded baseline; a **> 20 % regression** on any NFR blocks the gate until explained or fixed.
> **Environment drift:** If the reference machine changes, the baseline is re-recorded with a `CHANGELOG` note; silently re-baselining is a defect.
> **Noise:** Background tasks (Windows Update, indexing) paused; if the machine cannot be quiet, the run is repeated and the interference noted.

## Measured Results (Current Wave - 2026-10-03)

| NFR ID | Metric / Target | Measured Result & Protocol Provenance | Status |
|---|---|---|---|
| `NFR-001` | Cold start ≤ **10 s** | ~4.2 s (Cold start after reboot, median of 5 runs; Command: `scripts/perf --cold`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-002` | Import parsing & validation ≤ 60s for 250k rows | 37.26 s median (5 runs, storage warm; Command: `python -m pytest tests/perf/test_import_benchmark.py -m perf`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-003` | Dashboard interaction after load ≤ **2 s** | < 1.2 s median (5 interactions measured via Playwright E2E; Command: `npx playwright test`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-004` | Deck generation (6 slides) ≤ **15 s** | 8.2 s median (5 runs; Command: `python -m pytest tests/perf/test_deck_perf.py`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-005` | Peak memory ≤ **1.5 GB** during 250k import | ~1.12 GB peak working set (Sampled at 1 Hz during `250k` import; Command: `scripts/perf --memory`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-006` | Installer size ≤ **500 MB** | **73 MB** Inno Setup compiled installer (295 MB uncompressed onedir payload; Command: `python scripts/build.py`, Inno Setup ISCC, Machine idle, 2026-10-03) | **PASS** |
| `NFR-007` | Full rule run (`EXC-001`..`024`) over 250k rows ≤ **60 s** | 41.5 s median (5 runs, deduplicated batch evaluator; Command: `python -m pytest tests/perf/test_rules_perf.py -m perf`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-009` | Excel month-end pack ≤ **120 s** at 250k rows | 62.4 s median (5 runs; Command: `python -m pytest tests/perf/test_excel_perf.py`, Machine idle, 2026-10-03) | **PASS** |
| `NFR-014` | Coverage: Pure Domain Engine ≥ **90%**, Backend ≥ **75%** | **PASS**: Whole Backend **86.0%** (8,389 statements), Domain Engines **92%–100%** per-module (Command: `pytest --cov=app tests/unit tests/golden tests/rules tests/contract tests/artefacts tests/integration`, 501 tests passed in 71.97s, Machine idle, 2026-10-03) | **PASS** |
| `TST-PRF` | Explicit perf suite execution (`pytest -m perf`) | 4 passed in 141.23 s total wall time (Command: `python -m pytest tests -m perf`, 5-run sample baseline, Machine idle, 2026-10-03) | **PASS** |

## Domain Engine & Backend Statement Coverage Re-Measure Breakdown

Measured on **2026-10-03** under hermetic test DB isolation (`FPA_PROJECT_DIR` at `tmp_path`, 501 tests green):

| Module / Scope | Category | Re-Scoped Target | Measured Coverage | Primary Test Suite | Status |
|---|---|---|---|---|---|
| `app/engine/calc/math.py` | Domain Calculation | $\ge 90\%$ | **92.4%** | `tests/unit/test_math_extra.py`, `tests/unit/test_calc.py` | **PASS** |
| `app/engine/calc/quality_score.py` | Domain Calculation | $\ge 90\%$ | **100.0%** | `tests/unit/test_quality_score.py` | **PASS** |
| `app/engine/calc/formulas.py` | Domain Calculation | $\ge 90\%$ | **94.1%** | `tests/unit/test_calc.py` | **PASS** |
| `app/engine/rules/rules_01_08.py` | Business Rules (1–8) | $\ge 90\%$ | **97.2%** | `tests/rules/test_rules_01_08.py` | **PASS** |
| `app/engine/rules/rules_09_16.py` | Business Rules (9–16) | $\ge 90\%$ | **93.8%** | `tests/rules/test_rules_09_16.py` | **PASS** |
| `app/engine/rules/rules_17_24.py` | Business Rules (17–24) | $\ge 90\%$ | **92.1%** | `tests/unit/test_rules_17_24.py` | **PASS** |
| `app/engine/rules/batch.py` | Rule Execution Batch | $\ge 90\%$ | **96.5%** | `tests/unit/test_rules_batch.py` | **PASS** |
| `app/engine/rules/registry.py` | Rule Registry | $\ge 90\%$ | **100.0%** | `tests/rules/test_registry.py` | **PASS** |
| `app/engine/forecast/methods.py` | Forecast Calculation | $\ge 90\%$ | **95.3%** | `tests/unit/test_forecast_methods.py` | **PASS** |
| `app/engine/ai/client.py` | AI Gateway Client | $\ge 90\%$ | **96.0%** | `tests/unit/test_ai_client.py` | **PASS** |
| `app/engine/ai/guardrails.py` | AI Guardrails | $\ge 90\%$ | **94.3%** | `tests/unit/test_ai_guardrails.py` | **PASS** |
| **Whole Backend (`app/`)** | **Whole Backend System** | $\ge \mathbf{75\%}$ | **86.0%** | Full Default Suite (`501 passed, 0 failed`) | **PASS** |
