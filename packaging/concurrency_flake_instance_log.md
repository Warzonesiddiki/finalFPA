# Concurrency & Flake Instance Log (Playbook Appendix)

**Date**: 2026-10-02  
**Task**: Flake instance log (#01a0fdc7-a64c-7d90-b132-51eb59575d05)  
**Spec Reference**: `docs/14_TESTING_QA_PLAN.md` & `docs/SESSION_LOG.md` (Multi-agent concurrency and test reliability standards).  

---

## 1. Executive Summary
During the multi-agent parallel development and rigorous testing wave of the FP&A Month-End Copilot, several intermittent failure modes ("flakes"), concurrency bottlenecks, and test synchronization friction points were encountered. 

This log documents each flake instance, its root cause, the remediation applied, and permanent prevention protocols. It serves as the official concurrency appendix to the engineering operations playbook.

---

## 2. Flake Instance Log & Friction Point Analysis

| # | Flake Category | Description & Symptom | Root Cause | Fix / Remediation | Prevention Protocol |
|---|---|---|---|---|---|
| **1** | **Shared-DB Lock Contention** | Integration tests failing intermittently with DuckDB `IO Error: Could not set lock on file` / exclusive lock conflicts. | Multiple concurrent integration test modules attempting to open and write to the same default filesystem database path (`final_fpa.duckdb`). | Implemented hermetic test isolation via an `autouse` pytest fixture redirecting `DEFAULT_PROJECT_DIR` and `DatabaseManager` to `tmp_path` per test. | Enforce `tmp_path` fixtures for all test suites interacting with persistent DuckDB instances. Never share default DB files across tests. |
| **2** | **TypeScript / Vite Build Race** | Frontend `tsc` compilation or Vite packaging errors during rapid parallel code updates. | Concurrent multi-agent edits to React components (`ui/src`) while test runners or background builds read partial/uncompiled files. | Implemented sequential verification (`tsc --noEmit && vite build`) and ensured clean build states prior to test execution. | Require atomic file edits, separate build directories, and pre-bundling validation checks. |
| **3** | **API Error Envelope Mismatches** | Contract integration tests failing on 4xx/5xx responses returning raw `detail=str` instead of standardized error envelopes. | Endpoints raising raw `HTTPException` without central exception mapping to `docs/26_API_CONTRACT.md` §5. | Added universal FastAPI exception handlers mapping status codes to error catalog families (`VAL`, `BVA`, `FC`, `RUL`, `STO`, `AI`, `IMP`). | Mandate central exception handling; enforce automated contract test runs (`tests/integration/test_error_envelope.py`) on all API changes. |
| **4** | **Mid-Edit Reads & File Stale Sync** | Test assertions or agent edits reading outdated file states during parallel task execution. | Asynchronous multi-agent reads occurring while another agent was actively writing updates to documentation or test fixtures. | Enforced strict tool execution discipline: **always Read before Edit**; verify file hashes and content before applying diffs. | Strict adherence to platform protocol: never edit without prior Read; utilize atomic Write/Edit operations. |
| **5** | **Test Order-Dependence / State Leakage** | Tests failing when executed in random order (`pytest --random-order`) but passing sequentially. | Tests relying on shared singleton states, global configuration objects, or pre-existing fixture data in the default data store. | Isolated test state setup/teardown, purged global caches between test cases, and used independent temporary workspace fixtures. | Require zero test inter-dependency; run CI/CD test suites with random execution ordering enabled. |

---

## 3. Quoted Session Friction Points & Learnings
> *"Recurring pain: integration tests share the real default project DuckDB (exclusive lock) making runs order-dependent and flaky under concurrency... Implemented hermetic isolation: autouse fixture redirecting DEFAULT_PROJECT_DIR/DatabaseManager to tmp_path per test... Full suite must pass in one run plus a concurrent double-run proving no lock contention."*
> — **Engineering Session 009 Log & Concurrency Retrospective**

---

## 4. Operational Prevention Guidelines
1. **Hermetic Test Environments**: No test may touch production or default user data directories. All tests must operate within isolated temporary directories (`tmp_path`).
2. **Centralized Exception Boundaries**: All HTTP exceptions must flow through the central envelope handler (`app/api/main.py`) to guarantee uniform JSON envelope structure (`code`, `userMessage`, `hint`).
3. **Atomic File Protocols**: Agents must execute Read operations immediately prior to applying Edit diffs to prevent mid-edit race conditions.
4. **Pre-Commit Verification**: Run full unit, integration, and type-check verification suites prior to tagging build artefacts or issuing release sign-offs.
