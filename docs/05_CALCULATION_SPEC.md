> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-BVA-001`…`FR-BVA-016`, `FR-FC-002`/`FR-FC-007` (arithmetic), `FR-IMP-022` (score), `FR-EXC-013` (materiality), `FR-SET-005`/`FR-SET-006` (calendar, display); all formulas, tolerances, rounding, fiscal calendar, worked examples
> **TL;DR (≤ 15 lines):** This document owns every formula the product computes: the canonical sign
> convention (`Variance = Actual − Budget`, `net = debit − credit`), direction-aware favour*ability*, the
> MTD/YTD/PY/TTM window definitions, ratio/KPI arithmetic with divide-by-zero and percentage-point rules,
> rounding and display policy (compute at full precision, round only for display), the four forecast
> methods' arithmetic, forecast-accuracy metrics, the data-quality score, control-total variance,
> materiality thresholds, and the **tolerance policy** (exact equality at minor-unit precision — no
> epsilon anywhere in money paths). §12 contains **14 golden fixtures with exact numbers**, ready to lift
> into `tests/` as golden files. If a number is computed anywhere in the product, its formula is here.

---

# 05 — CALCULATION SPECIFICATION

## 1. Purpose, ownership boundary and conventions

This document owns **how numbers are computed**. Boundaries:

| Concern | Owner |
|---|---|
| Formula definitions, rounding, tolerances, window definitions, worked examples | **`05` (this document)** |
| Which rule raises which exception, thresholds, severities | `06` |
| Forecast *behaviour* (method selection, scenarios, locks, accuracy reporting, guidance) | `07` — it references the arithmetic defined here and does not restate it |
| Presentation (layout, chart types, colour rules) | `08` |
| Test IDs and NFR numbers | `14` |

**Universal conventions (binding):**

1. **Decimal only.** All money arithmetic uses Python `Decimal` in the engine and `DECIMAL(18,2)` in
   storage. Binary floats are forbidden in money paths; a schema/lint test fails the build if one appears.
2. **Compute at full precision; round at display.** Rounding is a rendering concern and never feeds a
   subsequent calculation.
3. **No epsilon.** Money comparisons use exact equality at minor-unit precision (Addon 4 §G.1). There is
   no "close enough" tolerance in the code path.
4. **One implementation.** Each formula below is implemented once in `app/engine/` and reused by the API,
   the Excel pack, the PPT deck and the CLI — so cross-artifact consistency is structural, not effortful.
5. **Every formula has an ID** (`CALC-nnn`, `KPI-nnn`) and at least one golden fixture (§12) and test (`14`).

## 2. Fiscal calendar and period assignment

### 2.1 Calendar definition (CALC-001)

The fiscal calendar is **data, not code** (`DimPeriod`, `03` §3.6):

| Parameter | Default | Configurable |
|---|---|---|
| Fiscal year start | January (period 1 = January) | Yes — any month; a 4-4-5 arrangement is a supported alternative |
| Periods per year | 12 | 12 or 4-4-5 |
| Period code format | `FY<yy>-P<nn>` | Display only; the stored identity is `(fiscal_year, period_number)` |
| Year label | `FY26` = the fiscal year that **ends** in 2026 | Yes (label only; no arithmetic depends on it) |

**No hardcoded calendar months anywhere.** Every window below is defined in terms of `DimPeriod` rows,
so a March year-start produces identical logic with different boundaries.

### 2.2 Period assignment rule (CALC-002)

| Rule | Detail |
|---|---|
| Default | **`posting_date` drives period assignment.** A transaction belongs to the period whose `start_date ≤ posting_date ≤ end_date` |
| Alternative | A project may be configured to use `document_date` instead; the choice is a project setting and appears in every export header |
| Source period column | If the source file supplies a fiscal period code, the derived period is compared with it; a mismatch is **reported** (validation warning) and never silently reconciled |
| Outside the calendar | A posting date outside every configured period → quarantine (`IMP-019`), never assigned to the nearest period |
| Document date | Used **only** by the cut-off exception rule (`06` `EXC-010`), never for period assignment (default configuration) |
| Closed periods | Facts in a closed period are immutable; the lock is enforced at write time (`03` §7 I5) |

### 2.3 Window definitions (CALC-003 … CALC-006)

Let `P` = the selected period, `Y` = the fiscal year containing `P`, and `n` = the number of loaded
periods in `Y` up to and including `P`.

| Window | Definition | Formula |
|---|---|---|
| **MTD** | The selected period only | `sum(net_amount) where period_id = P` |
| **YTD** | From the first period of the fiscal year through `P`, inclusive | `sum(net_amount) where fiscal_year = Y and period_number ≤ P.period_number` |
| **PY MTD** | The same period in the prior fiscal year | `sum(net_amount) where fiscal_year = Y−1 and period_number = P.period_number` |
| **PY YTD** | The prior year's equivalent YTD window (same number of periods) | `sum(net_amount) where fiscal_year = Y−1 and period_number ≤ P.period_number` |
| **TTM / rolling 12** (CALC-006) | The 12 periods ending at `P`, **where loaded**. If fewer than 12 are loaded, the window is `n` periods and the label states it | `sum(net_amount) over the last min(12, n) periods ending at P` |

**Window labels are always displayed** ("MTD (Sep-26)", "YTD (Apr-26 → Sep-26)", "TTM (7 of 12 periods)")
in the UI, in every export header, and on every chart. A total is never shown without its window.

## 3. Canonical sign conventions (CALC-007)

| Quantity | Definition | Note |
|---|---|---|
| `net_amount` | `debit − credit` | Stored; a debit increases the net, a credit decreases it |
| Line magnitude for expense accounts | `net_amount` | Expense debits are positive |
| Line magnitude for revenue accounts | `−net_amount` | Revenue credits are negative in `net_amount`, so revenue is presented as a positive figure |
| **Variance** | `actual − budget` | **The single canonical definition.** Every table, chart, Excel sheet, deck and CLI uses it |
| Variance direction | `+` = actual above budget, `−` = actual below budget | Direction is not a judgement; favour*ability* is (§4) |
| Presentation of negatives | Parentheses when the project setting is enabled: `(25,000.00)` | Display only; storage keeps the sign |

**Comparability rule:** a variance is only computed where both sides exist at the **same grain**
(§7). Where they do not, the UI shows the grain of each side and never a fabricated variance.

## 4. Variance, variance % and favour*ability* (CALC-010 … CALC-013)

### 4.1 Variance (CALC-010)

```
variance = actual − budget
```

- Computed in `Decimal` at minor-unit precision.
- Applies to any pair of comparable measures (Actual vs Budget, Actual vs Forecast, Forecast vs Budget,
  Actual vs PY with `budget` replaced by the comparator).

### 4.2 Variance % (CALC-011)

```
if |budget| > 0:  variance_pct = variance / |budget|
if budget = 0 and actual = 0:  variance_pct = null      → displayed as "—"
if budget = 0 and actual ≠ 0: variance_pct = undefined  → displayed as "n/a" (+ tooltip "no budget line")
```

- The denominator is the **absolute** value of the comparator, so the sign of the percentage always
  follows the sign of the variance.
- `null` (nothing to compare) and `undefined` (division by zero) are **distinct states** with distinct
  displays. Neither is ever `inf`, `NaN`, `0` or a crash.
- One shared helper implements this rule so every caller behaves identically.

### 4.3 Favour*ability* (CALC-012)

Favour*ability* is **direction-aware by statement-line type**, derived from `DimAccount.account_type`:

| Line type | Direction | Favourable when | Unfavourable when | Neutral when |
|---|---|---|---|---|
| Revenue | `higher_is_favourable` | `actual > budget` | `actual < budget` | equal |
| Expense / COGS | `lower_is_favourable` | `actual < budget` | `actual > budget` | equal |
| Balance sheet (asset, liability, equity) | `neutral` | — | — | always (no colour, no `Fav`/`Adv` label) |
| Memo / statistical | `neutral` | — | — | always |

**Display rules:** favour*ability* is never colour-only (P19) — it always carries a text or sign
element: `Favourable (▲)` / `Unfavourable (▼)` in tables, and `Fav`/`Adv` in the compact Excel column.
The exact colour tokens and label text are owned by `08`.

**Worked instances:** fixtures F2, F3, F4 and F5 in §12 cover revenue-favourable, expense-favourable,
expense-unfavourable and neutral/zero cases.

### 4.4 Percentage points vs percent (CALC-013)

| Measure type | Variance expressed as | Example |
|---|---|---|
| Money amount | Currency amount + % of comparator | `+80,000.00 (+8.0%)` |
| **Ratio / percentage** (e.g. gross margin %) | **Percentage points (pp)** | `40.0% vs 38.5% = +1.5 pp` |

A ratio variance must **never** be expressed as a relative percentage of a percentage: the difference
between 40.0% and 38.5% is `+1.5 pp`, not `+3.9%`. The UI labels the unit explicitly (`pp`), and fixtures
F10 and F11 assert both the correct value and the rejection of the incorrect one.

## 5. Ratio and KPI library (CALC-020 … CALC-027, KPI-001 … KPI-006)

### 5.1 Divides and guards

Every ratio uses the same guard helper: denominator `> 0` → compute; denominator `= 0` → `n/a`;
numerator and denominator both `0` → `—`. Ratios are stored at 6 dp and displayed at 1 dp.

### 5.2 KPI register (v1)

| ID | KPI | Formula | Guard behaviour |
|---|---|---|---|
| `KPI-001` | Gross margin % | `(revenue − COGS) / revenue` | revenue = 0 → `n/a` |
| `KPI-002` | Operating expense ratio | `opex / revenue` | revenue = 0 → `n/a` |
| `KPI-003` | Budget burn % | `YTD actual / annual budget` | annual budget = 0 → `n/a` |
| `KPI-004` | Revenue growth % (YoY) | `(actual − PY actual) / \|PY actual\|` | PY actual = 0 → `n/a` |
| `KPI-005` | Variance % (per line) | see CALC-011 | budget = 0 → `n/a` or `—` |
| `KPI-006` | Forecast accuracy (MAPE-lite) | see §9.2 | actual = 0 → `n/a` |

**Out of v1:** cost per head and any headcount-based KPI (parked, `BL-016`; no schema support). Balance
sheet ratios (current ratio, DSO, DPO) are parked with balance-sheet statements (`BL-010`).
**Rule:** adding a KPI requires a row here, a `05` changelog entry, and a golden fixture — never an
ad-hoc computation inside a screen.

## 6. Rounding and display policy (CALC-030, CALC-031)

### 6.1 Rounding rule

| Concern | Rule |
|---|---|
| Rounding mode | **Half-up** (banker's rounding is explicitly not used, so the rule is explainable to a finance user) |
| Currency display | 2 decimal places |
| Percentage display | 1 decimal place |
| Ratio display | 1 decimal place, unit labelled (`%`, `pp`, `×`) |
| Stored precision | Money 2 dp (minor units); ratios/rates 6 dp; never rounded in storage |
| Order of operations | Aggregate → compute → round **once** at the display boundary. No intermediate rounding |
| Comparisons | On unrounded stored values, exact equality; a comparison never uses the displayed value |

### 6.2 The sum-of-rounded rule (CALC-031) — mandatory footnote

**Totals and subtotals are always computed from unrounded values, then rounded. Therefore a displayed
column may not sum exactly to the displayed total.**

- The maximum discrepancy for a column of `n` rows is `n × 0.005` in the displayed unit.
- The UI shows a footnote on any table where `|Σ(displayed components) − displayed total| > 0`:
  *"Components may not sum to the total due to rounding."*
- The Excel pack applies the same rule and includes the same footnote; no row is ever adjusted to force
  the sum ("plugging" a line to make a column add up is forbidden).
- Fixture F6 demonstrates the case and asserts the footnote condition.

### 6.3 Display scale (CALC-032)

| Setting | Divisor | Label always shown | Example |
|---|---|---|---|
| Whole units | 1 | `₹` | `₹ 30,95,801.00` |
| Thousands | 1,000 | `₹ in thousands` | `₹ in thousands 3,095.80` |
| Lakhs | 100,000 | `₹ in lakhs` | `₹ in lakhs 30.96` |

Scale is **display-only**; the engine never computes scaled numbers. The label appears in the UI, the
Excel pack (header block and column headers) and the deck, identically (F-page fixtures assert this).

### 6.4 Negative presentation (CALC-033)

| Setting | Rendering | Storage |
|---|---|---|
| Parentheses (default for finance) | `(25,000.00)` | `-25000.00` |
| Minus sign | `-25,000.00` | `-25000.00` |
| Both | `(25,000.00)` in tables, `-25,000.00` in raw exports | `-25000.00` |

Digit grouping follows the project setting (Indian `1,23,456.00` or international `123,456.00`).
**Sign is never encoded by colour alone** (P19); the parenthesis/sign carries the meaning.

## 7. Aggregation, grain and hierarchy rules

| Rule | Detail |
|---|---|
| Lowest shared grain (CALC-040) | A comparison is computed at the lowest grain present on **both** sides. If budget exists only at `period × account` while actuals are at transaction level, actuals roll up to `period × account` and the UI states: *"Budget available at: month × account"* |
| Never imply unavailable precision | The UI must not show a variance at a grain where one side has no data; it shows the grain disclosure instead (FR-BVA-013) |
| Grouped entity totals (CALC-041) | Simple sum across entities with the label **"Simple sum — no eliminations"** wherever it appears; no intercompany netting in v1 |
| Hierarchy rollups (CALC-042) | Parent value = exact sum of its children. Unassigned accounts appear under a visible `Unmapped` node; an account assigned to a parent with no children appears as a direct child. Tested as an invariant over the whole sample dataset |
| Tie-to-children guarantee | If `parent ≠ Σ(children)` for any node, that is a **bug**, not a rounding artefact; the rollup test fails the build |
| Snapshot consistency | Comparisons for an issued pack use the frozen snapshot, not live data (`02` FR-PRJ-010) |

## 8. Data-quality score (CALC-050)

### 8.1 Formula

For a batch, let `R` = the set of checks that **ran** (submitted as `pass`, `fail` or `warn`; `skipped`
checks are excluded from both numerator and denominator), `w_c` = the configurable weight of check `c`
(defaults: High = 10, Medium = 5, Low = 2), and `d_c` = the deduction factor for check `c`:

| Check result | `d_c` |
|---|---|
| `pass` | 0.0 |
| `fail` (High / Medium / Low) | 1.0 |
| `warn` | 0.5 |
| `skipped` | excluded from `R` |

```
score = round_half_up( 100 × ( 1 − Σ_{c∈R} ( w_c × d_c ) / Σ_{c∈R} w_c ) , 0 )
```

### 8.2 Guarantees (why a score can never mask a failure)

1. **Bounded:** any failed High-severity check deducts at least `10 / 238 ≈ 4.2%`, so a batch with one
   failed High check **cannot score above 96** — a perfect 100 is impossible with any material failure.
2. **Decomposable:** the score is always displayed **alongside** the list of failed checks and their
   weights; the UI never shows the score alone (FR-IMP-022, Addon 3 §C.5).
3. **Deterministic:** same checks + same weights → same score.
4. **Versioned:** weight changes are project settings with history; a score always states the weight-set
   version that produced it.

### 8.3 Default weight totals (for the score denominator when every check runs)

| Severity | Checks | Weight each | Subtotal |
|---|---|---|---|
| High | 18 | 10 | 180 |
| Medium | 10 | 5 | 50 |
| Low | 4 | 2 | 8 |
| **Total** | **32** | — | **238** |

(Fixture F12 uses this table with a concrete failure set.)

## 9. Forecast arithmetic (CALC-060 … CALC-065)

Method **behaviour** (when each applies, scenarios, locks, guidance) is owned by `07`. The arithmetic is
defined here and only here.

### 9.1 Methods

| ID | Method | Formula | Guard / edge |
|---|---|---|---|
| `CALC-060` | **Locked actuals** | Closed periods take their actual values; no forecast is generated for them | Closed period with no actuals → treated as `0` **and** flagged in the forecast summary as "no actuals" |
| `CALC-061` | **Remaining-budget spread** | `remaining = annual_budget − Σ(actuals in loaded periods of the year)`; each remaining period gets `remaining / k` where `k` = number of remaining open periods | `k = 0` (year complete) → no rows generated; negative remaining → spread as computed (a documented, visible over-spend signal), never clamped silently |
| `CALC-062` | **Run-rate (last N actual months)** | `avg = Σ(net_amount over last N loaded actual periods) / N` | `N > loaded periods` → clamped to the loaded count with a visible notice; `N = 0` → not eligible |
| `CALC-063` | **3-month average** | Identical arithmetic to `CALC-062` with `N = 3` fixed | Same guards; exists as a named choice for users who want a fixed, explainable window while their run-rate setting differs. **Documented as an intentional duplication of arithmetic, not of implementation** |
| `CALC-064` | **Manual override** | The user-supplied value | Override requires a reason (enforced); recorded as method `manual` with `override_reason` |
| `CALC-065` | **Scenario adjustment** | Applied to a base method result: `forecast = base × (1 + adjustment_pct)` per driver/account group, or a per-line override | Applied only to forecast rows, never to actuals or budget |

**Determinism:** all methods are deterministic and non-seasonal in v1. Seasonality indices and
driver-based regression are parked (`BL-018`).

### 9.2 Forecast-accuracy metrics (CALC-066 … CALC-069)

Computed for **closed** periods by comparing the locked forecast to the actual:

| ID | Metric | Formula | Note |
|---|---|---|---|
| `CALC-066` | Signed error | `actual − forecast` | Canonical direction: positive = actual exceeded forecast |
| `CALC-067` | Absolute error | `\|actual − forecast\|` | |
| `CALC-068` | Signed bias | `mean(signed error)` over the compared periods | Positive = systematic under-forecasting |
| `CALC-069` | MAPE-lite | `mean( \|actual − forecast\| / \|actual\| )` over the periods where `actual ≠ 0` | Periods with `actual = 0` are **excluded and counted** in the report (never treated as `0%` error, which would flatter the score) |

## 10. Control-total variance and reconciliation (CALC-070 … CALC-072)

| ID | Quantity | Formula |
|---|---|---|
| `CALC-070` | Control-total variance (per total supplied) | `variance = loaded_total − supplied_total` |
| `CALC-071` | Balance variance | `debit_total − credit_total` (per file, entity, period, and overall) |
| `CALC-072` | Row-count reconciliation | `source_rows − (loaded + quarantined + rejected)`; must equal `0` |

**Decision thresholds:** `CALC-071` and `CALC-072` use the configured tolerance, default **0.00** (exact).
`CALC-070` fails by default on any non-zero variance; acceptance is an explicit, recorded user decision
(`04` §12). A non-default tolerance is a project setting with a mandatory reason and appears in every
report that uses it.

## 11. Materiality and threshold defaults (CALC-080)

The default amount threshold for amount-based exception rules (owned and applied by `06`) is:

```
materiality_amount(line) = max( absolute_floor , materiality_pct × |budget(line)| )
```

| Parameter | Default | Where configured |
|---|---|---|
| `materiality_pct` | 2% of the line's budget | Settings → Thresholds (project-level, versioned) |
| `absolute_floor` | ₹ 500,000 | Settings → Thresholds (seeded; editable) |
| `pct_threshold` (for the AND test in "material variance") | 5% | Per-rule threshold in `06` |
| Per-rule override | Any rule may override either parameter | Per-rule config; the **effective** value is stored on each raised exception (`FactException.effective_threshold`) |

**`AND` semantics are mandatory** for the material-variance rule: a line is flagged only when
`|variance| ≥ materiality_amount(line)` **and** `|variance_pct| ≥ pct_threshold`. Fixture F13 proves both
directions of the AND with exact numbers.

**Percentage-point exception:** for ratio-based lines the amount test is replaced by a percentage-point
test (`|Δpp| ≥ pp_threshold`, default 1.0 pp), because an amount threshold is meaningless for a ratio.

## 12. Golden fixtures (exact numbers — lift directly into tests)

Every fixture below is **arithmetic-complete**: given the inputs, the expected outputs are exact. `14`
maps each fixture to `TST-nnn`; the sample dataset is generated to reproduce them.

### F1 — MTD variance, variance %, revenue (favourable)

| Input | Value |
|---|---|
| Account | `4000 Revenue` (revenue → higher-is-favourable) |
| Period | `FY26-P09` (Sep-26) |
| Actual MTD | `1,080,000.00` |
| Budget MTD | `1,000,000.00` |

| Expected output | Value |
|---|---|
| Variance | `+80,000.00` |
| Variance % (full precision) | `0.080000` (8.000000%) |
| Variance % (displayed, 1 dp) | `8.0%` |
| Favour*ability* | **Favourable** (revenue above budget) |

### F2 — MTD variance, expense under budget (the classic trap)

| Input | Value |
|---|---|
| Account | `5200 Repairs and maintenance` (expense → lower-is-favourable) |
| Actual MTD | `355,000.00` |
| Budget MTD | `380,000.00` |

| Expected output | Value |
|---|---|
| Variance | `−25,000.00` |
| Variance % (6 dp) | `−0.065789` (−6.578947%) |
| Variance % (displayed) | `−6.6%` |
| Favour*ability* | **Favourable** — a negative variance on an expense line is good |

*This is the single most commonly mis-implemented case in variance tooling; the fixture exists to make a
regression impossible.*

### F3 — MTD variance, expense over budget

| Input | Value |
|---|---|
| Actual MTD | `245,000.00` |
| Budget MTD | `200,000.00` |
| Expected variance | `+45,000.00` |
| Expected variance % | `+0.225000` → displayed `+22.5%` |
| Favour*ability* | **Unfavourable** |

### F4 — Zero budget, non-zero actual

| Input | Value |
|---|---|
| Actual | `15,000.00` |
| Budget | `0.00` |
| Expected variance | `+15,000.00` |
| Expected variance % | **`n/a`** (undefined; never `inf`, never `0`) |
| Favour*ability* (expense line) | Unfavourable |
| Side effect | The line is eligible for the *unbudgeted spend* rule (`06`) |

### F5 — Zero budget and zero actual (neutral)

| Input | Value |
|---|---|
| Actual | `0.00` |
| Budget | `0.00` |
| Expected variance | `0.00` |
| Expected variance % | **`—`** (nothing to compare — distinct from `n/a`) |
| Favour*ability* | Neutral (no colour, no label) |

### F6 — YTD aggregation and the sum-of-rounded rule

| Period | Actual | Budget | Variance (full precision) | Variance (displayed) |
|---|---|---|---|---|
| FY26-P07 | `1,080,000.00` | `1,000,000.00` | `+80,000.00` | `+80,000.00` |
| FY26-P08 | `1,020,500.55` | `1,000,000.00` | `+20,500.55` | `+20,500.55` |
| FY26-P09 | `995,300.45` | `1,000,000.00` | `−4,699.55` | `−4,699.55` |
| **YTD (P07–P09)** | **`3,095,801.00`** | **`3,000,000.00`** | **`+95,801.00`** | **`+95,801.00`** |

- YTD variance % (half-up, 6 dp per §6.1) = `95,801.00 / 3,000,000.00 = 0.0319336666…` → `0.031934` → displayed **`3.2%`**.
- **Sum check:** `80,000.00 + 20,500.55 − 4,699.55 = 95,801.00` = the YTD variance. (In this fixture the
  rounded components happen to tie; the general rule still applies and F6b asserts the discrepancy case.)
- **F6b (rounding discrepancy):** three component ratios of `33.334%`, `33.333%`, `33.333%` display as
  `33.3%` each (sum of displayed = `99.9%`), while the true sum `100.000%` displays as `100.0%`. The
  footnote *"Components may not sum to the total due to rounding."* must be present, and **no component
  may be adjusted** to force the sum.

### F7 — TTM / rolling 12

| Period | Net revenue |
|---|---|
| FY25-P10 | `900,000.00` |
| FY25-P11 | `920,000.00` |
| FY25-P12 | `1,010,000.00` |
| FY26-P01 | `880,000.00` |
| FY26-P02 | `890,000.00` |
| FY26-P03 | `940,000.00` |
| FY26-P04 | `960,000.00` |
| FY26-P05 | `975,000.00` |
| FY26-P06 | `985,000.00` |
| FY26-P07 | `1,080,000.00` |
| FY26-P08 | `1,020,500.55` |
| FY26-P09 | `995,300.45` |

| Expected output | Value |
|---|---|
| TTM total | `11,555,801.00` |
| TTM average per period (full precision) | `962,983.416666…` |
| TTM average (displayed) | `962,983.42` |

*With only 7 periods loaded, the same arithmetic applies over 7 and the label reads "TTM (7 of 12
periods)".*

### F8 — Prior-year comparison

| Input | Value |
|---|---|
| Current MTD actual (Sep-26) | `1,080,000.00` |
| PY MTD actual (Sep-25) | `950,000.00` |
| Current YTD actual (Apr-26 → Sep-26) | `3,095,801.00` |
| PY YTD actual (same 6 periods of FY25) | `2,880,000.00` |

| Expected output | Value |
|---|---|
| MTD vs PY — variance | `+130,000.00` |
| MTD vs PY — % (full precision) | `0.136842` → displayed **`13.7%`** |
| YTD vs PY — variance | `+215,801.00` |
| YTD vs PY — % (full precision) | `0.074931` → displayed **`7.5%`** |

### F9 — KPI computations and divide-by-zero

| KPI | Inputs | Expected |
|---|---|---|
| `KPI-001` Gross margin % | Revenue `1,080,000.00`; COGS `648,000.00` | GP `432,000.00`; `0.400000` → **`40.0%`** |
| `KPI-002` Opex ratio | Opex `355,000.00`; Revenue `1,080,000.00` | `0.328704` → **`32.9%`** |
| `KPI-003` Budget burn % | YTD actual `3,095,801.00`; Annual budget `12,000,000.00` | `0.257983` → **`25.8%`** |
| `KPI-004` Revenue growth % | Current `1,080,000.00`; PY `950,000.00` | `0.136842` → **`13.7%`** |
| `KPI-001` divide-by-zero | Revenue `0.00` | **`n/a`** |
| `KPI-001` both zero | Revenue `0.00`; COGS `0.00` | **`—`** |

### F10 — Percentage-point variance (correct)

| Input | Value |
|---|---|
| Budget gross margin % | `38.5%` |
| Actual gross margin % | `40.0%` |
| Expected variance | **`+1.5 pp`** |
| Incorrect (must not be produced) | `+3.9%` (relative change) |

### F11 — Percentage-point variance with negative/neutral base

| Input | Value |
|---|---|
| Budget margin % | `−4.0%` (loss-making line) |
| Actual margin % | `−1.0%` |
| Expected variance | **`+3.0 pp`** (improvement) |
| Favour*ability* | Favourable (margin improved toward/above zero) |
| Guard | A ratio variance is never divided by the comparator's absolute value to produce a "%" — the unit is always `pp` |

### F12 — Data-quality score

| Input | Value |
|---|---|
| Checks run | all 32 (`Σ weights = 238`, §8.3) |
| `IMP-014` (High, weight 10) | **fail** (`d = 1.0`) → deduction `10` |
| `IMP-021` (Low, weight 2) | **warn** (`d = 0.5`) → deduction `1` |
| All other checks | pass or skipped (skipped excluded from `R`; here all ran) |
| Row counts | source `184,502`; loaded `184,494`; quarantined `8`; rejected `0` |
| Balance | pass (`0.00` variance) |

| Expected output | Value |
|---|---|
| Deduction total | `11` |
| Raw score | `100 × (1 − 11/238) = 95.378151…` |
| **Displayed score (half-up, 0 dp)** | **`95`** |
| Guarantee check | `95 ≤ 96` — a failed High check makes a perfect score impossible |
| UI requirement | The score is displayed **with** the failed-check list (IMP-014: 8 rows; IMP-021: 12 flagged) |

### F13 — Materiality AND-test

Shared settings: `materiality_pct = 2%`, `absolute_floor = ₹500,000`, `pct_threshold = 5%`.

| Case | Budget | Actual | Threshold `max(500,000, 2% × budget)` | Amount test | % test | Raised? |
|---|---|---|---|---|---|---|
| F13a | `10,000,000.00` | `10,540,000.00` (var `+540,000.00`, `+5.4%`) | `max(500,000, 200,000) = 500,000` | `540,000 ≥ 500,000` ✓ | `5.4% ≥ 5%` ✓ | **Yes** (`EXC-018`, High) |
| F13b | `1,000,000.00` | `1,060,000.00` (var `+60,000.00`, `+6.0%`) | `max(500,000, 20,000) = 500,000` | `60,000 ≥ 500,000` ✗ | `6.0% ≥ 5%` ✓ | **No** — the AND test fails |
| F13c | `40,000,000.00` | `40,900,000.00` (var `+900,000.00`, `+2.25%`) | `max(500,000, 800,000) = 800,000` | `900,000 ≥ 800,000` ✓ | `2.25% ≥ 5%` ✗ | **No** — percentage test fails |

### F14 — Forecast arithmetic and accuracy

**F14a — Remaining-budget spread (`CALC-061`)**

| Input | Value |
|---|---|
| Annual budget (account 4000) | `12,000,000.00` |
| Actuals P01–P09 (loaded) | `9,300,000.00` |
| Remaining open periods | `P10, P11, P12` → `k = 3` |

| Expected | Value |
|---|---|
| Remaining | `12,000,000.00 − 9,300,000.00 = 2,700,000.00` |
| Per-period forecast | `2,700,000.00 / 3 = 900,000.00` each |

**F14b — Run-rate, last 3 actual months (`CALC-062`)**

| Input | Value |
|---|---|
| Last 3 actuals | `1,080,000.00`, `1,020,500.55`, `995,300.45` |
| Sum | `3,095,801.00` |
| Average (full precision) | `1,031,933.666666…` |
| Per-period forecast (stored) | `1,031,933.666666…` (6 dp) → displayed `1,031,933.67` |

**F14c — Scenario adjustment (`CALC-065`)**

| Input | Value |
|---|---|
| Base forecast | `1,031,933.67` (stored unrounded `1,031,933.666666…`) |
| Adjustment (Best scenario) | `+5%` |
| Expected | `1,031,933.666666… × 1.05 = 1,083,530.35` (displayed) |

**F14d — Forecast accuracy metrics (`CALC-066 … CALC-069`)**

| Period | Forecast | Actual | Signed error | Absolute error | MAPE-lite term |
|---|---|---|---|---|---|
| FY26-P07 | `1,050,000.00` | `1,080,000.00` | `+30,000.00` | `30,000.00` | `30,000/1,080,000 = 0.027778` |
| FY26-P08 | `1,032,500.55` | `1,020,500.55` | `−12,000.00` | `12,000.00` | `12,000/1,020,500.55 = 0.011759` |
| FY26-P09 | `989,300.45` | `995,300.45` | `+6,000.00` | `6,000.00` | `6,000/995,300.45 = 0.006028` |

| Expected metric | Value |
|---|---|
| Signed bias (`CALC-068`) | `(+30,000 − 12,000 + 6,000) / 3 = +8,000.00` |
| MAPE-lite (`CALC-069`) | `(0.027778 + 0.011759 + 0.006028) / 3 = 0.015188` → displayed **`1.5%`** |
| Exclusion rule | Any period with `actual = 0` is excluded **and counted** in the report |

## 13. Tolerance policy (binding — Addon 4 §G.1)

| Context | Rule |
|---|---|
| Internal money arithmetic | **Exact equality at minor-unit precision.** No epsilon, no `isclose`, no tolerance parameter anywhere in a money comparison |
| Display | Half-up rounding per §6.1; tests assert on the **display-rounded** values using the same mode |
| Cross-artifact (UI vs Excel vs PPT vs CLI) | **Exact equality** of engine values at display precision — the cross-artifact consistency test (`14`) parses the artefacts and asserts equality |
| Import balance / row counts | Tolerance default `0.00`; any non-zero tolerance requires a recorded reason and appears in the report |
| Ratio comparisons | Compared at stored 6 dp; displayed at 1 dp |
| Prohibited phrase | "Close enough" does not exist in money paths; a mismatch is either a bug or a documented, user-accepted decision recorded on the batch |

## 14. Formula register (index)

| ID | Formula | Section | Fixture |
|---|---|---|---|
| `CALC-001`…`CALC-006` | Fiscal calendar, period assignment, MTD/YTD/PY/TTM windows | §2 | F1, F6, F7, F8 |
| `CALC-007` | Canonical sign conventions (`net = debit − credit`, `variance = actual − budget`) | §3 | F1–F6 |
| `CALC-010` | Variance | §4.1 | F1–F6 |
| `CALC-011` | Variance % with zero-budget states | §4.2 | F1, F2, F3, F4, F5 |
| `CALC-012` | Favour*ability* by line type | §4.3 | F2, F3, F5 |
| `CALC-013` | Percentage points vs percent | §4.4 | F10, F11 |
| `CALC-020`…`CALC-027`, `KPI-001`…`KPI-006` | Ratio/KPI library and divide-by-zero guards | §5 | F9 |
| `CALC-030` | Rounding mode and precision | §6.1 | All fixtures |
| `CALC-031` | Sum-of-rounded rule and footnote | §6.2 | F6, F6b |
| `CALC-032` | Display scale (whole / thousands / lakhs) | §6.3 | F-page assertion |
| `CALC-033` | Negative presentation | §6.4 | F3, F6 |
| `CALC-040`…`CALC-042` | Grain, grouped sums, hierarchy rollups | §7 | Rollup invariant |
| `CALC-050` | Data-quality score | §8 | F12 |
| `CALC-060`…`CALC-065` | Forecast methods | §9.1 | F14a, F14b, F14c, F14e, F14f, F14g |
| `CALC-066`…`CALC-069` | Forecast accuracy metrics | §9.2 | F14d |
| `CALC-070`…`CALC-072` | Control-total, balance and row-count variances | §10 | F13-style reconciliation |
| `CALC-080` | Materiality and threshold defaults | §11 | F13 |

## 15. Test mapping and change control

- Every fixture in §12 becomes a golden test with **exact expected values**; the sample dataset is
  generated so the fixtures reproduce through the real import → engine → export path, not just in unit
  tests (`14`, Addon 3 §F.4).
- Any formula change requires: this document updated → `CHANGELOG` entry → fixtures updated → tests
  updated → cross-artifact consistency re-run. Never the reverse order (P2).
- A new KPI or method requires a register row here, a fixture, and — for methods — the behaviour
  definition in `07`.
- Rounding, tolerance and materiality defaults may only change with a documented reason in-doc and a
  recorded decision (`18` §Decided).
