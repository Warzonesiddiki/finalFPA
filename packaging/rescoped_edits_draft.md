# Re-Scope Edits Draft (For Owner Approval)

> **Prepared by:** AionCLI-06 (Team Teammate)
> **Date:** 2026-10-02
> **Purpose:** Draft spec edits for `docs/14_TESTING_QA_PLAN.md` and `docs/CHANGELOG.md` implementing the re-scope of `NFR-014` (pure domain calculation, rules, and forecast methods maintain ≥ 90% statement coverage; storage repository and import layers satisfy the backend ≥ 75% threshold).

---

## 1. Draft Edits for `docs/14_TESTING_QA_PLAN.md`

### Current Text (Line 92):
```markdown
| `NFR-014` | Coverage: `app/engine` ≥ **90 %** statements; whole backend ≥ **75 %** | `pytest --cov` thresholds enforced in `scripts/check` | full suite | `coverage.xml` + threshold failure |
```

### Proposed Replacement Text:
```markdown
| `NFR-014` | Coverage: Domain calculation, rules, and forecast method engines (`calc/`, `rules/`, `forecast/methods.py`, `ai/`) ≥ **90 %** statements; storage repositories and whole backend (`store/`, `imports/`, `exports/`, etc.) ≥ **75 %** | `pytest --cov` thresholds enforced in `scripts/check` | full suite | `coverage.xml` + threshold failure |
```

---

## 2. Draft Edits for `docs/CHANGELOG.md`

### Current Text (Under `## [Unreleased]` or new session entry):
*(N/A - new entry)*

### Proposed Addition to `docs/CHANGELOG.md` (Under `## [Unreleased]` or Session log):
```markdown
- **NFR-014 Coverage Policy Re-Scope:** Formally re-scoped `NFR-014` statement coverage requirements in `docs/14_TESTING_QA_PLAN.md` following coverage closing batches (Batches 1–5): pure domain calculation, rules, and forecast method engines (`calc/`, `rules/`, `forecast/methods.py`, `ai/`) maintain the strict **≥ 90%** statement coverage gate, while storage repositories and supporting infrastructure (`store/`, `imports/`, `exports/`) satisfy the robust backend **≥ 75%** threshold. Backed by uncovered-lines triage proving zero dead code and high relational mock complexity in repository layers.
```

---
*Status:* **READY FOR OWNER APPROVAL** (No files have been modified; awaiting explicit project owner sign-off).
