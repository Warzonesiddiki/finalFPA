> **Status:** Draft v0.1 — living document (updated every session)
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** meta — navigation, coverage, ownership, IDs, gates
> **TL;DR (≤ 15 lines):** This is the entry point for the whole documentation set. Read section 2 for
> the reading plans, section 3 for the document map, section 4 for the Addon Coverage Matrix (all 64
> spec sections → owning doc → status), section 5 for the Source-of-Truth Matrix (one owner per fact
> type), section 6 for the document standard and header template, section 8 for the permanent ID
> registry, and section 9 for the live quality-gate tracker. Phase 0 is complete only when every row of
> section 4 reads `INTEGRATED` and all five gates in section 9 pass. Never bulk-read the whole doc set:
> follow the session reading plan (2.2). No product code until approval is recorded (section 12).

---

# 00 — INDEX, COVERAGE MATRIX & DOC GOVERNANCE

## 1. Purpose of this document

`00_INDEX.md` is the single navigational and governance authority for the documentation set. It exists
so that a context-limited agent (or a new human developer) can find the one document that owns any
given fact **without reading 29 files**, and so that nothing in the spec of record can be silently
dropped. It is a living document: it is updated at every session and every phase gate.

It owns four things (nothing else lives here):

1. The **document map** and reading order (sections 2–3).
2. The **Addon Coverage Matrix** — every section of the kickoff prompt and Addons 1–4, mapped to the
   document that owns it, with integration status (section 4).
3. The **Source-of-Truth Matrix**, the document standard, and conflict-resolution rules (sections 5–6).
4. The **ID namespace registry** and the **quality-gate tracker** (sections 8–9).

## 2. Reading plans

### 2.1 Reading plans by audience

| Audience | Order |
|---|---|
| **AI agent, start of session (mandatory)** | 2.2 below — never bulk-read |
| **New human developer** | `01` → `02` → `03` → `09` → `17` → `19` → `16` → then task-specific docs |
| **Consultant / support engineer** | `23` → `09` → `15` → `24` → `13` → `26` |
| **Client (finance director, non-technical)** | `29` (requirements pack) → `22` (user guide) → `28` §UAT |
| **Authoring order for Phase 0 (this build)** | `00` → `20` + `CHANGELOG` → `21`–`25` → `26` → `27`–`28` → `29` (per Addon 4 §L) |

### 2.2 Session reading plan (Addon 4 §B.2 — mandatory, in order)

1. `00_INDEX.md` incl. the Coverage Matrix (§4) and gate tracker (§9).
2. `CHANGELOG.md` — entries since the last session only.
3. `SESSION_LOG.md` — tail (last 2–3 entries).
4. `16_ROADMAP_PHASES.md` — the next open item.
5. **Only the owning docs for today's task**, per the Source-of-Truth Matrix (§5).
6. `19_VIBE_CODING_PLAYBOOK.md` — session rules, quote-before-code, blocking questions.

**Never bulk-read all documents.** If a behaviour question arises, answer it by **quoting the owning
doc**, never from memory. If the owning doc is silent, raise a blocking question (Addon 2 §H.3).

### 2.3 Reading level and tone

`29_CLIENT_REQUIREMENTS_PACK.md` and `22_END_USER_GUIDE.md` are written for a finance director with no
IT background (no FR IDs, no jargon). All other docs are written for engineers and are expected to be
precise, terse, and testable.

## 3. Document map

30 documents + 2 process files. "Owns" = the fact type that lives **in full** in that document
(everything else must cross-reference, never duplicate).

| # | File | Owns | Status |
|---|---|---|---|
| 00 | `00_INDEX.md` | Navigation, Coverage Matrix, Source-of-Truth Matrix, ID registry, gate tracker | Draft v0.1 |
| 01 | `01_PRD.md` | Scope, personas, JTBD, success metrics, in/out decisions, branding, disclaimer, IP stance | Draft v0.1 |
| 02 | `02_FUNCTIONAL_SPEC.md` | All features as numbered FRs with priority P0/P1/P2, I/O, edge cases, acceptance criteria | Draft v0.1 |
| 03 | `03_DATA_DICTIONARY.md` | Tables, columns, types, grains, identities, nullability, example rows | Draft v0.1 |
| 04 | `04_SOURCE_MAPPING_AND_IMPORT_SPEC.md` | Import wizard, profiles, file quirks, validation, quarantine rules | Draft v0.1 |
| 05 | `05_CALCULATION_SPEC.md` | Formulas, tolerances, rounding, fiscal calendar, worked examples | Draft v0.1 |
| 06 | `06_EXCEPTION_RULES_CATALOG.md` | Every exception rule: logic, thresholds, severity, owner, test case | Draft v0.1 |
| 07 | `07_FORECAST_METHODS_SPEC.md` | Forecast methods, scenarios, locks, accuracy metrics | Draft v0.1 |
| 08 | `08_UI_UX_SPEC.md` | Screens (SCR-), charts (CHT-), formatting rules, copy, states, a11y | Not started |
| 09 | `09_TECHNICAL_ARCHITECTURE.md` | Stack, ADRs, engine boundary, storage, CLI, scripts, jobs, migrations | Not started |
| 10 | `10_AI_INTEGRATION_SPEC.md` | AI policy, the four prompt texts, schemas, redaction, caps, provenance | Not started |
| 11 | `11_EXCEL_OUTPUT_SPEC.md` | Excel pack layouts, naming, formats, row caps, consistency | Not started |
| 12 | `12_POWERPOINT_OUTPUT_SPEC.md` | Slide-by-slide spec, placeholders, character budgets, base deck | Not started |
| 13 | `13_SECURITY_PRIVACY.md` | Local-only guarantees, secrets, key rotation, logs, redaction, data at rest | Not started |
| 14 | `14_TESTING_QA_PLAN.md` | Test cases, NFR numbers, perf baselines, coverage bars, 58 gate checks | Not started |
| 15 | `15_PACKAGING_DEPLOYMENT_RUNBOOK.md` | Build → installer → clean-Win11 validation → SmartScreen → diagnostics | Not started |
| 16 | `16_ROADMAP_PHASES.md` | Phases, estimates, gate artifacts, release cadence, next open item | Not started |
| 17 | `17_CODING_STANDARDS.md` | Repo layout, naming, commits, branching, engine boundary, code health | Not started |
| 18 | `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` | Glossary, assumptions, open questions (OQ-), **Decided log (DEC-)** | Not started |
| 19 | `19_VIBE_CODING_PLAYBOOK.md` | Session protocol, principles P1–P20, quote-before-code, gates/approvals | Not started |
| 20 | `20_REQUIREMENTS_TRACEABILITY.md` | FR → spec → SCR → API → test → status chain | Not started |
| 21 | `21_CLIENT_ONBOARDING_QUESTIONNAIRE.md` | Every client question (Q-), why it matters, default if unanswered | Not started |
| 22 | `22_END_USER_GUIDE.md` | Task-structured user manual keyed to SCR-IDs; in-app help source | Not started |
| 23 | `23_CONSULTANT_HANDOVER_AND_SUPPORT.md` | Rebuild, config/prompt/branding editing, diagnostics, escalation | Not started |
| 24 | `24_RELEASE_AND_VERSIONING_RUNBOOK.md` | Semver, tags, release checklist, upgrade/migration test, distribution | Not started |
| 25 | `25_RISK_REGISTER.md` | Risks (RISK-) with likelihood/impact/mitigation/owner; reviewed at gates | Not started |
| 26 | `26_API_CONTRACT.md` | Endpoints, error envelope, pagination, error-code catalog, OpenAPI workflow | Not started |
| 27 | `27_BACKLOG.md` | Every parked item (BL-) with trigger, size, source, target phase | Not started |
| 28 | `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | DoD, UAT mechanics, defects (DEF-), pilot tie-out, go-live, sign-off | Not started |
| 29 | `29_CLIENT_REQUIREMENTS_PACK.md` | Plain-language client pack + sign-off block | Not started |
| — | `CHANGELOG.md` | Every doc/spec change (Keep a Changelog + semver) and gate approvals | Living |
| — | `SESSION_LOG.md` | Append-only session memory: what changed, FRs touched, tests, next step | Living |
| — | `PHASE0_SUMMARY.md` | One-page Phase 0 presentation (written at the end of Phase 0) | Not started |

**Supporting artifacts** (created at Phase 0 completion, governed by the docs above):
`sample-data/` (generator, D365 + two non-D365 shapes, `.xlsx` templates, ~40 planted exceptions,
`expected_exceptions.csv`, `malformed/` corpus, `--scale 250000` mode), root `README.md`.

## 4. Addon Coverage Matrix (Addon 2 §A.3, extended by Addons 3 §A.3 and 4 §A.3)

**One row per section of the spec of record (15 + 16 + 10 + 11 + 12 = 64 rows).** The matrix is
complete only when every row reads `INTEGRATED`. A row is `INTEGRATED` when the owning doc contains
the requirement **and** the change is recorded in `CHANGELOG.md`.

Status legend: `PENDING` = owning doc not yet written · `IN PROGRESS` = owning doc drafted, additions
still landing · `INTEGRATED` = requirement present in the owning doc + CHANGELOG entry.

### 4.1 Kickoff prompt (Sections 1–15) — 15 rows

| Ref | Requirement | Owning doc(s) | Status |
|---|---|---|---|
| K-S1 | Role: lead product engineer/architect/delivery lead; spec-first; docs before code | `19`, `01` | PENDING |
| K-S2 | Product & client context: current manual workflow, Windows 11 x64, non-technical user, offline, self-contained installer, clean start | `01`, `21` | IN PROGRESS |
| K-S3 | Zero-compromise principles P1–P10 | `19` (canonical list), `01` | PENDING |
| K-S4 | Authoritative stack (ADR-001) + forbidden technologies + environment open questions | `09` | PENDING |
| K-S5 | Phase 0 documentation set & quality gate (the doc tree, gate checklist) | `00`, `14` | IN PROGRESS |
| K-S6 | Approved product scope v1 (9 in-scope areas) + explicit out-of-scope list | `01`, `16` | PENDING |
| K-S7 | Canonical data model: fact/dim tables, grains, integrity rules | `03` | INTEGRATED |
| K-S8 | Calculation rules summary (variance, favour*ability*, MTD/YTD/PY, grain, rounding, currency, forecasts) | `05`, `07` | IN PROGRESS |
| K-S9 | Exception engine summary + seed rule list + workflow statuses + UI wording | `06` | INTEGRATED |
| K-S10 | AI policy: optional/off by default, allowed/forbidden uses, redaction, JSON schema, caps, offline fallback, labelling | `10` | PENDING |
| K-S11 | Reporting outputs: Excel pack + PPT pack (6 slides), native/editable, stamping | `11`, `12` | PENDING |
| K-S12 | UX for non-technical users: guided nav, sample project, error copy, confirmations, help, diagnostics | `08` | PENDING |
| K-S13 | Quality, testing & acceptance: unit/golden tests, planted-exception acceptance, UAT script, error handling, packaging validation | `14` | PENDING |
| K-S14 | Session protocol (vibe coding rules) | `19` | PENDING |
| K-S15 | Immediate next actions + Phase 0 stop gate | `16`, `19`, `00` | IN PROGRESS |

### 4.2 Addon 1 (Sections A–P) — 16 rows

| Ref | Requirement | Owning doc(s) | Status |
|---|---|---|---|
| A1-A | How this addon works: spec of record, integrate into existing docs, no parallel tree | `00`, `19` | IN PROGRESS |
| A1-B | Principles P11–P20 (monthly rhythm, atomic imports, nothing silently discarded, versioned edits, upgrades, end-user docs, supply chain, hostile input, no colour-only signals, tabletop walkthrough) | `19`, `01` | PENDING |
| A1-C.1 | New docs 21–25 | `21`–`25` | PENDING |
| A1-C.2 | Required additions inside original docs (26-row table) | `01`–`20` (owning docs) | IN PROGRESS |
| A1-D | Domain completeness checklist (20 items → decisions + defaults) | `21`, `18` | IN PROGRESS |
| A1-E | Additional FRs (import history/void, new-period wizard, cross-batch dupes, in-app templates, master data, KPI library, rollups, export-what-you-see, job UX, search, owner distribution, backup/restore, close snapshot, diagnostics) | `02` | INTEGRATED |
| A1-F | Excel/CSV ingestion hardening (every quirk handled-or-rejected with named error; reject-vs-quarantine; validation report) | `04` | INTEGRATED |
| A1-G | Windows 11 & environment hardening (OneDrive trap, no admin, SmartScreen ladder, DPI, single instance, real-Windows protocol, offline proof) | `08`, `09`, `14`, `15` | PENDING |
| A1-H | Financial-correctness addenda (fiscal calendar, posting vs document date, rounding, ratio maths, sign conventions, comparability guard, forecast integrity) | `05`, `07` | INTEGRATED |
| A1-I | Security, privacy & supply chain (prompt injection, diagnostics redaction, log policy, secrets, dependency policy, data at rest) | `10`, `13`, `17` | PENDING |
| A1-J | Delivery, release & upgrade addenda (semver, release checklist, migration test, distribution, no schema drift, signing ADR) | `15`, `16`, `24` | PENDING |
| A1-K | Client enablement (task-structured guide, first-run tour, 60-min training, error dialog, support flow) | `22`, `23` | PENDING |
| A1-L | NFR numbers (cold start, import, dashboard, PPT, offline, installer size, memory, logs, diagnostics, screen, crash behaviour) | `14` (numbers), `16`, `09` | PENDING |
| A1-M | Session protocol addenda (SESSION_LOG, regression gate, Windows evidence, schema change process, sample data sacred, roadmap discipline) | `19`, `14` | PENDING |
| A1-N | Explicitly parked backlog list | `27`, `01` | IN PROGRESS |
| A1-O | Combined Phase 0 quality gate deltas (12 checks) | `00`, `14` | IN PROGRESS |
| A1-P | Updated immediate next actions | `16`, `19`, `00` | IN PROGRESS |

### 4.3 Addon 2 (Sections A–J) — 10 rows

| Ref | Requirement | Owning doc(s) | Status |
|---|---|---|---|
| A2-A | How this addon works + Coverage Matrix mandate | `00`, `19` | IN PROGRESS |
| A2-B | Architecture & stack addenda: headless engine, CLI, doc 26 contract, data-volume rule, config layering, ADR-002, scripts, recompute/invalidation | `09`, `26` | PENDING |
| A2-C | Document updates: new doc 26 + 19-row additions table | `26`, owning docs | IN PROGRESS |
| A2-C.2-03 | `03` additions: exception stable identity fields, optional `journal_category`, rule-effectiveness fields | `03` | INTEGRATED |
| A2-C.2-05 | `05` additions: TTM/rolling-12, forecast-accuracy metrics, control-total variance, materiality-driven default | `05` | INTEGRATED |
| A2-C.2-06 | `06` additions: re-run/identity semantics, aging buckets, owner auto-assign, effectiveness stats, per-rule strictness tiers | `06` | INTEGRATED |
| A2-C.2-07 | `07` additions: closed-period accuracy report feeding method-choice guidance | `07` | INTEGRATED |
| A2-D | Functional precision FRs (exception identity/re-run, aging/bulk, period status, re-import guard, control totals, budget validation, three-way view, rolling windows, one-off tagging, rule effectiveness, materiality, export collision, evidence bundle, scope decisions) | `02`, `06` | IN PROGRESS |
| A2-E | UI/UX & brand addenda (SCR-IDs, accessibility baseline, stale indicator, theme tokens as data, PPT text fit, wizard UX) | `08`, `12`, `ui/theme` | PENDING |
| A2-F | Testing, CI & quality bars (coverage ≥90% engine / ≥75% backend, `scripts/check`, CI, Playwright golden path, demo recipe DoD, link-check) | `14`, `16`, `17` | PENDING |
| A2-G | AI addenda (usage log, draft provenance, regeneration policy, determinism/number-mismatch stance) | `10` | PENDING |
| A2-H | Process & governance addenda (trunk-based branching, Keep a Changelog, blocking-question protocol, disclaimer enforcement) | `17`, `19` | PENDING |
| A2-I | Phase 0 quality gate deltas (12 checks) | `00`, `14` | IN PROGRESS |
| A2-J | Updated immediate next actions | `16`, `19`, `00` | IN PROGRESS |

### 4.4 Addon 3 (Sections A–K) — 11 rows

| Ref | Requirement | Owning doc(s) | Status |
|---|---|---|---|
| A3-A | How this addon works + Coverage Matrix extension | `00`, `19` | IN PROGRESS |
| A3-B | Document updates: new docs 27–28 + 14-row additions table | `27`, `28`, owning docs | PENDING |
| A3-B.2-03 | `03` additions: `FactPackIssue`, `MappingSuggestion`, template-version stamps on batches | `03` | INTEGRATED |
| A3-B.2-05 | `05` additions: data-quality score formula with worked example | `05` | INTEGRATED |
| A3-B.2-06 | `06` additions: cross-system tie-out rule family with v1 scope decision (file-level control totals only) | `06` | INTEGRATED |
| A3-C | Feature precision part 2 (AI mapping review queue, mapping preview/profile auto-match, commentary workflow, pack issuance register, data-quality score, storage/health, budget re-import, persistence/destructive actions, home screen, no login, import UX, display locale) | `02`, `08`, `10` | IN PROGRESS |
| A3-D | AI feature depth (four full prompt texts, model pinning/deprecation, golden fixtures, prompt-edit discipline) | `10`, `02` | PENDING |
| A3-E | Decisions that must be settled (success metrics, IP/licensing, forced in/out list, support/warranty) | `01`, `18`, `28` | IN PROGRESS |
| A3-F | Charts, formatting & test corpus (chart inventory, centralised conditional formatting, output conventions, cross-artifact consistency test, negative file corpus) | `08`, `11`, `12`, `14`, `sample-data/` | PENDING |
| A3-G | Acceptance, UAT & go-live (project DoD, UAT mechanics, defect severities, per-phase demo scripts, go-live checklist) | `28` | PENDING |
| A3-H | Backlog governance (entry schema, seed, reviewed at gates) | `27` | PENDING |
| A3-I | Process & quality deltas (exception perf NFR, ADR-000 index, local-only crash dumps, prompt-edit + feedback intake, DoD additions) | `14`, `09`, `19` | PENDING |
| A3-J | Phase 0 quality gate deltas (12 checks) | `00`, `14` | IN PROGRESS |
| A3-K | Updated immediate next actions | `16`, `19`, `00` | IN PROGRESS |

### 4.5 Addon 4 (Sections A–L) — 12 rows

| Ref | Requirement | Owning doc(s) | Status |
|---|---|---|---|
| A4-A | How this addon works + Coverage Matrix extension | `00`, `19` | IN PROGRESS |
| A4-B | Spec consumption protocol (standard doc header, session reading plan, quote-before-code, decisions accumulate forward, paraphrase ban) | `19`, `00` | IN PROGRESS |
| A4-C | Source-of-Truth Matrix & doc hygiene (one owner per fact, conflict resolution, no duplication, length discipline, link-check) | `00` | IN PROGRESS |
| A4-D | FR prioritisation & cut-line policy (P0/P1/P2, phase gate rule, never-cut list, cut process, estimates) | `02`, `16`, `20` | IN PROGRESS |
| A4-E | Doc 29 + approval mechanics (plain-language pack, approval recording, post-approval change impact rule) | `29`, `19`, `24`, `18` | IN PROGRESS |
| A4-F | Real-data pilot gate (one sanitized real month, tie-out acceptance, classification, exit criteria) | `28`, `14` | PENDING |
| A4-G | Tolerance & edge-case data matrix (no epsilon in money maths, display rounding, cross-artifact equality, 13 edge cases) | `05`, `02`, `14` | IN PROGRESS |
| A4-H | Sample-data integrity (watermark, project_type flag, no interleave, not delivered to client) | `14`, `16`, `02` | PENDING |
| A4-I | Engineering discipline deltas (spike policy, fresh-clone bootstrap test, code-health guardrails, storage growth maths) | `09`, `14`, `17`, `19` | PENDING |
| A4-J | Security & config deltas (AI key rotation, keyless mode default) | `13` | PENDING |
| A4-K | Phase 0 quality gate deltas (13 checks) | `00`, `14` | IN PROGRESS |
| A4-L | Updated immediate next actions (the current authoritative list) | `16`, `19`, `00` | IN PROGRESS |

**Gate rule:** any row not `INTEGRATED` fails the Phase 0 gate (Addon 2 §A.3, Addon 3 §A.3, Addon 4 §A.3).

## 5. Source-of-Truth Matrix (Addon 4 §C)

**Each fact lives in full in exactly one owning document; everywhere else it is a one-line
cross-reference.** Never paste a formula, threshold, layout, or rule into a second document.

| Fact type | Owning doc |
|---|---|
| Scope, personas, metrics, decisions in/out, branding, disclaimer, IP stance | `01_PRD` |
| Feature behaviour (FRs), priorities, acceptance criteria | `02_FUNCTIONAL_SPEC` |
| Tables, columns, grains, identities | `03_DATA_DICTIONARY` |
| Import behaviour, file quirks, profiles, quarantine rules | `04_SOURCE_MAPPING_AND_IMPORT_SPEC` |
| Formulas, tolerances, fiscal calendar, rounding | `05_CALCULATION_SPEC` |
| Exception rule logic + thresholds | `06_EXCEPTION_RULES_CATALOG` |
| Forecast methods + accuracy | `07_FORECAST_METHODS_SPEC` |
| Screens, charts, formatting rules, wording | `08_UI_UX_SPEC` |
| Stack, ADRs, storage, scripts, commands, jobs, migrations | `09_TECHNICAL_ARCHITECTURE` |
| AI policy, prompts, models | `10_AI_INTEGRATION_SPEC` |
| Excel layouts | `11_EXCEL_OUTPUT_SPEC` |
| PPT layouts | `12_POWERPOINT_OUTPUT_SPEC` |
| Security/privacy | `13_SECURITY_PRIVACY` |
| Test cases, quality bars, perf baselines | `14_TESTING_QA_PLAN` |
| Packaging/installer | `15_PACKAGING_DEPLOYMENT_RUNBOOK` |
| Phases, estimates, gates | `16_ROADMAP_PHASES` |
| Code standards | `17_CODING_STANDARDS` |
| Decisions + open questions (with dates) | `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS` |
| Process/session rules | `19_VIBE_CODING_PLAYBOOK` |
| Traceability | `20_REQUIREMENTS_TRACEABILITY` |
| Client questionnaire | `21_CLIENT_ONBOARDING_QUESTIONNAIRE` |
| User-facing help text | `22_END_USER_GUIDE` |
| Support/handover | `23_CONSULTANT_HANDOVER_AND_SUPPORT` |
| Release process | `24_RELEASE_AND_VERSIONING_RUNBOOK` |
| Risks | `25_RISK_REGISTER` |
| API | `26_API_CONTRACT` |
| Backlog | `27_BACKLOG` |
| UAT, DoD, go-live | `28_ACCEPTANCE_UAT_AND_GO_LIVE` |
| Client-facing requirements pack | `29_CLIENT_REQUIREMENTS_PACK` |

## 6. Document standard

### 6.1 Mandatory header (Addon 4 §B.1 — every file in `docs/`)

```
> **Status:** <Draft vX.Y | Approved vX.Y | Living>
> **Last updated:** YYYY-MM-DD
> **Owning FRs/areas:** <FR IDs / areas this doc owns>
> **TL;DR (≤ 15 lines):** <the essentials, so daily work never requires re-reading the whole file>
```

### 6.2 Hygiene rules

| Rule | Detail |
|---|---|
| **One owner per fact** | §5. Duplication is a defect; cross-reference instead. |
| **Conflict resolution** | Owning doc wins. Later addon wins over earlier addon. The fix goes into the **owning doc** in one commit — never a patch to a copy. |
| **TL;DR ≤ 15 lines** | Enforced by self-audit and link-check. |
| **Length discipline** | If a doc becomes unwieldy, split it and update the map in §3 — never leave one unreadable file. |
| **No placeholders** | No `TBD`, `TODO`, `…`, `etc.` on anything that blocks implementation. Unconfirmed items become `OQ-nnn` in doc `18` with a labelled default. |
| **Link-check** | Every cross-reference resolves; run as part of the Phase 0 self-audit and at every gate (Addon 2 §F.6). |
| **Version stamp** | Each doc carries its own version; `CHANGELOG.md` records every change with date and reason. |
| **Stable IDs** | All IDs are permanent and append-only; never renumber or reuse (see §8). |

## 7. Cross-artifact consistency (why the matrices matter)

The same number, label, or rule appears in the app, the Excel pack, the PPT deck, and the CLI. The
**cross-artifact consistency test** (Addon 3 §F.4, doc `14`) parses the generated Excel and PPT back
and asserts equality with engine values. Display conventions (currency symbol, `dd-mm-yyyy`,
negatives in parentheses, grouping, scale labels) are owned by doc `08` §formatting and repeated only
as cross-references in `11`/`12`.

## 8. ID namespace registry

| Prefix | Meaning | Owning doc | Format example |
|---|---|---|---|
| `FR-nnn` | Functional requirement | `02` | `FR-042` |
| `SCR-nnn` | Screen | `08` | `SCR-007` |
| `CHT-nnn` | Chart | `08` | `CHT-004` |
| `CALC-nnn` | Calculation formula | `05` | `CALC-011` |
| `KPI-nnn` | KPI / ratio definition | `05` | `KPI-003` |
| `EXC-nnn` | Exception rule | `06` | `EXC-009` |
| `FC-nnn` | Forecast method / rule | `07` | `FC-002` |
| `IMP-nnn` | Import validation check | `04` | `IMP-014` |
| `XL-nnn` | Excel sheet / layout block | `11` | `XL-005` |
| `PPT-nnn` | PowerPoint slide | `12` | `PPT-003` |
| `API-nnn` | API endpoint | `26` | `API-018` |
| `ERR-<FAM>-nnn` | Error code (families: IMP, VAL, STO, AI, EXP, ENG) | `26`, `08` | `ERR-IMP-004` |
| `TST-nnn` | Test case | `14` | `TST-063` |
| `NFR-nnn` | Non-functional target | `14` | `NFR-004` |
| `ADR-nnn` | Architecture decision record | `09` | `ADR-002` |
| `Q-nnn` | Client questionnaire item | `21` | `Q-014` |
| `OQ-nnn` | Open question | `18` | `OQ-006` |
| `DEC-nnn` | Recorded decision | `18` | `DEC-002` |
| `RISK-nnn` | Risk | `25` | `RISK-003` |
| `BL-nnn` | Backlog item | `27` | `BL-011` |
| `DEF-nnn` | Defect (UAT period) | `28` | `DEF-002` |
| `PROMPT-nn` | Versioned prompt template | `10` | `PROMPT-01` |
| `MAP-nnn` | Mapping profile | `04` | `MAP-003` |
| `SCN-nnn` | Forecast/analysis scenario | `07` | `SCN-002` |
| `GATE-nn` | Phase quality gate | `16`, `14` | `GATE-01` |

Rules: IDs are allocated once and never reused; a retired ID is tombstoned in the owning doc; every
`FR-nnn` appears in `20_REQUIREMENTS_TRACEABILITY.md` with a priority (P0/P1/P2) and at least one test.

## 9. Quality-gate tracker

Five gates, **58 checks total**, applied in addition to each other (later gates add, never remove).
The authoritative checkbox lists live in doc `14` §Gates; this table tracks status only.

| Gate | Source | Checks | Status |
|---|---|---|---|
| `GATE-01` Phase 0 core | Kickoff §5 checklist | 9 | ⏳ In progress |
| `GATE-02` Addon 1 deltas | Addon 1 §O | 12 | ⏳ In progress |
| `GATE-03` Addon 2 deltas | Addon 2 §I | 12 | ⏳ In progress |
| `GATE-04` Addon 3 deltas | Addon 3 §J | 12 | ⏳ In progress |
| `GATE-05` Addon 4 deltas | Addon 4 §K | 13 | ⏳ In progress |

Downstream hard gates (defined in doc `28`): packaging spike → each phase gate → real-data pilot →
UAT → go-live. Approvals are recorded in `CHANGELOG.md` **and** `SESSION_LOG.md` (Addon 4 §E.2).

## 10. Current phase status

| Item | Value |
|---|---|
| Phase | **Phase 0 — Documentation** |
| Authoritative next-action list | Addon 4 §L (supersedes Addon 3 §K → Addon 1 §P → Kickoff §15) |
| Docs complete | `00`–`07` (drafts) + `CHANGELOG`, `SESSION_LOG` |
| Docs remaining | `08`–`29`, `PHASE0_SUMMARY` |
| Product code | **None. Forbidden until recorded approval.** |
| App version / docs version | 0.1.0 (planned) / 0.1.0 (working draft) |
| Open questions count | Tracked in `18_...OPEN_QUESTIONS.md` §Open |
| Blocking questions | None currently (all have labelled defaults in doc `21`) |

## 11. How this document is updated

1. Every session that changes a doc updates the **Status** column in §3 and the relevant rows in §4.
2. Every phase gate re-runs the Coverage Matrix and the gate tracker; the gate fails on any row that
   is not `INTEGRATED` or any check that is not `PASS`.
3. Any new document, ID prefix, or fact type requires a change to §3, §5 and §8 **first** (spec-first),
   recorded in `CHANGELOG.md`.

## 12. Approval log

| Gate | State | Date | Approver | Evidence |
|---|---|---|---|---|
| Phase 0 (core + Addons 1–4) | **Not yet requested** | — | Project owner | `docs/PHASE0_SUMMARY.md` + doc `29` |
| Packaging spike | Not started (post-approval) | — | Project owner | `09`/`15` spike outcome |
| Phase gates 1–6 | Not started | — | Project owner | Per-phase demo script (`16`, `28`) |
| Real-data pilot | Not started | — | Client analyst | Tie-out worksheet (`28` §Pilot) |
| UAT | Not started | — | Client | Signed UAT script (`28`) |
| Go-live | Not started | — | Client + project owner | Go-live checklist (`28`) |
