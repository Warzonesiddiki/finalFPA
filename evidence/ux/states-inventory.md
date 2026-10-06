# Five-State UI & API Error Boundary Inventory (UX-04)

> **Task Reference:** `UX-04` (P1)  
> **Governing Spec:** `docs/08_UI_UX_SPEC.md` §15 (Screen State Matrix) & `docs/26_API_CONTRACT.md`  
> **Target Evidence Path:** `evidence/ux/states-inventory.md`  
> **Target Review Path (for Handoff):** `team/reviews/states-inventory.md`  
> **Date:** 2026-10-05  

---

## Executive Summary

This audit inventories the five foundational UI states (Normal, Empty, Loading, Error, Permission/Auth) across the 43 product screens, mapping them to their declared API endpoints (`docs/26_API_CONTRACT.md`).

**Finding:** 41 of the 43 screens consume network API endpoints without implementing React Suspense/ErrorBoundary boundaries for Empty or Error states. A user experiencing a 500 error from the backend or viewing an empty dataset will see a blank or broken layout instead of a standardized recovery state.

---

## 43-Screen State Inventory

| SCR ID | Screen Name | API Endpoints Called | Loading State Defined | Empty State Defined | Error State Defined | Expected API Error Codes | Implementation Defect |
|---|---|---|---|---|---|---|---|
| `SCR-001` | **Home** | `GET /api/periods/current, GET /api/health` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-002` | **Project Launcher (modal)** | `GET /api/projects` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-003` | **New Project Wizard** | `POST /api/projects` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-004` | **New Period Wizard** | `POST /api/periods` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-005` | **Import Step 1 — Choose File** | `POST /api/import/upload` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-006` | **Import Step 2 — Pre-scan** | `POST /api/import/prescan` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-007` | **Import Step 3 — Sheet & Header** | `POST /api/import/headers` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-008` | **Import Step 4 — Map Columns** | `POST /api/import/mappings` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-009` | **Import Step 5 — Validate** | `POST /api/import/validate` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-010` | **Import Step 6 — Commit & Confirm** | `POST /api/import/commit` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-011` | **Import History** | `GET /api/import/batches` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-012` | **Batch Detail / Validation Report** | `GET /api/import/batches/{id}/report` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-013` | **Quarantine Review** | `GET /api/import/quarantine` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-014` | **Check Screen** | `GET /api/check/summary, GET /api/check/rules` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-015` | **Analyze — BvA Matrix** | `GET /api/bva/matrix` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-016` | **Analyze — Bridge** | `GET /api/bva/bridge` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-017` | **Analyze — Trends** | `GET /api/bva/trends` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-018` | **Analyze — Top-N** | `GET /api/bva/top-variances` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-019` | **Analyze — Three-Way** | `GET /api/bva/three-way` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-020` | **Analyze — KPIs** | `GET /api/kpis` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-021` | **Drill-Through** | `GET /api/bva/drill` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-022` | **Search** | `GET /api/search` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-023` | **Exceptions Register** | `GET /api/exceptions` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-024` | **Exception Detail** | `GET /api/exceptions/{id}` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-025` | **Evidence Bundle Export (modal)** | `POST /api/exceptions/export-bundle` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-026` | **Rule Effectiveness** | `GET /api/exceptions/effectiveness` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-027` | **Forecast Workspace** | `GET /api/forecast/workspace, POST /api/forecast/generate` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-028` | **Forecast Comparison & Accuracy** | `GET /api/forecast/compare` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-029` | **Reports — Generate Pack** | `POST /api/reports/generate` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-030` | **Pack Issuance Register** | `GET /api/reports/issuance` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-031` | **Commentary Editor** | `POST /api/ai/commentary` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-032` | **Settings — Data & Storage** | `GET /api/settings/storage` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-033` | **Settings — Mappings** | `GET /api/settings/mappings` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-034` | **Settings — Master Data** | `GET /api/settings/master-data` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-035` | **Settings — Thresholds & Rules** | `GET /api/settings/rules` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-036` | **Settings — Display & Locale** | `GET /api/settings/locale` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-037` | **Settings — Branding** | `GET /api/settings/branding` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-038` | **Settings — AI** | `GET /api/settings/ai` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-039` | **Backup & Restore** | `POST /api/backup/export, POST /api/backup/restore` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-040` | **About / Diagnostics** | `GET /api/diagnostics` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |
| `SCR-041` | **Error Dialog (global)** | `Client-side / GET /api/health` | N/A | N/A | N/A | None |  |
| `SCR-042` | **Help Panel (global overlay)** | `Static doc / 22_END_USER_GUIDE.md` | N/A | N/A | N/A | None |  |
| `SCR-043` | **First-Run Tour Overlay** | `GET /api/settings/tour` | Yes | Yes | Yes | Standard 400/404/500 Envelope | **DEFECT: No Empty/Error boundary in React code** |

---
*Report generated by `scripts/audit_ui_states.py` for task `UX-04`.*