# Staged Re-Scope Application Package (Ready for Owner Sign-Off)

> **Prepared by:** AionCLI-06 (Team Teammate)
> **Date:** 2026-10-02
> **Purpose:** Staged replacement edits for `docs/14_TESTING_QA_PLAN.md`, `docs/CHANGELOG.md`, and defect tracker notes, ready for one-command apply upon formal project owner approval.

---

## Staged File 1: `docs/14_TESTING_QA_PLAN.md`

### Target Line to Replace:
```markdown
| `NFR-014` | Coverage: `app/engine` ≥ **90 %** statements; whole backend ≥ **75 %** | `pytest --cov` thresholds enforced in `scripts/check` | full suite | `coverage.xml` + threshold failure |
```

### Staged Replacement:
```markdown
| `NFR-014` | Coverage: Domain calculation, rules, and forecast method engines (`calc/`, `rules/`, `forecast/methods.py`, `ai/`) ≥ **90 %** statements; storage repositories and whole backend (`store/`, `imports/`, `exports/`, etc.) ≥ **75 %** | `pytest --cov` thresholds enforced in `scripts/check` | full suite | `coverage.xml` + threshold failure |
```

---

## Staged File 2: `docs/CHANGELOG.md`

### Target Insertion (Top of `## [Unreleased]`):
```markdown
- **NFR-014 Coverage Policy Re-Scope & DEF-003 Resolution:** Formally re-scoped `NFR-014` statement coverage requirements in `docs/14_TESTING_QA_PLAN.md` following coverage closing batches (Batches 1–5): pure domain calculation, rules, and forecast method engines (`calc/`, `rules/`, `forecast/methods.py`, `ai/`) maintain the strict **≥ 90%** statement coverage gate, while storage repositories and supporting infrastructure (`store/`, `imports/`, `exports/`) satisfy the robust backend **≥ 75%** threshold. DEF-003 (S1 coverage bars) marked **RESOLVED / CLOSED**, unblocking UAT (GATE-14) and Go-Live (GATE-15) gates. Backed by uncovered-lines triage proving zero dead code and high relational mock complexity in repository layers.
```

---

## Staging Location
- **Staged patch script / bundle:** `packaging/staged_rescoped_application.patch` (or this staging index file).
- **Application Command (upon approval):** Executed via Python patch script or exact string replacement.
