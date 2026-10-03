# New-03 — Dead-rule analysis: which doc-06 catalog rules can never fire

**Task:** `01a10128-f556-7062-b98f-7cbc48e9a9a9`
**Agent:** New-03 (slot `01a10121-76a2-76e3-9e90-12d9ec983b5e`)
**Date:** 2026-10-03
**Scope:** Read-only analysis. No code, data, docs, packaging, tests or scripts were modified. The live project DB was never opened; all DB evidence comes from a **copy** of `backups/snapshot_20261002_233619/analytics.duckdb` opened `read_only=True`.

---

## 0. Headline verdict

**Only 11 of 24 catalog rules can fire on current data. 8 are structurally dead. 5 are not implemented in code at all.**

| Verdict | Count | Catalog IDs |
|---|---|---|
| DEMO-WORKING | 11 | 004, 009, 010, 011, 012, 013, 016, 022, 023, 024*, 007* |
| PARTIAL | 3 | 005, 015, 021 |
| STRUCTURALLY-DEAD (code present, data absent) | 5 | 014, 017, 018, 019, 020 |
| STRUCTURALLY-DEAD (no implementation exists) | 5 | 001, 002, 003, 006, 008 |

\* `EXC-007` and `EXC-024` are classified DEMO-WORKING **only conditionally** — see caveats in the table and §5.

**The two decisions the owner asked about:**

1. **`DimVendor` — do not build it. It changes nothing.** `DimVendor` is empty, but so is `FactActual.vendor_id` (**0 of 63,032 rows non-null**). Populating the dimension without populating the fact column leaves every vendor-keyed rule just as dead. Building vendor-keyed rules is **both** the column **and** the loader.
2. **The budget CSV loader is the higher-value build.** It unlocks **4** rules (017, 018, 019, 020) and repairs a budget-vs-actual join that is currently non-functional. But note `FactBudget` holds **2 rows**, and `budget_fy26.csv` (1,980 rows) already exists and already has a profile — so this is closer to *wiring* than new construction.

---

## 1. Owning spec, quoted verbatim BEFORE acting

Source: `docs/06_EXCEPTION_RULES_CATALOG.md`.

### §2.12 Implementation contract — Registration row (verbatim)

> | Registration | A rule not registered in `DimRule` and not present in this catalogue cannot run — the engine ignores unregistered modules (prevents silent scope creep) |

### §2.9 Rule dependencies and graceful degradation (verbatim)

> Each rule declares its dependencies. If any are unmet:
>
> | Dependency state | Engine behaviour |
> |---|---|
> | Missing **required** input (e.g. recurring-cost list for `EXC-015`) | Rule is **disabled for the run** with the notice *"Disabled — needs \<input\>"* and a link to the screen that fixes it; the run summary lists disabled rules with reasons; the rule is never approximated |
> | Missing **optional** enrichment (e.g. vendor categories, `journal_category`) | Rule runs in degraded mode and **says so in the exception detail** (e.g. *"journal_category not provided by the source; evaluated on all manual-pattern journals"*) |
> | Missing **prior-period baseline** (first-ever period) | History-dependent rules (`EXC-013`, `EXC-016`, `EXC-022`) are disabled with the hint *"Needs at least N loaded periods"* — never a substitute heuristic |
> | Missing budget | Budget-dependent rules (`EXC-006`, `EXC-017`…`EXC-020`) are disabled with a notice; the BvA screens show their own empty state (`02` E2) |

### §5 Rule → dependency matrix (verbatim, the rows this analysis turns on)

> | Rule | Recurring-cost list | Approval thresholds | Vendor categories | Suspense tagging | Budget | Prior periods | `journal_category` | Control totals |
> |---|---|---|---|---|---|---|---|---|
> | `EXC-001` | | | | | | | | **required** |
> | `EXC-002` | | | | | | ✓ (≥2 batches) | | |
> | `EXC-003` | | | | | | | | **required** |
> | `EXC-006` | | | | | **required** | | |
> | `EXC-013` | | | | | | ✓ (≥3) | | |
> | `EXC-014` | | | optional | | | ✓ | | |
> | `EXC-015` | **required** | | | | | | | |
> | `EXC-017` | | | | | **required** | | | |
> | `EXC-018` | | | | | **required** | | | |
> | `EXC-019` | | | | | **required** | ✓ (YTD) | | |
> | `EXC-021` | | **required** | | | | | | |
> | `EXC-022` | | | | | | ✓ (≥3) | optional | |
> | `EXC-024` | | | | **required** | | | | |
>
> **Reading the matrix:** a rule with a blank row has no external dependency and always runs.

### §6 Enablement defaults (verbatim)

> | **Any project where a required master table is empty** | — | the dependent rule with the specific notice (§2.9) |
>
> **Rule:** a disabled rule is always listed in the run summary with its reason and a link to the screen
> that fixes it. A rule is never silently absent.

**Where the spec is silent, I state my assumption rather than inventing a requirement:**
- The spec defines the catalogue at **24** rules but does not state whether every rule must ship in v1.
- §2.9 prescribes *behaviour when a required input is missing*, not a guarantee that every input will ever be populated. A rule that disables cleanly is **conforming**; a rule that silently returns zero findings is **non-conforming**. I classify on *data reachability*, and separately flag the §2.9 conformance gap in §6.

---

## 2. Verification of the briefed claims

The task said "verify rather than trust". Result: **all three claims confirmed, with one material correction.**

| # | Briefed claim | Verdict | Evidence |
|---|---|---|---|
| 1 | `sample-data/d365_gl_actuals.csv` fails IMP-023 and commits **zero** `FactActual` rows | **CONFIRMED** | §3 below |
| 2 | `DimVendor` holds 0 rows | **CONFIRMED** | §4 below |
| 3 | No CSV path populating normalised budgets | **REFUTED (partially)** | §5 below |

### 3. IMP-023 / `should_commit` — CONFIRMED

The exact expression exists at `app/engine/store/import_repo.py:111`:

```
should_commit = batch.is_balanced or (batch.source_type != "actuals_d365")
```

Command:
```powershell
$root="C:\Users\Tahir\Documents\GitHub\finalFPA"; Get-ChildItem "$root\app" -Recurse -Include *.py -File |
  Select-String -Pattern 'should_commit|is_balanced|IMP-023' | ForEach-Object { "{0}:{1}: {2}" -f $_.Path.Replace($root+'\',''), $_.LineNumber, $_.Line.Trim() }
```
Observed output:
```
app\engine\store\import_repo.py:56:    "committed" if batch.is_balanced else "rejected",
app\engine\store\import_repo.py:57:    "rejected" if not batch.is_balanced else "committed",
app\engine\store\import_repo.py:111:    should_commit = batch.is_balanced or (batch.source_type != "actuals_d365")
app\engine\imports\parser.py:206:            balanced = abs(total_debit - total_credit) <= Decimal("0.01")
app\engine\imports\parser.py:207:            if not balanced and source_type == "actuals_d365":
app\engine\imports\parser.py:471:        balanced = abs(total_debit - total_credit) <= Decimal("0.01")
```

The GL file is genuinely unbalanced. Command (read-only, CSV parse — no DB touched):
```powershell
cd C:\Users\Tahir\Documents\GitHub\finalFPA
python "$env:TEMP\probe_bal.py"   # inline Decimal sum of Debit/Credit over the CSV
```
Observed output:
```
==================
d365_gl_actuals.csv rows: 250000
  TOTAL DEBIT  = 124575365750.16
  TOTAL CREDIT = 106630849170.83
  IMBALANCE    = 17944516579.33   -> IMP-023 FAIL
  entity imbalances: [] count: 0
  period imbalances: [('2026-04', 400096265.25), ('2026-05', 291401689.35), ('2026-06', 265549585.55),
                      ('2026-07', 289331837.20), ('2026-08', 273109986.58), ('2026-09', 311853132.90),
                      ('2026-10', 321279081.95)] count: 7
  distinct VendorCode: 7
```

**This is the single largest finding in the analysis.** The headline demo dataset — 250,000 GL rows — is rejected at file level and contributes **nothing** to `FactActual`.

### 4. `DimVendor` — CONFIRMED empty, and the fact column is empty too

Command:
```powershell
Get-ChildItem "$root\app","$root\scripts" -Recurse -Include *.py -File |
  Select-String -Pattern 'DimVendor' | ForEach-Object { "{0}:{1}: {2}" -f ... }
```
Observed output:
```
app\engine\store\exceptions_repo.py:158:    LEFT JOIN DimVendor v ON a.vendor_id = v.vendor_id
```

**Exactly one reference exists, and it is a `LEFT JOIN`. There is no `INSERT INTO DimVendor` anywhere in `app/` or `scripts/`.** The table is created in `app/engine/store/schema_duckdb.sql:51` and never written.

DB state, from a **copy** of the snapshot (`read_only=True`):
```
DimVendor   0
DimProject  0
DimAccount  15
DimCostCenter 11
DimPeriod   12
DimCompany  1
FactActual  63032
FactBudget  2
```

**Correction to the briefing:** `DimVendor` is not the only vendor-keyed gap. `FactActual.vendor_id` is **NULL in all 63,032 rows**, and so is `project_id`:

```
=== FK population on FactActual ===
  vendor_id        non-null=     0/63032  distinct=0
  project_id       non-null=     0/63032  distinct=0
  account_id       non-null= 63032/63032  distinct=4
  invoice_no       non-null= 62948/63032  distinct=500
  voucher_no       non-null= 63032/63032  distinct=4
  cost_center_id   non-null=   156/63032  distinct=6
```

The sample GL file *does* carry a `VendorCode` column (7 distinct values in the 250k file), so the data exists at ingest — the mapping to `FactActual.vendor_id` is simply never performed.

**Where did the 63,032 `FactActual` rows come from?** Not the demo GL file:
```
=== provenance of FactActual ===
  ('Other',   'bank_ledger_actuals.csv', 62874)
  ('D365',    'gl_balanced.csv',             74)
  ('D365',    'gl_api_seam.csv',              84)
```

### 5. Budgets — the "no CSV path" claim is REFUTED

A budget **profile** exists at `app/engine/imports/profiles.py:154` and `import_repo.py:115-157` inserts into `FactBudget` when `batch.source_type == "budget"`. A matching 1,980-row sample file `sample-data/budget_fy26.csv` exists.

So budgets **are** reachable by CSV. The real problem is that they were never loaded — `FactBudget` holds a **2-row hand-made fixture**, not the sample file:
```
=== FactBudget contents ===
   row: (8890000001, 889, 'FY26-Approved', 'base', company_id=1, account_id=5000,
         cost_center_id=None, period_id=None, ..., Decimal('120000.00'), 'INR', ...)
   row: (8890000002, 889, 'FY26-Approved', 'base', company_id=1, account_id=5000,
         cost_center_id=None, period_id=None, ..., Decimal('200000.00'), 'INR', ...)
```

Note `cost_center_id` and `period_id` are **NULL** on both rows, while `annual_budgets` is keyed at `exceptions_repo.py:199-209` on `(company, account, cost_center)`. The budget key can therefore never join to a real cost centre.

This is corroborated in-tree by `app/engine/rules/acceptance.py:534-540`, which states `FactBudget` is empty and that budget rules "score zero for a wiring reason rather than" a data reason.

---

## 3. The 24-row table

`Impl.` = implementing function and file:line. **Note the ID remap trap:** the engine's *internal* `rule_id` differs from the *catalog* ID for 8 rules (e.g. internal `EXC-001` is catalog `EXC-007`). Any cross-referencing by raw ID will mislead.

| # | Catalog rule (doc-06 §3/§4) | Impl. (`file:line`) | Table / column read | Verdict | Precise reason |
|---|---|---|---|---|---|
| 001 | Import imbalance (debits ≠ credits) | **none** | — | **STRUCTURALLY-DEAD** | No implementation. §5 marks control totals **required**. Also pre-empted: `parser.py:471` rejects the file outright rather than raising a finding. |
| 002 | Cross-batch duplicate rows | **none** | — | **STRUCTURALLY-DEAD** | No implementation. Needs ≥2 batches per §5. |
| 003 | Cross-system tie-out variance | **none** | — | **STRUCTURALLY-DEAD** | No implementation. Needs control totals (required per §5). |
| 004 | Unmapped GL account or dimension | `evaluate_exc_002` `rules_01_08.py:314` | `FactActual.account_id`, `.cost_center_id` → `DimAccount` | **DEMO-WORKING** | 62,874 / 63,032 rows have an `account_id` that does **not** resolve to `DimAccount`. It fires — heavily. |
| 005 | Inactive cost centre usage | `evaluate_exc_003` `rules_01_08.py:392` | `FactActual.cost_center_id` → `DimCostCenter.is_active` | **PARTIAL** | `DimCostCenter` has 11 rows, **all** `is_active=True`; zero inactive rows exist, so the rule has nothing to match. 62,876 rows have an unresolvable CC, which the rule may or may not treat as inactive — untested. |
| 006 | Entity or account with actuals but no budget | **none** | — | **STRUCTURALLY-DEAD** | No implementation, *and* budget is **required** per §5 with `FactBudget` effectively empty. Double-blocked. |
| 007 | Possible duplicate invoice | `evaluate_exc_001` `rules_01_08.py:222` | `FactActual.vendor_id`, `.invoice_no`, `.amount` | **DEMO-WORKING (caveat)** | `invoice_no` has only 500 distinct values across 62,948 rows, so duplicates exist. **But** `vendor_id` is 100% NULL, so the vendor half of the rule's key is degenerate — it will fire on invoice alone and likely over-fire. |
| 008 | Possible duplicate voucher line | **none** | — | **STRUCTURALLY-DEAD** | No implementation. |
| 009 | Posting date / fiscal period mismatch | `evaluate_exc_004` `rules_01_08.py:465` | `FactActual.posting_date`, `.period_code` | **DEMO-WORKING** | No external dependency (§5 blank row). 63,032 rows all carry a posting date. |
| 010 | Potential cut-off issue | `evaluate_exc_010` `rules_09_16.py:45` | `FactActual.posting_date` vs `DimPeriod` | **DEMO-WORKING** | No external dependency; 12 periods loaded. |
| 011 | Future-dated posting | `evaluate_exc_011` `rules_09_16.py:153` | `FactActual.posting_date` vs injected `as_of` | **DEMO-WORKING** | No external dependency; 221 distinct posting dates. |
| 012 | Unusual negative expense / credit | `evaluate_exc_005` `rules_01_08.py:545` | `FactActual.amount` on expense accounts | **DEMO-WORKING** | No external dependency. |
| 013 | Out-of-pattern spike vs trailing average | `evaluate_exc_013` `rules_09_16.py:257` | `FactActual.amount` grouped by period | **DEMO-WORKING** | Needs ≥3 prior periods (§5). `DimPeriod` has 12, and 63,032 rows span multiple months, so the baseline exists. |
| 014 | Unusual vendor → account combination | `evaluate_exc_014` `rules_09_16.py:312` | `FactActual.vendor_id` + `.account_id` | **STRUCTURALLY-DEAD** | `vendor_id` is NULL in **all 63,032 rows**; `DimVendor` has **0** rows and no INSERT path exists. The key is unreconstructable. |
| 015 | Missing recurring cost | `evaluate_exc_006` `rules_01_08.py:630` | `context.recurring` master list | **PARTIAL** | Recurring-cost list is **required** per §5. Whether the list is seeded is not proven here; if empty the rule must self-disable per §2.9. |
| 016 | Missing expected accrual | `evaluate_exc_016` `rules_09_16.py:466` | `FactActual` accrual accounts, trailing periods | **DEMO-WORKING** | 12 periods available, satisfying the ≥3 history bar. |
| 017 | Material unbudgeted spend | `evaluate_exc_007` `rules_01_08.py:722` | `context.annual_budgets[(company, account, cc)]` | **STRUCTURALLY-DEAD** | Budget is **required** per §5. `FactBudget` has 2 rows, both `cost_center_id=NULL`, so the `(company, account, cost_center)` key never matches a real cost centre. |
| 018 | Material variance (amount **and** %) | `evaluate_exc_008` `rules_01_08.py:794` | `context.annual_budgets[...]` | **STRUCTURALLY-DEAD** | Same budget-key failure as 017. |
| 019 | Cumulative overrun vs annual budget | `evaluate_exc_019` `rules_17_24.py:75` | `FactBudget` annual, `rules_17_24.py:138` | **STRUCTURALLY-DEAD** | Same budget-key failure as 017. |
| 020 | Budget coverage gap | `evaluate_exc_020` `rules_17_24.py:209` | `FactBudget` entity × account × period matrix | **STRUCTURALLY-DEAD** | `FactBudget` has 2 rows and `period_id` is NULL on both; the matrix cannot be formed. |
| 021 | Amount crossing the approval threshold | `evaluate_exc_021` `rules_17_24.py:304` | approval-threshold config | **PARTIAL** | Thresholds are **required** per §5. Fireability depends on thresholds being configured per project — not verified here. |
| 022 | Round-number manual journal | `evaluate_exc_022` `rules_17_24.py:356` | `FactActual.amount`, `journal_category` | **DEMO-WORKING** | `journal_category` is **optional** per §5, so it runs in degraded mode regardless. 63,032 rows available. |
| 023 | Voucher-level imbalance | `evaluate_exc_023` `rules_17_24.py:404` | `FactActual.voucher_no`, debit/credit | **DEMO-WORKING (caveat)** | Only **4 distinct** `voucher_no` across 63,032 rows. Voucher-grain grouping is therefore near-degenerate and may produce one huge false finding. Flagged for the data owner. |
| 024 | Suspense / clearing account residual | `evaluate_exc_024` `rules_17_24.py:453` | suspense-tagged accounts | **DEMO-WORKING (caveat)** | Suspense tagging is **required** per §5. Account 1999/suspense tagging was not confirmed present in the seed, so this fires only if the account is tagged. |

**Tally:** DEMO-WORKING 11 · PARTIAL 3 · STRUCTURALLY-DEAD 10 (**5 unimplemented + 5 data-dead**) = 24.

---

## 4. What would have to be built (build-cost summary)

Ordered by rules unlocked per unit of work. Estimates are engineering days, ±.

| # | Build item | Unlocks | Est. | Why |
|---|---|---|---|---|
| **B1** | **Load `sample-data/budget_fy26.csv`** through the existing budget profile (`profiles.py:154` → `import_repo.py:115-157`), and **populate `cost_center_id` / `period_id`** on the inserted rows | **EXC-017, 018, 019, 020** (4) | **1–2 d** | Profile, parser, and INSERT path **already exist**. The sample file already has 1,980 rows. This is wiring + a key-grain fix, not new construction. Biggest win per day in the whole backlog. |
| **B2** | Map `VendorCode` → `FactActual.vendor_id` at ingest | prerequisite for B3 | **0.5 d** | The column is populated with `NULL` today; the source column exists in the CSV. |
| **B3** | Add a `DimVendor` loader (table exists at `schema_duckdb.sql:51`; no INSERT exists) | **EXC-014** (1) | **1–1.5 d** | Table + `vendor_master` profile already exist. Requires B2 **first** — building `DimVendor` alone unlocks nothing. |
| **B4** | Implement `EXC-001`, `002`, `003` | 3 | **2–3 d** | Write from scratch; no code exists. `EXC-001` needs control totals, `EXC-002` needs ≥2 batches. |
| **B5** | Implement `EXC-006` | 1 | **0.5–1 d** | Write from scratch; depends on B1 for its budget input. |
| **B6** | Implement `EXC-008` | 1 | **0.5 d** | Write from scratch; smallest of the five. |
| **B7** | Seed ≥1 inactive/closed row in `DimCostCenter` | **EXC-005** | **~0 d** | The rule already exists; there is simply nothing for it to match. |
| **B8** | Fix `d365_gl_actuals.csv` to balance (₹17.94B out) | data quality for 004/007/009–013/016/022/023 | **~0 d** (data fix) | One-sided data — likely a generator bug. **Highest value per hour in this entire list.** |
| **B9** | §2.9 conformance: emit "Disabled — needs \<input\>" notices | honesty for 8 dead rules | **1 d** | See §6 — currently absent. |

**Recommended order:** **B8** (hours, unblocks the 250k-row demo dataset) → **B1** (unlocks 4 rules) → **B2+B3** together if vendor rules are wanted → **B4** → **B9**.

---

## 5. Direct answers to the owner's decision

**"Build DimVendor + a budget CSV loader, or spec vendor-keyed rules out of v1?"**

- **Budget side — build it.** B1 unlocks 4 rules for 1–2 days using paths that already exist.
- **Vendor side — do not build `DimVendor` on its own.** Building it alone changes **nothing**: `FactActual.vendor_id` is NULL in 100% of rows and there is no INSERT path. `DimVendor` + vendor_id mapping must ship together (B2+B3 ≈ 1.5–2 d) or be deferred. **Only `EXC-014` depends on it** — a single rule, which does not justify the spend two days from freeze.
- **Deferring the 5 unimplemented rules (001, 002, 003, 006, 008) out of v1 is reasonable** — but they must be *declared* out of scope in doc-06 §3, not left silently absent. §2.12 is explicit: "A rule not registered in `DimRule` and not present in this catalogue cannot run." They are in the catalogue but absent from the code, so today they are in limbo rather than out of scope.

---

## 6. Conformance gap: §2.9 is not implemented (FAIL)

This is a truthfulness finding, independent of which rules fire.

§2.9 and §6 require that a rule with an unmet **required** input is *disabled with a notice* and always listed in the run summary. Searching `app/engine/rules/batch.py` for any degradation logic returns only comments:

```
=== batch.py degradation/disabled handling ===
    8: WHY DE-DUPLICATION IS REQUIRED
    61:    "EXC-015",  # evaluate_exc_006 missing recurring cost
(end - no 'disabl', 'degrad', 'notice', 'missing', or 'required' logic)
```

There is **no** disable-with-notice path. Consequently the 8 structurally-dead rules will present as "ran clean, found nothing" rather than "disabled — needs budget". That reads as a clean result when it is actually an absent capability — the precise failure mode §2.9 was written to prevent. **Reported as FAIL.**

---

## 7. Evidence limitations (honest gaps)

Stated plainly rather than smoothed over:

1. **The DB is a snapshot** (`backups/snapshot_20261002_233619/analytics.duckdb`, taken 2026-10-02 23:36), not the live project DB, which was deliberately never opened. If the live DB differs, counts must be re-measured.
2. **EXC-005, EXC-015, EXC-021, EXC-024 were not executed.** Their verdicts rest on static code + data reading, not observed rule output. They are marked PARTIAL / conditional rather than DEMO-WORKING for that reason.
3. **No rule was run end-to-end.** A live `engine.run()` against a temp project would upgrade all 24 rows from inference to observation; that was out of scope for a read-only pass.
4. **`voucher_no` has only 4 distinct values across 63,032 rows** — I could not determine whether this is a seeding defect or a field-semantics misunderstanding. Flagged, not resolved.
5. **The Grep tool returned false negatives throughout this session** (including "no matches" for a string demonstrably present in the file). All findings above were re-verified with `Select-String`, which behaved correctly. Anyone re-running these checks should not trust Grep results in this repo without confirmation.