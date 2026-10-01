# SESSION LOG

Append-only memory bridge between sessions (Addon 1 §M.1, Addon 4 §B.4). Newest entry at the top.
Every entry records: what changed, which FRs/areas were touched, test results, the next step, and
anything deferred to the backlog or the open-questions log.

**Do not edit past entries.** If a past entry was wrong, correct it with a new entry that says so.

---

## Session 001 — 2026-10-01

### Objective

Start Phase 0 on a clean repository: create the skeleton and begin the documentation set, with **no
product code** (Addon 4 §L, steps 1–2).

### What changed

| File | Change |
|---|---|
| `README.md` | Rewritten: product summary, current phase (Phase 0, no code), repo layout, spec-of-record summary (kickoff + Addons 1–4), non-negotiable working rules |
| `docs/`, `app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/` | Created with `.gitkeep` (skeleton only — Kickoff §5 "Repo skeleton") |
| `docs/00_INDEX.md` | **New.** Document map (30 docs + 2 process files), reading plans incl. the mandatory session reading plan, Addon Coverage Matrix (64 rows), Source-of-Truth Matrix, document standard + header template, hygiene/conflict rules, ID registry (25 prefixes), 5-gate/58-check tracker, approval log |
| `docs/01_PRD.md` | **New.** Personas (4 + exclusions), monthly-rhythm JTBD, scope in/out (10 areas in, 24 parked items), forced in/out rulings, 10 success metrics with targets, multi-entity and pack-audience stances, no-login/no-RBAC decision, constraints, 20 labelled assumptions, 10 risks, canonical advisory disclaimer, IP/licensing stance, branding defaults, `DEC-001`–`DEC-019` index |
| `docs/02_FUNCTIONAL_SPEC.md` | **New.** 156 numbered FRs in 11 families, each with priority (P0/P1/P2), phase, behaviour, inputs/outputs, edge cases and testable acceptance criteria; priority + cut-line policy incl. the never-cut list; per-FR DoD; screen touchpoints; 13-row canonical edge-case matrix with message slugs |
| `docs/03_DATA_DICTIONARY.md` | **New.** Two-store model (DuckDB analytics / SQLite workflow), type + money rules, nullability and identity conventions, grain register (35 tables), full column specs, dedup keys, 15 integrity invariants, example rows, on-disk layout, volume estimates, supersessions, schema-versioning rules |
| `docs/CHANGELOG.md` | **New.** Keep a Changelog + semver policy for app and schema, Phase 0 entries, approval-record table, release history placeholder |
| `docs/SESSION_LOG.md` | **New.** This file |

### FRs / areas touched

- 156 `FR-nnn` allocated across 11 families, all with priorities and phases (`02` §2–§14).
- Areas governed: scope (`01`), behaviour (`02`), governance/metadata (`00`), process
  (`CHANGELOG`, `SESSION_LOG`).

### Spec sections integrated in this session

- Kickoff §5 (doc tree, quality gate), §2, §6, §7, §8, §9, §10, §11, §12 (partially, via `01`/`02`/`03`).
- Addon 1 §C.2/D/N (partially, via `01`), §O (tracker only).
- Addon 2 §A.3/C.2/D.14 (partially, via `01`/`00`).
- Addon 3 §B.2/E (partially, via `01`).
- Addon 4 §A.3/B/C/D/E (partially, via `00`/`01`).

Coverage-Matrix rows are only flipped to `INTEGRATED` when the owning doc is complete and the change is
recorded in `CHANGELOG.md`. A **full matrix refresh is required at the end of the doc build**.

### Test results

- No code, no tests possible yet. **Doc checks run this session:** file creation verified; FR-ID
  integrity verified (156 headings, zero duplicate IDs, per-family counts match the `02` §2 table
  exactly); placeholder scan clean (`TBD`/`TODO` hits are only the word "JTBD" and the hygiene rule
  itself); cross-references written only to docs that are planned in `00_INDEX.md` §3 (the full
  link-check runs once all docs exist).
- Quality gates: **0 of 5 gates attempted** (expected — gates are run at Phase 0 completion).

### Decisions taken this session

Recorded in `01_PRD.md` §21 as `DEC-001`…`DEC-019` and to be mirrored (with dates and rationale) into the
canonical Decided log in `18_...OPEN_QUESTIONS.md` when that doc is written.

### Blocking questions

None. Every unconfirmed client fact has a labelled default in `01` §12 and will be carried into `21`.

### Next step

Continue the mandated doc order: `04_SOURCE_MAPPING_AND_IMPORT_SPEC.md` — the import wizard flow,
profiles, the Excel/CSV hardening list (every quirk handled or explicitly rejected with named error
copy), reject-vs-quarantine decision, cross-import duplicate keys, incremental monthly loads,
profile versioning, the validation-check catalogue (`IMP-nnn`) and the control-totals reconciliation
rule — then `05_CALCULATION_SPEC.md`.

### Deferred to backlog / open questions

- All 24 parked scope items from `01` §6.2 → to be seeded into `27_BACKLOG.md` as `BL-001`…`BL-024`.
- Headcount metrics, one-off tagging, budget version-compare, commentary carry-forward, Power BI export,
  direct ERP connectors → already parked with triggers.
- Open commercial questions: support/warranty terms (`OQ-016`), delivery channel (`OQ-017`),
  signing-certificate budget (`OQ-012`).
