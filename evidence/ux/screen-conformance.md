# Screen-by-Screen Spec Conformance Matrix (SCR-001 .. SCR-043)

> **Task Reference:** `UX-03` (P1)  
> **Governing Spec:** `docs/08_UI_UX_SPEC.md` §4 (Screen Inventory)  
> **Target Evidence Path:** `evidence/ux/screen-conformance.md`  
> **Target Review Path (for Handoff):** `team/reviews/screen_conformance.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

This audit verifies all **43 defined screens (`SCR-001` through `SCR-043`)** from `docs/08_UI_UX_SPEC.md` against the active frontend React components (`ui/src/`) and API contracts (`app/api/`).

**Overall Conformance:** 42 of 43 screens are fully conforming with 5-state complete UI implementations; 1 screen (`SCR-023`) carries a minor P1 workflow enhancement gap (bulk owner assignment endpoint integration in progress).

---

## Conformance Matrix (43 Screens)

| SCR ID | Screen Name | Spec FRs Served | Implementation File & Line | Primary API Endpoint | State Completeness | Gap Status & Severity |
|---|---|---|---|---|---|---|
| `SCR-001` | **Home** | `FR-ONB-001, FR-PRJ-001, FR-ONB-003, FR-ONB-006, FR-ONB-008` | `ui/src/main.tsx:145` | `GET /api/periods/current, GET /api/health` | Full (Normal, Sample Banner, Health Warning, Actions) | **Conforming** (P0) |
| `SCR-002` | **Project Launcher (modal)** | `FR-ONB-001, FR-PRJ-002, FR-PRJ-003` | `ui/src/main.tsx:114` | `GET /api/projects` | Full (Recent list, Locate, Create, Restore) | **Conforming** (P0) |
| `SCR-003` | **New Project Wizard** | `FR-PRJ-002, FR-SET-005, FR-SET-006` | `ui/src/main.tsx:115` | `POST /api/projects` | Full (Form validation, Synced-path warning) | **Conforming** (P0) |
| `SCR-004` | **New Period Wizard** | `FR-PRJ-004, FR-PRJ-005` | `ui/src/components/settings/PeriodLifecycleScreen.tsx:40` | `POST /api/periods` | Full (Source checklist, Out-of-order warning) | **Conforming** (P0) |
| `SCR-005` | **Import Step 1 — Choose File** | `FR-ONB-003, FR-IMP-001, FR-IMP-010, FR-IMP-019` | `ui/src/components/import/ChooseFileStep.tsx:216` | `POST /api/import/upload` | Full (Drag-drop, File picker, Format check) | **Conforming** (P0) |
| `SCR-006` | **Import Step 2 — Pre-scan** | `FR-IMP-003` | `ui/src/components/import/PreScanModal.tsx:1` | `POST /api/import/prescan` | Full (Row estimate, Size limits, Warning) | **Conforming** (P0) |
| `SCR-007` | **Import Step 3 — Sheet & Header** | `FR-IMP-007, FR-IMP-009, FR-IMP-010` | `ui/src/components/import/SheetHeaderStep.tsx:1` | `POST /api/import/headers` | Full (Sheet selector, Header row picker, Preview) | **Conforming** (P0) |
| `SCR-008` | **Import Step 4 — Map Columns** | `FR-IMP-004, FR-IMP-005, FR-IMP-008, FR-IMP-011` | `ui/src/components/import/ColumnMappingStep.tsx:95` | `POST /api/import/mappings` | Full (Auto-match, AI suggestions, Unmapped alert) | **Conforming** (P0) |
| `SCR-009` | **Import Step 5 — Validate** | `FR-IMP-014, FR-IMP-015, FR-IMP-017` | `ui/src/components/import/ValidationStep.tsx:1` | `POST /api/import/validate` | Full (Progress bar, Per-check results, Offender log) | **Conforming** (P0) |
| `SCR-010` | **Import Step 6 — Commit & Confirm** | `FR-IMP-016, FR-IMP-018, FR-IMP-020` | `ui/src/components/import/CommitConfirmStep.tsx:29` | `POST /api/import/commit` | Full (Batch summary, DQ score badge, Next actions) | **Conforming** (P0) |
| `SCR-011` | **Import History** | `FR-IMP-023, FR-IMP-024, FR-IMP-025` | `ui/src/components/import/ImportHistoryScreen.tsx:1` | `GET /api/import/batches` | Full (Batch log, Void batch modal, Reversal state) | **Conforming** (P1) |
| `SCR-012` | **Batch Detail / Validation Report** | `FR-IMP-016, FR-IMP-017, FR-IMP-021` | `ui/src/components/import/CommitConfirmStep.tsx:250` | `GET /api/import/batches/{id}/report` | Full (9-part report modal, Rule breakdown, Export) | **Conforming** (P1) |
| `SCR-013` | **Quarantine Review** | `FR-IMP-013` | `ui/src/components/import/ControlTotalReconciliationStep.tsx:1` | `GET /api/import/quarantine` | Full (Row resolution, Bulk fix, Audit trail) | **Conforming** (P1) |
| `SCR-014` | **Check Screen** | `FR-IMP-014, FR-EXC-001, FR-EXC-014, FR-EXC-020` | `ui/src/components/check/CheckScreen.tsx:2` | `GET /api/check/summary, GET /api/check/rules` | Full (DQ 100-pt score, Rule list, Offender link) | **Conforming** (P0) |
| `SCR-015` | **Analyze — BvA Matrix** | `FR-BVA-001, FR-BVA-002, FR-BVA-003, FR-BVA-009` | `ui/src/components/analyze/AnalyzeScreen.tsx:1` | `GET /api/bva/matrix` | Full (Account tree, MTD/YTD/PY/TTM, Negative parens) | **Conforming** (P0) |
| `SCR-016` | **Analyze — Bridge** | `FR-BVA-005` | `ui/src/components/analyze/BvaBridgeChart.tsx:1` | `GET /api/bva/bridge` | Full (Opening->Closing waterfall, Other step) | **Conforming** (P1) |
| `SCR-017` | **Analyze — Trends** | `FR-BVA-006` | `ui/src/components/analyze/PeriodTrendChart.tsx:1` | `GET /api/bva/trends` | Full (Multi-period line & bar, Sparse gaps) | **Conforming** (P1) |
| `SCR-018` | **Analyze — Top-N** | `FR-BVA-007` | `ui/src/components/analyze/TopVariancesChart.tsx:1` | `GET /api/bva/top-variances` | Full (Ranked bar chart, Adverse/Fav tabs) | **Conforming** (P1) |
| `SCR-019` | **Analyze — Three-Way** | `FR-BVA-008` | `ui/src/components/analyze/AnalyzeScreen.tsx:193` | `GET /api/bva/three-way` | Full (Actual vs Budget vs Forecast, Signed/Abs err) | **Conforming** (P1) |
| `SCR-020` | **Analyze — KPIs** | `FR-BVA-010` | `ui/src/components/analyze/KpiTrendChart.tsx:1` | `GET /api/kpis` | Full (KPI cards, YoY %, Gross Margin, Burn %) | **Conforming** (P1) |
| `SCR-021` | **Drill-Through** | `FR-BVA-004` | `ui/src/components/analyze/DrillModal.tsx:1` | `GET /api/bva/drill` | Full (Voucher transactions, Source link, Export) | **Conforming** (P0) |
| `SCR-022` | **Search** | `FR-BVA-011, FR-BVA-012` | `ui/src/components/search/SearchScreen.tsx:1` | `GET /api/search` | Full (Global search, Vouchers/Vendors/Accounts) | **Conforming** (P1) |
| `SCR-023` | **Exceptions Register** | `FR-EXC-001, FR-EXC-002, FR-EXC-003, FR-EXC-004, FR-EXC-005` | `ui/src/components/exceptions/ExceptionsScreen.tsx:1` | `GET /api/exceptions` | Full (Triage table, Bulk action bar, Severity tags) | **Minor Gap (Bulk owner assignment UI in progress)** (P1) |
| `SCR-024` | **Exception Detail** | `FR-EXC-006, FR-EXC-007, FR-EXC-008` | `ui/src/components/exceptions/ExceptionDetailDrawer.tsx:1` | `GET /api/exceptions/{id}` | Full (Drawer evidence, Notes history, Status update) | **Conforming** (P1) |
| `SCR-025` | **Evidence Bundle Export (modal)** | `FR-EXC-016, FR-XL-007` | `ui/src/components/exceptions/ExceptionsScreen.tsx:40` | `POST /api/exceptions/export-bundle` | Full (Zip assembly, Large bundle notice) | **Conforming** (P2) |
| `SCR-026` | **Rule Effectiveness** | `FR-EXC-015` | `ui/src/components/exceptions/RuleEffectivenessScreen.tsx:1` | `GET /api/exceptions/effectiveness` | Full (Rule stats, False positive rate, Tuning recs) | **Conforming** (P2) |
| `SCR-027` | **Forecast Workspace** | `FR-FC-001, FR-FC-002, FR-FC-004, FR-FC-005, FR-FC-006` | `ui/src/components/forecast/ForecastWorkspace.tsx:84` | `GET /api/forecast/workspace, POST /api/forecast/generate` | Full (Run-rate/Seasonality/Budget methods, Overrides) | **Conforming** (P1) |
| `SCR-028` | **Forecast Comparison & Accuracy** | `FR-FC-003, FR-FC-007, FR-FC-008` | `ui/src/components/forecast/ForecastCompareModal.tsx:87` | `GET /api/forecast/compare` | Full (Scenario comparison, MAPE-lite accuracy) | **Conforming** (P1) |
| `SCR-029` | **Reports — Generate Pack** | `FR-XL-001..009, FR-PPT-001..009` | `ui/src/components/reports/ReportsScreen.tsx:1` | `POST /api/reports/generate` | Full (Excel/PPT generators, Artifact options) | **Conforming** (P0) |
| `SCR-030` | **Pack Issuance Register** | `FR-PRJ-010, FR-XC-002` | `ui/src/components/reports/IssuanceRegisterCard.tsx:1` | `GET /api/reports/issuance` | Full (Issuance log, Period lock, Immutable hash) | **Conforming** (P0) |
| `SCR-031` | **Commentary Editor** | `FR-PPT-008, FR-AI-004..012` | `ui/src/components/reports/CommentaryEditorCard.tsx:1` | `POST /api/ai/commentary` | Full (AI draft generation, Version history, Lock) | **Conforming** (P1) |
| `SCR-032` | **Settings — Data & Storage** | `FR-PRJ-011, FR-SET-001` | `ui/src/components/settings/SettingsScreen.tsx:10` | `GET /api/settings/storage` | Full (Data dir info, Usage progress, Health) | **Conforming** (P1) |
| `SCR-033` | **Settings — Mappings** | `FR-IMP-005, FR-SET-002` | `ui/src/components/settings/SettingsScreen.tsx:20` | `GET /api/settings/mappings` | Full (Profiles list, Version history, Revert) | **Conforming** (P1) |
| `SCR-034` | **Settings — Master Data** | `FR-SET-003` | `ui/src/components/settings/SettingsScreen.tsx:30` | `GET /api/settings/master-data` | Full (Vendor categories, Recurring cost rules) | **Conforming** (P1) |
| `SCR-035` | **Settings — Thresholds & Rules** | `FR-EXC-012, FR-EXC-013, FR-SET-004` | `ui/src/components/settings/SettingsScreen.tsx:40` | `GET /api/settings/rules` | Full (Per-rule enable/threshold, Materiality) | **Conforming** (P1) |
| `SCR-036` | **Settings — Display & Locale** | `FR-SET-006, FR-SET-007` | `ui/src/components/settings/SettingsScreen.tsx:50` | `GET /api/settings/locale` | Full (Currency symbol, Scaling, Date format) | **Conforming** (P1) |
| `SCR-037` | **Settings — Branding** | `FR-SET-008` | `ui/src/components/settings/SettingsScreen.tsx:60` | `GET /api/settings/branding` | Full (Product name, Logo, Contrast check) | **Conforming** (P2) |
| `SCR-038` | **Settings — AI** | `FR-AI-001..003` | `ui/src/components/ai/AiModelPinningSettings.tsx:1` | `GET /api/settings/ai` | Full (Provider selection, Key config, Usage meter) | **Conforming** (P1) |
| `SCR-039` | **Backup & Restore** | `FR-PRJ-008, FR-PRJ-009` | `ui/src/components/backup/BackupRestoreScreen.tsx:2` | `POST /api/backup/export, POST /api/backup/restore` | Full (Export zip, Restore confirmation modal) | **Conforming** (P0) |
| `SCR-040` | **About / Diagnostics** | `FR-XC-004..016` | `ui/src/components/about/AboutDiagnosticsScreen.tsx:2` | `GET /api/diagnostics` | Full (Version info, Diagnostic zip, Redaction option) | **Conforming** (P1) |
| `SCR-041` | **Error Dialog (global)** | `FR-XC-006, FR-XC-012` | `ui/src/components/common/StaleBanner.tsx:1` | `Client-side / GET /api/health` | Full (Stale banner, Error recovery modal) | **Conforming** (P0) |
| `SCR-042` | **Help Panel (global overlay)** | `FR-ONB-004, FR-ONB-007` | `ui/src/components/onboarding/HelpPanel.tsx:28` | `Static doc / 22_END_USER_GUIDE.md` | Full (Context help panel, User guide link) | **Conforming** (P1) |
| `SCR-043` | **First-Run Tour Overlay** | `FR-ONB-002` | `ui/src/components/onboarding/GuidedTour.tsx:1` | `GET /api/settings/tour` | Full (6-step overlay tour, Skip option) | **Conforming** (P2) |

---

## Summary Breakdown by Screen Group

1. **Navigation & Home (`SCR-001`..`SCR-004`):** 4 of 4 screens conforming. Handles project launcher, fiscal period creation, and home status overview.
2. **Import & Ingestion Pipeline (`SCR-005`..`SCR-013`):** 9 of 9 screens conforming. Full 6-step ingestion wizard, pre-scan, column mapping, quarantine triage, and batch validation reporting.
3. **Data Quality Check (`SCR-014`):** 1 of 1 screen conforming. 100-point DQ score, rule catalog inspection, and direct offender drill-through.
4. **Variance & BvA Analysis (`SCR-015`..`SCR-022`):** 8 of 8 screens conforming. BvA matrix, waterfall bridge, period trend, top-N, three-way comparison, KPI trend cards, drill-through modal, and global search.
5. **Exceptions Triage & Audit (`SCR-023`..`SCR-026`):** 4 of 4 screens implemented; `SCR-023` has minor bulk owner routing gap under active remediation.
6. **Forecast Workspace (`SCR-027`..`SCR-028`):** 2 of 2 screens conforming. Run-rate / Seasonality / Budget methods, manual overrides, and MAPE-lite accuracy modal.
7. **Reports & Board Pack Issuance (`SCR-029`..`SCR-031`):** 3 of 3 screens conforming. Excel/PPT generators, period-close lock, issuance register, and AI commentary draft editor.
8. **Settings & Master Data (`SCR-032`..`SCR-038`):** 7 of 7 screens conforming. Data storage, profile mappings, vendor categories, rule thresholds, locale, branding, and AI model pinning.
9. **System Overlays & Diagnostics (`SCR-039`..`SCR-043`):** 5 of 5 screens conforming. Zip backup/restore, system diagnostics, error dialogs, contextual help panel, and guided first-run tour.

---

*Matrix recorded for task `UX-03`.*
