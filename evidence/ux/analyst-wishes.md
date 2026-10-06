# FP&A Analyst Workday Enhancement Proposal & Artifacts of Desire

> **Document Author:** `hermes` (Analyst's Advocate)  
> **Task Reference:** `UX-05` (P2)  
> **Target Evidence Path:** `evidence/ux/analyst-wishes.md`  
> **Target Review Path (for Handoff):** `team/reviews/analyst-wishes.md`  
> **Governing Specs:** `docs/01_PRD.md`, `docs/02_FUNCTIONAL_SPEC.md`, `docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md`, `docs/05_CALCULATION_SPEC.md`, `docs/06_EXCEPTION_RULES_CATALOG.md`, `docs/07_FORECAST_METHODS_SPEC.md`, `docs/08_UI_UX_SPEC.md`, `docs/11_EXCEL_OUTPUT_SPEC.md`, `docs/12_POWERPOINT_OUTPUT_SPEC.md`, `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

This proposal provides a comprehensive analysis of the real-world FP&A Analyst month-end close workflow for clients operating in enterprise environments (e.g. **Microsoft Dynamics 365 (D365)** general ledger actuals + 2 ancillary software dumps for Bank and Payroll/Procurement).

The analyst's monthly responsibilities span five core pillars:
1. Ingesting multi-system Excel/CSV dumps without manual data entry or formula breakage.
2. Performing transaction-level Budget vs Actual (BvA) variance analysis.
3. Identifying accounting misclassifications and errors to guide operational accounting teams.
4. Building rolling forecasts and multi-scenario future budgets.
5. Generating board-ready PowerPoint presentation decks and Excel audit packs.

---

## Section 1: The Analyst's Three Core Artifacts of Desire

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               THE THREE ARTIFACTS OF DESIRE                                     │
├───────────────────────────────┬─────────────────────────────────┬───────────────────────────────┤
│ 1. Board Executive Narrative  │ 2. Multi-Source Reconciliation  │ 3. Accounting Feedback &      │
│    (1-Page Management Summary)│    Worksheet (Tie-Out Grid)     │    Misclassification Log      │
│    [Hours 11–12 · SCR-031]    │    [Hours 03–06 · SCR-010/014]   │    [Hours 07–08 · SCR-023]    │
└───────────────────────────────┴─────────────────────────────────┴───────────────────────────────┘
```

---

### Artifact 1: One-Page Board Executive Narrative ("The 5-Minute Executive Summary")

* **Analyst Need:** Executives, CFOs, and Board members do not read 500-row detailed spreadsheets during monthly reviews. They require a concise 1-page executive summary highlighting the top 5 key financial metrics, plain-language variance explanations, and critical operational assumptions.
* **Month-End Journey Step:** Hours 11–12 (Presentation Deck & Report Issuance).
* **Governing FRs & Screens:**
  * `SCR-031` (Commentary Editor) & `SCR-029` (Generate Pack).
  * `FR-AI-004..012` (Verifiable AI-assisted executive commentary).
  * `FR-PPT-001..009` (PowerPoint Slide 1 Executive Overview).
* **Smallest Shippable Slice:**
  * A single structured executive panel rendering 5 core KPIs (`KPI-001` Gross Margin %, `KPI-002` Opex Ratio, `KPI-003` Budget Burn %, Net Revenue, Net Income) alongside 3 bullet points explaining key favourable and adverse variance drivers.
  * Formula-verified against backend analytical store totals (`CALC-010`..`CALC-012`).

---

### Artifact 2: Multi-Source Reconciliation & Tie-Out Worksheet ("The Auditor-Ready Tie-Out")

* **Analyst Need:** FP&A analysts ingest transaction dumps from D365 GL Actuals, Bank Statement feeds, and Payroll/Procurement systems. They spend hours building manual Excel VLOOKUPs to prove that GL totals tie out to source dumps without missing vouchers or single-sided drops.
* **Month-End Journey Step:** Hours 03–04 (Multi-Source Import) & Hours 05–06 (Data Integrity Validation).
* **Governing FRs & Screens:**
  * `SCR-010` (Commit & Confirm), `SCR-012` (Batch Validation Report), `SCR-014` (Check Screen).
  * `FR-IMP-023` / `DEC-056` (Source-type scoped balance gates).
  * `EXC-001` (Control Totals Check) & `EXC-003` (Trial Balance Tie-Out).
* **Smallest Shippable Slice:**
  * A automated reconciliation table displaying declared source file control totals vs imported analytical store totals, explicitly isolating any residual delta as an `Other (unexplained)` variance line item (`DEF-018` / `DEC-065`).

---

### Artifact 3: Accounting Feedback & Misclassification Audit Log ("The Accounting Guidance Sheet")

* **Analyst Need:** Beyond reporting variance, the FP&A analyst supervises operational accounting teams. Accounting staff frequently make posting errors: misclassified account codes, duplicate invoice numbers, incorrect cost centers, and cut-off period errors. The analyst needs an automated error guidance report to hand back to accounting team leads for corrective journal entries.
* **Month-End Journey Step:** Hours 07–08 (Variance Investigation & Exception Triage).
* **Governing FRs & Screens:**
  * `SCR-023` (Exceptions Register) & `SCR-024` (Exception Detail Drawer).
  * `FR-EXC-007` (Owner assignment & status workflow).
  * `EXC-004`..`EXC-020` (Financial exception rules: duplicate invoices, magnitude anomalies, cut-off mismatches).
* **Smallest Shippable Slice:**
  * An exportable **"Accounting Action Log"** (`.xlsx` / `.csv`) grouped by Accounting Team Lead / Department, containing:
    1. Offender Voucher ID & Transaction Date.
    2. Rule Triggered (e.g. `EXC-007` Duplicate Invoice, `EXC-010` Cut-Off Mismatch).
    3. Anomaly Amount ($\text{Actual} - \text{Expected}$).
    4. Recommended Corrective Action (e.g. *"Reclassify from 5100-Opex to 1200-Prepaid Expenses"*).

---

## Section 2: End-to-End Automation Roadmap for D365 + Ancillary Feeds

To transform the analyst's monthly workflow from manual spreadsheet manipulation to an automated co-pilot, the following four automation pillars are specified:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                FOUR AUTOMATION PILLARS                                          │
├───────────────────┬───────────────────┬───────────────────┬─────────────────────────────────────┤
│ Pillar 1: Auto    │ Pillar 2: Micro   │ Pillar 3: Rolling │ Pillar 4: Board Deck &              │
│ Profile Binding   │ Transaction Drill │ Forecast Engine   │ Excel Pack Automation               │
│ (D365 + Feeds)    │ (D365 Vouchers)   │ (Run-Rate/Season) │ (PPTX Fill by Name)                 │
└───────────────────┴───────────────────┴───────────────────┴─────────────────────────────────────┘
```

### Pillar 1: Automated Profile Binding for D365 & Sub-Ledger Feeds
* **Current Friction:** Monthly re-mapping of column headers for `d365_gl_actuals.csv`, bank statements, and payroll exports.
* **Automation Solution:** Persistent mapping profiles (`FR-IMP-004`, `SCR-033`) automatically recognize source signatures and apply predefined column mappings, header row offsets, and date format parsers without user intervention.

### Pillar 2: Micro Transaction Drill-Through for Variance Culprits
* **Current Friction:** Identifying why an account (e.g. "Software Licenses") is over budget requires manually filtering 250,000 GL rows in Excel.
* **Automation Solution:** Clicking any BvA grid cell in `SCR-015` immediately opens `SCR-021` (Drill-Through Modal), displaying filtered D365 voucher rows, vendor names, posting dates, and original source references.

### Pillar 3: Automated Rolling Forecast & Future Budget Modeling
* **Current Friction:** Creating future budgets requires rebuilding manual spreadsheet formulas every period.
* **Automation Solution:** `SCR-027` (Forecast Workspace) automates 12-period rolling forecasts using:
  * **Run-Rate Method:** Average of last 3M/6M actuals (`07` §3.1).
  * **Seasonality Method:** Prior-year period weightings applied to target baselines (`07` §3.2).
  * **Budget-Remaining Method:** $\text{YTD Actuals} + \text{Remaining Annual Budget}$.

### Pillar 4: Automated Board Presentation & Audit Pack Generation
* **Current Friction:** Re-keying numbers into PowerPoint presentation slides and formatting Excel workbooks takes 4–8 hours per close.
* **Automation Solution:** 
  * `SCR-029` populates `FPAMonthEndCopilot_v1.pptx` by resolving shapes strictly by name (`FPA-PPT-001`..`006`) using run-preserving `set_text` helpers (`DEF-018` / `ADP-002`).
  * Generates formula-driven `.xlsx` workbooks (`FR-XL`) with mandatory sum-of-rounded footnotes (`CALC-031`).

---

## Section 3: Proposed `docs/18` Proposals for Owner Ruling

The following formal proposals are submitted for inclusion in `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` to enhance analyst productivity while respecting spec bounds (`R1`):

### `PROP-002` — Departmental Accounting Action Log Export
* **Proposal:** Add an explicit "Export Accounting Action Log" button on `SCR-023` (Exceptions Register) that outputs a formatted `.xlsx` workbook categorized by accounting team lead, listing flagged voucher numbers, exception rules, amounts, and reclassification instructions.
* **Impact:** Direct solution for guiding accounting teams on wrong entries. Zero core engine changes required.

### `PROP-003` — Multi-Source Batch Queue Ingestion Panel
* **Proposal:** Upgrade `SCR-005` (Import Step 1) to support dropping D365 GL actuals, bank dumps, and payroll files into a single unified queue panel with background progress indicators (`FR-IMP-030`).
* **Impact:** Eliminates multi-step screen switching for 4+ monthly file feeds.

---

## Section 4: Traceability & Spec Alignment Summary

| Artifact / Feature | Governing FR | Screen ID | Calculation / Rule ID | Primary Deliverable |
|---|---|---|---|---|
| **Board Narrative** | `FR-AI-004..012`, `FR-PPT-001` | `SCR-031`, `SCR-029` | `KPI-001`..`KPI-005`, `CALC-010` | 1-Page Executive Summary & PPT Slide 1 |
| **Reconciliation Grid** | `FR-IMP-016`, `FR-IMP-023` | `SCR-010`, `SCR-014` | `EXC-001`, `EXC-003`, `DEC-056` | Verified Control Total Tie-Out Sheet |
| **Accounting Action Log** | `FR-EXC-007`, `FR-EXC-016` | `SCR-023`, `SCR-024` | `EXC-004`..`EXC-020` | Departmental Error Correction Export |
| **D365 Profile Auto-Match**| `FR-IMP-004` | `SCR-005`, `SCR-008` | `IMP-004` Profile Binding | Zero-Touch File Ingestion |
| **Rolling Forecast** | `FR-FC-001`..`009` | `SCR-027`, `SCR-028` | `CALC-040`..`043`, `KPI-006` | Automated 12-Month Rolling Budget |

---

*Proposal submitted by `hermes` to `evidence/ux/analyst-wishes.md` for handoff under task `UX-05`.*
