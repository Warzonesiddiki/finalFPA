# UX-09 — Analyst Maths Audit: The Twelve Numbers

**Document Reference**: `docs/UX-09_ANALYST_MATHS_AUDIT.md`
**Status**: Draft v0.1
**Last updated**: 2026-10-09
**Owning FRs/areas**: the arithmetic a finance controller relies on — the twelve numbers that must never be wrong, and the path that proves each one

---

## 1. Purpose

An FP&A analyst who cannot trust a number will not use the tool. This document names the **twelve
numbers** that matter most in a month-end close, states exactly how each is computed, what "wrong" looks
like for each, and what proves the tool gets it right. It is an audit, not a feature spec — the features
are in `02`/`05`/`06`/`07`; this document is the *trust layer* on top.

The rule: **a number on a screen, in a workbook, or on a slide is trusted only if it traces through this
document to a definition in `05` or `07` and a test that proves it**.

---

## 2. The Twelve Numbers

### N1. Trial Balance — Debit = Credit

| Field | Value |
|---|---|
| **What it is** | For every imported batch, total debit equals total credit at minor-unit precision |
| **Why it matters** | If this is wrong, every number downstream is untrustworthy — there is no "close enough" in double-entry |
| **Definition** | `04` §12 / `IMP-023`: journal exact debit=credit for GL; sub-ledger net within tolerance per `DEC-056` |
| **What wrong looks like** | A batch commits with debit ≠ credit; the imbalance is absorbed silently into some account |
| **How the tool proves it** | `IMP-023` fails the batch before commit; `corpus_integrity()` in `scripts/acceptance` reports every batch's debit/credit/net; `scripts/verify_trial_balance.py` PASS on the generated corpus |
| **Evidence** | `evidence/acceptance_report.json` → `corpus[]` → `total_debit`, `total_credit`, `net_imbalance` per file; `scripts/verify_trial_balance.py` exit 0 |

**Assertion**: On the current corpus, every committed batch is balanced. The GL actuals file
(`d365_gl_actuals.csv`) commits 250,503 rows with debit = credit = ₹15,672,231,601.81.

---

### N2. Variance — Actual − Budget

| Field | Value |
|---|---|
| **What it is** | The difference between actual and budget for any account/period/grain |
| **Why it matters** | It is the headline number of the entire product — the first thing an analyst looks at |
| **Definition** | `05` §3: `variance = actual − budget`, sign convention fixed, never flipped |
| **What wrong looks like** | Variance shows budget − actual; or the sign flips between screens; or a zero-budget line shows `0.00` instead of `n/a` |
| **How the tool proves it** | `TST-CALC-17` asserts debit/credit → net sign convention; `TST-BVA-03` drills any variance to transactions that sum to it exactly; cross-artifact equality (`NFR-015`) asserts engine = UI = Excel = PPT |
| **Evidence** | `05` §3; `tests/rules/` per-rule recall; `cross_artifact.json` (when generated) |

**Assertion**: Variance sign convention is fixed in `05` §3 and enforced by `TST-CALC-17`. Any screen
or export that shows the opposite sign is a defect.

---

### N3. Variance % — Relative to Budget

| Field | Value |
|---|---|
| **What it is** | Variance expressed as a percentage of budget |
| **Why it matters** | A ₹1,00,000 variance is material against a ₹2,00,000 budget and noise against a ₹10,00,00,000 budget — the % tells you which |
| **Definition** | `05` §4 / `CALC-011`: `variance% = variance / budget`, with defined zero-budget behaviour |
| **What wrong looks like** | Budget = 0 shows `inf` or `0.00%` instead of `n/a`; both actual and budget = 0 shows `n/a` instead of `—`; negative denominator flips the sign |
| **How the tool proves it** | `TST-CALC-18` asserts the three zero-budget cases; `TST-XL-*` and `TST-PPT-12` extend to export strings; `n/a` vs `—` distinction enforced in every surface (`NFR-015`) |
| **Evidence** | `05` §4; `CALC-011`; `TST-CALC-18`; `05` §G.1 (no epsilon) |

**Assertion**: The three zero-budget cases are deterministic and identical in every surface. `n/a` (÷0)
and `—` (0/0) are never collapsed.

---

### N4. Favourability — Is This Variance Good or Bad?

| Field | Value |
|---|---|
| **What it is** | Whether a variance is favourable or adverse for the business, direction-aware by account type |
| **Why it matters** | An expense under budget is good; revenue under budget is bad — the same variance amount, opposite meaning |
| **Definition** | `05` §4.3 / `CALC-012`: favourability by statement-line type (revenue/expense/memo), with balance-sheet/other treatment |
| **What wrong looks like** | A favourable expense variance shown as adverse; a balance-sheet line given a favourability label it should not have; colour-only signal with no text |
| **How the tool proves it** | `TST-CALC-19` asserts favourability per account type including the balance-sheet/other treatment; `TST-UI-09` asserts no colour-only signal — every semantic colour has a sign/word (`Fav`/`Adv`) |
| **Evidence** | `05` §4.3; `CALC-012`; `TST-CALC-19`; `TST-UI-09` |

**Assertion**: Favourability is shown as colour **plus** a `+`/`−`-style sign or `Fav`/`Adv` label so it
survives black-and-white print and colour blindness (`08` §9).

---

### N5. MTD / YTD / PY / TTM — Period Window Totals

| Field | Value |
|---|---|
| **What it is** | The total for the current month, year-to-date, prior-year same period, prior-year YTD, and trailing twelve months |
| **Why it matters** | Every variance and trend is relative to one of these — if the window total is wrong, everything relative to it is wrong |
| **Definition** | `05` §2.3: MTD = current period; YTD = sum of periods in fiscal year to date; PY MTD = same period prior year; PY YTD = same YTD prior year; TTM = trailing 12 periods where data exists |
| **What wrong looks like** | YTD includes a period that is not in the fiscal year; PY shows `0.00` when prior-year data exists; TTM shows fewer than 12 periods without labelling it; a window total does not equal the sum of its drilled rows |
| **How the tool proves it** | `TST-CALC-16` asserts every window including "history does not exist yet" behaviour; `TST-BVA-01` asserts every matrix total = sum of visible rows after every filter/sort; `TST-BVA-09` asserts `n/a` vs `—` in PY comparisons |
| **Evidence** | `05` §2.3; `TST-CALC-16`; `TST-BVA-01`; `TST-BVA-09` |

**Assertion**: A window total is always labelled with its window (`MTD`/`YTD`/`TTM`), and no screen or
export shows a period total without naming its window (`FR-BVA-002`).

---

### N6. Drill-Through — Sum of Transactions = Displayed Figure

| Field | Value |
|---|---|
| **What it is** | Every displayed figure, when drilled to transactions, reconciles exactly to the sum of those transactions |
| **Why it matters** | This is the single most important trust property: an analyst who clicks a number must land on transactions that add up to it exactly |
| **Definition** | `FR-BVA-004`: drill path from any figure to the transactions that compose it; `05` §4: exact Decimal, no rounding drift |
| **What wrong looks like** | Drilling a ₹10,00,000 variance shows transactions summing to ₹9,99,999.99 or ₹10,00,000.01; or the drill shows transactions from a different period/entity; or the drill is empty for a figure that has transactions |
| **How the tool proves it** | `TST-BVA-02`: 100% drill traceability — every displayed number drills to transactions whose sum equals it exactly (exact Decimal); `TST-BVA-03`: ≤ 5 clicks, ≤ 5 minutes end-to-end on 250k rows |
| **Evidence** | `FR-BVA-004`; `05` §4; `TST-BVA-02`; `TST-BVA-03` |

**Assertion**: This is the invariant that, if it ever fails, is an S1 defect. It is tested at `TST-BVA-02`
as a property over the full sample dataset: zero violations.

---

### N7. KPI — Gross Margin %, Opex %, Margin Ratio

| Field | Value |
|---|---|
| **What it is** | The six KPIs in `KPI-001…006`, each with a defined formula, guard, and label |
| **Why it matters** | KPIs are the headline ratios on Home and in the pack — if the gross margin % is wrong, the narrative around it is wrong |
| **Definition** | `05` §5 / `KPI-001…006`: each formula, divide-by-zero behaviour, and the "never shown alone" score rule |
| **What wrong looks like** | A KPI shows `inf` or `0.00` when the denominator is zero; a KPI that requires absent data (e.g. headcount) is shown at all; a KPI value does not match its `05` definition on the golden dataset |
| **How the tool proves it** | `TST-CALC-21` asserts every KPI formula, guard, and label including the "never shown alone" rule; `TST-BVA-10` asserts the KPI cards on Home match their `05` definition |
| **Evidence** | `05` §5; `KPI-001…006`; `TST-CALC-21`; `TST-BVA-10` |

**Assertion**: Every KPI on Home matches `05` §5 on the golden dataset. The data-quality score is never
shown alone (`KPI-006` / `CALC-050`).

---

### N8. Data-Quality Score — 0 to 100, Never Hiding a Failure

| Field | Value |
|---|---|
| **What it is** | A weighted 0–100 score over the import's validation checks |
| **Why it matters** | A single number that summarises import health — but must never be used as the only signal, because a perfect score with a hidden failure is worse than no score |
| **Definition** | `CALC-050` / `04` §16: weighted formula, per-check breakdown one click away, score never masks a failure |
| **What wrong looks like** | A batch with a failed check shows DQ = 100; the score is shown without the failed-check list; the score is a hardcoded literal instead of computed |
| **How the tool proves it** | `DEF-021` fixed the literal-100 bug; `TST-CALC-24` asserts the formula, weight table, and "score never masks a failure" guarantee; `TST-IMP-33` asserts every malformed file produces its specific message and a computed (not literal) score |
| **Evidence** | `CALC-050`; `04` §16; `DEF-021`; `TST-CALC-24`; `acceptance_report.json` → `corpus[]` → `data_quality_score` per file (93, 100, 100, 100, 100, 100, 92 — computed, not literal) |

**Assertion**: The DQ score is computed by `calculate_quality_score()`, not a literal. A batch with any
failed check cannot display a perfect score. The per-check breakdown is one click away.

---

### N9. Bridge — Waterfall Sum = BvA Total

| Field | Value |
|---|---|
| **What it is** | The waterfall from Budget to Actual, with the top-N variance drivers plus an "Other" bar |
| **Why it matters** | The bridge is the visual story of the month — if the bars don't sum to the start and end, the story is wrong |
| **Definition** | `FR-BVA-005`: waterfall start = budget, end = actual, bars = top-N drivers + Other; sum reconciles exactly to BvA totals |
| **What wrong looks like** | The bridge's start/end/bar sum does not equal the BvA matrix totals; a drilled bar does not highlight the right variance; the "Other" bar is empty when there are more than N drivers |
| **How the tool proves it** | `FR-BVA-005` acceptance: the waterfall's start, end and bar sum reconcile exactly to the BvA totals in the matrix; `TST-BVA-11` asserts Top-N ordering is deterministic (same rows in app/Excel/deck) |
| **Evidence** | `FR-BVA-005`; `05` §4; `TST-BVA-05`; `TST-BVA-11` |

**Assertion**: The bridge is not an independent calculation — it is a rearrangement of the BvA matrix.
Start = budget total, end = actual total, bars sum to (end − start). Any mismatch is a defect in the
bridge renderer, not in the engine.

---

### N10. Control Total — Import Reconciliation

| Field | Value |
|---|---|
| **What it is** | The comparison of file totals vs loaded totals vs client-provided control totals |
| **Why it matters** | It proves the import landed intact — if the control total is off, something was dropped, doubled, or mis-parsed |
| **Definition** | `04` §12 / `FR-IMP-017`/`018`: file-level control totals, duplicate candidate detection, cross-batch overlap report |
| **What wrong looks like** | A file imports with a control total mismatch and no warning; a duplicate is silently double-counted; a cross-batch overlap is committed without a report |
| **How the tool proves it** | `TST-IMP-01…32` — one test per check, including `IMP-017` (within-file duplicates) and `IMP-018` (cross-batch duplicates); `TST-IMP-36` asserts re-import guard (identical checksum blocked, different checksum with overlap → report before commit) |
| **Evidence** | `04` §12; `FR-IMP-017`/`018`; `TST-IMP-17`/`18`/`36`; `acceptance_report.json` → `corpus[]` → `total_debit`/`total_credit` per file |

**Assertion**: Every import produces a validation report with per-check results. A control-total variance
beyond tolerance fails the import or requires an explicit recorded acceptance (`FR-IMP-017`).

---

### N11. Forecast — Method Arithmetic and Accuracy

| Field | Value |
|---|---|
| **What it is** | The rolling forecast's four methods (run-rate, prior-year, budget, driver-based), each with eligibility guards and exact arithmetic |
| **Why it matters** | The forecast is the forward-looking number the pack reports — if the method arithmetic is wrong, the forecast is misleading |
| **Definition** | `07` §4 / `05` §9: each method's formula, applicability guard, and "never a silent substitution" rule |
| **What wrong looks like** | A method is used when ineligible (no history, locked period); a method's arithmetic does not reproduce the `05` fixture; an override is applied without a reason; a locked version is changed |
| **How the tool proves it** | `TST-FC-01…08` — one per method, asserting arithmetic on its fixture, the applicability guard, and the "never a silent substitution" rule; `TST-FC-10` asserts lock semantics; `TST-FC-11` asserts accuracy metrics with worked examples |
| **Evidence** | `07` §4; `05` §9; `TST-FC-01…14`; `07` §8 (accuracy metrics) |

**Assertion**: Every forecast method's arithmetic reproduces the `05` fixtures. Eligibility guards refuse
ineligible combinations with the documented message. A locked version is immutable (`TST-FC-10`).

---

### N12. Cross-Artifact Equality — Engine = UI = Excel = PPT = CSV

| Field | Value |
|---|---|
| **What it is** | For one fixed filter state, the same numbers appear in all five surfaces at display precision, zero tolerance |
| **Why it matters** | If the workbook shows a different number than the screen, the analyst cannot trust either — and the pack sent to the CFO may disagree with the screen they used to approve it |
| **Definition** | `NFR-015` / `14` §7: engine JSON = UI payload = Excel named cells = PPT text frames by shape name = CSV row values, at display precision, zero tolerance |
| **What wrong looks like** | The Excel pack shows ₹15,672,231,601.81 where the screen shows ₹15,672,231,601.79; a variance % differs between the deck and the workbook; a KPI card differs between Home and the pack |
| **How the tool proves it** | `14` §7.2 harness: freeze filter state → capture engine + UI → generate pack + deck → read both back with parsers (openpyxl, python-pptx) → compare every value at display precision → `cross_artifact.json`; any difference is an S1 defect |
| **Evidence** | `NFR-015`; `14` §7; `TST-XL-*` + `TST-PPT-13` + `TST-API-14` under one harness |

**Assertion**: This is the strongest guard against display and export drift. It is tested as `TST-API-14` +
`TST-XL-*` + `TST-PPT-13` under one harness. Any difference is an S1 defect — the renderer or parser is
fixed, never the engine, never by relaxing the test.

---

## 3. The Trust Chain

Every number an analyst sees must trace through this chain:

```
Screen / Workbook / Slide
  → calculation definition in 05 or 07 (formula, sign convention, zero-budget rule)
  → test that proves it (TST-CALC-nn, TST-BVA-nn, TST-FC-nn, TST-RUL-nn)
  → cross-artifact equality (NFR-015) where it appears in more than one surface
  → acceptance recall (does the rule that raises it find its planting? 14 §5.3)
```

A number that cannot trace through all four links is not trusted. The analyst who sees a number that
cannot trace is entitled to ask "where does this come from?" and get a drill path that answers it.

---

## 4. What Breaks Trust — and What Fixes It

| Trust break | Severity | Fix |
|---|---|---|
| A drill-through does not sum to the figure | S1 | Fix the renderer or the drill query; regression test that fails before the fix |
| A variance sign flips between screens | S1 | Fix the sign convention in one place (`05` §3); cross-artifact equality catches the drift |
| A KPI shows `inf` or `0.00` on zero denominator | S2 | Fix the divide-by-zero rule in `05` §4; `TST-CALC-18` catches it |
| The DQ score is 100 on a failed batch | S1 | Fix the score formula; `DEF-021` + `TST-CALC-24` catch it |
| The workbook differs from the screen | S1 | Fix the renderer or parser; `NFR-015` harness catches it; never relax the test |
| A forecast method is used when ineligible | S2 | Fix the eligibility guard; `TST-FC-01…08` catch it |
| A bridge bar does not sum to the BvA total | S1 | Fix the bridge renderer; `FR-BVA-005` acceptance catches it |
| A window total includes a period not in the fiscal year | S2 | Fix the period-window definition; `TST-CALC-16` catches it |

---

## 5. The Audit Procedure

When an analyst (or controller, or auditor) asks "can I trust this number?", the answer is:

1. **Drill it.** Click the number. Do the transactions sum to it exactly? If yes, the engine is honest.
2. **Trace it.** Does the drill show the source file, batch, and row? If yes, the provenance is complete.
3. **Check the window.** Is the period window labelled (`MTD`/`YTD`/`TTM`)? If yes, the context is clear.
4. **Check the surface.** If the number is in a pack, does it match the screen? (`NFR-015` — when green).
5. **Check the rule.** If it is an exception, did the rule that raised it find its planting? (`14` §5.3 — when green).

A number that passes all five is a trusted number. A number that fails any is a flagged number, and the
flag is the recovery path, not a verdict of wrong.

---

## 6. Relationship to Other Docs

| Doc | Relationship |
|---|---|
| `05_CALCULATION_SPEC.md` | Owns the formulas, sign conventions, zero-budget rules, KPIs |
| `07_FORECAST_METHODS_SPEC.md` | Owns the forecast method arithmetic and accuracy |
| `06_EXCEPTION_RULES_CATALOG.md` | Owns the exception rules that raise findings |
| `08_UI_UX_SPEC.md` | Owns the display conventions, favourability signals, state matrix |
| `14_TESTING_QA_PLAN.md` | Owns the test IDs, NFR numbers, acceptance bars |
| `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | Owns the defect severities and the UAT scripts that exercise these numbers |
| `card_acceptance_standard.md` | Owns the acceptance standard every card (including the tests for these numbers) must meet |

---

## 7. Frozen Constants

| Constant | Value | Source |
|---|---|---|
| Trial balance | debit = credit, exact, minor-unit precision | `04` §12 / `IMP-023` |
| Variance sign | actual − budget, fixed | `05` §3 |
| Zero-budget variance % | `n/a` (÷0), `—` (0/0), absolute value of negative denominator | `05` §4 / `CALC-011` |
| Favourability | by statement-line type; balance-sheet/other neutral | `05` §4.3 / `CALC-012` |
| Period windows | MTD, YTD, PY MTD, PY YTD, TTM (12 periods where data exists) | `05` §2.3 |
| Drill traceability | 100%, exact Decimal, ≤ 5 clicks, ≤ 5 min on 250k rows | `FR-BVA-004`; `TST-BVA-02`/`03` |
| KPI count | 6 (`KPI-001…006`), never shown alone | `05` §5 |
| DQ score | 0–100, weighted, never masks a failure | `CALC-050` / `04` §16 |
| Bridge | start = budget, end = actual, bars = top-N + Other, sum = BvA total | `FR-BVA-005` |
| Control totals | file-level, duplicate detection, cross-batch overlap | `04` §12 / `FR-IMP-017`/`018` |
| Forecast methods | 4 (run-rate, prior-year, budget, driver-based), with eligibility guards | `07` §4 / `05` §9 |
| Cross-artifact equality | engine = UI = Excel = PPT = CSV, display precision, zero tolerance | `NFR-015` / `14` §7 |
| Acceptance bars | recall ≥ 29/32, 0/8 controls, 18/18 High, extras ≤ 3/rule, stability, 24/24 wired, 0 zero-coverage | `14` §5.3 |

These constants are frozen. Changing any of them is a spec change with an impact note, recorded in `18`
as a DEC, and reflected in `CHANGELOG`. A test that passes by relaxing one of these is not a passing test.
