# Acceptance remediation map — 2026-10-04

Owner: Engine / Acceptance. Source of truth: `evidence/acceptance_report.json` + `.md`
(run at corpus checksum `0667630f…e37f` for `d365_gl_actuals.csv`). Doc 14 §5.2 step 6 makes a
red acceptance run release-blocking, so this file records **what the run says, why, and what each
item needs** — it is not a claim that the bars pass.

## 1. What this session changed, and the measured effect

| Change | Evidence | Status |
|---|---|---|
| **DEF-030** — `ImportRepository.commit_batch` bulk-load rewritten from DuckDB `executemany` (236 rows/s) to batched multi-row `INSERT` inside one explicit transaction | `scratch/bench_duckdb_insert.py`; 250,040-row GL commit timed at **72.6 s** (was ~19 min); `tests/unit/test_def030_bulk_insert.py` (4 tests, rollback mutation-verified) | Fixed — pending reporter confirmation |
| **Corpus baseline window** — `generate_sample_data.py` now emits baseline rows only inside FY26-P01…P09 (2026-04-01…2026-09-30); post-September rows are now only the planted P9/P10/P11 cases the answer key describes | doc 06 §7 + P11's run-date note; EXC-011 extras **20,691 → 1**, total extras **21,112 → 422** | Fixed |
| **Planted-residual balancing legs** — the generator computes and emits the balancing legs itself (per entity × month, measured, never hard-coded); the corpus is reproducible and loadable from one command again | `scripts/verify_trial_balance.py` → `PASS - PERFECT BALANCE`; doc 14 §5.2 step 1 amended | Fixed |
| **Harness honesty** — stale DEF-010 divergence text (which still described the removed sub-ledger carve-out) replaced with the measured consequence; duplicate per-rule heading removed | `app/engine/rules/acceptance.py`; regenerated report | Fixed |

## 2. Current verdict (still FAIL — the remaining work, classified)

| Bar | Requirement | Measured |
|---|---|---|
| Planted-exception recall | ≥ 29 of 32 | **11/32 = 34.4 %** |
| Control precision | 0 of 8 controls raise | **1 fired** (P30, EXC-018) |
| High-severity recall | 18 of 18 | **6/18** |
| Extra findings | every extra justified | **422** across 10 rules |
| Stability | two identical runs | PASS |
| Rule catalog coverage | 24/24 wired | PASS |
| Zero-coverage rules | every planted rule raises | **14 rules** with zero findings |

### 2.1 The 21 misses, by cause

| Cause | Plantings | Evidence | Needs |
|---|---|---|---|
| **Sub-ledger sources rejected (unconditional IMP-023)** | `P1` (bank ledger), `P9` (`batch_040` payroll/procurement) | Report divergences: bank 0 of 499 and payroll 0 of 399 rows landed; doc 06 §8's P1 case requires the *malformed* bank fixture imported **with a configured ₹500 tolerance**, which the corpus never imports | **OQ-025** (owner): rebuild the fixtures balanced vs scope the gate per source type |
| **Answer-key keys the corpus/engine cannot produce** | `P2`×3 (needs an earlier overlapping **batch 37**), `P3` (needs a control-totals block; key `batch_039\|gl_control_total`), `P6` (key `entity\|IN02` vs EXC-006's default `entity_account`), `P8` (key includes cost centre and the rule's documented ₹500,000 floor suppresses the ₹12,500 plant) | Per-rule table: EXC-002 raised 0; EXC-006 raised 34 (key mismatch); EXC-008 raised 0; `sample-data/` contains **no earlier copy** of `VCH-2026-0915-001/002` and no control-totals CSV | **OQ-026** (owner) + **OQ-027** (import-history fixture) |
| **Rules raised, key/threshold differs** | `P20` (1 finding), `P21`×2 (8 findings), `P24` (1 finding) | Per-rule table; P21's catalog key is `company\|voucher\|threshold_id` while the key names the voucher only; P24's catalog key is `company\|account\|period` vs the key's `IN01\|1999\|suspense` | Key-format decision (**OQ-026**) or engine/report change |
| **Zero findings — needs per-rule investigation with the corpus in front of it** | `P4b` (`cost_center\|CC-999`), `P10`×2 (cut-off), `P12` (negative expense credit), `P13`×2 (spikes), `P14` (vendor→account), `P16` (accrual pattern), `P15b` (SaaS recurring charge not detected) | Per-rule table (0 findings each); each has a doc 06 sample case to diff against | Rule-by-rule work against the loaded corpus; **not** a corpus-only fix |

### 2.2 The 422 extras, by cause

| Rule | Extras | Cause |
|---|---|---|
| `EXC-017` | 205 | Rule fires on budget-vs-actual noise: the generator draws actuals and budget **independently at random** per (period, entity, cost centre, account), so "material unbudgeted spend" is satisfied all over the corpus rather than only at the planted case |
| `EXC-018` | 94 | Same root cause for the material-variance rule (and one of these is the **P30 control**, below) |
| `EXC-019` | 71 | Same root cause for the cumulative-overrun rule |
| `EXC-006` | 34 | `scope_grain = entity_account` default vs the answer key's entity-scope plant (see OQ-026) |
| `EXC-021` | 8 | Catalog key includes `threshold_id` (see 2.1) |
| `EXC-022` | 5 | Round-journal rule multiplies beyond the planted case |
| `EXC-023` | 2 | Voucher-level imbalance exists beyond the plant (the corpus's own balancing legs are single-line vouchers; `min_lines=2` excludes them, the extras come from other vouchers) |
| `EXC-024` / `EXC-020` / `EXC-011` | 1 each | Key-format / scope mismatches |

**The largest single lever is corpus coherence:** a sample budget and actuals generated from one plan
(actual = budget ± controlled noise, with only the planted variances material) would remove most of
the 370 `EXC-017/018/019` extras and make the "every extra justified" bar reachable. That is the
`PROP-001` mode split (`docs/18_PROPOSAL_FOR_GENERATOR_REBUILD.md`), now backed by a measurement.

### 2.3 Control precision

`P30` (`IN01|5200|CC-110`, EXC-018) fires because the corpus's random budget/actual pair satisfies the
AND-test the answer key says should fail for it (F13c: ₹900,000 variance but +2.25 % — below the 5 %
threshold). Once the corpus is coherent (2.2), this control's numbers can be authored exactly as doc
06 §7.2 describes instead of arriving at random.

## 3. Definition of done for this gate

1. `OQ-025`, `OQ-026`, `OQ-027` answered (or defaulted and recorded).
2. Corpus rebuilt for coherence (PROP-001) so controls are authored, not sampled.
3. Per-rule work for the ten zero-finding plantings in 2.1, each diffed against its doc 06 sample case.
4. `scripts/acceptance.py` exit 0, `scripts/check` green, re-run twice for the stability bar.
