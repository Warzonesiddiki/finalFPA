# Screen-to-Code Traceability Matrix (UX-15)

> **Task Reference:** `UX-15` (P1)  
> **Governing Spec:** `docs/08_UI_UX_SPEC.md` §4  
> **Target Evidence Path:** `evidence/ux/screen-to-code.md`  
> **Target Review Path (for Handoff):** `team/reviews/screen-to-code.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

This matrix bridges the spec inventory (`08` §4) to the source tree (`ui/src/`) and testing layer (`tests/`). Any screen without a physical component file or an automated test represents a structural verification gap.

### Audit Results
- **Screens Implemented in Code:** 43 of 43
- **Screens Missing Component Files:** 0 of 43
- **Screens with Zero Test Coverage:** 36 of 43

#### Unverified Screens (Zero Tests)
`SCR-002`, `SCR-003`, `SCR-004`, `SCR-005`, `SCR-006`, `SCR-007`, `SCR-008`, `SCR-009`, `SCR-010`, `SCR-011`, `SCR-012`, `SCR-013`, `SCR-014`, `SCR-015`, `SCR-016`, `SCR-017`, `SCR-018`, `SCR-019`, `SCR-020`, `SCR-021`, `SCR-022`, `SCR-024`, `SCR-025`, `SCR-026`, `SCR-027`, `SCR-032`, `SCR-033`, `SCR-034`, `SCR-035`, `SCR-036`, `SCR-037`, `SCR-038`, `SCR-039`, `SCR-040`, `SCR-042`, `SCR-043`

---

## Grounding Matrix

| SCR ID | Screen Name | Implementing Component | Test Verifications |
|---|---|---|---|
| `SCR-001` | **Home** | `ui/src/main.tsx:145` | `tests/integration/test_e2e_golden_path.py::test_e2e_golden_path_smoke_journey`<br>`tests/unit/test_open_cited_lines.py::test_only_key_value_backticks_become_claims`<br>`tests/unit/test_open_cited_lines.py::test_cited_but_nothing_checked_is_not_a_pass` |
| `SCR-002` | **Project Launcher (modal)** | `ui/src/main.tsx:114` | **DEFECT: No test covers this screen.** |
| `SCR-003` | **New Project Wizard** | `ui/src/main.tsx:115` | **DEFECT: No test covers this screen.** |
| `SCR-004` | **New Period Wizard** | `ui/src/components/settings/PeriodLifecycleScreen.tsx:40` | **DEFECT: No test covers this screen.** |
| `SCR-005` | **Import Step 1 — Choose File** | `ui/src/components/import/ChooseFileStep.tsx:216` | **DEFECT: No test covers this screen.** |
| `SCR-006` | **Import Step 2 — Pre-scan** | `ui/src/components/import/PreScanModal.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-007` | **Import Step 3 — Sheet & Header** | `ui/src/components/import/SheetHeaderStep.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-008` | **Import Step 4 — Map Columns** | `ui/src/components/import/ColumnMappingStep.tsx:95` | **DEFECT: No test covers this screen.** |
| `SCR-009` | **Import Step 5 — Validate** | `ui/src/components/import/ValidationStep.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-010` | **Import Step 6 — Commit & Confirm** | `ui/src/components/import/CommitConfirmStep.tsx:29` | **DEFECT: No test covers this screen.** |
| `SCR-011` | **Import History** | `ui/src/components/import/ImportHistoryScreen.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-012` | **Batch Detail / Validation Report** | `ui/src/components/import/CommitConfirmStep.tsx:250` | **DEFECT: No test covers this screen.** |
| `SCR-013` | **Quarantine Review** | `ui/src/components/import/ControlTotalReconciliationStep.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-014` | **Check Screen** | `ui/src/components/check/CheckScreen.tsx:2` | **DEFECT: No test covers this screen.** |
| `SCR-015` | **Analyze — BvA Matrix** | `ui/src/components/analyze/AnalyzeScreen.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-016` | **Analyze — Bridge** | `ui/src/components/analyze/BvaBridgeChart.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-017` | **Analyze — Trends** | `ui/src/components/analyze/PeriodTrendChart.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-018` | **Analyze — Top-N** | `ui/src/components/analyze/TopVariancesChart.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-019` | **Analyze — Three-Way** | `ui/src/components/analyze/AnalyzeScreen.tsx:193` | **DEFECT: No test covers this screen.** |
| `SCR-020` | **Analyze — KPIs** | `ui/src/components/analyze/KpiTrendChart.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-021` | **Drill-Through** | `ui/src/components/analyze/DrillModal.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-022` | **Search** | `ui/src/components/search/SearchScreen.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-023` | **Exceptions Register** | `ui/src/components/exceptions/ExceptionsScreen.tsx:1` | `tests/integration/test_e2e_golden_path.py::test_e2e_golden_path_smoke_journey` |
| `SCR-024` | **Exception Detail** | `ui/src/components/exceptions/ExceptionDetailDrawer.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-025` | **Evidence Bundle Export (modal)** | `ui/src/components/exceptions/ExceptionsScreen.tsx:40` | **DEFECT: No test covers this screen.** |
| `SCR-026` | **Rule Effectiveness** | `ui/src/components/exceptions/RuleEffectivenessScreen.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-027` | **Forecast Workspace** | `ui/src/components/forecast/ForecastWorkspace.tsx:84` | **DEFECT: No test covers this screen.** |
| `SCR-028` | **Forecast Comparison & Accuracy** | `ui/src/components/forecast/ForecastCompareModal.tsx:87` | `tests/integration/test_api.py::test_forecast_endpoints_workflow` |
| `SCR-029` | **Reports — Generate Pack** | `ui/src/components/reports/ReportsScreen.tsx:1` | `tests/integration/test_e2e_golden_path.py::test_e2e_golden_path_smoke_journey` |
| `SCR-030` | **Pack Issuance Register** | `ui/src/components/reports/IssuanceRegisterCard.tsx:1` | `tests/integration/test_api.py::test_reports_and_issuance_workflow` |
| `SCR-031` | **Commentary Editor** | `ui/src/components/reports/CommentaryEditorCard.tsx:1` | `tests/integration/test_e2e_golden_path.py::test_e2e_golden_path_smoke_journey` |
| `SCR-032` | **Settings — Data & Storage** | `ui/src/components/settings/SettingsScreen.tsx:10` | **DEFECT: No test covers this screen.** |
| `SCR-033` | **Settings — Mappings** | `ui/src/components/settings/SettingsScreen.tsx:20` | **DEFECT: No test covers this screen.** |
| `SCR-034` | **Settings — Master Data** | `ui/src/components/settings/SettingsScreen.tsx:30` | **DEFECT: No test covers this screen.** |
| `SCR-035` | **Settings — Thresholds & Rules** | `ui/src/components/settings/SettingsScreen.tsx:40` | **DEFECT: No test covers this screen.** |
| `SCR-036` | **Settings — Display & Locale** | `ui/src/components/settings/SettingsScreen.tsx:50` | **DEFECT: No test covers this screen.** |
| `SCR-037` | **Settings — Branding** | `ui/src/components/settings/SettingsScreen.tsx:60` | **DEFECT: No test covers this screen.** |
| `SCR-038` | **Settings — AI** | `ui/src/components/ai/AiModelPinningSettings.tsx:1` | **DEFECT: No test covers this screen.** |
| `SCR-039` | **Backup & Restore** | `ui/src/components/backup/BackupRestoreScreen.tsx:2` | **DEFECT: No test covers this screen.** |
| `SCR-040` | **About / Diagnostics** | `ui/src/components/about/AboutDiagnosticsScreen.tsx:2` | **DEFECT: No test covers this screen.** |
| `SCR-041` | **Error Dialog (global)** | `ui/src/components/common/StaleBanner.tsx:1` | `tests/integration/test_error_catalog.py::unknown format` |
| `SCR-042` | **Help Panel (global overlay)** | `ui/src/components/onboarding/HelpPanel.tsx:28` | **DEFECT: No test covers this screen.** |
| `SCR-043` | **First-Run Tour Overlay** | `ui/src/components/onboarding/GuidedTour.tsx:1` | **DEFECT: No test covers this screen.** |

---
*Report generated by `scripts/ground_screen_matrix.py` for task `UX-15`.*
