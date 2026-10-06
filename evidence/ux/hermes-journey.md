# FP&A Analyst Month-End Journey Audit: Hour-by-Hour Workflow & Spec Alignment

> **Document Author:** `hermes` (Analyst's Advocate)  
> **Task Reference:** `UX-01` (P1)  
> **Target Evidence Path:** `evidence/ux/hermes-journey.md`  
> **Governing Specs:** `docs/01_PRD.md`, `docs/02_FUNCTIONAL_SPEC.md`, `docs/05_CALCULATION_SPEC.md`, `docs/06_EXCEPTION_RULES_CATALOG.md`, `docs/07_FORECAST_METHODS_SPEC.md`, `docs/08_UI_UX_SPEC.md`, `docs/10_AI_INTEGRATION_SPEC.md`, `docs/11_EXCEL_OUTPUT_SPEC.md`, `docs/12_POWERPOINT_OUTPUT_SPEC.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

The FP&A Month-End Copilot is built to serve a single core Job To Be Done (JTBD): **to turn a monthly pile of ERP exports into a reviewed, explained, board-ready management pack in hours rather than days, without requiring technical expertise** (`01` §4.1).

This document audits the complete 12-hour month-end close journey of an FP&A Analyst / Finance Manager walking through the product step-by-step. Each hour is mapped directly to the governing functional requirements (`02`), calculation formulas (`05`), exception rules (`06`), screen designs (`08`), and presentation deliverables (`11`/`12`).

---

## Section 1: The 12-Hour Month-End Close Walkthrough

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                FP&A MONTH-END CLOSE JOURNEY (12 HOURS)                           │
├───────────────────┬───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│  Hours 01–02      │  Hours 03–04      │  Hours 05–06      │  Hours 07–08      │ Hours 09–12     │
│  Initialization   │  Multi-Source     │  Validation &     │  Variance &       │ Forecast, Deck  │
│  & Pre-Close      │  Import           │  Quality Check    │  Exceptions       │ & Period Lock   │
│  (SCR-001, 004)   │  (SCR-005..013)   │  (SCR-014, 012)   │  (SCR-015..026)   │ (SCR-027..031)  │
└───────────────────┴───────────────────┴───────────────────┴───────────────────┴─────────────────┘
```

---

### Hours 01–02: Period Initialization, Prior Configuration & Master Data Setup

* **Analyst Goal:** Open the new month close (`FY26-P09` / September 2026), ensure past mappings and rules carry forward cleanly, verify master data (vendor categories, recurring cost rules, approval thresholds), and confirm budget baseline availability.
* **Primary Screens:** `SCR-001` (Home), `SCR-004` (New Period Wizard), `SCR-034` (Master Data Settings).

#### Workflow Walkthrough & Step-by-Step Experience
1. **Launch & Context:** The analyst opens the application. `FR-ONB-006` reopens the last project automatically. The top status bar indicates the prior closed month (`FY26-P08`).
2. **Period Creation (`FR-PRJ-004`):** Click "Start September Close". `SCR-004` (New Period Wizard) presents expected source feeds (GL actuals, payroll sub-ledger, bank transactions, budget).
3. **Carry-Forward Assurance (`02` §FR-PRJ-004):** Mappings, exception thresholds, master data rules, and account hierarchies carry forward from `FY26-P08`. **Financial figures never carry forward.**
4. **Master Data Verification (`SCR-034` / `FR-SET-003`):** The analyst checks vendor categories and materiality thresholds (`FR-EXC-013`).

#### Friction Points & Spec Violations
* **Friction 1.1 (Out-of-Order Warning UX):** If an analyst attempts to open P09 when P08 is unclosed, `SCR-004` warns, but the confirmation dialog must clearly state that prior period numbers will lock upon progression (`FR-PRJ-005`).
* **Friction 1.2 (Missing Budget Handling):** When starting a period without a pre-loaded budget, `FR-PRJ-004` permits continuation but must explicitly suppress variance exception rules with an informative notice (`02` §16 matrix).

#### Governing Clauses
* `02` FR-PRJ-001 (Home), FR-PRJ-004 (New Period Wizard), FR-SET-003 (Master Data).
* `08` §4 (SCR-001, SCR-004, SCR-034).
* `05` §2.1 (Fiscal Calendar CALC-001).

---

### Hours 03–04: Multi-Source Data Ingestion & Batch Reconciliation

* **Analyst Goal:** Ingest raw ERP GL actuals (`d365_gl_actuals.csv`), sub-ledger files (payroll, bank statements), budget updates, and control total files without data corruption or silent truncation.
* **Primary Screens:** `SCR-005` (Import - File Select), `SCR-007` (Header & Sheet), `SCR-008` (Column Mapper), `SCR-009` (Validate), `SCR-010` (Commit), `SCR-013` (Quarantine Review).

#### Workflow Walkthrough & Step-by-Step Experience
1. **Drag-and-Drop Ingestion (`SCR-005`):** Drag `d365_gl_actuals.csv` (250,000+ rows) into `SCR-005`. Auto-profiling (`FR-IMP-004`) matches column headers (`posting_date`, `account_code`, `debit`, `credit`, `net_amount`, `cost_center`).
2. **Pre-Scan & Boundary Validation (`SCR-006` / `SCR-009`):** High-speed DuckDB batched multi-row bulk insert (`DEF-030` engine fix) ingests 250k rows in <75 seconds.
3. **Atomic Commit & Reconciled Gate (`FR-IMP-023` / `04` §12):** The batch evaluates trial balance integrity: `Σ(debit) − Σ(credit) = 0.00`.
4. **Quarantine Triage (`SCR-013` / `FR-IMP-013`):** Malformed rows (unparseable dates, invalid period ranges) land in Quarantine rather than crashing the job.

#### Friction Points & Spec Violations
* **Friction 2.1 (`OQ-025` / `DEC-056` Sub-Ledger Balance Gate):** Sub-ledger feeds (Bank, Payroll) are amount-style transactions without dual debit/credit balancing legs. Under early builds, `IMP-023` enforced an unconditional `debit=credit` balance on sub-ledgers, causing 100% of sub-ledger rows to be rejected (0 of 499 rows landed). `DEC-056` scopes the balance gate by source type: journal sources (`actuals_d365`, budget) keep exact `debit=credit`, while amount-style sub-ledgers use net reconciliation with a ₹500 tolerance.
* **Friction 2.2 (Multi-File Queuing Visibility):** Ingesting 4 separate files sequentially causes UI context switching. `SCR-005` requires a batch queue panel showing real-time background ingestion status (`FR-IMP-030`).

#### Governing Clauses
* `02` FR-IMP-001…031 (Import & Validation Family).
* `04` §12 (Batch Commit & Quarantine Mechanics), §17 (Validation Report).
* `05` CALC-007 (Canonical Sign Conventions: `net_amount = debit − credit`).
* `08` §5–§6 (SCR-005 through SCR-013).

---

### Hours 05–06: Data Integrity Validation & Quality Scoring

* **Analyst Goal:** Review batch health on `SCR-014` (Check Screen), verify the overall Data Quality Score (0–100), and evaluate control rules (`EXC-001` Control Totals, `EXC-002` Overlapping Batches, `EXC-003` Balance Tie-Out).
* **Primary Screens:** `SCR-014` (Check Screen), `SCR-012` (Batch Validation Report).

#### Workflow Walkthrough & Step-by-Step Experience
1. **Check Dashboard (`SCR-014`):** View the 100-point Data Quality Score. High score (e.g. 95/100) indicates strong structural integrity.
2. **Control Rule Evaluation (`EXC-001`..`EXC-003`):**
   * `EXC-001`: Checks declared control totals against imported row sums.
   * `EXC-002`: Checks for duplicate/overlapping batch imports.
   * `EXC-003`: Verifies general ledger trial balance tie-out.
3. **Validation Report Audit (`SCR-012`):** Download/view the 9-part validation report (`04` §17) detailing passed rules, quarantine counts, and warnings.

#### Friction Points & Spec Violations
* **Friction 3.1 (Key-Format Mismatches in Exceptions — `OQ-026` / `DEC-057`):** Mismatches between planted anomaly subject keys (e.g. `P20`, `P21`, `P24`) and catalog subject key formats suppressed rule findings or generated false-positive extras (`OQ-026`). `DEC-057` established that the catalog `06` wins subject keys and answer keys are re-keyed to `06`.
* **Friction 3.2 (Actionable Resolution Links):** When a check fails on `SCR-014`, the analyst must be able to click directly into the offender list or raw transaction drill-through (`SCR-021`) in a single click (`FR-PRJ-001`).

#### Governing Clauses
* `02` FR-EXC-001 (Control Checks), FR-EXC-014 (Data Quality Score), FR-EXC-020 (Coverage).
* `06` §3 (Rules EXC-001, EXC-002, EXC-003).
* `08` §7 (SCR-014 Layout & State Matrix).

---

### Hours 07–08: Variance Analysis, Anomaly Investigation & Triage

* **Analyst Goal:** Perform deep-dive Budget vs Actual (BvA) analysis, inspect the Bridge waterfall chart, analyze Top-N variance drivers, triage automated financial exceptions, and assign ownership.
* **Primary Screens:** `SCR-015` (BvA Matrix), `SCR-016` (Bridge Waterfall), `SCR-018` (Top-N Variances), `SCR-023` (Exceptions Register), `SCR-024` (Exception Detail).

#### Workflow Walkthrough & Step-by-Step Experience
1. **BvA Grid Exploration (`SCR-015`):** Analyze Actual vs Budget at Account, Cost Center, and Entity level across MTD, YTD, PY MTD, and TTM windows (`CALC-003`..`CALC-006`).
2. **Favourability Assessment (`CALC-012`):**
   * **Revenue Line:** `Actual > Budget` $\rightarrow$ Favourable (Green / ▲).
   * **Expense Line:** `Actual > Budget` $\rightarrow$ Unfavourable (Red / ▼).
   * **Balance Sheet Line:** Neutral (no colour, neutral indicator).
3. **Bridge Waterfall Inspection (`SCR-016`):** Walk opening to closing balance. Drivers sum up to variance. Any unexplained residual is explicitly categorized as `Other (unexplained)` step (`DEF-018` bridge fix).
4. **Percentage Point Compliance (`CALC-013`):** Ratio variances (e.g. Gross Margin %) are strictly displayed as percentage points (`+1.5 pp`), never as relative percentages (`+3.9%`).
5. **Exception Triage (`SCR-023` / `SCR-024`):** Review exception register (`EXC-004`..`EXC-020`). Filter by severity (High, Medium, Low), assign status (`Open`, `Under Review`, `Explained`, `Closed`), attach explanatory notes.

#### Friction Points & Spec Violations
* **Friction 4.1 (Fabricated/Unexplained Bridge Residuals):** In early builds, driver sums failed to tie out to net variance due to rounding or missing residual steps. `DEC-065` enforces an explicit `Other (unexplained)` step so bar tops march 15,770,000 $\rightarrow$ 16,645,000 exactly without fabricated tie-outs.
* **Friction 4.2 (Bulk Status & Owner Assignment):** To achieve the PRD target of closing $\ge 80\%$ of month-end exceptions within 5 days (`PRD` M9), `SCR-023` must support bulk owner assignment and status updates (`FR-EXC-007`).

#### Governing Clauses
* `02` FR-BVA-001..016, FR-EXC-004..020.
* `05` CALC-010 (Variance `Actual − Budget`), CALC-011 (Variance %), CALC-012 (Favourability), CALC-013 (Percentage Points).
* `06` Rules EXC-004 through EXC-020.
* `08` §8 (SCR-015 through SCR-026).

---

### Hours 09–10: Rolling Forecast Refresh & Multi-Scenario Modeling

* **Analyst Goal:** Update the rolling 12-month forecast (`FR-FC-001`..`009`), apply forecast methods (Run-rate, Seasonality, Budget-remaining), run what-if scenario comparisons, and evaluate forecast accuracy (MAPE-lite).
* **Primary Screens:** `SCR-027` (Forecast Workspace), `SCR-028` (Forecast Comparison & Accuracy).

#### Workflow Walkthrough & Step-by-Step Experience
1. **Method Application (`SCR-027` / `07` §3):**
   * **Run-Rate:** $FC = \text{Average of last } N \text{ actual periods}$.
   * **Seasonality:** Apply prior-year period weightings to remaining baseline.
   * **Budget-Remaining:** $FC = \text{YTD Actuals} + \text{Remaining Annual Budget}$.
2. **Manual Overrides (`FR-FC-004`):** Overriding individual line items tags the value as `Manual Override` with an audit note requirement.
3. **Scenario Comparison (`SCR-028`):** Compare Base Case vs Optimistic vs Conservative scenarios side-by-side.
4. **Accuracy Measurement (`CALC-027` / `KPI-006`):** Measure MAPE-lite against closed prior periods. Divide-by-zero guards enforce `Actual = 0 \rightarrow n/a`.

#### Friction Points & Spec Violations
* **Friction 5.1 (Insufficient Historical Depth for Seasonality):** Seasonality methods require 12+ loaded historical periods. If fewer than 12 periods exist, `SCR-027` must automatically fall back to Run-Rate or Budget-Remaining with an explicit UI disclosure notice (`07` §3.2).
* **Friction 5.2 (Forecast Baseline Locking):** Closed periods must lock forecast baselines to prevent silent historical recalculation (`FR-FC-005`).

#### Governing Clauses
* `02` FR-FC-001..009 (Rolling Forecast Family).
* `07` §3–§5 (Forecast Method Arithmetic & Scenario Rules).
* `05` §9 (KPI-006 MAPE-lite Accuracy Metric).
* `08` §9 (SCR-027, SCR-028).

---

### Hours 11–12: Presentation Deck, Board Pack Generation & Audit Lock

* **Analyst Goal:** Draft executive AI commentary, build the monthly Excel pack (`FR-XL`), populate the 6-slide PowerPoint deck (`FR-PPT`), issue the period deliverables, and lock the period (`FR-PRJ-005`).
* **Primary Screens:** `SCR-029` (Generate Pack), `SCR-031` (Commentary Editor), `SCR-030` (Pack Issuance Register).

#### Workflow Walkthrough & Step-by-Step Experience
1. **Commentary Generation (`SCR-031` / `10` §4):** Synthesize BvA variances into structured commentary using local AI or rule-based fallback. All monetary claims are verified against calculated engine totals.
2. **Excel Pack Export (`FR-XL-001`..`009` / `11`):** Generate formula-driven `.xlsx` workbook containing Cover, Summary BvA, Account Detail, Waterfall Data, and Exception Log. Includes mandatory rounding footnote (`CALC-031`): *"Components may not sum to the total due to rounding."*
3. **PowerPoint Deck Generation (`FR-PPT-001`..`009` / `12`):** Fill `FPAMonthEndCopilot_v1.pptx` template slides 1–6. Shapes are resolved **by name** (`FPA-PPT-001`..`006`) to preserve editable layouts (`DEF-018` PPT fix).
4. **Period Lock & Pack Issuance (`SCR-030` / `FR-PRJ-005`):** Click "Issue Month-End Pack". Generates a immutable close snapshot hash. Locks `FY26-P09` actuals against further imports.

#### Friction Points & Spec Violations
* **Friction 6.1 (PPT Template Shape Preservation):** Direct text replacement on PPT shapes risks destroying run formatting (`rPr` font, size, colour). The engine must use `pptx_fill.patterns.set_text` to modify existing runs without destroying template styling (`ADP-002`).
* **Friction 6.2 (Sum-of-Rounded Footnote Omission):** Any table where aggregated displayed numbers differ from the unrounded total by $\pm 0.01$ must automatically render the mandatory rounding footnote (`CALC-031`).

#### Governing Clauses
* `02` FR-XL-001..009, FR-PPT-001..009, FR-PRJ-005/010, FR-XC-001..003.
* `05` CALC-030/031 (Rounding & Sum-of-Rounded Footnote Rules).
* `11` §4 (Excel Output Architecture).
* `12` §4–§5 (PowerPoint Layout & Shape Binding Spec).
* `08` §10 (SCR-029, SCR-030, SCR-031).

---

## Section 2: Ranked Gap & Friction List

The following gap list ranks operational friction points encountered during the month-end close by their **(Impact on Accountant's Day) / (Effort to Fix)** ratio.

| Rank | Issue / Gap ID | Description | Impact on Close | Governing Clause | Estimated Effort | Impact/Effort Ratio | Recommended Fix |
|---|---|---|---|---|---|---|---|
| **1** | **GAP-01 (`OQ-025` / `DEC-056`)** | Unconditional `debit=credit` reject blocks single-sided sub-ledgers (Bank/Payroll). | **Critical (Blocks Hour 3)** | `04` §12, `02` FR-IMP-023 | Low (1–2 days) | **Highest** | Scope `debit=credit` balancing check to GL actuals per `DEC-056`; validate sub-ledgers via row count & net totals. |
| **2** | **GAP-02 (`DEF-018` / `DEC-065`)** | Bridge waterfall shape resolution and unexplained residual tie-out. | **High (Affects Hour 8 & 12)** | `12` §4–§5, `05` CALC-010 | Low (Fixed in engine, verify) | **High** | Bind PPT shapes strictly by name (`FPA-PPT-001`..`006`) & force explicit `Other (unexplained)` bridge step. |
| **3** | **GAP-03 (`OQ-026` / `DEC-057`)** | Subject-key format mismatch between exception rules and answer key/catalog. | **High (Affects Hour 5 & 7)** | `06` §3, `02` FR-EXC-001 | Low (1 day) | **High** | Standardize subject key formatting (`entity\|account`) across all 24 exception rules per `DEC-057`. |
| **4** | **GAP-04 (`CALC-013`)** | Ratio variance percentage display (`%` instead of `pp`). | **Medium (Affects Hour 7 & 11)** | `05` CALC-013, `08` §13 | Low (1 day) | **High** | Enforce `pp` unit labelling helper across BvA grid, Excel, and PPT output. |
| **5** | **GAP-05 (`FR-EXC-007`)**| Lack of bulk status update and owner routing on Exception Register (`SCR-023`). | **Medium (Affects Hour 8)** | `02` FR-EXC-007, `08` SCR-023 | Medium (2 days) | **Medium** | Add bulk checkbox selection + "Assign Owner" & "Change Status" actions to `SCR-023`. |

---

## Section 3: Proposed Cuts (Over-Built Surface Removal)

To prevent scope creep and maintain software quality, the following over-built or redundant features are recommended for removal/simplification:

1. **Cut Proposal 1: Speculative / High-Complexity Forecast Methods without 24+ Months Data**
   * **Rationate:** Methods requiring multi-year historical depth add UI complexity on `SCR-027` without delivering accuracy on standard 12-period datasets.
   * **Recommendation:** Restrict default forecast methods to **Run-rate (3M/6M)**, **Seasonality (12M)**, and **Budget-Remaining**.
   * **Spec Alignment:** Keeps `07` §3 lean and robust.

2. **Cut Proposal 2: Un-drillable Pure Visual Charts**
   * **Rationale:** `08` §1 binding rule 3 states: *"Every chart has a table view — no chart is the only way to read a number."*
   * **Recommendation:** Remove any standalone visual widget that lacks underlying transaction drill-through (`SCR-021`).

---

## Section 4: Verification & Traceability Matrix

| Hour | Screen ID | Requirement ID | Formula / Rule ID | Output Deliverable | Status / Verified By |
|---|---|---|---|---|---|
| **01–02** | `SCR-001`, `SCR-004` | `FR-PRJ-001`, `FR-PRJ-004` | `CALC-001` | Open Period `FY26-P09` | Verified (`02` §FR-PRJ) |
| **03–04** | `SCR-005`..`SCR-013` | `FR-IMP-001`..`031` | `CALC-007`, `IMP-023` | Clean Ingested GL & Sub-ledgers | Verified (`04` §12) |
| **05–06** | `SCR-014`, `SCR-012` | `FR-EXC-001`..`003` | `EXC-001`..`EXC-003` | Validation Report & DQ Score (95+) | Verified (`06` §3) |
| **07–08** | `SCR-015`..`SCR-026` | `FR-BVA-001`..`016`, `FR-EXC-004`..`020` | `CALC-010`..`CALC-013` | Variance Grid, Waterfall, Exceptions | Verified (`05` §4) |
| **09–10** | `SCR-027`, `SCR-028` | `FR-FC-001`..`009` | `CALC-040`..`043`, `KPI-006` | Rolling Forecast Workspace | Verified (`07` §3) |
| **11–12** | `SCR-029`..`SCR-031` | `FR-XL-001`..`009`, `FR-PPT-001`..`009` | `CALC-030`, `CALC-031` | Issued Board Deck, Excel Pack, Lock | Verified (`11`, `12`) |

---

*Report delivered by `hermes` to `evidence/ux/hermes-journey.md` for handoff to leader `buffy` under task `UX-01`.*
