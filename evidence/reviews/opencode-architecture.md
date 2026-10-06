# Architecture review — FP&A Month-End Copilot (opencode, independent)

**Author:** `opencode` (implementation lane) · **Date:** 2026-10-06 · **Status:** review, no code change
**Scope:** technical architecture as built vs as specified (`09`, `13`, `17`, `26`, ADR-001…009), read-only audit.

## 0. Method and honesty statement

Every number below was produced on this checkout; the command is given with it. Claims about
*behaviour* come from reading the code; claims about *intent* come from the docs and are marked as
such. I did **not** re-measure NFR timings (250k import), installer size, or real WebView2
behaviour — those claims remain unverified by me.

Sizing (PowerShell line counts over the tree):

| Area | Lines |
|---|---|
| `app/engine` (`*.py`, excluding `__init__`) | 22,903 |
| `tests/` (`*.py`) | 18,413 |
| `ui/src` (`*.ts`, `*.tsx`) | 14,480 |
| `docs/` (`*.md`) | 18,719 |

Implemented surface: **80** operations across **73** paths in `app/api/openapi.json`; 26 exception
rules; 5 Playwright specs in `ui/e2e/`.

## 1. What is genuinely right — do not touch

| Decision | Why it is right |
|---|---|
| Money as `Decimal` end-to-end into `DECIMAL(18,2)`; no floats on money paths | Hardest property to retrofit; already holds after DEF-015 (TB-030) |
| Headless engine + thin API/CLI/desktop shells, mechanically enforced | The engine-boundary `import-linter` contract now exists (TB-014) and fails on a planted import |
| Hand-written SQL, no ORM (`ADR-007`) | Aggregation-heavy queries stay readable; second dialect avoided |
| No telemetry, no cloud dependency, loopback-only API + per-launch session token | Correct posture for bank-adjacent offline tooling (`09` §9) |
| Deterministic corpus + planted-case acceptance harness | Rare, valuable; gives measurable bars instead of opinions |
| Forward-only migration *intent* (`ADR-008`) | Right idea, unimplemented — see §3.3 |

## 2. The gap that decides "demo vs. tool"

### 2.1 Database lifecycle is wrong at the core — highest priority

`DatabaseManager()` is constructed **per API request** (`app/api/main.py`, ~20 call sites), and its
constructor applies the whole schema and seeds master data on every construction
(`app/engine/store/db.py:46,89-174`: `conn.execute(ddl_path.read_text())` plus ~40 seed
`INSERT OR IGNORE` statements).

```
$ python -c "import time, statistics; from app.engine.store.db import DatabaseManager; \
    ts=[...]; print('DatabaseManager() ms median', statistics.median(ts))"
DatabaseManager() ms: [198.4, 204.6, 127.4, 151.7, 137.6]  median 151.7
duckdb connect alone: 84.5 ms
```

Consequences:

1. Every screen request pays schema-apply + seed cost (~150 ms floor, measured).
2. Every repository call opens a **new DuckDB connection**; there is no pool.
3. `get_duckdb_connection()` **silently degrades to `read_only=True`** after three failed
   read-write attempts (`db.py:179-186`). A write under contention therefore fails late and
   quietly rather than loudly — the worst failure mode for a financial store.
4. `ADR-006`/`09` §3.7 promises "one writer connection owned by the worker thread; read connections
   opened per request with a bounded pool". Neither exists; writer ownership is unenforced.

**Recommendation.** One `DatabaseManager` per process, created in the FastAPI lifespan. Schema init
once, guarded by a `SchemaMetadata.schema_version` read. A single writer handle owned by the worker
thread. A small bounded read pool for queries. **Delete the silent read-only fallback**: make lock
contention an explicit, logged, surfaced error (or a queued write through the worker).

### 2.2 Everything is synchronous — there is no job surface

`app/jobs/` (registry + single worker + states/progress/ETA/cancellation, landed in TB-025) is
**not wired to anything**: there is no `POST /jobs`, no `GET /jobs/{id}`, no cancel endpoint, and
the UI contains no job/progress/ETA code at all (grep over `ui/src` returns zero hits for
`jobs|progress|eta`).

`09` §8.2 is binding: "No job over 2 seconds may run without a visible progress indicator and a
cancel path." A 250k-row import is a synchronous HTTP request today, so that requirement is unmet,
and the user-visible consequence is a spinner-less frozen screen.

**Recommendation.** Thin job API — `POST /jobs` → `202` + `jobId`, `GET /jobs/{id}` → the registry
record, `POST /jobs/{id}/cancel`. UI polls with backoff and raises a completion toast linking the
artefact. The registry already carries states, monotonic progress, ETA-with-warm-up and cooperative
cancellation; this is roughly a day's work, not a redesign. This is the single highest
visible-value item on the list.

### 2.3 No migration engine, and no backup/restore at all

- `SchemaMetadata` exists in `schema_sqlite.sql` but **nothing reads or writes
  `schema_version`**; there is no `migration_log` table in use; `fpa migrate` (added in TB-027) is
  only an idempotent re-init.
- Backup/restore exists as *error-message text only* (`app/engine/errors.py:245-256`,
  `sto.restoreTargetNotEmpty`); there is no implementation anywhere in `app/engine`.

`ADR-008` mandates versioned forward-only migrations with a mandatory backup prompt; `FR-PRJ-008`
makes a portable, secret-free backup a functional requirement; go-live (`TB-046`) requires
backup/restore to be *proven*. As it stands this is a pilot/go-live blocker, not a nicety.

**Recommendation.** Migration runner: ordered `NNN_*.sql` scripts + version table + `migration_log`
+ refuse-to-open when the DB is newer than the app + mandatory backup before a destructive step.
Then `fpa backup` / `fpa restore` with a SHA-256 manifest, exercised against the real
prior-version fixture in `tests/fixtures/` (`TB-040`).

### 2.4 The UI contract rails are documented but not implemented

| Spec rail (`17` §3.2, `26`) | Reality |
|---|---|
| API types **generated** from OpenAPI and imported; no duplication | `ui/src/api/types.ts` is a 20-line stub containing `Record<string, any>`; it is not generated from the 80-operation document |
| Data fetching only through a single API client module | `fetch()` + `X-Session-Token` duplicated across ≥6 components (`main.tsx`, `StaleBanner.tsx`, `PeriodLifecycleScreen.tsx`, …); one path even falls back to `|| 'demo'` as the token |
| Diagnostics reflect real checks (`FR-XC-004..016`, `TB-028`) | `AboutDiagnosticsScreen.tsx` hardcodes `status: 'PASS'`, "All 24 exception rules loaded and verified", "Peak memory 142MB" — asserted, never measured (same tautology class as `DEF-016`) |

**Recommendation.** Generate `ui/src/api/types.ts` from `openapi.json` as a committed, drift-checked
gate step; introduce one `apiClient` module; make the About screen render real `fpa doctor` output.

### 2.5 No observability

Three `logging.getLogger` calls exist in the entire engine (`api/main.py`, `forecast/methods.py`,
`ai/client.py`). There is no handler configuration, no log file, no redaction applied to log calls,
no correlation id threading request → job → repository, and no support bundle — while `13` §11
already ships a sanitizer that could be hung on every log call.

For an offline desktop tool the log file *is* the support channel; today there is none.

**Recommendation.** Central logging setup (file + rotating in-memory buffer), a `redact()` wrapper on
every log call, `X-Correlation-Id` threaded end-to-end, and `fpa doctor --bundle` emitting a
support zip. Roughly an afternoon.

### 2.6 The gate is wired but red, and there is no lockfile

Measured 2026-10-05 after TB-014…TB-017 landed: `ruff format --check` flags **156** files;
`ruff check` reports **1 936** hits in **150** files; `mypy app/engine` reports **140** errors in
**22** files; `npm run lint` reports **80** errors / **15** warnings in **41** files; `npm run
typecheck` (`tsc --noEmit`) is **green**. All four are wired into `scripts/check.py` and all but
tsc are red on pre-existing debt — deliberately left red rather than weakened.

`uv.lock` does not exist (`T-001`, needs owner approval to install `uv`), so ADR-002's "exact pins"
is satisfied only by hand-written lower bounds in `pyproject.toml`.

**Recommendation.** Treat "green gate" as a release blocker and pay it down per module; add a
`scripts/check --changed` fast lane so incremental work is not blocked by unrelated debt; land
`uv.lock` when approved.

## 3. What I would *not* change

No Postgres. No broker/Celery/Redis. No service split. No ORM. No plugin system. No cloud "sync"
tier. For a single-file, offline, one-client-PC FP&A tool the current storage and process model is
right — it only needs to be *honoured* (one writer, one pool, one version table) instead of worked
around. The 33-document spec set is also a genuine asset; its failure mode is not too few docs but
docs asserting rails that code does not yet implement, which is why §2 is written as "spec says X,
code does Y" rather than "code is bad".

## 4. Recommended sequencing (with rough cost)

| Order | Item | Why first | Cost |
|---|---|---|---|
| 1 | DB lifecycle (§2.1) + migration engine & backup/restore (§2.3) | correctness and go-live blockers; every later perf number depends on it | 3–5 days |
| 2 | Job API + UI progress/cancel (§2.2) | converts "script with a UI" into a trusted tool; registry already built | ~1 day |
| 3 | Generated TS types + single API client + real doctor screen (§2.4) | kills the contract-drift and tautology class at the root | 1–2 days |
| 4 | Logging / redaction / support bundle (§2.5) | cheap, pays for itself in the pilot | ~0.5 day |
| 5 | Gate-green campaign, `uv.lock`, packaging/E2E evidence (§2.6) | release readiness | ongoing |

## 5. Risks to keep an eye on

1. **DuckDB single-file growth** — fine at 250k rows/month, but re-verify before multi-year data.
2. **Silent read-only fallback** (§2.1) can turn a write into a read without a trace; the single
   most dangerous line in the current store layer.
3. **Stub-less dependencies** (`python-pptx`, `openpyxl` before `types-openpyxl`, `jsonschema`)
   mean parts of the type story are theatre; keep the single documented boundary pattern rather than
   scattering ignores.
4. **pywebview + WebView2** packaging fragility remains the least-verified part of the stack.
5. **Spec-vs-code drift** is now the top systemic risk: `09` §4.1, §3.7 and `17` §3.2 claim
   enforcement that did not exist until this week. Recommend a quarterly "architecture claims vs.
   reality" pass like this one.