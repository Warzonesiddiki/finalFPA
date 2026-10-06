# Whole-Project Design Review — FP&A Analyst Perspective

> **Reviewer:** `hermes` (Analyst's Advocate)  
> **Task ID:** `RV-01` (P1)  
> **Target Evidence Path:** `evidence/reviews/hermes-review.md`  
> **Target Review Path (for Handoff):** `team/reviews/hermes.md`  
> **Governing Specs:** `docs/00_INDEX.md` through `docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

As the **Analyst's Advocate**, this review evaluates the FP&A Month-End Copilot against real-world accounting workflows, financial specifications (`05`, `06`, `07`), user experience contracts (`08`), and presentation deliverables (`11`, `12`). 

The system's architectural foundations — exact `Decimal` arithmetic (`R8`), DuckDB bulk multi-row loading (`DEF-030`), shape-by-name PowerPoint pattern filling (`DEF-018`), and deterministic golden fixtures (`05` §12) — provide immense product strength. However, key friction points in import gating, exception triage, and unit presentation currently impede seamless month-end execution.

---

## Responses to Core Review Questions

### 1. Most Valuable Capability vs Current Implementation Shortcoming

* **Most Valuable Capability:**  
  The ability to ingest disparate multi-system ERP exports (`d365_gl_actuals.csv`, sub-ledgers, budget files), validate structural integrity without silent data loss (`P13`), compute canonical variance and favourability (`CALC-010`..`CALC-012`), and render board-ready PowerPoint decks (`FR-PPT-001`..`009`) in hours rather than days.

* **Where Implementation Falls Short:**  
  The acceptance gate previously failed recall (11/32) due to three operational blockers, which `DEC-056`…`DEC-059` have now resolved:
  1. **`OQ-025` $\rightarrow$ `DEC-056` Sub-Ledger Balance Gate:** Unconditional `debit=credit` enforcement (`IMP-023`) rejected 100% of single-sided sub-ledger feeds. `DEC-056` scopes the check so amount-style sub-ledgers use net reconciliation with ₹500 tolerance.
  2. **`OQ-026` $\rightarrow$ `DEC-057` Subject Key Discrepancies:** Key format mismatches (e.g. `P20`, `P21`, `P24`) prevented valid exceptions from matching the answer key. `DEC-057` establishes `06` catalog as authoritative.
  3. **`OQ-027` $\rightarrow$ `DEC-058` History Fixture Absence:** Missing overlapping batch fixtures suppressed duplicate import detection (`EXC-002`). `DEC-058` adds history fixtures.
  4. **`PROP-001` $\rightarrow$ `DEC-059` Coherent Corpus Rebuild:** Approved bundled corpus rebuild to eliminate 370 extra false positives.

---

### 2. What to Cut (Over-Built Surface Removal)

1. **Speculative Forecasting Methods on Sparse Data (`07` §3):**  
   Complex predictive algorithms requiring 24+ historical periods add unnecessary UI clutter to `SCR-027` when operating on standard 12-period fiscal datasets.  
   *Cut:* Retain only **Run-rate (3M/6M)**, **Seasonality (12M)**, and **Budget-Remaining** methods.

2. **Un-drillable Standalone Visual Widgets (`08` §1):**  
   Any chart widget on `Analyze` screens that acts as a visual end-point without supporting raw line-item transaction drill-through (`SCR-021`) violates UI Principle 3 (*"Every chart has a table view"*).  
   *Cut:* Remove static visual summaries in favour of interactive BvA tables with inline micro-charts.

---

### 3. Missing Capabilities Needed in the First Hour of Use

1. **Bulk Exception Triage & Assignment Workflow (`FR-EXC-007` / `SCR-023`):**  
   During a month-end close, an analyst must triage 50+ flagged exceptions. Processing them one-by-one is prohibitive. The analyst requires multi-select bulk assignment to regional accounting leads and bulk status updates (`Open` $\rightarrow$ `Under Review` $\rightarrow$ `Explained`).
2. **Multi-File Batch Queue Progress (`SCR-005`..`SCR-009`):**  
   When importing GL actuals, payroll, bank, and budget files simultaneously, switching screens for each file creates high friction. A unified batch upload queue with pre-scan status indicators is essential.

---

### 4. Architectural Friction & Structural Impediments

1. **Import Boundary Coupling (`04` §12 vs `04` §3):**  
   Enforcing general-ledger trial balance constraints (`debit = credit`) at the generic import repository boundary (`app/engine/store/import_repo.py`) breaks sub-ledger ingestion. GL constraints must be isolated to GL source types (`OQ-025`).
2. **Template Run Formatting Sensitivity in PPT Fill (`12` §4):**  
   Replacing text in PowerPoint shapes via standard `text_frame.text = ...` destroys template formatting (`rPr`). The architecture correctly introduced `pptx_fill.patterns.set_text` (`ADP-002`), but shape binding must remain strictly name-based (`FPA-PPT-001`..`006`) to ensure stability (`DEF-018`).

---

### 5. Lessons & Insights from Prior Art

Earlier implementations (`/fpa`, `/fp-A-betterversion`) excelled at **frictionless data exploration** — allowing analysts to drop files, immediately view multi-dimensional BvA grids, and drill down without hard gating blocks. `finalFPA` improves on arithmetic rigor and presentation quality, but must preserve that instant time-to-insight experience by providing clear inline fixes when validation checks fire.

---

## Top 5 Prioritized Recommendations

| Rank | Recommendation | Governing Clause | Expected Impact | Estimated Effort | Trade-off / Risk |
|---|---|---|---|---|---|
| **1** | **Scope `debit=credit` check per source type (`OQ-025`)** | `04` §12, `02` FR-IMP-023 | Unblocks 100% of sub-ledger imports; fixes recall gating blocker. | Low (1 day) | Requires explicit profile classification per file. |
| **2** | **Implement Bulk Exception Assignment & Triage (`SCR-023`)** | `02` FR-EXC-007, `08` SCR-023 | Achieves PRD Target M9 ($\ge 80\%$ exception closure in 5 days). | Medium (2 days) | Requires batch database update endpoint. |
| **3** | **Standardize Exception Subject Key Formatting (`OQ-026`)** | `06` §3, `02` FR-EXC-001 | Resolves recall gap; aligns rules with catalog definitions. | Low (1 day) | Requires answer key alignment script. |
| **4** | **Enforce Percentage Point (`pp`) Unit Rendering (`CALC-013`)** | `05` CALC-013, `08` §13 | Ensures financial accuracy; prevents misinterpretation of ratio variances. | Low (1 day) | UI string formatting changes. |
| **5** | **Streamline Forecast Workspace Defaults (`07` §3)** | `07` §3, `02` FR-FC-001 | Reduces cognitive load; accelerates forecast generation. | Low (1 day) | Hides speculative forecasting methods behind advanced toggle. |

---

*Review submitted by `hermes` to `evidence/reviews/hermes-review.md` for handoff under task `RV-01`.*
