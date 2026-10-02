# MATHEMATICAL & EXAMPLE RECOMPUTATION AUDIT (A3 — WAVE 5: 74 CHECKS, 1 MISMATCH)

_Every arithmetic calculation, rounding operation, and worked example in the Phase 0 specification recomputed independently using exact Decimal arithmetic (zero binary float drift). Wave 5 re-run: `audit/recompute_wave5.py` → `audit/recompute_wave5.log` (74 checks, **1 MISMATCH** — see F6 below and `F-021`)._

---

## 1. Summary of Results

| Target Area | Fixtures / Items Evaluated | Independent Matches | Mismatches | Status |
|---|---|---|---|---|
| **Doc 05 Golden Fixtures (F1–F14)** | 14 primary fixture blocks (Wave 5: 74 scripted checks, `audit/recompute_wave5.py`) | 73 | **1** | **MISMATCH — F6 6dp variance %** (`05:419` states `0.031933`; half-up 6dp of `0.031933666…` = `0.031934`, violating `05:182`) |
| **Doc 05 KPI Library & Edge Cases** | 6 KPIs + divide-by-zero guards | 6 | 0 | **100% MATCH** |
| **Doc 05 Data Quality Score** | Raw score, deduction logic, rounding | 3 | 0 | **100% MATCH** |
| **Doc 05 Forecast Accuracy & Spreads** | Run-rate, remaining spread, scenario, bias, MAPE | 7 | 0 | **100% MATCH** |
| **Doc 10 AI Prompt Worked Examples** | 4 prompts (token budgets, JSON lengths, schemas) | 4 | 0 | **100% MATCH** |
| **Doc 06 Exception Rule Thresholds** | 24 rules (amounts, percentages, multipliers) | 24 | 0 | **100% MATCH** |

**Verdict (Wave 5):** **74 checks, 1 MISMATCH.** The single mismatch is F6's 6dp YTD variance % (`05:419` `0.031933` vs computed `0.031934`) — see `F-021`; it violates the doc's own half-up rule (`05:182`) and, per `30:113` ("Mismatch = BLOCKER"), is a BLOCKER. All other money values (variances, TTM/YTD totals, KPI, DQ score, thresholds, forecast math, bias/MAPE) match exactly and remain valid as golden test anchors **once F6 and F-020 (F13a rule ID) are corrected**.

---

## 2. Doc 05 Golden Fixtures Verification (F1 to F14)

### F1 — MTD Variance, Variance %, Revenue (Favourable)
- **Inputs:** Account `4000 Revenue` (revenue line → higher is favourable); Period `FY26-P09`; Actual MTD = `1,080,000.00`; Budget MTD = `1,000,000.00`
- **Formulas:**
  - `Variance = Actual − Budget`
  - `Variance % = Variance / Budget`
- **Recomputation:**
  - Variance = `1,080,000.00 − 1,000,000.00 = +80,000.00`
  - Variance % = `80,000.00 / 1,000,000.00 = +0.080000` (+8.000000%) → Displayed (1 dp): **`+8.0%`**
  - Favorability: Actual > Budget on revenue line → **`Favourable`**
- **Doc Stated Output:** Variance = `+80,000.00`, % = `0.080000` → `8.0%`, Favorability = `Favourable`
- **Verdict:** **MATCH**

---

### F2 — MTD Variance, Expense Under Budget (The Classic Trap)
- **Inputs:** Account `5200 Repairs and maintenance` (expense line → lower is favourable); Period `FY26-P09`; Actual MTD = `355,000.00`; Budget MTD = `380,000.00`
- **Formulas:**
  - `Variance = Actual − Budget`
  - `Variance % = Variance / Budget`
- **Recomputation:**
  - Variance = `355,000.00 − 380,000.00 = −25,000.00`
  - Variance % = `−25,000.00 / 380,000.00 = −0.06578947...` → Displayed (1 dp): **`−6.6%`**
  - Favorability: Actual < Budget on expense line → **`Favourable`**
- **Doc Stated Output:** Variance = `−25,000.00`, % = `−0.065789` → `−6.6%`, Favorability = `Favourable`
- **Verdict:** **MATCH**

---

### F3 — MTD Variance, Expense Over Budget
- **Inputs:** Expense line; Actual MTD = `245,000.00`; Budget MTD = `200,000.00`
- **Recomputation:**
  - Variance = `245,000.00 − 200,000.00 = +45,000.00`
  - Variance % = `45,000.00 / 200,000.00 = +0.225000` → Displayed: **`+22.5%`**
  - Favorability: Actual > Budget on expense line → **`Unfavourable`**
- **Doc Stated Output:** Variance = `+45,000.00`, % = `+0.225000` → `+22.5%`, Favorability = `Unfavourable`
- **Verdict:** **MATCH**

---

### F4 — Zero Budget, Non-Zero Actual
- **Inputs:** Expense line; Actual = `15,000.00`; Budget = `0.00`
- **Recomputation:**
  - Variance = `15,000.00 − 0.00 = +15,000.00`
  - Variance % = Division by zero → **`n/a`** (undefined; never `inf` or `0`)
  - Favorability: Actual > Budget on expense line → **`Unfavourable`**
- **Doc Stated Output:** Variance = `+15,000.00`, % = `n/a`, Favorability = `Unfavourable`
- **Verdict:** **MATCH**

---

### F5 — Zero Budget and Zero Actual (Neutral)
- **Inputs:** Actual = `0.00`; Budget = `0.00`
- **Recomputation:**
  - Variance = `0.00`
  - Variance % = Nothing to compare → **`—`** (em-dash; distinct from `n/a`)
  - Favorability: Neutral (no colour, no indicator)
- **Doc Stated Output:** Variance = `0.00`, % = `—`, Favorability = `Neutral`
- **Verdict:** **MATCH**

---

### F6 — YTD Aggregation and the Sum-of-Rounded Rule
- **Inputs:**
  - FY26-P07 Actual: `1,080,000.00`, Budget: `1,000,000.00`, Var: `+80,000.00`
  - FY26-P08 Actual: `1,020,500.55`, Budget: `1,000,000.00`, Var: `+20,500.55`
  - FY26-P09 Actual: `995,300.45`, Budget: `1,000,000.00`, Var: `−4,699.55`
  - YTD Budget: `3,000,000.00`
- **Recomputation:**
  - YTD Actual = `1,080,000.00 + 1,020,500.55 + 995,300.45 = 3,095,801.00`
  - YTD Variance = `3,095,801.00 − 3,000,000.00 = +95,801.00`
  - Sum check: `80,000.00 + 20,500.55 − 4,699.55 = +95,801.00` (exact match)
  - YTD Variance % = `95,801.00 / 3,000,000.00 = 0.031933666...` → Displayed (1 dp): **`3.2%`**
  - **F6b Sum-of-Rounded Footnote:** Component ratios `33.334%`, `33.333%`, `33.333%` each display as `33.3%` (sum = `99.9%`), while true sum `100.0%` displays as `100.0%`. Stated rule: Footnote mandatory, zero artificial forced adjustments.
- **Doc Stated Output:** YTD Actual = `3,095,801.00`, YTD Var = `+95,801.00`, YTD % = `3.2%`; intermediate at `05:419`: "YTD variance % (full precision) = `95,801.00 / 3,000,000.00 = 0.031933` → displayed **`3.2%`**"
- **Verdict (Wave 5):** **MISMATCH (1 of 74)** — `0.031933666…` rounded half-up at 6 dp = **`0.031934`**, not `0.031933` (which is truncation, prohibited by the doc's own `05:182` "Rounding mode: **Half-up**"). Displayed `3.2%` and all totals unaffected; the stated intermediate violates the rounding rule → `F-021` (BLOCKER per `30:113`).

---

### F7 — TTM / Rolling 12 Total & Average
- **Inputs (12 monthly net revenue figures):**
  `900,000.00`, `920,000.00`, `1,010,000.00`, `880,000.00`, `890,000.00`, `940,000.00`, `960,000.00`, `975,000.00`, `985,000.00`, `1,080,000.00`, `1,020,500.55`, `995,300.45`
- **Recomputation:**
  - TTM Total = `sum(12 periods) = 11,555,801.00`
  - TTM Average (exact) = `11,555,801.00 / 12 = 962,983.416666...`
  - TTM Average (half-up, 2 dp) = **`962,983.42`**
- **Doc Stated Output:** TTM total = `11,555,801.00`, average = `962,983.42`
- **Verdict:** **MATCH**

---

### F8 — Prior-Year Comparison
- **Inputs:**
  - Current MTD (Sep-26): `1,080,000.00`; PY MTD (Sep-25): `950,000.00`
  - Current YTD (6 mos): `3,095,801.00`; PY YTD (6 mos): `2,880,000.00`
- **Recomputation:**
  - MTD vs PY Var = `1,080,000.00 − 950,000.00 = +130,000.00`
  - MTD vs PY % = `130,000.00 / 950,000.00 = 0.1368421...` → Displayed (1 dp): **`13.7%`**
  - YTD vs PY Var = `3,095,801.00 − 2,880,000.00 = +215,801.00`
  - YTD vs PY % = `215,801.00 / 2,880,000.00 = 0.0749309...` → Displayed (1 dp): **`7.5%`**
- **Doc Stated Output:** MTD Var = `+130,000.00`, MTD % = `13.7%`; YTD Var = `+215,801.00`, YTD % = `7.5%`
- **Verdict:** **MATCH**

---

### F9 — KPI Computations & Divide-by-Zero
- **Inputs & Recomputations:**
  - `KPI-001` Gross margin %: Rev `1,080,000.00`, COGS `648,000.00` → GP = `432,000.00`. Margin % = `432,000.00 / 1,080,000.00 = 0.400000` → **`40.0%`**
  - `KPI-002` Opex ratio: Opex `355,000.00`, Rev `1,080,000.00` → `355,000.00 / 1,080,000.00 = 0.3287037...` → **`32.9%`**
  - `KPI-003` Budget burn %: YTD Actual `3,095,801.00`, Annual Budget `12,000,000.00` → `3,095,801.00 / 12,000,000.00 = 0.2579834...` → **`25.8%`**
  - `KPI-004` Revenue growth %: Cur `1,080,000.00`, PY `950,000.00` → `130,000.00 / 950,000.00 = 0.136842...` → **`13.7%`**
  - Divide-by-zero guard: Rev `0.00` → **`n/a`**
  - Both zero guard: Rev `0.00`, COGS `0.00` → **`—`**
- **Doc Stated Output:** All results identical to recomputed values.
- **Verdict:** **MATCH**

---

### F10 & F11 — Percentage-Point (pp) Variance
- **F10 Inputs:** Budget Gross Margin = `38.5%`, Actual Gross Margin = `40.0%`
  - Recomputation: `40.0 − 38.5 = +1.5 pp` (never relative change `+3.9%`)
  - Doc Stated: `+1.5 pp` → **MATCH**
- **F11 Inputs:** Budget Margin = `−4.0%`, Actual Margin = `−1.0%`
  - Recomputation: `−1.0 − (−4.0) = +3.0 pp` (favourable improvement)
  - Doc Stated: `+3.0 pp`, Favourable → **MATCH**

---

### F12 — Data-Quality Score (`CALC-050`)
- **Inputs:**
  - Total checks run: 32 (`Σ weights = 238`)
  - `IMP-014` (High, weight 10): failed (`d = 1.0`) → deduction = `10`
  - `IMP-021` (Low, weight 2): warn (`d = 0.5`) → deduction = `1`
  - Total deduction = `11`
- **Formula:** `Score = 100 × (1 − Total Deduction / Sum Weights)`
- **Recomputation:**
  - Raw Score = `100 × (1 − 11 / 238) = 100 × (227 / 238) = 95.37815126...`
  - Displayed Score (half-up, 0 dp) = **`95`**
  - Guarantee Check: High severity failure caps max score at `96`; `95 ≤ 96` satisfies guard.
- **Doc Stated Output:** Raw = `95.378151...`, Displayed = `95`
- **Verdict:** **MATCH**

---

### F13 — Materiality AND-Test (`CALC-080`)
- **Parameters:** `materiality_pct = 2%`, `absolute_floor = ₹500,000`, `pct_threshold = 5%`
- **Dynamic Threshold Formula:** `max(500,000, 2% × budget)`
- **Cases:**
  - **F13a:** Budget `10,000,000.00`, Actual `10,540,000.00` (Var `+540,000.00`, `+5.4%`)
    - Threshold = `max(500,000, 200,000) = 500,000`
    - Amount test: `540,000 ≥ 500,000` (Pass)
    - Pct test: `5.4% ≥ 5%` (Pass)
    - Verdict: **Raised (`EXC-010`, High)** → money math **MATCH**; rule ID **MISMATCH** — owner doc `06:738`/`06:222` maps canonical case F13a (P18) to `EXC-018` (Material variance), while `05:524` states `EXC-010` (Potential cut-off issue, `06:214`). See `F-020` (BLOCKER).
  - **F13b:** Budget `1,000,000.00`, Actual `1,060,000.00` (Var `+60,000.00`, `+6.0%`)
    - Threshold = `max(500,000, 20,000) = 500,000`
    - Amount test: `60,000 < 500,000` (Fails)
    - Verdict: **Not Raised** (AND test fails) → **MATCH**
  - **F13c:** Budget `40,000,000.00`, Actual `40,900,000.00` (Var `+900,000.00`, `+2.25%`)
    - Threshold = `max(500,000, 800,000) = 800,000`
    - Amount test: `900,000 ≥ 800,000` (Pass)
    - Pct test: `2.25% < 5%` (Fails)
    - Verdict: **Not Raised** (% test fails) → **MATCH**

---

### F14 — Forecast Arithmetic & Accuracy Metrics
- **F14a Remaining-Budget Spread:**
  - Annual Budget `12,000,000.00`; Actuals P01–P09 `9,300,000.00`; Remaining periods `k = 3`
  - Remaining Budget = `12,000,000.00 − 9,300,000.00 = 2,700,000.00`
  - Per-period forecast = `2,700,000.00 / 3 = 900,000.00` each → **MATCH**
- **F14b Run-Rate (Last 3 Actuals):**
  - Actuals: `1,080,000.00`, `1,020,500.55`, `995,300.45` (Sum = `3,095,801.00`)
  - Average = `3,095,801.00 / 3 = 1,031,933.666666...` → Stored unrounded; Displayed: **`1,031,933.67`** → **MATCH**
- **F14c Scenario Adjustment:**
  - Base: `1,031,933.666666...`; Adjustment: `+5%` (`1.05`)
  - Value = `1,031,933.666666... × 1.05 = 1,083,530.35` (displayed) → **MATCH**
- **F14d Accuracy Metrics:**
  - Periods:
    - P07: Forecast `1,050,000.00`, Actual `1,080,000.00` → Signed err: `+30,000.00`, Abs: `30,000.00`, MAPE: `30,000 / 1,080,000 = 0.0277777...`
    - P08: Forecast `1,032,500.55`, Actual `1,020,500.55` → Signed err: `−12,000.00`, Abs: `12,000.00`, MAPE: `12,000 / 1,020,500.55 = 0.0117589...`
    - P09: Forecast `989,300.45`, Actual `995,300.45` → Signed err: `+6,000.00`, Abs: `6,000.00`, MAPE: `6,000 / 995,300.45 = 0.0060283...`
  - Signed Bias = `(+30,000 − 12,000 + 6,000) / 3 = 24,000 / 3 = +8,000.00` → **MATCH**
  - MAPE-lite = `(0.0277777... + 0.0117589... + 0.0060283...) / 3 = 0.0455650... / 3 = 0.0151883...` → Displayed: **`1.5%`** → **MATCH**

---

## 3. Doc 10 AI Prompt Worked Examples Verification

- **PROMPT-01 (Variance Commentary):**
  - Worked example output length = 436 characters (schema constraint: 40 to 600 chars) → **COMPLIANT**
  - Drivers count = 3 items (schema constraint: max 3 items) → **COMPLIANT**
  - All numeric tokens (`₹4,50,000`, `₹1,80,000`, `5.4%`, `4`) match values in `data_block_json` payload → **COMPLIANT**
  - JSON validity: 100% valid JSON matching JSON Schema Draft 2020-12 → **COMPLIANT**
- **PROMPT-02 (Mapping Suggestion):**
  - Worked example confidence = `high` (schema enum: high, medium, low) → **COMPLIANT**
  - JSON Schema Draft 2020-12 valid → **COMPLIANT**
- **PROMPT-03 (Exception Grouping Summary):**
  - Worked example JSON valid; character count and group references compliant → **COMPLIANT**
- **PROMPT-04 (Follow-up Message Draft):**
  - Plain English tone, no accusatory language, valid JSON envelope → **COMPLIANT**
