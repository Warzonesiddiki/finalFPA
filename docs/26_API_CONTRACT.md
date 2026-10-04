> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the **HTTP contract** at `/api/v1/`: the OpenAPI document as the single source of truth,
> the universal envelope, pagination/filter/sort grammar, value encodings, the long-job contract, the
> **error-code catalogue** (`ERR-<FAM>-nnn`, families registered in `00_INDEX` §8), the type-generation and
> contract-test workflow, and the endpoint → FR/screen reverse index (Addon 2 §B.2/§B.3/§B.4/§B.6/§H.4)
> **TL;DR (≤ 15 lines):**
> - **Authoritative interface:** 95 REST API endpoints providing headless engine functionality to UI and external CLI consumers.
> - **Standard error envelope:** Consistent JSON envelope (success flag, data payload, error code, plain message, hint, request ID).
> - **Data pagination:** Enforces strict limits preventing the browser from receiving raw transaction firehoses.
> - **OpenAPI source of truth:** Automated Pydantic schema generation; TypeScript client types generated directly from OpenAPI.
> - **Contract testing:** Every endpoint covered by schema-validation and HTTP status contract tests in CI pipeline.

# 26 — API Contract

## 1. Purpose, ownership and boundary

### 1.1 What this document owns

| Owned here | Detail |
|---|---|
| The OpenAPI document | The schema of record for every route, request, response and error (§6) |
| The universal envelope | Success, list, error and warning shapes (§2.2–§2.4) |
| Pagination, filter and sort grammar | One grammar for UI and API (§2.5); parity is tested (`TST-API-04`) |
| Value encodings | Dates, decimals, nulls, ids, enums, `n/a` (§2.6) |
| The long-job contract | `202` + `GET /jobs` poll, progress, cancel, terminal states (§2.7) |
| The **error-code catalogue** | Families, codes, slugs, HTTP mapping, hints (§5); `08` §16 owns wording/shape |
| The type-generation workflow | `openapi-typescript` output committed; drift is a build error (§6) |
| Contract tests | Fixture layout and the `TST-API-01`…`016` mapping (§7) |
| The endpoint → FR/screen reverse index | §10 (the forward direction stays in `20` §3) |

### 1.2 What this document does not own

| Not here | Owner |
|---|---|
| Which engine function computes a number | `05`/`06`/`07` (this document only says how it is exposed) |
| Message wording, banned words, severity vocabulary | `08` §16 |
| Transport security (loopback, token, origin, TLS posture) | `ADR-009`, `13` §3 (restated, never re-decided here) |
| The CLI's flags and exit codes | `09` §5.2/§5.3 (this document keeps parity honest, §11) |
| Storage layout and migrations | `09` §7/§13, `ADR-004`/`ADR-008` |
| Screen behaviour and states | `08` (this document names the consuming screen only) |

### 1.3 Readers and how the contract is used

| Reader | Uses § |
|---|---|
| Backend engineer | §2, §4, §5, §6, §7 |
| Frontend engineer | §2, §4, §6 (generated types), §8, §10 |
| Test engineer | §5, §7, §8 |
| Reviewer at a gate | §10 (coverage), §6 (drift), §7 (fixtures), §13 (frozen constants) |
| Consultant/support | §5 (what a code means, what the hint says) |

## 2. The universal contract

### 2.1 Transport and authorship

| Rule | Detail |
|---|---|
| Prefix | Every route is under `/api/v1/`; a breaking change is `/api/v2/` and a new ADR, never an in-place mutation |
| Binding | `127.0.0.1` on a random free port chosen at launch (`ADR-009`); the shell discovers the port and hands it to the WebView |
| Auth | Every route requires the per-launch token (`X-FPA-Token`), including `GET /health`; a missing/incorrect token is `ERR-API-001` (`SEC-004`/`008`) |
| Origin | Only the app origin is accepted; CORS is closed and DNS-rebinding-style requests are refused (`TST-API-06`) |
| Concurrency | One FastAPI process, one worker thread for long jobs (`ADR-006`); a second long job is `queued` with its position |
| Payloads | JSON only (`application/json`); file downloads are `application/octet-stream` or `text/csv` with a filename header |
| No cache by accident | Responses carry `Cache-Control: no-store`; the UI has no HTTP cache layer (TanStack Query owns cache semantics) |
| Determinism | Identical requests return identical payloads for identical data; ordering is always explicit (never engine-default) |

### 2.2 Success envelope

```json
{ "status": "ok", "data": { }, "warnings": [], "errors": [] }
```

| Field | Type | Rule |
|---|---|---|
| `status` | `"ok"` | Always present; `"error"` on any failure (§2.3) |
| `data` | object / array / null | The payload; `null` only for `Ack`-style commands |
| `warnings` | `Finding[]` | Non-blocking findings the UI must show (stale data, caps hit, ignored rows) |
| `errors` | `Finding[]` | Empty on success — present in every response so clients parse one shape |

`Finding` is defined in §4.2. Warnings never change the HTTP status; they are part of the payload.

### 2.3 Error envelope and the universal codes

```json
{ "status": "error", "data": null, "warnings": [],
  "errors": [ { "code": "ERR-STO-006", "slug": "period.closed", "severity": "blocking",
                "message": "September 2026 is closed.",
                "hint": "Reopen the period first (audited), or import into the open period.",
                "details": [ { "path": "periodId", "value": "2026-09" } ] } ] }
```

| Rule | Detail |
|---|---|
| One error object per failure | Field-level problems are separate entries in `details[]`, never prose-only (`TST-API-16`) |
| `code` | A catalogue code (§5); stable forever, never reused, never renumbered |
| `slug` | The dotted join key used by `02`/`04`/`08` (e.g. `import.missingRequiredColumns`) |
| `hint` | The next action, in plain language; if a code has no hint it is not shippable (`08` §16.1) |
| `details[]` | `{path, value, expected?}` pointers for field-level validation; never a stack trace, SQL, or a path outside the project folder (`TST-API-02`) |
| `severity` | `info` / `attention` / `blocking`, matching the catalogue (`08` §16.2) |
| Status mapping | `400` malformed/validation, `401` token, `404` not found, `409` state conflict/lock, `413` payload too large, `422` contract violation (dev builds), `429` provider rate limit, `500` unexpected internal, `503` dependency unavailable |
| `500` handling | Any unexpected exception becomes `ERR-ENG-010` with the correlation id in `details[]`; the traceback goes to the log only, and a diagnostics offer appears in the UI |

**Universal codes — declared once, never repeated per row in §3.**

| Code | HTTP | Trigger | Hint |
|---|---|---|---|
| `ERR-API-001` | 401 | Missing/incorrect per-launch token, or a request from another origin | "Restart the app from the desktop shortcut." |
| `ERR-API-002` | 404 | Unknown route or wrong method | "This action isn't available in this version — update the app." |
| `ERR-API-003` | 400 | Unsupported filter/sort parameter or operator (§2.5) | "Reload the view; if it repeats, send a diagnostics bundle." |
| `ERR-API-004` | 400 | `pageSize` above the cap or a non-integer page | "Reload the view — the app will use the standard page size." |
| `ERR-API-005` | 413 | Request body above the documented limit (1 MB; imports and packs use the file path, not the body) | "Use the file-based action instead of pasting data." |
| `ERR-API-006` | 422 | Schema/handler mismatch — a **development and test** failure, enforced by `TST-API-07` | "This is a build error; report it with the diagnostics bundle." |
| `ERR-API-007` | 400 | Unsupported `Accept`/version prefix | "Update the app to match the requested contract version." |

### 2.4 List envelope and pagination

```json
{ "status": "ok", "data": { "items": [], "total": 0, "page": 1, "pageSize": 100, "hasMore": false },
  "warnings": [], "errors": [] }
```

| Rule | Detail |
|---|---|
| Defaults | `page=1`, `pageSize=100`; `pageSize` cap **200** (`09` §12) — values above the cap are rejected (`ERR-API-004`), never silently clamped |
| `hasMore` | Computed server-side from `total` and the current window; the virtualiser relies on it (never on `items.length == pageSize`) |
| Stable ordering | Every list declares a deterministic sort (documented per endpoint), with a tie-break on a unique key so pages never overlap or skip |
| `total` | The count for the *filtered* set, computed in the same query |
| Deep paging | Offset paging is allowed to 10,000 rows; beyond that the UI must narrow the filter (a capped view, not an error) |
| Aggregations | One result set per view, column-capped and row-capped with an explicit "of M" note (`09` §12) |
| Search | Capped at 50 items per group with per-group totals and a link to the filtered view (`09` §12) |

### 2.5 Filter, sort and column grammar

```
?filter=severity:in:High,Medium;status:eq:open;amount:gte:100000
&sort=-amount,ruleId            # '-' = descending; commas are the tie-break order
&columns=ruleId,subject,amount  # optional projection; the endpoint's default columns apply otherwise
```

| Operator | Meaning | Applies to |
|---|---|---|
| `eq` / `ne` | equals / not equals | text, enum, id, date, decimal |
| `gt` / `gte` / `lt` / `lte` | comparisons | date, decimal, integer |
| `in` | comma-separated set | text, enum, id |
| `contains` | case-insensitive substring | text |
| `between` | `a..b` inclusive | date, decimal, integer |
| `isnull` / `notnull` | presence test | any nullable field |

| Rule | Detail |
|---|---|
| Fields | Only the fields an endpoint declares as filterable/sortable; anything else is `ERR-API-003` (no SQL passthrough, ever) |
| Values | URL-encoded; dates `YYYY-MM-DD`; periods `YYYY-Pnn`; decimals as plain strings (§2.6); `null` is not a literal (use `isnull`) |
| Parity | The UI builds this grammar through one client helper; the same filter must return the same rows in UI and API (`TST-API-04`) |
| Persistence | The shared filter context is stored per project via `GET`/`PUT /filters` and survives navigation (`FR-` behaviour owned by `08`) |
| No ad-hoc SQL | There is no endpoint that accepts SQL or an expression string; the API surface is fixed by §3 |

### 2.6 Value encodings

| Kind | Encoding | Rule |
|---|---|---|
| Money | String decimal, `"1234567.89"` | Never a JSON number: IEEE-754 would break the Decimal-only rule (`05` §2). Scale comes from the field; display rounding is the client's job (`05` §6.3) |
| Percentages / ratios | String decimal or `"n/a"` | Division by zero is `n/a`, never `Infinity`/`NaN` (`05` §9) |
| Dates | `YYYY-MM-DD` | No timezone, no time-of-day except `raisedAt`/`runAt` which are ISO-8601 with the local offset |
| Periods | `YYYY-Pnn` plus `{startDate, endDate, status}` | The period object is the only place month semantics live |
| Ids | Opaque strings | Clients never parse them; `rule_id + subject_key` is the exception's stable identity (`03`) |
| Enums | Lower-case snake strings | `severity: "high"`, `status: "open"`, `state: "running"` — the UI maps to display text (`08` §16) |
| Nulls | `null` | Absent ≠ null: an absent field means "not requested"; `null` means "no value" |
| Booleans | `true`/`false` | No `0`/`1`, no `"yes"` |
| Large ints | String when > 2^53 | Counts and byte sizes above that are strings to avoid precision loss |

### 2.7 Long-running jobs

| Rule | Detail |
|---|---|
| Trigger | A long route returns `202` with `{jobId}` inside the standard envelope; the work runs on the worker thread (`ADR-006`) |
| Poll | `GET /jobs?state=active` (drawer) or `GET /jobs/{id}` (one job) returns the `Job` shape (§4.2) |
| States | `queued` / `running` / `cancelling` / `succeeded` / `failed` / `cancelled` (`09` §8.1) |
| Progress | Monotonic percentage with a named stage and an honest ETA (elapsed + stage when unstable) — the same numbers the drawer shows |
| Cancel | `POST /jobs/{id}/cancel` is cooperative: the job stops at the next boundary, rolls back, and reports `cancelled` |
| Result | On success the job's `result` carries ids/paths (report, file, counts); on failure it carries one catalogue error, never a traceback |
| Queue depth 1 | A second job is `queued` with its position; the UI must show that honestly (no invented parallelism) |
| Server restart | Jobs do not survive a restart; the UI re-reads state and shows the interrupted work as not-run (`09` §8.3) |

### 2.8 Exports, downloads and uploads

| Rule | Detail |
|---|---|
| Exports | Generated server-side to the path the user chose and returned as `FileRef`; the browser never assembles the file |
| Downloads | `GET /imports/{batch}/archive` streams the archived source with its SHA-256 in a header; range requests are not required |
| CSV | UTF-8 with BOM, CRLF, quoted per RFC 4180 (`TST-API-11`) — the same writer as `11`/`06` exports |
| Uploads | Files are referenced by **path** (the app runs locally); request bodies never carry file bytes |
| Collisions | The export collision policy is `11` §12: prompt, keep-both with the next `vN`, never silent overwrite |
| Partial files | A failed or cancelled export leaves nothing behind (write to a temp name, then rename) |

### 2.9 Warnings, stale markers and cap notices

| Situation | Contract |
|---|---|
| Derived results older than a mapping/threshold/master-data change | The response carries a `stale` warning `Finding` with `slug: "results.stale"`; screens show the "Re-run required" banner (`08` §17, `09` §11) |
| Rows ignored or quarantined | Import responses carry warnings naming the counts; details live in the report endpoints |
| A cap was applied (top-N, search, deep paging) | A `capped` warning with `{shown, total}` so the UI can say "showing 10 of 43" |
| A rule auto-disabled for missing master data | A warning on `GET /rules` and inside rule-run results (`06` §2.9) |
| AI off / keyless | AI endpoints return `ERR-AI-001` with the rule-based alternative in the hint (`10` §3) |

### 2.10 Safety rules

| Rule | Detail |
|---|---|
| `GET` has no side effects | Never triggers a write, a migration or a job (`TST-API-15`) |
| Idempotency | Every mutating POST accepts an `Idempotency-Key` header; a repeated key returns the first result rather than double-applying (`TST-API-15`) |
| Typed confirmations | Destructive or lock-breaking routes require the confirmation fields in §3 (project name, `confirmText`, `reason`); a missing/mismatched value is `ERR-VAL-001` |
| Closed-period writes | Any write touching a closed period is `409 ERR-STO-006` unless it is the audited reopen route |
| Audit | Every mutation writes one audit entry per object (bulk actions: one per item) and returns the ids in `details[]` where the screen links to them |

## 3. Endpoint inventory (95 routes)

Every route below is adopted **verbatim** from `20` §2.3. Columns: the contract shape (`Request → Response`,
with the named shapes of §4), the domain error codes beyond the universal set of §2.3 (which applies to
every row and is therefore not repeated), the consuming screen(s) and the FR(s) that require the route.

| Rule | Detail |
|---|---|
| No aliases | A renamed path is recorded in `26` + `20` + `CHANGELOG` in one change; the old path is removed |
| No orphans | Every route has at least one FR consumer and one consuming screen (`14` §12.3) |
| Permissions | All routes require the per-launch token (`ERR-API-001`); there is no other permission model in v1 (`DEC-010`) |
| Idempotency | Every mutating route honours `Idempotency-Key` (§2.10) |

### 3.1 Lifecycle — projects, periods, storage (19)

Area error profile: `ERR-STO-001`/`003`/`006`/`008`/`010`/`012`/`013`/`014`, `ERR-SEC-007`/`008`, `ERR-ENG-005`/`008`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `GET /bootstrap` | First-run state: ensure/share the sample project, resolve the last project, launch target | `— → {app:{appVersion, docsVersion, schemaVersion}, sample:{exists, path\|null, convertPending}, lastProject:ProjectRef\|null, firstRun:bool}` | — | `SCR-001`, `SCR-002` | `FR-ONB-001`, `FR-ONB-006` |
| `GET /projects` | Recent-project list (path, last opened, last period, status) | `?q?, ?page, ?pageSize → Page<ProjectRef>` | — | `SCR-002` | `FR-PRJ-003` |
| `POST /projects` | Create a project (fiscal calendar, currency, units, entities, optional branding) | `{name, path, fiscalStart, currency, units, entities[], sample:bool=false, branding?} → Project` | — | `SCR-002`, `SCR-003` | `FR-PRJ-002`, `FR-SET-005` |
| `POST /projects/{id}/open` | Open a project: single-instance mutex, schema check/migration, period state | `{} → {project:Project, period:PeriodState, migration?:MigrationNote}` | — | `SCR-002` | `FR-PRJ-003`, `FR-PRJ-006`, `FR-PRJ-007` |
| `GET /projects/{id}` | Project and period status, health summary for Home | `— → {project:Project, periods:[PeriodState], health:Health}` | — | `SCR-001` | `FR-ONB-008`, `FR-PRJ-001` |
| `DELETE /projects/{id}` | Delete a project (typed confirmation recorded) [Later Phase / Planned] | `{confirmName} → Ack` | `ERR-VAL-001` (name mismatch) | `SCR-002` | `FR-PRJ-012` |
| `POST /projects/{id}/backup` | Backup zip (databases, archives, settings, mappings, master data; manifest; no secrets) | `{outPath} → 202 Job → {file:FileRef, manifest:{entries, sha256}}` | — | `SCR-039` | `FR-PRJ-008` |
| `POST /projects/restore` | Validate a backup zip and restore it to a chosen folder | `{zipPath, targetPath, confirm:true} → 202 Job → {project:ProjectRef}` | `ERR-STO-008`/`009` (zip invalid, target not empty) | `SCR-002`, `SCR-039` | `FR-PRJ-009` |
| `POST /projects/{id}/convert` | Convert a sample project to a normal project (typed confirmation, audit-logged) | `{confirmText, keepSampleCopy:bool} → Project` | — | `SCR-001` | `FR-ONB-008` |
| `GET /projects/{id}/storage` | Storage breakdown, low-storage warning inputs, archive sizes | `— → {areas:[{name, bytes}], archiveBytes, freeBytes, warning:Finding\|null}` | — | `SCR-032`, `SCR-040` | `FR-PRJ-011`, `FR-SET-009` |
| `POST /projects/{id}/archive-raw` | Archive raw files to a user-chosen zip, then remove them after confirmation | `{outPath, batchIds?} → 202 Job → {file:FileRef, removedBytes}` | — | `SCR-032`, `SCR-040` | `FR-PRJ-011` |
| `GET /projects/{id}/versions` | Version history for mappings, thresholds, master data, assumptions, prompts, branding | `?kind=, ?page, ?pageSize → Page<VersionRef>` | — | `SCR-033`, `SCR-035`, `SCR-037` | `FR-SET-011` |
| `POST /projects/{id}/versions/{v}/revert` | Revert a versioned artefact to a named version | `{confirm:true} → VersionRef` | — | `SCR-033`, `SCR-035`, `SCR-037` | `FR-SET-011` |
| `GET /projects/{id}/periods` | Period list with Open/Closed status | `— → {items:[PeriodState]}` | — | `SCR-001`, `SCR-004` | `FR-PRJ-004` |
| `POST /projects/{id}/periods` | Open a new period (expected-source checklist; carries config forward, never numbers) | `{code, startDate, endDate, expectedSources[]?} → PeriodState` | — | `SCR-001`, `SCR-004` | `FR-PRJ-004` |
| `POST /periods/{id}/close` | Close a period: lock actuals, prompt the backup reminder | `{confirm:true, backupReminder:Ack} → PeriodState` | `ERR-STO-007` (already closed), `ERR-VAL-001` | `SCR-001`, `SCR-004` | `FR-PRJ-005` |
| `POST /periods/{id}/reopen` | Warned, typed-confirmation, audited reopen | `{confirmText, reason} → PeriodState` | `ERR-STO-006` (closed-period guard is the route's purpose), `ERR-VAL-001` | `SCR-001`, `SCR-004` | `FR-PRJ-005` |
| `GET /periods/{id}/snapshots` | Read-only period-close snapshots behind issued packs | `— → {items:[SnapshotRef]}` | — | `SCR-001`, `SCR-030` | `FR-PRJ-010` |
| `GET /checks` | Check-screen aggregate: validation findings, exception counts, stale markers, storage warnings [Later Phase / Planned] | `?period → ChecksSummary` | — | `SCR-001` | `FR-PRJ-001`, `FR-SET-010` |

### 3.2 Imports and batches (11)

Area error profile: `ERR-IMP-001`…`032`, `ERR-VAL-002`, `ERR-STO-002`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `POST /imports/pre-scan` | Source type, SHA-256 fingerprint, size/rows/estimate, limit checks | `{path, sourceType?} → PreScan` | — | `SCR-001`, `SCR-005`, `SCR-006`, `SCR-007`, `SCR-009` | `FR-ONB-003`, `FR-IMP-001`, `FR-IMP-002`, `FR-IMP-003`, `FR-IMP-007`, `FR-IMP-019` |
| `POST /imports` | Stage → parse → validate a file (long-running job; 202 + `GET /jobs` poll) | `{path, sourceType, sheetName?, headerRow?, profileId\|null, dryRun:bool=false, overLimitAck?, balanceTolerance?, controlTotalAcceptance?:{acceptedBy, reason}} → 202 Job → BatchRef` | `ERR-IMP-002`/`003` (over-limit confirmation), `ERR-IMP-001` (unreadable), `ERR-STO-002` | `SCR-005`, `SCR-007`, `SCR-008`, `SCR-009`, `SCR-010`, `SCR-014` | `FR-IMP-009`, `FR-IMP-010`, `FR-IMP-012`, `FR-IMP-014`, `FR-IMP-015`, `FR-IMP-027`, `FR-IMP-030`, `FR-IMP-031` |
| `GET /imports` | Batch history (status, counts, score, links to report and archive) | `?period, ?status, ?page, ?pageSize → Page<BatchRef>` | — | `SCR-011` | `FR-IMP-023` |
| `PUT /imports/{batch}/mapping` | Column mapping with preview, overrides, profile apply/save | `{columns:[{source, target, rule?}], multiHeaderRows?, saveProfileAs?} → MappingPreview` | — | `SCR-008`, `SCR-011`, `SCR-033` | `FR-IMP-004`, `FR-IMP-011`, `FR-IMP-026` |
| `GET /imports/{batch}/report` | Validation report (per-check pass/fail, counts, samples, control totals, timings) | `?page, ?pageSize, ?check → Report` | — | `SCR-009`, `SCR-010`, `SCR-012` | `FR-IMP-016`, `FR-IMP-017`, `FR-IMP-021` |
| `GET /imports/{batch}/quarantine` | Quarantined rows with failing field, reason and raw values | `?check, ?page, ?pageSize → Page<QuarantineRow>` | — | `SCR-013` | `FR-IMP-013` |
| `POST /imports/{batch}/commit` | Atomic staged commit (single transaction) | `{acceptWarningIds[]} → CommitResult` | `ERR-IMP-*` re-checked at commit; nothing is written on failure | `SCR-010` | `FR-IMP-018`, `FR-IMP-020`, `FR-IMP-028` |
| `POST /imports/{batch}/cancel` | Cancel staging; no partial data left behind | `— → Ack` | — | `SCR-009` | `FR-IMP-030` |
| `POST /imports/{batch}/void` | Void/reverse one batch (all-or-nothing; blocked for closed periods) | `{confirm:true, reason} → VoidResult` | `ERR-STO-006` when the batch's period is closed | `SCR-011` | `FR-IMP-024` |
| `GET /imports/{batch}/archive` | The immutable archived source file and its recorded checksum | `— → FileRef (download; sha256 in header)` | — | `SCR-011`, `SCR-012` | `FR-IMP-025` |
| `GET /imports/{batch}/score` | Data-quality score with the per-check breakdown | `— → ScoreBreakdown` | — | `SCR-010`, `SCR-014` | `FR-IMP-022` |

### 3.3 Mapping profiles, master data, rules, settings (15)

Area error profile: `ERR-VAL-003`, `ERR-STO-002`/`010`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `GET /mapping-profiles` | List/version mapping profiles; header-fingerprint suggestion source | `?sourceType, ?q → {items:[ProfileRef], suggestion:ProfileRef\|null}` | — | `SCR-008`, `SCR-033` | `FR-IMP-005`, `FR-IMP-006`, `FR-SET-002` |
| `PUT /mapping-profiles/{id}` | Create/edit/clone a profile (column map, overrides, date/number rules) | `ProfileBody → ProfileRef` | — | `SCR-008`, `SCR-033` | `FR-IMP-005`, `FR-SET-002` |
| `GET /master-data/{kind}` | Master-data tables (vendor categories, recurring costs, approval thresholds, owners) | `?page, ?pageSize, ?q → Page<MasterRow>` | — | `SCR-034` | `FR-SET-003` |
| `PUT /master-data/{kind}` | Edit master data (versioned, revertable) | `{rows[], versionNote} → MasterTable` | — | `SCR-034` | `FR-SET-003` |
| `POST /master-data/{kind}/import` | Import master data through the standard validation/archive path | `{path, dryRun:bool=false} → 202 Job → MasterTable` | — | `SCR-034` | `FR-IMP-029` |
| `GET /rules` | Rule catalogue with per-project enable state, defaults and effective thresholds | `— → {items:[RuleState], engine:{runAt\|null, stale:bool}}` | — | `SCR-014`, `SCR-023`, `SCR-034`, `SCR-035` | `FR-EXC-012`, `FR-EXC-014`, `FR-SET-004` |
| `PUT /rules/{id}` | Edit a rule's threshold/enable state (versioned; marks derived results stale) | `{enabled?, threshold?, severity?, note} → RuleState` | — | `SCR-035` | `FR-EXC-012`, `FR-SET-004` |
| `POST /rules/run` | Run the enabled rule set over the loaded data (job; run summary) | `{period, scope?} → 202 Job → RunSummary` | — | `SCR-014`, `SCR-023` | `FR-EXC-001`, `FR-EXC-003`, `FR-EXC-005`, `FR-EXC-020` |
| `GET /settings` | All settings (machine vs project scope) for the Settings screens | `— → {machine:{...}, project:{...}, precedence:[AppLevel, ProjectLevel]}` | — | `SCR-032`, `SCR-038` | `FR-AI-001`, `FR-SET-001` |
| `PUT /settings` | Update settings (display, thresholds, branding, storage, rule defaults) | `{scope:'machine'\|'project', patch} → SettingsView` | — | `SCR-003`, `SCR-032`, `SCR-035`, `SCR-036`, `SCR-037` | `FR-EXC-013`, `FR-PPT-006`, `FR-SET-006`, `FR-SET-007`, `FR-SET-008`, `FR-SET-009` |
| `PUT /settings/ai-key` | Store the AI key via DPAPI (write-only; status returned, never the key) | `{key, endpoint, model, deployment?} → {status:'stored'\|'rejected'\|'unreachable', checked:bool}` | `ERR-SEC-001`/`002` (DPAPI/key rejection), `ERR-SEC-004`/`005` (TLS/network) | `SCR-038` | `FR-AI-002` |
| `DELETE /settings/ai-key` | Rotate/revoke: purge the old value from config and memory, audit-logged | `{confirm:true} → Ack` | — | `SCR-038` | `FR-AI-003` |
| `PUT /ui-state` | UI state: tour dismissal, last screen per project, sticky display preferences | `{tourDismissed?, lastScreenByProject?, stickyDisplay?} → UiState` | — | `SCR-001`, `SCR-002`, `SCR-043` | `FR-ONB-002`, `FR-ONB-006` |
| `GET /filters` | Shared filter context for the current project | `— → FilterContext` | — |  | `FR-BVA-015` |
| `PUT /filters` | Persist the shared filter context (survives navigation) | `FilterContext → FilterContext` | — |  | `FR-BVA-015` |

### 3.4 Analysis and search (9)

Area error profile: `ERR-BVA-001`…`003`, `ERR-VAL-003`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `GET /analysis/bva` | BvA matrix: windows, grain, rollups, variance, comparability, entity sums | `?period, ?window, ?grain, ?entity, ?account, ?scenario, ?materiality, ?page → BvaMatrix` | — | `SCR-015`, `SCR-022` | `FR-BVA-001`, `FR-BVA-002`, `FR-BVA-003`, `FR-BVA-009`, `FR-BVA-013`, `FR-BVA-014`, `FR-BVA-016`, `FR-XC-010` |
| `GET /analysis/bridge` | Bridge/waterfall drivers from Budget to Actual [Mapped to /api/v1/bva] | `?period, ?window, ?entity → BridgeSet` | — | `SCR-016` | `FR-BVA-005` |
| `GET /analysis/trends` | Multi-period actual/budget/PY trends and variance bars [Mapped to /api/v1/bva] | `?period, ?buckets, ?grain, ?window → TrendSet` | — | `SCR-017` | `FR-BVA-006` |
| `GET /analysis/topn` | Ranked adverse/favourable variances with the deterministic tie-break [Mapped to /api/v1/bva] | `?period, ?window, ?n=10, ?side, ?basis → RankedVariances` | — | `SCR-018` | `FR-BVA-007` |
| `GET /analysis/three-way` | Actual vs Budget vs Forecast with accuracy columns [Mapped to /api/v1/bva] | `?period, ?window, ?grain → ThreeWay` | — | `SCR-019` | `FR-BVA-008` |
| `GET /analysis/kpis` | KPI/ratio cards with target comparison and drill target [Mapped to /api/v1/bva] | `?period, ?window → KpiCards` | — | `SCR-020` | `FR-BVA-010` |
| `GET /analysis/drill` | Transaction detail for exactly one displayed figure (source-file evidence) | `?figure, ?key, ?page, ?pageSize → Page<DrillRow> (each row carries its source file + batch)` | `ERR-BVA-004` (ambiguous figure) | `SCR-021` | `FR-BVA-004` |
| `GET /search` | Grouped search across vouchers, vendors, descriptions, accounts | `?q, ?groups → {groups:[{name, total, items[]}], capped:true}` | — | `SCR-022` | `FR-BVA-012` |
| `POST /exports/ad-hoc` | Export what you see (current filter/sort/columns) to Excel or CSV | `{grid, filter, sort, columns, format:'xlsx'\|'csv', outPath?} → 202 Job → FileRef` | — | `SCR-015`, `SCR-022` | `FR-BVA-011` |

### 3.5 Exceptions (7)

Area error profile: `ERR-STO-002`, `ERR-VAL-003`, `ERR-EXP-001`/`003`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `GET /exceptions` | Register rows for the current filter (severity, amount at risk, owner, status, aging) | `?period, ?severity, ?status, ?owner, ?rule, ?q, ?sort, ?page, ?pageSize → Page<ExceptionRow>` | — | `SCR-023`, `SCR-024` | `FR-EXC-002`, `FR-EXC-009`, `FR-EXC-011`, `FR-EXC-019`, `FR-XC-010` |
| `GET /exceptions/{id}` | Exception detail with history, notes and evidence links | `— → ExceptionDetail` | — | `SCR-023` | `FR-EXC-004` |
| `PATCH /exceptions/{id}` | Status, owner and note changes (append-only note history) | `{status?, owner?, note?} → ExceptionDetail` | — | `SCR-024`, `SCR-034` | `FR-EXC-006`, `FR-EXC-007`, `FR-EXC-008` |
| `POST /exceptions/bulk` | Bulk status/owner change (one audit entry per item) | `{ids[], patch, note?} → {updated, skipped:[{id, reason}], auditIds[]}` | — | `SCR-023` | `FR-EXC-010` |
| `GET /exceptions/effectiveness` | Per-rule effectiveness analytics (raised, explained share, days to close, tuning) [Later Phase / Planned] | `?period, ?ruleId → EffectivenessTable` | — | `SCR-026` | `FR-EXC-015` |
| `POST /exceptions/{id}/evidence` | Evidence bundle workbook/zip for one exception | `{include:{validation, mapping, audit}} → 202 Job → FileRef` | — | `SCR-024`, `SCR-025` | `FR-EXC-016`, `FR-XL-007` |
| `GET /exceptions/export` | Register export: filtered sheet + unfiltered sheet, owner-wise grouping [Mapped to /api/v1/exceptions/export/owner] | `?filter, ?outPath → 202 Job → FileRef` | — | `SCR-023` | `FR-EXC-017`, `FR-EXC-018` |

### 3.6 Forecast (7)

Area error profile: `ERR-FC-001`…`003`, `ERR-STO-002`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `GET /forecast/versions` | Forecast versions, scenarios, locks and provenance | `?scenario → {items:[VersionRef], locked:[VersionRef]}` | — | `SCR-027` | `FR-FC-001`, `FR-FC-004` |
| `POST /forecast/versions` | Create/copy/rename/delete a scenario/version | `{op:'create'\|'copy'\|'rename'\|'delete', from?, name?, scenario?} → VersionRef` | — | `SCR-027`, `SCR-028` | `FR-FC-003` |
| `POST /forecast/run` | Generate the forecast (method per line/group; job) | `{period, scope, methods?, scenario} → 202 Job → RunSummary` | — | `SCR-027` | `FR-FC-002`, `FR-FC-005` |
| `PATCH /forecast/cells` | Manual override with a mandatory reason (audited) | `{cells:[{line, period, value}], reason} → {applied, auditId}` | — | `SCR-027` | `FR-FC-006` |
| `POST /forecast/versions/{v}/lock` | Lock a version (read-only; referenced by issued packs) | `{confirm:true} → VersionRef` | — | `SCR-027`, `SCR-028` | `FR-FC-009` |
| `GET /forecast/compare` | Version/scenario comparison | `?a, ?b, ?grain → CompareSet` | — | `SCR-027`, `SCR-028` | `FR-FC-009` |
| `GET /forecast/accuracy` | Forecast-vs-actual accuracy metrics and method guidance | `?period, ?version → AccuracyReport` | — | `SCR-028` | `FR-FC-007`, `FR-FC-008` |

### 3.7 Packs, issuance, commentary, templates (10)

Area error profile: `ERR-EXP-001`…`018`, `ERR-STO-002`, `ERR-VAL-001`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `POST /packs/excel` | Generate the Excel pack (job; 250k-row and standard paths) | `{period, window, scope?, outPath?} → 202 Job → PackRef` | `ERR-EXP-001`…`011` | `SCR-029` | `FR-XL-001`, `FR-XL-002`, `FR-XL-004`, `FR-XL-005`, `FR-XL-006`, `FR-XL-008`, `FR-XL-009` |
| `POST /packs/deck` | Generate the six-slide deck (job; base-deck mode included) | `{period, scenario?, baseDeckMode:bool=false} → 202 Job → PackRef` | `ERR-EXP-012`…`018` | `SCR-029`, `SCR-031`, `SCR-037` | `FR-PPT-001`, `FR-PPT-002`, `FR-PPT-003`, `FR-PPT-004`, `FR-PPT-005`, `FR-PPT-007`, `FR-PPT-008`, `FR-PPT-009` |
| `POST /packs/{id}/refresh` | Refresh a pack from current data and report exactly what changed | `{dataScopeAck:true} → 202 Job → RefreshDiff` | — | `SCR-029` | `FR-XL-003` |
| `GET /packs` | Generated/issued packs with version, snapshot reference and status | `?period, ?status, ?page → Page<PackRef>` | — | `SCR-029` | `FR-XL-003` |
| `POST /issuance` | Issue a pack: freeze snapshots, lock commentary, record recipients, increment version | `{packId, recipients[], lockCommentary:true, confirm:true} → IssuanceRef` | — | `SCR-030`, `SCR-031` | `FR-XC-002` |
| `GET /issuance` | Issuance register (every issued version, recipients, re-issues) | `?period, ?page → Page<IssuanceRef>` | — | `SCR-030` | `FR-XC-003` |
| `POST /issuance/{id}/reissue` | Re-issue: new pack version; the previous version stays immutable | `{reason, changesAck} → IssuanceRef (version+1)` | — | `SCR-030` | `FR-XC-003` |
| `GET /commentary` | Commentary for lines/periods (typed, rule-based or approved AI draft) | `?period, ?scope, ?page → Page<CommentaryRow>` | — | `SCR-029`, `SCR-031` | `FR-AI-013`, `FR-XC-001` |
| `PUT /commentary` | Save commentary (locked after issuance until a re-issue) | `{rows:[{key, text, source}], lock:bool=false} → CommentaryRows` | — | `SCR-029`, `SCR-031` | `FR-XC-001` |
| `POST /templates/export` | Write a blank input template (actuals/budget/forecast/master data) to a chosen path | `{kind:'actuals'\|'budget'\|'forecast'\|'master-data', outPath} → FileRef` | — | `SCR-001`, `SCR-005` | `FR-ONB-005` |

### 3.8 Optional AI (7)

Area error profile: `ERR-SEC-001`…`005`, `ERR-AI-001`…`003`, `ERR-STO-002`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `POST /ai/test-connection` | Manual connectivity test for the configured endpoint (user-triggered only) | `{} → {reachable, latencyMs, models?[], finding:Finding\|null}` | — | `SCR-038` | `FR-AI-014` |
| `POST /ai/drafts` | Run one of the four AI features (variance commentary, mapping suggestion, exception summary, follow-up draft) | `{feature:'variance'\|'mapping'\|'exception'\|'commentary', scope, promptVersion?, evidenceAck:true} → 202 Job → Draft` | — | `SCR-008`, `SCR-023`, `SCR-029`, `SCR-031`, `SCR-038` | `FR-AI-004`, `FR-AI-006`, `FR-AI-007`, `FR-AI-008`, `FR-AI-010`, `FR-AI-012` |
| `GET /ai/drafts` | Draft history with provenance, evidence and status | `?feature, ?status, ?page → Page<Draft>` | — | `SCR-031` | `FR-AI-005`, `FR-AI-011` |
| `POST /ai/drafts/{id}/approve` | Human approval of a draft (the only path into a pack) | `{editedText?} → Draft` | — | `SCR-029`, `SCR-031` | `FR-XC-001` |
| `POST /ai/mapping-suggestions` | Propose column mappings with confidence and evidence | `{batch, columns[]} → {suggestions:[{source, target, confidence, evidence}]}` | — | `SCR-008` | `FR-IMP-008` |
| `GET /ai/mapping-suggestions` | Mapping Review Queue (acceptance applies to the next import, never in-run) | `?batch, ?page → Page<Suggestion>` | — | `SCR-008` | `FR-IMP-008` |
| `GET /ai/usage` | Local usage log: tokens, estimated cost, caps and outcomes | `?from, ?to → UsageReport` | — | `SCR-038` | `FR-AI-009` |

### 3.9 Operations, diagnostics, meta (10)

Area error profile: `ERR-SEC-006`, `ERR-ENG-001`…`010`.

| Endpoint | Purpose | Request → Response | Errors (beyond §2.3) | Screen(s) | FR(s) |
|---|---|---|---|---|---|
| `GET /jobs` | Job list/status (progress, ETA, terminal state) for the job drawer and polling [Later Phase / Planned] | `?state, ?page → Page<Job>` | — |  | `FR-XC-008` |
| `POST /jobs/{id}/cancel` | Cancel a running job where the job supports it [Later Phase / Planned] | `— → Job` | — |  | `FR-XC-008` |
| `GET /doctor` | Environment doctor: WebView2, paths, permissions, DB integrity, disk, profile mismatch | `— → DoctorReport` | — | `SCR-040` | `FR-XC-004` |
| `GET /health` | Liveness/version only (no data), for the shell and tests | `— → {status, appVersion, schemaVersion, uptimeMs}` | — | `SCR-040` | `FR-XC-004` |
| `POST /diagnostics` | Build the redacted diagnostics zip (metadata-only by default) | `{scope:{logs, machine, project}, redactionAck:true} → 202 Job → FileRef` | `ERR-SEC-006` (over 20 MB), `ERR-STO-002` | `SCR-040` | `FR-XC-004`, `FR-XC-005` |
| `GET /audit` | Filterable audit log with export [Later Phase / Planned] | `?actor, ?event, ?from, ?to, ?page → Page<AuditEntry>` | — | `SCR-040` | `FR-SET-012` |
| `GET /instrumentation` | Local job timings (import, rules, exports, cold start) surfaced in Diagnostics [Later Phase / Planned] | `— → {timings:[{stage, p50Ms, p95Ms, samples}]}` | — | `SCR-040` | `FR-XC-016` |
| `GET /help` | Help topics keyed by `SCR-nnn` (single-sourced with `22`) [Later Phase / Planned] | `?scr → {topics:[{scr, title, bodyMd, version}]}` | — | `SCR-040`, `SCR-042` | `FR-ONB-004`, `FR-ONB-007`, `FR-XC-014` |
| `POST /update-check` | Manual update check against the documented channel (disabled by default; never auto-installs) [Later Phase / Planned] | `{manual:true} → {status:'disabled'\|'up-to-date'\|'update-available', version?}` | — | `SCR-040` | `FR-XC-015` |
| `GET /meta/error-catalog` | The error-code catalog: code → user message + hint, keyed by the `26` families [Later Phase / Planned] | `?family, ?q → {items:[{code, slug, severity, message, hint, httpStatus, ownerDoc}]}` | — (pure read; the catalogue is generated from §5) | `SCR-041` | `FR-XC-006`, `FR-XC-012` |

## 4. Shared shapes

### 4.1 Notation

| Token | Meaning |
|---|---|
| `—` | No request body or parameters |
| `T[]` | Array of `T` |
| `Page<T>` | `{items: T[], total, page, pageSize, hasMore}` (§2.4) |
| `T\|null` | Nullable; `null` is a value, absence is not (§2.6) |
| `202 Job → X` | Returns `202` with a job id; the job's `result` is `X` when it succeeds (§2.7) |
| `Ack` | `{ok: true}` — the command did what its name says, nothing more |

### 4.2 Universal shapes

| Shape | Fields |
|---|---|
| `Finding` | `{code, slug, severity: info\|attention\|blocking, message, hint, details: [{path, value?, expected?}]}` — one shape for warnings and errors (`08` §16.2) |
| `Page<T>` | `{items, total, page, pageSize, hasMore}` (§2.4) |
| `Job` | `{jobId, type, state, stage, progress, etaSeconds\|null, startedAt, finishedAt\|null, cancelable, position\|null, result\|null, error: Finding\|null}`; `type`/`state` per `09` §8.1 |
| `FileRef` | `{path, bytes, sha256, createdFrom, generatedAt}` |
| `Ack` | `{ok: true}` |
| `VersionRef` | `{id, kind, version, createdAt, author, note, current: bool}` |
| `ProjectRef` | `{id, name, path, lastOpenedAt, lastPeriod, status, sample: bool}` |
| `PeriodState` | `{id, code, startDate, endDate, status: open\|closed, closedAt\|null, actualsLocked: bool}` |
| `SnapshotRef` | `{id, periodCode, reason, createdAt, packVersion\|null, sha256}` |
| `Health` | `{level: ok\|attention\|blocking, checks: [{name, status, detail}], warnings: Finding[]}` |
| `UiState` | `{tourDismissed, lastScreenByProject: {projectId: screenId}, stickyDisplay}` |
| `FilterContext` | `{scope, filter, sort, columns, materialityOverride\|null, updatedAt}` |

### 4.3 Domain shapes

Domain payloads are the entities of `03` plus the API-only wrapper fields; field-level truth lives in `03`
and this document never restates it. The mapping is:

| API shape | `03` entity/table | API-only additions |
|---|---|---|
| `Project` / `ProjectRef` | `DimProject`/`DimPeriod` (project rows) | `sample`, `health`, `path` |
| `BatchRef` | `FactImportBatch` | `links: {report, quarantine, archive}` |
| `Report` | `FactImportBatch` + check results (`IMP-001`…`032`) | `checks[]`, `timings`, `page` (sample rows) |
| `QuarantineRow` | quarantine table | `rowNumber`, `failingField`, `rawValues`, `reason` |
| `ScoreBreakdown` | `data_quality_score` (`CALC-050`) | per-check contribution list |
| `ProfileRef` / `ProfileBody` | `MappingProfile` version rows | `fingerprint`, `appliesTo` |
| `MasterRow` / `MasterTable` | `MasterVendorCategory`, `MasterRecurringCost`, `MasterApprovalThreshold`, owner tables | `version`, `stale` |
| `RuleState` | rule catalogue + enable/threshold rows (`06` §2.11) | `effectiveThreshold`, `default`, `degraded: bool` |
| `RunSummary` | rule-run header + summary counters | `raised`, `updated`, `suppressed`, `durationMs` |
| `BvaMatrix` / `BridgeSet` / `TrendSet` / `RankedVariances` / `ThreeWay` / `KpiCards` | calculation outputs (`05`) | `filters`, `warnings`, `stale`, `ofM` notes |
| `DrillRow` | `Fact*` rows behind one figure | `sourceFile`, `batchId`, `sheetOrLine` |
| `ExceptionRow` / `ExceptionDetail` | `FactExceptionEvent` + history | `ageDays`, `bucket`, `evidenceLinks`, `history[]` |
| `EffectivenessTable` | rule-effectiveness fields (`06` §9) | `closedShare`, `avgDaysToClose`, `lastTuning` |
| `VersionRef[]` (forecast) | `FactForecastVersion` | `locked`, `scenario`, `provenance` |
| `CompareSet` / `AccuracyReport` | forecast comparison/accuracy (`07` §8) | `signedError`, `absError`, `bias`, `mapeLite` |
| `PackRef` | pack/issuance tables | `version`, `status`, `files[]`, `snapshotId` |
| `IssuanceRef` | issuance register | `recipients[]`, `reissueOf`, `version` |
| `CommentaryRow` / `CommentaryRows` | commentary rows | `source: typed\|rule\|ai`, `approvedBy` |
| `Draft` | `AiDraft` + provenance | `model`, `promptVersion`, `generatedAt`, `status` |
| `UsageReport` | AI usage log | `tokensIn/out`, `estimatedCost`, `cap`, `remaining` |
| `DoctorReport` | diagnostics inputs | `checks[]`, `paths`, `permissions`, `webview2` |
| `AuditEntry` | audit log | `actor`, `event`, `object`, `before/after` summary |
| `ChecksSummary` | check-screen aggregate | `validation`, `exceptions`, `stale[]`, `storage` |
| `PreScan` | file metadata | `sha256`, `bytes`, `rows`, `sheets[]`, `limits`, `alreadyImported` |
| `MappingPreview` | mapping evaluation | `previewRows[]`, `unmapped[]`, `proposedProfileId` |

### 4.4 Job stages and result types

| Job type | Result shape | Stages (weights per `09` §8.1) |
|---|---|---|
| `import_validate` | `BatchRef` | pre-scan 5 · parse 40 · validate 35 · stage 15 · report 5 |
| `import_commit` | `CommitResult {batch, facts, quarantined, durationMs}` | commit 100 (single transaction) |
| `rule_run` | `RunSummary` | load 20 · evaluate 60 · persist 15 · analyse 5 |
| `forecast_generate` | `RunSummary` | load 20 · method 50 · write 25 · accuracy 5 |
| `export_xlsx` / `export_ppt` / `exports/ad-hoc` | `FileRef` | prepare 20 · build 60 · checks 15 · write 5 |
| `backup` / `restore` | `FileRef` / `ProjectRef` | copy 80 · manifest 10 · verify 10 |
| `migrate` | `MigrationNote {from, to, backupPath}` | backup 50 · migrate 50 |
| `ai_batch` | `Draft` | redact 20 · call 60 · validate 20 |

## 5. Error catalogue

### 5.1 Families (registered in `00_INDEX` §8)

| Family | Covers | In this document | Codes |
|---|---|---|---|
| `IMP` | Import, parsing and validation | §5.5 (catalogue rows) + §5.3 (aggregation) | `ERR-IMP-001`…`032` + 27 hardening slugs |
| `VAL` | Input and parameter validation outside import | §5.4 | `ERR-VAL-001`…`004` |
| `BVA` | Analysis, comparability and drill | §5.4 | `ERR-BVA-001`…`004` |
| `FC` | Forecast methods, versions and overrides | §5.4 | `ERR-FC-001`…`004` |
| `RUL` | Rule catalogue and runs | §5.4 | `ERR-RUL-001`…`003` |
| `STO` | Projects, periods, storage, versions, backup/restore | §5.4 | `ERR-STO-001`…`015` |
| `AI` | AI features and drafts | §5.4 | `ERR-AI-001`…`003` |
| `EXP` | Excel/CSV/PowerPoint/evidence-bundle generation | §5.3 (owned by `11` §12, `12` §10) | `ERR-EXP-001`…`018` |
| `SEC` | Key, TLS, diagnostics bundle, synced-folder guard | §5.3 (owned by `13` §14) | `ERR-SEC-001`…`008` |
| `ENG` | Environment, installation, lifecycle | §5.3 (owned by `15` §12) | `ERR-ENG-001`…`010` |
| `API` | Transport, session, pagination, contract | §2.3 (universal codes) | `ERR-API-001`…`007` |

### 5.2 Rules

| Rule | Detail |
|---|---|
| Slug is the join key | `import.<camelCase>` for `IMP`; `<object>.<condition>` for the rest (e.g. `period.closed`). Specs in `02`/`04`/`06` refer to slugs, never to numbers |
| Codes are stable | Allocated here, never reused, never renumbered; a retired code stays in the catalogue with `severity: retired` |
| One hint per code | The hint is the single next action (`08` §16.1); wording rules and banned words are owned by `08` §16 and enforced by the wording lint |
| Severity | `info` (“nothing is wrong”) / `attention` (warning, continues) / `blocking` (the action did not complete) |
| Families owned elsewhere | `EXP`, `SEC`, `ENG` and the `IMP` check rows keep their detail in their owning documents; this catalogue aggregates them by reference and surfaces them at `GET /meta/error-catalog` |
| No code without a test | A catalogued error path needs a fixture (§7) or a `TST-API-*` assertion; an untested code is a defect |
| Engine errors are typed | The engine raises typed errors carrying slug + hint (`17` §8); the API adds code + HTTP status. Routers never invent messages |

### 5.3 Aggregated from owning documents

| Family | Detail lives in | Aggregated here as |
|---|---|---|
| `IMP` | `04` §10 (32 catalogue checks) and `04` §7–§9 (hardening cases) | §5.5 tables, codes aligned 1:1 with `IMP-nnn` |
| `EXP` | `11` §12 (`ERR-EXP-001`…`011`), `12` §10 (`ERR-EXP-012`…`018`) | code + slug + severity + owner pointer; message/hint stay in the owners |
| `SEC` | `13` §14 (`ERR-SEC-001`…`008`) | as above; the AI endpoints and `POST /diagnostics` are the consumers |
| `ENG` | `15` §12 (`ERR-ENG-001`…`010`) | as above; `GET /doctor`, `POST /projects/{id}/open` and the shell surfaces consume them |

`GET /meta/error-catalog` is the runtime projection of this section: `{code, slug, severity, message, hint, httpStatus, ownerDoc}` — the same data the support flow reads (`23` §10).

### 5.4 Codes allocated by this document

| Code | HTTP | Trigger | Hint (the one action) |
|---|---|---|---|
| `ERR-VAL-001` | 400 | Typed confirmation missing or mismatched (project name, reopen reason) | *"Type the name exactly as shown to confirm."* |
| `ERR-VAL-002` | 400 | A required field for this action is missing | *"Complete the highlighted field and try again."* |
| `ERR-VAL-003` | 400 | Invalid enum/date/period/amount, or an unsupported filter/sort field | *"Reload the view; the app will use valid values."* |
| `ERR-VAL-004` | 400 | Value outside the allowed range (threshold, page size, materiality override) | *"Enter a value within the range shown next to the field."* |
| `ERR-BVA-001` | 404 | No data for the requested period/window | *"Import that period's files, or choose another window."* |
| `ERR-BVA-002` | 409 | Comparability guard: prior-year/TTM comparison unavailable | *"Show the view without the comparison, or import the missing period."* |
| `ERR-BVA-003` | 400 | Unsupported grain/rollup combination for this view | *"Choose a supported grain for this view."* |
| `ERR-BVA-004` | 409 | Drill target is ambiguous (more than one figure matches) | *"Pick the exact figure you want to drill into."* |
| `ERR-FC-001` | 409 | No eligible history for the chosen method | *"Choose another method, or extend the history."* |
| `ERR-FC-002` | 409 | Forecast version is locked | *"Copy the version to edit it."* |
| `ERR-FC-003` | 404 | Scenario or version not found | *"Pick an existing scenario from the list."* |
| `ERR-FC-004` | 400 | Manual override has no reason | *"Add a short reason for the override."* |
| `ERR-RUL-001` | 404 | Rule not found | *"Reload the rule catalogue."* |
| `ERR-RUL-002` | 409 | A rule run is already in progress | *"Wait for the current run to finish."* |
| `ERR-RUL-003` | 200 | Rule auto-disabled: required master data is missing (warning only, `06` §2.9) | *"Load the missing master data, then re-run."* |
| `ERR-STO-001` | 404 | Project not found | *"Open it from the project list."* |
| `ERR-STO-002` | 409 | Project is open in another window (single-instance mutex) | *"Bring that window forward, or close it and retry."* |
| `ERR-STO-003` | 400 | Project path invalid or not writable | *"Choose a folder under your user profile that you can write to."* |
| `ERR-STO-004` | 409 | A project already exists at that path | *"Open it instead, or choose another folder."* |
| `ERR-STO-005` | 404 | Period not found | *"Pick a period from the list."* |
| `ERR-STO-006` | 409 | Write attempted on a closed period | *"Reopen the period (audited) or use the open period."* |
| `ERR-STO-007` | 409 | Period is already closed | *"Continue with the next period."* |
| `ERR-STO-008` | 400 | Backup zip invalid or incompatible | *"Choose a backup made by this app; nothing was changed."* |
| `ERR-STO-009` | 409 | Restore target folder is not empty | *"Choose an empty folder; nothing was changed."* |
| `ERR-STO-010` | 404 | Versioned artefact or version not found | *"Pick a version from the history list."* |
| `ERR-STO-011` | 409 | Revert blocked by a dependent artefact | *"Revert the dependent item first; nothing was changed."* |
| `ERR-STO-012` | 404 | Archived source file is missing from the archive | *"Re-import the file; the rest of the project is unaffected."* |
| `ERR-STO-013` | 400 | Delete confirmation name mismatch | *"Type the project name exactly to confirm deletion."* |
| `ERR-STO-014` | 409 | Free space below the working threshold | *"Free space or archive raw files before continuing."* |
| `ERR-STO-015` | 400 | Sample-project conversion confirmation missing | *"Tick the conversion confirmation and retry."* |
| `ERR-AI-001` | 409 | AI is off or keyless | *"Turn AI on in Settings, or use the rule-based version."* |
| `ERR-AI-002` | 400 | Payload would exceed the redaction or token cap policy | *"Narrow the scope, or use the rule-based version."* |
| `ERR-AI-003` | 409 | Draft is already approved (immutable) | *"Create a new draft; approved text stays in history."* |

### 5.5 `IMP` — the validation catalogue (`04` §10, aligned 1:1 with `IMP-nnn`)

| Code | Check | Scope | On failure | Severity | Slug |
|---|---|---|---|---|---|
| `ERR-IMP-001` | File readable and format supported | F | Reject | High | `import.unreadableFile` |
| `ERR-IMP-002` | File size within the configured limit (`NFR`) | F | Explicit confirmation required, else reject | Medium | `import.fileTooLarge` |
| `ERR-IMP-003` | Row count within the configured limit (`NFR`) | F | Explicit confirmation required, else reject | Medium | `import.rowLimitExceeded` |
| `ERR-IMP-004` | Header row detected | F | User must pick the header row | High | `import.noHeaderDetected` |
| `ERR-IMP-005` | Required columns present after mapping | F | Reject, naming each missing column and the sheet | High | `import.missingRequiredColumns` |
| `ERR-IMP-006` | Duplicate column headers resolved | F | Block until renamed or ignored | High | `import.duplicateHeaders` |
| `ERR-IMP-007` | Expected sheet present (per profile) | F | User picks a sheet or cancels | High | `import.sheetNotFound` |
| `ERR-IMP-008` | Data range not empty | F | Reject (zero-activity override available) | High | `import.noDataRows` |
| `ERR-IMP-009` | Workbook not encrypted / not unreadable | F | Reject | High | `import.encryptedFile` |
| `ERR-IMP-010` | All required canonical fields mapped | F | Block until mapped | High | `import.mappingIncomplete` |
| `ERR-IMP-011` | Unmapped-row share below 90% | F | Reject with a mapping CTA and the unmapped share | High | `import.unmappedThreshold` |
| `ERR-IMP-012` | Dimension-string tokens parsed | R | Quarantine the row | Medium | `import.dimensionUnparsed` |
| `ERR-IMP-013` | Unknown/unmapped account codes | W | List distinct codes with row counts and a mapping CTA | Medium | `import.unknownAccounts` |
| `ERR-IMP-014` | Date values parsed | R | Quarantine the row | High | `import.dateUnparsed` |
| `ERR-IMP-015` | Ambiguous date formats confirmed | F | Stop and ask once; save the choice to the profile version | High | `import.ambiguousDate` |
| `ERR-IMP-016` | Numeric values parsed | R | Quarantine the row | High | `import.numberUnparsed` |
| `ERR-IMP-017` | Sign / `Cr`-`Dr` interpretation applied | R | Warn with the interpreted direction and the rule used | Low | `import.signRuleApplied` |
| `ERR-IMP-018` | Period resolved against the fiscal calendar | R | Quarantine the row | High | `import.periodNotInCalendar` |
| `ERR-IMP-019` | Dates inside the configured fiscal year | R | Quarantine the row | Medium | `import.dateOutsideFiscalYear` |
| `ERR-IMP-020` | Currency matches the project currency | R | Quarantine the row, naming the currencies found | High | `import.mixedCurrency` |
| `ERR-IMP-021` | Zero-amount rows noted | R | Keep the row; count and flag it (excluded from outlier rules) | Low | `import.zeroAmountRows` |
| `ERR-IMP-022` | Debit and credit not both populated | R | Warn; load as provided | Low | `import.bothDebitCredit` |
| `ERR-IMP-023` | Debit = credit within tolerance, per file/entity/period | F | Reject; show the imbalance amount and the top contributing rows | High | `import.balanceMismatch` |
| `ERR-IMP-024` | Row-count reconciliation (source = loaded + quarantined + rejected) | F | **Block commit** (internal invariant; a mismatch is a bug, never a user error) | High | `import.countMismatch` |
| `ERR-IMP-025` | Control-total variance within tolerance (when provided) | F | Fail the import or require a recorded acceptance (`§12`) | High | `import.controlTotalVariance` |
| `ERR-IMP-026` | Budget sum matches the approved total (when provided) | F | Fail or require a recorded acceptance | Medium | `import.approvedTotalVariance` |
| `ERR-IMP-027` | Within-file duplicate candidates reported | R | Report only — never auto-delete | Medium | `import.duplicateCandidates` |
| `ERR-IMP-028` | Cross-batch duplicate candidates reported | R | Pre-commit report; the user chooses skip / import anyway (recorded) / cancel | Medium | `import.crossBatchDuplicates` |
| `ERR-IMP-029` | File checksum not previously committed | F | Block: "already imported on <date> as batch <id>" | High | `import.alreadyImported` |
| `ERR-IMP-030` | Inactive cost centre usage noted | R | Warn and list (the exception engine also raises this; no double-reporting in the UI) | Low | `import.inactiveCostCentre` |
| `ERR-IMP-031` | Budget coverage matrix reported | F | Report the missing entity × account × period cells as a percentage, listable | Medium | `import.budgetCoverageGap` |
| `ERR-IMP-032` | Budget/forecast duplicate lines on the uniqueness key | R | Report; block the commit only when the duplicates conflict (same key, different amount) | Medium | `import.duplicateBudgetLines` |

### 5.6 `IMP` hardening slugs (report/quarantine findings, `04` §7–§9)

These carry **no numeric code**: they are findings in the validation report (counts, samples, raw values) and
follow the behaviour stated in `04`. They are catalogued so the UI and support can name them.

| Slug | Hardening case | Behaviour |
|---|---|---|
| `import.blankRowsIgnored` | X6 — Fully blank rows inside the data | All-mapped-columns-empty test |
| `import.blankTailTrimmed` | X5 — Blank trailing rows/columns | Trailing empty range detection |
| `import.currencySymbolStripped` | X17 — Currency symbols in numeric cells | Symbol match |
| `import.delimiterAmbiguous` | C6 — Ambiguous delimiter (e.g. single column with commas inside quotes) | Force an explicit user choice; offer a "single column" parse |
| `import.delimiterDetected` | C5 — Delimiters: comma, semicolon, tab, pipe | Auto-detected by field-count consistency across sample lines; **shown for confirmation** before parsing |
| `import.encodingDetected` | C1 — UTF-8 BOM | BOM stripped; encoding recorded |
| `import.encodingUnsupported` | C4 — Unknown/other encoding | Reject with the detected byte pattern and instruct the user to re-export as UTF-8 or Windows-1252 |
| `import.errorCell` | X12 — Error cells (#REF!, #DIV/0!, #N/A, #VALUE!) | Cell value match |
| `import.fileLocked` | X25 — File open/locked in Excel | Lock error on open |
| `import.formulaNoCachedValue` | X11 — Formula cells | Cell data type |
| `import.headerRowProposed` | X1 — Title/banner rows above the real header | Candidate header row scoring (density of non-empty, text-like, unique cells) |
| `import.hiddenSheetSkipped` | X7 — Hidden sheets | Sheet visibility flag |
| `import.ignoredColumns` | X24 — Very wide files (many unmapped columns) | Column count vs mapped count |
| `import.lineEndingsNormalised` | C9 — Mixed line endings (CRLF/LF/CR) | Normalised; count reported |
| `import.mergedDataCells` | X2 — Merged cells above or inside the header | Merge ranges in the header zone |
| `import.multiRowHeader` | X3 — Multi-row headers | Profile's multi_header_rows |
| `import.multilineField` | C8 — Quoted fields containing newlines | Parsed correctly; the row's source reference reports the logical row number and the physical line range |
| `import.parenthesesUnresolved` | X18 — Accounting parentheses negatives | Pattern match |
| `import.raggedRow` | C10 — Ragged rows (fewer/more fields than the header) | Fewer → missing values treated as empty and validated normally; more → extra fields quarantined as a structural warning naming the line |
| `import.rowsHiddenInExcel` | X23 — Excel "table" objects and autofilters over the range | Table metadata |
| `import.serialDatesConverted` | X14 — Dates stored as serials | Numeric in a date-mapped column |
| `import.sheetProtected` | X9 — Protected sheet (read allowed) | Workbook protection flags |
| `import.sheetSelected` | X8 — Multiple sheets | Sheet enumeration |
| `import.syncedPathWarning` | X26 — File on a OneDrive-synced path | Path inspection |
| `import.totalRowsIgnored` | X4 — Embedded Total / Subtotal rows | Label match in the key column(s) + a numeric row below a blank separator |
| `import.trailingDelimiter` | C11 — Trailing delimiter on every line | Detected and ignored; count reported |
| `import.whitespaceTrimmed` | C12 — Leading/trailing whitespace in headers and values | Trimmed for matching and parsing; original values preserved in quarantine payloads |

## 6. OpenAPI as the single source of truth

### 6.1 Artefacts

| Artefact | Path | Committed | Generated by |
|---|---|---|---|
| Spec builder | `app/api/openapi.py` | yes (hand-written) | — |
| Routers with response models | `app/api/routers/*.py` | yes (hand-written) | — |
| OpenAPI document | `app/api/openapi.json` | **yes** | `uv run python -m app.api.openapi --write` |
| TypeScript types | `ui/src/api/types.ts` | **yes** | the same command (`openapi-typescript`, pinned via `ADR-002`) |
| Contract fixtures | `tests/fixtures/api/**` | yes | hand-written, schema-validated in `scripts/check` |

### 6.2 Workflow

1. A route change starts in `26` (§3 row + any new code in §5) — spec first (`19` `P1`).
2. The router changes with a Pydantic response model; the handler stays thin (`09` §4.1).
3. `uv run python -m app.api.openapi --write` regenerates the document and the TS types in one step.
4. `scripts/check` runs `--check` (drift) + `tsc --noEmit` + the contract tests; any mismatch fails the build.
5. The regenerated files are committed with the change; the spec diff is reviewed like code.

### 6.3 Rules

| Rule | Detail |
|---|---|
| No hand-duplicated types | A TS interface for an API shape outside `ui/src/api/types.ts` fails review and `TST-API-08` |
| Stable operation ids | `area_verb_object` (e.g. `imports_commit_batch`); used by the generated client and the tests |
| Tags per area | The nine areas of §3 are the tags; the doc groups match the spec groups |
| No `deprecated` in v1 | A route is either current or removed (recorded in `26` + `20` + `CHANGELOG`) |
| Dev-only surfaces | `/docs`, `/redoc` and `/openapi.json` are **disabled in packaged builds**; the committed document is the reference (`TST-API-12`) |
| Token on everything | The generated spec declares the `X-FPA-Token` security scheme as global (`ADR-009`) |
| Version | `/api/v1` for the whole v1 lifetime; a breaking change is `/api/v2` plus an ADR, never an in-place edit |

	### 6.4 Breaking Changes and Version-Bump Policy

	| Rule | Policy |
	|---|---|
	| **Additive changes** | New optional fields in request/response envelopes or new endpoints under `/api/v1` are non-breaking and permitted without version bump. |
	| **Breaking changes** | Removing fields, changing field types, altering error code semantics, or removing endpoints requires a new namespace (`/api/v2`), an Architecture Decision Record (ADR), and a recorded migration entry in `docs/24_RELEASE_AND_VERSIONING_RUNBOOK.md`. |
	| **Unversioned duplicates** | Forbidden. Every route must be versioned under `/api/v1` (with no unversioned fallback aliases). |

## 7. Contract tests and fixtures

### 7.1 Layout

```
tests/fixtures/api/<area>/<route_slug>__<case>.json     # response fixtures (success + each error path)
tests/api/test_envelope.py                             # TST-API-01/02/16 over every route
tests/api/test_pagination_filters.py                   # TST-API-03/04
tests/api/test_auth_origin.py                          # TST-API-05/06
tests/api/test_openapi_drift.py                        # TST-API-07/08
tests/api/test_jobs_downloads.py                       # TST-API-10/11
tests/api/test_cli_parity.py                           # TST-API-13
```

| Rule | Detail |
|---|---|
| Coverage | Every route in §3 has at least one success fixture and one fixture per error code listed for it |
| Validation | Each fixture is validated against the generated schema at test time; a fixture that no longer matches fails |
| No live calls in unit tests | Entries are exercised through the FastAPI test client; engine work is stubbed only where `14` allows |
| Determinism | Fixtures contain no timestamps/ids that vary; where a value must vary it is asserted by shape, not equality |
| Wiring | `scripts/check` runs `pytest tests/api` plus the drift check; the gate transcript is the evidence (`16` §5.1) |

### 7.2 The 16 contract tests

| Test | Asserts |
|---|---|
| `TST-API-01` | The standard envelope on every endpoint (`{status, data, warnings[], errors[]}` shape) |
| `TST-API-02` | Error mapping: every engine error maps to a catalog code + hint; no stack traces, no secrets, no raw paths |
| `TST-API-03` | Pagination: caps honoured, stable ordering, `has_more` correct, page-size abuse rejected |
| `TST-API-04` | Filter grammar parity with the UI (same filter → same rows) |
| `TST-API-05` | Loopback-only binding and per-launch token required on every endpoint (`SEC-004`/`008`) |
| `TST-API-06` | CORS/origin closed to the app origin; DNS-rebinding style requests refused |
| `TST-API-07` | **OpenAPI drift:** the generated spec matches the handlers; a changed route without a spec change fails |
| `TST-API-08` | Generated TS types compile and are used by the UI (no hand-written duplicates) |
| `TST-API-09` | Response size budget: payloads over the documented limit fail the test (`09` §11) |
| `TST-API-10` | Long-running jobs: `202` + poll contract, progress, cancel, terminal states |
| `TST-API-11` | CSV/stream downloads: correct BOM/line endings, correct row counts, cancel works |
| `TST-API-12` | `doctor`/health endpoints expose only non-sensitive information |
| `TST-API-13` | **CLI smoke:** every command runs with `--json`; exit codes `0`/`2`/`3`/`4` behave as documented; output is deterministic |
| `TST-API-14` | The cross-artifact harness endpoints return exactly the engine values (§7) |
| `TST-API-15` | GET has no side effects; POST idempotency keys behave |
| `TST-API-16` | Validation failures return field-level pointers, not prose only |

## 8. Data-volume rule (Addon 2 §B.3)

| Rule | Contract obligation | Test |
|---|---|---|
| Server-side everything | Aggregation, filtering, sorting and paging run in DuckDB/SQLite; the browser never receives raw bulk rows (`09` §12) | `TST-PRF-*` at `--scale 250000` |
| Page bounds | Default 100, cap 200 for detail grids; over-cap requests are rejected (`ERR-API-004`) | `TST-API-03`, `TST-API-09` |
| Aggregations | One result set per view, column-capped, row-capped, with an explicit “of M” note | `TST-API-09` |
| Virtualisation | Every grid virtualises rows; drill lists paginate (`08`) | `TST-UI-*` + `TST-PRF-*` |
| Search | 50 items per group with counts and a link to the filtered view | `TST-API-09` |
| Payload budget | List/detail responses ≤ 2 MB; one analysis payload ≤ 5 MB; an over-budget response fails the test | `TST-API-09` |
| Exports | Always generated to a file server-side; never streamed through React state | `TST-API-11` |
| Budget source | The response-size budget above is the number `09` §12 requires tests to check | — |

## 9. Configuration exposure (Addon 2 §B.4)

### 9.1 The two layers

| Layer | Holds | Where it lives | Secrets |
|---|---|---|---|
| App-level (machine) | AI key/provider/model, theme, language, data directory, telemetry (always off) | `%LOCALAPPDATA%` settings store, DPAPI for the key (`13` §5) | **The only place a secret may live** |
| Project-level | Fiscal calendar, currency/units display, mappings, thresholds, master data, branding, rule enablement, UI state | Inside the project folder (`ADR-004`) | None, by rule |

| Rule | Detail |
|---|---|
| Precedence | A project value wins over an app default where both exist; the Settings response returns both plus the effective value so the UI can show “set here / inherited” |
| Portability | A project folder copied to another machine works, because nothing secret is in it; the AI key is re-entered once |
| Backups | Project zips therefore contain no secrets and need no sanitising (`13` §9, `24` §5) |
| Write path | Every setting has exactly one write route below; there is no second way to change a value |

### 9.2 Which routes touch which layer

| Route | Reads | Writes |
|---|---|---|
| `GET /settings` | both + effective values | — |
| `PUT /settings` | — | app or project, per `scope` in the body |
| `PUT`/`DELETE /settings/ai-key` | app | app (DPAPI write-only) |
| `GET`/`PUT /ui-state`, `GET`/`PUT /filters` | project (UI metadata) | project |
| `GET`/`PUT /rules/{id}`, `POST /rules/run` | project | project (versioned) |
| `GET`/`PUT /master-data/{kind}`, `POST /master-data/{kind}/import` | project | project (versioned) |
| `GET`/`PUT /mapping-profiles/{id}` | project | project (versioned) |
| `GET /doctor`, `POST /diagnostics` | machine + project (redacted) | — |
| `GET`/`POST /forecast/*`, `/analysis/*`, `/exceptions*`, `/packs/*`, `/issuance`, `/commentary` | project | project data (never settings) |

## 10. Reverse index: endpoint → FR → screen → test

This is the reverse of `20` §3 (`20` keeps FR → endpoint). Generated from the matrix; a route missing here is a defect.

| Endpoint | FR(s) | Screen(s) | Contract test(s) |
|---|---|---|---|
| `GET /bootstrap` | `FR-ONB-001`, `FR-ONB-006` | `SCR-001`, `SCR-002` | `TST-API-01` |
| `GET /projects` | `FR-PRJ-003` | `SCR-002` | `TST-API-01` |
| `POST /projects` | `FR-PRJ-002`, `FR-SET-005` | `SCR-002`, `SCR-003` | `TST-API-01` |
| `POST /projects/{id}/open` | `FR-PRJ-003`, `FR-PRJ-006`, `FR-PRJ-007` | `SCR-002` | `TST-API-01` |
| `GET /projects/{id}` | `FR-ONB-008`, `FR-PRJ-001` | `SCR-001` | `TST-API-01` |
| `DELETE /projects/{id}` | `FR-PRJ-012` | `SCR-002` | `TST-API-01` |
| `POST /projects/{id}/backup` | `FR-PRJ-008` | `SCR-039` | `TST-API-01` |
| `POST /projects/restore` | `FR-PRJ-009` | `SCR-002`, `SCR-039` | `TST-API-01` |
| `POST /projects/{id}/convert` | `FR-ONB-008` | `SCR-001` | `TST-API-01` |
| `GET /projects/{id}/storage` | `FR-PRJ-011`, `FR-SET-009` | `SCR-032`, `SCR-040` | `TST-API-01` |
| `POST /projects/{id}/archive-raw` | `FR-PRJ-011` | `SCR-032`, `SCR-040` | `TST-API-01` |
| `GET /projects/{id}/versions` | `FR-SET-011` | `SCR-033`, `SCR-035`, `SCR-037` | `TST-API-01` |
| `POST /projects/{id}/versions/{v}/revert` | `FR-SET-011` | `SCR-033`, `SCR-035`, `SCR-037` | `TST-API-01` |
| `GET /projects/{id}/periods` | `FR-PRJ-004` | `SCR-001`, `SCR-004` | `TST-API-01` |
| `POST /projects/{id}/periods` | `FR-PRJ-004` | `SCR-001`, `SCR-004` | `TST-API-01` |
| `POST /periods/{id}/close` | `FR-PRJ-005` | `SCR-001`, `SCR-004` | `TST-API-01` |
| `POST /periods/{id}/reopen` | `FR-PRJ-005` | `SCR-001`, `SCR-004` | `TST-API-01` |
| `GET /periods/{id}/snapshots` | `FR-PRJ-010` | `SCR-001`, `SCR-030` | `TST-API-01` |
| `GET /checks` | `FR-PRJ-001`, `FR-SET-010` | `SCR-001` | `TST-API-01` |
| `POST /imports/pre-scan` | `FR-ONB-003`, `FR-IMP-001`, `FR-IMP-002`, `FR-IMP-003`, `FR-IMP-007`, `FR-IMP-019` | `SCR-001`, `SCR-005`, `SCR-006`, `SCR-007`, `SCR-009` | `TST-API-01` |
| `POST /imports` | `FR-IMP-009`, `FR-IMP-010`, `FR-IMP-012`, `FR-IMP-014`, `FR-IMP-015`, `FR-IMP-027`, `FR-IMP-030`, `FR-IMP-031` | `SCR-005`, `SCR-007`, `SCR-008`, `SCR-009`, `SCR-010`, `SCR-014` | `TST-API-01` · `TST-PRF-02`, `TST-PRF-16` |
| `GET /imports` | `FR-IMP-023` | `SCR-011` | `TST-API-01` |
| `PUT /imports/{batch}/mapping` | `FR-IMP-004`, `FR-IMP-011`, `FR-IMP-026` | `SCR-008`, `SCR-011`, `SCR-033` | `TST-API-01` |
| `GET /imports/{batch}/report` | `FR-IMP-016`, `FR-IMP-017`, `FR-IMP-021` | `SCR-009`, `SCR-010`, `SCR-012` | `TST-API-01` |
| `GET /imports/{batch}/quarantine` | `FR-IMP-013` | `SCR-013` | `TST-API-01` |
| `POST /imports/{batch}/commit` | `FR-IMP-018`, `FR-IMP-020`, `FR-IMP-028` | `SCR-010` | `TST-API-01` |
| `POST /imports/{batch}/cancel` | `FR-IMP-030` | `SCR-009` | `TST-API-01` · `TST-PRF-02`, `TST-PRF-16` |
| `POST /imports/{batch}/void` | `FR-IMP-024` | `SCR-011` | `TST-API-01` |
| `GET /imports/{batch}/archive` | `FR-IMP-025` | `SCR-011`, `SCR-012` | `TST-API-01` |
| `GET /imports/{batch}/score` | `FR-IMP-022` | `SCR-010`, `SCR-014` | `TST-API-01` |
| `GET /mapping-profiles` | `FR-IMP-005`, `FR-IMP-006`, `FR-SET-002` | `SCR-008`, `SCR-033` | `TST-API-01` |
| `PUT /mapping-profiles/{id}` | `FR-IMP-005`, `FR-SET-002` | `SCR-008`, `SCR-033` | `TST-API-01` |
| `GET /master-data/{kind}` | `FR-SET-003` | `SCR-034` | `TST-API-01` |
| `PUT /master-data/{kind}` | `FR-SET-003` | `SCR-034` | `TST-API-01` |
| `POST /master-data/{kind}/import` | `FR-IMP-029` | `SCR-034` | `TST-API-01` |
| `GET /rules` | `FR-EXC-012`, `FR-EXC-014`, `FR-SET-004` | `SCR-014`, `SCR-023`, `SCR-034`, `SCR-035` | `TST-API-01` |
| `PUT /rules/{id}` | `FR-EXC-012`, `FR-SET-004` | `SCR-035` | `TST-API-01` |
| `POST /rules/run` | `FR-EXC-001`, `FR-EXC-003`, `FR-EXC-005`, `FR-EXC-020` | `SCR-014`, `SCR-023` | `TST-API-01` · `TST-PRF-07` |
| `GET /settings` | `FR-AI-001`, `FR-SET-001` | `SCR-032`, `SCR-038` | `TST-API-01` |
| `PUT /settings` | `FR-EXC-013`, `FR-PPT-006`, `FR-SET-006`, `FR-SET-007`, `FR-SET-008`, `FR-SET-009` | `SCR-003`, `SCR-032`, `SCR-035`, `SCR-036`, `SCR-037` | `TST-API-01` |
| `PUT /settings/ai-key` | `FR-AI-002` | `SCR-038` | `TST-API-01` |
| `DELETE /settings/ai-key` | `FR-AI-003` | `SCR-038` | `TST-API-01` |
| `PUT /ui-state` | `FR-ONB-002`, `FR-ONB-006` | `SCR-001`, `SCR-002`, `SCR-043` | `TST-API-01` |
| `GET /filters` | `FR-BVA-015` | Global (`08` §3.3 shell) | `TST-API-01` |
| `PUT /filters` | `FR-BVA-015` | Global (`08` §3.3 shell) | `TST-API-01` |
| `GET /analysis/bva` | `FR-BVA-001`, `FR-BVA-002`, `FR-BVA-003`, `FR-BVA-009`, `FR-BVA-013`, `FR-BVA-014`, `FR-BVA-016`, `FR-XC-010` | `SCR-015`, `SCR-022` | `TST-API-03`, `TST-API-09` · `TST-PRF-03` |
| `GET /analysis/bridge` | `FR-BVA-005` | `SCR-016` | `TST-API-01` |
| `GET /analysis/trends` | `FR-BVA-006` | `SCR-017` | `TST-API-01` |
| `GET /analysis/topn` | `FR-BVA-007` | `SCR-018` | `TST-API-01` |
| `GET /analysis/three-way` | `FR-BVA-008` | `SCR-019` | `TST-API-01` |
| `GET /analysis/kpis` | `FR-BVA-010` | `SCR-020` | `TST-API-01` |
| `GET /analysis/drill` | `FR-BVA-004` | `SCR-021` | `TST-API-01` |
| `GET /search` | `FR-BVA-012` | `SCR-022` | `TST-API-01` |
| `POST /exports/ad-hoc` | `FR-BVA-011` | `SCR-015`, `SCR-022` | `TST-API-01` |
| `GET /exceptions` | `FR-EXC-002`, `FR-EXC-009`, `FR-EXC-011`, `FR-EXC-019`, `FR-XC-010` | `SCR-023`, `SCR-024` | `TST-API-03`, `TST-API-09` |
| `GET /exceptions/{id}` | `FR-EXC-004` | `SCR-023` | `TST-API-01` |
| `PATCH /exceptions/{id}` | `FR-EXC-006`, `FR-EXC-007`, `FR-EXC-008` | `SCR-024`, `SCR-034` | `TST-API-01` |
| `POST /exceptions/bulk` | `FR-EXC-010` | `SCR-023` | `TST-API-01` |
| `GET /exceptions/effectiveness` | `FR-EXC-015` | `SCR-026` | `TST-API-01` |
| `POST /exceptions/{id}/evidence` | `FR-EXC-016`, `FR-XL-007` | `SCR-024`, `SCR-025` | `TST-API-01` |
| `GET /exceptions/export` | `FR-EXC-017`, `FR-EXC-018` | `SCR-023` | `TST-API-01` |
| `GET /forecast/versions` | `FR-FC-001`, `FR-FC-004` | `SCR-027` | `TST-API-01` |
| `POST /forecast/versions` | `FR-FC-003` | `SCR-027`, `SCR-028` | `TST-API-01` |
| `POST /forecast/run` | `FR-FC-002`, `FR-FC-005` | `SCR-027` | `TST-API-15` |
| `PATCH /forecast/cells` | `FR-FC-006` | `SCR-027` | `TST-API-01` |
| `POST /forecast/versions/{v}/lock` | `FR-FC-009` | `SCR-027`, `SCR-028` | `TST-API-01` |
| `GET /forecast/compare` | `FR-FC-009` | `SCR-027`, `SCR-028` | `TST-API-01` |
| `GET /forecast/accuracy` | `FR-FC-007`, `FR-FC-008` | `SCR-028` | `TST-API-01` |
| `POST /packs/excel` | `FR-XL-001`, `FR-XL-002`, `FR-XL-004`, `FR-XL-005`, `FR-XL-006`, `FR-XL-008`, `FR-XL-009` | `SCR-029` | `TST-API-14` |
| `POST /packs/deck` | `FR-PPT-001`, `FR-PPT-002`, `FR-PPT-003`, `FR-PPT-004`, `FR-PPT-005`, `FR-PPT-007`, `FR-PPT-008`, `FR-PPT-009` | `SCR-029`, `SCR-031`, `SCR-037` | `TST-API-01` · `TST-PRF-04` |
| `POST /packs/{id}/refresh` | `FR-XL-003` | `SCR-029` | `TST-API-01` |
| `GET /packs` | `FR-XL-003` | `SCR-029` | `TST-API-01` |
| `POST /issuance` | `FR-XC-002` | `SCR-030`, `SCR-031` | `TST-API-01` |
| `GET /issuance` | `FR-XC-003` | `SCR-030` | `TST-API-01` |
| `POST /issuance/{id}/reissue` | `FR-XC-003` | `SCR-030` | `TST-API-01` |
| `GET /commentary` | `FR-AI-013`, `FR-XC-001` | `SCR-029`, `SCR-031` | `TST-API-01` |
| `PUT /commentary` | `FR-XC-001` | `SCR-029`, `SCR-031` | `TST-API-01` |
| `POST /templates/export` | `FR-ONB-005` | `SCR-001`, `SCR-005` | `TST-API-01` |
| `POST /ai/test-connection` | `FR-AI-014` | `SCR-038` | `TST-API-01` |
| `POST /ai/drafts` | `FR-AI-004`, `FR-AI-006`, `FR-AI-007`, `FR-AI-008`, `FR-AI-010`, `FR-AI-012` | `SCR-008`, `SCR-023`, `SCR-029`, `SCR-031`, `SCR-038` | `TST-API-01` |
| `GET /ai/drafts` | `FR-AI-005`, `FR-AI-011` | `SCR-031` | `TST-API-01` |
| `POST /ai/drafts/{id}/approve` | `FR-XC-001` | `SCR-029`, `SCR-031` | `TST-API-01` |
| `POST /ai/mapping-suggestions` | `FR-IMP-008` | `SCR-008` | `TST-API-01` |
| `GET /ai/mapping-suggestions` | `FR-IMP-008` | `SCR-008` | `TST-API-01` |
| `GET /ai/usage` | `FR-AI-009` | `SCR-038` | `TST-API-01` |
| `GET /jobs` | `FR-XC-008` | Global (`08` §3.3 shell) | `TST-API-01` |
| `POST /jobs/{id}/cancel` | `FR-XC-008` | Global (`08` §3.3 shell) | `TST-API-01` |
| `GET /doctor` | `FR-XC-004` | `SCR-040` | `TST-API-12` |
| `GET /health` | `FR-XC-004` | `SCR-040` | `TST-API-12` |
| `POST /diagnostics` | `FR-XC-004`, `FR-XC-005` | `SCR-040` | `TST-API-12` · `TST-PRF-10` |
| `GET /audit` | `FR-SET-012` | `SCR-040` | `TST-API-01` |
| `GET /instrumentation` | `FR-XC-016` | `SCR-040` | `TST-API-01` · `TST-PRF-01` |
| `GET /help` | `FR-ONB-004`, `FR-ONB-007`, `FR-XC-014` | `SCR-040`, `SCR-042` | `TST-API-01` |
| `POST /update-check` | `FR-XC-015` | `SCR-040` | `TST-API-01` |
| `GET /meta/error-catalog` | `FR-XC-006`, `FR-XC-012` | `SCR-041` | `TST-API-02` |
## 11. CLI parity (the engine's second face)

| Rule | Detail |
|---|---|
| Same engine | The CLI and the API are both thin shells over `app/engine/` (`09` §4.1); neither owns a calculation |
| Same envelope | `--json` emits `{status, data, warnings[], errors[]}` with the same catalogue codes (`09` §5.3) |
| Stable exit codes | `0` success · `1` unexpected internal · `2` usage error · `3` project error · `4` import/validation rejection (`09` §5.3; `TST-API-13`) |
| Determinism | Identical inputs produce identical machine-readable output (no timestamps unless requested) |
| Non-interactive | The CLI never prompts; a decision becomes a required flag or a refusal with a next action |
| Command set | `import`, `validate`, `bva`, `exceptions`, `forecast`, `export-xlsx`, `export-ppt`, `doctor`, `migrate`, `report` (`09` §5.2) — a new command is a doc change here and in `09` |
| Locking | A mutating command refuses to run while the app holds the project's single-instance mutex (`ERR-STO-002`) |
| No API client | The CLI never calls the local HTTP API; both call the engine, so a broken API cannot break automation |

## 12. Obligations, change control and frozen constants

### 12.1 Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `20` | §3 keeps FR → endpoint and §2.3 the reference set; a rename updates both documents plus `CHANGELOG` in one change |
| `08` | Owns the message catalogue shape and wording (`08` §16); every `hint` in §5 must pass its wording lint |
| `14` | Owns the test IDs; §12.1 lists the 16 contract tests this document's §7 fixes. A new route adds its fixture rule |
| `09` | Keeps the job model (`§8.1`), the CLI (`§5.2`/`§5.3`), the data-volume rule (`§12`) and the engine-boundary rule (`§4.1`) that this contract exposes |
| `13` | Owns the transport posture (`§3`, `ADR-009`) and the `SEC` codes (`§14`); this document only requires them on every route |
| `10` | AI endpoints never return or log a key; `GET /ai/usage` mirrors the usage log, never the secret |
| `00_INDEX` | §8 registers the families; this document is where codes are allocated |
| `24` | Carries the API/schema versions in the release record; a route change is noted in the release notes when client-visible |
| `23` | Support reads §5 to explain a code; the diagnostics bundle contains the catalogue version |

### 12.2 Change control

| Change | Required in the same change |
|---|---|
| **Add a route** | An FR (or an existing FR's need), a consuming screen, a §3 row, a schema + generated types, a fixture, a `TST-API-*` reference, `CHANGELOG` |
| **Rename a route** | `26` §3 + §10, `20` §2.3 + §3, the affected tests, `CHANGELOG`; no alias is kept |
| **Remove a route** | Proof it has no FR consumer (`14` §12.3); removal recorded in both documents |
| **Add an error code** | A §5 row with slug, HTTP status and hint, a fixture, and the owning doc's detail if the family lives elsewhere |
| **Change a shape** | §4, the OpenAPI regeneration, the fixtures, the UI types; a breaking change is `/api/v2` + ADR |
| **Change a limit** | §13 + §8 and the test that enforces it (`TST-API-03`/`09`) |

### 12.3 Frozen constants and conventions

| Constant | Value | Source |
|---|---|---|
| Prefix | `/api/v1/` | §2.1 |
| Envelope | `{status, data, warnings[], errors[]}` | §2.2/§2.3 |
| Error object | `{code, slug, severity, message, hint, details[]}` | §2.3, `08` §16.2 |
| List payload | `{items, total, page, pageSize, hasMore}` | §2.4 |
| Page defaults | `page=1`, `pageSize=100`, cap `200` | §2.4, `09` §12 |
| Filter operators | `eq, ne, gt, gte, lt, lte, in, contains, between, isnull, notnull` | §2.5 |
| Money encoding | String decimal; `n/a` for undefined ratios | §2.6 |
| Job states | `queued, running, cancelling, succeeded, failed, cancelled` | §2.7, `09` §8.1 |
| Root job poll | `GET /jobs` | §2.7 |
| Response budgets | lists/details ≤ 2 MB; analysis ≤ 5 MB; search 50/group | §8 |
| Error families | `IMP, VAL, BVA, FC, RUL, STO, AI, EXP, SEC, ENG, API` | §5.1, `00_INDEX` §8 |
| Universal codes | `ERR-API-001`…`007` | §2.3 |
| Fixture root | `tests/fixtures/api/` | §7 |
| Regeneration command | `uv run python -m app.api.openapi --write` | §6 |
| Generated artefacts | `app/api/openapi.json`, `ui/src/api/types.ts` | §6 |
| Route count | 95 (nine areas) | §3, `20` §2.3 |
| Session token | `X-FPA-Token`, required on every route | §2.1, `ADR-009` |

### 12.4 Verification at a gate

| Check | Evidence |
|---|---|
| 95 routes match `20` §2.3 exactly | §3/§10 regeneration (`GATE-03-02`) |
| Every route has a fixture and a screen | §7 coverage report |
| OpenAPI drift check green | `scripts/check` transcript |
| Generated types compile | `tsc --noEmit` in the transcript |
| No orphan routes, no aliases | §10 + `20` §6.3 |
| Catalogue complete (no untested code) | §5 cross-check against the fixture list |
