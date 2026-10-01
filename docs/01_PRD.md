> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** scope, personas, jobs-to-be-done, success metrics, branding, disclaimer, IP stance; FR families referenced by `02_FUNCTIONAL_SPEC.md`
> **TL;DR (≤ 15 lines):** The product is a local, offline, single-user Windows 11 desktop app that runs the
> client's monthly FP&A rhythm: import ERP exports → validate → analyse budget vs actual → review
> potential exceptions → refresh the rolling forecast → issue an Excel pack and a PowerPoint deck.
> Primary user is a non-technical FP&A analyst; secondary users are accounting owners who fix entries and
> a CFO who reads the pack. v1 is deliberately narrow: P&L focus, import-only budgeting, single reporting
> currency per project, no eliminations, no login, no cloud. Core scope decisions, the forced in/out list,
> the IP stance and the canonical advisory disclaimer are settled here (§6, §7, §16, §15.1). Everything
> else is owned by a single downstream doc per the Source-of-Truth Matrix in `00_INDEX.md`.

---

# 01 — PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1. Purpose and status of this document

This PRD owns **what we are building, for whom, why, and what is explicitly excluded**. It is the
inherited-context document: a reader who has never seen the client should finish §2–§5 and understand
the product well enough to judge any downstream spec.

- Behaviour is **not** specified here — every feature lives in `02_FUNCTIONAL_SPEC.md` as an `FR-nnn`.
- Numbers that gate work (performance, coverage, sizes) live in `14_TESTING_QA_PLAN.md` as `NFR-nnn`.
- The full principles list lives in `19_VIBE_CODING_PLAYBOOK.md`; this PRD only records the scope
  consequences of them.
- Unconfirmed client facts live in `18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md` as `OQ-nnn`, each with a
  labelled default from `21_CLIENT_ONBOARDING_QUESTIONNAIRE.md`.

## 2. Product overview

### 2.1 One-paragraph definition

**FP&A Month-End Copilot** is a local desktop application for a mid-size company's finance team that
turns a monthly pile of ERP exports into a reviewed, explained, board-ready month-end pack. The analyst
drops in the month's Excel/CSV exports; the app validates them, loads them into a local analytic store,
compares actuals against budget and prior year at the lowest shared grain, flags **potential**
exceptions for human review, projects the rest of the year with deterministic forecast methods, and
generates the Excel working pack and the PowerPoint management deck — with every number drillable back
to a source transaction and the exact file it came from. It runs entirely on the user's laptop, works
with no internet connection, requires no technical setup beyond a double-click installer, and never
writes back to the ERP.

### 2.2 Working name and final naming

- **Working name:** FP&A Month-End Copilot (used in paths, installer IDs, and this doc set).
- **User-facing product name:** to be confirmed by the client (`Q-019`, branding). The default until
  assets arrive is "FP&A Month-End Copilot".
- **Naming constraints:** the final name must not change the install directory contract, the project
  file location contract, or any `SCR-` id. The name appears in exactly three places: window title,
  installer display name, and the About/Diagnostics screen (`SCR-014`). Renaming is a config/branding
  change (`08`, `23`), not a code change.

### 2.3 The problem today (manual workflow being replaced)

| # | Current manual activity | Pain it creates |
|---|---|---|
| 1 | Downloads large Excel exports monthly from Microsoft Dynamics 365 | Manual, error-prone, format drift month to month |
| 2 | Compares actuals vs budget, investigates variances to transaction level | Hours of filter-sorting per month; no repeatable rule set |
| 3 | Investigates questionable entries and guides several accounting teams to correct them | Ad-hoc lists, no tracking of who owns what, no audit trail |
| 4 | Builds budgets including rolling forecasts | Rebuilds the same spreadsheet logic every cycle |
| 5 | Produces management PowerPoint presentations | Copy-paste formatting, last-minute rework before management review |

The cycle repeats **every month** (Addon 1 P11). This is not a one-off analysis tool.

### 2.4 Why we are rebuilding from scratch

Two previous vibe-coded prototypes were abandoned. Their failure modes are recorded as design
constraints, not history lessons:

| Failure mode of prior prototypes | Constraint it creates here |
|---|---|
| Sprawled into an all-in-one FP&A platform | Scope is fixed per phase; new ideas go to `27_BACKLOG.md` (P6) |
| Heavy architecture (Tauri/Rust, hundreds of files) before any validated core | Approved stack only (`09`, ADR-001); headless testable engine first (`09`, §ADR-002) |
| No validated core calculation | Golden tests tied to `05`/`06` before features (`14`) |
| Improvised product decisions mid-build | Docs-first, quote-before-code (`19`) |

Prior repositories, if made available, are **reference for exception-rule and idea brainstorming only**.
Their architecture, code, and data model must never be reused or carried over.

### 2.5 What "done" looks like for the client

On a clean Windows 11 machine, with no Python/Node/Docker/terminal, and with the network cable pulled:

1. Double-click `Setup-FPandAMonthEndCopilot-<version>.exe`, click through a per-user install (no admin),
   and launch from the Start Menu.
2. The app opens on a ready sample project, so it is demoable in the first minute.
3. Drop in this month's exports → get a validation report → see the data-quality score.
4. Open Analyze → see budget vs actual, drill any figure to transactions and to the source file.
5. Open Exceptions → see a triaged list with owners and statuses, export it for the accounting teams.
6. Refresh the rolling forecast for the open periods.
7. Generate the Excel pack and the PowerPoint deck (≤ 15 s), review, and issue the pack with a version.
8. Repeat next month without a single technical step.

## 3. Personas

### 3.1 P1 — FP&A Analyst (primary user, "Aarti")

| Attribute | Detail |
|---|---|
| Role | Sole or lead FP&A analyst in a mid-size company |
| Technical skill | None beyond Excel, Outlook, and Windows; cannot install tooling, will not use a terminal |
| Environment | Windows 11 x64 laptop (4-core typical), 8–16 GB RAM, scaling 100–150%, Documents folder possibly OneDrive-synced |
| Goals | Close the month-end pack quickly and correctly; answer "why is this account off?" in minutes; not get blamed for a missed error |
| Frustrations | Rebuilding the same analysis monthly; hunting variance drivers; formatting PowerPoint by hand; being unable to trace a number back |
| Success looks like | Pack issued in under half a day; every number traceable; no rework from management |
| What would make them abandon the tool | A raw error message, a silent data change, a number they cannot explain, a slow grid, any need to touch config files |

### 3.2 P2 — Accounting Owner (secondary user, "Rahul")

| Attribute | Detail |
|---|---|
| Role | Accountant responsible for one or more cost centres / legal entities |
| Technical skill | Excel-level; uses the outputs, not the app |
| Goals | Get a clear, short list of entries to check, with evidence attached, and be able to reply "explained"/"corrected" |
| Touchpoints | Receives the exported exception list grouped by owner; may open the app read-only on the analyst's machine during review; receives the evidence bundle workbook |
| Success looks like | No ambiguity about which entry, which amount, and what is expected of them |

### 3.3 P3 — Finance Director / CFO (tertiary user, pack recipient)

| Attribute | Detail |
|---|---|
| Role | Reads and signs off the monthly management pack |
| Technical skill | None in the app; PowerPoint/Excel fluent |
| Goals | Understand the month in one page: actual vs budget, top drivers, control issues, outlook |
| Touchpoints | The generated `.pptx` and `.xlsx`; possibly a live walkthrough during review |
| Drives | Which KPIs appear on slide 2 (`12_POWERPOINT_OUTPUT_SPEC.md`, `Q-013`) |
| Success looks like | The deck answers their next three questions without a follow-up meeting |

### 3.4 P4 — Consultant / Support Engineer (support persona, "you")

| Attribute | Detail |
|---|---|
| Role | The person who built and maintains the tool |
| Needs | Rebuild steps, config/prompt/branding editing, dependency updates, diagnostics workflow (`23`) |
| Success looks like | A support call resolved from a redacted diagnostics zip without remote access |

### 3.5 Explicitly not personas in v1

No multi-user collaboration, no approver workflow inside the app, no IT administrator persona (no
admin install, no server, no policy management), no auditor persona (audit trail exists but has no
dedicated auditor UI).

## 4. Jobs-to-be-done

### 4.1 The core JTBD: the monthly rhythm (first-class, Addon 1 P11)

> **"When the month closes, help me turn the exports I already have into a reviewed, explained,
> traceable management pack — in hours, not days — without me having to be technical."**

The recurring cycle, in the order the user performs it:

| Step | Activity | Contract in this doc set |
|---|---|---|
| 1 | **New period opens** | `FR` new-period wizard (`02`), period status Open/Closed (`02`, A2 §D.3) |
| 2 | **Import** the month's files | Import wizard + profiles (`04`), atomic commit (P12) |
| 3 | **Validate** and reconcile | Validation report, data-quality score (`04`, `05`) |
| 4 | **Analyse** budget vs actual, MTD/YTD/PY/TTM | BvA engine + views (`02`, `05`, `08`) |
| 5 | **Investigate** potential exceptions | Rule catalog (`06`), workflow statuses (`02`) |
| 6 | **Refresh** the rolling forecast | Methods + scenarios (`07`) |
| 7 | **Produce** the pack | Excel (`11`) + PowerPoint (`12`) |
| 8 | **Issue** and archive the period | Issuance register + close snapshot (`02`, A3 §C.4/C.5), period lock |
| 9 | *(next month)* | Mapping profiles carry forward; **numbers never do** (`02`, A1 §E.2) |

### 4.2 Secondary JTBDs

| JTBD | Delivered by |
|---|---|
| "Tell me what changed and why, in words I can paste into the deck" | AI commentary draft + rule-based fallback (`10`) |
| "Give me the exact transactions behind this number" | Drill-down with source-file evidence (`02`, `08`) |
| "Make sure nothing silently went missing in the import" | Nothing-silently-discarded guarantee (P13), validation report (`04`) |
| "Help me not miss the same control issue twice" | Rule effectiveness analytics + tuning (`06`, A2 §D.10) |
| "Let me hand each accountant their own list" | Owner-wise exception distribution + evidence bundle (`02`, A2 §D.13) |
| "Prove the deck I sent last month still matches what I sent" | Period-close snapshot + issued-pack immutability (`02`, A3 §C.4) |

## 5. Product principles applied to scope

The canonical principles list (P1–P20) is owned by `19_VIBE_CODING_PLAYBOOK.md` §2. Their **scope
consequences** are:

| Principle | Scope consequence recorded here |
|---|---|
| P1 Docs before code | No FR is implemented unless it exists in `02` and is traced in `20` |
| P3 Deterministic money math | AI commentary is decorative text; every number comes from the engine |
| P4 Offline, local-only | No cloud service is a dependency of any in-scope feature; AI is optional and off by default |
| P6 Scope discipline | §6.2/§6.3 lists are exhaustive for v1; anything else is parked in `27_BACKLOG.md` |
| P7 Non-technical UX | Every screen must be judgment-free usable without training (`08`, `22`) |
| P8 "Potential exception," never "error confirmed" | Wording rules are owned by `08`; the advisory disclaimer is §15.1 |
| P10 Boring, testable code | Approved stack only (`09`), no speculative abstractions |
| P11 Monthly rhythm first-class | §4.1 is the spine of the product; one-shot loading is a design failure |
| P16 End-user documentation is a deliverable | `22` ships with the product; the phase gate fails without it |
| P19 Colour is never the only signal | Formatting rules (`08` §formatting) apply to app, Excel and PPT |

## 6. Scope

### 6.1 In scope for v1 (approved, phased per `16_ROADMAP_PHASES.md`)

| # | Area | FR family (owned by `02`) | Priority baseline |
|---|---|---|---|
| 1 | Import & validation (profiles, archive with checksum, validation dashboard, import history/void) | `FR-IMPORT-*` | P0 |
| 2 | Budget vs Actual analysis (MTD/YTD/PY/TTM, variance, favour*ability*, matrix, waterfall, trends, drill-down) | `FR-BVA-*` | P0 |
| 3 | Exception engine & register (≥15 rules, statuses, owners, aging, bulk actions, effectiveness) | `FR-EXC-*` | P0 |
| 4 | Rolling forecast (locked actuals, 4 methods, 3 scenarios, accuracy report) | `FR-FC-*` | P1 |
| 5 | Excel reporting pack (refreshable, specified layouts) | `FR-XL-*` | P0 |
| 6 | PowerPoint management pack (4–6 editable slides, ≤ 15 s) | `FR-PPT-*` | P0 |
| 7 | AI commentary (optional, off by default, keyless fallback) | `FR-AI-*` | P1 |
| 8 | Settings (mappings, master data, thresholds, branding, locale, storage, AI key) | `FR-SET-*` | P0 |
| 9 | First-run experience (sample project, guided tour) | `FR-ONB-*` | P0 |
| 10 | Cross-cutting: KPI/ratio library, hierarchy rollups, search, export-what-you-see, job UX, backup/restore, close snapshots, issuance register, About/Diagnostics | `FR-XC-*` | P0/P1 |

### 6.2 Explicitly out of scope for v1

These appeared in the source material as possible features and are **not built in v1** (each is
recorded in `27_BACKLOG.md` with a trigger condition):

| Excluded | Rationale | Backlog ref |
|---|---|---|
| Write-back/posting to D365 or any ERP | The tool advises; humans post (P3, P8) | `BL-001` |
| Replacing the ERP / ledger-of-record functions | Out of product category | `BL-002` |
| Journal approval workflows | Human process, not software | `BL-003` |
| Multi-user, cloud, collaboration, RBAC | Single-user local decision (§10) | `BL-004` |
| In-app login/authentication | Trust = OS user account; no server | `BL-005` |
| Mobile / web-hosted UI | Local desktop only | `BL-006` |
| Auto-update framework | Manual "check for updates" only in v1 (`08`) | `BL-007` |
| Direct D365/API connectors | Excel/CSV first; API is a later optional phase | `BL-008` |
| Auto-generated Power BI files / direct `.pbip` authoring | Backlog; **star-schema CSV export** is a documented Phase 6 candidate | `BL-009` |
| Balance sheet & cash-flow statements | v1 = P&L focus (§6.3) | `BL-010` |
| Price/volume/mix revenue decomposition | Analytical depth beyond v1; parked | `BL-011` |
| Purchase-commitment / PO data | Source data not part of the current monthly set | `BL-012` |
| Cost allocation / recharging | Requires allocation rules the client has not defined | `BL-013` |
| Automated cross-system tie-out | v1 = manual control totals only (§6.3) | `BL-014` |
| In-app budget authoring | v1 = import-only (§6.3) | `BL-015` |
| Headcount / FTE metrics (incl. cost per head) | A3 §E.3 parks headcount metrics; no headcount field in the v1 schema | `BL-016` |
| Intercompany eliminations & consolidation netting | v1 = per-entity + simple grouped totals (§8) | `BL-017` |
| Advanced forecast methods (seasonality index, driver-based regression) | Deterministic simple methods only in v1 (`07`) | `BL-018` |
| Email/Teams distribution of packs | Packs are issued locally; delivery is the user's channel | `BL-019` |
| Budget version-compare view | v1 stores a version field; comparison UI parked | `BL-020` |
| Commentary carry-forward between periods | Nice-to-have; parked | `BL-021` |
| Localisation beyond English | v1 English only; number/date display is configurable | `BL-022` |
| Multi-client licence management | Single client, single product build | `BL-023` |
| One-off / exceptional item tagging | PRD decision (A2 §D.9): **parked**, not minimal-v1 — not in the approved §6.1 scope, and it adds tagging UX + adjusted-toggle views + AI integration; revisit after the first real month | `BL-024` |
| Partial-amount duplicate detection (staged/split payments) | v1 duplicate detection requires an exact amount match to keep precision high; partial matching is a refinement for a later phase | `BL-025` |

### 6.3 Forced in/out decisions (A2 §D.14, A3 §E.3) — each settled

| Decision | Ruling for v1 | Consequence |
|---|---|---|
| Financial statements covered | **P&L focus.** Balance sheet and cash flow are out (§6.2) | Statement-line mapping in `DimAccount` is P&L-first; BS/CF accounts can still be imported and drilled but have no dedicated views |
| Budget creation | **Import-only.** Budgets arrive as files via the budget template | No budget-authoring UI; re-import replaces a version atomically (A3 §C.7) |
| Journal-category column (manual/auto/reclass/accrual) | **Optional via mapping profile** | Absent = the dependent rules degrade gracefully (`06`); present = richer exception precision |
| Cross-system tie-out | **Manual control totals only.** The actuals template accepts a control-totals block and compares it file-vs-loaded | A fully automated cross-system tie-out is parked (`BL-014`) |
| One-off/exceptional tagging | **Parked** (`BL-024`) | Not built in v1; AI commentary will not reference one-offs |
| Multi-currency | **Single reporting currency per project.** No FX table in v1 | Mixed-currency rows are quarantined at import (`04`, A4 §G.2) unless the client confirms otherwise (`Q-006`) |

### 6.4 Cut-line policy application

FR priorities (P0/P1/P2), the never-cut list, and the cut approval process are owned by
`02_FUNCTIONAL_SPEC.md` §priorities and `16_ROADMAP_PHASES.md` §gates (Addon 4 §D). This PRD states the
scope; it does not award priorities.

## 7. Success metrics (baselines from questionnaire, targets as numbers)

Baselines are collected in `21_CLIENT_ONBOARDING_QUESTIONNAIRE.md` (`Q-001`, `Q-014`). Where the client
has not answered, the baseline is recorded as **"unmeasured — default assumption"** and must be
measured during the real-data pilot (`28` §Pilot) before the metric is reported as achieved.

| # | Metric | Baseline (source) | Target after go-live | Measured by |
|---|---|---|---|---|
| M1 | Time to produce the monthly management pack | Unmeasured — assumption: 3 days (Q-001) | **≤ 0.5 day** for a trained analyst | UAT observation + pilot timing |
| M2 | Time to investigate a variance to transaction level | Assumption: 30–60 min per significant variance | **≤ 5 min** per variance | Demo/UAT timing |
| M3 | Number of control issues (exceptions) found per month | Unmeasured — assumption: "found late or missed" (Q-002) | **≥ 15 rules active; ≥ 90% of planted exceptions detected** on the acceptance dataset | Acceptance test (`14`) |
| M4 | Manual consolidation/formatting steps in the monthly cycle | Assumption: 20+ steps (Q-001) | **≤ 5 manual steps** (drop files, review, decide, issue) | UAT walkthrough count |
| M5 | Pack rework after management review | Unmeasured | **≤ 1 revision cycle** per month in the first quarter | Pilot log |
| M6 | Traceability | Manual, partly impossible | **100%** of displayed figures drill to source rows + source file + import batch | Cross-artifact + drill tests |
| M7 | Offline capability | n/a | Full sample-project walkthrough **passes with the network disabled** (except the marked AI step) | `NFR-008` test |
| M8 | Adoption | 0 | **3 consecutive months** of packs issued from the app within 6 months of go-live | Issuance register |
| M9 | Exception closure hygiene | Untracked | **≥ 80%** of month-end exceptions carry a status + owner within 5 working days | Exception analytics (`06`) |
| M10 | Performance on the client's real file sizes | Manual, no target | Import 250k rows ≤ 60 s; dashboard ≤ 2 s; deck ≤ 15 s; cold start ≤ 10 s; installer ≤ 500 MB | `NFR-001`…`NFR-006` and `NFR-009` (`14` §3) |

## 8. Multi-entity stance and consolidation

| Question | Ruling |
|---|---|
| Entities in v1 | 2–3 legal entities in the sample data; the model supports N entities |
| Reporting | **Per-entity reporting plus simple grouped totals** (sum of entities at a shared grain) |
| Eliminations / intercompany netting | **None in v1** (`BL-017`); the UI must label grouped totals as "simple sum — no eliminations" wherever they appear (`08`) |
| Entity-level budget | Budget files carry an entity dimension; entities without budget are flagged by the "orphan dimension" rule (`06`) |
| Cross-entity drill | Drill-down always shows the entity on each transaction row (`02`) |

## 9. Who receives the pack (drives slide-2 KPI selection)

- The pack recipient set is confirmed by `Q-013` (CFO alone vs management team vs both).
- **Default until confirmed:** the deck targets a **CFO/finance director**, so slide 2 carries a
  compact KPI strip (revenue, gross margin %, Opex, EBITDA-level result, variance to budget, forecast
  landing) rather than a departmental breakdown.
- The KPI strip is **configurable** (which KPIs, how many) in Settings; changing it is a settings
  change, not a code change (`08`, `12`).
- Distribution itself (email/Teams) is out of scope; the app produces files and an issuance record.

## 10. Single-user stance: no login, no RBAC (explicit decision)

| Aspect | Ruling | Rationale |
|---|---|---|
| Accounts | **No in-app authentication in v1** | Single-user local desktop app; a login screen would be security theatre over a local file store |
| Privacy boundary | **The Windows OS user account** | Data lives in the user's own profile directory; another OS user cannot read it by default |
| Concurrent users | **One user, one machine, one project at a time** | Single-instance mutex per project (`09`, A1 §G.5) with a friendly "already open" message |
| Roles / permissions | **None in v1** (`BL-004`) | Adding RBAC requires a server or encrypted role store; unjustified complexity |
| Shared machine | Supported but not encouraged: the second OS user sees no projects unless they import them; projects are portable via backup zip | Backup/restore is the sanctioned transfer path (`02`, `08`) |
| Audit | **Local audit log** of user actions (who did what *within the session*) | Auditability without identity: entries state the action, timestamp, and object |
| Consequence for reviewers (P2 persona) | Accounting owners do **not** log in; they receive exported exception lists and evidence bundles | Keeps v1 to one real user role |

This decision is recorded as `DEC-010`, is restated in `13_SECURITY_PRIVACY.md` (privacy boundary) and
`09_TECHNICAL_ARCHITECTURE.md` (no auth layer), and is reviewed if a multi-user requirement ever
arrives (it would be a new phase with a new ADR, not a v1 tweak).

## 11. Constraints

### 11.1 Client environment constraints (hard)

| Constraint | Consequence |
|---|---|
| Windows 11 x64 only | No macOS/Linux packaging in v1; dev may happen anywhere, packaging evidence must come from real Windows 11 (A1 §G.6) |
| Non-technical user (no Python/Node/.NET/Docker/terminal) | Self-contained installer, no prerequisites, per-user install without admin (A1 §G.2) |
| Documents folder may be OneDrive-synced | Project/database storage must default to `%LOCALAPPDATA%`, never a syncing folder (A1 §G.1, `09`); exports may go to Documents but detect sync and warn |
| Offline operation required | No runtime network dependency; the only network use is the optional AI call (`10`) |
| Client internet available only for optional AI | Keyless mode must be fully functional and demoable (`10` §keyless) |
| Data arrives as Excel/CSV exports | Import robustness is a product feature, not a technical detail (`04`) |
| Scale: up to ~250k GL rows / ~100 MB per file | Analytics in DuckDB server-side; browser never receives bulk rows (`09` §B.3 equivalent) |
| Defender + SmartScreen present | Unsigned installer friction is launch-blocking, with a written mitigation ladder (A1 §G.3, `15`, `24`) |

### 11.2 Product constraints (self-imposed, from P1–P20)

Deterministic money maths · atomic imports · versioned user-editable artefacts · upgradeable releases ·
supply-chain hygiene · hostile-input treatment · no colour-only signals · tabletop-verified docs.

### 11.3 What the product must never do

1. Never write to, post to, or modify an ERP or any external system.
2. Never upload client data anywhere (no telemetry, no crash upload, no silent AI call).
3. Never silently discard a row, sheet, column, or file.
4. Never present an AI-produced number as a computed value.
5. Never show a figure the user cannot drill to source.
6. Never compute money with binary floats.
7. Never overwrite history behind an issued pack.

## 12. Assumptions (labelled, all traceable)

Every assumption below is a **"default, unconfirmed"** until the client answers the matching
questionnaire item. The canonical list with owners lives in `18_...OPEN_QUESTIONS.md`; the questionnaire
with defaults lives in `21_...QUESTIONNAIRE.md`.

| # | Assumption | Default used | Question |
|---|---|---|---|
| A1 | D365 edition | Generic "D365-style GL export" template + documented dimension parsing | `Q-002` |
| A2 | The two other systems | Two distinct sample export shapes (payroll summary, procurement/bank ledger) | `Q-003` |
| A3 | Fiscal calendar | January year-start, 12 monthly periods, calendar months; configurable | `Q-004` |
| A4 | Reporting currency | INR, whole units, optional ₹ thousands/lakhs display | `Q-006` |
| A5 | Prior-year data availability | Build PY views; auto-hide when no PY batch exists | `Q-005` |
| A6 | Budget versions | One approved annual budget + `version` field for later reforecasts | `Q-007` |
| A7 | Forecast cadence | Monthly rolling forecast, Base/Best/Worst scenarios | `Q-008` |
| A8 | Approval thresholds | Editable master-data table seeded with sensible defaults | `Q-009` |
| A9 | Recurring-cost list | Editable master-data table maintained by the client | `Q-010` |
| A10 | Vendor master/categories | Optional importable table; dependent rules degrade gracefully | `Q-011` |
| A11 | Current outputs to replicate | None provided yet; app uses its own house style until samples arrive | `Q-012` |
| A12 | Pack audience | CFO/finance director (§9) | `Q-013` |
| A13 | File sizes seen in practice | 250k rows / 100 MB upper bound | `Q-014` |
| A14 | Signing certificate | None; SmartScreen mitigation ladder applies | `Q-015` |
| A15 | Delivery channel | Secure link + published SHA-256 | `Q-016` |
| A16 | Training | 60-minute guided session + recorded demo outline | `Q-017` |
| A17 | Support model | Analyst calls the consultant first; diagnostics zip workflow | `Q-018` |
| A18 | Branding assets | Working name, neutral placeholder palette, no logo | `Q-019` |
| A19 | Data retention | Projects kept locally until the user deletes them | `Q-020` |
| A20 | Headcount data | Not provided; headcount metrics parked (`BL-016`) | `Q-021` |

**Rule:** an assumption may be used to proceed only when it is labelled "default, unconfirmed" in the
documents that depend on it. It may never be presented to the client as a fact.

## 13. Top product risks (register owned by `25_RISK_REGISTER.md`)

| # | Risk | Impact | Early mitigation |
|---|---|---|---|
| R1 | Unsigned installer flagged by SmartScreen → client cannot install | Launch-blocking | Mitigation ladder + non-technical walkthrough + SHA-256 (A1 §G.3, `15`) |
| R2 | Real client files break the importer (messy headers, encodings, accounting formats) | Blocks the primary workflow | Hardening spec `04` + negative corpus `sample-data/malformed/` + graceful failure copy |
| R3 | Scope sprawl repeats the previous prototypes' failure | Project failure | Fixed scope + cut-line policy + backlog governance (`27`) |
| R4 | Client expects the tool to *find every error* | Trust damage | Advisory disclaimer (§15.1) + "potential exception" wording (P8) |
| R5 | Numbers differ from the existing manual pack | Loss of confidence at UAT | Real-data pilot tie-out gate with difference classification (`28`) |
| R6 | OneDrive/Documents sync corrupts or locks project databases | Data corruption | `%LOCALAPPDATA%` default + sync-folder tests (`09`, `14`) |
| R7 | Windows-only evidence gap (dev environment is not Windows) | Untested delivery | Real-Windows validation protocol at every gate (A1 §G.6) |
| R8 | AI output drifts from engine numbers or leaks data | Credibility / confidentiality | Number-mismatch stance, redaction, caps, keyless default (`10`) |
| R9 | Client's actual data volumes exceed NFRs | Unusable performance | Measurement at pilot; scale mode `--scale 250000` in the perf suite |
| R10 | Single-user design conflicts with how the team actually shares work | Rework | Explicit decision §10 + backup/restore transfer path; revisit post-pilot |

## 14. Open questions (registry owned by `18_...OPEN_QUESTIONS.md`)

The complete open-question list is `18` §Open. The **blocking set for design decisions** is:

`OQ-001` D365 edition · `OQ-002` the two other systems' column lists · `OQ-003` fiscal calendar ·
`OQ-004` prior-year availability · `OQ-005` currency/multi-currency · `OQ-006` budget versions ·
`OQ-007` approval thresholds · `OQ-008` recurring-cost list · `OQ-009` vendor master ·
`OQ-010` current Excel/PPT outputs for house-style matching · `OQ-011` pack audience ·
`OQ-012` signing certificate budget · `OQ-013` real file sizes · `OQ-014` sample real data for the
pilot · `OQ-015` branding assets · `OQ-016` support/warranty terms · `OQ-017` delivery channel.
Added by the `11` pass (non-blocking, defaults in place): `OQ-021` client's current report format
(`.xlsx` / `.xlsm` / protected / paper) for house-style matching · `OQ-022` preferred pack default units
(whole units vs lakhs).

**Registry hygiene flag — resolved (`18` §4.4).** `OQ-020` was referenced in §16 but defined nowhere; it is
now a **retired tombstone** and the §16 reference above has been corrected to `OQ-016`. `OQ-018` and
`OQ-019` were never allocated and remain reserved, never reused (`18` §4.4, `00_INDEX` §8).

None of these blocks Phase 0: each has a labelled default (§12) that is safe to build against and cheap
to change (mapping profiles, settings, brand config). Any question that later proves **unsafe** to
default — anything touching money semantics, data loss, or client facts — becomes a blocking question
under A2 §H.3 and stops work until answered.

## 15. Disclaimer and legal posture

### 15.1 Canonical advisory disclaimer (the single source of wording)

This is the **one canonical wording** (A2 §H.4). Every other artefact quotes it verbatim from here —
the About/Diagnostics screen (`SCR-014`), the EULA text shipped with the installer, the footer of every
generated Excel pack, the cover/back slide of every generated deck, and the client requirements pack
(`29`).

> **Advisory tool — not professional advice.**
> FP&A Month-End Copilot is an analysis aid. It highlights **potential** exceptions, variances, and
> trends for review. It does **not** provide audit, accounting, tax, or legal advice, and it does
> **not** guarantee that every error, misstatement, or irregularity will be detected. All figures,
> flags, and AI-generated drafts must be reviewed by a qualified accountant before any business
> decision, filing, or external reporting. The tool never posts, approves, or alters accounting
> records, and it never replaces professional judgement.

### 15.2 Where the disclaimer must appear (enforced by tests)

| Location | Form |
|---|---|
| About/Diagnostics screen (`SCR-014`) | Full text, scrollable, with a "Copy" button |
| EULA shown during install (`15`) | Full text, requires explicit acceptance |
| Excel pack (`11`) | Footer of every sheet: short form + reference to the About screen for full text |
| PowerPoint pack (`12`) | Cover slide footer or back slide |
| Client requirements pack (`29`) | A dedicated plain-language section |
| User guide (`22`) | A dedicated "What this tool does not do" section |
| AI-generated text (`10`) | Prefixed "AI draft — review before use." |

**Short form** (for footers where space is constrained): *"Potential exceptions only — advisory tool,
not professional advice. Review by a qualified accountant required. Figures may be revised."*

### 15.3 Data-handling posture (restated in `13_SECURITY_PRIVACY.md`)

Client data stays on the client's machine. Raw files are archived immutably per import. Nothing is
uploaded. The only outbound call is the optional AI request, explicitly enabled by the user, to a
configured endpoint, with redaction applied. Crash dumps and logs are local-only and never uploaded
(A3 §I.3).

## 16. IP and licensing stance

| Item | Ruling (`DEC-016`) |
|---|---|
| Client data | Owned by the client, always; stays on the client's machine |
| Client branding (name, logo, colours) | Owned by the client; used only inside their installed build |
| Application IP (source, architecture, docs, prompts) | Retained by the consultant |
| Delivered build | Client receives a **perpetual usage licence** for the delivered build, for internal business use, on their machines |
| Redistribution | Client may not resell or redistribute the app |
| Source code handover | Not part of v1 delivery; support/handover is via `23` (rebuild capability retained by the consultant) |
| Third-party licences | No GPL/AGPL in shipped binaries; `THIRD_PARTY_LICENSES.txt` shipped with the installer (A1 §I, `13`, `17`) |

**Action:** the user (commercial owner) must confirm or amend these terms before delivery; recorded as
the open commercial question `OQ-016` (`18` §4.1) and mirrored in `28` §sign-off.

## 17. Branding

| Element | v1 default (until assets arrive) | Changeable by |
|---|---|---|
| Product name (user-facing) | "FP&A Month-End Copilot" | `Q-019` → settings/branding (`08`, `23`), installer display name (`15`) |
| Logo | None (text lockup only) | Settings: logo file (`08`, `12`) |
| Brand colour 1 (primary/accent) | Neutral slate `#1F3A5F` placeholder | Settings: two brand colours (`08`, `12`) |
| Brand colour 2 (secondary) | Neutral amber `#B7791F` placeholder — used for warnings, never as the only signal | Settings |
| Deck/Excel house style | App house style until the client supplies one recent BvA workbook + one recent management deck (`Q-012`), which then become the base for layout matching | `11`, `12` |
| Theme mechanism | Tokens live in `ui/theme/tokens.ts`, generated/validated against `08`; no hardcoded hex in components (lint-enforced) | `08`, `09` |
| Localisation | English only; number/date/scale display configurable per project (A3 §C.12) | `08` |

**Accessibility guard:** brand colours must satisfy WCAG AA (4.5:1) for text contrast, and favour*ability*
must remain readable when printed in black and white (P19). If a supplied brand colour fails contrast,
the app uses an accessible variant and documents the substitution in `08`.

## 18. Release and phasing overview

The phase plan, estimates, and gate artefacts are owned by `16_ROADMAP_PHASES.md`. This PRD records
only the scope-to-phase mapping in one line: **Phase 1** import & validation → **Phase 2** BvA analysis
& drill-down → **Phase 3** exception engine & register → **Phase 4** forecast → **Phase 5** Excel +
PowerPoint packs → **Phase 6** AI commentary + polish, with the **packaging spike** executed
immediately after Phase 0 approval and before Phase 1 (Addon 4 §L.13).

First-run/onboarding (scope item 9) is delivered progressively with each phase but must be complete
before UAT. The application is not considered delivered until: all gates green, docs `00`–`28` complete,
user guide written, UAT signed, and a real sanitized month reconciled (`28` §Pilot/§UAT).

## 19. Commercial placeholders (flagged, not decided here)

| Item | Status |
|---|---|
| Support/warranty duration and inclusions | **Open commercial question** — to be defined by the user (commercial owner) before delivery (A3 §E.4); placeholder section exists in `23` and `28` |
| Training scope beyond the 60-minute session | Default: one session + user guide; further training is commercial |
| Delivery channel and checksum publication | Default: secure link + published SHA-256 (`Q-016`) |
| Code-signing certificate purchase | Default: not purchased; SmartScreen mitigation applies (`Q-015`) |

## 20. Traceability for this PRD

Every scope statement here maps forward as follows: PRD §6.1 area → `FR-*` family in `02` → screen
`SCR-nnn` in `08` → endpoint `API-nnn` in `26` → test `TST-nnn` in `14` → row in
`20_REQUIREMENTS_TRACEABILITY.md`. PRD success metrics (§7) map to acceptance evidence in `28`.

## 21. Decision index for this document

The **canonical decision log with dates and rationale is owned by `18_...OPEN_QUESTIONS.md` §Decided**.
This table is an index of the rulings made in this document; IDs are allocated here and must appear in
`18` (Addon 3 §B.2, Addon 4 §E.2/E.3).

| ID | Ruling | Section |
|---|---|---|
| `DEC-001` | v1 scope = the 10 areas in §6.1; nothing else is built in v1 | §6.1 |
| `DEC-002` | P&L focus; balance sheet and cash flow out of v1 | §6.3 |
| `DEC-003` | Budgets are import-only; no in-app budget authoring | §6.3 |
| `DEC-004` | Journal-category column optional via mapping profile | §6.3 |
| `DEC-005` | Cross-system tie-out = manual control totals only in v1 | §6.3 |
| `DEC-006` | One-off/exceptional item tagging parked to `BL-024` | §6.2, §6.3 |
| `DEC-007` | Single reporting currency per project; mixed-currency rows quarantined | §6.3 |
| `DEC-008` | Per-entity reporting + simple grouped totals; no eliminations/netting in v1 | §8 |
| `DEC-009` | Pack audience defaults to CFO/finance director; KPI strip configurable | §9 |
| `DEC-010` | Single-user, no login, no RBAC in v1; privacy boundary = OS user account | §10 |
| `DEC-011` | Headcount/FTE metrics parked; no headcount field in the v1 schema | §6.2 |
| `DEC-012` | Prior prototypes are reference-only; no architecture or code reuse | §2.4 |
| `DEC-013` | Success metrics require measured baselines before being reported as achieved | §7 |
| `DEC-014` | Advisory disclaimer wording is canonical in §15.1 | §15.1 |
| `DEC-015` | Data-handling posture: local-only, no upload, AI opt-in + redacted | §15.3 |
| `DEC-016` | IP: consultant retains app IP; client gets a perpetual usage licence | §16 |
| `DEC-017` | Branding defaults apply until assets arrive; colours must meet WCAG AA | §17 |
| `DEC-018` | Packaging spike runs immediately after Phase 0 approval, before Phase 1 | §18 |
| `DEC-019` | Support/warranty terms are flagged as an open commercial question | §19 |
| `DEC-020` | Cross-system tie-out: v1 covers **file-level control totals only**; automated cross-system matching parked (`BL-014`) | §6.3 |
| `DEC-021` | Cross-batch duplicate detection uses **two keys** (voucher+line, and vendor+invoice+date+amount) because neither is sufficient alone | §6.3 |
| `DEC-022` | Control-total variance **fails the import by default**, with an explicit recorded-acceptance path | §6.3 |
| `DEC-023` | Cross-batch duplicate handling **reports and asks** (skip / import anyway / cancel) — never auto-skip, never auto-import | §6.3 |
| `DEC-024` | Exception rules are **registered and catalogued**; an unregistered rule module cannot run, and a new rule requires a catalogue entry + planting + golden test | §6.1 |
| `DEC-025` | Forecast: default project method `remaining_budget`, `N = 3` for run-rate, three scenarios with **default, unconfirmed** adjustment percentages | §6.1, §12 |
| `DEC-026` | AI number-mismatch policy: figures not present in the payload are **stripped and flagged**, never trusted | §6.1, §15.3 |
| `DEC-027` | AI redaction defaults: vendor names and descriptions masked; account/cost-centre/entity codes **not** masked (required for the task) and disclosed to the client | §15.3 |
| `DEC-030` | **Data at rest is plain local files.** No application-level encryption of the analytic database or project backups in v1; the only encrypted artefact is the AI key (DPAPI). BitLocker/EFS guidance is given to the client, and the "not a secure erase" caveat on delete is stated | §15.3, `13` §9.1 |
| `DEC-029` | **Missing-input deck behaviour:** the deck is always the six specified slides, with a *not-available* state naming the reason and the action; omitting a slide is an explicit user choice that must be stated on the deck's cover (`5 of 6 slides generated — <reason>`). Reconciles `FR-PPT-001` with the `08` §11.1 example | `12` §2.1 |
| `DEC-028` | **PDF is not rendered in-app.** v1 delivers print/PDF *readiness* (tested page setup per sheet) plus an "Open for printing / Save as PDF" action using Excel / Microsoft Print to PDF; no bundled renderer and no Excel automation. Rationale and the three rejected alternatives: `11` §10.3 | §12, `11` §10.3 |

