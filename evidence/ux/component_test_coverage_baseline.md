# UI Component Test Coverage Baseline (ENG-08)

**Date**: 2026-10-05  
**Total `.tsx` Components**: 60  
**Tested Components**: 0 (0.0%)  
**Untested Components**: 60  
**Total Component LOC**: 14,928 lines  

---

## 1. Executive Summary

In accordance with task `ENG-08`, this audit measures the front-end component inventory honestly without
masking gaps or injecting false pass assertions. Currently, 0 frontend unit/component tests exist in the
React repository (E2E workflows are tested via Python integration suites). A comprehensive component testing
harness is required to verify the interactive visual states across the screens.

---

## 2. Component Inventory & Audit Table

| Component | Relative Path | LOC | Tested? | Test Path |
|:---|:---|:---:|:---:|:---|
| `AboutDiagnosticsScreen` | `ui/src/components/about/AboutDiagnosticsScreen.tsx` | 187 | ✗ NO | — |
| `AiCommentaryScreen` | `ui/src/components/ai/AiCommentaryScreen.tsx` | 100 | ✗ NO | — |
| `AiModelPinningSettings` | `ui/src/components/ai/AiModelPinningSettings.tsx` | 161 | ✗ NO | — |
| `AiPromptTemplatesScreen` | `ui/src/components/ai/AiPromptTemplatesScreen.tsx` | 231 | ✗ NO | — |
| `AiProvenanceHistory` | `ui/src/components/ai/AiProvenanceHistory.tsx` | 209 | ✗ NO | — |
| `AiUsageDashboard` | `ui/src/components/ai/AiUsageDashboard.tsx` | 196 | ✗ NO | — |
| `AiUsageMeter` | `ui/src/components/ai/AiUsageMeter.tsx` | 51 | ✗ NO | — |
| `FollowUpMessageComposer` | `ui/src/components/ai/FollowUpMessageComposer.tsx` | 213 | ✗ NO | — |
| `AiUsageDashboard` | `ui/src/components/ai/usage/AiUsageDashboard.tsx` | 196 | ✗ NO | — |
| `AnalyzeScreen` | `ui/src/components/analyze/AnalyzeScreen.tsx` | 391 | ✗ NO | — |
| `BudgetConsumptionChart` | `ui/src/components/analyze/BudgetConsumptionChart.tsx` | 191 | ✗ NO | — |
| `BvaBridgeChart` | `ui/src/components/analyze/BvaBridgeChart.tsx` | 185 | ✗ NO | — |
| `BvaFilterBar` | `ui/src/components/analyze/BvaFilterBar.tsx` | 210 | ✗ NO | — |
| `BvaMatrixTable` | `ui/src/components/analyze/BvaMatrixTable.tsx` | 214 | ✗ NO | — |
| `DrillModal` | `ui/src/components/analyze/DrillModal.tsx` | 242 | ✗ NO | — |
| `KpiTrendChart` | `ui/src/components/analyze/KpiTrendChart.tsx` | 169 | ✗ NO | — |
| `PeriodTrendChart` | `ui/src/components/analyze/PeriodTrendChart.tsx` | 183 | ✗ NO | — |
| `StatementLineCards` | `ui/src/components/analyze/StatementLineCards.tsx` | 112 | ✗ NO | — |
| `TopVariancesChart` | `ui/src/components/analyze/TopVariancesChart.tsx` | 151 | ✗ NO | — |
| `VarianceHeatMapChart` | `ui/src/components/analyze/VarianceHeatMapChart.tsx` | 200 | ✗ NO | — |
| `BackupRestoreScreen` | `ui/src/components/backup/BackupRestoreScreen.tsx` | 247 | ✗ NO | — |
| `CheckScreen` | `ui/src/components/check/CheckScreen.tsx` | 184 | ✗ NO | — |
| `StaleBanner` | `ui/src/components/common/StaleBanner.tsx` | 84 | ✗ NO | — |
| `BulkActionBar` | `ui/src/components/exceptions/BulkActionBar.tsx` | 151 | ✗ NO | — |
| `ExceptionAgingChart` | `ui/src/components/exceptions/ExceptionAgingChart.tsx` | 125 | ✗ NO | — |
| `ExceptionDetailDrawer` | `ui/src/components/exceptions/ExceptionDetailDrawer.tsx` | 552 | ✗ NO | — |
| `ExceptionParetoChart` | `ui/src/components/exceptions/ExceptionParetoChart.tsx` | 211 | ✗ NO | — |
| `ExceptionSeverityChart` | `ui/src/components/exceptions/ExceptionSeverityChart.tsx` | 133 | ✗ NO | — |
| `ExceptionsFilterBar` | `ui/src/components/exceptions/ExceptionsFilterBar.tsx` | 296 | ✗ NO | — |
| `ExceptionsRegisterTable` | `ui/src/components/exceptions/ExceptionsRegisterTable.tsx` | 252 | ✗ NO | — |
| `ExceptionsScreen` | `ui/src/components/exceptions/ExceptionsScreen.tsx` | 453 | ✗ NO | — |
| `RuleEffectivenessScreen` | `ui/src/components/exceptions/RuleEffectivenessScreen.tsx` | 239 | ✗ NO | — |
| `ForecastAccuracyModal` | `ui/src/components/forecast/ForecastAccuracyModal.tsx` | 213 | ✗ NO | — |
| `ForecastAccuracyTrendChart` | `ui/src/components/forecast/ForecastAccuracyTrendChart.tsx` | 138 | ✗ NO | — |
| `ForecastCompareModal` | `ui/src/components/forecast/ForecastCompareModal.tsx` | 196 | ✗ NO | — |
| `ForecastScreen` | `ui/src/components/forecast/ForecastScreen.tsx` | 153 | ✗ NO | — |
| `ForecastVsActualChart` | `ui/src/components/forecast/ForecastVsActualChart.tsx` | 183 | ✗ NO | — |
| `ForecastWorkspace` | `ui/src/components/forecast/ForecastWorkspace.tsx` | 587 | ✗ NO | — |
| `ManualOverrideModal` | `ui/src/components/forecast/ManualOverrideModal.tsx` | 255 | ✗ NO | — |
| `ChooseFileStep` | `ui/src/components/import/ChooseFileStep.tsx` | 615 | ✗ NO | — |
| `ColumnMappingStep` | `ui/src/components/import/ColumnMappingStep.tsx` | 465 | ✗ NO | — |
| `CommitConfirmStep` | `ui/src/components/import/CommitConfirmStep.tsx` | 276 | ✗ NO | — |
| `ControlTotalReconciliationStep` | `ui/src/components/import/ControlTotalReconciliationStep.tsx` | 198 | ✗ NO | — |
| `ImportHistoryScreen` | `ui/src/components/import/ImportHistoryScreen.tsx` | 393 | ✗ NO | — |
| `ImportWizard` | `ui/src/components/import/ImportWizard.tsx` | 270 | ✗ NO | — |
| `PreScanModal` | `ui/src/components/import/PreScanModal.tsx` | 278 | ✗ NO | — |
| `SheetHeaderStep` | `ui/src/components/import/SheetHeaderStep.tsx` | 309 | ✗ NO | — |
| `ValidationStep` | `ui/src/components/import/ValidationStep.tsx` | 442 | ✗ NO | — |
| `GuidedTour` | `ui/src/components/onboarding/GuidedTour.tsx` | 125 | ✗ NO | — |
| `HelpPanel` | `ui/src/components/onboarding/HelpPanel.tsx` | 158 | ✗ NO | — |
| `CommentaryEditorCard` | `ui/src/components/reports/CommentaryEditorCard.tsx` | 236 | ✗ NO | — |
| `IssuanceRegisterCard` | `ui/src/components/reports/IssuanceRegisterCard.tsx` | 226 | ✗ NO | — |
| `PackGeneratorCard` | `ui/src/components/reports/PackGeneratorCard.tsx` | 135 | ✗ NO | — |
| `PackIssuanceModal` | `ui/src/components/reports/PackIssuanceModal.tsx` | 212 | ✗ NO | — |
| `PackReissueModal` | `ui/src/components/reports/PackReissueModal.tsx` | 189 | ✗ NO | — |
| `ReportsScreen` | `ui/src/components/reports/ReportsScreen.tsx` | 215 | ✗ NO | — |
| `SearchScreen` | `ui/src/components/search/SearchScreen.tsx` | 264 | ✗ NO | — |
| `PeriodLifecycleScreen` | `ui/src/components/settings/PeriodLifecycleScreen.tsx` | 496 | ✗ NO | — |
| `SettingsScreen` | `ui/src/components/settings/SettingsScreen.tsx` | 652 | ✗ NO | — |
| `main` | `ui/src/main.tsx` | 330 | ✗ NO | — |

---

## 3. Recommended Remediation & Test Harness Plan

1. Stand up Vitest + React Testing Library under `ui/` (`vitest.config.ts`).
2. Add component test scripts to `ui/package.json` (`npm run test:ui`).
3. Prioritize critical interactive components:
   - `ui/src/components/exceptions/ExceptionsRegisterTable.tsx` (sorting, filtering, actions)
   - `ui/src/components/analyze/BvaMatrixTable.tsx` (variance calculations, colour indicators)
   - `ui/src/components/import/ControlTotalReconciliationStep.tsx` (reconciliation math verification)
   - `ui/src/components/forecast/ForecastWorkspace.tsx` (scenario override handling)
