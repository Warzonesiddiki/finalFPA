# FP&A Month-End Copilot — Recorded Demo Chapter Scripts (Doc 22 §10.2)

## Quoted Specification (Doc 22 §10.2)
> *"Six chapters, one per screen area, 3–5 minutes each, recorded on the sample project: (1) Home and the period, (2) Import and Check, (3) Analyse and drill, (4) Exceptions, (5) Forecast and commentary, (6) Pack, issue and backup. Chapter titles match the §4 task titles so a viewer can jump straight to the guide."*

---

## Chapter 1: Home and the Period (Duration: ~3:30)
- **What to click**: Launch app → view Home dashboard (`SCR-001`), note active period indicator (`FY26-P09`), inspect summary KPI cards and quick-jump navigation links. Click `? Help` to demonstrate the contextual help drawer.
- **What to say**: "Welcome to the FP&A Month-End Copilot. When you launch the application, you land directly on the Home dashboard. Notice the active period indicator showing FY26-P09. Here, you get an immediate snapshot of data quality, key financial metrics, and quick links to guide your monthly close rhythm. Clicking the Help button at any time opens a contextual guide matching our end-user manual."
- **Expected on-screen result**: Clean Home dashboard loaded with active period status, KPI cards, and responsive Help drawer.

---

## Chapter 2: Import and Check (Duration: ~4:15)
- **What to click**: Click **Import** tab (`SCR-002`..`005`) → review pre-loaded sample batch items (`d365_gl_actuals.csv`, `bank_ledger_actuals.csv`) → click **Check & Quality** tab (`SCR-011`) to review balance equations and data quality score (99.2%).
- **What to say**: "Step two of our monthly cycle is ingestion and validation. The Import wizard walks you through D365 GL actuals, bank ledgers, payroll, and budget files in 6 structured steps. As files are ingested, the engine runs 32 strict validation and hardening checks. Quarantined rows are safely isolated without dropping data. Once committed, the Check & Quality screen confirms trial balance equality and overall health."
- **Expected on-screen result**: Import wizard interface showing committed batches and green PASS indicators on balance checks.

---

## Chapter 3: Analyse and Drill (Duration: ~4:30)
- **What to click**: Click **Analyse** tab (`SCR-015`) → select department filter (`Commercial`) → click any variance figure in the BvA matrix table to open the transaction evidence drill-down drawer (`SCR-021`).
- **What to say**: "Now that our data is validated, we move to analysis. The Analyse screen presents our Budget vs Actual matrix tables across statement lines. Notice the favorable and unfavorable variance indicators. By clicking directly on any variance figure, the transaction evidence drawer opens instantly, showing the underlying journal voucher lines, batch IDs, and source records with exact decimal precision."
- **Expected on-screen result**: BvA matrix grid with statement line summaries and transaction evidence drill-down drawer.

---

## Chapter 4: Exceptions and Review (Duration: ~4:30)
- **What to click**: Click **Exceptions** tab (`SCR-020`) → filter findings by severity (`Critical`, `Warning`) → select finding `EXC-001` → assign owner (`Priya Sharma`) → transition status from `Open` to `In Review` or `Explained`.
- **What to say**: "The exceptions engine evaluates 24 automated rules (EXC-001 through EXC-024) using deterministic Decimal math—never AI guesses. The Exceptions register displays severity badges, aging buckets, and automatic owner assignments based on cost center mappings. Analysts can assign owners, add explanatory notes, and track the resolution workflow from Open to Closed."
- **Expected on-screen result**: Exceptions register table with severity badges, aging columns, and active detail drawer.

---

## Chapter 5: Forecast and Commentary (Duration: ~4:30)
- **What to click**: Click **Forecast** tab (`SCR-028`) → view method selection (Run-rate, Trailing Average, Remaining Budget) → switch between Base, Best, and Worst scenario views → enter a manual override with justification reason. Click **AI & Commentary** tab (`SCR-031`) → review AI draft commentary labeled *"AI draft — review before use"* and generate a follow-up message draft (`PROMPT-04`).
- **What to say**: "Next, we generate rolling forecasts and scenario comparisons. You can select forecasting methods, compare Base, Best, and Worst scenarios, and enter manual overrides with mandatory audit reasons. In the AI Commentary screen, narratives are generated with strict PII redaction guardrails and are explicitly labeled as drafts requiring human review. You can also draft internal follow-up messages for accounting owners and copy them directly to clipboard."
- **Expected on-screen result**: Forecast scenario comparison curves, override modal, and AI commentary draft viewer with prominent labels.

---

## Chapter 6: Pack, Issue and Backup (Duration: ~4:15)
- **What to click**: Click **Reports** tab (`SCR-033`) → preview Excel pack export (`11`) and PowerPoint deck generation (`12`) → click **Issue Pack** to increment version and record recipient list. Navigate to **Backup & Restore** (`SCR-039`) → click **Download Project Backup Zip**. Finally, view **About & Diagnostics** (`SCR-040`) → run CLI doctor checks (`DOC-01`..`05`) and export redacted diagnostics bundle.
- **What to say**: "In our final chapter, we issue formal financial packs. The Reports screen generates structured Excel workbooks and PowerPoint executive decks. Issuing a pack locks the commentary and increments the version registry. For ongoing maintenance, the Backup & Restore screen provides one-click project snapshots to timestamped zips. Finally, the About & Diagnostics screen displays system build provenance, runs CLI doctor integrity checks, and exports redacted support bundles per doc 13 security policies."
- **Expected on-screen result**: Reports issuance registry, backup download prompt, and About & Diagnostics telemetry table.
