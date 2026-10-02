> **Status:** Draft v0.1
> **Last updated:** 2026-10-02
> **Owning FRs/areas:** the **traceability chain** — every `FR-nnn` in `02` joined to its spec section(s),
> its screen ID(s) (`08` §4), its API endpoint(s), its test ID(s) (`14` §4) and its status; the invariants
> a change must preserve; the reverse indexes (screen → FR, endpoint → FR, test family → FR); and the
> **endpoint reference set** that `26` adopts
> **TL;DR (≤ 15 lines):**
> - **Complete traceability chain:** All 156 FRs mapped end-to-end: FR → Spec Section → Screen ID → API Endpoint → Test ID → Status.
> - **Priority distribution:** 110 P0 (must ship), 39 P1 (high value), 7 P2 (deferrable polish) across 11 functional families.
> - **Zero orphans:** Every API route has an owning FR; every screen component maps to an FR; every FR has automated tests.
> - **Bidirectional verification:** Forward and reverse indexes ensure complete coverage and prevent speculative dead code.
> - **Living synchronization:** Updates synchronized atomically with spec changes; verified by doc-lint scripts.

# 20 — Requirements Traceability

## 1. Purpose, ownership and the chain

### 1.1 What this document owns

| Fact | Where it lives |
|---|---|
| The FR → section → screen → endpoint → test **join** | **here** (the only place the five keys meet) |
| FR text, priority, phase, acceptance criteria | `02` (§4–§14); priorities from `02` §3 |
| Screen IDs, screen behaviour, states | `08` (§4 inventory, §5–§12 per screen, §17 states) |
| Test IDs, families, counts, levels, runners | `14` §4 (the 292-test inventory) |
| Endpoint inventory, request/response schema, error codes | `26` (this document's endpoint column is the reference set it adopts) |
| Business rules, formulas, rules, layouts | `04`–`07`, `10`–`13` (the spec column points at the owning section) |
| Open questions, assumptions, decisions | `18` (§3 assumptions, §4 `OQ-`, §5 `DEC-`) |
| Phase ordering, gate contracts, estimates | `16`; the 66 gate checks are enumerated in `14` §15 (9+12+12+12+13+8) |

**Rule.** This document never becomes the source of a fact. If a row here disagrees with the owning doc,
the owning doc wins and the row is the defect. Corrections follow the change-impact rule (`19` §5.2).

### 1.2 The chain

```
FR-nnn  →  spec section(s)  →  SCR-nnn  →  HTTP endpoint  →  TST-xxx-nn  →  status
  02          owning docs        08             26            14 §4        16/14
```

| Join key | Format | Owned by | Resolution rule in this document |
|---|---|---|---|
| Requirement | `FR-<FAMILY>-nnn` | `02` | Never renumbered; a new family needs `02` §2 and `00_INDEX` §8 first |
| Spec section | `<doc> §<section>` | the owning doc | Only sections that *specify* the FR; `02` §N is always first |
| Screen | `SCR-nnn` (or a sanctioned non-value, §2.2) | `08` §4 | The inventory row that owns the FR, plus section-level owners |
| Endpoint | `METHOD /path` (relative to `/api/v1`, `ADR-009`) | `26` | Must resolve to the reference set in §2.3 |
| Test | `TST-<FAMILY>-nn` | `14` §4 | Must resolve to the frozen inventory; ≥ 1 per FR |
| Status | `Spec'd` / `Built` / `Complete` | this document | Vocabulary fixed in §1.3 |

The join itself is the deliverable: `02` §15 states that the feature-to-screen join lives in this
document, and `02` §17 fixes the column set reproduced in §2.1.

### 1.3 Status vocabulary (three values, no others)

| Value | Means | Evidence required |
|---|---|---|
| `Spec'd` | Behaviour, edge cases and acceptance criteria exist in `02`; ≥ 1 test assigned here | This document (Phase 0 default for every FR) |
| `Built` | The behaviour exists in a merged commit and its assigned tests are written | Commit + test file; `16`'s phase checklist |
| `Complete` | All assigned tests are green **and** the 3–6 step demo recipe is recorded (`14` §14.3) | Gate record (`16` §5.2) + demo recipe |

**No FR may be marked `Built` while its owning doc still carries an open blocking question, and no FR
may be marked `Complete` without a test ID in this table showing green in the latest gate run.**

## 2. How to read the matrix

### 2.1 Columns

| Column | Meaning |
|---|---|
| **FR** | The numbered requirement from `02`; the title is quoted verbatim from `02` |
| **P** | Priority `P0`/`P1`/`P2` with the never-cut semantics in `02` §3 and `16` §9.2 |
| **Ph** | The delivery phase from `02`; phase contents and gates from `16` §9.2 |
| **Spec section(s)** | The sections that specify the behaviour — `02` first, then the owning detail docs |
| **Screen(s)** | `SCR-nnn` from `08` §4, or a sanctioned non-value (§2.2) |
| **Endpoint(s)** | Member(s) of the §2.3 reference set; the contract itself is `26` |
| **Test ID(s)** | The **minimum mandatory evidence set** from the 292-test inventory (`14` §4) |
| **Status** | `Spec'd` today for all 156 (§1.3) |

### 2.2 Sanctioned non-values (and why they are not gaps)

| Value | Use it when | Examples |
|---|---|---|
| `Global (08 §3.3 shell)` | The behaviour appears on every screen through a shell component (banner, filter bar, job drawer, dialog) | `FR-SET-010` stale banner, `FR-BVA-015` filter context, `FR-XC-008` job state |
| `Global (08 §18)` | A cross-cutting UI baseline with no single screen | `FR-XC-011` accessibility |
| `n/a — headless` | No user surface exists in v1 | `FR-XC-007` logging |
| `n/a — <reason>` | A guard/policy with no screen and no route; the reason is the sentence after the dash | `n/a — release guard` (`FR-XC-013`), `n/a — network policy` (`FR-XC-009`) |

**Rule.** Every `n/a` is a claim that must be falsifiable: if a screen or route that serves the FR is
found later, the cell was wrong and gets corrected in the same change. `FR-EXC-003`, `FR-EXC-004`,
`FR-FC-005`, `FR-XC-012` and the other engine-invariant FRs keep their screen (they surface through
the screen that exposes the invariant) — `n/a` is never a shorthand for "not thought about".

### 2.3 The endpoint reference set (95 routes, adopted by `26`)

All paths are relative to `/api/v1` (`ADR-009`: loopback only, random port, per-launch token). This set
is the **consumer-driven reference**: every route exists because at least one FR or screen needs it.

| Rule | Detail |
|---|---|
| Ownership | `26` owns the endpoint contract (schemas, codes, pagination, permissions). It adopts these 95 paths **verbatim** or records a rename |
| Renames | A rename updates `26`, this document and the affected `TST-API-*` in one change; the old path is not kept as an alias |
| Reverse index | `26` publishes endpoint → FR + consuming screen; this document keeps the FR → endpoint direction |
| No orphans | An endpoint with no FR consumer is deleted, not shipped (`14` §12.3) |
| Jobs | Long-running operations (`POST /imports`, `POST /rules/run`, `POST /forecast/run`, `POST /packs/*`, `POST /diagnostics`) follow the 202 + poll contract over `GET /jobs` (`TST-API-10`) |
| Envelope | Every route uses the standard envelope and catalog errors (`TST-API-01`, `TST-API-02`); every route needs the per-launch token (`TST-API-05`) |

**Lifecycle — projects, periods, storage** (19)

| Endpoint | Purpose |
|---|---|
| `GET /bootstrap` | First-run state: ensure/share the sample project, resolve the last project, launch target |
| `GET /projects` | Recent-project list (path, last opened, last period, status) |
| `POST /projects` | Create a project (fiscal calendar, currency, units, entities, optional branding) |
| `POST /projects/{id}/open` | Open a project: single-instance mutex, schema check/migration, period state |
| `GET /projects/{id}` | Project and period status, health summary for Home |
| `DELETE /projects/{id}` | Delete a project (typed confirmation recorded) |
| `POST /projects/{id}/backup` | Backup zip (databases, archives, settings, mappings, master data; manifest; no secrets) |
| `POST /projects/restore` | Validate a backup zip and restore it to a chosen folder |
| `POST /projects/{id}/convert` | Convert a sample project to a normal project (typed confirmation, audit-logged) |
| `GET /projects/{id}/storage` | Storage breakdown, low-storage warning inputs, archive sizes |
| `POST /projects/{id}/archive-raw` | Archive raw files to a user-chosen zip, then remove them after confirmation |
| `GET /projects/{id}/versions` | Version history for mappings, thresholds, master data, assumptions, prompts, branding |
| `POST /projects/{id}/versions/{v}/revert` | Revert a versioned artefact to a named version |
| `GET /projects/{id}/periods` | Period list with Open/Closed status |
| `POST /projects/{id}/periods` | Open a new period (expected-source checklist; carries config forward, never numbers) |
| `POST /periods/{id}/close` | Close a period: lock actuals, prompt the backup reminder |
| `POST /periods/{id}/reopen` | Warned, typed-confirmation, audited reopen |
| `GET /periods/{id}/snapshots` | Read-only period-close snapshots behind issued packs |
| `GET /checks` | Check-screen aggregate: validation findings, exception counts, stale markers, storage warnings |

**Imports and batches** (11)

| Endpoint | Purpose |
|---|---|
| `POST /imports/pre-scan` | Source type, SHA-256 fingerprint, size/rows/estimate, limit checks |
| `POST /imports` | Stage → parse → validate a file (long-running job; 202 + `GET /jobs` poll) |
| `GET /imports` | Batch history (status, counts, score, links to report and archive) |
| `PUT /imports/{batch}/mapping` | Column mapping with preview, overrides, profile apply/save |
| `GET /imports/{batch}/report` | Validation report (per-check pass/fail, counts, samples, control totals, timings) |
| `GET /imports/{batch}/quarantine` | Quarantined rows with failing field, reason and raw values |
| `POST /imports/{batch}/commit` | Atomic staged commit (single transaction) |
| `POST /imports/{batch}/cancel` | Cancel staging; no partial data left behind |
| `POST /imports/{batch}/void` | Void/reverse one batch (all-or-nothing; blocked for closed periods) |
| `GET /imports/{batch}/archive` | The immutable archived source file and its recorded checksum |
| `GET /imports/{batch}/score` | Data-quality score with the per-check breakdown |

**Mapping profiles, master data, rules, settings** (15)

| Endpoint | Purpose |
|---|---|
| `GET /mapping-profiles` | List/version mapping profiles; header-fingerprint suggestion source |
| `PUT /mapping-profiles/{id}` | Create/edit/clone a profile (column map, overrides, date/number rules) |
| `GET /master-data/{kind}` | Master-data tables (vendor categories, recurring costs, approval thresholds, owners) |
| `PUT /master-data/{kind}` | Edit master data (versioned, revertable) |
| `POST /master-data/{kind}/import` | Import master data through the standard validation/archive path |
| `GET /rules` | Rule catalogue with per-project enable state, defaults and effective thresholds |
| `PUT /rules/{id}` | Edit a rule's threshold/enable state (versioned; marks derived results stale) |
| `POST /rules/run` | Run the enabled rule set over the loaded data (job; run summary) |
| `GET /settings` | All settings (machine vs project scope) for the Settings screens |
| `PUT /settings` | Update settings (display, thresholds, branding, storage, rule defaults) |
| `PUT /settings/ai-key` | Store the AI key via DPAPI (write-only; status returned, never the key) |
| `DELETE /settings/ai-key` | Rotate/revoke: purge the old value from config and memory, audit-logged |
| `PUT /ui-state` | UI state: tour dismissal, last screen per project, sticky display preferences |
| `GET /filters` | Shared filter context for the current project |
| `PUT /filters` | Persist the shared filter context (survives navigation) |

**Analysis and search** (9)

| Endpoint | Purpose |
|---|---|
| `GET /analysis/bva` | BvA matrix: windows, grain, rollups, variance, comparability, entity sums |
| `GET /analysis/bridge` | Bridge/waterfall drivers from Budget to Actual |
| `GET /analysis/trends` | Multi-period actual/budget/PY trends and variance bars |
| `GET /analysis/topn` | Ranked adverse/favourable variances with the deterministic tie-break |
| `GET /analysis/three-way` | Actual vs Budget vs Forecast with accuracy columns |
| `GET /analysis/kpis` | KPI/ratio cards with target comparison and drill target |
| `GET /analysis/drill` | Transaction detail for exactly one displayed figure (source-file evidence) |
| `GET /search` | Grouped search across vouchers, vendors, descriptions, accounts |
| `POST /exports/ad-hoc` | Export what you see (current filter/sort/columns) to Excel or CSV |

**Exceptions** (7)

| Endpoint | Purpose |
|---|---|
| `GET /exceptions` | Register rows for the current filter (severity, amount at risk, owner, status, aging) |
| `GET /exceptions/{id}` | Exception detail with history, notes and evidence links |
| `PATCH /exceptions/{id}` | Status, owner and note changes (append-only note history) |
| `POST /exceptions/bulk` | Bulk status/owner change (one audit entry per item) |
| `GET /exceptions/effectiveness` | Per-rule effectiveness analytics (raised, explained share, days to close, tuning) |
| `POST /exceptions/{id}/evidence` | Evidence bundle workbook/zip for one exception |
| `GET /exceptions/export` | Register export: filtered sheet + unfiltered sheet, owner-wise grouping |

**Forecast** (7)

| Endpoint | Purpose |
|---|---|
| `GET /forecast/versions` | Forecast versions, scenarios, locks and provenance |
| `POST /forecast/versions` | Create/copy/rename/delete a scenario/version |
| `POST /forecast/run` | Generate the forecast (method per line/group; job) |
| `PATCH /forecast/cells` | Manual override with a mandatory reason (audited) |
| `POST /forecast/versions/{v}/lock` | Lock a version (read-only; referenced by issued packs) |
| `GET /forecast/compare` | Version/scenario comparison |
| `GET /forecast/accuracy` | Forecast-vs-actual accuracy metrics and method guidance |

**Packs, issuance, commentary, templates** (10)

| Endpoint | Purpose |
|---|---|
| `POST /packs/excel` | Generate the Excel pack (job; 250k-row and standard paths) |
| `POST /packs/deck` | Generate the six-slide deck (job; base-deck mode included) |
| `POST /packs/{id}/refresh` | Refresh a pack from current data and report exactly what changed |
| `GET /packs` | Generated/issued packs with version, snapshot reference and status |
| `POST /issuance` | Issue a pack: freeze snapshots, lock commentary, record recipients, increment version |
| `GET /issuance` | Issuance register (every issued version, recipients, re-issues) |
| `POST /issuance/{id}/reissue` | Re-issue: new pack version; the previous version stays immutable |
| `GET /commentary` | Commentary for lines/periods (typed, rule-based or approved AI draft) |
| `PUT /commentary` | Save commentary (locked after issuance until a re-issue) |
| `POST /templates/export` | Write a blank input template (actuals/budget/forecast/master data) to a chosen path |

**Optional AI** (7)

| Endpoint | Purpose |
|---|---|
| `POST /ai/test-connection` | Manual connectivity test for the configured endpoint (user-triggered only) |
| `POST /ai/drafts` | Run one of the four AI features (variance commentary, mapping suggestion, exception summary, follow-up draft) |
| `GET /ai/drafts` | Draft history with provenance, evidence and status |
| `POST /ai/drafts/{id}/approve` | Human approval of a draft (the only path into a pack) |
| `POST /ai/mapping-suggestions` | Propose column mappings with confidence and evidence |
| `GET /ai/mapping-suggestions` | Mapping Review Queue (acceptance applies to the next import, never in-run) |
| `GET /ai/usage` | Local usage log: tokens, estimated cost, caps and outcomes |

**Operations, diagnostics, meta** (10)

| Endpoint | Purpose |
|---|---|
| `GET /jobs` | Job list/status (progress, ETA, terminal state) for the job drawer and polling |
| `POST /jobs/{id}/cancel` | Cancel a running job where the job supports it |
| `GET /doctor` | Environment doctor: WebView2, paths, permissions, DB integrity, disk, profile mismatch |
| `GET /health` | Liveness/version only (no data), for the shell and tests |
| `POST /diagnostics` | Build the redacted diagnostics zip (metadata-only by default) |
| `GET /audit` | Filterable audit log with export |
| `GET /instrumentation` | Local job timings (import, rules, exports, cold start) surfaced in Diagnostics |
| `GET /help` | Help topics keyed by `SCR-nnn` (single-sourced with `22`) |
| `POST /update-check` | Manual update check against the documented channel (disabled by default; never auto-installs) |
| `GET /meta/error-catalog` | The error-code catalog: code → user message + hint, keyed by the `26` families |

### 2.4 Test references (the frozen inventory)

The 292 test IDs in `14` §4 are frozen for Phase 0: **16 families, 206 owned by `14` and 86 reserved**
by `10`/`11`/`12`/`13`. The test column lists each FR's **minimum mandatory evidence**; a phase may add
tests, but no ID is renumbered and no bar is lowered (`14` §1.2).

| Family | Range | Count | Level(s) | Owns |
|---|---|---|---|---|
| `TST-CALC` | `01`–`24` | 24 | L1, L2 | Formulas, windows, rounding, KPIs, score, materiality |
| `TST-IMP` | `01`–`36` | 36 | L1, L3, L6 | The 32 checks 1:1, corpus, resumability, atomicity, re-import guards |
| `TST-RUL` | `01`–`28` | 28 | L1, L3 | One per rule + scorecard, controls, re-run identity, effectiveness |
| `TST-FC` | `01`–`14` | 14 | L1–L3 | Methods, scenarios, locks, accuracy, TTM, overrides |
| `TST-BVA` | `01`–`12` | 12 | L1, L6, L7 | Matrix, drill, rollups, parity |
| `TST-EXC` | `01`–`12` | 12 | L1, L6 | Register workflow, bulk, aging, owners, evidence |
| `TST-UI` | `01`–`20` | 20 | L7 + manual | States, a11y, tokens, wording, jobs, help |
| `TST-API` | `01`–`16` | 16 | L4 | Envelope, errors, pagination, filters, auth, OpenAPI drift, CLI parity |
| `TST-E2E` | `01`–`08` | 8 | L7 + manual | Golden path, issuance, offline, crash, upgrade, backup, diagnostics, fresh install |
| `TST-PRF` | `01`–`16` | 16 | L8 | One per `NFR-001`…`016` |
| `TST-WIN` | `01`–`14` | 14 | L9 | Windows environment, DPI, paths, sleep, locks |
| `TST-UAT` | `01`–`06` | 6 | L9 | UAT scripts and tie-out (`28` owns the mechanics) |
| `TST-AI` | `01`–`14` | 14 | L1, L4, L5 | Reserved by `10` |
| `TST-XL` | `01`–`26` | 26 | L5 (+ L1) | Reserved by `11` |
| `TST-PPT` | `01`–`24` | 24 | L5 (+ L1/L8) | Reserved by `12` |
| `TST-SEC` | `01`–`22` | 22 | L1–L6, L9 | Reserved by `13` §13.2 |

**Reading a row.** `TST-IMP-24` means check `IMP-024`; `TST-RUL-27` means the re-run identity scenario;
`TST-PRF-07` means `NFR-007`. A row's list is the **shortest defensible set** — not the full suite that
will run against the FR.

## 3. The matrix (156 FRs)

### 3.1 `FR-ONB` — onboarding, first-run and help (8 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-ONB-001` | First run opens the sample project | P0 | 1 | `02` §4; `16` §6.1; `15` §6.1 | `SCR-001`, `SCR-002` | `GET /bootstrap` | `TST-E2E-08`, `TST-UI-17` | `Spec'd` |
| `FR-ONB-002` | Guided first-run tour | P2 | 6 | `02` §4; `08` §12 | `SCR-043` | `PUT /ui-state` | `TST-UI-17`, `TST-E2E-08` | `Spec'd` |
| `FR-ONB-003` | "Load your own data" is always one action away | P0 | 1 | `02` §4; `08` §5.3 | `SCR-001`, `SCR-005` | `POST /imports/pre-scan` | `TST-E2E-01`, `TST-UI-17` | `Spec'd` |
| `FR-ONB-004` | Help panel with contextual help | P1 | 1 | `02` §4; `08` §12; `22` | `SCR-042` | `GET /help` | `TST-UI-18`, `TST-UAT-04` | `Spec'd` |
| `FR-ONB-005` | Blank templates downloadable from inside the app | P0 | 1 | `02` §4; `04` §4 | `SCR-001`, `SCR-005` | `POST /templates/export` | `TST-E2E-01`, `TST-IMP-01` | `Spec'd` |
| `FR-ONB-006` | Reopen last project and autosave | P0 | 1 | `02` §4; `08` §3.1 | `SCR-001`, `SCR-002` | `GET /bootstrap`, `PUT /ui-state` | `TST-E2E-01`, `TST-UI-20` | `Spec'd` |
| `FR-ONB-007` | Help text is single-sourced with the user guide | P1 | 2 | `02` §4; `22`; `08` §12 | `SCR-042` | `GET /help` | `TST-UI-18`, `TST-UI-10` | `Spec'd` |
| `FR-ONB-008` | Sample data is unmistakable and cannot contaminate client data | P0 | 1 | `02` §4/§14; `13` §10; `15` §1.2 | `SCR-001`; Global (08 §3.3 shell) | `GET /projects/{id}`, `POST /projects/{id}/convert` | `TST-XL-26`, `TST-PPT-21`, `TST-SEC-17` | `Spec'd` |

### 3.2 `FR-PRJ` — projects, periods, storage and lifecycle (12 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-PRJ-001` | Home screen | P0 | 1 | `02` §5; `08` §5.3 | `SCR-001` | `GET /projects/{id}`, `GET /checks` | `TST-UI-01`, `TST-E2E-01` | `Spec'd` |
| `FR-PRJ-002` | Create project | P0 | 1 | `02` §5; `08` §6.2; `09` §7.1 | `SCR-003`, `SCR-002` | `POST /projects` | `TST-SEC-16`, `TST-E2E-01` | `Spec'd` |
| `FR-PRJ-003` | Open and manage recent projects | P0 | 1 | `02` §5; `08` §6.1 | `SCR-002` | `GET /projects`, `POST /projects/{id}/open` | `TST-SEC-15`, `TST-UI-16` | `Spec'd` |
| `FR-PRJ-004` | New Period wizard | P0 | 1 | `02` §5; `04` §14; `08` §6.3 | `SCR-004`, `SCR-001` | `GET /projects/{id}/periods`, `POST /projects/{id}/periods` | `TST-CALC-15`, `TST-BVA-08` | `Spec'd` |
| `FR-PRJ-005` | Period status: Open / Closed, with audited reopen | P0 | 1 | `02` §5; `03` §3.6; `08` §6.3 | `SCR-001`, `SCR-004` | `POST /periods/{id}/close`, `POST /periods/{id}/reopen` | `TST-EXC-06`, `TST-CALC-15` | `Spec'd` |
| `FR-PRJ-006` | Single instance per project | P0 | 1 | `02` §5; `09` §7.4 | `SCR-002` | `POST /projects/{id}/open` | `TST-WIN-05` | `Spec'd` |
| `FR-PRJ-007` | Schema version check and migration on open | P0 | 1 | `02` §5; `09` §13/§16 | `SCR-002` | `POST /projects/{id}/open` | `TST-E2E-05`, `TST-WIN-09` | `Spec'd` |
| `FR-PRJ-008` | Back up a project to a zip | P0 | 1 | `02` §5; `09` §7.1; `13` §9.2 | `SCR-039` | `POST /projects/{id}/backup` | `TST-E2E-06` | `Spec'd` |
| `FR-PRJ-009` | Restore a project from a zip | P0 | 1 | `02` §5; `09` §7.1; `13` §9.2 | `SCR-039`, `SCR-002` | `POST /projects/restore` | `TST-E2E-06`, `TST-UI-16`, `TST-UAT-06` | `Spec'd` |
| `FR-PRJ-010` | Period-close snapshot | P1 | 3 | `02` §5; `03` §5.4; `07` §7 | `SCR-030`, `SCR-001` | `GET /periods/{id}/snapshots` | `TST-E2E-02`, `TST-EXC-06` | `Spec'd` |
| `FR-PRJ-011` | Storage health and archive-and-delete | P1 | 3 | `02` §5; `03` §9.2; `09` §7.3 | `SCR-032`, `SCR-040` | `GET /projects/{id}/storage`, `POST /projects/{id}/archive-raw` | `TST-WIN-12`, `TST-UI-16` | `Spec'd` |
| `FR-PRJ-012` | Delete project with typed confirmation | P1 | 1 | `02` §5; `13` §10.2; `15` §7.1 | `SCR-002` | `DELETE /projects/{id}` | `TST-SEC-15`, `TST-UI-16` | `Spec'd` |

### 3.3 `FR-IMP` — import, mapping, validation and batches (31 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-IMP-001` | Import entry: drag-and-drop and file picker | P0 | 1 | `02` §6; `04` §3; `08` §7.1 | `SCR-005` | `POST /imports/pre-scan` | `TST-UI-01`, `TST-E2E-01` | `Spec'd` |
| `FR-IMP-002` | Source type and file fingerprint | P0 | 1 | `02` §6; `04` §3 | `SCR-005` | `POST /imports/pre-scan` | `TST-IMP-01`, `TST-IMP-29` | `Spec'd` |
| `FR-IMP-003` | Pre-scan with estimate and limits | P0 | 1 | `02` §6; `04` §3 | `SCR-006` | `POST /imports/pre-scan` | `TST-IMP-02`, `TST-IMP-03` | `Spec'd` |
| `FR-IMP-004` | Column mapping with preview | P0 | 1 | `02` §6; `04` §5; `08` §7.4 | `SCR-008` | `PUT /imports/{batch}/mapping` | `TST-IMP-04`, `TST-IMP-05`, `TST-IMP-10`, `TST-IMP-11` | `Spec'd` |
| `FR-IMP-005` | Saved mapping profiles | P0 | 1 | `02` §6; `04` §5; `16` §6.1 | `SCR-008`, `SCR-033` | `GET /mapping-profiles`, `PUT /mapping-profiles/{id}` | `TST-UI-20`, `TST-IMP-15` | `Spec'd` |
| `FR-IMP-006` | Header-fingerprint profile auto-suggest | P1 | 1 | `02` §6; `04` §5.1/§5.2 | `SCR-008` | `GET /mapping-profiles` | `TST-IMP-10`, `TST-UI-01` | `Spec'd` |
| `FR-IMP-007` | Template version stamp and outdated-template warning | P1 | 1 | `02` §6; `03` §5.1; `04` §4.2 | `SCR-007`, `SCR-009` | `POST /imports/pre-scan` | `TST-IMP-01`, `TST-UI-10` | `Spec'd` |
| `FR-IMP-008` | AI mapping review queue | P1 | 6 | `02` §6; `10` §5.2/§11; `08` §7.4 | `SCR-008` | `POST /ai/mapping-suggestions`, `GET /ai/mapping-suggestions` | `TST-AI-13`, `TST-AI-14` | `Spec'd` |
| `FR-IMP-009` | Excel structure quirks are handled or explicitly rejected | P0 | 1 | `02` §6; `04` §8 | `SCR-007`, `SCR-009` | `POST /imports` | `TST-IMP-04`, `TST-IMP-06`, `TST-IMP-07`, `TST-IMP-08`, `TST-IMP-09` | `Spec'd` |
| `FR-IMP-010` | CSV handling | P0 | 1 | `02` §6; `04` §9 | `SCR-005`, `SCR-007` | `POST /imports` | `TST-IMP-01`, `TST-IMP-33` | `Spec'd` |
| `FR-IMP-011` | Value parsing rules per profile | P0 | 1 | `02` §6; `04` §7; `05` §6 | `SCR-008` | `PUT /imports/{batch}/mapping` | `TST-IMP-14`, `TST-IMP-15`, `TST-IMP-16`, `TST-IMP-17`, `TST-IMP-20` | `Spec'd` |
| `FR-IMP-012` | Formula and error-cell policy | P0 | 1 | `02` §6; `04` §8 | `SCR-007`, `SCR-008` | `POST /imports` | `TST-IMP-12`, `TST-IMP-16` | `Spec'd` |
| `FR-IMP-013` | Row-level validation and quarantine | P0 | 1 | `02` §6; `04` §11/§17 | `SCR-013` | `GET /imports/{batch}/quarantine` | `TST-IMP-24`, `TST-UI-01` | `Spec'd` |
| `FR-IMP-014` | File-level rejection conditions | P0 | 1 | `02` §6; `04` §10/§11 | `SCR-009`, `SCR-014` | `POST /imports` | `TST-IMP-05`, `TST-IMP-08`, `TST-IMP-09`, `TST-IMP-23` | `Spec'd` |
| `FR-IMP-015` | Debit = credit balance check | P0 | 1 | `02` §6; `04` §12 | `SCR-009` | `POST /imports` | `TST-IMP-23` | `Spec'd` |
| `FR-IMP-016` | Control-total reconciliation | P1 | 1 | `02` §6; `04` §12 | `SCR-010`, `SCR-012` | `GET /imports/{batch}/report` | `TST-IMP-25`, `TST-IMP-26` | `Spec'd` |
| `FR-IMP-017` | Duplicate candidate detection at import | P0 | 1 | `02` §6; `04` §13; `06` §1 | `SCR-009`, `SCR-012` | `GET /imports/{batch}/report` | `TST-IMP-27`, `TST-UI-01` | `Spec'd` |
| `FR-IMP-018` | Cross-batch duplicate detection | P0 | 1 | `02` §6; `04` §13 | `SCR-010` | `POST /imports/{batch}/commit` | `TST-IMP-28`, `TST-IMP-36` | `Spec'd` |
| `FR-IMP-019` | Re-import guard | P0 | 1 | `02` §6; `04` §13/§14 | `SCR-005`, `SCR-009` | `POST /imports/pre-scan` | `TST-IMP-29`, `TST-IMP-36` | `Spec'd` |
| `FR-IMP-020` | Atomic staged commit | P0 | 1 | `02` §6; `04` §15 | `SCR-010` | `POST /imports/{batch}/commit` | `TST-IMP-35`, `TST-WIN-09` | `Spec'd` |
| `FR-IMP-021` | Validation report | P0 | 1 | `02` §6; `04` §17 | `SCR-012`, `SCR-009` | `GET /imports/{batch}/report` | `TST-IMP-24`, `TST-UI-01` | `Spec'd` |
| `FR-IMP-022` | Data-quality score | P1 | 1 | `02` §6; `04` §16; `05` §8 | `SCR-010`, `SCR-014` | `GET /imports/{batch}/score` | `TST-CALC-24`, `TST-IMP-22` | `Spec'd` |
| `FR-IMP-023` | Import history | P0 | 1 | `02` §6; `04` §18 | `SCR-011` | `GET /imports` | `TST-UI-01`, `TST-IMP-35` | `Spec'd` |
| `FR-IMP-024` | Void or reverse a batch | P0 | 1 | `02` §6; `04` §18; `03` §3.6 | `SCR-011` | `POST /imports/{batch}/void` | `TST-UI-16`, `TST-IMP-35` | `Spec'd` |
| `FR-IMP-025` | Immutable raw-file archive with checksum | P0 | 1 | `02` §6; `03` §5.1; `09` §7.2 | `SCR-011`, `SCR-012` | `GET /imports/{batch}/archive` | `TST-SEC-05`, `TST-IMP-01` | `Spec'd` |
| `FR-IMP-026` | Incremental monthly load and mid-year profile versioning | P0 | 1 | `02` §6; `04` §14 | `SCR-008`, `SCR-011`, `SCR-033` | `PUT /imports/{batch}/mapping` | `TST-IMP-28`, `TST-IMP-36` | `Spec'd` |
| `FR-IMP-027` | Budget and forecast file validation | P0 | 1 | `02` §6; `04` §10; `11` §8 | `SCR-007`, `SCR-009` | `POST /imports` | `TST-IMP-26`, `TST-IMP-31`, `TST-IMP-32` | `Spec'd` |
| `FR-IMP-028` | Budget re-import replaces a version atomically | P1 | 1 | `02` §6; `04` §14 | `SCR-010` | `POST /imports/{batch}/commit` | `TST-IMP-24`, `TST-IMP-35` | `Spec'd` |
| `FR-IMP-029` | Master-data imports | P1 | 2 | `02` §6; `03` §5; `04` §6 | `SCR-034` | `POST /master-data/{kind}/import` | `TST-UI-20`, `TST-IMP-24` | `Spec'd` |
| `FR-IMP-030` | Long-running import UX | P0 | 1 | `02` §6; `04` §3; `09` §8.2 | `SCR-009`; Global (08 §3.3 shell) | `POST /imports`, `POST /imports/{batch}/cancel` | `TST-UI-13`, `TST-PRF-02`, `TST-PRF-16` | `Spec'd` |
| `FR-IMP-031` | Sample-project import guard | P1 | 1 | `02` §6; `14` §16 | `SCR-005`, `SCR-010` | `POST /imports` | `TST-UI-01`, `TST-SEC-17` | `Spec'd` |

### 3.4 `FR-BVA` — budget vs actual analysis (16 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-BVA-001` | BvA matrix at the lowest shared grain | P0 | 2 | `02` §7; `05` §4; `08` §9.2 | `SCR-015` | `GET /analysis/bva` | `TST-BVA-01`, `TST-BVA-02`, `TST-PRF-03`, `TST-UAT-02` | `Spec'd` |
| `FR-BVA-002` | Period windows: MTD, YTD, PY MTD, PY YTD, TTM | P0 | 2 | `02` §7; `05` §3; `08` §9.1 | `SCR-015` | `GET /analysis/bva` | `TST-CALC-16`, `TST-BVA-07` | `Spec'd` |
| `FR-BVA-003` | Variance, variance % and favour*ability* | P0 | 2 | `02` §7; `05` §4.2 | `SCR-015` | `GET /analysis/bva` | `TST-CALC-18`, `TST-CALC-19`, `TST-CALC-20` | `Spec'd` |
| `FR-BVA-004` | Drill-down to transactions with source-file evidence | P0 | 2 | `02` §7; `05` §4; `08` §9.4 | `SCR-021` | `GET /analysis/drill` | `TST-BVA-02`, `TST-BVA-03` | `Spec'd` |
| `FR-BVA-005` | BvA bridge/waterfall chart | P0 | 2 | `02` §7; `05` §5; `08` §9.3 | `SCR-016` | `GET /analysis/bridge` | `TST-BVA-12`, `TST-PPT-14` | `Spec'd` |
| `FR-BVA-006` | Trend charts | P0 | 2 | `02` §7; `08` §9.3 | `SCR-017` | `GET /analysis/trends` | `TST-BVA-12`, `TST-CALC-16` | `Spec'd` |
| `FR-BVA-007` | Top-N variance views | P0 | 2 | `02` §7; `08` §9.3 | `SCR-018` | `GET /analysis/topn` | `TST-BVA-11`, `TST-PPT-15` | `Spec'd` |
| `FR-BVA-008` | Three-way view and forecast accuracy columns | P1 | 4 | `02` §7; `05` §9; `08` §9.3 | `SCR-019` | `GET /analysis/three-way` | `TST-FC-14`, `TST-BVA-12` | `Spec'd` |
| `FR-BVA-009` | Hierarchy rollups with tie-to-children guarantee | P1 | 2 | `02` §7; `05` §4.3 | `SCR-015` | `GET /analysis/bva` | `TST-BVA-05`, `TST-XL-15` | `Spec'd` |
| `FR-BVA-010` | KPI/ratio library | P1 | 2 | `02` §7; `05` §7 | `SCR-020` | `GET /analysis/kpis` | `TST-CALC-21`, `TST-BVA-12` | `Spec'd` |
| `FR-BVA-011` | Export what you see | P0 | 2 | `02` §7; `11` §7 | `SCR-015`–`SCR-022` | `POST /exports/ad-hoc` | `TST-BVA-06`, `TST-XL-22` | `Spec'd` |
| `FR-BVA-012` | Search | P1 | 2 | `02` §7; `08` §9.5 | `SCR-022` | `GET /search` | `TST-UI-14` | `Spec'd` |
| `FR-BVA-013` | Comparability guard | P0 | 2 | `02` §7; `05` §4.1 | `SCR-015` | `GET /analysis/bva` | `TST-BVA-08`, `TST-BVA-09` | `Spec'd` |
| `FR-BVA-014` | Grouped entity totals are labelled as simple sums | P0 | 2 | `02` §7; `01` §8 | `SCR-015` | `GET /analysis/bva` | `TST-BVA-04` | `Spec'd` |
| `FR-BVA-015` | Shared filter context | P0 | 2 | `02` §7; `08` §3.3 | Global (08 §3.3 shell) | `GET /filters`, `PUT /filters` | `TST-BVA-01`, `TST-BVA-06` | `Spec'd` |
| `FR-BVA-016` | Empty, loading and error states | P0 | 2 | `02` §7/§16; `08` §17 | `SCR-015`–`SCR-022` | `GET /analysis/bva` | `TST-BVA-08`, `TST-UI-01` | `Spec'd` |

### 3.5 `FR-EXC` — exception engine and register (20 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-EXC-001` | Rule run | P0 | 3 | `02` §8; `06` §2; `08` §14 | `SCR-014`, `SCR-023` | `POST /rules/run` | `TST-RUL-25`, `TST-PRF-07`, `TST-UI-13` | `Spec'd` |
| `FR-EXC-002` | Exception register | P0 | 3 | `02` §8; `08` §10.1 | `SCR-023` | `GET /exceptions` | `TST-EXC-07`, `TST-EXC-09` | `Spec'd` |
| `FR-EXC-003` | Deterministic evaluation only | P0 | 3 | `02` §8; `10` §6 | `SCR-023` | `POST /rules/run` | `TST-RUL-27`, `TST-AI-14` | `Spec'd` |
| `FR-EXC-004` | Stable exception identity | P0 | 3 | `02` §8; `06` §D.1 | `SCR-023` | `GET /exceptions/{id}` | `TST-RUL-27`, `TST-EXC-11` | `Spec'd` |
| `FR-EXC-005` | Re-run preserves workflow state | P0 | 3 | `02` §8; `06` §2.2 | `SCR-023` | `POST /rules/run` | `TST-RUL-27`, `TST-EXC-11` | `Spec'd` |
| `FR-EXC-006` | Status workflow | P0 | 3 | `02` §8; `06` §1.1 | `SCR-024` | `PATCH /exceptions/{id}` | `TST-EXC-01` | `Spec'd` |
| `FR-EXC-007` | Owner assignment | P0 | 3 | `02` §8; `03` §5.6; `06` §2.6 | `SCR-024`, `SCR-034` | `PATCH /exceptions/{id}` | `TST-EXC-05` | `Spec'd` |
| `FR-EXC-008` | Notes with history | P0 | 3 | `02` §8 | `SCR-024` | `PATCH /exceptions/{id}` | `TST-EXC-02` | `Spec'd` |
| `FR-EXC-009` | Aging and overdue | P1 | 3 | `02` §8; `06` §1.1 | `SCR-023`, `SCR-024` | `GET /exceptions` | `TST-EXC-04` | `Spec'd` |
| `FR-EXC-010` | Bulk operations | P1 | 3 | `02` §8 | `SCR-023` | `POST /exceptions/bulk` | `TST-EXC-03` | `Spec'd` |
| `FR-EXC-011` | Severity | P0 | 3 | `02` §8; `06` §3 | `SCR-023`, `SCR-024` | `GET /exceptions` | `TST-RUL-25`, `TST-UI-09` | `Spec'd` |
| `FR-EXC-012` | Per-project rule configuration | P0 | 3 | `02` §8; `06` §2.11; `08` §12 | `SCR-035` | `GET /rules`, `PUT /rules/{id}` | `TST-RUL-27`, `TST-UI-08` | `Spec'd` |
| `FR-EXC-013` | Global materiality | P1 | 3 | `02` §8; `05` §11 | `SCR-035` | `PUT /settings` | `TST-CALC-24`, `TST-RUL-27` | `Spec'd` |
| `FR-EXC-014` | Master-data dependencies degrade gracefully | P0 | 3 | `02` §8; `03` §5; `08` §12 | `SCR-014`, `SCR-023`, `SCR-034` | `GET /rules` | `TST-RUL-26`, `TST-UI-01` | `Spec'd` |
| `FR-EXC-015` | Rule effectiveness analytics | P1 | 3 | `02` §8; `06` §9 | `SCR-026` | `GET /exceptions/effectiveness` | `TST-RUL-28` | `Spec'd` |
| `FR-EXC-016` | Evidence bundle | P1 | 3 | `02` §8; `11` §6 | `SCR-025`, `SCR-024` | `POST /exceptions/{id}/evidence` | `TST-XL-21`, `TST-EXC-10` | `Spec'd` |
| `FR-EXC-017` | Owner-wise distribution | P1 | 3 | `02` §8; `11` §8 | `SCR-023` | `GET /exceptions/export` | `TST-XL-20` | `Spec'd` |
| `FR-EXC-018` | Register export | P0 | 3 | `02` §8; `11` §6/§8 | `SCR-023` | `GET /exceptions/export` | `TST-XL-19`, `TST-EXC-09`, `TST-UAT-02` | `Spec'd` |
| `FR-EXC-019` | Canonical wording | P0 | 3 | `02` §8; `06` §1.1; `08` §16 | `SCR-023`, `SCR-024` | `GET /exceptions` | `TST-EXC-08`, `TST-UI-10`, `TST-UAT-03` | `Spec'd` |
| `FR-EXC-020` | Rule-run performance | P0 | 3 | `02` §8; `06` §8.3; `14` §3 | `SCR-014` | `POST /rules/run` | `TST-PRF-07` | `Spec'd` |

### 3.6 `FR-FC` — rolling forecast (9 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-FC-001` | Locked actuals, forecasted remainder | P0 | 4 | `02` §9; `05` §9; `07` §2 | `SCR-027` | `GET /forecast/versions` | `TST-FC-10`, `TST-FC-14` | `Spec'd` |
| `FR-FC-002` | Four deterministic methods | P0 | 4 | `02` §9; `07` §3 | `SCR-027` | `POST /forecast/run` | `TST-FC-01`, `TST-FC-02`, `TST-FC-03`, `TST-FC-12` | `Spec'd` |
| `FR-FC-003` | Scenarios | P1 | 4 | `02` §9; `07` §5 | `SCR-027`, `SCR-028` | `POST /forecast/versions` | `TST-FC-09` | `Spec'd` |
| `FR-FC-004` | Forecast provenance | P0 | 4 | `02` §9; `07` §4 | `SCR-027` | `GET /forecast/versions` | `TST-FC-13`, `TST-FC-14` | `Spec'd` |
| `FR-FC-005` | Actuals are never overwritten | P0 | 4 | `02` §9; `07` §2; `03` §6 | `SCR-027` | `POST /forecast/run` | `TST-API-15`, `TST-FC-10` | `Spec'd` |
| `FR-FC-006` | Manual override with audit | P1 | 4 | `02` §9; `07` §6 | `SCR-027` | `PATCH /forecast/cells` | `TST-FC-13` | `Spec'd` |
| `FR-FC-007` | Forecast accuracy report | P1 | 4 | `02` §9; `05` §9; `07` §8 | `SCR-028` | `GET /forecast/accuracy` | `TST-FC-11` | `Spec'd` |
| `FR-FC-008` | Method-choice guidance | P2 | 4 | `02` §9; `07` §8.2 | `SCR-028` | `GET /forecast/accuracy` | `TST-FC-11` | `Spec'd` |
| `FR-FC-009` | Forecast versions and comparison | P1 | 4 | `02` §9; `07` §7 | `SCR-027`, `SCR-028` | `POST /forecast/versions/{v}/lock`, `GET /forecast/compare` | `TST-FC-10`, `TST-FC-09` | `Spec'd` |

### 3.7 `FR-XL` — Excel output pack (9 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-XL-001` | Generate the Excel pack | P0 | 5 | `02` §10; `11` §2/§4 | `SCR-029` | `POST /packs/excel` | `TST-XL-01`, `TST-XL-02`, `TST-WIN-10` | `Spec'd` |
| `FR-XL-002` | Format compliance | P0 | 5 | `02` §10; `11` §3; `08` §14 | `SCR-029` | `POST /packs/excel` | `TST-XL-07`, `TST-XL-11`, `TST-XL-13`, `TST-XL-26` | `Spec'd` |
| `FR-XL-003` | Refreshable from the project | P0 | 5 | `02` §10; `11` §3.8 | `SCR-029` | `GET /packs`, `POST /packs/{id}/refresh` | `TST-XL-04`, `TST-XL-12` | `Spec'd` |
| `FR-XL-004` | File naming and collision policy | P0 | 5 | `02` §10; `11` §8 | `SCR-029` | `POST /packs/excel` | `TST-XL-17`, `TST-XL-18` | `Spec'd` |
| `FR-XL-005` | Sheet row caps | P0 | 5 | `02` §10; `11` §5 | `SCR-029` | `POST /packs/excel` | `TST-XL-16` | `Spec'd` |
| `FR-XL-006` | Stamping | P0 | 5 | `02` §10; `11` §3.7 | `SCR-029` | `POST /packs/excel` | `TST-XL-04`, `TST-XL-05`, `TST-XL-26` | `Spec'd` |
| `FR-XL-007` | Evidence bundle workbook layout | P1 | 5 | `02` §10; `11` §6 | `SCR-025` | `POST /exceptions/{id}/evidence` | `TST-XL-21` | `Spec'd` |
| `FR-XL-008` | Cross-artifact consistency | P0 | 5 | `02` §10; `11` §7; `14` §7 | `SCR-029` | `POST /packs/excel` | `TST-XL-23`, `TST-PPT-13`, `TST-API-14` | `Spec'd` |
| `FR-XL-009` | Print/PDF readiness | P2 | 5 | `02` §10; `11` §10; `DEC-028` | `SCR-029` | `POST /packs/excel` | `TST-UI-19`, `TST-XL-07` | `Spec'd` |

### 3.8 `FR-PPT` — PowerPoint management pack (9 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-PPT-001` | Generate the six-slide deck | P0 | 5 | `02` §11; `12` §2/§4 | `SCR-029` | `POST /packs/deck` | `TST-PPT-01`, `TST-PPT-03`, `TST-WIN-10` | `Spec'd` |
| `FR-PPT-002` | Native, editable output | P0 | 5 | `02` §11; `12` §3.2 | `SCR-029` | `POST /packs/deck` | `TST-PPT-02`, `TST-PPT-04` | `Spec'd` |
| `FR-PPT-003` | Generation performance and UX | P0 | 5 | `02` §11; `12` §7; `14` §3 | `SCR-029` | `POST /packs/deck` | `TST-PPT-17`, `TST-PPT-18`, `TST-PRF-04` | `Spec'd` |
| `FR-PPT-004` | Text fitting | P0 | 5 | `02` §11; `12` §3.4 | `SCR-029` | `POST /packs/deck` | `TST-PPT-05`, `TST-PPT-06` | `Spec'd` |
| `FR-PPT-005` | Client base deck and house style | P2 | 6 | `02` §11; `12` §3.5 | `SCR-029`, `SCR-037` | `POST /packs/deck` | `TST-PPT-19`, `TST-PPT-20` | `Spec'd` |
| `FR-PPT-006` | Branding | P1 | 5 | `02` §11; `12` §3.3; `08` §19 | `SCR-037` | `PUT /settings` | `TST-PPT-10` | `Spec'd` |
| `FR-PPT-007` | Deterministic element ordering | P1 | 5 | `02` §11; `12` §3.6 | `SCR-029` | `POST /packs/deck` | `TST-PPT-08` | `Spec'd` |
| `FR-PPT-008` | AI commentary in the deck | P1 | 6 | `02` §11; `12` §3.4; `10` §5.1 | `SCR-029`, `SCR-031` | `POST /packs/deck` | `TST-PPT-11` | `Spec'd` |
| `FR-PPT-009` | Stamping and disclaimer | P0 | 5 | `02` §11; `12` §3.7; `01` §15.1 | `SCR-029` | `POST /packs/deck` | `TST-PPT-09`, `TST-PPT-21` | `Spec'd` |

### 3.9 `FR-AI` — optional AI commentary and suggestions (14 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-AI-001` | Optional, off by default, keyless-capable | P0 | 6 | `02` §12; `10` §1 | `SCR-038` | `GET /settings` | `TST-AI-10`, `TST-AI-11` | `Spec'd` |
| `FR-AI-002` | Bring-your-own-key configuration | P0 | 6 | `02` §12; `10` §2; `13` §5 | `SCR-038` | `PUT /settings/ai-key` | `TST-SEC-06`, `TST-SEC-08`, `TST-AI-10` | `Spec'd` |
| `FR-AI-003` | Key rotation and revocation | P1 | 6 | `02` §12; `13` §5.3; `23` | `SCR-038` | `DELETE /settings/ai-key` | `TST-SEC-10`, `TST-SEC-11` | `Spec'd` |
| `FR-AI-004` | Four AI features | P1 | 6 | `02` §12; `10` §4/§5 | `SCR-031`, `SCR-008`, `SCR-023` | `POST /ai/drafts` | `TST-AI-01`, `TST-AI-12` | `Spec'd` |
| `FR-AI-005` | Evidence linkage and confidence | P0 | 6 | `02` §12; `10` §6 | `SCR-031` | `GET /ai/drafts` | `TST-AI-06`, `TST-AI-12` | `Spec'd` |
| `FR-AI-006` | Strict schema validation | P0 | 6 | `02` §12; `10` §8 | `SCR-031` | `POST /ai/drafts` | `TST-AI-01`, `TST-AI-10` | `Spec'd` |
| `FR-AI-007` | Redaction and minimum data | P0 | 6 | `02` §12; `10` §7; `13` §11 | `SCR-038`, `SCR-031` | `POST /ai/drafts` | `TST-AI-05`, `TST-SEC-21` | `Spec'd` |
| `FR-AI-008` | Prompt-injection defence | P0 | 6 | `02` §12; `10` §9; `13` §11 | `SCR-031` | `POST /ai/drafts` | `TST-AI-03`, `TST-AI-04`, `TST-SEC-14` | `Spec'd` |
| `FR-AI-009` | Caps, usage log and caching | P0 | 6 | `02` §12; `10` §10 | `SCR-038` | `GET /ai/usage` | `TST-AI-08`, `TST-AI-09` | `Spec'd` |
| `FR-AI-010` | Number-mismatch policy | P0 | 6 | `02` §12; `10` §8.2 | `SCR-031` | `POST /ai/drafts` | `TST-AI-02` | `Spec'd` |
| `FR-AI-011` | Draft provenance and history | P1 | 6 | `02` §12; `10` §11 | `SCR-031` | `GET /ai/drafts` | `TST-AI-09`, `TST-AI-12` | `Spec'd` |
| `FR-AI-012` | Labelling | P0 | 6 | `02` §12; `10` §12; `12` §3.4 | `SCR-031`, `SCR-029` | `POST /ai/drafts` | `TST-AI-14`, `TST-PPT-11` | `Spec'd` |
| `FR-AI-013` | Offline/keyless fallback narrative | P0 | 6 | `02` §12; `10` §3.3 | `SCR-031` | `GET /commentary` | `TST-AI-10`, `TST-AI-11` | `Spec'd` |
| `FR-AI-014` | Data boundary and model pinning | P0 | 6 | `02` §12; `10` §13; `13` §13 | `SCR-038` | `POST /ai/test-connection` | `TST-AI-10`, `TST-AI-11`, `TST-SEC-02` | `Spec'd` |

### 3.10 `FR-SET` — settings, master data and display (12 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-SET-001` | Settings screen sections | P0 | 1 | `02` §13; `08` §12 | `SCR-032`–`SCR-038` | `GET /settings` | `TST-UI-20` | `Spec'd` |
| `FR-SET-002` | Mapping management | P0 | 1 | `02` §13; `04` §5; `08` §12 | `SCR-033` | `GET /mapping-profiles`, `PUT /mapping-profiles/{id}` | `TST-UI-20`, `TST-IMP-15` | `Spec'd` |
| `FR-SET-003` | Master data screens | P0 | 3 | `02` §13; `03` §5; `08` §12 | `SCR-034` | `GET /master-data/{kind}`, `PUT /master-data/{kind}` | `TST-UI-20`, `TST-EXC-05` | `Spec'd` |
| `FR-SET-004` | Rule configuration | P0 | 3 | `02` §13; `06` §2.11; `08` §12 | `SCR-035` | `GET /rules`, `PUT /rules/{id}` | `TST-RUL-27`, `TST-UI-08` | `Spec'd` |
| `FR-SET-005` | Fiscal calendar configuration | P0 | 1 | `02` §13; `05` §3; `03` §3 | `SCR-003` | `POST /projects` | `TST-CALC-15`, `TST-CALC-16` | `Spec'd` |
| `FR-SET-006` | Currency and unit display | P0 | 1 | `02` §13; `05` §6.3; `11` §3.6 | `SCR-036`, `SCR-003` | `PUT /settings` | `TST-CALC-23`, `TST-XL-08` | `Spec'd` |
| `FR-SET-007` | Uniform display locale | P0 | 1 | `02` §13; `11` §3; `12` §3.9 | `SCR-036` | `PUT /settings` | `TST-XL-23`, `TST-WIN-13` | `Spec'd` |
| `FR-SET-008` | Branding settings | P1 | 5 | `02` §13; `12` §3.3; `08` §19 | `SCR-037` | `PUT /settings` | `TST-PPT-10`, `TST-XL-10` | `Spec'd` |
| `FR-SET-009` | Storage locations and sync detection | P0 | 1 | `02` §13; `09` §7.3; `13` §8 | `SCR-032` | `GET /projects/{id}/storage`, `PUT /settings` | `TST-SEC-16`, `TST-WIN-06` | `Spec'd` |
| `FR-SET-010` | Stale-derived indicator | P0 | 2 | `02` §13; `08` §3.3; `05` §11 | Global (08 §3.3 shell) | `GET /checks` | `TST-UI-08`, `TST-XL-12` | `Spec'd` |
| `FR-SET-011` | Version history and revert | P0 | 1 | `02` §13; `03` §11 | `SCR-033`–`SCR-035`, `SCR-037` | `GET /projects/{id}/versions`, `POST /projects/{id}/versions/{v}/revert` | `TST-UI-20`, `TST-IMP-15` | `Spec'd` |
| `FR-SET-012` | Audit log viewer | P2 | 3 | `02` §13; `03` §5.7; `13` §13.2 | `SCR-040` | `GET /audit` | `TST-SEC-22`, `TST-UI-01` | `Spec'd` |

### 3.11 `FR-XC` — cross-cutting behaviour (16 FRs)

| FR | Requirement | P | Ph | Spec section(s) | Screen(s) | Endpoint(s) | Test ID(s) | Status |
|---|---|---|---|---|---|---|---|---|
| `FR-XC-001` | Commentary workflow | P1 | 5 | `02` §14; `10` §5; `08` §11.3 | `SCR-031`, `SCR-029` | `GET /commentary`, `PUT /commentary`, `POST /ai/drafts/{id}/approve` | `TST-PPT-11`, `TST-AI-12` | `Spec'd` |
| `FR-XC-002` | Commentary locks on issuance | P0 | 5 | `02` §14; `11` §3.7 | `SCR-030`, `SCR-031` | `POST /issuance` | `TST-E2E-02` | `Spec'd` |
| `FR-XC-003` | Pack issuance register | P1 | 5 | `02` §14; `08` §11.2 | `SCR-030` | `GET /issuance`, `POST /issuance/{id}/reissue` | `TST-E2E-02` | `Spec'd` |
| `FR-XC-004` | About / Diagnostics screen | P0 | 1 | `02` §14; `08` §12; `15` §9 | `SCR-040` | `GET /doctor`, `GET /health`, `POST /diagnostics` | `TST-E2E-07`, `TST-API-12`, `TST-WIN-11` | `Spec'd` |
| `FR-XC-005` | Diagnostics bundle with redaction | P0 | 1 | `02` §14; `13` §9; `15` §9.1 | `SCR-040` | `POST /diagnostics` | `TST-SEC-12`, `TST-SEC-13`, `TST-PRF-10` | `Spec'd` |
| `FR-XC-006` | Global error handling | P0 | 1 | `02` §14; `08` §16 | `SCR-041` | `GET /meta/error-catalog` | `TST-API-02`, `TST-SEC-18` | `Spec'd` |
| `FR-XC-007` | Logging policy | P0 | 1 | `02` §14; `13` §8; `NFR-011` | n/a — headless | `n/a (file-based logs)` | `TST-SEC-09`, `TST-SEC-13`, `TST-PRF-11` | `Spec'd` |
| `FR-XC-008` | Crash recovery and job resumption | P0 | 1 | `02` §14; `09` §8.3; `04` §15 | Global (08 §3.3 shell) | `GET /jobs`, `POST /jobs/{id}/cancel` | `TST-E2E-04`, `TST-WIN-09`, `TST-IMP-35` | `Spec'd` |
| `FR-XC-009` | Offline guarantee | P0 | 1 | `02` §14; `13` §2; `NFR-008` | n/a — headless | `n/a (network policy)` | `TST-E2E-03`, `TST-SEC-01`, `TST-SEC-02` | `Spec'd` |
| `FR-XC-010` | Data-volume rule | P0 | 2 | `02` §14; `09` §12 | Global (08 §3.3 shell) | `GET /analysis/bva`, `GET /exceptions` | `TST-API-03`, `TST-API-09`, `TST-UI-15` | `Spec'd` |
| `FR-XC-011` | Accessibility baseline | P0 | 1 | `02` §14; `08` §18 | Global (08 §3.3 shell) | `n/a (UI baseline)` | `TST-UI-05`, `TST-UI-07`, `TST-UI-09` | `Spec'd` |
| `FR-XC-012` | Error message catalog compliance | P0 | 1 | `02` §14; `08` §16; `26` | `SCR-041`; Global (08 §3.3 shell) | `GET /meta/error-catalog` | `TST-API-02`, `TST-UI-10` | `Spec'd` |
| `FR-XC-013` | Sample-data non-delivery guarantee | P1 | 5 | `02` §14; `14` §16; `15` §1.2 | n/a — headless | `n/a (release guard)` | `TST-SEC-17`, `TST-XL-26`, `TST-PPT-21` | `Spec'd` |
| `FR-XC-014` | Client support flow | P1 | 6 | `02` §14; `23`; `13` §9.3 | `SCR-042`, `SCR-040` | `GET /help` | `TST-UI-18`, `TST-E2E-07`, `TST-UAT-04` | `Spec'd` |
| `FR-XC-015` | Manual update check | P2 | 6 | `02` §14; `15` §8 | `SCR-040` | `POST /update-check` | `TST-SEC-02`, `TST-UI-20` | `Spec'd` |
| `FR-XC-016` | Local performance instrumentation | P2 | 6 | `02` §14; `08` §12; `14` §3 | `SCR-040` | `GET /instrumentation` | `TST-PRF-01` | `Spec'd` |

## 4. Coverage, invariants and reverse indexes

### 4.1 Counts

- **FRs joined:** 156 of 156 in `02` (100 %). No FR is missing and none appears twice.
- **Priority:** `P0` 110 · `P1` 39 · `P2` 7 (`02` §3; the never-cut list is `02` §3.3).
- **Phase:** 1 60 · 2 19 · 3 25 · 4 10 · 5 21 · 6 21.
- **Screens referenced:** 43 of the 43 in `08` §4 — every screen serves at least one FR (§4.3).
- **Shell-level rows:** 8 FRs are marked **Global** (on every screen through `08` §3.3): `FR-BVA-015`, `FR-IMP-030`, `FR-ONB-008`, `FR-SET-010`, `FR-XC-008`, `FR-XC-010`, `FR-XC-011`, `FR-XC-012`.
- **Non-visual rows:** 3 FRs carry an `n/a — <reason>` cell: `FR-XC-007`, `FR-XC-009`, `FR-XC-013`.
- **Endpoints in the reference set:** 95, in nine areas; every route serves ≥ 1 FR (I7).
- **Distinct test IDs assigned:** 188 of the 292 frozen inventory IDs; every FR has ≥ 1 (I1) and every ID resolves (I2).

| Family | FRs | P0 | P1 | P2 | Phases | Distinct tests |
|---|---|---|---|---|---|---|
| `FR-ONB` | 8 | 5 | 2 | 1 | 1, 2, 6 | 11 |
| `FR-PRJ` | 12 | 9 | 3 | 0 | 1, 3 | 15 |
| `FR-IMP` | 31 | 23 | 8 | 0 | 1, 2, 6 | 44 |
| `FR-BVA` | 16 | 12 | 4 | 0 | 2, 4 | 25 |
| `FR-EXC` | 20 | 14 | 6 | 0 | 3 | 27 |
| `FR-FC` | 9 | 4 | 4 | 1 | 4 | 10 |
| `FR-XL` | 9 | 7 | 1 | 1 | 5 | 18 |
| `FR-PPT` | 9 | 5 | 3 | 1 | 5, 6 | 17 |
| `FR-AI` | 14 | 11 | 3 | 0 | 6 | 20 |
| `FR-SET` | 12 | 10 | 1 | 1 | 1, 2, 3, 5 | 18 |
| `FR-XC` | 16 | 10 | 4 | 2 | 1, 2, 5, 6 | 33 |
| **Total** | **156** | **110** | **39** | **7** | 1–6 | **188** |

### 4.2 Invariants (the acceptance checks for this document)

| ID | Invariant | How it is checked |
|---|---|---|
| **I1** | Every FR in `02` has exactly one row here, and every row has ≥ 1 test ID | Doc-lint: parse `02` headings, parse the matrix, diff both ways (`scripts/check`) |
| **I2** | Every test ID resolves to the frozen inventory (`14` §4) | Regex + whitelist (16 families, 292 IDs) |
| **I3** | Every endpoint cell resolves to the §2.3 reference set | Regex + the 95-route catalogue |
| **I4** | Every screen token is a `SCR-nnn` from `08` §4, `Global`, or a justified `n/a` | Regex + the §2.2 token list |
| **I5** | Priorities and phases equal `02`'s | Re-parse `02` and compare, per FR |
| **I6** | Every `SCR-nnn` in `08` §4 is served by ≥ 1 FR, and the inventory's FR column equals this join | Reverse index §4.3 vs `08` §4 |
| **I7** | Every endpoint has ≥ 1 FR consumer and carries a `26` contract test | §2.3 vs `26`; `14` §12.3 |
| **I8** | The area map (§4.4) and the test-family map (§4.5) agree with the rows | Recompute and diff |
| **I9** | Status values come only from §1.3; a `Complete` row names a green gate run | Manual at gates + `16` §5.2 |

### 4.3 Reverse index — screen → FRs

`08` §4's **Owning FRs** column is generated from this index (I6); a screen with no FR would be an orphan
screen and is itself a defect. Counts are FRs per screen.

| Screen | Name (from `08` §4) | FRs | Count |
|---|---|---|---|
| `SCR-001` | Home | `FR-ONB-001`, `FR-ONB-003`, `FR-ONB-005`, `FR-ONB-006`, `FR-ONB-008`, `FR-PRJ-001`, `FR-PRJ-004`, `FR-PRJ-005`, `FR-PRJ-010` | 9 |
| `SCR-002` | Project launcher (modal) | `FR-ONB-001`, `FR-ONB-006`, `FR-PRJ-002`, `FR-PRJ-003`, `FR-PRJ-006`, `FR-PRJ-007`, `FR-PRJ-009`, `FR-PRJ-012` | 8 |
| `SCR-003` | New Project wizard | `FR-PRJ-002`, `FR-SET-005`, `FR-SET-006` | 3 |
| `SCR-004` | New Period wizard | `FR-PRJ-004`, `FR-PRJ-005` | 2 |
| `SCR-005` | Import — 1 Choose file | `FR-ONB-003`, `FR-ONB-005`, `FR-IMP-001`, `FR-IMP-002`, `FR-IMP-010`, `FR-IMP-019`, `FR-IMP-031` | 7 |
| `SCR-006` | Import — 2 Pre-scan | `FR-IMP-003` | 1 |
| `SCR-007` | Import — 3 Sheet & header | `FR-IMP-007`, `FR-IMP-009`, `FR-IMP-010`, `FR-IMP-012`, `FR-IMP-027` | 5 |
| `SCR-008` | Import — 4 Map columns | `FR-IMP-004`, `FR-IMP-005`, `FR-IMP-006`, `FR-IMP-008`, `FR-IMP-011`, `FR-IMP-012`, `FR-IMP-026`, `FR-AI-004` | 8 |
| `SCR-009` | Import — 5 Validate | `FR-IMP-007`, `FR-IMP-009`, `FR-IMP-014`, `FR-IMP-015`, `FR-IMP-017`, `FR-IMP-019`, `FR-IMP-021`, `FR-IMP-027`, `FR-IMP-030` | 9 |
| `SCR-010` | Import — 6 Commit & confirm | `FR-IMP-016`, `FR-IMP-018`, `FR-IMP-020`, `FR-IMP-022`, `FR-IMP-028`, `FR-IMP-031` | 6 |
| `SCR-011` | Import History | `FR-IMP-023`, `FR-IMP-024`, `FR-IMP-025`, `FR-IMP-026` | 4 |
| `SCR-012` | Batch detail / validation report | `FR-IMP-016`, `FR-IMP-017`, `FR-IMP-021`, `FR-IMP-025` | 4 |
| `SCR-013` | Quarantine review | `FR-IMP-013` | 1 |
| `SCR-014` | Check | `FR-IMP-014`, `FR-IMP-022`, `FR-EXC-001`, `FR-EXC-014`, `FR-EXC-020` | 5 |
| `SCR-015` | Analyze — BvA matrix | `FR-BVA-001`, `FR-BVA-002`, `FR-BVA-003`, `FR-BVA-009`, `FR-BVA-011`, `FR-BVA-013`, `FR-BVA-014`, `FR-BVA-016` | 8 |
| `SCR-016` | Analyze — Bridge | `FR-BVA-005`, `FR-BVA-011`, `FR-BVA-016` | 3 |
| `SCR-017` | Analyze — Trends | `FR-BVA-006`, `FR-BVA-011`, `FR-BVA-016` | 3 |
| `SCR-018` | Analyze — Top-N | `FR-BVA-007`, `FR-BVA-011`, `FR-BVA-016` | 3 |
| `SCR-019` | Analyze — Three-way | `FR-BVA-008`, `FR-BVA-011`, `FR-BVA-016` | 3 |
| `SCR-020` | Analyze — KPIs | `FR-BVA-010`, `FR-BVA-011`, `FR-BVA-016` | 3 |
| `SCR-021` | Drill-through | `FR-BVA-004`, `FR-BVA-011`, `FR-BVA-016` | 3 |
| `SCR-022` | Search | `FR-BVA-011`, `FR-BVA-012`, `FR-BVA-016` | 3 |
| `SCR-023` | Exceptions register | `FR-EXC-001`, `FR-EXC-002`, `FR-EXC-003`, `FR-EXC-004`, `FR-EXC-005`, `FR-EXC-009`, `FR-EXC-010`, `FR-EXC-011`, `FR-EXC-014`, `FR-EXC-017`, `FR-EXC-018`, `FR-EXC-019`, `FR-AI-004` | 13 |
| `SCR-024` | Exception detail | `FR-EXC-006`, `FR-EXC-007`, `FR-EXC-008`, `FR-EXC-009`, `FR-EXC-011`, `FR-EXC-016`, `FR-EXC-019` | 7 |
| `SCR-025` | Evidence bundle export (modal) | `FR-EXC-016`, `FR-XL-007` | 2 |
| `SCR-026` | Rule effectiveness | `FR-EXC-015` | 1 |
| `SCR-027` | Forecast workspace | `FR-FC-001`, `FR-FC-002`, `FR-FC-003`, `FR-FC-004`, `FR-FC-005`, `FR-FC-006`, `FR-FC-009` | 7 |
| `SCR-028` | Forecast comparison & accuracy | `FR-FC-003`, `FR-FC-007`, `FR-FC-008`, `FR-FC-009` | 4 |
| `SCR-029` | Reports — Generate pack | `FR-XL-001`, `FR-XL-002`, `FR-XL-003`, `FR-XL-004`, `FR-XL-005`, `FR-XL-006`, `FR-XL-008`, `FR-XL-009`, `FR-PPT-001`, `FR-PPT-002`, `FR-PPT-003`, `FR-PPT-004`, `FR-PPT-005`, `FR-PPT-007`, `FR-PPT-008`, `FR-PPT-009`, `FR-AI-012`, `FR-XC-001` | 18 |
| `SCR-030` | Pack issuance register | `FR-PRJ-010`, `FR-XC-002`, `FR-XC-003` | 3 |
| `SCR-031` | Commentary editor | `FR-PPT-008`, `FR-AI-004`, `FR-AI-005`, `FR-AI-006`, `FR-AI-007`, `FR-AI-008`, `FR-AI-010`, `FR-AI-011`, `FR-AI-012`, `FR-AI-013`, `FR-XC-001`, `FR-XC-002` | 12 |
| `SCR-032` | Settings — Data & storage | `FR-PRJ-011`, `FR-SET-001`, `FR-SET-009` | 3 |
| `SCR-033` | Settings — Mappings | `FR-IMP-005`, `FR-IMP-026`, `FR-SET-001`, `FR-SET-002`, `FR-SET-011` | 5 |
| `SCR-034` | Settings — Master data | `FR-IMP-029`, `FR-EXC-007`, `FR-EXC-014`, `FR-SET-001`, `FR-SET-003`, `FR-SET-011` | 6 |
| `SCR-035` | Settings — Thresholds & rules | `FR-EXC-012`, `FR-EXC-013`, `FR-SET-001`, `FR-SET-004`, `FR-SET-011` | 5 |
| `SCR-036` | Settings — Display & locale | `FR-SET-001`, `FR-SET-006`, `FR-SET-007` | 3 |
| `SCR-037` | Settings — Branding | `FR-PPT-005`, `FR-PPT-006`, `FR-SET-001`, `FR-SET-008`, `FR-SET-011` | 5 |
| `SCR-038` | Settings — AI | `FR-AI-001`, `FR-AI-002`, `FR-AI-003`, `FR-AI-007`, `FR-AI-009`, `FR-AI-014`, `FR-SET-001` | 7 |
| `SCR-039` | Backup & restore | `FR-PRJ-008`, `FR-PRJ-009` | 2 |
| `SCR-040` | About / Diagnostics | `FR-PRJ-011`, `FR-SET-012`, `FR-XC-004`, `FR-XC-005`, `FR-XC-014`, `FR-XC-015`, `FR-XC-016` | 7 |
| `SCR-041` | Error dialog (global) | `FR-XC-006`, `FR-XC-012` | 2 |
| `SCR-042` | Help panel (global overlay) | `FR-ONB-004`, `FR-ONB-007`, `FR-XC-014` | 3 |
| `SCR-043` | First-run tour overlay | `FR-ONB-002` | 1 |

**Global shell components** (`08` §3.3) serve `FR-BVA-015`, `FR-IMP-030`, `FR-ONB-008`, `FR-SET-010`, `FR-XC-008`, `FR-XC-010`, `FR-XC-011`, `FR-XC-012` — they are not screens and are not counted in the 43.

### 4.4 Reverse index — endpoint area → FRs served

| Area | Endpoints | FRs served |
|---|---|---|
| Lifecycle — projects, periods, storage | 19 | 19 |
| Imports and batches | 11 | 28 |
| Mapping profiles, master data, rules, settings | 15 | 25 |
| Analysis and search | 9 | 16 |
| Exceptions | 7 | 15 |
| Forecast | 7 | 9 |
| Packs, issuance, commentary, templates | 10 | 21 |
| Optional AI | 7 | 12 |
| Operations, diagnostics, meta | 10 | 11 |
| **Total** | **95** | **152** FRs cite ≥ 1 route; 4 are non-networked policies (`n/a`) |

The per-endpoint reverse index (endpoint → FR + consuming screen) is published by `26` (`14` §12.3); this
document keeps the FR → endpoint direction.

### 4.5 Test-family usage

| Family | FRs citing it | Family | FRs citing it |
|---|---|---|---|
| `TST-AI` | 16 | `TST-PPT` | 17 |
| `TST-API` | 6 | `TST-PRF` | 8 |
| `TST-BVA` | 15 | `TST-RUL` | 10 |
| `TST-CALC` | 10 | `TST-SEC` | 19 |
| `TST-E2E` | 18 | `TST-UAT` | 6 |
| `TST-EXC` | 14 | `TST-UI` | 43 |
| `TST-FC` | 10 | `TST-WIN` | 10 |
| `TST-IMP` | 31 | `TST-XL` | 20 |

## 5. Gate interface

| Gate check | What it asks | This document's contribution | Status after this pass |
|---|---|---|---|
| `GATE-01-01` | Every FR numbered, testable, with acceptance criteria; zero blocking TBDs | The 156-row inventory proves one row per FR; acceptance criteria remain in `02` | ✅ |
| `GATE-01-09` | `20` links every FR to at least one future test | I1 + the test column (188 distinct IDs from the 292) | ✅ |
| `GATE-03-08` | Screen inventory exists; the chain includes screen IDs and API endpoints | Screen column (43 `SCR`), endpoint column (95 routes); the catalogue itself lands with `26` | ✅ (chain; catalogue finalised by `26`) |
| `GATE-05-02` | Standard doc header on every doc; TL;DR ≤ 15 lines | Header block + a 10-line TL;DR | ✅ |
| `GATE-05-03` | Source-of-Truth Matrix; no duplicated formula/threshold | This document owns only the join; §1.1 restates the mapping rules | ✅ |

## 6. Audit of this pass

### 6.1 Non-blocking client-fact dependencies

These `OQ-` items change *detail*, never the promise: each FR below behaves per its documented default
until `21` returns the client's answer, and the answer is then recorded as a `DEC` row (`18` §4/§5). The
**question ↔ risk** join (what happens if the answer never comes) is kept in `25_RISK_REGISTER.md` §4, one
row per line below.

| Client fact | `OQ-` | `Q-` | FRs whose detail it changes | Default in force today |
|---|---|---|---|---|
| D365 edition/export column set | `OQ-001` | `Q-002` | `FR-IMP-002`, `FR-IMP-004`, `FR-IMP-005`, `FR-IMP-011` | Generic D365-style template + documented dimension parsing (`04` §2/§7) |
| The two other systems' column lists | `OQ-002` | `Q-003` | `FR-IMP-002`, `FR-IMP-005`, `FR-IMP-010`, `FR-IMP-011` | Two distinct shapes: payroll summary and procurement/bank ledger (`04` §2) |
| Fiscal calendar (year start, periods) | `OQ-003` | `Q-004` | `FR-PRJ-004`, `FR-PRJ-005`, `FR-SET-005`, `FR-BVA-002`, `FR-BVA-016` | January start, 12 monthly periods, configurable (`03` §3) |
| Prior-year data availability | `OQ-004` | `Q-005` | `FR-BVA-002`, `FR-BVA-016`, `FR-FC-002` | PY views built; hidden with a note when no PY batch exists (`02` §16 E1) |
| Single vs multiple currency | `OQ-005` | `Q-006` | `FR-SET-006`, `FR-IMP-011` | Single reporting currency; mixed-currency rows quarantine (`02` §16 E10) |
| Budget versions and revisions | `OQ-006` | `Q-007` | `FR-IMP-027`, `FR-IMP-028`, `FR-BVA-003` | One budget version per period; a re-import replaces atomically (`04` §14) |
| Approval thresholds | `OQ-007` | `Q-009` | `FR-EXC-013`, `FR-EXC-014`, `FR-SET-003` | Global materiality `max(₹500,000, 2 % × \|budget\|)` (`05` §11) |
| Recurring-cost list | `OQ-008` | `Q-010` | `FR-EXC-014`, `FR-SET-003` | Rule auto-disables with a visible notice until the list is loaded (`06` §4 `EXC-015`, §2.9) |
| Vendor master and categories | `OQ-009` | `Q-011` | `FR-EXC-014`, `FR-SET-003`, `FR-EXC-007` | Vendor-category rules auto-disable; owner auto-assign falls back to manual (`03` §5.6, `06` §2.6) |
| Current Excel/PPT outputs | `OQ-010`, `OQ-021` | `Q-012` | `FR-XL-001`, `FR-XL-002`, `FR-PPT-001` | Documented layouts in `11`/`12`; pack assumed `.xlsx`/`.pptx` |
| Pack recipients | `OQ-011` | `Q-013` | `FR-XC-003`, `FR-XC-014` | Recipients typed per issue; the product has no send path (`13` §1) |
| Code-signing certificate | `OQ-012` | `Q-015` | — (packaging, `15` §8) | Unsigned v1 + documented SmartScreen path (`ADR-003`) |
| Real file sizes seen in practice | `OQ-013` | `Q-014` | `FR-IMP-003`, `FR-IMP-030`, `FR-XC-010` | Limits per `NFR-002` (250k rows / ~100 MB) with explicit over-limit confirmation |
| One sanitized real month, isolated local pilot only | `OQ-014` | `Q-001` | all analysis FRs at UAT (`28`) | Sample-data corpus until the real month is made available locally at `GATE-13`; never sent into development (`14` §16, `13` §3.1) |
| Logo and brand colours | `OQ-015` | `Q-019` | `FR-SET-008`, `FR-PPT-006` | PRD placeholder branding (`01` §17) |
| Support/warranty terms | `OQ-016` | `Q-018` | `FR-XC-014`, `23` | Support flow documented in `23`; terms pending |
| Installer delivery channel | `OQ-017` | `Q-016` | `FR-XC-015`, `15` §8 | Manual download; update check disabled by default (`FR-XC-015`) |
| Preferred default units | `OQ-022` | `Q-006` | `FR-SET-006`, `FR-XL-002` | Whole rupees with the unit label always shown (`05` §6.3) |

### 6.2 Evidence to strengthen in Phase 1 (existing tests only)

Eight FRs are specified and acceptance-criteria'd, but their assigned evidence is currently an umbrella
test (a state sweep, a round-trip, a contract check). Phase 1 extends the existing test — **no new IDs,
no renumbering** (`14` §1.2):

| FR | Why the current evidence is thin | Action (extend an existing test) |
|---|---|---|
| `FR-IMP-007` | Outdated-template warning has no named assertion | Add the warning string to the `TST-UI-10` catalogue and a template-version case to the `TST-IMP-01` fixture set |
| `FR-IMP-012` | Formula/error-cell policy is asserted only through numeric parsing | Extend `TST-IMP-16` with a formula-without-cached-value row and an error-cell column |
| `FR-IMP-023` | History listing relies on the generic state sweep | Extend `TST-UI-01` with staged/committed/voided/rejected rows and their links |
| `FR-IMP-028` | Atomic replace is covered; the old-vs-new diff summary is not | Extend `TST-IMP-35` with the diff-summary assertion (totals, line counts, no silent merge) |
| `FR-FC-004` | Provenance is asserted indirectly | Extend `TST-FC-13` with method, scenario, generated-at, user and driver-reference assertions per row |
| `FR-FC-005` | "Actuals never overwritten" is asserted indirectly | Extend `TST-API-15` with a hash comparison before/after regenerate and delete |
| `FR-XL-003` | Refresh is covered; "states exactly what changed" is not | Extend `TST-XL-04` with the refresh change-summary assertions (period, batch IDs, row counts, values-changed) |
| `FR-XC-015` | Update check is covered only as a call site | Extend `TST-SEC-02` with the "never auto-installs" assertion and `TST-UI-20` with the disabled-by-default toggle |

### 6.3 Obligations on `26` (endpoint reconciliation)

1. **Adopt or rename:** every one of the 95 routes in §2.3 appears in `26` with the same path, or the rename
   is recorded in `26`, `CHANGELOG` and this document in the same change.
2. **Reverse index:** `26` publishes endpoint → FR + consuming screen (this document keeps FR → endpoint).
3. **Error catalog:** `26` owns the numeric codes; `08` §16 owns the message catalog shape (`GATE-04-10`).
4. **Contract tests:** each route carries a `TST-API-*` contract test and a generated TypeScript type
   (`TST-API-07`/`08`); an endpoint with no consumer is deleted (`14` §12.3).

### 6.4 Document fixes made in this pass

- `08` §4 — the **Owning FRs** column is regenerated from §4.3, so the inventory's FR links are exact
  (previously they named the primary FRs only); a **Global shell components** line names the five
  shell-level FRs that no single screen owns. No screen, state or behaviour changed.
- `14` §15.1 — `GATE-01-09` set to ✅; `14` §15.3 — `GATE-03-08` note clarified to "chain complete here;
  endpoint catalogue finalised by `26`".
- `00_INDEX` — doc-map row 20 and the completeness counters; `16` §1.3 — next open item advanced to `21`.
- **Section pointers corrected (16 cells, 2026-10-01, doc-21 pass)** — the `21` pass exposed section
  cites that resolved to the wrong topic: `05` §4.4→§11 (materiality), `05` §10→§6.3 (units), `06` §7→§2.11
  (rule configuration) and `06` §4 `EXC-015`/§2.9 (recurring-cost rule), `03` §5.5→§5.6 (`FR-EXC-007`) and
  `06` §2.6 (owner assignment), `09` §10→§7.1 (backup/restore paths), `09` §11→§8.2/§8.3 (job UX, crash
  recovery), `09` §11→§12 (`FR-XC-010` only) and `09` §11→`03` §5.4 (`FR-PRJ-010` snapshots), `09` §11→`08`
  §6.3 (`FR-PRJ-005`). Matrix rows and §6.1 now agree with the owning documents; no FR, screen, endpoint,
  test or status changed.

## 7. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `26` | Adopt/rename the 95 routes, publish the reverse index, cover each with contract tests and generated types (§6.3) |
| `14` | Keep the 292-ID inventory frozen; strengthen the eight FRs in §6.2; keep I1–I8 mechanically checkable |
| `16` | Read the status column at every phase gate: a phase closes only when its FRs are `Built` with green tests (`16` §5.1) |
| `02` | Keep one row per FR: an FR added, split or retired updates §4–§14 and this matrix in the same change |
| `08` | Keep the §4 FR column equal to §4.3 here; a new screen needs an FR (I6) |
| `27` | An FR deferred to a later release is recorded there and stays `Spec'd` here — FRs are never deleted |
| `29` | The client-facing promise table maps to FR IDs from this document (plain-language titles only) |
| `22` | Task topics key to `SCR-nnn` (from §4.3) and cite the FR they serve |

## 8. Change control for this document

1. **Any change that touches behaviour updates this matrix in the same change** — spec first, then tests,
   then code, then here (`19` §5.1). A row that no longer matches its FR is a defect, not a comment.
2. Adding/retiring an FR: update `02` §2/§3 and this matrix together; retired IDs are tombstoned with a
   reason, never reused (same discipline as `18`'s `OQ-020`).
3. Adding a screen/endpoint/test: update the owning doc first (`08`/`26`/`14`), then the row, then the
   reverse index (§4.3–§4.5) and the invariants.
4. A gate run records which rows turned `Built`/`Complete`; the column is the release dashboard.
5. The mechanical invariants (I1–I5, I8) run in `scripts/check`; a red-lint commit is not merged.

## 9. Frozen constants and conventions in this document

| Constant | Value | Source |
|---|---|---|
| FR count | **156** across 11 families | `02` §2 |
| Priority split | `P0` 110 · `P1` 39 · `P2` 7 | `02` §3 |
| Delivery phases | 1–6 | `16` |
| Screen inventory | 43 (`SCR-001`…`SCR-043`), all served | `08` §4 |
| Chart inventory | 12 (`CHT-001`…`CHT-012`) | `08` §13 |
| Conditional-format rules | 12 (`CF-001`…`CF-012`) | `08` §14 |
| Test inventory | 292 IDs, 16 families | `14` §4 |
| Endpoint reference set | 95 routes, nine areas, `/api/v1` base | §2.3 (`26` owns the contract) |
| Status vocabulary | `Spec'd` · `Built` · `Complete` | §1.3 |
| Chain column set | FR · P · Phase · spec · screen · endpoint · test · status | `02` §17 |
| Invariants | I1–I9 | §4.2 |
| Strengthening list | 8 FRs, existing tests only | §6.2 |
| Conflict rule | Owning doc wins; this document is corrected | `00_INDEX` §6 (Addon 4 §C) |

