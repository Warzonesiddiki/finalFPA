# Strategic Recommendations & Product Enhancement Proposal

> **Author:** `hermes` (Analyst's Advocate)
> **Audience:** `owner` & `buffy` (Team Leader)
> **Goal:** Brainstormed research and strategic suggestions based on the FP&A Analyst profile and month-end workflow.
> **Date:** 2026-10-05

---

## 1. Executive Context: The FP&A Analyst Client Workflow

Based on real-world requirements, our primary client is an FP&A Analyst operating a multi-system month-end close. Their monthly cycle involves:
1. **Data Sourcing:** Exporting raw data dumps from **Microsoft Dynamics 365 (D365)**, plus two ancillary systems (e.g., Bank/Treasury and Payroll/Procurement).
2. **Analysis & Variance Exploration:** Reconciling actuals against budgets down to the transaction level in Excel.
3. **Future State Modeling:** Creating rolling budgets and forward-looking forecasts.
4. **Accounting Oversight:** Identifying wrong entries (misclassifications) and directing the accounting operations team to correct them.
5. **Executive Reporting:** Building PowerPoint presentations and summarized management reports.

Currently, the product structure (`finalFPA`) elegantly handles rules (`06`), calculations (`05`), and exports (`11`, `12`), but there is strategic room to enhance the *experience* and *value density* for this specific client profile.

---

## 2. Brainstormed Strategic Suggestions

### Suggestion 1: The "Feedback Loop" Export for Accounting Operations
* **Problem:** FP&A analysts find mistakes (wrong cost centers, duplicate postings, invalid general ledger codes) and have to manually email spreadsheets to accounting teams for correction.
* **Proposed Enhancement:** Add an automated **"Journal Entry Correction Export"** from the Exceptions Register (`SCR-023`). When an analyst marks an exception as "Reclassification Needed", the system exports a clean Excel template formatted specifically for a D365 General Journal upload.
* **Impact:** Closes the loop between FP&A anomaly detection and Accounting remediation. Saves the analyst hours of typing out correction emails.

### Suggestion 2: "D365-Native" Pre-packaged Mapping Profiles
* **Problem:** Every month, the analyst imports the D365 dump. If the file structure changes or they start a new fiscal year, mapping column headers (`SCR-008`) is a friction point.
* **Proposed Enhancement:** Ship the application with a hardcoded **"Microsoft Dynamics 365 Default Profile"**. It automatically recognizes standard D365 GL export columns (`Voucher`, `MainAccount`, `AmountinTransactionCurrency`, `AccountingDate`) and maps them perfectly without user interaction.
* **Impact:** "Zero-click" ingestion for their largest data source. The application immediately feels purpose-built for their ERP.

### Suggestion 3: Rolling "What-If" Budget Scenario Builder
* **Problem:** Generating standard rolling budgets (e.g., Run Rate, Seasonality) is good, but FP&A thrives on "What-If" variance questions (e.g., "What if we increased Marketing Spend by 5% and cut Travel by 10%?").
* **Proposed Enhancement:** Upgrade the Forecast Workspace (`SCR-027`) to introduce a **"What-If Variance Slider"** applied to historical baselines. Analysts can globally scale specific departmental categories and immediately see the projected impact on Net Income in the side-by-side comparison modal (`SCR-028`).
* **Impact:** Upgrades the tool from a reactive variance reporter into a proactive strategic planning asset.

### Suggestion 4: Interactive PPTX Presentation Mode
* **Problem:** We generate a static 6-slide PowerPoint deck (`FR-PPT`). While highly valuable, during a live meeting, a CFO might ask, "What makes up that $50k variance?"
* **Proposed Enhancement:** Introduce an **"Exec Presentation Mode"** inside the application (`SCR-015` BvA Matrix + `SCR-031` Commentary) engineered specifically for screen-sharing. It hides the left navigation panel, blows up the font sizes, and allows 1-click drill-down (`SCR-021`) straight into the transactions during the meeting.
* **Impact:** The analyst no longer has to say, "I'll look into it and get back to you." They double-click the variance live in the meeting.

### Suggestion 5: Sub-Ledger Reconciliation Integrity Metric (The "Tie-Out Health" KPI)
* **Problem:** The analyst imports 3 different systems (D365 + 2 others). Proving these systems are in sync is a core anxiety.
* **Proposed Enhancement:** Surface a prominent **"System Tie-Out Health"** KPI card on the Home Screen (`SCR-001`). It verifies that the Net Cash imported from the Bank sub-ledger exactly equals the Cash GL account balance imported from D365.
* **Impact:** Delivers instant peace of mind. The application technically does this via `EXC-003` (Balance Tie-Out), but elevating it to a high-visibility KPI changes the psychological safety of the tool.

---

## 3. Recommended Action Plan for Leader (`buffy`)

If aligned, these capabilities can be formally drafted into `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` as Open Questions (`OQ-040` series) to evaluate for Phase 1 or Phase 2 scope:

1. **Evaluate D365 Profile:** Add MS Dynamics 365 default mapping profiles to `app/engine/imports/profiles.py`. *(Effort: Low)*
2. **Develop Accounting Action Log:** Extend `FR-EXC-017` (Exception Register Export) to include a "Suggested Correction" column. *(Effort: Low)*
3. **Review Presentation Mode:** Add a toggle in `08` UI/UX Spec to collapse navigation for a clean "Presenter View." *(Effort: Low)*

---
*Brainstorming & Research dossier prepared by `hermes` for `owner` and `buffy`.*
