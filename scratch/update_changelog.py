changelog_wave2_entry = """### Phase 0 — Documentation & Wave 2 Remediation (Complete)

#### Added — 2026-10-01 (Wave 2 Remediation)

- **`docs/30_DOCUMENTATION_SET_REVIEW_GUIDE.md`** (Draft v0.1) — Added Doc 30 satisfying Addon 5 requirements: 5-minute pre-flight checklist, session-report standard, 3-level evidence ladder, 5-tier red-flag ladder, implementability sampling protocol, and single-source oracle procedure (`F-002`).
- **`sample-data/` suite & negative corpus** — Generated complete synthetic data suite: `d365_gl_actuals.csv` (10,000 rows with 6,000 P&L + 4,000 Balance Sheet), `bank_ledger_actuals.csv` (1,200 rows), `payroll_procurement_actuals.csv` (600 rows), `budget_fy26.csv` (1,500 rows), all 3 `.xlsx` mapping templates, 16 negative test corpus files in `sample-data/malformed/`, and `sample-data/expected_exceptions.csv` with 40 plantings (32 expected raises + 8 controls). Satisfies `GATE-04-02` and `GATE-04-07` (`F-003`).
- **Repo skeleton and root `README.md`** — Provisioned full repository skeleton directories (`app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/`, `evidence/`, `scratch/` with `.gitkeep` files) and expanded root `README.md` into comprehensive project guide (`F-004`).
- **Canonical Divergence Notice** — Integrated Addon 5 §A.4 Divergence Notice into `docs/19_VIBE_CODING_PLAYBOOK.md` §5.5 and `docs/00_INDEX.md` §6.3 (`F-010`).
- **Quality Gate 6 & Gate closure** — Formally incorporated Subsection 15.6 `GATE-06` (Addon 5-M deltas, 8 checks) into `docs/14_TESTING_QA_PLAN.md`. Flipped all open checks in `GATE-01` (`GATE-01-06`) and `GATE-04` (`GATE-04-02`, `GATE-04-07`) to `✅`. Total gate status across all 6 gates is now 66 / 66 ✅ (100% PASS) (`F-006`).

#### Changed — 2026-10-01 (Wave 2 Remediation)

- **`docs/13`–`29`, `PHASE0_SUMMARY.md`** — Condensed TL;DR sections across all 18 violating documents to strictly 6 lines each, ensuring zero documents exceed the 15-line limit (`F-008`).
- **`docs/00_INDEX.md`** — Added Addon 5 coverage matrix (8 rows, all `INTEGRATED`), updated doc map to 31 documents (`00`–`30`), resolved older `IN PROGRESS` rows (`K-S2`, `K-S5`, `A1-O`) to `INTEGRATED`, updated Gate Tracker to 6 gates (66 checks all green) (`F-001`, `F-007`).
- **`docs/PHASE0_SUMMARY.md`** — Updated document count to 31 documents (`00`–`30`), removed deferral text for `sample-data/`, and updated gate snapshot to 66/66 ✅ (`F-009`).
- **Workspace & Scratch** — Reorganized temporary audit and generation utilities into `scratch/` (`F-012`).

"""

with open('docs/CHANGELOG.md', 'r', encoding='utf-8') as f:
    cl_text = f.read()

target = "### Phase 0 — Documentation (in progress)\n\n#### Added — 2026-10-01"
assert target in cl_text, "Target anchor in CHANGELOG.md not found"
new_cl_text = cl_text.replace(target, changelog_wave2_entry + target, 1)

# Also update the Approval records table at the bottom of CHANGELOG.md
old_approval_table = """| Gate | Recorded approval | Date |
|---|---|---|
| Phase 0 (docs `00`–`29` + all five quality gates) | *awaiting request* | — |
| Packaging spike | *not started* | — |
| Phase gates 1–6 | *not started* | — |
| Real-data pilot | *not started* | — |
| UAT | *not started* | — |
| Go-live | *not started* | — |"""

new_approval_table = """| Gate | Recorded approval | Date |
|---|---|---|
| Phase 0 (docs `00`–`30` + all six quality gates, 66/66 green) | *awaiting recorded approval* | — |
| Packaging spike (`GATE-07`) | *not started* | — |
| Phase gates 1–6 (`GATE-08`–`12`) | *not started* | — |
| Real-data pilot (`GATE-13`) | *not started* | — |
| UAT (`GATE-14`) | *not started* | — |
| Go-live (`GATE-15`) | *not started* | — |"""

assert old_approval_table in new_cl_text, "Old approval table not found in CHANGELOG.md"
new_cl_text = new_cl_text.replace(old_approval_table, new_approval_table)

with open('docs/CHANGELOG.md', 'w', encoding='utf-8') as f:
    f.write(new_cl_text)

print("docs/CHANGELOG.md updated successfully.")
