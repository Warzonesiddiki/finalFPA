# Changelog

All notable changes to this project are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for **both** the application
(`app`) and the **project schema** (`schema`). The schema version is stored inside every project
database and is the anchor for upgrade/migration work (`24_RELEASE_AND_VERSIONING_RUNBOOK.md`).

**Doc-change rule (P2):** behaviour changes update the owning spec **and this file first**, then code.
Every entry states the doc, the change, and the reason. Gate approvals are recorded here **and** in
`SESSION_LOG.md` (Addon 4 §E.2).

| Version track | Current | Notes |
|---|---|---|
| App version | `0.1.0` (planned, unreleased) | Packaged as `Setup-FPandAMonthEndCopilot-<version>.exe` |
| Schema version | `1` (planned) | Bumped only with a documented migration (`24`) |
| Docs version | `0.1.0` (working draft) | This Phase 0 set |

---

## [Unreleased]

### Phase 0 — Documentation (in progress)

#### Added — 2026-10-01

- **Repo skeleton** — `docs/`, `app/`, `ui/`, `sample-data/`, `tests/`, `packaging/`, `scripts/`
  (folders + `.gitkeep` only) and a root `README.md` describing the product, the current phase, the
  repo layout, and the non-negotiable working rules. Reason: Kickoff §15.1 / Addon 4 §L.1.
- **`docs/00_INDEX.md`** (Draft v0.1) — document map for docs `00`–`29`, reading plans (including the
  mandatory session reading plan), the **Addon Coverage Matrix** covering all **64 sections** of the
  spec of record (kickoff 15 + Addon 1 §16 + Addon 2 §10 + Addon 3 §11 + Addon 4 §12), the
  **Source-of-Truth Matrix**, the document standard and header template, hygiene and conflict-resolution
  rules, the permanent **ID namespace registry** (25 prefixes), the 5-gate/58-check tracker, and the
  approval log. Reason: Kickoff §5, Addon 2 §A.3, Addon 3 §A.3, Addon 4 §A.3/B/C.
- **`docs/01_PRD.md`** (Draft v0.1) — product definition, current-state problem and prior-prototype
  failure modes, four personas, the monthly-rhythm core JTBD plus secondary JTBDs, scope consequences of
  the principles, the **in-scope list** (10 areas), the **explicit out-of-scope list** (24 parked items
  with reasons and `BL-` ids), the **forced in/out rulings** (P&L focus; import-only budgets; optional
  journal-category column; manual control totals; one-off tagging parked; single currency),
  **10 success metrics with baselines and numeric targets**, multi-entity/consolidation stance,
  pack-recipient stance, the **no-login/no-RBAC decision**, hard constraints, 20 labelled assumptions,
  10 top product risks, the open-question set, the **canonical advisory disclaimer** and its mandated
  appearances, the **IP/licensing stance**, branding defaults with an accessibility guard, phasing
  overview, commercial placeholders, and a `DEC-001`–`DEC-019` decision index. Reason: Kickoff §2/§6/§12,
  Addon 1 §C.2/D/N, Addon 2 §C.2/D.14, Addon 3 §B.2/E, Addon 4 §D/E.

- **`docs/02_FUNCTIONAL_SPEC.md`** (Draft v0.1) — the complete functional specification:
  **156 numbered FRs** across 11 families (`FR-ONB` 8, `FR-PRJ` 12, `FR-IMP` 31, `FR-BVA` 16,
  `FR-EXC` 20, `FR-FC` 9, `FR-XL` 9, `FR-PPT` 9, `FR-AI` 14, `FR-SET` 12, `FR-XC` 16), each with a
  priority (P0/P1/P2), phase, behaviour, inputs/outputs, edge cases and testable acceptance criteria;
  the priority and **cut-line policy** including the never-cut list and the cut approval process; the
  per-FR Definition of Done; the screen-touchpoint inventory; and the canonical **13-row edge-case
  matrix** with stable message slugs (numeric codes reserved for doc `26`). Reason: Kickoff §5/§6/§8,
  Addon 1 §E, Addon 2 §D, Addon 3 §C/§F, Addon 4 §D/§G.

- **`docs/03_DATA_DICTIONARY.md`** (Draft v0.1) — the canonical data model: two-store split (DuckDB
  analytics / SQLite workflow state) with an authority rule per table; the full type system with the
  binding money rule (`DECIMAL(18,2)`, floats forbidden in money paths, no epsilon); nullability and
  identity conventions; a **grain register** covering all 40 tables in the model; complete column specifications for the
  dimensions, the three fact tables, forecast versions, quarantine rows, validation checks, rule runs,
  import batches, the exception register and its event history, pack issues and period snapshots,
  mapping profiles/versions/suggestions, four master-data tables, configuration, commentary, AI drafts
  and usage, audit and version history; documented duplicate-detection keys; 15 integrity invariants;
  worked example rows; the on-disk project layout; volume expectations; explicit supersessions from the
  seed model (`FactImportAudit` absorbed into `FactImportBatch`); and the schema-versioning and
  migration rules. Reason: Kickoff §7, Addon 1 §C.2, Addon 2 §C.2, Addon 3 §B.2, Addon 4 §G.1/H.

#### Changed — 2026-10-01

- Nothing yet (no doc has been revised after first issue).

#### Fixed — 2026-10-01

- Nothing yet.

#### Removed — 2026-10-01

- Nothing yet.

### Notes carried into the next session

- Docs `02`–`29` remain to be written, in the mandated order: `02`–`20` first (Kickoff §5), then
  Addon 1's `21`–`25`, Addon 2's `26`, Addon 3's `27`–`28`, Addon 4's `29`.
- Cross-addon additions are folded into the owning documents as they are written (never a parallel tree).
- **No product code may be written before recorded Phase 0 approval** (Addon 4 §L.12).

---

## Approval records

Approvals are recorded here in the form `Phase 0 APPROVED — <who> — <date>` (Addon 4 §E.2). None yet.

| Gate | Recorded approval | Date |
|---|---|---|
| Phase 0 (docs `00`–`29` + all five quality gates) | *awaiting request* | — |
| Packaging spike | *not started* | — |
| Phase gates 1–6 | *not started* | — |
| Real-data pilot | *not started* | — |
| UAT | *not started* | — |
| Go-live | *not started* | — |

---

## Release history

No application release yet. The first release will be tagged `v0.1.0` after the Phase 0 approval and the
packaging spike, per `24_RELEASE_AND_VERSIONING_RUNBOOK.md`.
