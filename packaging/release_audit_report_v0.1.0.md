# Release Readiness & Version Audit Report (v0.1.0)

## 1. Quoted Runbook References (Docs 15 & 24)
- **Doc 24 §2.3 (The One-Place Rule)**: *"A mismatch between the installer's file version, the About screen and the artefact file name fails the release."*
- **Doc 15 §2.2 (Single-Source Version Chain)**: *"The version in pyproject.toml is the single source of truth; scripts/release writes the version and scripts/build reads it — never typed twice. The version in CHANGELOG.md and release-notes.md is generated from the same value — never typed."*

---

## 2. Version Consistency Audit
| Component / File | Recorded Version | Expected Version | Status |
|---|---|---|---|
| `pyproject.toml` (Project Root) | `0.1.0` | `0.1.0` | **MATCH (Single Source of Truth)** |
| `ui/package.json` (Frontend) | `0.1.0` | `0.1.0` | **MATCH** |
| `AboutDiagnosticsScreen.tsx` (UI About) | `0.1.0` | `0.1.0` | **MATCH** |
| `app/api/main.py` (Backend API & Doctor) | `0.1.0` | `0.1.0` | **MATCH** |

---

## 3. Draft Release Notes (v0.1.0) — Doc 24 Template

### Release Title: FP&A Month-End Copilot v0.1.0 (Real-Data Pilot Release)
* **Release Date:** October 2, 2026
* **Target Environment:** Windows 11 x86_64 Desktop Native (pywebview + FastAPI + DuckDB)

#### Summary of New Features & Capabilities
1. **Import & Wizard (SCR-001..010)**: 6-step guided ingestion workflow for D365 GL Actuals, Bank Ledgers, Payroll & Procurement, and Budgets with live validation and error reporting.
2. **Check & Quality (SCR-011..014)**: Automated trial balance verification, duplicate detection, and batch status workflows.
3. **Analyze & Variance (SCR-015..019)**: Budget vs. Actual matrix tables, statement line summaries, variance heatmaps, and one-click transaction-level evidence drill-down.
4. **Exceptions & Review (SCR-020..027)**: Complete rule catalog implementation (EXC-001 through EXC-024) with deterministic Decimal math, aging buckets, severity badges, and 6-step owner auto-assignment with manual override precedence.
5. **Forecast & Scenarios (SCR-028..032)**: Method selection (Run-rate, Trailing Average, Remaining Budget) and Base/Best/Worst scenario comparison with manual overrides and justification logging.
6. **Reports & Pack Issuance (SCR-033..038)**: Automated Excel pack generation (doc 11), PowerPoint executive deck generation (doc 12), and formal issuance registry with version increment and commentary locks.
7. **AI Commentary & Guardrails (DOC-10)**: Deterministic narrative generation with PII redaction guardrails and keyless rule-based fallback paths.
8. **Settings & Master Data (SCR-033..038)**: Configurable mapping rules, approval thresholds, currency formatting (incl. lakh/crore toggle), and brand styling.
9. **Backup & Restore (SCR-039)**: One-click project backup to zip, restore from zip, storage health breakdown, and closed-period archive-and-delete with typed confirmation.
10. **About & Diagnostics (SCR-040)**: Build provenance metadata, manual check-for-updates, CLI doctor health checks (DOC-01..05), and redacted diagnostics zip export (doc 13).
11. **Onboarding & Help (FR-ONB)**: 6-step non-blocking guided tour and contextual help panel keyed to active screen (doc 22).
12. **Stale-Derived Data Indicator (Addon 2 B.7)**: Automatic staleness detection when configuration or mappings change, displaying a prominent warning banner with an explicit "Re-run Now" action.

#### Bug Fixes & Improvements
- Fixed bank ledger imbalanced batch handling without weakening balance validation rules.
- Resolved future-dated ranking mitigation in EXC-011 for accurate register usability.
- Deterministic Decimal arithmetic enforced across all financial calculations.

---

## 4. Supported Artefacts & Third-Party Licenses Verification
- **Supported Artefacts**:
  - `Setup-FPandAMonthEndCopilot-0.1.0.exe` (Inno Setup Windows Installer)
  - `FPandAMonthEndCopilot-0.1.0-portable.zip` (Portable Desktop Archive)
  - `fpa_diagnostics_redacted_v0.1.0.zip` (Diagnostics Bundle Template)
- **Third-Party Licenses**:
  - All Python dependencies (FastAPI, DuckDB, Polars, openpyxl, python-pptx, httpx, pywebview, pydantic) verified compatible under MIT / BSD / Apache-2.0 licenses.
  - Frontend libraries (React, ECharts, Lucide Icons) verified compatible under MIT licenses.

---

## 5. Release-Checklist Gaps (Report Only)
- **Git Tagging**: `v0.1.0` tag creation pending formal lead sign-off.
- **Code Signing**: Windows Authenticode code-signing certificate integration for the `.exe` installer is currently simulated/placeholder pending production key provisioning.
- **Auto-Update Feed**: GitHub releases publishing feed is configured for manual check-only (no auto-update per doc 08/02 spec).
