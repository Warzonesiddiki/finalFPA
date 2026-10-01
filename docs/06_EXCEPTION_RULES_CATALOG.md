> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-EXC-001`…`FR-EXC-020`, `FR-SET-004`, `FR-SET-010`, `FR-IMP-017`/`FR-IMP-018`; every exception rule's logic, thresholds, severity, owner, mitigation, test case
> **TL;DR (≤ 15 lines):** This document is the formal catalogue of the **24 exception rules** (`EXC-001`…
> `EXC-024`) the engine runs. Each rule is fully specified: business intent, severity, suggested owner role,
> master-data dependencies, exact deterministic logic, subject-key definition (which fixes the exception's
> stable identity), thresholds with defaults, strictness tier, false-positive mitigation, and a planted
> sample case with an expected verdict. §2 defines the engine model that applies to all rules — identity
> and re-run semantics, statuses, aging buckets, owner auto-assignment, enable/disable, effectiveness
> statistics and strictness tiers. §7 maps 40 planted cases in the sample dataset to rules and expected
> verdicts; the machine-readable answer key is `sample-data/expected_exceptions.csv`. Rules flag
> **potential** exceptions for human review — the engine never concludes, never auto-closes, and never
> posts anything.

---

# 06 — EXCEPTION RULES CATALOG

## 1. Purpose, scope and the honesty rule

This document owns **rule logic**: what each rule detects, on what evidence, with which thresholds, and
how a human is meant to act on it. Boundaries:

| Concern | Owner |
|---|---|
| Rule logic, thresholds, severities, subject keys, plantings | **`06` (this document)** |
| Formula arithmetic used by rules (variance, %, materiality, ratio guards) | `05` — referenced by `CALC-nnn`, never restated |
| Engine behaviour and register workflow (`FR-EXC-*`) | `02` |
| Register screens, wording, badges | `08` |
| Rule configuration storage (`RuleConfig`, `DimRule`) | `03` |
| Rule implementation in code | `app/engine/rules/` (§2.12) |

### 1.1 The honesty rule (binding, from P8)

The engine detects **patterns**. It does not determine whether an entry is wrong. Therefore:

1. Every exception is presented as *"Potential exception — requires accounting review."*
2. Rule names describe the pattern, never a verdict: *"Possible duplicate invoice"*, never *"Duplicate
   invoice"*; *"Potential cut-off issue"*, never *"Wrong period"*.
3. **Nothing is auto-closed, auto-explained, auto-corrected or auto-posted.** The engine raises; humans
   decide. The only automatic transitions are raise, update-evidence and flagged-again.
4. A rule that cannot run for lack of input is **disabled with a visible notice**, never approximated into
   a false positive (§2.9).

## 2. The engine model (applies to every rule)

### 2.1 Rule anatomy

Every rule in §4 defines exactly these fields, in this order:

| Field | Meaning |
|---|---|
| **Family / version** | Grouping and rule version (`1.0`) — a logic change bumps the version |
| **Intent** | The control objective the rule serves |
| **Severity** | `High` / `Medium` / `Low` default (per-rule, overridable per project) |
| **Owner role** | Suggested accounting owner role for auto-assignment (§2.6) |
| **Depends on** | Master data, settings, prior periods, optional columns the rule needs |
| **Subject key** | The canonical string that identifies the subject of the exception (§2.2) |
| **Logic** | Deterministic pseudocode; all arithmetic references `CALC-nnn` from `05` |
| **Thresholds** | Named parameters with defaults; effective value recorded on each raise (§2.10) |
| **Tier** | `exact` (deterministic match) or `fuzzy` (statistical/threshold-based, requires mitigation) |
| **Mitigation** | How false positives are suppressed or explained |
| **Sample case** | The planted case from the sample dataset with the exact expected verdict |
| **Registers on** | Which subject rows the exception links to (for drill-down and the evidence bundle) |

### 2.2 Identity and re-run semantics (Addon 2 §D.1 — binding)

| Rule | Detail |
|---|---|
| Identity | `identity_hash = SHA-256(rule_id + '\|' + subject_key)` — one exception per rule per subject, forever (`03` §5.2) |
| Re-run behaviour | A re-run **updates** matching exceptions (evidence, amounts, `last_seen_at`, effective threshold) and **never duplicates**, **never wipes workflow state** |
| Open stays open | An `open`/`in_review` exception stays in its state across re-runs |
| Closed stays closed | A `closed` exception that matches again is **not** auto-reopened; it receives the **"flagged again"** badge plus a `flagged_again` event, and stays closed until a human reopens it |
| `first_seen_period_id` | Set once and never overwritten — it is the aging anchor |
| Disappeared subjects | An exception whose subject no longer matches (data corrected/voided) is **not** deleted; it keeps its state and shows a *"no longer detected in the current data"* marker on its next run, with the last-detected timestamp |
| History | Every raise, flag-again, status change, owner change and note is an append-only `FactExceptionEvent` |
| Determinism | Same data + same configuration + same rule version ⇒ identical exception set (tested by running twice and comparing) |

**Worked scenario (the gate's required proof):** run 1 raises `EXC-018` for account 5200/CC-100 at
`variance = +540,000.00` (severity High) → the analyst moves it to `in_review` and adds a note → the FP&A
lead lowers `materiality_pct` from 2% to 1.5% and re-runs → the exception matches again: status stays
`in_review`, the note survives, `effective_threshold` updates to the new value, and a `threshold_changed`
event is recorded. No duplicate row is created.

### 2.3 Statuses and transitions (human-only)

```
                 ┌──────────────► not_applicable (reason required, terminal-ish: reopenable)
                 │
open ──► in_review ──► explained ──► corrected ──► closed
  ▲            │                                    │
  └────────────┴──── reopened (reason required) ◄────┘
```

| Rule | Detail |
|---|---|
| Who may transition | A human only. The engine may only raise, update and flag-again |
| Required evidence | `corrected` requires a note stating what was changed and when; `not_applicable` requires a reason (this feeds effectiveness statistics) |
| Audit | Every transition writes an event with actor and timestamp |
| Bulk | Bulk transitions write one event per exception (`FR-EXC-010`) |
| Withdrawal | If a human closes an exception, no later run may reopen it silently |

### 2.4 Severity model

| Severity | Meaning | Default SLA (aging target) |
|---|---|---|
| `High` | Material misstatement risk, control failure, or data integrity issue (e.g. imbalance, cut-off, approval breach) | Close within **7 days** |
| `Medium` | Likely misstatement or process issue worth investigation (e.g. duplicates, spikes, missing recurring cost) | Close within **21 days** |
| `Low` | Hygiene or informational signal (e.g. inactive cost centre, unmapped vendor) | Close within **45 days** |

Severity is overridable per rule (`FR-EXC-012`) and recorded on each raise; the aging target drives the
overdue highlight (§2.5), not any automatic action.

### 2.5 Aging

| Concept | Definition |
|---|---|
| Days open | `current_date − date(first_seen_period_id's period end)`, **plus** `raised_at` for intra-period precision; the register shows both the period-age and the calendar-age |
| Buckets | `0–7`, `8–30`, `31+` days |
| Overdue | `days_open > severity SLA` → highlighted with a text badge (`Overdue 12d`), never colour alone |
| Report | Aging is summarised per rule and per owner in the effectiveness dashboard and the owner-wise export |

**Why period-based aging:** finance work is period-driven; an exception raised for Sep-26 remains
"Sep-26 work" regardless of when it is reviewed. The register therefore shows *"Sep-26 · 24 days"*.

### 2.6 Owner auto-assignment

Resolution order (first match wins), then overridable by hand:

1. `MasterOwnerAssignment` at scope `account` (most specific).
2. `MasterOwnerAssignment` at scope `cost_center`.
3. `MasterOwnerAssignment` at scope `company`.
4. `DimCostCenter.owner_name` (descriptive attribute).
5. The rule's **default owner role** (§4) resolved to a named person if the role is mapped in Settings.
6. Otherwise **`Unassigned`** — surfaced in a dedicated filter so nothing is lost.

Every assignment change is audited; a bulk assignment writes one event per exception.

### 2.7 Strictness tiers

| Tier | Meaning | Rules |
|---|---|---|
| **`exact`** | Deterministic match on keys, dates, amounts or missing master data. A raise is a fact about the data, not a statistical judgement | `EXC-001`…`EXC-012`, `EXC-021`, `EXC-023`, `EXC-024` |
| **`fuzzy`** | Threshold- or statistics-based; carries an explicit mitigation and a tuning mechanism | `EXC-013`…`EXC-020`, `EXC-022` |

**Obligation for `fuzzy` rules:** every fuzzy rule must state its false-positive mitigation and carry a
tuning path (threshold edit, master-data curation, or statistical parameter). A fuzzy rule that produces
more `not_applicable` closures than `explained`/`corrected` closures over two consecutive periods is
flagged for review on the effectiveness dashboard (§9).

### 2.8 Evaluation scope and grain

| Aspect | Rule |
|---|---|
| Scope | Rules run per project over loaded periods; a run may be scoped to one period (default: all open periods, plus previously raised exceptions for closed periods so their status is preserved) |
| Grain | Each rule declares the grain it evaluates at (transaction, voucher, account × period, account × period × cost centre, entity × period) |
| Currency | All thresholds are in the project's reporting currency; single-currency project in v1 (`01` §6.3) |
| Materiality | Amount thresholds default to `max(absolute_floor, materiality_pct × |budget|)` (`CALC-080`); ratio lines use the percentage-point test |
| Closed periods | Rules do not create **new** exceptions in closed periods (the close snapshot is frozen), but existing exceptions remain visible and workflowable; a reopen re-enables raising for that period |

### 2.9 Rule dependencies and graceful degradation

Each rule declares its dependencies. If any are unmet:

| Dependency state | Engine behaviour |
|---|---|
| Missing **required** input (e.g. recurring-cost list for `EXC-015`) | Rule is **disabled for the run** with the notice *"Disabled — needs <input>"* and a link to the screen that fixes it; the run summary lists disabled rules with reasons; the rule is never approximated |
| Missing **optional** enrichment (e.g. vendor categories, `journal_category`) | Rule runs in degraded mode and **says so in the exception detail** (e.g. *"journal_category not provided by the source; evaluated on all manual-pattern journals"*) |
| Missing **prior-period baseline** (first-ever period) | History-dependent rules (`EXC-013`, `EXC-016`, `EXC-022`) are disabled with the hint *"Needs at least N loaded periods"* — never a substitute heuristic |
| Missing budget | Budget-dependent rules (`EXC-006`, `EXC-017`…`EXC-020`) are disabled with a notice; the BvA screens show their own empty state (`02` E2) |

### 2.10 Effective thresholds and traceability

Every raised exception stores `effective_threshold` — a human-readable string of the parameters actually
used (e.g. `materiality 2.0% or ₹500,000; AND pct 5%`). This is what makes a flag explainable months
later, after settings have changed. Threshold changes are versioned (`VersionHistory`) and mark derived
results stale (`FR-SET-010`).

### 2.11 Rule configuration defaults

| Configuration | Default | Where |
|---|---|---|
| Enabled/disabled | Per rule, defaults in §6 | Settings → Thresholds & rules |
| Thresholds | Per rule, defaults in §4 | Same screen, with reset-to-default |
| Severity override | Per rule | Same screen |
| Owner role mapping | Role → person mapping | Settings → Master data |
| Global materiality | `materiality_pct = 2%`, `absolute_floor = ₹500,000` | Settings → Thresholds (`CALC-080`) |
| Per-rule overrides | Win over global | Same screen |

### 2.12 Implementation contract

| Contract | Detail |
|---|---|
| Location | One module per rule under `app/engine/rules/`, each exposing `evaluate(context) -> list[Finding]` and declaring `rule_id`, `version`, `dependencies`, `subject_key(finding)` and `defaults` |
| Purity | Rules are pure functions of the loaded data + configuration; no network, no clock beyond an injected `as_of` date, no randomness |
| Determinism | No `set` iteration order, no `dict` ordering assumptions, no floating point (`Decimal` only, `CALC` conventions) |
| Evidence | Every finding returns the exact row references (`source_row_ref`, voucher, line) used to raise it, capped at a documented sample size for display while the full set is retrievable for the evidence bundle (`FR-EXC-016`) |
| Coverage bar | Each rule module requires ≥ 90% engine coverage and at least one golden test per branch (`14`, Addon 2 §F.1) |
| Registration | A rule not registered in `DimRule` and not present in this catalogue cannot run — the engine ignores unregistered modules (prevents silent scope creep) |

## 3. Catalogue index (24 rules)

| ID | Rule name | Family | Severity | Tier | Owner role | Depends on |
|---|---|---|---|---|---|---|
| `EXC-001` | Import imbalance (debits ≠ credits) | Import integrity | High | exact | GL Accountant | — |
| `EXC-002` | Cross-batch duplicate rows | Import integrity | High | exact | GL Accountant | — |
| `EXC-003` | Cross-system tie-out variance | Import integrity | High | exact | Controller | Control totals |
| `EXC-004` | Unmapped GL account or dimension | Import integrity | Medium | exact | FP&A Analyst | — |
| `EXC-005` | Inactive cost centre usage | Master data hygiene | Low | exact | Cost Centre Owner | Master data |
| `EXC-006` | Entity or account with actuals but no budget | Master data hygiene | Medium | exact | FP&A Analyst | Budget |
| `EXC-007` | Possible duplicate invoice | Duplicates | High | exact | Accounts Payable | — |
| `EXC-008` | Possible duplicate voucher line | Duplicates | Medium | exact | GL Accountant | — |
| `EXC-009` | Posting date / fiscal period mismatch | Timing | High | exact | GL Accountant | Source period column |
| `EXC-010` | Potential cut-off issue | Timing | High | exact | GL Accountant | — |
| `EXC-011` | Future-dated posting | Timing | Medium | exact | GL Accountant | — |
| `EXC-012` | Unusual negative expense / credit | Anomaly — sign | Medium | exact | Cost Centre Owner | — |
| `EXC-013` | Out-of-pattern spike vs trailing average | Anomaly — magnitude | Medium | fuzzy | Cost Centre Owner | ≥3 loaded periods |
| `EXC-014` | Unusual vendor → account combination | Anomaly — pairing | Medium | fuzzy | Accounts Payable | Prior periods |
| `EXC-015` | Missing recurring cost | Completeness | High | fuzzy | Accounts Payable | Recurring-cost list |
| `EXC-016` | Missing expected accrual | Completeness | Medium | fuzzy | GL Accountant | ≥3 loaded periods |
| `EXC-017` | Material unbudgeted spend | Budget relationship | High | fuzzy | FP&A Analyst | Budget |
| `EXC-018` | Material variance (amount **and** %) | Budget relationship | High | fuzzy | FP&A Analyst | Budget |
| `EXC-019` | Cumulative overrun vs annual budget | Budget relationship | Medium | fuzzy | FP&A Analyst | Budget |
| `EXC-020` | Budget coverage gap | Budget relationship | Medium | exact | FP&A Analyst | Budget |
| `EXC-021` | Amount crossing the approval threshold | Controls | High | exact | Controller | Approval thresholds |
| `EXC-022` | Round-number manual journal | Controls | Low | fuzzy | GL Accountant | `journal_category` (optional) |
| `EXC-023` | Voucher-level imbalance | Controls | High | exact | GL Accountant | — |
| `EXC-024` | Suspense / clearing account residual | Controls | High | exact | Controller | Account tagging |

## 4. Rule specifications

### EXC-001 — Import imbalance (debits ≠ credits)

| Field | Value |
|---|---|
| **Family / version** | Import integrity / 1.0 |
| **Intent** | Catch a source file that cannot be loaded as a balanced ledger — the earliest possible point to stop bad data |
| **Severity** | **High** |
| **Owner role** | GL Accountant (fallback: Controller) |
| **Depends on** | Nothing |
| **Subject key** | `batch_id` (one exception per unbalanced batch) |
| **Logic** | `debit_total − credit_total` per `CALC-071`, computed at minor-unit precision per (file, entity, period) and overall. If any level ≠ the configured tolerance (default `0.00`) → raise. Severity is High regardless of amount because an unbalanced load corrupts every downstream total |
| **Thresholds** | `balance_tolerance` = `0.00` (may be raised only with a documented reason; the value appears in the report and on the exception) |
| **Tier** | `exact` |
| **Mitigation** | Normally caught and **rejected at import** by `IMP-023`, so this exception fires only for (a) legacy batches loaded before the check existed, (b) a tolerance explicitly configured, or (c) a void that removed one side of a batch. The exception detail states which |
| **Sample case** | Planting P1: the `Other System — Bank Ledger` malformed corpus file `bank_ledger_unbalanced.csv` (debits `1,84,50,200.00`, credits `1,84,49,850.00`, variance `350.00`) is imported **with a configured tolerance of ₹500** → batch commits with the tolerance recorded → the rule raises |
| **Expected verdict** | **Raised**, `High`, amount at risk = `350.00`, subject = batch, `effective_threshold = balance_tolerance 500.00` |
| **Registers on** | All rows of the batch; the drill shows the largest contributing vouchers first |

### EXC-002 — Cross-batch duplicate rows

| Field | Value |
|---|---|
| **Family / version** | Import integrity / 1.0 |
| **Intent** | Prevent the same transaction being counted twice because a file was re-exported with a different name or an overlapping date range |
| **Severity** | **High** |
| **Owner role** | GL Accountant |
| **Depends on** | ≥2 committed batches |
| **Subject key** | `company_code\|voucher_no\|line_no` (primary) and `vendor_code\|invoice_no\|posting_date\|amount` (secondary) |
| **Logic** | For each batch, compare its rows against all **earlier committed** batches using both keys from `04` §13. Any match where the batch is still committed on both sides → raise, with the earlier batch ID, its import date, and the overlapping row count. Rows skipped at import time by an explicit user decision are excluded and the decision is quoted in the detail |
| **Thresholds** | `min_overlap_rows` = `1` (a single overlapping row is worth knowing); `include_voided_batches` = `false` |
| **Tier** | `exact` |
| **Mitigation** | Purely mechanical; false positives are limited to legitimately identical rows (e.g. two genuine identical small expenses on the same day with the same voucher line — impossible by voucher+line key, which is why the voucher key is primary). The secondary invoice key can legitimately match a credit note and an invoice; the detail says which key matched |
| **Sample case** | Planting P2: batch 41 re-imports `GL_Sep26_reexport.xlsx` containing 3 vouchers already loaded by batch 37 (same voucher numbers, different file layout) |
| **Expected verdict** | **Raised** once per overlapping subject (3 exceptions), `High`, with `Overlap: 3 rows · earlier batch 37 (imported 03-Oct-2026)` |
| **Registers on** | The overlapping rows in both batches |

### EXC-003 — Cross-system tie-out variance

| Field | Value |
|---|---|
| **Family / version** | Import integrity / 1.0 |
| **Intent** | Detect that a source system's own control totals disagree with what was loaded — the v1 substitute for an automated cross-system tie-out |
| **Severity** | **High** |
| **Owner role** | Controller |
| **Depends on** | The optional control-totals block in the actuals template (`04` §12) |
| **Subject key** | `batch_id\|control_total_scope` |
| **Logic** | `CALC-070`: `variance = loaded_total − supplied_total` for each supplied control total. Non-zero beyond tolerance → raise. If no control totals were supplied, the rule is **disabled for that batch** with the notice *"No control-totals block supplied"* — never silently passed (`IMP-025` reports the skip) |
| **Thresholds** | `control_total_tolerance` = `0.00` |
| **Tier** | `exact` |
| **Mitigation** | The scope decision for v1 is explicit (`DEC-020`): **file-level control totals only**; an automated cross-system tie-out (matching payroll/procurement totals against the GL) is parked (`BL-014`). The exception detail states the scope so nobody infers more coverage than exists |
| **Sample case** | Planting P3: the `D365 GL` October file supplies a control total of `1,84,00,000.00` while the loaded total is `1,83,99,650.00` |
| **Expected verdict** | **Raised**, `High`, `variance = −350.00` (loaded below supplied), subject = batch + scope |
| **Registers on** | The batch; the drill shows the file's control-total block and the loaded total with its row count |

### EXC-004 — Unmapped GL account or dimension

| Field | Value |
|---|---|
| **Family / version** | Import integrity / 1.0 |
| **Intent** | Ensure every posted account and dimension value is represented in the model, so nothing hides in an "unknown" bucket |
| **Severity** | **Medium** |
| **Owner role** | FP&A Analyst |
| **Depends on** | Nothing (compares source values against `DimAccount`, `DimCostCenter`, `DimVendor`, `DimProject`) |
| **Subject key** | `dimension_type\|source_value` (e.g. `account\|5999-TEMP`) |
| **Logic** | Scan loaded facts for values that resolved to an auto-created placeholder dimension row or that were accepted under an "unknown" mapping. One exception per distinct source value, with the row count and the total amount it carries, and a link to the mapping screen |
| **Thresholds** | `min_rows` = `1` (every unmapped value is worth surfacing); `min_amount` = `0.00` |
| **Tier** | `exact` |
| **Mitigation** | Not noisy by construction — one exception per distinct value, not per row. Closing requires either mapping the value or recording that it is intentionally out of scope (e.g. a dormant account) |
| **Sample case** | Planting P4: 6 rows post to account `5999-TEMP` (₹ 42,300.00 total) which is not in the chart of accounts |
| **Expected verdict** | **Raised** once, `Medium`, subject `account\|5999-TEMP`, `6 rows · ₹ 42,300.00` |
| **Registers on** | All rows carrying the unmapped value |

### EXC-005 — Inactive cost centre usage

| Field | Value |
|---|---|
| **Family / version** | Master data hygiene / 1.0 |
| **Intent** | Detect postings to cost centres that the business considers closed, merged or dormant — a common source of misallocated cost |
| **Severity** | **Low** |
| **Owner role** | Cost Centre Owner |
| **Depends on** | Cost-centre master data with `is_active` flags |
| **Subject key** | `cost_center_code\|period_id` |
| **Logic** | For each period, find cost centres marked inactive in `DimCostCenter` that carry non-zero net activity. Raise one exception per inactive cost centre per period with the row count, net amount, and the account split |
| **Thresholds** | `min_amount` = `0.00` (any activity is flagged); `ignore_credit_only` = `false` |
| **Tier** | `exact` |
| **Mitigation** | Inactivity is often intentional (final accruals, reversals), so severity is Low and the detail shows the account mix so the reviewer can dismiss it in seconds. If a cost centre is legitimately still in use, the fix is to reactivate it in master data (recorded, versioned) — not to silence the rule |
| **Sample case** | Planting P5: `CC-950` (marked inactive from FY26-P06) receives 4 postings totalling ₹ 96,500.00 in FY26-P09 |
| **Expected verdict** | **Raised** once for `CC-950\|FY26-P09`, `Low`, `4 rows · ₹ 96,500.00` |
| **Registers on** | The 4 postings |

### EXC-006 — Entity or account with actuals but no budget

| Field | Value |
|---|---|
| **Family / version** | Master data hygiene / 1.0 |
| **Intent** | Catch the "orphan dimension" case: spend or revenue is being recorded where no budget exists, so no variance control is possible |
| **Severity** | **Medium** |
| **Owner role** | FP&A Analyst |
| **Depends on** | Budget loaded for the period |
| **Subject key** | `scope\|value` where scope ∈ {`entity`, `account`, `entity_account`} |
| **Logic** | For each loaded period, compute the set of (entity) and (entity × account) combinations with non-zero actuals. Compare with the budget coverage matrix. For each combination with actuals and **no budget line in any period of the fiscal year** → raise, with the YTD actual amount and the number of postings |
| **Thresholds** | `min_ytd_amount` = `max(absolute_floor, materiality_pct × |entity_ytd_actual|)` — defaulting to the global materiality (`CALC-080`); `scope_grain` = `entity_account` |
| **Tier** | `exact` |
| **Mitigation** | Ignores combinations with budget in *any* period of the year (a seasonal line is not an orphan). Accounts intentionally unbudgeted (e.g. some balance-sheet accounts) are excluded via an explicit "excluded from budget control" list in Settings — an explicit, versioned decision, not a blanket silencing |
| **Sample case** | Planting P6: entity `IN02` has ₹ 4,50,000.00 of YTD actuals across 3 accounts with no budget lines in FY26 (the entity was onboarded mid-year) |
| **Expected verdict** | **Raised** once for `entity\|IN02`, `Medium`, with the 3 accounts listed in the detail |
| **Registers on** | All orphan combinations' rows (capped sample; full set retrievable) |

### EXC-007 — Possible duplicate invoice

| Field | Value |
|---|---|
| **Family / version** | Duplicates / 1.0 |
| **Intent** | Detect a payment or expense that may have been recorded twice (the classic vendor-invoice duplicate) |
| **Severity** | **High** |
| **Owner role** | Accounts Payable |
| **Depends on** | Nothing (vendor + invoice number on the transaction); invoice numbers are often absent in payroll data, which simply yields no candidates for those rows |
| **Subject key** | `vendor_code\|invoice_no\|amount` (the invoice is the subject, not the row) |
| **Logic** | Group expense-side rows (debit with a vendor and a non-empty invoice number) by (`vendor_code`, normalised `invoice_no`, `amount`). If a group contains ≥2 rows whose posting dates differ by ≤ `date_window_days` → raise one exception for the group, listing every matching row with voucher, date and amount. Normalisation: trim, upper-case, strip leading zeros and non-alphanumeric separators |
| **Thresholds** | `date_window_days` = `90`; `min_amount` = `max(absolute_floor, materiality_pct × |account_budget|)`; `exact_amount_match` = `true` |
| **Tier** | `exact` |
| **Mitigation** | Requires an exact amount match and a strong normalised invoice number; the detail always shows every candidate row side by side so a reviewer can confirm or dismiss quickly. Partial-amount duplicates (e.g. staged payments) are deliberately **out of scope** for v1 to keep precision high — parked as a refinement (`BL-025`, recorded in `01_PRD.md` §6.2 and to be seeded into `27_BACKLOG.md`) |
| **Sample case** | Planting P7: vendor `V-00931` invoice `INV-88213` for ₹ 45,000.00 posted twice — voucher `VCH-2026-0912-004` on 14-Sep and voucher `VCH-2026-0918-011` on 18-Sep |
| **Expected verdict** | **Raised** once, `High`, `2 rows · ₹ 45,000.00`, both vouchers listed |
| **Registers on** | Both posting rows |

### EXC-008 — Possible duplicate voucher line

| Field | Value |
|---|---|
| **Family / version** | Duplicates / 1.0 |
| **Intent** | Catch the same voucher line posted twice (re-posted journal, double-keyed entry) even when no invoice number exists |
| **Severity** | **Medium** |
| **Owner role** | GL Accountant |
| **Depends on** | Nothing |
| **Subject key** | `company_code\|account_code\|amount\|posting_date\|cost_center_code` |
| **Logic** | Group rows by (company, account, absolute amount, posting date, cost centre, and net sign). A group with ≥2 rows **in different vouchers** → raise. Rows in the *same* voucher with the same values are treated as normal multi-line postings and are excluded |
| **Thresholds** | `min_amount` = `max(absolute_floor, materiality_pct × |account_budget|)`; `require_different_voucher` = `true` |
| **Tier** | `exact` |
| **Mitigation** | The "different voucher" requirement removes the largest class of false positives (split postings within one document). Identical recurring amounts (e.g. the same rent on the same day from two cost centres) are excluded by the cost-centre component of the key |
| **Sample case** | Planting P8: the same ₹ 12,500.00 debit to account `5300` on 22-Sep-2026 appears in vouchers `VCH-2026-0922-007` and `VCH-2026-0922-009` |
| **Expected verdict** | **Raised** once, `Medium`, `2 rows · ₹ 12,500.00` |
| **Registers on** | Both rows |

### EXC-009 — Posting date / fiscal period mismatch

| Field | Value |
|---|---|
| **Family / version** | Timing / 1.0 |
| **Intent** | Detect transactions whose source-declared fiscal period disagrees with the period implied by their posting date — a common ERP/export integrity problem and a misstatement risk |
| **Severity** | **High** |
| **Owner role** | GL Accountant |
| **Depends on** | The source file supplying a fiscal-period column (optional in the profile) |
| **Subject key** | `batch_id\|company_code\|period_mismatch_pair` |
| **Logic** | `CALC-002`: derive `period_id` from `posting_date`, then compare with the source-declared period resolved against `DimPeriod`. Any row where they differ → candidate. Group candidates by (batch, company, source period, derived period) and raise one exception per group with the row count and the net amount, listing the first N rows. Rows whose dates fall outside the calendar are handled by `IMP-019` (quarantine) and are not re-flagged here |
| **Thresholds** | `min_rows` = `1`; `min_amount` = `0.00` (a date/period disagreement is worth seeing even when small, because it signals a process failure, not an amount risk) |
| **Tier** | `exact` |
| **Mitigation** | Groups, not per-row exceptions, keep the register readable during a systematic export problem. The detail shows the calendar used for derivation, so the reviewer can see whether the source or the app is the odd one out. If the source format defines its fiscal period differently, the fix is a documented project setting or profile rule — never a silent suppression |
| **Sample case** | Planting P9: 9 rows in the October procurement file carry source period `FY26-P09` (September) but posting dates in October |
| **Expected verdict** | **Raised** once, `High`, `9 rows · ₹ 2,14,600.00`, source period `FY26-P09` vs derived `FY26-P10` |
| **Registers on** | The 9 rows |

### EXC-010 — Potential cut-off issue

| Field | Value |
|---|---|
| **Family / version** | Timing / 1.0 |
| **Intent** | Catch goods/services or documents from a prior period being posted in the current period close to the boundary — the classic cut-off misstatement |
| **Severity** | **High** |
| **Owner role** | GL Accountant |
| **Depends on** | `document_date` available on the transaction |
| **Subject key** | `company_code\|account_code\|vendor_code\|document_date` |
| **Logic** | For each expense-side row with a `document_date`: if `period(document_date) < period(posting_date)` **and** `posting_date ≥ period_end − cutoff_window_days` → candidate. Raise one exception per (company, account, vendor, document date) group, stating both dates, the day gap, and the amount. This is the **only** rule that uses `document_date` (`CALC-002`) |
| **Thresholds** | `cutoff_window_days` = `7` (the last week of the period); `min_amount` = `max(absolute_floor, materiality_pct × |account_budget|)`; `max_gap_days` = `90` (beyond this the item is more likely a genuine correction than a cut-off issue, and is reported separately in the detail rather than raised) |
| **Tier** | `exact` |
| **Mitigation** | The day-gap and materiality filters remove noise from genuinely late corrections; the detail names both dates so the reviewer sees the issue immediately. Where a valid business reason exists (goods received after period end), the closure note records it and the effectiveness dashboard learns the pattern per vendor/account |
| **Sample case** | Planting P10: vendor `V-00412`, document dated 29-Sep-2026 for ₹ 3,20,000.00, posted 05-Oct-2026 (6 days into October, and the document date is in the prior period) |
| **Expected verdict** | **Raised**, `High`, `document 29-Sep-2026 → posted 05-Oct-2026 (6 days)` |
| **Registers on** | The posting row |

### EXC-011 — Future-dated posting

| Field | Value |
|---|---|
| **Family / version** | Timing / 1.0 |
| **Intent** | Detect postings dated after the period under review — either mis-keyed dates or entries deliberately pushed into a future period |
| **Severity** | **Medium** |
| **Owner role** | GL Accountant |
| **Depends on** | Nothing |
| **Subject key** | `company_code\|voucher_no\|posting_date` |
| **Logic** | Compare each row's `posting_date` with the project's `as_of` date (the run date, injected — never a raw system clock inside the rule). `posting_date > as_of` → candidate, grouped by (company, voucher, posting date), raised with the day gap |
| **Thresholds** | `allow_days_ahead` = `0` (any future date is surfaced); `min_amount` = `0.00` |
| **Tier** | `exact` |
| **Mitigation** | Genuine forward-dated accruals exist, so severity is Medium and the detail shows the voucher and account. Rows dated within the **current open period** but after the run date are the common legitimate case and are ranked last in the detail; rows dated beyond the period end are ranked first |
| **Sample case** | Planting P11: voucher `VCH-2026-0930-021` posts ₹ 1,75,000.00 on 30-Nov-2026 while the period under review is FY26-P10 (October) with a run date of 12-Nov-2026 |
| **Expected verdict** | **Raised**, `Medium`, `posting 30-Nov-2026 · 18 days ahead of the run date` |
| **Registers on** | The posting row |

### EXC-012 — Unusual negative expense / credit

| Field | Value |
|---|---|
| **Family / version** | Anomaly — sign / 1.0 |
| **Intent** | Detect credits to expense accounts and other sign-reversed postings that are large enough to distort the period unless explained (correct provisions, reversals, reclassifications) |
| **Severity** | **Medium** |
| **Owner role** | Cost Centre Owner |
| **Depends on** | Nothing |
| **Subject key** | `company_code\|account_code\|cost_center_code\|period_id` |
| **Logic** | For expense-type accounts, sum credits (`net_amount < 0`) per (company, account, cost centre, period). If the **absolute credited total** exceeds the threshold **and** the credited total is not offset within the same period by debits on the same key equal or greater in magnitude (an ordinary netting), raise one exception per key with the credited total, the debit offset, and the net, listing the largest credit rows |
| **Thresholds** | `min_credit_amount` = `max(absolute_floor, materiality_pct × |account_budget|)`; `offset_ratio` = `0.90` (credits retain < 90% of their value after same-period same-key debits are netted off) |
| **Tier** | `exact` |
| **Mitigation** | The offset test removes the most common false positive (an accrual and its reversal inside the same period). The detail names the offsetting rows so a reviewer validates in one glance. Balance-sheet accounts are out of scope (credits there are normal) |
| **Sample case** | Planting P12: account `5400` / `CC-110` receives credits of ₹ 6,80,000.00 in FY26-P09 with only ₹ 1,20,000.00 of offsetting debits — a 17.6% offset |
| **Expected verdict** | **Raised**, `Medium`, `credits ₹ 6,80,000.00 · offset ₹ 1,20,000.00 · net credit ₹ 5,60,000.00` |
| **Registers on** | The largest credit rows on that key |

### EXC-013 — Out-of-pattern spike vs trailing average

| Field | Value |
|---|---|
| **Family / version** | Anomaly — magnitude / 1.0 |
| **Intent** | Surface a month that is wildly out of line with the recent run for the same account/cost centre, where the cause is usually a mis-posting, a duplicated accrual, or an unrecorded one-off |
| **Severity** | **Medium** |
| **Owner role** | Cost Centre Owner |
| **Depends on** | ≥ `baseline_periods` (default 3) loaded periods of actuals for the same key |
| **Subject key** | `company_code\|account_code\|cost_center_code\|period_id` |
| **Logic** | For each key with a full baseline: `baseline = mean(|net_amount|)` over the previous `baseline_periods` loaded periods (`CALC-062` arithmetic, absolute values so sign flips do not cancel). If `|current| ≥ spike_ratio × baseline` **and** `|current − baseline| ≥ min_deviation_amount` → raise, stating the current value, the baseline, the ratio and the baseline periods used. Zero-amount rows and accounts with fewer than the required baseline periods are excluded |
| **Thresholds** | `baseline_periods` = `3`; `spike_ratio` = `2.5`; `min_deviation_amount` = `max(absolute_floor, materiality_pct × |account_budget|)`; `exclude_accounts` = the "noisy accounts" list (§8.2) |
| **Tier** | `fuzzy` |
| **Mitigation** | Three independent filters (ratio, absolute deviation, noisy-account exclusion) plus a per-project exclusion list. The baseline uses **median-adjacent robustness**: if any baseline period is itself ≥ `spike_ratio` above the others, the baseline is recomputed excluding it and the detail says so — one prior anomaly cannot mask the next one. Tuning path: the register's "explain" and "not applicable" closures per account drive the noisy-account list on the effectiveness dashboard (§9) |
| **Sample case** | Planting P13: account `5600` / `CC-140` runs at ₹ 42,000–₹ 48,000 for FY26-P06…P08 and hits ₹ 1,86,000.00 in FY26-P09 (ratio 4.1×, deviation ₹ 1.41 lakh) |
| **Expected verdict** | **Raised**, `Medium`, `₹ 1,86,000.00 vs baseline ₹ 45,333.33 (4.1×)` |
| **Registers on** | The current-period rows for that key |

### EXC-014 — Unusual vendor → account combination

| Field | Value |
|---|---|
| **Family / version** | Anomaly — pairing / 1.0 |
| **Intent** | Detect spend posted to an account this vendor has never (or rarely) used — a frequent symptom of mis-keyed cost classification, or of a fraud pattern (familiar vendor, unfamiliar category) |
| **Severity** | **Medium** |
| **Owner role** | Accounts Payable |
| **Depends on** | Prior posted history for the same vendor (≥ `min_history_rows` across ≥ `min_history_periods`) |
| **Subject key** | `vendor_code\|account_code` |
| **Logic** | Build the historical vendor→account matrix from posted periods strictly **before** the period under review. For each new posting pair in the current period: if the pair was never seen before **and** the vendor has otherwise consistent behaviour (≥ `min_history_rows` postings across ≥ `min_history_periods` on ≤ `max_historical_accounts` distinct accounts) **and** the amount clears materiality → raise one exception per (vendor, account) with the historical account mix shown |
| **Thresholds** | `min_history_rows` = `3`; `min_history_periods` = `2`; `max_historical_accounts` = `3`; `min_amount` = `max(absolute_floor, materiality_pct × |account_budget|)`; `require_amount_materiality` = `true` |
| **Tier** | `fuzzy` |
| **Mitigation** | The "consistent vendor" precondition removes the largest false-positive class (vendors that legitimately bill many account types, e.g. a general contractor, a utility with multiple tariffs, a bank). The detail shows the vendor's own history so a reviewer can judge instantly. Tuning path: `max_historical_accounts` is editable, and repeated `not_applicable` closures for a vendor drive a per-vendor exception list |
| **Sample case** | Planting P14: vendor `V-00276` has 14 postings to account `5100` (Salaries) across FY26-P05…P08 and one ₹ 2,60,000.00 posting to account `5800` (Marketing) in FY26-P09 |
| **Expected verdict** | **Raised**, `Medium`, `new pair V-00276 → 5800 · ₹ 2,60,000.00` with the historical mix shown |
| **Registers on** | The single new-pair row |

### EXC-015 — Missing recurring cost

| Field | Value |
|---|---|
| **Family / version** | Completeness / 1.0 |
| **Intent** | Detect a known recurring charge that did not appear in the period — the classic "missed rent/insurance/subscription" understatement |
| **Severity** | **High** |
| **Owner role** | Accounts Payable |
| **Depends on** | **Required:** the recurring-cost list (`MasterRecurringCost`). Without it the rule is disabled with a notice |
| **Subject key** | `recurring_id\|period_id` |
| **Logic** | For each active recurring-cost entry whose schedule expects a charge in this period (respecting `frequency` and `start_period_id`/`end_period_id`), search the period's fact rows on the entry's (vendor, account, cost centre) for a charge whose amount is within `tolerance_pct` of `expected_amount`. No match → raise, showing the expected amount, the tolerance, the last period in which the charge **was** posted, and the closest candidate found (if any) with its difference |
| **Thresholds** | `tolerance_pct` = `10%` (default from the master record; editable per entry); `skip_if_period_missing` = `true` (a period with no loaded data never produces a missing-charge exception); `min_expected_amount` = `0.00` |
| **Tier** | `fuzzy` |
| **Mitigation** | The expected-amount tolerance absorbs price changes and part-month charges; the detail always shows the nearest candidate (e.g. an amount posted 12% lower) so the reviewer sees "it's there but different" rather than a bare absence. Partial-period charges are handled by the tolerance, not by guesswork. Tuning path: per-entry tolerance and deactivation of entries that are genuinely over |
| **Sample case** | Planting P15: `MasterRecurringCost` entry "Office rent — Andheri" expects ₹ 4,50,000.00 monthly from vendor `V-00118`; FY26-P09 has no posting to that vendor/account/cost-centre combination (the nearest candidate is ₹ 3,60,000.00 posted to a different cost centre) |
| **Expected verdict** | **Raised**, `High`, `expected ₹ 4,50,000.00 · last posted FY26-P08 · nearest ₹ 3,60,000.00 (20.0% below)` |
| **Registers on** | The master-data entry plus the nearest candidate rows (for evidence) |

### EXC-016 — Missing expected accrual

| Field | Value |
|---|---|
| **Family / version** | Completeness / 1.0 |
| **Intent** | Detect a month-end accrual that the entity's own history says should exist (a pattern learned from prior periods, not from a master list) — catching understatements where no recurring-cost entry exists |
| **Severity** | **Medium** |
| **Owner role** | GL Accountant |
| **Depends on** | ≥ `pattern_periods` (default 3) loaded prior periods for the same key, and `journal_category` where available |
| **Subject key** | `company_code\|account_code\|cost_center_code\|period_id` |
| **Logic** | For each (company, account, cost centre) with a **stable pre-close accrual pattern** — a credit posting in each of the last `pattern_periods` periods within the `accrual_post_window_days` window before period end, on an expense account, with period-to-period variation ≤ `stability_band` — flags the current period when no comparable posting exists in the same window. The exception states the pattern evidence (periods, amounts, dates) and the window searched |
| **Thresholds** | `pattern_periods` = `3`; `stability_band` = `25%` (max deviation from the mean); `accrual_post_window_days` = `5`; `min_amount` = `max(absolute_floor, materiality_pct × |account_budget|)` |
| **Tier** | `fuzzy` |
| **Mitigation** | The stability band ensures only genuinely regular accruals qualify, and the detail shows the historical evidence explicitly so the reviewer can confirm the pattern. If a pattern legitimately stopped, the account is added to the accrual-pattern exclusion list (**the tuning path**) rather than the rule being weakened |
| **Sample case** | Planting P16: account `6100` / `CC-120` has received ₹ 1,85,000.00 accruals on 27-Sep-2025, 28-Oct-2025 and 27-Nov-2025 in prior periods; FY26-P09 has no posting in the last 5 days of the period (loading periods FY26-P06…P09 provide the required history) |
| **Expected verdict** | **Raised**, `Medium`, with the three historical accruals listed as evidence |
| **Registers on** | The historical accrual rows (evidence) and the current period's account activity |

### EXC-017 — Material unbudgeted spend

| Field | Value |
|---|---|
| **Family / version** | Budget relationship / 1.0 |
| **Intent** | Detect material spend on accounts with **no budget at all** — spending that no plan authorised |
| **Severity** | **High** |
| **Owner role** | FP&A Analyst |
| **Depends on** | Budget loaded |
| **Subject key** | `company_code\|account_code\|cost_center_code\|period_id` |
| **Logic** | For each (company, account, cost centre, period) with actuals but **no budget line anywhere in the fiscal year**: if `|actual| ≥ materiality_amount` (`CALC-080`) → raise, stating the actual, the YTD actual, and the fact that no budget line exists for the year. Zero-budget variance % is `n/a` (`CALC-011` F4) and is never presented as `0%` or `inf` |
| **Thresholds** | `materiality_amount` = `max(500,000, 2% × |budget of the account's parent group|)` when a parent budget exists, otherwise the absolute floor; `scope` = `account × cost centre` |
| **Tier** | `fuzzy` (amount-based) |
| **Mitigation** | Uses the account's budget parent group as the materiality denominator where possible, so a small cost centre is judged against its real scale rather than the absolute floor alone. Accounts on the "not budget-controlled" exclusion list (e.g. some intercompany or clearing accounts) are excluded explicitly and by decision |
| **Sample case** | Planting P17: account `5450` / `CC-160` has ₹ 8,40,000.00 of FY26-P09 spend and no budget line in FY26 (a new project cost centre) |
| **Expected verdict** | **Raised**, `High`, `₹ 8,40,000.00 unbudgeted (no FY26 budget line)` |
| **Registers on** | The period's rows for that key |

### EXC-018 — Material variance (amount **and** %)

| Field | Value |
|---|---|
| **Family / version** | Budget relationship / 1.0 |
| **Intent** | The workhorse analysis rule: catch variances that are material in **both** absolute and relative terms, so the register is not flooded by large-but-expected or small-but-percentage-heavy lines |
| **Severity** | **High** |
| **Owner role** | FP&A Analyst |
| **Depends on** | Budget loaded |
| **Subject key** | `company_code\|account_code\|cost_center_code\|period_id` |
| **Logic** | `CALC-010`/`CALC-011`/`CALC-080`: compute `variance = actual − budget` and `variance_pct = variance / |budget|`. Raise when `|variance| ≥ max(absolute_floor, materiality_pct × |budget|)` **AND** `|variance_pct| ≥ pct_threshold`. The AND is mandatory (`CALC-080` F13). For ratio-type lines the amount test is replaced by the percentage-point test (`CALC-013`) |
| **Thresholds** | `materiality_pct` = `2%`; `absolute_floor` = `₹ 500,000`; `pct_threshold` = `5%`; `pp_threshold` = `1.0 pp` for ratio lines |
| **Tier** | `fuzzy` |
| **Mitigation** | The AND test is itself the primary mitigation (F13b and F13c are the canonical "should not raise" cases). Severity can be tiered per project (e.g. High above ₹20 lakh, Medium below) without changing the logic. Known-expected variances (e.g. a planned marketing push) are handled by **explaining and closing** with a note, which feeds the effectiveness dashboard — not by suppressing the rule |
| **Sample case** | Planting P18: account `5200` / `CC-100`, FY26-P09 actual `10,540,000.00` vs budget `10,000,000.00` → variance `+540,000.00`, `+5.4%`, threshold `max(500,000, 2%×10,000,000) = 500,000` → **raised** (canonical case F13a) |
| **Expected verdict** | **Raised**, `High`, `+540,000.00 (+5.4%)`, `effective_threshold = materiality 2.0% or ₹500,000; AND pct 5.0%` |
| **Registers on** | The period's rows for that key |

### EXC-019 — Cumulative overrun vs annual budget

| Field | Value |
|---|---|
| **Family / version** | Budget relationship / 1.0 |
| **Intent** | Detect a line that is still inside its monthly budget but has already exceeded its share of the **annual** budget — the overrun that only becomes visible too late |
| **Severity** | **Medium** |
| **Owner role** | FP&A Analyst |
| **Depends on** | Budget loaded with annual coverage |
| **Subject key** | `company_code\|account_code\|cost_center_code` (the year is implied by the period) |
| **Logic** | For each key: `ytd_actual` (`CALC-004`) vs `ytd_budget`. Raise when `ytd_actual > ytd_budget × (1 + ytd_tolerance_pct)` **and** `ytd_actual ≥ annual_budget × annual_consumption_pct` **and** the amount exceeds the floor. The exception states the YTD position, the annual budget, the consumption percentage, and the implied full-year outcome at the current run rate |
| **Thresholds** | `ytd_tolerance_pct` = `5%`; `annual_consumption_pct` = `80%`; `amount_floor` = `max(absolute_floor, materiality_pct × annual_budget)` |
| **Tier** | `fuzzy` |
| **Mitigation** | The 80% consumption gate prevents mid-year noise (a line can be 6% over in month 2 and still trivially recoverable), and the YTD tolerance absorbs normal phasing. Seasonal lines are the main false-positive class: the app's forecast view shows the phasing, and a repeated `not_applicable` closure for a key adds it to the seasonality watch list shown on the dashboard |
| **Sample case** | Planting P19: account `5500` / `CC-130` has YTD actual `9,60,000.00` vs YTD budget `8,40,000.00` (14.3% over) with 88% of the annual budget `10,90,000.00` consumed by FY26-P09 |
| **Expected verdict** | **Raised**, `Medium`, `YTD +₹ 1,20,000.00 (+14.3%) · 88% of annual budget consumed by P09` |
| **Registers on** | The YTD rows for that key |

### EXC-020 — Budget coverage gap

| Field | Value |
|---|---|
| **Family / version** | Budget relationship / 1.0 |
| **Intent** | Make the **shape** of the budget visible: entity × account × period cells with no budget line, so a variance report is never silently incomplete |
| **Severity** | **Medium** |
| **Owner role** | FP&A Analyst |
| **Depends on** | Budget loaded |
| **Subject key** | `entity_account_pair` |
| **Logic** | Compute the coverage matrix over (entity × account) for the open periods of the fiscal year (`IMP-031`). For each pair with **partial** coverage (budget in some periods but not all) or **no** coverage while actuals exist, raise one exception per pair, stating the missing periods and the coverage percentage |
| **Thresholds** | `min_coverage_gap_periods` = `1`; `include_no_actuals_pairs` = `false` (budget gaps where nothing is spent are informational and are shown on the Check screen instead) |
| **Tier** | `exact` |
| **Mitigation** | It flags the **budget artefact**, not the spend, so closing it means fixing the budget or recording an explicit decision that the pair is intentionally unbudgeted. The Check screen shows the full coverage percentage so the reviewer sees scale, not just instances |
| **Sample case** | Planting P20: account `5450` has budget lines for FY26-P01…P06 but none for P07…P09, while actuals exist for all three months |
| **Expected verdict** | **Raised** once for the pair, `Medium`, `coverage 67% · missing FY26-P07, P08, P09` |
| **Registers on** | The budget matrix for the pair |

### EXC-021 — Amount crossing the approval threshold

| Field | Value |
|---|---|
| **Family / version** | Controls / 1.0 |
| **Intent** | Detect expense commitments at or above the level that requires a documented approval, so the approval can be evidenced — a **control** rule, not an error rule |
| **Severity** | **High** |
| **Owner role** | Controller |
| **Depends on** | **Required:** approval thresholds (`MasterApprovalThreshold`). Without them the rule is disabled with a notice |
| **Subject key** | `company_code\|voucher_no\|threshold_id` |
| **Logic** | Resolve the effective threshold for each row's (company, account, cost centre) by scope priority (`cost_center` > `account` > `company`), respecting `effective_from`. For expense-side rows with `|net_amount| ≥ threshold_amount` → raise one exception per (voucher, threshold). The exception states the threshold, its scope, whether dual approval is required, and the voucher's other lines (so the reviewer sees the whole document, not one line) |
| **Thresholds** | From `MasterApprovalThreshold`, seeded with two defaults: ₹ 5,00,000 (single approval) and ₹ 25,00,000 (dual approval) at company scope |
| **Tier** | `exact` |
| **Mitigation** | It is a control, so volume is acceptable — but grouped at voucher level, not per line, and the register can be filtered or exported by owner in one action (`FR-EXC-017`) so the control is discharged efficiently. Vouchers already closed as approved in a prior period stay closed across re-runs |
| **Sample case** | Planting P21: voucher `VCH-2026-0925-003` posts ₹ 27,50,000.00 to account `5450`, above the ₹ 25,00,000 dual-approval threshold, with no recorded approval evidence |
| **Expected verdict** | **Raised**, `High`, `₹ 27,50,000.00 ≥ ₹ 25,00,000 (company scope · dual approval required)` |
| **Registers on** | All lines of the voucher |

### EXC-022 — Round-number manual journal

| Field | Value |
|---|---|
| **Family / version** | Controls / 1.0 |
| **Intent** | Surface large, suspiciously round manual journals — a long-standing review indicator for top-side adjustments, estimates and plug entries |
| **Severity** | **Low** |
| **Owner role** | GL Accountant |
| **Depends on** | `journal_category` (optional — see degradation), ≥ `history_periods` loaded periods for the round-number baseline |
| **Subject key** | `company_code\|voucher_no` |
| **Logic** | Candidates: rows whose `journal_category = manual` (or, when the column is absent, all rows — with an explicit degradation notice) **and** whose `|net_amount|` is an exact multiple of `round_unit` (default ₹ 10,000) **and** `|net_amount| ≥ round_floor`. Raise one exception per voucher when the voucher's total meets the same test **and** the amount exceeds `mean_round_journal_amount × multiple` for that entity (a round number that is normal for the entity is not flagged) |
| **Thresholds** | `round_unit` = `10,000`; `round_floor` = `₹ 500,000`; `multiple` = `1.5`; `history_periods` = `3` |
| **Tier** | `fuzzy` |
| **Mitigation** | Low severity plus two conditions (round **and** larger than the entity's normal round journal) keep volume down. The detail names the exact round multiple and the historical comparison. Tuning path: entity-level `round_unit` adjustment and the exclusion of known estimation accounts (e.g. provisions) |
| **Sample case** | Planting P22: top-side voucher `VCH-2026-0929-014` records exactly ₹ 15,00,000.00 (150 × ₹10,000) against account `6300` with `journal_category = manual`, while the entity's mean round journal is ₹ 4,20,000.00 (a 3.6× multiple) |
| **Expected verdict** | **Raised**, `Low`, `₹ 15,00,000.00 (round ₹10,000 ×150) · 3.6× the entity average` |
| **Registers on** | The voucher's lines |

### EXC-023 — Voucher-level imbalance

| Field | Value |
|---|---|
| **Family / version** | Controls / 1.0 |
| **Intent** | Detect a voucher whose own lines do not balance — a sign of a partial or truncated posting that a file-level balance check cannot see (the file balances because another voucher compensates) |
| **Severity** | **High** |
| **Owner role** | GL Accountant |
| **Depends on** | Voucher completeness in the source export (all lines of each voucher present in the file) |
| **Subject key** | `company_code\|voucher_no` |
| **Logic** | Group rows by (company, voucher), sum `debit` and `credit`, and compare at minor-unit precision. Any voucher whose sums differ beyond the configured tolerance → raise, stating the imbalance, the line count, and the individual lines |
| **Thresholds** | `voucher_tolerance` = `0.00`; `min_lines` = `2` (a single-line "voucher" is a data-shape issue, reported by the import checks instead) |
| **Tier** | `exact` |
| **Mitigation** | The `min_lines` guard avoids firing on exports that omit balancing lines by design; if the export shape legitimately carries partial vouchers (e.g. paginated extraction), the profile documents it and the rule disables itself for that source type with a notice — an explicit decision, not a silent skip |
| **Sample case** | Planting P23: voucher `VCH-2026-0912-004` has lines totalling debits `45,000.00` and credits `40,000.00` (a truncated credit line) |
| **Expected verdict** | **Raised**, `High`, `debits ₹ 45,000.00 vs credits ₹ 40,000.00 · difference ₹ 5,000.00 · 2 lines` |
| **Registers on** | The voucher's lines |

### EXC-024 — Suspense / clearing account residual

| Field | Value |
|---|---|
| **Family / version** | Controls / 1.0 |
| **Intent** | Month-end hygiene: suspense, clearing and goods-received-not-invoiced accounts should be near zero at close; a residual balance means something is unresolved |
| **Severity** | **High** |
| **Owner role** | Controller |
| **Depends on** | Accounts tagged as suspense/clearing — **required**; the tag is a master-data flag on `DimAccount` (`account_tag = suspense` \| `clearing`). Without any tagged account the rule is disabled with a notice |
| **Subject key** | `company_code\|account_code\|period_id` |
| **Logic** | For each tagged account and period, compute the period's closing residual (cumulative balance through the period end, per `CALC-004` window arithmetic) and the period's activity. Raise when `|residual| ≥ residual_threshold` **or** `|activity| ≥ movement_threshold` while the residual remains non-zero — i.e. either a large stale balance or a balance that moved without clearing |
| **Thresholds** | `residual_threshold` = `max(absolute_floor, materiality_pct × |account_annual_budget|)`; `movement_threshold` = `residual_threshold × 0.5`; `ignore_sign` = `true` (both debit and credit residuals matter) |
| **Tier** | `exact` |
| **Mitigation** | The account tag is an explicit, versioned master-data decision, so untagged accounts never fire; the "moved without clearing" condition targets genuine unresolved balances rather than normal in-period flow. Where a residual is expected (e.g. a standing prepayment account), the closure note records it and the tag can be refined |
| **Sample case** | Planting P24: account `1999` (tagged `suspense`) shows a closing residual of ₹ 12,40,000.00 at FY26-P09 and a period movement of ₹ 9,80,000.00 that did not clear |
| **Expected verdict** | **Raised**, `High`, `residual ₹ 12,40,000.00 · movement ₹ 9,80,000.00 (not cleared)` |
| **Registers on** | The period's rows for the tagged account |

## 5. Rule → dependency matrix (what disabling what, and why)

| Rule | Recurring-cost list | Approval thresholds | Vendor categories | Suspense tagging | Budget | Prior periods | `journal_category` | Control totals |
|---|---|---|---|---|---|---|---|---|
| `EXC-001` | | | | | | | | |
| `EXC-002` | | | | | | ✓ (≥2 batches) | | |
| `EXC-003` | | | | | | | | **required** |
| `EXC-004` | | | | | | | | |
| `EXC-005` | | | | | | | | |
| `EXC-006` | | | | | **required** | | | |
| `EXC-007` | | | | | | | | |
| `EXC-008` | | | | | | | | |
| `EXC-009` | | | | | | | | |
| `EXC-010` | | | | | | | | |
| `EXC-011` | | | | | | | | |
| `EXC-012` | | | | | | | | |
| `EXC-013` | | | | | | ✓ (≥3) | | |
| `EXC-014` | | | optional | | | ✓ | | |
| `EXC-015` | **required** | | | | | | | |
| `EXC-016` | | | | | | ✓ (≥3) | optional | |
| `EXC-017` | | | | | **required** | | | |
| `EXC-018` | | | | | **required** | | | |
| `EXC-019` | | | | | **required** | ✓ (YTD) | | |
| `EXC-020` | | | | | **required** | | | |
| `EXC-021` | | **required** | | | | | | |
| `EXC-022` | | | | | | ✓ (≥3) | optional | |
| `EXC-023` | | | | | | | | |
| `EXC-024` | | | | **required** | | | | |

**Reading the matrix:** a rule with a blank row has no external dependency and always runs.
"optional" means the rule runs better with the input and states its degraded mode in the exception detail
(§2.9). "required" means the rule disables itself with a notice when the input is absent.

## 6. Enablement defaults per project type

| Project type | Enabled by default | Disabled by default (with notice) |
|---|---|---|
| **Sample project** | All 24 | none — the sample dataset is built to exercise every rule |
| **New client project (first period)** | `EXC-001`…`EXC-012`, `EXC-015`, `EXC-017`, `EXC-018`, `EXC-021`, `EXC-023`, `EXC-024` | History-dependent rules (`EXC-013`, `EXC-014`, `EXC-016`, `EXC-019`, `EXC-022`) auto-disable until enough periods are loaded; `EXC-003` disables per batch when no control totals exist; `EXC-020` disables without a budget |
| **Established client project** | All 24 | none |
| **Any project where a required master table is empty** | — | the dependent rule with the specific notice (§2.9) |

**Rule:** a disabled rule is always listed in the run summary with its reason and a link to the screen
that fixes it. A rule is never silently absent.

## 7. Planted sample dataset plan (40 plantings → `expected_exceptions.csv`)

The sample generator (`sample-data/`) plants exactly these cases. The answer key
`sample-data/expected_exceptions.csv` carries: `planting_id, rule_id, expected_verdict, subject_key,
severity, amount, period, notes`. Doc `14` maps each row to a test (`TST-nnn`); the acceptance test
asserts the engine finds at least the expected set, and every unexpected finding must be justified in the
false-positive log (`14`).

### 7.1 Expected raises — 32 plantings

| Planting | Rule | Count | Severity | Planted case |
|---|---|---|---|---|
| `P1` | `EXC-001` | 1 | High | Unbalanced bank-ledger file loaded under a ₹500 tolerance (variance ₹350.00) |
| `P2` | `EXC-002` | 3 | High | Re-export overlaps batch 37 on 3 voucher lines |
| `P3` | `EXC-003` | 1 | High | Control-total variance ₹350.00 |
| `P4` | `EXC-004` | **2** | Medium | (a) 6 rows post to `5999-TEMP`; (b) a dimension value `CC-999` appears in 2 rows with no cost-centre master record |
| `P5` | `EXC-005` | 1 | Low | `CC-950` (inactive since P06) receives 4 postings |
| `P6` | `EXC-006` | 1 | Medium | Entity `IN02` has ₹4,50,000.00 YTD actuals and no FY26 budget |
| `P7` | `EXC-007` | **2** | High | (a) `INV-88213` posted twice for ₹45,000.00; (b) `INV-91004` posted twice for ₹78,500.00 |
| `P8` | `EXC-008` | 1 | Medium | Same ₹12,500.00 debit in two different vouchers |
| `P9` | `EXC-009` | 1 | High | 9 October-dated rows declare source period `FY26-P09` |
| `P10` | `EXC-010` | **2** | High | (a) document 29-Sep posted 05-Oct (₹3,20,000.00); (b) document 28-Sep posted 03-Oct (₹1,45,000.00) |
| `P11` | `EXC-011` | 1 | Medium | Posting 18 days ahead of the run date |
| `P12` | `EXC-012` | 1 | Medium | Expense credits ₹6,80,000.00 offset only ₹1,20,000.00 |
| `P13` | `EXC-013` | **2** | Medium | (a) `5600/CC-140` at 4.1× baseline; (b) `6300/CC-120` at 3.2× baseline |
| `P14` | `EXC-014` | 1 | Medium | Consistent vendor `V-00276` posts to a never-used account |
| `P15` | `EXC-015` | **2** | High | (a) office rent ₹4,50,000.00 missing; (b) software subscription ₹1,25,000.00 missing |
| `P16` | `EXC-016` | 1 | Medium | Monthly accrual pattern on `6100/CC-120` absent |
| `P17` | `EXC-017` | 1 | High | New cost centre `CC-160` spends ₹8,40,000.00 with no budget line |
| `P18` | `EXC-018` | 1 | High | Canonical case F13a (`+540,000.00`, `+5.4%`) |
| `P19` | `EXC-019` | 1 | Medium | `5500/CC-130` at 88% annual consumption, YTD +14.3% |
| `P20` | `EXC-020` | 1 | Medium | Pair coverage 67% (missing P07–P09) |
| `P21` | `EXC-021` | 2 | High | One voucher above the ₹5,00,000 single threshold; one above the ₹25,00,000 dual threshold |
| `P22` | `EXC-022` | 1 | Low | Round ₹15,00,000 manual journal at 3.6× the entity average |
| `P23` | `EXC-023` | 1 | High | Voucher imbalance ₹5,000.00 (truncated credit line) |
| `P24` | `EXC-024` | 1 | High | Suspense residual ₹12,40,000.00 with ₹9,80,000.00 unsettled movement |
| | **Total raises** | **32** | | 18 High · 12 Medium · 2 Low |

### 7.2 Expected non-raises — 8 precision controls (must **not** raise)

| Planting | Rule | Planted near-miss | Why it must not raise |
|---|---|---|---|
| `P25` | `EXC-007` | A legitimate second invoice from the same vendor for a similar amount | Different normalised invoice number |
| `P26` | `EXC-008` | A multi-line posting inside one voucher with repeated amounts | `require_different_voucher = true` |
| `P27` | `EXC-012` | An accrual and its reversal inside the same period on one key | Same-period same-key offset exceeds the `offset_ratio` |
| `P28` | `EXC-013` | A 1.4× variation against the trailing average | Below `spike_ratio = 2.5` |
| `P29` | `EXC-018` | F13b: variance above the % test but below the absolute floor | The mandatory AND test fails |
| `P30` | `EXC-018` | F13c: variance above the floor but below the % test | The mandatory AND test fails |
| `P31` | `EXC-021` | A voucher of ₹4,99,999.00 against a ₹5,00,000.00 threshold | Below the resolved threshold |
| `P32` | `EXC-015` | The recurring charge posted 8% below the expected amount | Within `tolerance_pct = 10%` |

### 7.3 Tally

| Category | Count |
|---|---|
| Expected raises (`P1`–`P24`) | **32** |
| Expected non-raises (`P25`–`P32`) | **8** |
| **Total plantings in `expected_exceptions.csv`** | **40** |

Severity mix of the 32 raises: **18 High · 12 Medium · 2 Low** — deliberately weighted so the register
demonstrates severity filtering rather than being uniformly alarming.

Each `expected_exceptions.csv` row carries: `planting_id, rule_id, expected_verdict, subject_key,
severity, amount, period, notes`. Doc `14` maps every row to a `TST-nnn`; the acceptance test asserts the
engine finds **at least** the expected raise set (recall ≥ 90% per §8.3) **and raises none** of the eight
precision controls.

**Sample-data integrity (Addon 4 §H):** the sample project is flagged `project_type = sample`, carries a
"SAMPLE DATA" banner in-app and a watermark on every generated artefact, refuses client imports
(`FR-IMP-031`), and is excluded from every client deliverable (verified at the go-live checklist).

## 8. False-positive management

### 8.1 The mitigation contract

Every `fuzzy` rule (§2.7) must provide all three of:

1. **A precision filter** stated in its thresholds (e.g. `EXC-014`'s consistent-vendor precondition,
   `EXC-018`'s AND test, `EXC-013`'s three-way filter).
2. **Visible evidence in the exception detail**, so a reviewer can dismiss or confirm in seconds without
   leaving the register — the exception always shows *why it was raised*, never just *that it was*.
3. **A tuning path** — a documented, versioned way to suppress the specific known-benign case (an
   exclusion list entry, a per-entry tolerance, a threshold change) rather than disabling the control.

### 8.2 Suppression mechanisms (in order of preference)

| Mechanism | Use when | Audit |
|---|---|---|
| Close with an explanatory note | A specific instance is expected | Per-exception event; feeds effectiveness statistics |
| Master-data correction | The underlying data is wrong (e.g. reactivate a cost centre, add a recurring-cost entry) | `VersionHistory` entry with old→new |
| Exclusion list entry | A whole class is known-benign and permanent (e.g. a specific account is never budget-controlled) | Versioned, dated, with a mandatory reason, shown to the reviewer |
| Threshold tuning | The rule is directionally right but calibrated wrong for this client | Versioned; the previous value is retained; the effectiveness dashboard shows the impact |
| Disabling the rule | Only with a recorded decision and rationale (a project-level setting, versioned) | Appears in Settings history and in the run summary's disabled-rules list |

**Prohibited:** deleting or editing `expected_exceptions.csv`, golden outputs, or a rule's planted case to
make a test pass (Addon 1 §M.5). If expectations change, the spec changes first, with a `CHANGELOG` entry.

### 8.3 Precision targets

| Metric | Target | Where measured |
|---|---|---|
| Planted-exception recall | **≥ 90%** of expected raises found (`NFR` acceptance) | Acceptance test in `14` |
| False positives on the control plantings | **0** of the 8 expected non-raises may be raised | Acceptance test in `14` |
| Unexplained raises | Every additional finding must be justified in the false-positive log; a rule exceeding 3 unexplained findings on the sample dataset is tuned or documented before the phase gate | `14` + `SESSION_LOG` |

## 9. Rule effectiveness analytics

Per rule, computed from `FactExceptionEvent` history and surfaced on the tuning dashboard (`FR-EXC-015`):

| Metric | Definition | Use |
|---|---|---|
| Times raised | Count of distinct identities ever raised | Volume calibration |
| Explained / corrected share | Closures of type `explained` or `corrected` ÷ total closures | **Signal that the rule finds real issues** |
| `not_applicable` share | Closures of type `not_applicable` ÷ total closures | **Signal of false positives** |
| Average days to close | Mean `closed_at − raised_at` | Owner workload and SLA health |
| Aging profile | Open exceptions by bucket (§2.5) | Escalation input |
| Repeat rate | Share of subjects raised, closed, then flagged again | Data-quality trend |
| Last threshold tuning | Date and old→new of the most recent threshold change | Governance trail |

**Review trigger:** a rule with `not_applicable` share above `explained + corrected` share for two
consecutive periods is flagged **"review recommended"** on the dashboard with the specific tuning path
named (an exclusion list, a threshold, or a decision to disable). The engine improves month over month
through configuration — **never** through hidden code changes.

## 10. Change control for rules

1. **A logic change is a spec change.** Update this document → `CHANGELOG` → fixtures → tests → code.
2. **Rule versioning:** a logic change bumps the rule's version; existing exceptions keep the version
   that raised them (shown in the detail), so history stays explainable.
3. **A new rule** requires: a row in §3, a full §4 specification, a planting in §7 and a golden test —
   without all four it cannot be registered in `DimRule` and cannot run (§2.12).
4. **A removed rule** is not deleted from history: it is disabled, tombstoned in §3, and its exceptions
   remain readable with a note that the rule is retired.
5. **Threshold defaults** in this document are the shipped defaults; changes require a documented reason
   here, not merely a settings edit in one project.
6. **AI may never** create, modify, enable, disable, raise or close a rule or an exception
   (`FR-EXC-003`); AI's only permitted relationship with exceptions is summarising and grouping them for
   a human reader, with the numbers supplied by the engine (`10`).



