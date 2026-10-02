# FP&A Month-End Copilot

**FP&A Month-End Copilot** is a self-contained, offline-first Windows 11 desktop application designed for corporate finance teams. It ingests messy general ledger and operational exports (Microsoft Dynamics 365 plus auxiliary accounting systems), validates and balances them, detects accounting anomalies through an authoritative catalogue of 24 exception rules, powers budget-vs-actual (BvA) drill-down, generates rolling forecasts, and produces board-ready Excel workbooks and PowerPoint management decks.

---

## 1. Zero-Compromise Operating Principles

1. **Docs before code:** No product implementation until the full specification set passes its quality gates and is approved.
2. **The spec is the source of truth:** Code never drifts from specification. Any behavioral change updates the spec and changelog first.
3. **Deterministic money math:** All calculations, reconciliations, and tolerances use exact minor units (`Decimal`). AI never computes money.
4. **Offline-first, local-only data:** Zero cloud storage, zero silent telemetry, zero auto-upload. Financial data never leaves the client's laptop.
5. **Traceability:** Every figure on screen, in Excel, or in PowerPoint drills down to source transaction rows and file vouchers.
6. **Non-technical UX:** Guided wizards, self-contained Windows installer (no developer tooling/Docker prerequisites), plain-language error hints.

---

## 2. Current Project Phase

- **Current Phase:** **Phase 0 — Documentation & Specification of Record**
- **Status:** **Phase 0 documentation is ready for owner presentation.** The 70-check documentary re-audit is recorded in `evidence/2026-10-02-phase0-re-audit/`; no Phase 0 approval has been recorded.
- **Next permitted work:** Present `docs/PHASE0_SUMMARY.md`, doc `29`, doc `30`, and the evidence pack for an explicit approval or rejection. Only recorded approval may release the packaging spike (`GATE-06`).

---

## 3. How to Open and Navigate the Documentation

All project documentation lives in the [`docs/`](docs/) directory. Start with the index document:

1. **Start Here:** Open [`docs/00_INDEX.md`](docs/00_INDEX.md) for the master document map, reading order by role, Addon Coverage Matrix, and Source-of-Truth Matrix.
2. **For Product & Scope:** Open [`docs/01_PRD.md`](docs/01_PRD.md) and [`docs/02_FUNCTIONAL_SPEC.md`](docs/02_FUNCTIONAL_SPEC.md).
3. **For Finance & Calculations:** Open [`docs/05_CALCULATION_SPEC.md`](docs/05_CALCULATION_SPEC.md) and [`docs/06_EXCEPTION_RULES_CATALOG.md`](docs/06_EXCEPTION_RULES_CATALOG.md).
4. **For Architecture & Stack:** Open [`docs/09_TECHNICAL_ARCHITECTURE.md`](docs/09_TECHNICAL_ARCHITECTURE.md) and [`docs/26_API_CONTRACT.md`](docs/26_API_CONTRACT.md).
5. **For Quality & Verification:** Open [`docs/14_TESTING_QA_PLAN.md`](docs/14_TESTING_QA_PLAN.md) and [`docs/30_OWNER_OPERATING_HANDBOOK.md`](docs/30_OWNER_OPERATING_HANDBOOK.md).
6. **For Client Review:** Open [`docs/29_CLIENT_REQUIREMENTS_PACK.md`](docs/29_CLIENT_REQUIREMENTS_PACK.md).

---

## 4. Repository Layout

```
.
├── docs/               # Phase 0 Documentation of Record (Docs 00–30, CHANGELOG, SESSION_LOG)
├── audit/              # Independent audit artifacts, findings register, and verification logs
├── evidence/           # Verification logs, quality gate evidence packs, and test outputs
├── sample-data/        # Generator + instructions only; local synthetic outputs are ignored and regenerated
├── app/                # Backend Python headless engine (Phase 1+)
├── ui/                 # Frontend React + TypeScript application (Phase 1+)
├── tests/              # Test suites, contract tests, and golden fixtures (Phase 1+)
├── packaging/          # PyInstaller spec and Inno Setup installer scripts (Phase 1+)
├── scripts/            # Development, test, build, and audit automation scripts
└── scratch/            # Temporary scratch files and audit working logs
```

---

## 5. Advisory Disclaimer

> **ADVISORY NOTICE:** FP&A Month-End Copilot is a financial analysis and variance review aid. It does not provide certified accounting opinions, tax advice, or statutory audit assurances. All calculations, reconciliations, exceptions, and AI drafts must be reviewed and approved by a qualified finance professional before presentation to management, external auditors, or regulatory authorities.
