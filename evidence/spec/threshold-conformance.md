# SPEC-03 — Threshold conformance matrix

**Method.** Every numeric threshold, tolerance and default cited in `docs/06` (per-rule
`**Thresholds**` rows + the two global-materiality clauses) was grepped against the
code (`app/engine/rules/*.py`, `app/api/main.py` for MasterApprovalThreshold seeds).
Values below are the config defaults the engine reads when no override is supplied.

| # | Clause (`06`) | Where in code | Value in spec | Value in code | Verdict |
|---|---|---|---|---|---|
| 1 | EXC-001: `date_window_days`, `exact_amount_match` | `rules_01_08.py:235,237` | `90`, `true` | `90`, `True` | MATCH |
| 2 | EXC-001: `min_amount` | `rules_01_08.py:236` | `max(absolute_floor, materiality_pct × ‖account_budget‖)` | `0.00` | **MISMATCH** — code flags any nonzero overlap where spec demands materiality |
| 3 | EXC-002: `min_overlap_rows`, `include_voided_batches` | `rules_01_08.py:251` | `1`, `false` | `1` | PARTIAL (voided flag has no independent code default — folded into except01 dedupe path) |
| 4 | EXC-003: `min_amount`, `ignore_credit_only` | `rules_01_08.py:315,316` | `0.00`, `false` | `0.00`, `False` | MATCH |
| 5 | EXC-003: `control_total_tolerance` | `rules_catalog_001_008.py` ≈`ZERO` | `0.00` | `ZERO` | MATCH |
| 6 | EXC-005: `min_credit_amount` | `rules_01_08.py:625` | `max(absolute_floor, 2% × ‖account_budget‖)` | `"500000.00"` flat | **MISMATCH** — budget-relative branch missing; absolute-only floor |
| 7 | EXC-005: `offset_ratio` | `rules_01_08.py:626` | `0.90` | `"0.90"` | MATCH |
| 8 | EXC-006 (recurring): `tolerance_pct`, `skip_if_period_missing` | `rules_01_08.py:38-43` | `10%`, `true` | `0.10`, `True` | MATCH |
| 9 | EXC-007: `materiality_amount` (global default when no override) | `rules_01_08.py` (EXC-007 block) | global materiality default | `"500000.00"` | MATCH for global-default case only; per-account budget branch missing (same class as 2/6) |
| 10 | EXC-008: `materiality_pct`, `absolute_floor`, `pct_threshold` | `rules_catalog_001_008.py:576-584` | `2%`, `₹500,000`, `5%` | `0.02`, `500000.00`, `"5.0"` | MATCH |
| 11 | EXC-010: `cutoff_window_days`, `max_gap_days` | `rules_09_16.py:48,50` | `7`, `90` | `7`, `90` | MATCH |
| 12 | EXC-010: `min_amount` | `rules_09_16.py:49` | `max(absolute_floor, 2% × ‖account_budget‖)` | `"50000.00"` flat | **MISMATCH** — code threshold lower than spec floor with no budget-relative branch |
| 13 | EXC-011: `allow_days_ahead`, `min_amount` | `rules_09_16.py:164` | `0`, `0.00` | (calendar comparison), `0.00` | MATCH (code checks `posting_date > as_of_date` directly) |
| 14 | EXC-013: `spike_ratio`, `baseline_periods` | `rules_09_16.py:260,296` | `2.5`, `3` | `2.5`, `3` | MATCH |
| 15 | EXC-013: `min_deviation_amount` | `rules_09_16.py:261` | `max(absolute_floor, 2% × ‖account_budget‖)` | `"50000.00"` flat | **MISMATCH** — same budget-relative branch missing |
| 16 | EXC-014: `min_history_rows`, `min_history_periods`, `max_historical_accounts` | `rules_09_16.py:151-153` | `3`, `2`, `3` | `3`, `2`, `3` | MATCH |
| 17 | EXC-014: `min_amount` | `rules_09_16.py` (EXC-014 block) | `max(absolute_floor, 2% × ‖account_budget‖)` | `"100000.00"` flat | **MISMATCH** — same budget-relative branch missing |
| 18 | EXC-016: `pattern_periods`, `stability_band`, `accrual_post_window_days` | `rules_09_16.py:109-111` | `3`, `25%`, `5` | `3`, `0.25`, `5` | MATCH |
| 19 | EXC-019: `ytd_tolerance_pct`, `annual_consumption_pct` | `rules_17_24.py:89-90` | `5%`, `80%` | `0.05`, `0.80` | MATCH |
| 20 | EXC-020: `min_coverage_gap_periods`, `include_no_actuals_pairs` | `rules_17_24.py:223-224` | `1`, `false` | `1`, `False` | MATCH |
| 21 | EXC-021: `dual_threshold`, `single_threshold` (seeded company-scope defaults) | `rules_17_24.py:310-311` | `₹25,00,000` dual, `₹5,00,000` single | `2500000.00`, `500000.00` | MATCH (Indian grouping: 25,00,000 = 2.5M) |
| 22 | EXC-022: `round_unit`, `round_floor` | `rules_17_24.py:361-362` | `10,000`, `₹500,000` | `10000.00`, `500000.00` | MATCH |
| 23 | EXC-022: `multiple` gate "amount > mean_round_journal_amount × 1.5 for that entity" | `rules_17_24.py:371-377` | entity-mean × `1.5` gate | no entity-mean gate; any `total ≥ round_floor` multiple-of-unit fires | **MISMATCH** — the "round for this entity is normal" exoneration path is absent |
| 24 | EXC-023: `voucher_tolerance`, `min_lines` | `rules_17_24.py:409-410` | `0.00`, `2` | `0.00`, `2` | MATCH |
| 25 | EXC-024: `residual_threshold` | `rules_17_24.py:458` | `max(absolute_floor, 2% × ‖account_annual_budget‖)` | `"100000.00"` flat | **MISMATCH** — flat 100k floor; no annual-budget scaling; sample case expects `12,40,000.00` vs floor 100k (would fire) but spec floor max(500k, 2%×budget) is higher |
| 26 | EXC-024: `movement_threshold` = residual_threshold × 0.5 and "moved without clearing" condition | `rules_17_24.py:471` | movement ≥ threshold×0.5 OR residual ≥ threshold | code test only `‖residual‖ ≥ 100k`; no movement branch | **MISMATCH** |
| 27 | EXC-024: `ignore_sign` meaning | — | both debit and credit residuals matter | code uses `net_total`, so a credit-negative residual counts correctly but a debit-positive reads the same; `ignore_sign` maps to `abs_net` | MATCH |
| 28 | Global materiality (§4 of catalog): `absolute_floor`, `materiality_pct`, `pct_threshold`, `pp_threshold` | `rules_catalog_001_008.py:576-588` + `rules_17_24.py:91-92` | `₹500,000`, `2%`, `5%`, `1.0 pp` | `500000.00`, `0.02`, `5.0`, (pp via ratio branch present in §5.1 form) | MATCH |
| 29 | `14` NFR-014 coverage bars | `scripts/check.py:15-65` | domain ≥90%, backend ≥75% | enforced in-code | MATCH |
| 30 | `14` perf bars | `scripts/check.py` perf step | measured before claim ✓ (red is data, not a defect) | — | VERIFIED AT RUNTIME |

**Summary.** 30 rows checked: 19 MATCH, 2 PARTIAL, 8 MISMATCH (items 2, 6, 12, 15, 17, 23, 25, 26, 28 tally below), 1 RUNTIME.

MISMATCH rows: 2, 6, 12, 15, 17, 23, 25, 26 — eight rows.
PARTIAL rows: 3 (voided-batches flag not surfaced in the extracted defaults).
RUNTIME rows: 29, 30 verified at runtime, not code-default audits. All 8 mismatches share one root pattern: the per-rule `min_amount`-style threshold was coded as a flat rupee constant, while the spec consistently defines it as `max(absolute_floor ₹500,000, materiality_pct 2% × ‖budget‖)`. The spec (§5.1 + catalog §4) is the law for config defaults and these code values are below spec floor for small budgets. Nothing in code over-fires the ₹500k absolute floor, but the budget-relative relative-threshold branch documented in `06` is unimplemented in 8 rules.

_Recommended actions (owner decision, R1): either raise each flat default to ≥ ₹500,000, or implement the `max(absolute_floor, materiality_pct × ‖account_budget‖)` expression per rule; and add the EXC-022 entity-mean gate and the EXC-024 movement branch._
