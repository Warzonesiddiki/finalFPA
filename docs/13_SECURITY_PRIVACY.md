> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-XC-004`…`FR-XC-009`, `FR-XC-013`…`FR-XC-015`, `FR-PRJ-008`…`012`,
> `FR-AI-001`…`FR-AI-003`, `FR-AI-007`, `FR-AI-009`; Addon 1 §I (security, privacy, supply chain),
> Addon 1 §L (log/diagnostics budgets), Addon 3 §J (key rotation), Addon 4 §D.2 (no login), §K (gates)
> **TL;DR (≤ 15 lines):**
> - **Nothing leaves the machine** unless the user enables AI *and* clicks an AI action. No telemetry, no
>   crash upload, no background update check, no cloud storage (`SEC-001`…`SEC-006`).
> - The only outbound call is the user-configured OpenAI-compatible AI endpoint, over TLS with
>   verification **on and not user-disableable**, carrying a redacted, capped payload (`SEC-019`…`SEC-021`).
> - Secrets are one thing only — the AI API key — stored with **Windows DPAPI (per-user)**, never in a
>   project file, backup, log, export, diagnostics bundle, crash dump or the repo (`SEC-009`…`SEC-012`).
> - Data at rest is **plain local files** under `%LOCALAPPDATA%`. This document says so plainly and states
>   exactly what that does and does not protect (`SEC-022`…`SEC-024`).
> - Logs contain no amounts and no vendor names, rotate at ≤ 50 MB / 7 days, and stay local (`SEC-013`…`015`).
> - The diagnostics bundle is **metadata-only by default**; data rows require a labelled opt-in (`SEC-016`…`018`).
> - Imported text is hostile data, never instructions: prompt-injection defence is architectural and tested
>   with a planted malicious description (`SEC-025`…`027`).
> - Supply chain: pinned lockfile, license allow-list (no GPL/AGPL in shipped binaries), secret scan in
>   pre-commit + CI, SBOM-lite per release (`SEC-028`…`031`).
> - Every statement in this document has an ID, a mechanism and a planned test — no unverifiable claims,
>   and no security-theatre UI (the app never implies encryption it does not perform).
> - v1 has **no in-app login**; the privacy boundary is the Windows user account (`DEC-010`), stated to the
>   client rather than disguised as a feature.

# 13 — Security & Privacy

## 1. Purpose, scope and the honesty rule

This document owns the security, privacy and supply-chain contract of the product. It answers five
questions with verifiable statements rather than assurances:

1. **What data exists, and where does it live?** (§4, §9)
2. **What can leave the machine, and under whose control?** (§3, §8)
3. **How are secrets held, rotated and revoked?** (§5)
4. **What is written to logs, diagnostics and dumps?** (§6, §7)
5. **How do we know?** — every statement carries a mechanism and at least one test (§13, §14).

**The honesty rule (binding on all docs, code and UI copy).** No document, screen, or message may state or
imply a security property the product does not implement. If encryption is absent, say "plain files"; if a
call is possible, say where it goes; if a deletion is not a secure erase, say so. This rule exists because
the client is a finance team whose threat model includes auditors, and because a false assurance is worse
than a documented gap. `TST-SEC-19` audits user-visible strings against the claim list in §13.

**Scope.** The Windows 11 x64 desktop app, its local API (loopback only), the project and machine data
folders, exports, logs, diagnostics, crash dumps, the installer, the repository and the AI data path.

**Out of scope (stated, not ignored).** Multi-user servers, single sign-on, in-app authentication and
RBAC (`DEC-010`, `BL-004`/`BL-005`), client-side encryption of the analytic database, remote support
access, mobile, macOS/Linux, and network deployment.

## 2. Threat model

| # | Threat | Realistic here? | Consequence | Control (this document) |
|---|---|---|---|---|
| T1 | **Silent data egress** — the app phones home with client figures | Should be impossible | Total loss of trust; confidentiality breach | No network by default; socket-level test; no telemetry/update calls (`SEC-001`…`006`, `TST-SEC-01/02`) |
| T2 | **Credential theft from disk** — a copied config file yields the AI key | Yes if stored plainly | Cost abuse, possible data exposure | DPAPI per-user; no plaintext key anywhere (`SEC-009`…`012`) |
| T3 | **Diagnostics over-share** — user mails a bundle containing amounts or vendor names | Very likely | Confidential data leaves in a support email | Metadata-only default; labelled opt-in; redaction map; manifest preview (`SEC-016`…`018`) |
| T4 | **Log leakage** — amounts/vendor names/keys land in log files, then in a bundle | Likely by accident | Same as T3, continuously | Content policy + scrub filter + test that greps planted values (`SEC-013`…`015`) |
| T5 | **Prompt injection** — a transaction description tells the model to ignore its instructions | Certain to be attempted once tested | Wrong/misleading commentary; reputational damage | Data-not-instructions rule, delimiters, stripping, caps, schema validation, no tool use (`SEC-025`…`027`) |
| T6 | **Sync-folder corruption** — OneDrive/Dropbox touches live databases | Common in finance laptops | Corruption, silent data loss | `%LOCALAPPDATA%` default; sync detection blocks project storage; export guidance (`SEC-032`) |
| T7 | **Local file exposure** — another Windows user or a stolen laptop reads project data | Plausible | Confidentiality breach | Per-user ACLs on app folders; BitLocker/EFS guidance; honest "plain files" statement (`SEC-022`…`024`) |
| T8 | **Malicious import file** — formula/HTML/control characters, huge fields | Plausible | Corruption, weird rendering, injection | Treat as hostile: strip, cap, validate (`04`), never evaluate macros/formulas (`SEC-026`) |
| T9 | **Supply-chain compromise** — a dependency or a build step | Low but real | Arbitrary code in a finance product | Pinned lockfile, allow-list, SBOM-lite, vulnerability triage, no binary blobs (`SEC-028`…`031`) |
| T10 | **Secret in the repository** | Common failure mode of AI-assisted work | Key exposure, audit finding | `.gitignore` + pre-commit scan + CI gate + rotation runbook (`SEC-011`, `SEC-031`) |
| T11 | **Ransomware / compromised Windows account / physical theft without BitLocker / admin-level malware** | Possible | Full data access | **Explicitly not defended**; reliance on OS protections and backups; stated to the client (`SEC-024`) |
| T12 | **TLS interception by corporate proxy breaks AI calls** | Plausible in enterprises | Feature unavailable (fail-closed) | Verification never disabled; clear message; proxy support parked (`SEC-020`, `BL-029`) |

## 3. Local-only guarantees

Each statement below is a **claim with a mechanism and a verification**; §13 indexes them.

| ID | Statement | Mechanism | Verified by |
|---|---|---|---|
| `SEC-001` | With the network disabled, everything except the marked AI actions works end to end | No other outbound call exists in the codebase; a static check lists every `httpx`/socket call site and asserts they all belong to `engine/ai` | `TST-SEC-01` (offline walkthrough), `TST-SEC-02` (call-site inventory) |
| `SEC-002` | The app makes **no** background network calls — no telemetry, no crash upload, no usage ping, no ad/analytics SDK | Dependency allow-list excludes analytics/SDK packages; no scheduler starts a call; `Check for updates` is a manual action that opens a browser link | `TST-SEC-01`, `TST-SEC-03` |
| `SEC-003` | Crashing never uploads anything; crash dumps and logs are local files | Dumps written under `%APPDATA%`, never sent; the only way they leave is a user action | `TST-SEC-18` |
| `SEC-004` | No cloud storage, no remote database, no server component | Single process (`ADR-006`); DuckDB/SQLite files; the API binds `127.0.0.1` with a per-launch token and a random port | `TST-SEC-04` |
| `SEC-005` | Client files are read in place and copied into the project archive; nothing is uploaded or "synced" | Import pipeline is local; the raw archive is a local copy | `TST-SEC-01`, `TST-SEC-02` |
| `SEC-006` | The app never changes a source workbook | openpyxl is opened read-only for imports; no Office automation; write-back exists only in explicit exports with new filenames (`11`) | `TST-SEC-05` (source-file hash unchanged after import) |
| `SEC-007` | Client data never enters the repository, the installer, the sample project, or a test fixture | `.gitignore` covers project/data folders; the sample project is synthetic; fixtures are sanitised; `FR-XC-013` gate | `TST-SEC-17` (repo scan for client markers), go-live checklist (`28`) |
| `SEC-008` | Loopback API requires a per-launch token; no other local process can drive the engine without it | Token generated per launch, passed to the webview, required on every endpoint; CORS closed to the app origin | `TST-SEC-06` |

**Design note — why "no telemetry" is a test, not a promise.** The strongest guarantee for an offline-first
finance tool is an assertion that fails the build if a new call site appears outside `engine/ai`
(`SEC-001`/`SEC-002`). A policy sentence can be forgotten; an allow-list cannot.

## 4. Data locations, file handling and deletion

### 4.1 Where everything lives (authoritative tree)

| Path | Contents | Sensitivity | Leaves the machine? |
|---|---|---|---|
| `%LOCALAPPDATA%\FP&A Month-End Copilot\Projects\<project>\analytics.duckdb` | Analytic model (rebuildable from the archives) | Confidential | No |
| …`\state.sqlite` | Workflow authority: exceptions, statuses, commentary, pack issue, snapshots, audit trail | Confidential | No |
| …`\archives\` | Immutable raw source files (`09` §7.1) | Confidential | No |
| …`\snapshots\` | Immutable close/issue snapshots | Confidential | No |
| …`\exports\` (+ `.recycle\`) | Generated Excel/CSV/deck packs; overwritten files in `.recycle\` for 30 days (`11` §3.4) | Confidential | Only when the user shares a file |
| …`\logs\` | Project-scoped log files (rotated) | Metadata only by policy | Only inside a diagnostics bundle (`SEC-016`) |
| `%APPDATA%\FP&A Month-End Copilot\` | Machine settings, AI key (DPAPI), app logs, diagnostics, crash dumps | Mixed (one secret) | Bundle only, redacted, never the key |
| `%LOCALAPPDATA%\FP&A Month-End Copilot\Sample\` | Synthetic sample project | None | No |
| `%PROGRAMFILES%\FP&A Month-End Copilot\` | Installed binaries + bundled `templates/` | None | No |

**Folder ACLs.** On first run the app creates its folders with inheritance disabled and grants full control
to the current user and `SYSTEM`/`Administrators` only (`SEC-023`). This protects against *other standard
users* on the same machine; it does not protect against an administrator or malware running as the user.

### 4.2 File-handling rules

| Situation | Rule |
|---|---|
| Source workbooks | Opened read-only, never written; the file name, size, mtime and SHA-256 are recorded in `FactImportBatch`; a change between preview and commit is detected and blocked (`04`) |
| Interrupted write | Every writer writes `<name>.tmp` then renames atomically; a stale `.tmp` is cleared on next open and reported by `doctor` |
| Overwritten export | Moved to `.recycle\` (same-drive rename), purged after 30 days or by `doctor` (`11` §3.4) |
| Temporary extraction | Under `%TEMP%\fpa-<guid>\`, deleted at the end of the job and swept on next launch |
| Path length | Project paths are validated against the Windows 260-character limit (long-path aware) before any write (`09`) |
| Synced folders | Project storage on a OneDrive/Dropbox/Google-Drive-synced path is **blocked by default** with an explanation and a "use the default location" action; the user may override only through an explicit, recorded acknowledgement (`09` §7.2), which is written to the security events. Exports to a synced folder are allowed with a warning (`SEC-032`, `ADR-004`) |
| Executable content | Imported macro-enabled files (`.xlsm`) are read as data only; macros are never executed; external links and DDE are never followed |
| Antivirus interaction | Locked files surface as `ERR-EXP-002`-style messages, never as a raw OS error (`11` §12, `26`) |

### 4.3 Delete project, and what it really means

`FR-PRJ-012` requires typed confirmation; this document fixes the semantics:

1. The dialog states: project name, folder path, total size, database sizes, archive size, batch count,
   export count, and the exact sentence *"This deletes your working data for this project. Backups you made
   yourself, and files you exported, are not affected."*
2. Deletion removes the project folder tree (databases, raw archive, logs, exports, `.recycle`, snapshots).
   The machine-level settings and the AI key are **not** project data and are untouched.
3. A **pre-delete backup offer** appears in the same dialog (default checked): *"Save a backup zip first
   (recommended)"* → `FR-PRJ-008`.
4. The action is audit-logged (project id, timestamp, size, user) at machine level, so the deletion is
   visible after the project is gone (`SEC-033`).
5. **Not a secure erase.** On SSDs with wear-levelling and on NTFS with USN/journaling, deleted blocks may
   survive; Windows `Delete` is not a shredder and this document will not pretend otherwise. Guidance:
   rely on BitLocker/EFS plus physical control; for a hard requirement, the client's IT wipes the device.
   A "secure erase" feature is parked (`BL-030`) with the SSD caveat recorded there.
6. Verification: after deletion the path does not exist, the recent-projects list no longer offers it, and
   a re-scan finds no residual project files (`TST-SEC-15`).

## 5. Secrets and key management

### 5.1 The complete list of secrets

| Secret | Exists? | Where it lives | Never appears in |
|---|---|---|---|
| AI provider API key | Yes (only if AI is configured) | DPAPI-protected blob in `AppSetting` (`03` §5.7), machine scope = per Windows user | Project files, backups, exports, logs, diagnostics, crash dumps, repo, prompt payloads, UI after entry |
| Azure OpenAI endpoint URL / deployment name, model names | Not secret, but treated as confidential configuration | `AppSetting` (plain) | Repo, client-facing docs, diagnostics include the host only when the user opts in (default: `Azure OpenAI (host redacted)`) |
| Project data | Not a secret by definition, but confidential | §4.1 | Anywhere off-machine without a user action |
| Signing certificate (build-time) | Yes, in the release process | Build machine only (`24`, `15`) | Repo, installer, docs |

**Nothing else is a secret.** There is no license key, no login, no session token persisted (the API token
is per launch, in memory only), no database password (`SEC-034`).

### 5.2 Storage mechanics

| Aspect | Rule |
|---|---|
| API | Windows **DPAPI**, user scope (`CryptProtectData` with a fixed app entropy string), accessed through the Credential Manager abstraction so the value is retrievable only by the same Windows user on the same machine |
| Envelope | `AppSetting.value` stores `{"scheme":"dpapi-user","entropy":"fpa.v1","blob":"<base64>"}` — a self-describing envelope so a future scheme can be detected and rejected rather than misread |
| Write path | Key enters through a masked input, is encrypted immediately, and the cleartext reference is dropped; the input field is cleared after save (`FR-AI-002`) |
| Read path | Decrypted only inside `engine/ai` at call time, held only for the duration of the HTTP request, never logged or serialised |
| Display | The UI shows **configured / not configured**, the provider name, and the last-changed date. **No part of the key is ever displayed**, including the last characters, and there is no "reveal" action |
| Backup interaction | The project backup zip and the diagnostics bundle exclude `AppSetting` secret fields by construction (allow-list serializer, not a block-list) — `SEC-035` |
| Machine-change behaviour | A project folder is portable; the **key is not** — on a new machine the user re-enters it, and the app says so rather than failing obscurely |
| Failure | DPAPI unavailable or the blob unreadable → AI is disabled with `ERR-SEC-001`, everything else works |

### 5.3 Lifecycle: set → test → rotate → revoke → purge

| Step | Behaviour | Audit event (no key material) |
|---|---|---|
| Set | `FR-AI-002`; validation is syntactic; the key is never echoed back | `ai.key.set` (provider, host class, timestamp) |
| Test connection | `FR-AI-002` "Test connection": one minimal call; failure messages distinguish `401` (key rejected), DNS/TLS, timeout, rate limit — never echoes the request headers | `ai.key.test` (result) |
| Rotate | `FR-AI-003`: replacing the key **overwrites and purges** the old blob, clears any in-memory client, and is logged as a rotation | `ai.key.rotate` |
| Revoke | If the key is compromised or the person leaves: revoke it in the provider portal **first** (documented per provider in `23`), then remove it in Settings | `ai.key.remove` |
| Remove | "Remove key" deletes the blob; AI surfaces fall back to rule-based narrative (`FR-AI-013`), which is the default state anyway | `ai.key.remove` |
| Purge guarantee | After rotation/removal, a byte scan of all app files, the project folder, backups, exports, logs and diagnostics finds no key material or any prefix of it (`TST-SEC-11`) | — |

**Client-facing wording (used verbatim in Settings → AI):** *"Your key is stored by Windows for your
Windows account on this PC. It is never written into your project, your backups, your exports or our logs,
and it is never shown again after you save it. Removing it here deletes it from this PC; revoke it at your
provider as well if it may have been exposed."* (`SEC-036`)

### 5.4 Key-hygiene rules for the build and the repo

| Rule | Detail |
|---|---|
| `.gitignore` (minimum) | `.env`, `.env.*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `secrets.*`, `**/client-data/`, `**/*.duckdb`, `**/*.sqlite`, `%LOCALAPPDATA%` copies, `sample-data/local-*` |
| Pre-commit secret scan | `scripts/check-secrets` over staged files: provider key patterns (`sk-…`, 32+ char base64ish tokens adjacent to `key`/`token`/`secret`/`authorization`), private-key headers, connection strings with credentials; false positives resolved by an explicit allow-list file, never by disabling the scan (`SEC-031`) |
| CI | The same scan runs on every push and fails the build; a committed secret is rotated first, then removed (`10` §11, `24`) |
| Log/exception scrubbing | A logging filter replaces any value matching the key patterns or an exact match of the current key with `<redacted>` before the record is written; the filter is unit-tested with a fake key (`TST-SEC-10`) |
| No secrets in prompts | The prompt assembly never includes configuration values other than the model name; a test asserts the payload contains no key material (`TST-AI-05` extends to `TST-SEC-10`) |
| Installer/build | PyInstaller build needs no secrets; code-signing material is used only in the release step and never enters the workspace |

## 6. Logging policy

### 6.1 Locations, rotation and levels

| Aspect | Rule |
|---|---|
| Locations | `%APPDATA%\FP&A Month-End Copilot\logs\app.log` (machine/app) and `<project>\logs\project.log` (project context). Both local-only |
| Format | One record per line: `YYYY-MM-DDTHH:MM:SS+ZZ:ZZ LEVEL event_id message key=value …`. `event_id` is a stable slug (`imp.batch.start`), never free text from user data |
| Levels | `ERROR`, `WARN`, `INFO` (default), `DEBUG` (support-only, and the **same content policy applies** — debug may add counts and timings, never amounts/vendor names/secrets) |
| Rotation | Size **≤ 50 MB per file**, retain **7 days**, at most 10 files per location; rotation is by size *and* age; `doctor` reports and can purge (`NFR-011`) |
| Redaction filter | Installed on the root logger before any handler; scrubs secrets (`5.4`), absolute user paths (`C:\Users\<name>` → `%USER%`), and any string on the forbidden list (§6.2) |
| Crash behaviour | The unhandled-exception handler writes the traceback to the log, shows the plain-language dialog with "Copy details" (`FR-XC-006`), and writes the crash dump beside the logs. Dumps and logs are never uploaded (`SEC-003`) |
| Support mode | A Settings toggle raises the level to `DEBUG` for a session and shows a banner; it resets on exit and is recorded (`SEC-037`) |

### 6.2 Content policy — what logs may and may not contain

| May appear | Must not appear |
|---|---|
| Project id/name, entity codes, account codes, period codes, rule ids, error codes, message slugs | Financial amounts (any currency), balances, KPI values, variance values |
| Counts (rows, files, exceptions, batches), durations, byte sizes, percentages of progress | Vendor names, vendor ids, descriptions, invoice numbers, document numbers, person names |
| File names of **source imports** (needed for support) in `project.log` **only**; never in a diagnostics bundle without opt-in | Any part of the API key, tokens, headers, or full request/response bodies |
| Provider/model names, prompt ids and versions, token counts, cost estimates (the AI usage log is a product feature, `10` §10) | Prompt payload content or model output text (unless the user opts in for a specific AI troubleshooting session — a labelled action, `SEC-038`) |
| Technical identifiers: versions, ports (never tokens), paths as `%LOCALAPPDATA%/…` | Raw SQL containing literals from imported data (log the parameterised statement id only) |

**Why so strict.** The finance team will attach a log to a support email without thinking about it. The
policy is therefore designed so that the *default* artefact is safe to send, and the test is a grep for
planted values (`TST-SEC-09`): the fixture import contains a vendor named `ACME-HOSTILE-VENDOR` and an
amount `₹ 9,99,999.99`; after a full run — including an induced error — neither string appears anywhere in
`logs\`.

### 6.3 Audit trail vs. logs vs. security events (three different artefacts)

The word "audit" covers three artefacts with different audiences and different content rules. Confusing
them is how amounts end up in a log file, so the boundaries are fixed here:

| Artefact | What it is | Where | Contents | Retention | Owner |
|---|---|---|---|---|---|
| **Project audit trail** (`03` §5.7 `AuditLog`) | The product's record of *who changed what*: imports, mapping/threshold edits, exception statuses, commentary, issuance, settings (`FR-SET-011`, `FR-SET-012`) | `state.sqlite` in the project | Actor, timestamp, action code, object, `before`/`after` JSON — **values allowed** in the JSON (it is project data, and an audit that hides the old value is useless); action codes and text fields contain **no** amounts or vendor names (`03` §5.7) | Project lifetime (exports with the pack, `11` §4.8) | `03`, `02` |
| **Log files** (`FR-XC-007`) | Diagnostic trail for support: what the app did and how long it took | `%APPDATA%` + project `logs\` | IDs, codes, counts, timings — **no** amounts, vendor names, descriptions or secrets (§6.2) | ≤ 50 MB / 7 days | this document (§6.1/§6.2) |
| **Security events** | Security-relevant actions that must survive log rotation and, in one case, project deletion | `%APPDATA%\FP&A Month-End Copilot\security.log` (JSON-Lines, one object per line) | See the event list below — no key material, no amounts, no vendor names | 24 months, then rotated out (`doctor` reports) | this document |

**Security event list (complete):** `ai.key.set`, `ai.key.rotate`, `ai.key.remove`, `ai.key.test`
(result only), `diag.export` (bundle id, size, opt-in flag), `project.delete` (project hash, size, batch
count), `storage.syncRefused`, `perms.restrictFailed`, `storage.syncOverride`, `log.level.debugOn`/`debugOff`,
`ai.payload.flagged` (count only). Each line carries `occurred_at`, `event`, `actor` (Windows user),
`app_version`, and event-specific fields.

| ID | Statement |
|---|---|
| `SEC-048` | The project audit trail is append-only: no UI action deletes or edits an audit row, and the trail exports with the pack |
| `SEC-049` | Security events are recorded in a machine-level append-only file that survives log rotation and project deletion; it contains no key material, amounts or vendor names |

**Honesty note:** these files are ordinary local files under the user's own profile — a user with
administrator rights can delete them. Append-only means *the application offers no path to tamper*, not
that tampering is impossible (`SEC-024`). `doctor` reports the file's presence, size and last event so an
unexpected gap is visible (`15`).

## 7. Diagnostics bundle (`FR-XC-005`, Addon 1 §I)

### 7.1 Contents

| Group | Included by default | With explicit opt-in (labelled) |
|---|---|---|
| Versions | App version, build date, schema version, Python/runtime versions, dependency lock hash | — |
| Environment | Windows build, architecture, locale, DPI/scaling, installed fonts list, free disk space, RAM | — |
| Configuration | Provider/model names with the host **redacted** (`Azure OpenAI (host redacted)`), theme, data directory as `%LOCALAPPDATA%`, feature flags | the endpoint host itself |
| Data shape | Project name **hashed**, table names, **column headers**, row counts, file counts and sizes, batch ids | up to 200 sample rows per table, with a visible warning |
| Logs | Last 2 MB of the app log and the project log, tail-truncated | full logs (still scrubbed by §6) |
| Machine health | Migration state, integrity check summary (`doctor`), failed checks, last 20 error records with codes | — |
| Not included, ever | The AI key or any secret blob, the DuckDB/SQLite files, raw archives, exports, crash dumps (offered separately with their own warning) | — |

### 7.2 Redaction rules for the bundle

| Data | Transformation | Example |
|---|---|---|
| Windows user name / paths | `C:\Users\asha\…` → `%USER%\…`; machine name → `%MACHINE%` | — |
| Project name | SHA-256 prefix + an alias the user recognises in the UI preview (`Project-3f9a`) | — |
| Vendor names, descriptions, document numbers | Column **headers** are kept (they are structure); values exist only under opt-in, and then are masked to `V-###`, `D-###`, `DOC-###` with a stable mapping recorded in the bundle | `Ironclad Traders` → `V-014` |
| Accountant/owner names | Replaced with `OWNER-###` | — |
| Amounts (opt-in only) | One order of magnitude bucket per column (`₹ ~10^5`) unless the user ticks *"include exact values"*, which is off by default and separately labelled | — |
| Entity/account/cost-centre codes | **Kept** — they are structure, not identities (`DEC-027`) | `IN01`, `400120` |
| Paths in exports | Kept as `%PROJECT%\exports\…` | — |

### 7.3 Mechanics

1. Export runs in a background job with progress; **size cap `NFR-010` = 20 MB** (`ERR-SEC-006` if exceeded,
   with the offending group named).
2. Before writing, the UI shows a **manifest preview** — the exact file list and the sentence *"This bundle
   contains no amounts and no vendor names"* or, with opt-in, *"This bundle contains data rows (N rows) —
   review it before sending."*
3. The zip contains `manifest.json`, `redaction.json` (the mapping used, local to the bundle),
   `logs/`, `config/`, `health/` and, under opt-in, `data/`.
4. `manifest.json` carries the SHA-256 of every member and of the zip itself, plus the app/schema versions
   and whether opt-in data was included:

```json
{
  "schema": "fpa.diagnostics.v1",
  "created_at": "2026-10-01T14:22:31+05:30",
  "app_version": "0.9.0",
  "schema_version": "1",
  "platform": "Windows-11-10.0.22631-x64",
  "data_rows_included": false,
  "exact_values_included": false,
  "redactions_applied": ["user_paths", "machine_name", "vendor_names", "owner_names", "project_name"],
  "content_policy": "fpa.log.policy.v1",
  "members": [
    {"path": "logs/app.log", "bytes": 204800, "sha256": "3f9c…"},
    {"path": "config/settings.json", "bytes": 4096, "sha256": "a71b…"},
    {"path": "health/doctor.json", "bytes": 8192, "sha256": "9d0e…"}
  ],
  "zip_sha256": "c4e1…"
}
```

5. Sending is a **user action in their own mail client**; the app never sends anything (`SEC-003`).
6. The bundle is written to the user's chosen folder (default Desktop) and its location is shown with a
   "Show in folder" action; the About screen records the last export date (`FR-XC-004`).

## 8. Network posture and the AI data path

### 8.1 The complete outbound inventory

| # | Outbound action | Trigger | Destination | Payload |
|---|---|---|---|---|
| 1 | AI completion request | **User clicks an AI action** (draft commentary, mapping suggestion, grouping, follow-up draft) | The single configured OpenAI-compatible endpoint (Azure OpenAI preferred) | Redacted, capped, filtered context for that one feature (`10` §6) |
| 2 | "Check for updates" | Manual menu action | A documented HTTPS release-info URL | None (a GET with no identifiers); result shown in-app; **no auto-download** (`FR-XC-015`) |
| 3 | Provider "test connection" | Manual action in Settings | The configured endpoint | A minimal request with no client data |

There is no other outbound call in the product — this list is exhaustive by design, and `SEC-001`/`SEC-002`
enforce it statically (`TST-SEC-02`).

### 8.2 AI call requirements (enforced in `engine/ai`)

| Requirement | Rule |
|---|---|
| Opt-in | AI is off until a key is configured and the toggle is on (`FR-AI-001`); keyless mode is the default demo path (`FR-AI-013`) |
| TLS | Verification is **on** and cannot be disabled from Settings; no custom CA in v1 (`BL-029`) → corporate TLS interception yields `ERR-SEC-004` with a plain-language hint |
| Redaction first | The payload is assembled from the redacted data block (`10` §6, `DEC-027`); masking of vendor names/descriptions is on by default |
| Minimum data | Only the aggregate/driver context needed for the chosen feature; never whole tables; per-feature field caps (`10`) |
| Caps | Per-call and monthly token/cost caps with a hard stop (`FR-AI-009`) |
| Provenance | Every stored draft records provider, model, prompt id/version, timestamps, input scope, redaction and truncation flags (`10` §11) |
| Non-authority | AI output can never alter a number, a rule verdict, a mapping, or a data record; it produces draft text that a human approves (`DEC-*`, `FR-AI-*`) |
| Failure | Timeouts, `401`, rate limits and blocked networks produce a readable message and fall back to rule-based narrative; the user's work is never blocked |

### 8.3 What the client is told (plain language, verbatim)

*"The app works completely offline. Nothing is sent anywhere unless you switch AI on, add your own key,
and press an AI button — in that case, a small redacted summary goes to the AI service you chose. The app
never sends your files, your data or your key anywhere else."* (`SEC-039`, used in `29` and `22`.)

## 9. Data at rest, backups and the encryption stance

### 9.1 Statement of fact

| Question | Answer (v1) |
|---|---|
| Is the analytic database encrypted? | **No.** `analytics.duckdb` and `state.sqlite` are standard local files |
| Is a project backup zip encrypted? | **No.** A plain `.zip` with a manifest |
| Is anything encrypted? | **Yes — only the AI key blob, via Windows DPAPI**, plus whatever the OS provides (BitLocker/EFS) |
| Why? | Recorded as `DEC-030`. The app is a single-user tool with no password to manage. Application-level encryption with a user-chosen password adds key-recovery risk (a forgotten password = the whole month's work), while full-disk encryption is the correct control for a stolen device and is already standard on managed Windows 11 laptops. Precedent: the client's own Excel files are also plain files |
| Residual risk | Another local user (subject to ACLs), an administrator, malware running as the user, a decommissioned disk, or a backup file copied elsewhere |
| Recommended client controls | BitLocker with TPM, EFS if policy requires per-file encryption, device encryption in Intune/managed policy, no personal devices, physical control (`21`, `29`) |

### 9.2 Backups (`FR-PRJ-008`/`009`)

| Aspect | Rule |
|---|---|
| Contents | Databases, raw archive, snapshots, `ProjectSetting`, manifest with schema/app version — **secrets excluded by construction** (allow-list serializer, `SEC-035`) |
| Format | `<Project>_<YYYY-MM-DD-HHMM>.zip`, plain; manifest `fpa.backup.v1` with member hashes |
| Restore | Validates the manifest, hashes and schema, restores into an empty folder, runs migrations forward, never merges into an existing project |
| Guidance | The UI states plainly: *"This backup is a normal zip file — anyone who can open the file can read the project. Store it somewhere protected, or let Windows encryption (BitLocker) protect the disk."* (`SEC-040`) |
| Location | Any local/network folder the user chooses; a synced folder is allowed **with a warning** (it is a snapshot, not live databases) |
| Retention | User-owned; the app never deletes a backup; `doctor` lists backups it can see beside the project |

### 9.3 Export destinations

Exports inherit the destination's protections, which the app cannot know; the export dialog therefore shows
the resolved path and, when it detects a synced folder (`SEC-032`), a one-line notice: *"This folder syncs
to the cloud. The pack will be uploaded by <sync provider>."* — a warning, not a block, because sharing the
pack is the point of the pack.

## 10. Privacy and personal data

### 10.1 What personal data the product touches

| Data class | Present? | Examples | Handling |
|---|---|---|---|
| Financial records | Yes | Journals, budgets, invoices | Local only; never uploaded; exported only by the user |
| Business contact data in free text | Possibly | Vendor names, invoice text, description fields | Treated as hostile input (§11); masked before any AI call (`DEC-027`); never in logs |
| Employee/person names | Possibly, incidentally | Owner fields, created-by fields in imported data, approvals in the source systems | Kept locally as imported; masked in AI payloads under the *person name* mask; `OWNER-###` in diagnostics opt-in data |
| System identifiers | Yes | Windows user name, machine name, paths | Local; redacted in diagnostics; never uploaded |
| The AI API key | Yes, if configured | — | DPAPI-protected, never displayed (§5) |
| Usage/telemetry | **No** | — | No telemetry exists (`SEC-002`) |

`SEC-041` — the product's operator (the consultant) receives **no** client data at any point: not during
build, not during support (a diagnostics bundle travels through the client's own mail client and the client
can inspect it first), and not through the AI path (the client's own key, endpoint and contract).

### 10.2 Retention

| Data | Retention |
|---|---|
| Project data | Kept until the user deletes the project (`FR-PRJ-012`) or removes the folder |
| Raw archives | Kept with the project; `doctor`/storage screen reports their size and offers a "compact archives" action for batches already merged |
| Exports and backups | User-owned; the app never auto-deletes them |
| Logs | 7 days / ≤ 50 MB, automatic |
| Crash dumps | Keep the last 5; older removed automatically; offer "delete all" |
| Project audit trail | Project lifetime; exported with the pack (`11` §4.8); not deleted separately |
| Security events (`security.log`) | 24 months, then rotated out; survives project deletion (`SEC-049`) |
| Diagnostics bundles | Written to the user's folder; never re-collected |
| AI usage log | Kept with the project (it is product data, `10` §10); contains counts/costs, not payloads |

`SEC-042` — **no retention surprise:** every automatic deletion (log rotation, dump pruning, `.recycle`
purge at 30 days) is stated in `22`, surfaced in the storage screen, and logged.

### 10.3 Roles and the plain-language privacy note

The client is the data controller; the consultant ships a tool that runs on the client's machine. The
client-facing text (used in `29`, `22` §Help and the About screen) is owned here and must not be rewritten
downstream:

> **Where your data lives and goes**
> Everything you import, calculate and export stays on this PC, in your Windows user folder. The app works
> with the network switched off. There is no account, no cloud copy and no usage tracking.
> If you choose to turn on AI features, you add your own key from your AI provider. Only then, when you
> press an AI button, does a small redacted summary go to that provider — never your files, never the whole
> database, and never your key. If you never turn AI on, the app never connects to anything.
> Deleting a project removes its working files from this PC. Backups you created and files you exported
> stay where you put them. This is not a secure erase; ask IT to enable BitLocker if the laptop could be
> lost or stolen.
> `SEC-043`

## 11. Hostile input and prompt-injection defence (Addon 1 §I)

### 11.1 The rule

**Imported content is data, never instructions.** A transaction description, vendor name, comment or
filename is untrusted text that may contain prompt-injection payloads. Defence is architectural, in our
code, and independent of provider behaviour (`09`).

| Layer | Control | Statement |
|---|---|---|
| Ingest | HTML tags, control characters, zero-width and bidirectional characters stripped; field lengths capped (description ≤ 500 chars after cleaning, vendor ≤ 200); formula and macro content never evaluated | `SEC-025` |
| Prompt assembly | Data is wrapped in an explicitly delimited block (`<data>…</data>`) with an escaped closing sequence; the system prompt states that content inside the block is data and must never be obeyed as an instruction; instructions never come from data | `SEC-026` |
| Model surface | Exactly four versioned prompts (`10` §4), no user-supplied system prompts, no tool/function calling, no browsing, no code execution | `SEC-027` |
| Output | Strict JSON schema validation; one retry; on failure the rule-based fallback is used; AI text is stored as a draft and can only become a deliverable when a human approves it (`FR-PPT-008`, `FR-XC-001`) | `SEC-027` |
| Authority | AI output never changes a figure, a rule verdict, a mapping or a record; the numeric authority stays in the engine (`10` §1) | `SEC-027` |
| Detection | The engine flags payload-shaped text (long imperative phrases, "ignore previous instructions", role-play markers, base64 blobs) and **excludes it from the AI payload** while keeping the row in the analysis; the flag is visible in the AI log and never blocks the month-end flow | `SEC-044` |
| Evidence | The fixture set in `14` plants a malicious description in the sample data and asserts: the payload excludes it, the model output validates or falls back, no data was changed, and the flag is recorded | `TST-SEC-14` |

### 11.2 Why not "just trust the model"

Provider-side mitigations change without notice and cannot be audited by the client. Owning the boundary
(delimit, strip, cap, validate, never act) keeps the guarantee inside a codebase the client can inspect and
a repo the consultant maintains — and it keeps the claim honest when the model changes.

## 12. Supply chain and repository hygiene (Addon 1 §I, kickoff §12)

| ID | Statement | Mechanism |
|---|---|---|
| `SEC-028` | Dependencies are pinned and reproducible | `requirements.txt` (ranges) + `requirements.lock` (hash-pinned) committed; PyInstaller build uses the lock; a fresh clone + documented bootstrap installs the same versions (`09` §13, `17`) |
| `SEC-029` | No GPL/AGPL in shipped binaries; licenses are declared | Dependency allow-list (MIT, BSD, Apache-2.0, PSF, ISC); a license scan over the resolved lock runs in `scripts/check`; `THIRD_PARTY_LICENSES.txt` is generated at release and shipped in the installer manifest; GPL/AGPL requires an ADR and is default-denied |
| `SEC-030` | Vulnerabilities are triaged on a clock | `pip-audit` (or equivalent, pinned) run at each release and monthly; strategy: critical/high exploited-in-wild → patch release within 7 days; critical not exploited → next scheduled release ≤ 30 days; medium/low → next release; every finding and decision recorded in `24` |
| `SEC-031` | A secret can never be committed or shipped | `.gitignore` (§5.4) + pre-commit scan + CI scan (fails the build) + release-time scan of the installer payload; the scan patterns and the allow-list file are versioned; a found secret triggers rotation first (`24`) and an incident note |
| `SEC-045` | No binary blobs or vendored code enter the repo without review | Review rule in `17`: any binary > 1 MB or any vendored source requires a note in `THIRD_PARTY_LICENSES.txt` and a `CHANGELOG` entry |
| `SEC-046` | The build is reproducible from a fresh clone | `scripts/bootstrap`, `scripts/check`, and the fresh-clone test are requirements at every phase gate (Addon 3 §G.2, `16`) |
| `SEC-047` | SBOM-lite per release | `sbom/py-<app-version>.txt` = `pip freeze` snapshot of the built environment, attached to the release (`24`), not committed as a moving target |

## 13. Verification matrix and statement index

### 13.1 Statement index (the complete, auditable list)

Each statement exists in full — with its mechanism — in the section named in the *Mechanism* column. This
index is the enumeration of record: a `SEC-nnn` that is not here, or that has no test, is a defect.

| ID | Statement (one line) | Mechanism | Test(s) |
|---|---|---|---|
| `SEC-001` | Everything except the marked AI actions works with the network off | No other outbound call site exists | `TST-SEC-01`, `02` |
| `SEC-002` | No background network calls: no telemetry, crash upload or auto-update | Dependency allow-list + call-site inventory + update check is manual | `TST-SEC-01`, `02`, `03` |
| `SEC-003` | Crashes upload nothing; dumps and logs are local files | Local dump writer; no upload path | `TST-SEC-03`, `18` |
| `SEC-004` | No cloud storage, remote database or server component | Single process; loopback-only API | `TST-SEC-04` |
| `SEC-005` | Source files are read in place and archived locally; nothing is uploaded | Local import pipeline + raw archive | `TST-SEC-01` |
| `SEC-006` | The app never modifies a source workbook | Read-only open; no Office automation; exports use new names | `TST-SEC-05` |
| `SEC-007` | Client data never enters the repo, installer, sample project or fixtures | `.gitignore`, synthetic sample, fixture rule, go-live check | `TST-SEC-17` |
| `SEC-008` | The loopback API needs the per-launch token; no other process can drive it | Random port + token per launch, origin-closed CORS | `TST-SEC-04` |
| `SEC-009` | The AI key is stored only as a DPAPI (per-user) blob — never plaintext | DPAPI envelope in `AppSetting` | `TST-SEC-08` |
| `SEC-010` | The key is never displayed again after entry, not even partially | Write-only field; UI shows status + date | `TST-SEC-06`, `10` |
| `SEC-011` | A secret cannot be committed or shipped | `.gitignore` + pre-commit + CI + release scan | `TST-SEC-08`, `10`, `17` |
| `SEC-012` | Rotation/removal purges the old value from config and memory | Overwrite blob, drop client, then byte scan | `TST-SEC-08`, `10`, `11` |
| `SEC-013` | Logs live under `%APPDATA%`, rotate at ≤ 50 MB / 7 days, one stable line format | Size+age rotation; fixed record format | `TST-SEC-09` |
| `SEC-014` | Logs carry IDs, codes, counts and timings — never amounts, vendor names, descriptions or secrets | Content policy + redaction filter before handlers | `TST-SEC-09` |
| `SEC-015` | The default log is safe to attach to a support email | Policy + path/name scrubbing | `TST-SEC-09` |
| `SEC-016` | Diagnostics are metadata-only by default; data rows are a labelled opt-in | Bundle builder allow-list; warning before export | `TST-SEC-12`, `13` |
| `SEC-017` | Bundle redaction: user paths, machine name, vendor/owner names, project name; codes kept | Redaction map + `redaction.json` | `TST-SEC-12`, `13` |
| `SEC-018` | The bundle has a hashed manifest, a preview, and leaves only by the user's own action | Manifest + UI preview; no send path | `TST-SEC-12` |
| `SEC-019` | The outbound inventory is exhaustive: AI call, manual update check, test connection | Static inventory test; any new call site fails the build | `TST-SEC-02` |
| `SEC-020` | TLS verification is on and cannot be disabled from the app | httpx default context, no override in config | `TST-SEC-21` |
| `SEC-021` | AI payloads are redacted, minimal, capped and never authoritative | Redaction + field caps + schema validation + human approval | `TST-SEC-21`, `TST-AI-05` |
| `SEC-022` | Data at rest is plain local files — stated plainly, not implied encrypted | This document + UI copy audit | `TST-SEC-19` |
| `SEC-023` | App folders grant access only to the current user, `SYSTEM` and admins | ACLs set on first run | `TST-SEC-07` |
| `SEC-024` | Threats we do not defend (admin malware, stolen unlocked device, ransomware) are stated to the client | Threat model §2 + client pack | `TST-SEC-19` |
| `SEC-025` | Imported text is stripped of HTML/control characters and length-capped before use | Ingest sanitiser | `TST-SEC-14` |
| `SEC-026` | Prompt data sits in delimited blocks; the system prompt forbids obeying it | Prompt assembly + template | `TST-SEC-14` |
| `SEC-027` | Four fixed prompts, no tools, schema-validated output, human approval, no data mutation | `engine/ai` design + validation + approval gates | `TST-SEC-14` |
| `SEC-028` | Dependencies are pinned and reproducible from a fresh clone | `requirements.lock` + bootstrap script + fresh-clone gate | `TST-SEC-17`, `20` |
| `SEC-029` | No GPL/AGPL in shipped binaries; licenses declared and shipped | Allow-list + license scan + `THIRD_PARTY_LICENSES.txt` | `TST-SEC-20` |
| `SEC-030` | Vulnerabilities are triaged on a documented clock | Pinned audit tool + release/monthly run + policy | `TST-SEC-20` |
| `SEC-031` | Committed or shipped secrets fail the pipeline | Pre-commit + CI + release scan; rotation first | `TST-SEC-17` |
| `SEC-032` | Project storage in a synced folder is blocked by default (override only via recorded acknowledgement); exports there warn | Sync detection + `ERR-SEC-007` + `storage.syncOverride` event | `TST-SEC-16` |
| `SEC-033` | Project deletion is audit-logged at machine level | Machine-level audit row | `TST-SEC-15` |
| `SEC-034` | There is no login, license key, database password or persisted session token | Design: the only secret is the AI key | `TST-SEC-19` |
| `SEC-035` | Backups and diagnostics exclude secrets **by construction** (allow-list serialiser) | Serialiser allow-list | `TST-SEC-10`, `11` |
| `SEC-036` | Key-storage wording is fixed and accurate in Settings | Verbatim copy §5.3 | `TST-SEC-06`, `19` |
| `SEC-037` | Support DEBUG level is session-scoped, banner-announced, logged and auto-reset | Settings toggle behaviour | `TST-SEC-18` |
| `SEC-038` | AI payload/output text is never logged unless a labelled troubleshooting opt-in is used | Logging policy for AI content | `TST-SEC-13` |
| `SEC-039` | "Nothing leaves unless you switch AI on" is the client-facing statement | Copy §8.3, used in `22`/`29` | `TST-SEC-19` |
| `SEC-040` | Backups are plain zips and are described as such | UI copy + docs | `TST-SEC-19` |
| `SEC-041` | The consultant receives no client data through the product | No upload path; bundle travels by the client's own mail | `TST-SEC-01`, `02`, `28` gate |
| `SEC-042` | No retention surprise: every automatic deletion is documented, surfaced and logged | Retention table §10.2 + storage screen + logs | `TST-SEC-15` |
| `SEC-043` | The privacy note text is owned here and reused verbatim | §10.3 | `TST-SEC-19` |
| `SEC-044` | Payload-shaped text is flagged and excluded from AI payloads without blocking the flow | Detector + AI log record | `TST-SEC-14` |
| `SEC-045` | No unreviewed binaries or vendored code in the repo | Review rule + license note + `CHANGELOG` | `TST-SEC-17` |
| `SEC-046` | The build is reproducible from a fresh clone with no machine-local secrets | Bootstrap + `scripts/check` + gate evidence | `TST-SEC-20` |
| `SEC-047` | Each release ships an SBOM-lite snapshot | `pip freeze` artefact attached to the release | `TST-SEC-20` |
| `SEC-048` | The project audit trail is append-only and exports with the pack | No delete/edit path in the UI or API; `AuditLog` written by the service layer only | `TST-SEC-22` |
| `SEC-049` | Security events live in a machine-level append-only file that outlives log rotation and project deletion | `security.log` JSON-Lines + `doctor` reporting | `TST-SEC-18`, `22` |

### 13.2 Test contract (owned by `14`, reserved here)

| Test | Asserts | Statements covered |
|---|---|---|
| `TST-SEC-01` | Full sample walkthrough with networking disabled: import → rules → forecast → Excel + deck → diagnostics; no failure and no retry storm | `SEC-001`, `002`, `005`, `041` |
| `TST-SEC-02` | Static inventory: every socket/HTTP call site resolves to `engine/ai` or the manual update check; a planted call site fails the check | `SEC-001`, `002`, `019`, `041` |
| `TST-SEC-03` | No timer/scheduler performs non-loopback I/O; a 10-minute idle trace shows zero outbound packets | `SEC-002`, `003` |
| `TST-SEC-04` | API binds `127.0.0.1` only on a random port; a request without the per-launch token from another process fails | `SEC-004`, `008` |
| `TST-SEC-05` | Source workbook SHA-256 unchanged after import; no handle left open | `SEC-006` |
| `TST-SEC-06` | Key field is write-only: no reveal control, no key in the UI payload or DOM, status shows provider + last-changed only | `SEC-010`, `036` |
| `TST-SEC-07` | A second local standard user cannot read the project folder | `SEC-023` |
| `TST-SEC-08` | DPAPI round-trip: set → restart → usable; a copied profile blob is unreadable on another machine (simulated) | `SEC-009`, `011`, `012` |
| `TST-SEC-09` | Log-content scan after a full run with planted amount `₹ 9,99,999.99` and vendor `ACME-HOSTILE-VENDOR`: neither string, no key material, no `C:\Users\<name>` in any log | `SEC-013`, `014`, `015` |
| `TST-SEC-10` | With a fake key configured, the fake value never appears in logs, exception text, prompts, project files, exports or diagnostics | `SEC-010`, `011`, `012`, `035` |
| `TST-SEC-11` | Byte scan of project folder + backups + exports + diagnostics after rotation/removal: no key material or any part of it | `SEC-012`, `035` |
| `TST-SEC-12` | Default bundle: no amounts, vendor names or secrets; every member hashed in `manifest.json`; size ≤ 20 MB | `SEC-016`, `017`, `018` |
| `TST-SEC-13` | Opt-in bundle: warning before export; data rows appear only with the box ticked; masking applied; exact values still off by default | `SEC-016`, `017`, `038` |
| `TST-SEC-14` | Injection fixture: malicious description → excluded from payload, flagged, schema-valid output or fallback, no data mutation | `SEC-025`, `026`, `027`, `044` |
| `TST-SEC-15` | Delete project: typed confirmation, pre-delete backup offer, folder removed, audit row written, no residual files | `SEC-033`, `042` |
| `TST-SEC-16` | Synced-folder guard: project creation inside a simulated OneDrive path is blocked with `ERR-SEC-007`; the override requires the acknowledgement, is recorded as `storage.syncOverride`, and export to the same path warns and proceeds | `SEC-032` |
| `TST-SEC-17` | Repo scan: no client identifiers, no data files, no binaries > 1 MB without a license note; secret scan green | `SEC-007`, `011`, `028`, `031`, `045` |
| `TST-SEC-18` | Crash-dump locality: induced crash writes a local dump + log, uploads nothing, shows the plain-language dialog with "Copy details" | `SEC-003`, `037` |
| `TST-SEC-19` | UI-copy audit: every privacy/storage/encryption string matches §5/§9/§10; "encrypted"/"secure" never appear for unimplemented properties | `SEC-022`, `024`, `034`, `036`, `039`, `040`, `043` |
| `TST-SEC-20` | Pipeline: allow-list scan, `THIRD_PARTY_LICENSES.txt` in the installed payload, `pip-audit` report on the release, SBOM-lite attached, fresh-clone build green | `SEC-028`…`031`, `046`, `047` |
| `TST-SEC-21` | TLS verification cannot be disabled; an intercepting/self-signed endpoint fails with `ERR-SEC-004`; a fixture payload contains only allowed fields and respects the caps | `SEC-020`, `021` |
| `TST-SEC-22` | Audit integrity: no UI/API path deletes or edits an `AuditLog` row; an attempted write to an audit row fails and is logged; the Audit Trail export matches the table; `security.log` contains the key-lifecycle and deletion events with no key material | `SEC-048`, `049`, `033` |

## 14. Failure modes and error codes (family `SEC`)

`ERR-SEC-nnn` is allocated here and aggregated into the catalog in `26` (`00_INDEX` §8). Copy is
plain-language, states what was **not** lost, and gives one action — the `FR-XC-006` shape.

| ID | Trigger | Headline + hint | Not lost | Security consequence |
|---|---|---|---|---|
| `ERR-SEC-001` | Stored key cannot be decrypted (DPAPI failure, different Windows account/machine) | *"The saved AI key can't be read on this PC — it is protected by your Windows account."* → Re-enter the key in Settings, or keep working without AI | All project data; AI features fall back to rule-based | Fail-closed: no silent retry with a stale key |
| `ERR-SEC-002` | Provider rejects the key (`401`/`403`) | *"The AI service rejected the key."* → Check the key, endpoint and deployment in Settings | Everything; the AI action falls back to rule-based text | The key is not echoed in the message or the log |
| `ERR-SEC-003` | Rate limit / quota exhausted | *"The AI service is limiting requests right now."* → Retry later or turn AI off for this step | Everything; rule-based text is available | The single retry is bounded (`10`) |
| `ERR-SEC-004` | TLS/certificate verification failure (often a corporate proxy) | *"The connection to the AI service could not be verified."* → Ask IT whether the network inspects HTTPS traffic | Everything | Verification is **never** disabled to make it work (`SEC-020`) |
| `ERR-SEC-005` | Network unreachable/timeout during an AI action | *"The AI service could not be reached. Here is a rule-based version instead."* | The action's output (rule-based) | No retry loop; no background retry |
| `ERR-SEC-006` | Diagnostics bundle exceeds 20 MB | *"The support bundle is larger than the limit."* → the dialog names the group to exclude | Nothing — export can proceed with the group excluded | The cap prevents mailing a database by accident |
| `ERR-SEC-007` | Attempt to store a project in a synced folder | *"This folder is synced to the cloud, so it is not a safe place for a live project."* → Use the default local folder, or override with a recorded acknowledgement | Nothing — no project is created until the user chooses | Prevents sync-induced corruption (`09` §7.2, `ADR-004`) |
| `ERR-SEC-008` | Folder permissions could not be restricted | *"Windows would not let the app restrict access to its data folder."* → Continue, but note that other users of this PC may be able to read the project | Everything; the app works | Stated residual risk, logged, and shown in the storage screen |

**Error-copy rule:** none of these messages may contain a key, a header, a URL with credentials, a file
path containing a user name, or any client data (`TST-SEC-09`/`10`).

## 15. Parked items (accepted-for-later, not forgotten)

| ID | Item | Why parked | Trigger to revisit |
|---|---|---|---|
| `BL-029` | Corporate proxy / custom CA support for AI calls | v1 fails closed with a clear message; adding trust-store management is real work | A client on an inspecting proxy needs AI |
| `BL-030` | "Secure erase" of a project | SSD wear-levelling makes app-level shredding a false promise; BitLocker is the right control | Client policy explicitly requires it |
| `BL-031` | Password-protected (encrypted) project backups | Adds key-recovery failure modes for a non-technical user; no crypto dependency in v1 | Client requires encrypted backups off-machine |
| `BL-032` | Data-retention automation (auto-archive/purge after N years) | Retention is the client's policy; a wrong default is destructive | Client retention policy supplied |
| `BL-033` | Windows Hello / TPM-bound key unlock | DPAPI per-user is proportionate for v1 | Client IT mandates it |
| `BL-034` | Endpoint allow-list (restrict AI calls to specific hosts) | The endpoint is already a single configured value | Multi-provider support lands |
| `BL-035` | In-app authentication, RBAC, multi-user | Server-dependent; explicitly out (`DEC-010`, `BL-004`/`005`) | The product ever gains a shared/server mode |

## 16. Change control and cross-document obligations

### 16.1 Obligations this document places elsewhere

| Obligation | Owner doc |
|---|---|
| Implement `TST-SEC-01`…`22`; include the injection fixture, the log-content scan and the audit-integrity test in the suite | `14` |
| Installer manifest ships `THIRD_PARTY_LICENSES.txt`; release checklist includes the secret scan, license scan, vulnerability triage, SBOM-lite and diagnostics-size check | `15`, `24` |
| Secret scan in pre-commit and CI; `.gitignore` entries; logging/error-handling standards; the "no binaries without review" rule | `17` |
| Error codes `ERR-SEC-001`…`008` in the catalog with this copy; the diagnostics/update endpoints documented | `26` |
| Risks T1…T12 mirrored with likelihood/impact/mitigation and gate reviews | `25` |
| The client questionnaire carries the storage, BitLocker, proxy and retention questions | `21` |
| The user guide carries the privacy note (`SEC-043`), the key-rotation steps, "what is in a support bundle", delete-project semantics, and the synced-folder warning | `22` |
| The handover doc carries the key-revocation runbook and the diagnostics workflow | `23` |
| The API contract documents the loopback token requirement and exposes no secret values | `26` |
| `00_INDEX` hosts the `SEC-nnn` prefix, the `TST-SEC` family and the `SEC` error family (done, §8) | `00` |

### 16.2 Changes to this document

| Change | Requires |
|---|---|
| A new statement (`SEC-nnn`) | A mechanism, a test ID, and a `13` + `CHANGELOG` entry; `14` updated in the same pass |
| A new outbound call | An ADR in `09`, a client-visible disclosure update (`SEC-039`), the static inventory test updated, and `.gitignore`/diagnostics review |
| A change to log or diagnostics content | `SEC-014`/`SEC-017` update + `TST-SEC-09`/`12` fixtures updated + `22` copy updated if the user-visible statement changes |
| Any weakening of a control | Written rationale, risk register entry (`25`), and explicit sign-off recorded in `CHANGELOG` + `SESSION_LOG` (`Addon 4 §E.2`) — **never** a silent relaxation |
| Enabling encryption at rest | New ADR (key recovery design first), migration/restore plan, and this document rewritten before code |

**Frozen constants owned by this document:** the location tree (§4.1) · the deletion semantics and the
"not a secure erase" statement (§4.3) · the DPAPI envelope and the lifecycle events (§5.2/§5.3) · the log
rotation numbers and content policy (§6) · the diagnostics contents and redaction map (§7) · the exhaustive
outbound inventory (§8.1) · the data-at-rest stance (§9.1) · the privacy note text (§10.3) · the injection
defence layers (§11.1) · the license/secret/vulnerability rules (§12) · error codes `ERR-SEC-001`…`008`
(§14).


