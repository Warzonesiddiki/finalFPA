# Nightly Automated E2E Runbook & Triage Guide

> **Quoting Nightly E2E Run List (`packaging/nightly_e2e_run_list.md`)**:
> *"Automated E2E suites run against local builds (FastAPI backend + React frontend) prior to phase gates and during scheduled nightly pipelines. Every suite must complete within established time budgets, produce zero console errors or unhandled page exceptions, and satisfy strict functional assertions."*

---

## 1. Scope & Execution Order

The nightly runbook governs unattended automated execution of the 4 core Playwright E2E suites:

1. **Golden Path** (`ui/e2e/golden-path.spec.ts`) — Duration: ~10.5s
2. **Error Paths** (`ui/e2e/error-paths.spec.ts`) — Duration: ~5.8s
3. **Tour & Help** (`ui/e2e/tour-help.spec.ts`) — Duration: ~2.0s
4. **Console Audit** (`ui/e2e/console-audit.spec.ts`) — Duration: ~7.7s

**Total Expected Duration**: **~26.0 seconds**.

---

## 2. Execution Commands & Prerequisites

### Prerequisites
- Python 3.10+ virtual environment activated with backend dependencies installed.
- Node.js 18+ and Playwright browsers installed (`npx playwright install`).

### Full Execution Command
```powershell
cd ui
npx playwright test golden-path.spec.ts error-paths.spec.ts tour-help.spec.ts console-audit.spec.ts --reporter=dot
```

---

## 3. Pass Criteria & Gates

- **100% Test Success**: All specs must return `passed`.
- **Zero Console Errors / Page Exceptions**: `console-audit.spec.ts` must verify zero uncaught JavaScript page exceptions (`pageerror`) and zero critical console errors (`console` error level excluding expected 404/400 API fault tests).
- **Gate Blocking**: Any failure immediately blocks release gates (`GATE-13`, `GATE-14`, `GATE-15`).

---

## 4. Failure Triage & Troubleshooting Guide

### Flaky vs. Real Failures
- **Flaky Failure**: Intermittent network timeout or port binding conflict (e.g. port 8000 already in use). Check if a previous backend process is lingering (`Get-Process python`).
- **Real Failure**: Functional assertion failure (e.g., missing element, unexpected error envelope code, console error). Inspect captured trace and screenshot artefacts.

### Log Locations & Artefacts
- **Playwright Test Results**: `ui/test-results/`
- **Playwright HTML Report**: `ui/playwright-report/`
- **Backend Diagnostic Logs**: Captured via FastAPI stdout/stderr during test runs or `%LOCALAPPDATA%/FP&A Month-End Copilot/Logs/`.
