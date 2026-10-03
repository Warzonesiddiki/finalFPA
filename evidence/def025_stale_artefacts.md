# DEF-025 Stale Artefact Sweep & Hygiene Report

**Author:** AionCLI-09  
**Date:** 2026-10-03  
**Status:** Completed  
**Scope:** Read-only scan of compiled bytecode `.pyc` orphans under `__pycache__` and cross-reference check against the documentation set (`docs/*.md`).

---

## 1. Executive Summary

Following a report where a missing test source file (`tests/unit/test_000_meta_vacuous.py`) was referenced while only its compiled `.pyc` artefact survived in `__pycache__`, a repository-wide sweep was conducted to identify all orphaned `.pyc` files whose `.py` source no longer exists.

- **Total `.pyc` orphans found:** 81
- **Broken document citations pointing to orphaned source files:** **0**
- **Recommended Hygiene Rule:** Implement a check in `scripts/check.py` or a maintenance script that detects compiled bytecode artefacts lacking their corresponding source files.

---

## 2. Orphaned Bytecode Analysis

Python compiles modules into `.pyc` bytecode files stored in `__pycache__` directories (e.g., `test_000_meta_vacuous.cpython-314-pytest-9.1.1.pyc`). When test or application source files are deleted or renamed during refactoring, the corresponding `.pyc` files often remain intact unless explicitly cleaned.

Our sweep identified **81 orphaned `.pyc` files** across `tests/`, `tests/unit/`, `tests/uat/`, `tests/rules/`, `tests/perf/`, `tests/integration/`, and `tests/artefacts/`.

Examples of detected orphans:
1. `tests/unit/__pycache__/test_000_meta_vacuous.cpython-314-pytest-9.1.1.pyc` -> missing source `tests/unit/test_000_meta_vacuous.py`
2. `tests/unit/__pycache__/test_def013_guard_vacuous_asserts.cpython-314-pytest-9.1.1.pyc` -> missing source `tests/unit/test_def013_guard_vacuous_asserts.py`
3. `tests/integration/__pycache__/test_api.cpython-314-pytest-9.1.1.pyc` -> missing source `tests/integration/test_api.py`

---

## 3. Documentation Citation Check

Every detected orphan filename (e.g., `test_000_meta_vacuous.py`, `test_api.py`, etc.) was searched across all Markdown files in `docs/*.md`.

- **Result:** **0 broken citations found.**
- No official documentation file references the deleted or orphaned source filenames directly in a manner that creates a dangling link or phantom reference.

---

## 4. Recommended Hygiene Rule

To prevent stale bytecode confusion during audits and local test runs, we recommend one of the following hygiene mechanisms:

**Recommendation: Add a bytecode staleness / orphan validation step to `scripts/check.py`.**
- **Rule:** A script/check that walks the repository, locates any `.pyc` file in a `__pycache__` directory, and asserts that the corresponding `.py` source file exists in the parent directory.
- **Action:** If an orphan is found, print a warning or fail in strict mode.
- **Constraint:** Per session constraints, `.pyc` files are **not** deleted automatically during test execution to prevent interfering with active parallel test runs by other teammates, but flagging them ensures codebase hygiene.

---
*Signed, AionCLI-09*
