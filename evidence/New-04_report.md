# New-04 — Money-type audit: float arithmetic on money

**Task:** `01a10128-f558-74b0-a758-1d00204a6520`
**Scope:** `app/engine/`, `app/api/` (read-only; nothing outside this report was modified)
**Agent:** New-04 (slot `01a10123-3cc2-75e0-a8e0-2f6851e520fc`)
**Date:** 2026-10-03
**Status:** COMPLETE with explicit gaps (see §6). Live project DB was not touched — all
dynamic checks used an in-memory DuckDB (`duckdb.connect(":memory:")`).

---

## 1. Owning spec — quoted verbatim BEFORE acting

### 1.1 `docs/01_PRD.md` §11.3 "What the product must never do" (lines 336–344)

```
336	### 11.3 What the product must never do
337	
338	1. Never write to, post to, or modify an ERP or any external system.
339	2. Never upload client data anywhere (no telemetry, no crash upload, no silent AI call).
340	3. Never silently discard a row, sheet, column, or file.
341	4. Never present an AI-produced number as a computed value.
342	5. Never show a figure the user cannot drill to source.
343	6. Never compute money with binary floats.
344	7. Never overwrite history behind an issued pack.
```

### 1.2 `docs/09_TECHNICAL_ARCHITECTURE.md` ADR stack table (line 94)

```
| Backend / engine | **Python 3.12**, FastAPI (local API on `127.0.0.1:<random port>` with a session
token), **DuckDB** for analytics storage, Polars and/or Pandas for transformations, `openpyxl` for
Excel read/write, `python-pptx` for PowerPoint, `httpx` for optional AI calls, `pytest` for tests.
**Decimal-safe money handling** (Python `Decimal` or integer minor units) — binary floats are
forbidden for currency maths |
```

### 1.3 `docs/17_CODING_STANDARDS.md` §5.1 "Money and numbers" (lines 224–235) — the operative standard

```
224	### 5.1 Money and numbers
225	
226	| Rule | Detail |
227	|---|---|
228	| Type | `Decimal` everywhere in money paths; `float` is banned (lint rule + review) |
229	| Construction | `Decimal("1234.56")` from strings/ints; **never** `Decimal(some_float)` |
230	| Precision | Money quantised to 2 decimals at the boundary defined in `05` §6; intermediate calculations keep full precision |
231	| Rounding | One rounding policy (`05` §6.1) and one sum-of-rounded rule (`05` §6.2) — no second implementation |
232	| Comparison | Exact equality on `Decimal`; **no epsilon/tolerance comparisons in the engine** (`05` §13) |
233	| Division | Divide-by-zero returns the documented `n/a` (÷0) or `—` (0/0) sentinel (`05` §4), never `inf`/`NaN` |
234	| Percentages | Percentage-point vs percent (`CALC-013`) is decided in `05`, never re-decided at a call site |
235	| Scale display | Lakh/crore grouping is a display concern (`08` §15, `11` §3.6) — the stored value is unaffected |
```

### 1.4 The one sanctioned boundary — `docs/11_EXCEL_OUTPUT_SPEC.md` §3.6 rule 4 (lines 269–271)

```
269	4. **Money is written as a number at exactly 2 decimal places** (the engine's stored precision — no
270	   loss), as `float(Decimal)`. Values are quantised before conversion; the cross-artifact test compares
271	   at 2 dp.
```

**Assumption stated (spec is silent beyond this):** I read 1.4 as permitting exactly one float
conversion — `Decimal → float` — at the `openpyxl` cell-write call, *after* the value has already been
quantised to 2 dp. It does **not** license (a) `float()` coercions upstream of the storage layer, or
(b) money being *modelled* as `float` in an intermediate dataclass. I flag this explicitly because
several findings below sit near that line and the distinction decides whether they are violations or
by design.

---

## 2. Check results at a glance

| # | Check class | Verdict |
|---|---|---|
| C1 | `float(...)` applied to a monetary value | **FAIL — 5 genuine hits** (§3) |
| C2 | `Decimal` divided by a `float`; bare `/` on money | **PASS — 0 genuine hits** (§4.2) |
| C3 | DuckDB DDL declaring amount/balance/variance as FLOAT/DOUBLE | **PASS — 0 hits** (§4.3) |
| C4 | SQL `SUM`/`AVG` over money columns | **PASS** — all over `DECIMAL(18,2)` (§4.4) |
| C5 | JSON serialisation of Decimal amounts via `float()` | **PASS** (§4.5) |
| C6 | `round()` on money instead of `quantize()` | **PASS — 0 hits** (§4.6) |

---

## 3. Findings — genuine money-path violations, ranked by severity

### 3.1 S1 / CRITICAL — `float()` on transaction money at the primary ingestion boundary

**File:** `app/engine/store/import_repo.py`, lines 209–211 (and 149)

**Exact expression (read of `import_repo.py` lines 196–245):**

```python
209	                    float(tx.debit),
210	                    float(tx.credit),
211	                    float(tx.net_amount),
```

```python
149	            float(b.amount),
```

**Target columns** — `app/engine/store/schema_duckdb.sql` (grep `CREATE TABLE IF NOT EXISTS Fact`,
lines 109–111, 132, 165):

```
109	CREATE TABLE IF NOT EXISTS FactActual (
110	    debit      DECIMAL(18,2) NOT NULL,
111	    credit     DECIMAL(18,2) NOT NULL,
132	    amount     DECIMAL(18,2) NOT NULL,
165	    amount     DECIMAL(18,2) NOT NULL,
```

**Classification: GENUINE MONEY PATH.** `tx.debit` / `tx.credit` / `tx.net_amount` / `b.amount` are
the ingested GL and budget money values. Each is coerced `Decimal → float64` and then handed to a
`DECIMAL(18,2)` column. This is precisely what §1.2 ("binary floats are forbidden for currency maths")
and §1.3 rule 228 (`float` is banned) prohibit, and it is on the main data-ingestion path for both
actuals and budget.

**Empirical proof of cent loss** (in-memory DuckDB, direct-vs-float comparison):

```
$ python -c "@' ... '@ | python -"
=== A) Decimal -> float -> DECIMAL(18,2) ===
  in=100.05               float=100.05                     duckdb=100.05                 lossless=True
  in=0.145                float=0.145                      duckdb=0.14                  lossless=False
  in=2.675                float=2.675                      duckdb=2.68                  lossless=False
  in=99999999999999.99    float=99999999999999.98           duckdb=99999999999999.98     lossless=False
  in=1234567890123456.78  float=1234567890123456.8          duckdb=1234567890123456.80   lossless=False
  in=123456789012345.67   float=123456789012345.67          duckdb=123456789012345.68    lossless=False
```

Two entries above are *not* float artifacts and are excluded from the claim, to avoid a false alarm:
`0.145 → 0.14` and `2.675 → 2.68` are correct half-up rounding into a 2 dp target. The three
genuine float64 losses are `99999999999999.99 → ...98` (**one cent lost**),
`123456789012345.67 → ...68` (**one cent gained**) and `1234567890123456.78 → ...80`. All sit inside
the `DECIMAL(18,2)` domain.

**Honest caveat:** these point examples all use ≥ 10^13 magnitude. I did **not** measure the loss
*frequency* across the normal FP&A range — see §6 GAP-1. At small magnitudes float64 happened to
round-trip in every case I tested, so this is a correctness risk that scales with magnitude, not a
guaranteed break on ordinary values.

---

### 3.2 S2 / HIGH — `float()` on forecast money (computed and manual)

**File:** `app/engine/store/forecast_repo.py`, lines 304 and 416

**Exact expressions** (read of `forecast_repo.py` lines 290–330 and 400–430):

```python
304	            float(final_amt),
```

```python
416	                    float(amount),
```

`final_amt` (line 304) is the computed forecast amount; `amount` (line 416) is the **human-typed
manual override** arriving from `POST /forecasts/{id}/override`, where
`app/api/main.py:1231` does `Decimal(payload.amount)` from a Pydantic field declared
`amount: str` (`app/api/main.py:49`). So the API boundary is correct — the money is a properly
constructed `Decimal` — and the loss is introduced one layer down by the explicit `float()`.

**Classification: GENUINE MONEY PATH.** Both write to `FactForecast.amount DECIMAL(18,2)`
(`schema_duckdb.sql:165`). Same rule breach as 3.1, but ranked lower because forecast amounts are
downstream of import rather than the ledger of record. Line 416 is the more user-visible of the two:
a controller types a number into the UI and a cent can move on the way to storage.

---

### 3.3 S2 / HIGH — money *modelled* as `float` in the Excel pack model layer

**File:** `app/engine/exports/excel_pack.py`, dataclasses at lines 150–178 and 261–268;
float money literals at lines 330–381.

**Exact expressions** (read of `excel_pack.py` lines 146–190, 255–275, 300–340) — the money fields are
annotated `float`:

```python
150	class BvARow:
...
			actual: float
			budget: float
			var_pct: float | None
			var_pct_mtd: float | None
			var_pct_ytd: float | None
```

```python
261	(actual: float | None, budget: float, var_pct: float | None, adjustment_pct: float | None)
```

And the data feeding them is written as **Python float money literals**, e.g. `12500000.00`
(read of lines 300–340).

**Classification: GENUINE MONEY PATH.** This is the structural version of the same breach: money is
not merely *converted* at the sanctioned `openpyxl` boundary (§1.4) — it is *represented* as binary
float across the whole export model, one layer inside the writer. Every `actual`, `budget`,
`transaction` and `variance` value in the pack is a float64 before it is ever quantised.

**Caveat, stated rather than glossed:** Python dataclasses do not enforce annotations, so I cannot
assert from the annotation alone that a `Decimal` is not also being assigned into these fields. What
I *can* assert with evidence is that the declared model type is `float` and that the literal dataset
at lines 330–381 is float money. Confirming which call sites instantiate `BvARow`/`PLRow` was in
progress and is GAP-2 in §6.

---

### 3.4 S3 / MEDIUM — float arithmetic on AI vendor cost

**File:** `app/engine/ai/usage.py`, lines 65–66 (and rounding at 67, 146, 171)

**Exact expressions:**

```python
65	cost_in  = (tokens_in  / 1_000_000.0) * 5.00
66	cost_out = (tokens_out / 1_000_000.0) * 20.00
```

`cost_in` / `cost_out` are pure `float` — there is no `Decimal` anywhere in the expression. The
figures are USD/INR per-token rates multiplied by token counts, i.e. **money**, and the result feeds
a spend cap enforced by `app/engine/ai/guardrails.py:853,857`
(`float(monthly_cost)`).

**Classification: GENUINE MONEY PATH, lower blast radius.** This is the vendor's own bill, not the
client's ledger, and it is an order-of-magnitude estimate rather than a reportable figure. But it is
a real spend number, it is compared against a configured cap, and §1.2's wording ("binary floats are
forbidden for currency maths") has no carve-out for it. Ranked below the client-ledger paths.

---

### 3.5 S4 / LOW — money not quantised to 2 dp (reported because it is near-miss, **not** a float bug)

**File:** `app/engine/store/analytics_repo.py`, line 542

**Exact expression** (read of `analytics_repo.py` lines 525–565):

```sql
542	COALESCE(SUM(fa.net_amount), 0) * 1.02 as forecast_amount
```

I want to be precise here because the literal `1.02` *looks* like the float-literal trap. It is not.
DuckDB resolves it in **decimal**, not binary, arithmetic:

```
$ python -c "..."
=== B) SUM(DECIMAL) * float literal 1.02 ===
  in=100.05               duckdb=102.0510               exact_decimal=102.05                match=False  dbl=102.051
  in=3333.33              duckdb=3399.9966              exact_decimal=3400.00               match=False  dbl=3399.9966
  in=1234567.89           duckdb=1259259.2478           exact_decimal=1259259.25            match=False  dbl=1259259.2478
  in=99999999999999.99    duckdb=101999999999999.9898   exact_decimal=101999999999999.99    match=False  dbl=101999999999999.98

=== C) type of SUM(amt)*1.02 ===
  ('DECIMAL(38,4)', 'DECIMAL(38,2)')
```

**Classification: NOT a binary-float violation.** The result type is `DECIMAL(38,4)`, not `DOUBLE` —
DuckDB widens the literal into decimal. The real defect is different and smaller: the money leaves
this query at **4 dp** (`102.0510`, `3399.9966`) rather than the 2 dp that §1.3 rule 230 requires at
the boundary, and the surrounding code then recovers it with `Decimal(str(...))`
(`analytics_repo.py:552–554`) — a correct *construction* pattern that preserves the unquantised
scale. So: **scale discipline bug, not a float64 bug.** Reporting it so it is not mis-filed.

---

## 4. Passing checks (with the commands that show they pass)

### 4.1 `float(` inventory — complete list, so the benign ones are auditable

Command: grep for `\bfloat\s*\(` across `app/**/*.py`.

Genuine money-path hits: `import_repo.py:149,209,210,211`; `forecast_repo.py:304,416`;
`excel_pack.py` (money fields typed `float` at 150–178/261–268 and float literals at 330–381);
`usage.py:65,66` (via arithmetic, not `float()` call).

Benign / non-monetary — **separated out per the task instruction**:

| file:line | expression | why benign |
|---|---|---|
| `app/engine/imports/hardening.py:494` | `float(clean_s)` | **type probe** — tests whether a source string parses as a number; the result is discarded, never stored or summed |
| `app/engine/calc/math.py:212` | `pct = (variance / abs(budget)) * ONE_HUNDRED` | `Decimal / Decimal` → a ratio; monetary operands, decimal operands. Benign |
| `app/engine/forecast/methods.py:212` | `remaining / Decimal(k)` | `Decimal / Decimal`. Benign |
| `app/engine/forecast/methods.py:465` | `quantize_money(total / Decimal(len(...)))` | `Decimal / Decimal`, then `quantize_money`. Benign — and it is the *correct* pattern |
| `app/engine/forecast/methods.py:486` | `abs(act - fct) / abs(act)` | `Decimal / Decimal` ratio. Benign |
| `app/engine/forecast/scenarios.py:596` | `quantize_money(total_error / count)` | `Decimal` count, then `quantize_money`. Benign |
| `app/engine/rules/rules_17_24.py:375` | `multiple = int(total_amt / round_unit)` | `round_unit = Decimal(str(...))` at line 359 → `Decimal / Decimal`, then `int()` truncation. Benign |
| `app/engine/rules/rules_09_16.py:558` | `mean = total / Decimal(pattern_periods)` | `Decimal / Decimal`. Benign |
| `app/engine/exports/excel_pack.py:671` | `var_pct = (var_total / abs(bud_total)) if bud_total else 0.0` | `Decimal / Decimal` variance ratio. Benign (the `0.0` fallback is a zero-ratio sentinel, not money) |
| `app/engine/exports/excel_pack.py:807, 935, 939, 1349, 1352` | `r_data.var_pct / 100.0` | `var_pct` is a **percentage ratio**, not money — but it is `float`-typed, so this is a downstream symptom of 3.3, not an independent violation |
| `app/engine/imports/hardening.py:171–172` | `avg = sum(counts) / len(counts)` | integer counts. Benign |
| `app/engine/imports/profiles.py:244` | Jaccard similarity | similarity score. Benign |
| `app/engine/ai/guardrails.py:853, 857` | `float(monthly_cost)` | spend-cap **config** value; related to 3.4 but a limit, not a computed figure |
| `app/engine/calc/quality_score.py` (`total_deductions`, `deduction_amount`) | Decimal additions | these are **score points**, not currency — `raw_score` is out of 100 |
| `app/engine/cli/main.py:38` | `round(elapsed, 1)` | elapsed seconds. Benign |

**Critical note on C2:** there are **no** occurrences of `Decimal / float` anywhere in
`app/engine/` or `app/api/`. Every `/` I classified above has a `Decimal` on both sides. A Decimal
divided by a float would raise `TypeError` in Python, so the absence is also structurally confirmed by
the fact that these code paths run green in the test suite.

### 4.2 Division check — PASS

Command: `Get-ChildItem app\engine, app\api -Recurse -Filter *.py | Select-String -Pattern '/'`
then per-hit context reads. Result: every division on a money operand is `Decimal / Decimal`.
**0 genuine violations.** The only `Decimal/float` shapes in the codebase are `var_pct / 100.0`
(ratios, §4.1) and the token-cost expressions (§3.4).

### 4.3 DDL check — PASS

Command: grep `\b(DOUBLE|REAL|FLOAT)\b` over `app/engine/store/*.sql` → **no matches**.
Every money column in `schema_duckdb.sql` is `DECIMAL(18,2)` — including `FactActual.debit/credit/
net_amount` (:109–111), `FactBudget.amount` (:132), `FactForecast.amount` (:165).

One observation, not a finding: `schema_sqlite.sql` stores money as `TEXT`
(`FactException.subject_amount TEXT`, `amount_at_risk TEXT DEFAULT '0.00'`). SQLite is declared the
workflow-state store (ADR-004), not the analytic model, and TEXT *avoids* float — so this is
defensible, not a violation.

### 4.4 SQL `SUM`/`AVG` over money — PASS

Command: grep `SUM\(` over `app/engine/**/*.py`.

All `SUM()` targets are `DECIMAL(18,2)` columns (`fa.net_amount`, `b.amount`, `f.amount`, …), and
`analytics_repo.py:552–554` wraps results in `Decimal(str(...))`. **No `AVG()` or `MEAN()` over a
money column exists anywhere in `app/`.** Where Python-side summation of money happens — e.g.
`app/engine/store/exceptions_repo.py:871`,
`total_amt = sum(Decimal(i["amount_at_risk"]) for i in owner_items)` — the sum starts from `Decimal`,
which is the correct pattern.

### 4.5 JSON serialisation of Decimal — PASS

Commands: grep `jsonable_encoder|Decimal|default=str|json_encoders` across `app/api/`, plus
inspection of the request models.

The API boundary is correct: Pydantic request models declare monetary inputs as **`str`**
(`app/api/main.py:49`, `amount: str`), and handlers construct money as `Decimal(payload.amount)`
(`app/api/main.py:337`, `:1231`). That is exactly the `Decimal("1234.56")`-from-string construction
§1.3 rule 229 requires. No `float()` is applied to a Decimal for JSON emission anywhere in
`app/api/`. Outbound money leaves as `str` (e.g. `forecast_repo.py:423`,
`{"amount": str(amount)}`), preserving cents.

### 4.6 `round()` on money — PASS

Command: grep `round\(` across `app/**/*.py`.

Every hit is on elapsed time, AI cost/utilisation, or an acceptance-harness recall percentage
(`app/cli/main.py:38`; `app/engine/ai/usage.py:67,146,171`;
`app/engine/rules/acceptance.py:185,244`). **No `round()` is applied to a monetary value anywhere** —
`quantize_money` is used instead. No finding.

---

## 5. Headline

**Genuine money-path binary-float violations: 8 distinct sites across 4 files.**

| severity | file | lines | mechanism |
|---|---|---|---|
| **CRITICAL** | `app/engine/store/import_repo.py` | 149, 209, 210, 211 | `float()` on debit/credit/net/budget money → `DECIMAL(18,2)` |
| **HIGH** | `app/engine/store/forecast_repo.py` | 304, 416 | `float()` on computed + manual-override forecast money → `DECIMAL(18,2)` |
| **HIGH** | `app/engine/exports/excel_pack.py` | 150–178, 261–268, 330–381 | money modelled/seeded as `float` in the export dataclasses |
| **MEDIUM** | `app/engine/ai/usage.py` | 65, 66 | pure-float money arithmetic on AI vendor spend |

Plus **1 LOW adjacent finding** (`analytics_repo.py:542` — 4 dp money, *decimal* not float) reported
so it is not mis-triaged as a float bug.

**Benign hits separated out: 15** (§4.1) — ratios, counts, percentages, score points, and one
type-probe.

**The storage layer's own typing is sound.** The DDL, the SQL aggregations, the API request/response
boundary and the `round()`-vs-`quantize()` discipline all pass. The defect is concentrated in
**Python-side coercion at write time** — a `float()` wrapper sitting between a correct `Decimal` and
an equally correct `DECIMAL(18,2)` column.

---

## 6. Explicit gaps (not softened — this audit is partial)

- **GAP-1 — loss frequency unmeasured.** I ran point examples through an in-memory DuckDB but the
  400k-sample statistical run comparing `Decimal → DECIMAL(18,2)` against
  `Decimal → float → DECIMAL(18,2)` was cancelled mid-command. I therefore know the `float()`
  conversions *can* move a cent (demonstrated), but I have **not** measured how often across the
  realistic FP&A magnitude range. Do not read §3.1 as "every row is wrong".
- **GAP-2 — runtime types not confirmed for `BvARow`/`PLRow`.** The `float` annotations are on disk
  and the float money literals are on disk; which call sites actually instantiate them with `Decimal`
  was not traced to completion.
- **GAP-3 — frontend not audited.** Task scope was `app/engine/` + `app/api/`. The React/TypeScript
  client (`src/`) parses JSON money as a JavaScript `number`, which is binary floating point by
  language definition. That is a **separate audit** and is not covered by this report — flagging it
  because it is likely the largest remaining float exposure in the product.
- **GAP-4 — `Decimal(some_float)` construction.** §1.3 rule 229 bans it. I confirmed no such call on
  the audited paths (`app/api/` declares money as `str`), but I did not exhaustively grep the whole
  repo including `scripts/` and `tests/`, which are outside the stated scope.
- **GAP-5 — `FactException.amount_at_risk` write path.** Declared `TEXT` in SQLite (defensible, §4.3)
  but I did not trace whether any DuckDB-side value feeding it passes through a `float()`.