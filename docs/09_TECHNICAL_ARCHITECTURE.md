> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** architecture, ADRs, engine boundary, CLI, storage layout, job queue, crash recovery, migrations, configuration layering, data-volume rule, code-health guardrails
> **TL;DR (≤ 15 lines):** This document owns how the system is built. §3 is the **ADR index** (`ADR-000`
> template + `ADR-001`…`ADR-010`): the approved stack (ADR-001), the pinned toolchain (ADR-002), the
> unsigned-installer stance (ADR-003), the non-synced storage location (ADR-004), real-Windows validation
> (ADR-005), the single-process/threaded-job model (ADR-006), hand-written SQL over an ORM (ADR-007),
> forward-only migrations with backup (ADR-008), static-UI serving through the local API (ADR-009), and
> AI providers over OpenAI-compatible HTTP (ADR-010).
> §4 is the module map and the **headless-engine boundary rule**; §5 the CLI with exit codes; §6 the data
> flow; §7 storage layout, `%LOCALAPPDATA%` decision and the **storage-growth maths**; §8 the job queue,
> cancellation and crash recovery; §9 the local API and security posture; §10 configuration layering;
> §11 recompute/invalidation semantics; §12 the data-volume rule; §13 schema migration; §14 performance
> budgets mapped to `NFR`; §15 spikes, code-health guardrails and the fresh-clone gate.

---

# 09 — TECHNICAL ARCHITECTURE

## 1. Purpose and boundary

| Concern | Owner |
|---|---|
| Stack decisions, module boundaries, storage, jobs, migrations, scripts, CLI | **`09` (this document)** |
| Screen behaviour and layout | `08` |
| Table/column detail | `03` |
| Import mechanisms | `04` |
| Formulas | `05` |
| API endpoint shapes | `26` |
| Security/privacy detail | `13` |
| Packaging/installer steps | `15` |
| Code standards, naming, commits | `17` |

## 2. Architectural principles

1. **Headless engine first.** All logic lives in `app/engine/` as pure Python with no UI, HTTP or desktop
   imports. The API, the CLI and the tests are all thin consumers of the same engine (Addon 2 §B.1).
2. **One process, two stores, no services.** A single user-facing process hosts the local API, the UI and
   the jobs. No microservices, no containers, no background daemons.
3. **Boring and testable.** No speculative abstractions, no plugin systems, no message brokers, no ORM.
4. **Deterministic money maths.** `Decimal` end-to-end (`05` §13); floats are banned in money paths and a
   schema/lint test enforces it.
5. **Nothing is silently discarded or silently changed** (P13, P14). Every state change is auditable and
   versioned.
6. **Offline by default; the network is an explicit, user-initiated exception** (the optional AI call).
7. **Fail readably.** Every failure produces a catalog message plus a hint (`08` §16), never a traceback.
8. **Replaceable edges.** UI framework, packaging or AI provider may change behind their ADRs; the engine
   and the data model must not.

## 3. Architecture Decision Records

### 3.1 `ADR-000` — template and index

**Template (every ADR contains exactly these sections):**

| Section | Content |
|---|---|
| `Status` | `Proposed` / `Accepted` / `Superseded by ADR-nnn` / `Rejected` |
| `Date` | Decision date (and the gate at which it was confirmed) |
| `Context` | The problem and the constraints that force a decision |
| `Decision` | What we will do, stated Imperatively |
| `Alternatives considered` | Each with why it was rejected |
| `Consequences` | Positive, negative, and what becomes harder |
| `Reversibility` | Cheap / costly / irreversible, and the migration path if reversed |
| `Affected docs` | Cross-references updated by this decision |

**Index (a decision without a row here is incomplete — Addon 3 §I.2):**

| ADR | Decision | Status | Date | Reversibility |
|---|---|---|---|---|
| `ADR-001` | Authoritative technical stack (§3.2) | **Accepted** | 2026-10-01 | Costly (packaging + UI would be rebuilt) |
| `ADR-002` | Pinned toolchain and forbidden libraries (§3.3) | **Accepted** | 2026-10-01 | Cheap |
| `ADR-003` | Ship unsigned in v1; SmartScreen mitigation ladder (§3.4) | **Accepted** | 2026-10-01 | Cheap (buy a certificate later) |
| `ADR-004` | Project storage in `%LOCALAPPDATA%`, never a synced folder (§3.5) | **Accepted** | 2026-10-01 | Costly after client data exists |
| `ADR-005` | Real-Windows-11 validation evidence at every gate (§3.6) | **Accepted** | 2026-10-01 | Cheap |
| `ADR-006` | Single process; long jobs on a worker thread; one writer per store (§3.7) | **Accepted** | 2026-10-01 | Costly |
| `ADR-007` | Hand-written SQL over DuckDB/SQLite; no ORM (§3.8) | **Accepted** | 2026-10-01 | Cheap |
| `ADR-008` | Forward-only schema migrations with mandatory backup (§3.9) | **Accepted** | 2026-10-01 | Costly |
| `ADR-009` | The local API serves the built UI as static assets (§3.10) | **Accepted** | 2026-10-01 | Cheap |
| `ADR-010` | AI providers are reached over the OpenAI-compatible HTTP interface; no vendor SDK (§3.11) | **Accepted** | 2026-10-01 | Cheap |

### 3.2 `ADR-001` — Authoritative technical stack

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** kickoff §4 (this is the record required by the spec)

**Context.** A non-technical Windows 11 user needs a self-contained, offline, installable analytics
application with fast aggregation over ~250k-row monthly datasets, deterministic money maths, native
Excel/PPT output and an optional AI call. Two previous prototypes were abandoned for over-engineering.

**Decision.** Build on exactly this stack:

| Layer | Decision |
|---|---|
| Backend / engine | **Python 3.12**, FastAPI (local API on `127.0.0.1:<random port>` with a session token), **DuckDB** for analytics storage, Polars and/or Pandas for transformations, `openpyxl` for Excel read/write, `python-pptx` for PowerPoint, `httpx` for optional AI calls, `pytest` for tests. **Decimal-safe money handling** (Python `Decimal` or integer minor units) — binary floats are forbidden for currency maths |
| Frontend | **React + TypeScript + Vite**, Tailwind CSS, **ECharts** for charts. Single-page app served locally |
| Desktop shell | **pywebview** native window (WebView2 is present on Windows 11) loading the local API/UI; documented fallback = open the default browser at the local URL |
| Persistence | DuckDB file(s) for the analytic model; SQLite for workflow state (exception register, settings, audit log). Files under `%LOCALAPPDATA%\FP&A Month-End Copilot\` (see `ADR-004`, which supersedes the original `Documents` path in this ADR) |
| Packaging | **PyInstaller (onedir, not onefile)** → **Inno Setup** installer producing `Setup-FPandAMonthEndCopilot-<version>.exe`, plus a documented portable-zip option. Desktop + Start Menu shortcuts, uninstaller, app icon, version metadata. No runtime prerequisites |
| Version control | Git, Conventional Commits, docs-only commits kept separate from code commits |
| Explicitly forbidden without an approved ADR | Tauri, Rust, Electron, any cloud service dependency, containers, auto-update frameworks in v1, ORMs/DB layers beyond the above, "AI agent frameworks" for core logic |

**Alternatives considered.** Tauri/Rust (previous prototype's failure mode: heavy toolchain, slow
iteration, no validated core). Electron (large installer, Node runtime weight, two-language codebase).
Pandas-only in memory (insufficient for repeat 250k-row aggregations and no persistence story). SQLite
for analytics (row-store, poor for wide aggregations at this scale). Documented and rejected.

**Consequences.** Positive: one language for the core, mature Excel/PPT libraries, an analytic engine
suited to the data shape, and a well-trodden Windows packaging path. Negative: PyInstaller bundles are
large (bounded by `NFR-006` ≤ 500 MB) and unsigned bundles attract SmartScreen (see `ADR-003`);
WebView2 dependency must be validated on the target machine (`ADR-005` spike list).

**Reversibility.** Costly — replacing the frontend or packaging path is contained, but replacing the
engine or storage layer would touch every module.

**Affected docs.** `03`, `05`, `09`, `13`, `15`, `17`, `24`, `26`.

### 3.3 `ADR-002` — Pinned toolchain (stop framework flip-flopping)

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** Addon 2 §B.5

| Area | Decision |
|---|---|
| Python toolchain | `ruff` (lint + format), `mypy` (strict on `app/engine`), `pytest` + `pytest-cov`, CLI via **`argparse`** — chosen over `typer` to keep the runtime dependency surface minimal in a frozen binary; exactly one of the two is ever used |
| Frontend runtime state | TanStack Query for server state, Zustand for UI state — **no Redux** |
| Routing / tables | React Router; TanStack Table + virtualiser for all grids |
| Frontend testing | Vitest + React Testing Library; **Playwright** for the E2E golden path |
| Frontend hygiene | ESLint + Prettier; `tsc --noEmit` gate |
| Version pinning | Python `3.12.x` pinned (`pyproject.toml` + `.python-version`); Node LTS pinned (`.nvmrc`); exact pins in lockfiles (`uv.lock` + `package-lock.json`) |
| Forbidden | Any library outside this table and `ADR-001` without a new ADR |

**Consequences.** Every shipped import is traceable to `ADR-001`/`ADR-002` (quality-gate item). Adding a
library requires an ADR, which is deliberately friction.

**Reversibility.** Cheap.

### 3.4 `ADR-003` — Unsigned installer in v1, with a written mitigation ladder

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** Addon 1 §G.3/§J, open question `Q-015`

**Context.** PyInstaller output is frequently flagged by SmartScreen/Defender (false positives are
common for unsigned bundles). The client is non-technical and may abandon the install at the first scary
dialog. A code-signing certificate costs money and takes lead time.

**Decision.** Ship v1 **unsigned**, and treat the friction as a launch-blocking workstream rather than a
footnote, with this mitigation ladder:

| Step | Action |
|---|---|
| 1 | Publish the installer's **SHA-256** alongside the download and state the expected size |
| 2 | Provide a **non-technical walkthrough** with screenshots: *"More info" → "Run anyway"*, plus what to do if Defender quarantines the file |
| 3 | Submit the false-positive to Microsoft's malware-analysis portal before delivery; record the submission ID |
| 4 | Recommend the client's IT allow-list the installer path/hash before rollout |
| 5 | Document the **cost and lead time** of a code-signing certificate so the client can choose to fund one; if they do, this ADR is superseded by a signing ADR with no code changes |

**Consequences.** Positive: no cost or lead time blocking delivery; the mitigation is documented and
testable. Negative: residual user friction on first install and any subsequent release; uninstall/reinstall
cycles repeat the prompt. The trade-off is accepted explicitly.

**Reversibility.** Cheap — buying a certificate and signing the same build requires no architectural change.

**Affected docs.** `15`, `24`, `28`, `01` §19, `25` (`RISK-` for SmartScreen).

### 3.5 `ADR-004` — Storage location: `%LOCALAPPDATA%`, never a synced folder

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** Addon 1 §G.1

**Context.** `%USERPROFILE%\Documents` is frequently redirected into OneDrive ("Known Folder Move"). A
DuckDB/SQLite file inside a syncing folder risks lock contention, partial uploads, corrupted databases and
surprising storage consumption.

**Decision.** Project databases, archives, snapshots and logs live under
`%LOCALAPPDATA%\FP&A Month-End Copilot\`. Exports may default to Documents, but the app **detects a synced
path** (Known Folder Move / OneDrive environment markers) and warns with a "use the default location"
action. The app never stores a database on a network share.

| Path | Contents |
|---|---|
| `%LOCALAPPDATA%\FP&A Month-End Copilot\Projects\<project>\` | Project databases, archives, snapshots, exports, logs |
| `%APPDATA%\FP&A Month-End Copilot\` | Machine-level settings, logs, diagnostics, crash reports |
| `%LOCALAPPDATA%\FP&A Month-End Copilot\Sample\` | Bundled sample project (re-creatable) |

**Consequences.** Positive: no sync contention, predictable performance, per-user privacy. Negative:
data does not roam between machines and is not backed up by OneDrive — mitigated by the project
backup/restore feature (`FR-PRJ-008/009`), a backup reminder at period close, and a documented recovery
drill.

**Reversibility.** Costly once client data exists (migration would need a copy-and-verify path).

**Affected docs.** `03` §9.1, `13`, `14` (OneDrive test), `15`, `23`.

### 3.6 `ADR-005` — Real Windows 11 validation evidence at every gate

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** Addon 1 §G.6

**Context.** Development may happen on any OS, but the artefact must run on the client's Windows 11 x64
machine with Defender, WebView2 and 100–150% scaling. "It should work on Windows" is not evidence.

**Decision.** Every phase gate requires evidence from a **real Windows 11 x64 machine**:

| Evidence | Detail |
|---|---|
| Install | `scripts/build` output installed on a clean Windows 11 VM (or the target machine) via the documented per-user install |
| Launch | Cold start measured against `NFR-001` |
| Golden path | The Playwright E2E golden path run in the installed build (Addon 2 §F.4) |
| SmartScreen path | The `ADR-003` walkthrough exercised and screenshotted |
| DPI | Verified at 100% and 150% scaling |
| Offline | The sample-project walkthrough with the network disabled (`NFR-008`) |

Options were: manual checklist on a real machine (chosen, cheapest and sufficient at this scale) versus a
Windows CI runner (deferred; revisit if a hosted Windows runner becomes available at no cost, since it
would automate the `scripts/check` transcript).

**Consequences.** Positive: the gate cannot be passed on optimism. Negative: manual evidence per gate;
the checklist in `15` must be followed precisely (it is scripted to keep it short).

**Reversibility.** Cheap (a CI runner can be added without changing the app).

### 3.7 `ADR-006` — Single process, worker-thread jobs, one writer per store

**Status:** Accepted · **Date:** 2026-10-01

**Context.** Long operations (import, rule runs, exports, migrations) must not freeze the UI, and the two
embedded databases have different concurrency characteristics.

**Decision.**

| Aspect | Decision |
|---|---|
| Process model | **One** application process hosts the API, the UI and the jobs. No subprocesses, no daemon, no service |
| Job execution | Long jobs run on a **single background worker thread** with a job registry exposing progress, ETA and cancellation; the API thread never blocks on analysis work |
| Concurrency limit | **One long job at a time** (queue of depth 1 with an explicit "queued" state); prevents two imports contending for the same stores |
| DuckDB access | One **writer** connection owned by the worker thread; read connections opened per request with a bounded pool. DuckDB file locking is respected, never fought |
| SQLite access | WAL mode; short transactions; `busy_timeout` set; writes serialised through the worker for long operations, immediate for small workflow updates (status changes, notes) |
| Thread safety | Engine functions are pure and stateless; shared state is passed explicitly; no module-level mutable globals |
| Rendering | The UI never blocks on a job: progress arrives by polling a job-status endpoint (and, where supported, server-sent events) |

**Alternatives considered.** Multiprocessing (faster CPU-bound analytics, but PyInstaller multi-process
start-up cost, duplicated memory for the analytic store, and much harder crash recovery in a frozen app);
async task queues (Celery/RQ — requires a broker, forbidden by `ADR-001`); running every job inline
(freezes the UI, breaks `NFR-002`/`NFR-004` UX requirements).

**Consequences.** Positive: simple mental model, easy crash recovery, no IPC. Negative: a very large rule
run plus a simultaneous import must queue; mitigated by the explicit queued state and progress reporting.

**Reversibility.** Costly (job execution is threaded through the API layer), but the engine boundary
(§4) keeps the logic itself process-agnostic.

### 3.8 `ADR-007` — Hand-written SQL, no ORM

**Status:** Accepted · **Date:** 2026-10-01

**Context.** The model spans two engines (DuckDB for analytics, SQLite for workflow) with different SQL
dialects. An ORM would need to abstract both, and the analytic queries are aggregation-heavy where
hand-written SQL is clearer and faster.

**Decision.** Use hand-written SQL in repository modules (`app/engine/store/`), with:

| Rule | Detail |
|---|---|
| Parameterised queries only | No string interpolation of values anywhere (SQL-injection defence applies even locally) |
| One repository module per aggregate | `imports`, `facts`, `exceptions`, `forecast`, `mappings`, `masterdata`, `commentary`, `audit` |
| Schema as SQL scripts | Versioned, reviewed, tested; the schema is the source of truth, not a model class |
| Row mapping | Explicit mapping functions to typed dataclasses at the boundary; no dynamic attribute magic |
| Migration | Forward-only scripts + a version table (`ADR-008`) |

**Alternatives considered.** SQLAlchemy (a second abstraction over two dialects, plus ORM overhead in a
frozen binary); an analytics-oriented ORM (immature for DuckDB); `pandas.read_sql` everywhere (loses
explicit typing and encourages loading more than needed).

**Consequences.** Positive: no dialect abstraction leaks, full control over query plans, small dependency
surface. Negative: more boilerplate and a discipline requirement (reviewed in `17`).

**Reversibility.** Cheap in principle, costly in practice (many call sites) — hence the repository
boundary is enforced from day one.

### 3.9 `ADR-008` — Forward-only migrations with a mandatory backup

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** Addon 1 §J

**Decision.** Schema changes ship as **forward-only** migration scripts applied on project open:

1. Compare `SchemaMetadata.schema_version` with the app's expected version.
2. Older → **prompt for a backup** (recommended, and mandatory before a destructive migration), then run
   the migration in a transaction with progress and a written result, recording it in `migration_log`.
3. Newer than the app → refuse to open with guidance to update the app.
4. Failure → the project is left untouched, the backup is retained, and a diagnostics prompt appears.
5. Migration test fixtures: a **real prior-version project** is retained in `tests/fixtures/` and the
   upgrade test runs against it at every gate (Addon 1 §J, Addon 2 §F).
6. Ad-hoc `ALTER` statements during feature work are forbidden; there is no "quick fix" path.

**Reversibility.** Costly (rolling a client backward requires a restore from backup — which is why the
backup prompt is mandatory).

### 3.10 `ADR-009` — The local API serves the built UI

**Status:** Accepted · **Date:** 2026-10-01

**Decision.** In production, FastAPI serves the built SPA (Vite output) as static assets at `/`, and the
API under `/api/v1/`. pywebview opens the local URL in a native window; the documented fallback opens the
default browser at the same URL. In development, Vite serves the UI and proxies `/api` to the API.

| Rule | Detail |
|---|---|
| Bind address | `127.0.0.1` only, never `0.0.0.0` (the app is single-user and local) |
| Port | Random free port chosen at start-up, passed to the window and to the UI |
| Session token | Generated per launch, required as a header/cookie for every API call; the static shell is served only with the token in the URL fragment (never logged) |
| CORS | No cross-origin access; same-origin only |
| Host allow-list | Requests with a foreign `Host`/`Origin` are rejected |
| No external exposure | The API is not reachable from the network; no tunnelling, no port forwarding |

**Consequences.** Positive: one artefact serves both UI and API, simplifying packaging and the SmartScreen
story (no browser extension, no separate server install). Negative: the UI and API ship together, so a UI
fix requires a rebuild — acceptable at this scale.

**Reversibility.** Cheap.

### 3.11 `ADR-010` — AI providers over the OpenAI-compatible HTTP interface, no vendor SDK

**Status:** Accepted · **Date:** 2026-10-01 · **Source:** Kickoff §10, Addon 1 §I, Addon 3 §D

**Context.** The optional AI features need exactly one capability: a single chat-completions call that
returns JSON. Two provider families must be supported (Azure OpenAI preferred; any OpenAI-compatible
endpoint), the key must be handled locally, and the whole thing ships inside a frozen PyInstaller bundle
where every extra dependency costs installer size and increases the supply-chain surface (Addon 1 §I).
Prompt-injection defence, redaction and output validation must sit **in our code**, not inside a vendor
client we do not control.

**Decision.** Talk to providers over the **OpenAI-compatible HTTP interface using `httpx`** (already in
`ADR-001`). No vendor SDK is added. We own:

| Owned by us | Detail |
|---|---|
| Request assembly | Model/deployment, messages (system + user), response-format hint, temperature fixed at `0.2`, token caps |
| Retry/backoff | 2 retries with exponential backoff on 429/5xx, 30 s timeout, cancellation-aware |
| Response parsing | Strict JSON parse + schema validation + guardrails (doc `10` §8) |
| Error taxonomy | Classified outcomes (`schema_error`, `timeout`, `cap_exceeded`, `refused`, `network_error`, `model_retired`) mapped to the usage log and to user-facing hints |
| Security | Redaction, delimiter escaping, injection defences, key from DPAPI, log hygiene |

**Alternatives considered.** Vendor SDK (adds a large dependency, hides error taxonomy, and its own
version drift would leak into our behaviour); a provider-agnostic AI framework (forbidden by `ADR-001`'s
"no AI agent frameworks for core logic"); direct REST with `requests` (rejected: `httpx` is already
approved and supports timeouts/cancellation better).

**Consequences.** Positive: tiny dependency surface, complete control over redaction and validation,
provider-swappable by configuration, and the same code path is unit-testable with a recorded-response
double. Negative: we track API-version changes ourselves (owned in `24` release notes), and we implement
retry/backoff rather than inheriting it.

**Reversibility.** Cheap — a provider or transport swap touches only `engine/ai/`.

**Affected docs.** `10` (§3 provider configuration), `13` (secrets), `14` (AI fixtures), `24` (API-version
notes in release notes), `26` (endpoints that trigger AI actions).

## 4. Module boundaries and repo structure

### 4.1 The headless-engine boundary rule (Addon 2 §B.1 — non-negotiable)

```
app/
  engine/          ← PURE PYTHON. No FastAPI, no pywebview, no HTTP, no UI imports. Ever.
    calc/          formulas (CALC-nnn, KPI-nnn)
    rules/         one module per exception rule (EXC-nnn)
    forecast/      method resolution, generation, accuracy
    imports/       parse → map → validate → stage → commit
    store/         repositories (hand-written SQL, ADR-007)
    exports/       Excel pack (openpyxl), PPT deck (python-pptx)
    ai/            provider client, prompt assembly, redaction, schema validation
    common/        Decimal helpers, period maths, hashing, message slugs
  api/             FastAPI app, routers, schemas, error envelope, session token
  cli/             argparse entry points over the engine
  desktop/         pywebview shell, single-instance mutex, window/DPI handling
  jobs/            worker thread, job registry, progress/ETA, cancellation
ui/                React + TS + Vite SPA (src/, theme/tokens.ts, e2e/ Playwright)
tests/             unit, golden, rules, contract, artefacts, integration, e2e, perf, manual, fixtures (prior-version projects)
packaging/         PyInstaller spec, Inno Setup script, icons, version metadata
scripts/           dev, check, build, release, acceptance, perf (one command each)
sample-data/       generator, templates, planted exceptions, malformed corpus
docs/              this documentation set
```

**Enforcement:** an import-linter rule (run by `scripts/check`) fails the build if `app/engine/**` imports
`fastapi`, `pywebview`, `app.api`, `app.desktop` or `app.jobs`. Violations fail code review, and the rule
is a quality-gate item.

### 4.2 Layer responsibilities

| Layer | May import | May not |
|---|---|---|
| `engine` | stdlib, approved third-party libs (`ADR-001`), `engine.*` | API, UI, desktop, jobs, HTTP |
| `api` | engine, its own schemas, FastAPI | UI source, desktop, direct SQL outside repositories |
| `cli` | engine, stdlib (`argparse`) | API internals, UI |
| `desktop` | stdlib, `pywebview`, the API app object | engine internals directly (it only starts the API) |
| `jobs` | engine, its own registry | API routers (it reports progress through the registry the API reads) |
| `ui` | its own code, the generated API types (`26`) | any Python |

### 4.3 Engine module responsibilities

| Module | Owns | Key entry points |
|---|---|---|
| `engine/imports` | Pre-scan, parse, map, validate (32 checks), stage, commit, void, quarantine | `prescan()`, `validate_file()`, `commit_batch()`, `void_batch()` |
| `engine/calc` | All `CALC-` formulas and `KPI-` definitions; single implementation shared by every consumer | `variance()`, `windows()`, `kpis()`, `rollups()`, `quality_score()` |
| `engine/rules` | 24 rule modules with declared dependencies, subject keys and deterministic evaluation | `run_rules(context, rule_ids)` |
| `engine/forecast` | Method resolution, eligibility, generation, scenarios, locking, accuracy | `generate()`, `lock_version()`, `accuracy()` |
| `engine/exports` | Excel pack and PPT deck generation with the shared formatting rules (`08` §14) | `build_excel_pack()`, `build_ppt_pack()` |
| `engine/ai` | Provider client, prompt assembly from versioned templates, redaction, schema validation, caps, usage log | `draft_commentary()`, `suggest_mappings()`, `validate_response()` |
| `engine/store` | Repositories over DuckDB and SQLite; schema application; migrations | `open_project()`, `apply_migrations()`, per-aggregate repositories |
| `engine/common` | Decimal/money helpers, fiscal-period maths, hashing (`row_fingerprint`, `identity_hash`), message slugs | used everywhere |

**Rule:** no module outside `engine/calc` implements a formula, and no module outside `engine/rules`
implements a rule. Duplicated arithmetic is a defect, not a shortcut — it is the root cause of the
display/export drift the cross-artifact test exists to catch.

## 5. Command-line interface

### 5.1 Purpose

The CLI is the automation, testing and support surface over the same engine (Addon 2 §B.1). It exists so
that (a) tests target the engine without HTTP, (b) support can reproduce a client issue from a backup, and
(c) the parked automation backlog (Power BI export, scheduled runs) has a foundation.

### 5.2 Commands

```
python -m app.cli <command> --project <path> [options]
```

| Command | Purpose | Key options |
|---|---|---|
| `import` | Import a file end-to-end (pre-scan → validate → commit) | `--file <path> --source-type <t> --profile <name> [--dry-run]` |
| `validate` | Validate a file without committing (produces the report) | `--file <path> --source-type <t> [--report <path>]` |
| `bva` | Emit BvA figures for a filter context | `--period <code> --window <mtd\|ytd\|py_mtd\|py_ytd\|ttm> [--entity <code>] [--account <code>]` |
| `exceptions` | Run rules (or list the register) | `[--run] [--period <code>] [--severity <s>] [--status <s>] [--export <path>]` |
| `forecast` | Generate, list or lock forecast versions | `[--generate] [--scenario <code>] [--lock] [--accuracy]` |
| `export-xlsx` | Build the Excel pack | `--period <code> --out <path> [--window <w>]` |
| `export-ppt` | Build the PowerPoint deck | `--period <code> --out <path> [--scenario <code>]` |
| `doctor` | Environment/project health: DB integrity, disk space, schema compatibility, WebView2 presence, permissions, profile versions | `[--json]` |
| `migrate` | Apply pending schema migrations (with backup) | `[--backup <path>] [--dry-run]` |
| `report` | Emit the validation report for a batch | `--batch <id> --out <path>` |

### 5.3 Behaviour and exit codes

| Aspect | Rule |
|---|---|
| `--json` | Available on every command; emits a single machine-readable JSON object on stdout (`{status, data, warnings[], errors[]}`) suitable for CI |
| stdout/stderr | Human-readable output on stdout; **all** errors and warnings on stderr; `--json` keeps stdout pure JSON |
| Non-interactive | The CLI never prompts. A decision that the UI would ask about (duplicate handling, over-limit confirmation) becomes a required flag or a refusal with the reason |
| Dry run | `--dry-run` performs every step up to commit and reports exactly what would change |
| Determinism | Identical inputs produce identical outputs and exit codes (no timestamps in machine-readable payloads unless requested) |
| Safety | Mutating commands (`import`, `forecast --lock`, `migrate`) refuse to run against a project locked by a running app instance (single-instance mutex, §7.4) |

**Exit codes (documented and stable — scripts may rely on them):**

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Unexpected internal failure (a bug; a diagnostics bundle is offered) |
| `2` | Usage error (unknown command, missing/invalid argument) |
| `3` | Project error (not found, locked by another instance, schema newer than the app) |
| `4` | Import/validation rejection (the file failed a file-level check; nothing committed) |
| `5` | Rule-run failure (engine error while evaluating rules; partial results are discarded) |
| `6` | Export failure (file not produced; existing file untouched) |
| `7` | Environment failure (`doctor` findings that block work: no WebView2, no write permission, low disk) |
| `8` | Cancelled by the user (Ctrl+C) — state is clean and resumable |

### 5.4 Why `argparse` and not a CLI framework

Chosen in `ADR-002`: `argparse` is stdlib, has no runtime dependency cost in a frozen binary, and every
command here is a thin adapter over the engine. A framework buys nothing that this surface needs.

## 6. Data flow

```
 Source files (xlsx/csv)
        │
        ▼
 ┌──────────────────┐   stage rows, run 32 checks, quarantine failures
 │ engine/imports   │──────────────────────────────────────────────┐
 └────────┬─────────┘                                              │
          │ commit (single transaction)                            │
          ▼                                                        ▼
 ┌──────────────────┐      ┌──────────────────┐         ┌──────────────────┐
 │  DuckDB          │      │  SQLite          │         │  archives/       │
 │  facts, dims,    │◄────►│  batches,        │         │  immutable raw   │
 │  validation,     │      │  exceptions,     │         │  files + checksum│
 │  forecast,       │      │  mappings,       │         └──────────────────┘
 │  derived views   │      │  master data,    │
 └────────┬─────────┘      │  commentary,     │
          │                │  audit, settings │
          │                └────────┬─────────┘
          │                         │
          ▼                         ▼
 ┌───────────────────────────────────────────────┐
 │           engine/calc · rules · forecast      │   derived on demand;
 │  (deterministic; single implementation)       │   nothing cached silently
 └────────┬──────────────────────┬───────────────┘
          │                      │
          ▼                      ▼
 ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
 │  api (FastAPI)   │   │  exports         │   │  ai (optional)   │
 │  page-sized,     │   │  Excel + PPT     │   │  draft text only │
 │  aggregated      │   │  native objects  │   │  never numbers   │
 └────────┬─────────┘   └────────┬─────────┘   └──────────────────┘
          ▼                      ▼
   React SPA (pywebview)   reports/ files
```

**Invariants in the flow:** (1) every fact row carries its `import_batch_id`; (2) derived results are
computed on demand (§11); (3) the UI receives aggregated, page-sized payloads only (§12); (4) AI sits
outside the numeric path entirely.

## 7. Storage, files and environment

### 7.1 On-disk layout

| Location | Contents | Backed up by |
|---|---|---|
| `%LOCALAPPDATA%\FP&A Month-End Copilot\Projects\<project>\analytics.duckdb` | Analytic model | Project backup |
| `…\state.sqlite` | Workflow state | Project backup |
| `…\archives\` | Immutable raw source files (read-only, named `<yyyymmdd-HHMM>_<source_type>_<checksum8>.<ext>`) | Project backup (optionally excluded by archive-and-delete, `FR-PRJ-011`) |
| `…\snapshots\` | Immutable close/issue snapshots | Project backup |
| `…\exports\` | Generated packs | Not backed up (regenerable) |
| `…\logs\` | Local logs, rotated | Not backed up |
| `%APPDATA%\FP&A Month-End Copilot\` | Machine settings, AI key (DPAPI), diagnostics, crash reports, `security.log` (key lifecycle, deletions, sync overrides — `13` §6.3) | Not applicable (machine-local, secret-bearing) |
| `%LOCALAPPDATA%\FP&A Month-End Copilot\Sample\` | Bundled sample project | Re-creatable from the installer |

### 7.2 The OneDrive / synced-folder rule (`ADR-004`)

| Situation | Behaviour |
|---|---|
| Project folder inside a detected syncing path | **Blocked by default** with an explanation and a "use the default location" action (the user may override with an explicit, recorded acknowledgement) |
| Export path inside a syncing path | Allowed with a warning about lock/performance risk |
| Import reading a file from a syncing path | Warned (`import.syncedPathWarning`); the app always reads a **stable copy** into staging, never the live file |
| Detection method | Environment markers (`OneDrive`, `OneDriveCommercial`), known-folder redirection registry values, and a path-prefix check |

### 7.3 Storage-growth maths (Addon 4 §I.4)

Assumptions (labelled **estimates to be validated at the real-data pilot**):

| Input | Value |
|---|---|
| Actual GL rows per month | ~180,000 (peak file 250,000) |
| Rows per year | ~2.16 M |
| DuckDB effective bytes/row incl. indexes and derived views | ~150–280 B (columnar, compressed) |
| Source files archived per month | 3 systems ≈ 30–50 MB |
| Snapshot per close/issue | ~2–5 MB each, 1–2 per month |
| Exports | User-managed; typically replaced or deleted, not counted as growth |

| Horizon | DuckDB | Raw archives | Project total (indicative) |
|---|---|---|---|
| 1 month | ~30–55 MB | ~30–50 MB | **~60–105 MB** |
| 1 year | ~350–600 MB | ~0.4–0.6 GB | **~0.8–1.2 GB** |
| 3 years | ~1.1–1.8 GB | ~1.1–1.8 GB | **~2.2–3.6 GB** |

**Controls:** Settings shows a storage breakdown (`FR-PRJ-011`); a low-storage warning fires below a
configurable free-space threshold (default **5 GB**); **archive-and-delete** exports and removes raw
archives while keeping the analytic model intact; the `doctor` command reports disk space. Raw-archive
retention default: **keep indefinitely** unless the user runs archive-and-delete (evidence retention
outranks disk usage for an audit tool).

**Consistency note:** the per-month DuckDB range here (30–55 MB) matches the `03` §9.2 estimate
(35–60 MB); both are placeholders until measured at the pilot, at which point both documents are updated
together.

### 7.4 Single instance and file locks

| Rule | Detail |
|---|---|
| Mutex | A named mutex **per project** (and one global mutex for machine settings) |
| Second launch, same project | Friendly dialog: *"This project is already open in another window"* with "Switch to it" / "Close" — never a database-lock error (`FR-PRJ-006`) |
| Second launch, different project | Allowed (each project is independent); both share the worker-thread policy per process |
| CLI while the app is open | Mutating commands refuse with exit code `3` and an explanation |
| Stale mutex after a crash | Detected and cleared on launch by checking that the recorded PID is gone; the user sees an informational note, not an error |

### 7.5 Logging and error strategy

| Aspect | Rule |
|---|---|
| Locations | `%APPDATA%\FP&A Month-End Copilot\logs\` (app-level) and the project's `logs\` (project-level) |
| Rotation | Size/age limits from `NFR-011` (7 days / 50 MB); rotation is automatic and silent |
| Content policy | **No secrets, no financial amounts, no vendor names** in normal logs (`13`); IDs, counts, durations, codes and message slugs instead |
| Levels | `INFO` default; `DEBUG` toggleable per session for support (with a visible banner that verbose logging is on) |
| Error strategy | Engine raises typed errors carrying a catalog message + hint; the API maps them to the standard envelope (`26`); the UI renders message + hint; unexpected exceptions produce a diagnostics-ready log entry and the `SCR-041` dialog — **never a traceback in the UI** |
| Crash handling | An unhandled process-level failure writes a local crash report (no upload), records interrupted jobs, and shows the recovery dialog on next launch (§8.3) |
| Timing | Every long job records stage timings, surfaced in Diagnostics (`FR-XC-016`) for `NFR` verification on the client's machine |

## 8. Job execution, cancellation and crash recovery

### 8.1 Job model

| Aspect | Rule |
|---|---|
| Job types | `import_validate`, `import_commit`, `rule_run`, `forecast_generate`, `export_xlsx`, `export_ppt`, `backup`, `restore`, `migrate`, `ai_batch` |
| Registry | Each job has an id, type, state (`queued` / `running` / `cancelling` / `succeeded` / `failed` / `cancelled`), progress percentage, current stage, ETA, started/finished timestamps and a result summary |
| Concurrency | One long job at a time (queue depth 1); a second request shows `queued` with its position |
| Progress reporting | Stages with weights (pre-scan 5%, parse 40%, validate 35%, stage 15%, commit 5% for imports) so the aggregate percentage is monotonic and honest |
| ETA | Computed from observed throughput with a warm-up window; if the estimate is unstable the UI shows elapsed time and the stage instead of a misleading ETA |
| Cancellation | Cooperative cancellation checked at every stage boundary and every N rows (N documented per job type); a cancelled job rolls back its transaction and reports the clean state |
| Results | Success leaves a summary artefact (report, file paths, counts) linked from the job; failure leaves the reason and a "Copy details" payload |

### 8.2 UI expectations (binding on `08`)

No job over 2 seconds may run without a visible progress indicator and a cancel path; navigation is never
blocked; and a job's completion raises a toast that links to the result (report, batch, generated file).

### 8.3 Crash recovery

| Interruption | Recovery on next launch |
|---|---|
| Crash during **staging** an import | The staged batch is detected and offered for **discard** or **resume**; the UI states plainly that nothing was committed |
| Crash during **commit** | The transaction is rolled back by the database; the batch is marked `cancelled` with the reason; no partial data exists |
| Crash during **export** | The partial file in a temp location is discarded; the target path is untouched (exports are written to a temp file and atomically renamed) |
| Crash during **migration** | The backup is retained; the project opens in its pre-migration state and the migration is reported as not applied |
| Crash at any other point | The project opens normally; derived results are recomputed or marked stale; interrupted jobs are listed with their state |
| Sleep/standby mid-job (A1 §G.4) | The job either completes on resume or fails cleanly into the same recoverable state as a crash |

## 9. Local API and security posture (summary; detail in `13`/`26`)

| Aspect | Rule |
|---|---|
| Bind | `127.0.0.1`, random free port, never `0.0.0.0` (`ADR-009`) |
| Auth | Per-launch session token (header/cookie); the API rejects requests without it |
| Host/Origin | Foreign `Host`/`Origin` rejected; no CORS cross-origin allowance |
| Payload limits | Request bodies capped; file uploads stream directly to the staging area rather than into memory |
| Secrets | AI key via Windows DPAPI/Credential Manager; never in project files, backups, logs or exports (`13`) |
| Outbound network | Only the configured AI endpoint, only on explicit user action, only with redaction applied |
| Telemetry | **None.** No analytics, no crash upload, no update ping without a user action |
| Update check | Manual only; disabled by default (`FR-XC-015`) |

## 10. Configuration layering

**Precedence: project setting → app (machine) setting → built-in default.** A project setting wins
because it travels with the data; a machine setting supplies what the project does not specify.

| Layer | Stored in | Contains | Travels with backup? |
|---|---|---|---|
| **App-level** (machine) | `AppSetting` (SQLite in `%APPDATA%`) | AI provider/model/key (DPAPI), theme, language, data directory, telemetry flag (always off), log level, update-check preference | **No** (and contains secrets) |
| **Project-level** | `ProjectSetting` (SQLite inside the project) | Fiscal calendar, currency/units/display locale, mappings and profile versions, thresholds and rule configuration, master data references, branding, storage preferences, KPI selection, forecast defaults | **Yes** — a project backup is portable and contains **no secrets** (`FR-PRJ-008`) |
| **Built-in** | Code + seeded tables | Defaults for every setting, seed master data, default thresholds, built-in profiles | n/a |

| Rule | Detail |
|---|---|
| Precedence is visible | Settings screens label each value as *project* or *this computer* so a user can predict what a backup carries |
| No hidden third layer | No per-screen or per-session settings; if a value matters it is one of the two layers |
| Secrets never leave the machine | A project backup must never contain an AI key — asserted by a test (`FR-PRJ-008`) |
| Change tracking | Every change to a project setting is versioned (`VersionHistory`) and, where it affects derived results, marks them stale (§11) |

## 11. Recompute and invalidation semantics (Addon 2 §B.7)

| Rule | Detail |
|---|---|
| Derived on demand | Aggregates, BvA, exceptions and forecasts are computed on demand from stored facts; there are **no unbounded caches** |
| No silent staleness | A change to mappings, thresholds, master data, loaded data or forecast configuration marks dependent derived results **stale** and raises the visible "Re-run required" banner naming what changed (`FR-SET-010`) |
| Staleness model | Per artefact type (aggregates · BvA · exceptions · forecast · packs) with the timestamp of the last successful computation and the reason for staleness |
| Re-run actions | The banner offers the specific re-run (e.g. "Re-run rules"), which is a normal job with progress |
| Snapshot immunity | Issued packs read their frozen snapshot; a re-run never rewrites an issued pack's numbers (`FR-PRJ-010`) |
| Cache policy if ever introduced | Any future cache must be **bounded, keyed by an invalidation token, and documented here first** — otherwise it may not ship |
| Cheap memoisation | In-process memoisation is permitted only for the lifetime of a single request, and never across a write boundary |

## 12. Data-volume rule (Addon 2 §B.3)

| Rule | Detail |
|---|---|
| Server-side everything | Aggregation, filtering, sorting and pagination happen in DuckDB/SQLite; the UI never receives raw bulk rows |
| Page size | Default **100**, maximum **200** rows per page for detail grids |
| Aggregation payloads | One aggregation result set per view; column-capped and row-capped (top N with an explicit "of M" note) |
| Virtualisation | All grids virtualise rows; drill lists paginate; no screen loads a full dataset into React state |
| Streaming | Large details are streamed page-by-page; exports are generated server-side to file, never through the browser |
| Payload budget | JSON responses are size-checked in tests; a response exceeding the documented budget fails the test (protects the ≤ 2 s interaction `NFR-003`) |
| Search | Search returns a capped result set (default 50 per group) with counts and a link to the full filtered view |
| Enforcement | A performance test at `--scale 250000` asserts the payload sizes and interaction timings (Addon 2 §F.1, Addon 3 §I.1) |

## 13. Schema migration strategy

Detailed in `ADR-008`; operational detail lives in `24_RELEASE_AND_VERSIONING_RUNBOOK.md`. The
architecture-level rules:

1. `SchemaMetadata.schema_version` (integer) is the only source of truth for the schema state.
2. Migrations are ordered, forward-only scripts with an idempotence guard and a recorded `migration_log`.
3. A migration that cannot complete leaves the project untouched and the backup in place.
4. **Every release that changes the schema must ship a migration and a prior-version test fixture**
   (Addon 1 P15: a release that cannot upgrade is not releasable).
5. No feature work may perform DDL outside a migration script.
6. Downgrading the app is not supported; the documented rollback is *restore from the pre-migration
   backup*.

## 14. Performance budgets mapped to the architecture

| NFR | Budget | Architectural driver |
|---|---|---|
| `NFR-001` Cold start ≤ 10 s (sample project) | Avoid import-time work: lazy-load AI/export modules; open stores once; defer rule/dimension work until requested | `ADR-006`, lazy imports, single process |
| `NFR-002` Import 250k rows ≤ 60 s | Bulk insert via DuckDB `Appender`/batched `INSERT`, vectorised validation, validation and staging in one pass, no per-row round-trips | `engine/imports`, DuckDB native bulk paths |
| `NFR-003` Dashboard interaction ≤ 2 s | Pre-aggregated dimension joins, server-side aggregation, page-sized payloads, virtualised grids, indexed fact columns | `engine/calc`, §12 |
| `NFR-004` PPT generation ≤ 15 s | `python-pptx` with native charts (no image rendering), reused base deck, single pass over aggregated data | `engine/exports` |
| `NFR-005` Memory ≤ 1.5 GB during import | Streaming parse (no full-file DataFrame), bounded batches, staged rows written to disk | `engine/imports` |
| `NFR-006` Installer ≤ 500 MB | PyInstaller `onedir`, excluded dev dependencies, `--exclude-module` for unused scientific stacks, compressed Inno Setup | `packaging/`, `ADR-001` |
| `NFR-007` Rule run ≤ 60 s over 250k rows | Set-based evaluation in SQL where possible, one pass per rule family, indexed subject keys | `engine/rules` |
| `NFR-008` Offline walkthrough passes | No background network calls anywhere; AI strictly user-initiated | `ADR-009`, §9 |
| `NFR-009` Excel pack ≤ 120 s at 250k rows | Write-only workbook mode, one pass over aggregates, no full-sheet DataFrame (`11` §13) | `engine/exports` |
| `NFR-010` Diagnostics zip ≤ 20 MB | Metadata-only bundle with a capped log tail; opt-in for data rows | `FR-XC-005` |
| `NFR-011` Logs ≤ 50 MB / 7 days | Rotation, no verbose logging by default, no amounts/vendor names in logs | §7.5 |
| `NFR-012` Crash never yields a raw traceback | Typed errors + catalog mapping + global handler + recovery flow | §7.5, §8.3 |
| `NFR-013` Screen ≥ 1366×768, 100–150 % scaling correct | Responsive layout, DPI-aware sizing, minimum-size enforcement | `ui/` |
| `NFR-014` Coverage: engine ≥ 90 %, backend ≥ 75 % | Test discipline enforced in `scripts/check` | `14` |
| `NFR-015` Cross-artifact equality (zero tolerance) | Values-only workbooks, engine authority, parsed-back assertions | `14` §7 |
| `NFR-016` UI responsive during long jobs | Worker-thread jobs + polling API; no blocking calls on the UI thread | `09` §7.4 |

*(Numbers themselves are owned by `14`; this table records which architectural decision protects each.)*

## 15. Engineering discipline

### 15.1 Spike policy (Addon 4 §I.1)

A risky unknown gets a **timeboxed spike (≤ half a day)** with a written question, the options considered,
and an outcome recorded as an ADR or a `27_BACKLOG.md` entry **before** any production code is committed.

**Pre-approved spike list** (to be run immediately after Phase 0 approval, before Phase 1 feature work):

| # | Spike question | Output |
|---|---|---|
| `SPK-01` | Does the PyInstaller bundle install and launch on a real Windows 11 machine without triggers beyond the documented SmartScreen path? | Packaging ADR update + `15` evidence |
| `SPK-02` | Does Defender quarantine the build? What are the exact dialogs? | `ADR-003` mitigation confirmation + screenshots for the walkthrough |
| `SPK-03` | Does `python-pptx` reproduce the client's slide fidelity (fonts, chart styling, speaker notes) on a supplied template? | `12` feasibility note |
| `SPK-04` | Does WebView2 behave correctly (window sizing, DPI 150%, printing, clipboard) in the packaged build? | `08`/`09` notes |
| `SPK-05` | DuckDB performance on a 250k-row import and aggregation set on a 4-core/8 GB machine | `NFR` baseline recorded in `14` |
| `SPK-06` | Does Playwright drive the packaged app's UI on Windows (or only the dev server)? | `14` E2E approach |
| `SPK-07` | Which openpyxl behaviours matter for the client's real workbooks (tables, named styles, conditional formats)? | `11` notes |
| `SPK-08` | Does the pinned `python-pptx` support a native waterfall chart (`XL_CHART_TYPE.WATERFALL`), and does PowerPoint render the generated XML correctly? If not, the documented stacked-column fallback is used | `12` §5.2 (chart decision recorded there) |

**Rule:** a spike never ships partial production code; its findings update the owning document first.

### 15.2 Fresh-clone bootstrap test (Addon 4 §I.2)

Every phase gate proves that a **clean `git clone`** plus the documented bootstrap (`scripts/dev` or
`scripts/check`) works with no machine-local state:

| Requirement | Detail |
|---|---|
| No untracked prerequisites | No machine-local secrets, no manual file copies, no undocumented steps |
| Reproducible installs | `uv sync` + `npm ci` from lockfiles only |
| Documented environment | `.python-version`, `.nvmrc`, `README` bootstrap section, `scripts/dev` |
| Evidence | The transcript of a clean-clone `scripts/check` run is attached to the gate (Addon 1 §G.6 spirit) |

### 15.3 Code-health guardrails (Addon 4 §I.3)

| Rule | Enforcement |
|---|---|
| No source file over **500 LOC** without a justification note in the file header | `scripts/check` line-count check with an allow-list that must name a reason |
| Zero commented-out code | Review + lint heuristic |
| Every `TODO` cites a `27_BACKLOG.md` ID (e.g. `TODO(BL-018)`) | Lint rule where practical; review otherwise |
| Dead code deleted, not left behind | Review; unreferenced-module check |
| Engine-boundary import rule | Import-linter in `scripts/check` (§4.1) |
| No `print()` in library code | Lint |
| No bare `except:` | Lint (typed exceptions only) |
| Type hygiene | `mypy --strict` on `app/engine`; typed public functions elsewhere |
| Coverage bars | `app/engine` ≥ 90%, backend ≥ 75%, enforced by `scripts/check` (Addon 2 §F.1) |

### 15.4 One-command scripts (Addon 2 §B.6)

| Script | What it does | Must succeed from a clean checkout |
|---|---|---|
| `scripts/dev` | Install/sync dependencies, start the API with reload, start Vite with the proxy, open the app window | Yes |
| `scripts/check` | Format check + lint + `mypy` + eslint + `tsc --noEmit` + pytest (+coverage) + contract tests + import-linter + link-check + guardrails | **Yes — this is the gate** |
| `scripts/build` | UI build → PyInstaller (`onedir`) → Inno Setup installer → emit artefacts and checksums | Yes (on Windows) |
| `scripts/release` | Bump version (app + schema if applicable), update CHANGELOG, tag, build, emit SHA-256, produce release notes | Yes (on Windows) |

**Rule:** `scripts/build` from a clean checkout is part of every release checklist (`24`), and packaging
evidence always comes from a real Windows 11 machine (`ADR-005`).

## 16. Traceability

| Architectural area | FRs | Docs |
|---|---|---|
| Engine boundary, CLI | `FR-XC-*`, `FR-IMP-*`, `FR-EXC-*`, `FR-FC-*` | `17`, `19`, `26` |
| Storage, backups, health | `FR-PRJ-008`…`FR-PRJ-011`, `FR-SET-009` | `03`, `13`, `15` |
| Jobs, cancellation, recovery | `FR-IMP-030`, `FR-XC-008` | `02`, `08`, `14` |
| Configuration layering | `FR-SET-001`, `FR-PRJ-009` | `13`, `23` |
| Recompute/invalidation | `FR-SET-010`, `FR-PRJ-010` | `02`, `08` |
| Data-volume rule | `FR-XC-010`, `FR-BVA-010` | `08`, `14` |
| Migrations | `FR-PRJ-007` | `03`, `24` |
| Performance budgets | all `NFR` | `14` |
| Spikes, guardrails, scripts | process | `17`, `19`, `27` |

## 17. Change control

1. A new dependency requires an ADR (or an explicit extension of `ADR-002`) **before** the import appears
   in code.
2. A new architectural boundary or module requires an update to §4 first; violating the engine boundary is
   a review-blocking defect.
3. A new long-running operation must register as a job (§8) with stages, progress and cancellation — no
   unbounded blocking work in the API thread.
4. Any cache requires §11 updated first, with its invalidation rule stated.
5. `ADR-000`'s index (§3.1) must list every ADR; a decision without a row is incomplete.

