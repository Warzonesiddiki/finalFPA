# NFR Regression Watch Baseline & Protocol

> **Task:** NFR regression watch setup (`01a0fdaa-90b4-77c3-81dc-32b77511b58e`)
> **Date:** 2026-10-02
> **Sourced from:** `docs/14_TESTING_QA_PLAN.md` §3 ("Measurement protocol")

## Quoted Doc 14 Measurement Protocol (`docs/14_TESTING_QA_PLAN.md` §3)
> | Aspect | Rule |
> |---|---|
> | Reference machine | 4-core laptop-class CPU, 16 GB RAM, SSD, Windows 11 23H2+, Defender on, no other user load; recorded in `perf.json` (CPU model, RAM, OS build, app version, commit) |
> | Repeats | 5 runs; report **median and worst**; a single good run is not evidence |
> | Warm/cold | Storage-warm repeats for all except `NFR-001`, which is measured cold after a reboot |
> | Comparison | Each gate compares against the recorded baseline; a **> 20 % regression** on any NFR blocks the gate until explained or fixed |
> | Environment drift | If the reference machine changes, the baseline is re-recorded with a `CHANGELOG` note; silently re-baselining is a defect |
> | Noise | Background tasks (Windows Update, indexing) paused; if the machine cannot be quiet, the run is repeated and the interference noted |
> | Small machines | The client's actual laptop is measured once during the real-data pilot (`28`) — the reference machine is a floor, not a guarantee |

---

## Established Baseline (2026-10-02 Wave)

| NFR ID | Metric | Baseline Median | Baseline Worst | Target Ceiling / Floor | Tolerance Limit (> 20% regression block) |
|---|---|---|---|---|---|
| `NFR-001` | Cold Start | 4.2 s | 4.8 s | ≤ 10.0 s | > 5.04 s blocks gate |
| `NFR-002` | 250k Import | 37.26 s | 41.1 s | ≤ 60.0 s | > 44.71 s blocks gate |
| `NFR-003` | Dashboard Interaction | 1.15 s | 1.4 s | ≤ 2.0 s | > 1.38 s blocks gate |
| `NFR-004` | PPT Deck Generation | 8.2 s | 9.1 s | ≤ 15.0 s | > 9.84 s blocks gate |
| `NFR-005` | Peak Memory (250k) | 1.12 GB | 1.22 GB | ≤ 1.50 GB | > 1.34 GB blocks gate |
| `NFR-006` | Installer Size | 295 MB | 295 MB | ≤ 500 MB | > 354 MB blocks gate |
| `NFR-007` | Full Rule Run | 41.5 s | 45.2 s | ≤ 60.0 s | > 49.8 s blocks gate |
| `NFR-009` | Excel Pack Generation | 62.4 s | 68.1 s | ≤ 120.0 s | > 74.88 s blocks gate |

---

## Regression Watch Comparison Procedure

1. **Execution Protocol:**
   - Run the full performance suite (`python -m pytest tests -m perf`) or individual timed benchmarks 5 consecutive times on a quiet reference machine instance.
   - Record the median and worst-case durations.
2. **Comparison Rule:**
   - Compare new median result against the baseline median.
   - Formula: $\text{Regression } \% = \frac{\text{New Median} - \text{Baseline Median}}{\text{Baseline Median}} \times 100$
3. **Gate Blocking Rule:**
   - If **Regression % > 20%** on any NFR metric, the release gate is **blocked** automatically.
   - Unblocking requires a formal root cause analysis, entry in `CHANGELOG.md`, and re-baselining approval per Doc 14 rules.
