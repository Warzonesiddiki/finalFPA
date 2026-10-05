# FP&A Month-End Copilot

**FP&A Month-End Copilot** is a self-contained, offline-first Windows 11 desktop application designed for corporate finance teams. It ingests messy general ledger and operational exports (Microsoft Dynamics 365 plus auxiliary accounting systems), validates and balances them, detects accounting anomalies through an authoritative catalogue of 24 exception rules (`EXC-001` through `EXC-024`), powers budget-vs-actual (BvA) drill-down, generates rolling forecasts, and produces board-ready Excel workbooks and PowerPoint management decks.

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

- **Current Phase:** **Acceptance gate (doc 14 §5.3) — red but fully measured.** App version `0.1.0` (`pyproject.toml`).
- **Status:** Engine, API, CLI, UI and packaging waves are built; the planted-exception acceptance harness runs for real (verdict **FAIL, exit 1**: recall 11/32, extras 422 — every miss/extra classified in `evidence/acceptance_remediation_2026-10-04.md`). The sample corpus is balanced, loadable and byte-reproducible from one command. In flight: `OQ-025`…`027` decided 2026-10-05 (`DEC-056`…`058`), coherent corpus rebuild `PROP-001` approved (`DEC-059`); the real-data pilot stays blocked on client data. **`STATE.md` and `docs/16_ROADMAP_PHASES.md` §1.3 are the live records** — this section was corrected on 2026-10-05 because it claimed "Feature Complete & Verified (v1.0.0-rc2)", which was false (Addon 6 §14.3, truthfulness defect).

---

## 3. How to Open and Navigate the Documentation

All project documentation lives in the [`docs/`](docs/) directory. Start with the master index:

1. **Start Here:** Open [`docs/00_INDEX.md`](docs/00_INDEX.md) for the master document map, reading order by role, Addon Coverage Matrix, and Source-of-Truth Matrix.
2. **For Product & Scope:** Open [`docs/01_PRD.md`](docs/01_PRD.md) and [`docs/02_FUNCTIONAL_SPEC.md`](docs/02_FUNCTIONAL_SPEC.md).
3. **For Finance & Calculations:** Open [`docs/05_CALCULATION_SPEC.md`](docs/05_CALCULATION_SPEC.md) and [`docs/06_EXCEPTION_RULES_CATALOG.md`](docs/06_EXCEPTION_RULES_CATALOG.md).
4. **For Architecture & Stack:** Open [`docs/09_TECHNICAL_ARCHITECTURE.md`](docs/09_TECHNICAL_ARCHITECTURE.md) and [`docs/26_API_CONTRACT.md`](docs/26_API_CONTRACT.md).
5. **For Quality & Verification:** Open [`docs/14_TESTING_QA_PLAN.md`](docs/14_TESTING_QA_PLAN.md), [`docs/15_BUILD_RUNBOOK.md`](docs/15_BUILD_RUNBOOK.md), and [`docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md`](docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md).

---

## 4. Repository Layout

```
.
├── docs/               # Phase 0 Documentation of Record (Docs 00–30, CHANGELOG, SESSION_LOG)
├── audit/              # Independent audit artifacts, findings register, and verification logs
├── evidence/           # Phase gate evidence packs, manifests, NFR tables, and defect logs
├── sample-data/        # Realistic fictional dataset, generator, templates, and malformed corpus
├── app/                # Backend Python FastAPI engine, rule evaluators, store, and AI client
├── ui/                 # Frontend React + TypeScript + Vite application
│   └── e2e/            # Playwright E2E smoke tests
├── tests/              # Test suites, performance benchmarks, cross-artifact harness, and fixtures
│   ├── artefacts/      # Cross-artifact consistency test harness
│   └── perf/           # Performance benchmarks (250k-row rule-run tests)
├── packaging/          # PyInstaller spec, Inno Setup installer scripts, and icons
├── scripts/            # Development, test (`scripts/check`), build (`scripts/build`), and audit automation
└── scratch/            # Temporary scratch files and working logs
```

---

## 5. Quick Development & Verification Commands

- **Fast Test Suite (excluding slow perf tests):**
  ```powershell
  pytest -m "not perf"
  ```
- **Performance & Rule-Run Benchmark Suite:**
  ```powershell
  pytest -m perf
  ```
- **Full Quality Check (format + lint + type + tests):**
  ```powershell
  python scripts/check.py
  ```
- **PyInstaller Standalone Build & Payload Audit:**
  ```powershell
  python scripts/build.py
  ```

---

## 6. Advisory Disclaimer

> **ADVISORY NOTICE:** FP&A Month-End Copilot is a financial analysis and variance review aid. It does not provide certified accounting opinions, tax advice, or statutory audit assurances. All calculations, reconciliations, exceptions, and AI drafts must be reviewed and approved by a qualified finance professional before presentation to management, external auditors, or regulatory authorities.
