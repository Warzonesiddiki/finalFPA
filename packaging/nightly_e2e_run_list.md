# Nightly Automated E2E Run List & Execution Plan

> **Quoting Doc 14 §9 (Testing & QA Plan)**:
> *"Automated E2E suites run against local builds (FastAPI backend + React frontend) prior to phase gates and during scheduled nightly pipelines. Every suite must complete within established time budgets, produce zero console errors or unhandled page exceptions, and satisfy strict functional assertions."*

---

## 1. Execution Sequence & Order

The nightly unattended Playwright E2E pipeline executes the following 4 specifications in sequential order to ensure clean state initialization, core flow smoke testing, edge-case robustness, onboarding/help verification, and console cleanliness:

| Order | Suite Name & File | Purpose & Scope | Expected Duration | Pass Criteria |
|---|---|---|---|---|
| **1** | **Golden Path**<br>`ui/e2e/golden-path.spec.ts` (`TST-E2E-01`) | Core end-to-end user journey: app launch, sample project load, import validation, variance drill-down, exception register interaction, forecast update, and pack issuance. | ~10.5s | 100% assertions pass; exact numerical tie-outs match baseline. |
| **2** | **Error Paths**<br>`ui/e2e/error-paths.spec.ts` (`TST-E2E-04`) | Fault resilience & negative flows: malformed inputs, API timeouts, invalid operations, graceful error dialogs, and crash prevention. | ~5.8s | All expected error states handled gracefully without unhandled crashes. |
| **3** | **Tour & Help**<br>`ui/e2e/tour-help.spec.ts` (`FR-ONB-001..007`) | Onboarding tour overlay steps, Next/Skip persistence, and contextual help panel topic display across Home, Import, and Analyze tabs. | ~2.0s | Tour steps advance/skip correctly; help panels display accurate SCR reference topics. |
| **4** | **Console Audit**<br>`ui/e2e/console-audit.spec.ts` (`TST-E2E-CONSOLE`) | Runtime error monitor: asserts zero uncaught JavaScript page exceptions (`pageerror`) and zero critical console errors across full app navigation. | ~7.7s | **Zero** unhandled page exceptions and **zero** critical console errors. |

---

## 2. Pipeline Execution & Environment Configuration

- **Environment**: Headless Chromium / Playwright runner on Windows runner node.
- **Backend**: FastAPI server running locally on `http://127.0.0.1:8000` with test database fixture.
- **Frontend**: Vite preview / development server running locally on `http://localhost:5173` (or root proxied).
- **Run Command**:
  ```powershell
  cd ui
  npx playwright test golden-path.spec.ts error-paths.spec.ts tour-help.spec.ts console-audit.spec.ts --reporter=dot
  ```
- **Total Expected Suite Duration**: **~26.0 seconds**.

---

## 3. Failure & Alert Protocol

1. **Gate Blocking**: Any test failure in the nightly E2E run automatically blocks deployment and phase gate sign-off (`GATE-13`, `GATE-14`, `GATE-15`).
2. **Artifact Capture**: Playwright traces, screenshots, and console logs are automatically captured on failure for triage.
3. **Regression Logging**: Regressions are filed against the responsible component owner per `docs/18` and `docs/14`.
