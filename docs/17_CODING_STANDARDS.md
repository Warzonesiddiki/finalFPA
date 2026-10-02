> **Status:** Draft v0.1
> **Last updated:** 2026-10-02
> **Owning FRs/areas:** repo layout and file naming (Kickoff §5), language/format/lint/type rules, the
> engine-boundary and layering enforcement (`09` §4), money/time/determinism rules, error handling and
> logging standards (`13` §6, `NFR-012`), dependency, licence and supply-chain rules (Addon 1 §I), secrets
> and test-data hygiene, testing conventions, UI/React standards, git workflow and commit format (Addon 2
> §H.1), code-health guardrails (Addon 4 §I.3), the review checklist, and the coverage/`scripts/check`
> enforcement bars (`14` §13)
> **TL;DR (≤ 15 lines):**
> - **Deterministic money math:** Minor units / Decimal only; floating-point types strictly prohibited in financial calculations.
> - **Headless engine boundary:** Import-linter enforced; UI/CLI shells depend on engine, engine never imports UI or framework shells.
> - **Zero silent failures:** Explicit catalogued exceptions; raw stack traces sanitized; plain-language error hints surfaced to users.
> - **Testing & coverage bars:** ≥90% test coverage on engine core; every bug fix begins with a failing regression test.
> - **Trunk-based discipline:** Conventional Commits, reproducible one-command build scripts, and spec-before-code synchronization.

# 17 — Coding Standards

## 1. Purpose, ownership and the rules that bind this document

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| Repository layout, folder responsibilities, file and symbol naming | **`17` (this document)** |
| Formatting, linting, typing and static-analysis configuration | **`17`** |
| The engine-boundary enforcement mechanism (import-linter) and layering rules | **`17`**, with `09` §4 |
| Money/time/determinism coding rules | **`17`**, with `03`/`05` |
| Error-handling and logging conventions in code | **`17`**, with `13` §6, `26`, `08` §16 |
| Dependency, licence, binary and supply-chain rules | **`17`**, with `13` §12 |
| Secrets and test-data hygiene in the repo | **`17`**, with `13` §5, `14` §16 |
| Git workflow: branching, commit format, history hygiene | **`17`**, with Addon 2 §H.1 and `24` |
| Code-health guardrails (file size, dead code, `TODO` policy) | **`17`**, with `09` §15.3 |
| The review/self-review checklist and how the standards are enforced | **`17`** |
| What the product must do; formulas and rules; screens and copy | `02`, `05`, `06`, `07`, `08` |
| Architecture, module boundaries, ADRs, CLI, migrations | `09` |
| Test cases, coverage bars, CI composition, gate checklists | `14` |
| Where each doc's facts live (single-source rule) | `00_INDEX` §5 |

### 1.2 The three rules that outrank everything else in this document

1. **Spec first, then code.** A behaviour change updates the owning spec and `CHANGELOG` **before** code;
   traceability (`20`) follows the code in the same change (Kickoff §14.2, `19`).
2. **Quote before code.** Every non-trivial implementation starts by quoting the FR/section it implements
   in the session's notes (`19`); if the quote does not exist, the work does not start.
3. **Never weaken a test, a golden file or a threshold to make a change pass.** If an expectation must
   change, the spec changed first and the `CHANGELOG` says why (`14` §1.2 item 3, `06` §1.1).

### 1.3 The never-cut coding properties

These are architecture-level instances of `02` §3.3: exact Decimal money, atomic imports, versioned audit,
offline behaviour, the installer, backup/restore, golden tests and the cross-artifact equality. In code
terms: never introduce a float into a money path, never catch-and-continue around a data write, never add
a network call outside the marked AI client, and never bypass the single formula owner.

## 2. Repository layout and file naming

### 2.1 The canonical layout (from `09` §4.1 — no deviations without an ADR)

```
app/
  engine/          PURE PYTHON: calc/ rules/ forecast/ imports/ store/ exports/ ai/ common/
  api/             FastAPI app, routers, schemas, error envelope, session token
  cli/             argparse entry points over the engine
  desktop/         pywebview shell, single-instance mutex, window/DPI handling
  jobs/            worker thread, job registry, progress/ETA, cancellation
ui/                React + TS + Vite SPA (src/, theme/tokens.ts, e2e/)
tests/             unit, golden, rules, contract, artefacts, integration, e2e, perf, manual, fixtures/
packaging/         PyInstaller spec, Inno Setup script, icons/, templates/, version_info.txt
scripts/           dev, check, build, release, acceptance, perf
sample-data/       generator, templates, planted exceptions, malformed corpus
docs/              this documentation set
```

### 2.2 Folder rules

| Folder | Rules |
|---|---|
| `app/engine/*` | One concern per module; a new exception rule is one file under `engine/rules/`; a new formula belongs in `engine/calc/`; no I/O beyond the store and file formats it owns |
| `app/api/` | Thin: validate → call engine → shape response. No arithmetic, no SQL outside repositories, no business rules |
| `app/cli/` | Thin over the engine; argument parsing and exit codes only (`09` §5.3) |
| `app/desktop/` | Window/lifecycle only; it starts the API and never imports engine internals |
| `app/jobs/` | Worker thread, registry, progress and cancellation; it reports through the registry the API reads |
| `ui/src/` | Feature folders (`features/import`, `features/bva`, …), `components/`, `api/`, `theme/`; the API client lives in one module |
| `tests/` | The exact categories of `14` §4.1; a test's home follows what it proves, not where the code lives |
| `tests/fixtures/` | Synthetic fixtures only, including the prior-version project fixture for upgrade tests (`24`) |
| `scripts/` | One command per script, no logic that belongs in the app; `scripts/check` is the gate command (`14` §13.1) |
| `packaging/` | Only build inputs and generated metadata (`15` §2.3); `packaging/out/` is git-ignored |
| `sample-data/` | Generator + committed expectations; large generated datasets are regenerated, never committed |

**New top-level folders are an architecture change** and require an ADR (`09` §3) — the layout is a
contract, not a suggestion.

### 2.3 File and symbol naming

| Thing | Convention | Example |
|---|---|---|
| Python module | `snake_case.py`, singular where it holds one concept | `engine/rules/missing_recurring_cost.py` |
| Python package | `snake_case/` with `__init__.py` exposing only the public surface | `engine/imports/` |
| Python function/method | `snake_case`, verb-first for actions, noun for queries | `commit_batch()`, `quality_score()` |
| Python class | `PascalCase`, no `I`/`Impl` suffixes | `DuplicateInvoiceRule` |
| Constant | `UPPER_SNAKE_CASE` in `common/constants.py` where shared | `MAX_ROWS_PER_SHEET` |
| React component | `PascalCase.tsx`, one component per file | `VarianceWaterfallChart.tsx` |
| React hook | `useThing.ts` | `useProjectPeriod.ts` |
| TS type/interface | `PascalCase`; generated types are never renamed | `BvaRow` (from the OpenAPI schema) |
| Test function | `test_<behaviour>_<condition>` | `test_variance_percent_zero_budget_is_na()` |
| Test file | `test_<unit>.py` mirroring the module under test | `tests/unit/test_variance.py` |
| SQL migration | `NNNN_<snake_description>.sql`, strictly ordered | `0007_add_pack_issue_register.sql` |
| Doc file | `NN_TITLE_IN_CAPS.md` as in `00_INDEX` §3 | `17_CODING_STANDARDS.md` |

**Rule:** names carry meaning — `data`, `tmp`, `helper`, `utils`, `manager`, `handle` and `process` are
banned as sole names; if a name needs a comment to explain it, rename it instead.

## 3. Formatting, lint and types (per language)

### 3.1 Python 3.12 (`app/`)

| Aspect | Rule | Enforced by |
|---|---|---|
| Formatter | `ruff format`, line length 100 | `scripts/check` step 1 |
| Lint | `ruff check` with the shared rule set; complexity and argument-count limits on | `scripts/check` step 2 |
| Types | `mypy --strict` on `engine/`, standard `mypy` on `app/`; no `# type: ignore` without a reason comment | `scripts/check` step 3 |
| Docstrings | Every public module, class and function: one-line summary + parameters/returns where non-obvious; no narration of the obvious | Review |
| Imports | Absolute within `app.*`; no wildcard imports; stdlib → third-party → local grouping | `ruff` |
| `print` | Banned in `app/` — use the logger (`§6.2`) | Lint rule |
| Time | `datetime.now(UTC)` with tz-aware values; local conversion happens in the display layer only | Review, tests |
| Randomness | Only via an injected seed for sample-data generation; never in product paths | Tests |
| Sleeps/retries | No `time.sleep` in app code; retries are explicit, bounded and logged | Review |
| Paths | `pathlib.Path`; never `os.chdir`; long/Unicode paths handled (`TST-WIN-03`) | Review |
| Money | `Decimal` only (`§5.1`); the float ban is reviewed and swept | `14` §6.1 |

### 3.2 TypeScript / React (`ui/`)

| Aspect | Rule | Enforced by |
|---|---|---|
| TS config | `strict` on, `noUncheckedIndexedAccess`, `noImplicitOverride` | `tsc --noEmit` in `scripts/check` |
| `any` | Banned; `unknown` + narrowing where the shape is genuinely unknown | Lint |
| API types | **Generated from the OpenAPI schema** and imported — hand-written duplicates are forbidden (Addon 2 §B.2) | `scripts/check`, review |
| Data fetching | Only through the single API client module (token, envelope handling, error mapping in one place) | Review |
| Formatting | Prettier, defaults + the repo config; no manual alignment tricks | `scripts/check` |
| Lint | ESLint with the React/hooks rules on | `scripts/check` |
| Styling | Tailwind utilities + theme tokens; **no hardcoded hex** outside `theme/tokens.ts` (`08` §19) | Lint rule |
| Components | Function components + hooks; one component per file; props typed; no prop drilling beyond one level without a context | Review |
| Copy | All user-visible strings come from the message catalog (`08` §16); no concatenated sentences | `TST-SEC-19` copy audit |
| State | Server state is never duplicated in local state; derived values are computed from the server response, not stored | Review |

### 3.3 SQL (`engine/store`)

| Aspect | Rule |
|---|---|
| Style | Hand-written SQL in repositories (ADR-007); one module per aggregate; named statements |
| Parameters | **Parameterised only** — string interpolation of values is a defect (injection + type bugs) |
| Columns | Explicit column lists in application queries; `SELECT *` only in diagnostics scripts with a comment |
| Ordering | Every query that feeds output declares `ORDER BY` (determinism, `§5.4`) |
| Dialect | DuckDB for analytics, SQLite for workflow state (`03` §2); no dialect-specific tricks without a comment |
| Migrations | Forward-only, versioned, applied by the migration runner (`09` §13); never ad-hoc `ALTER` in feature code (Addon 1 §J) |
| Performance | Aggregation/filter/pagination server-side; no N+1 (`14` §12.2) |
| Money | `DECIMAL(18,2)` columns; no `FLOAT`/`REAL` in money paths (`03` §3) |

### 3.4 Configuration, docs and other files

- TOML/YAML/JSON: two-space indent, keys in `snake_case`, no secrets (placeholders only), one purpose per file.
- Markdown: the standard doc header (`00_INDEX` §7), relative links, tables for structured facts, no HTML.
- `.editorconfig` + `.gitattributes` keep line endings stable (LF in the repo; CRLF is the client's problem,
  not Git's).

## 4. The engine boundary and layering

### 4.1 The rule (Addon 2 §B.1 — non-negotiable)

| Layer | May import | May **not** import |
|---|---|---|
| `engine` | stdlib, approved libraries (`ADR-001`/`ADR-002`), `engine.*` | `api`, `ui`, `desktop`, `jobs`, HTTP clients |
| `api` | `engine`, its schemas, FastAPI | UI source, `desktop`, SQL outside repositories |
| `cli` | `engine`, stdlib (`argparse`) | API internals, UI |
| `desktop` | stdlib, `pywebview`, the API app object | engine internals directly |
| `jobs` | `engine`, its registry | API routers |
| `ui` | its own code, generated API types | any Python |

**Enforcement:** an `import-linter` contract run by `scripts/check` fails the build when
`app/engine/**` imports `fastapi`, `pywebview`, `app.api`, `app.desktop` or `app.jobs` (`09` §4.1, `14` §13.1).

### 4.2 What to do when the boundary feels inconvenient

| Symptom | Wrong fix | Right fix |
|---|---|---|
| The engine needs something only the API has | Import it "just this once" | Pass it in as a parameter or a protocol; the engine owns no transport concerns |
| A formula is needed in the UI | Re-implement it in TypeScript | Formatting only in the UI (`08` §15); all arithmetic comes from the API |
| A rule needs data the repository doesn't expose yet | Query DuckDB directly from the rule | Add a repository method (`engine/store`) and use it |
| The CLI duplicates engine logic | Copy-paste | The CLI composes engine calls; duplication is a defect |

### 4.3 Single-owner rules

- **One formula, one implementation** — all arithmetic lives in `engine/calc` (`CALC-*`, `KPI-*`).
- **One rule, one module** — every `EXC-nnn` is exactly one module under `engine/rules/`.
- **One display rule set** — scale, grouping, negatives, rounding for display per `08` §15/`05` §6; exports
  consume the same constants, never their own copies.
- **One copy catalogue** — user-visible strings live in the message catalog, single-sourced with `22`.

## 5. Money, time, numbers and determinism

### 5.1 Money and numbers

| Rule | Detail |
|---|---|
| Type | `Decimal` everywhere in money paths; `float` is banned (lint rule + review) |
| Construction | `Decimal("1234.56")` from strings/ints; **never** `Decimal(some_float)` |
| Precision | Money quantised to 2 decimals at the boundary defined in `05` §6; intermediate calculations keep full precision |
| Rounding | One rounding policy (`05` §6.1) and one sum-of-rounded rule (`05` §6.2) — no second implementation |
| Comparison | Exact equality on `Decimal`; **no epsilon/tolerance comparisons in the engine** (`05` §13) |
| Division | Divide-by-zero returns the documented `n/a` (÷0) or `—` (0/0) sentinel (`05` §4), never `inf`/`NaN` |
| Percentages | Percentage-point vs percent (`CALC-013`) is decided in `05`, never re-decided at a call site |
| Scale display | Lakh/crore grouping is a display concern (`08` §15, `11` §3.6) — the stored value is unaffected |

### 5.2 Dates, periods and timezones

| Rule | Detail |
|---|---|
| Fiscal calendar | Period assignment follows `CALC-002`; no other module derives a period |
| Storage | Date-only values are date-only; timestamps are UTC; display uses the project's locale (`08` §15) |
| Boundaries | Month-end and TTM windows come from `CALC-003`…`006`; no ad-hoc date maths in features |
| Locale changes | A timezone/locale change must not alter stored values or period assignment (`TST-WIN-13`) |

### 5.3 Identity and hashing

| Rule | Detail |
|---|---|
| Row fingerprint | `row_fingerprint` from `engine/common`, one implementation (`03` §4) |
| Exception identity | `identity_hash = SHA-256(rule_id\|subject_key)` exactly as specified (`06` §2.2); never hashed locally |
| Content hashes | SHA-256 through the shared helper; hex-lowercase; no home-made digests (`03`, `11` §6) |
| Idempotency | Re-running a job on unchanged input produces identical identities (`TST-RUL` re-run scenario) |

### 5.4 Determinism

1. Every output has an explicit, stable order — sort in SQL or in the engine, never rely on dictionary order.
2. Machine-readable payloads (`--json`, manifests, stamps) contain **no** wall-clock timestamps unless the
   contract requires one; when they do, they are ISO-8601 UTC.
3. No random values in product paths; sample data uses the fixed seed (`14` §16).
4. Locale-independent formatting in machine outputs — grouping/currency symbols never leak into data files.
5. A test that cannot be run twice with identical results is a defect (`09` §5.3, `TST-API-13`).

## 6. Error handling and logging

### 6.1 Error handling

| Rule | Detail |
|---|---|
| Typed errors | The engine raises typed errors carrying a **slug/code from the catalog** (`26`), a safe message and structured details — never a bare string or an OS error |
| Envelope | The API maps every failure to `{code, message, hint, details[]}`; the `hint` is the plain-language next action (`08` §16, `26`) |
| Copy ownership | User-facing text comes from the message catalog — code never invents wording, and internal exception text is never shown as the headline |
| What the user sees | Three parts: what happened · what was not lost · the one next action (`08` §16); the same rule applies to installer and CLI output |
| No raw tracebacks | A crash never surfaces a traceback (`NFR-012`); the crash path writes a local dump + log and shows the dialog with a "Copy details" action |
| No silent swallowing | `except Exception: pass` is banned; a caught exception is either handled (with a documented behaviour) or re-raised with context |
| No bare `except:` | Always catch the narrowest type that can occur |
| Atomic failure | A write path either completes or leaves the previous state intact (`04` §15, `TOCTOU`-safe temp-file + rename) |
| Cancellation | Cancellation is a normal outcome (exit code 8 for the CLI), not an error (`09` §8) |
| Exit codes | The CLI's documented codes `0`…`8` (`09` §5.3) are part of the contract — never re-purpose one |

### 6.2 Logging

| Rule | Detail |
|---|---|
| Library | The standard `logging` module with one configured root; no `print`, no logging in library import paths |
| Format | Structured JSON-Lines with stable keys; one event per state transition (`09` §7.3) |
| Levels | `DEBUG` off in normal runs (session-scoped troubleshooting only, `SEC-037`); `INFO` for state changes, `WARNING` for recoverable oddities, `ERROR` for failed operations, `CRITICAL` never in normal operation |
| Context | Job logs carry `job_id`, stage, attempt and duration; request logs carry a correlation id — no user/machine identifiers |
| **Never logged** | Amounts, vendor/owner names, account descriptions, source-file names, secrets or key material, client data of any kind (`13` §6.1); values are redacted with `<redacted>` or replaced by counts |
| Rotation | ≤ 50 MB per file / 7 days retention (`NFR-011`), machine-level events in `security.log` with its own retention (`13` §6.3) |
| Diagnostics reuse | The same redaction helpers feed the support bundle (`13` §7) — one implementation, so the bundle can never be more permissive than the logs |
| Noise | No logging inside tight loops; aggregate counters instead; no "here" trace markers in production code |
| Errors | Every failed operation logs once at the boundary where it is handled, with the code and the safe detail — not at every stack frame it passes |

### 6.3 What "safe detail" means

Safe: identifiers (`rule_id`, `batch_id`, `job_id`), counts, durations, sizes, versions, error codes,
file **types**, booleans, column **names**. Unsafe: anything a client could object to seeing in a zip a
non-technical user emails to support — values, names, paths with personal data, and anything secret. If in
doubt, log the count.

## 7. Dependencies, licences and the supply chain

### 7.1 Adding a dependency

1. Check `ADR-001`/`ADR-002` first: is the capability already covered?
2. Prefer the smallest, most-maintained package with a permissive licence; check its licence and its
   transitive footprint.
3. Record the addition (ADR or the ADR-002 library table) with the reason, then pin it in the lockfile.
4. Run `scripts/check` (licence scan included) and the affected tests before the commit that adds it.

### 7.2 Dependency rules

| Rule | Detail |
|---|---|
| Python | `uv` with `pyproject.toml` + `uv.lock`; installs in CI/build use the lock (`SEC-028`) |
| UI | `npm ci` from `package-lock.json`; no floating ranges in the lockfile-consuming path |
| No GPL/AGPL | Never in shipped binaries; the licence allow-list is MIT/BSD/Apache/PSF-class per `13` §12 (`SEC-029`) |
| Licence artefacts | `THIRD_PARTY_LICENSES.txt` ships in the payload and is regenerated at build (`15` §3.2, `TST-SEC-20`) |
| SBOM | A per-release `pip freeze` snapshot is attached to the release (`SEC-047`) |
| No vendoring | Vendored source and binaries > 1 MB require review, a licence check and an entry in `THIRD_PARTY_LICENSES.txt` (`SEC-045`) |
| Vulnerability clock | `pip-audit` runs on the documented schedule (`13` §12); a known-exploitable finding is a defect, not a note |
| Upgrades | Deliberate, one dependency group at a time, with the full test suite and a `CHANGELOG` entry; no drive-by bumps |
| Postinstall scripts | Not trusted by default; a package with one needs a justification in the review checklist |
| No new patterns | A new framework/pattern (state manager, ORM, charting library) requires an ADR — the stack is closed (`01` §13, `09` ADR-002) |

### 7.3 Reproducibility

A build must succeed from a fresh clone with the documented bootstrap and no machine-local state
(`09` §15.2, Addon 4 §I.2). Builds use lockfiles; versions are single-sourced (`15` §2.2); nothing is
downloaded at runtime.

## 8. Secrets and data hygiene in the repo

| Rule | Detail |
|---|---|
| No secrets in the repo | `.gitignore` covers `.env`, key files and client data folders; the pre-commit hook and the CI job both run `scripts/check-secrets` (`SEC-011`) |
| No secrets in code | The only secret the product ever handles is the client's AI key, stored via DPAPI and never read back into UI code (`13` §5) |
| No secrets in fixtures | Tests use dummy values; none of them resemble a real key |
| No client data anywhere | Repo, tests, fixtures, sample data, screenshots and docs contain synthetic data only (`SEC-007`); an accidental client file is an S1 process failure (`14` §16) |
| Sample data | Generated from the fixed seed, watermarked and flagged; the corpus is regenerated, not curated by hand (`14` §16) |
| Screenshots/logs in issues | Redacted with the same rules as the diagnostics bundle before they are attached anywhere |
| Network | No outbound call exists outside the marked AI client (`13` §3); adding one is an architecture change, not a feature detail |

### 8.1 Repository exclusions and survivability (Addon 5 §H)

The repository is a specification and source repository, not an artifact bucket. `.gitignore` is a safety
net; review must reject a prohibited file even if a pattern did not catch it.

| Category | Rule |
|---|---|
| Never in Git | Real client data, client backups/databases, secrets/keys, installers, build/package output, coverage output, caches, and large binary artifacts. A release is distributed outside Git with its SHA-256 (`24`). |
| Generated sample data | Commit the generator, seed/configuration, documentation and empty directory markers. Do **not** commit generated CSV/XLSX/corpus outputs as blobs; regenerate them locally. |
| Narrow reviewed fixture exception | A small formula-visible oracle workbook and small Golden Month comparison fixtures may live only beneath `tests/oracle/` or `tests/golden/`, with a manifest/readme, reviewer acknowledgement and no client data. This exception never permits installers, generic build output or large binaries. |
| New binary request | First ask whether a deterministic generator or text representation can replace it. If not, record size, licence, purpose, SHA-256 and review decision; use approved release/artifact storage rather than ordinary Git when it is large. |
| Secret/client-data detection | Run the secret/binary scan before each merge. A detection is a stop-work issue governed by `13` §3.1 and `30` §8, not something to suppress with an ignore rule. |

**Repository survivability policy.** The project keeps an independent copy with full history by using either
a second remote or a weekly `git bundle` archive in an approved, access-controlled location separate from
the primary development machine. The default is the weekly archive until the owner selects a second remote:

1. After each active development week, create `git bundle create fpa-YYYY-MM-DD.bundle --all` outside this
   repository and store it in the approved secondary location.
2. Verify the bundle in a clean temporary clone with `git bundle verify`; record only the path class, command,
   commit SHA and verification result in `evidence/YYYY-MM-DD-repo-survivability/`.
3. Do not commit the bundle itself. It is a large binary archive, not source.
4. Before the first post-approval product phase gate, the owner reviews the first successful archive or
   second-remote evidence. A missing independent copy blocks that gate until remediated.

## 9. Testing standards (how code is written to be testable)

### 9.1 Structure and naming

| Aspect | Rule |
|---|---|
| Layout | The categories of `14` §4.1 (`tests/{unit,golden,rules,contract,artefacts,integration,e2e,perf,manual}`) — a test lives where its *level* says, not where its code lives |
| Naming | `test_<behaviour>_<condition>`; a failing test's name should read as the bug |
| One behaviour | One logical assertion per test; multiple asserts are fine when they describe one behaviour |
| Structure | Arrange–act–assert, with the arrange factored into builders |
| Fixtures | Small, explicit builders in `tests/factories/`; share setup only when it is genuinely identical |
| Network | No test touches the network except the marked AI stub endpoints (`14` §12.1) |
| Time | Inject the clock; never `sleep` to synchronise a test |
| Money | Compare `Decimal` exactly; if a tolerance is involved it belongs to `05` §13 and is applied by the shared helper |
| Engine vs UI | Prefer engine-level tests (fast, deterministic); reserve Playwright for the golden path and state sweeps (`14` §9) |
| Golden files | Frozen (`14` §1.2 item 3); a change follows the spec-first rule with `CHANGELOG` evidence |
| Failure injection | Tests that prove atomicity kill the process at documented points (`14` §8.3, §11) |

### 9.2 Rules a reviewer enforces

1. New engine function ⇒ new test in the same change (`14` §13.2).
2. New rule ⇒ its `TST-RUL-nn` and its planted case, or the rule is not done.
3. New screen state ⇒ a state-matrix row and its sweep test (`08` §17).
4. New error ⇒ its catalogue entry and a test that asserts the **message ID**, not the prose (`26`).
5. Bug fix ⇒ a regression test that fails before the fix.
6. No test may depend on another test's side effects or on execution order.
7. No `.skip`/`.only`/`xfail` without a `27` ID in the same line.

## 10. UI/React standards (beyond formatting)

| Rule | Detail |
|---|---|
| Server is the truth | The UI never computes money or business rules; it renders what the API returns, formatted per `08` §15 |
| No duplicated derivation | Derived values are computed once (engine) and asserted equal everywhere by the cross-artifact harness (`14` §7) |
| Generated types only | `api/types.ts` is generated from OpenAPI; hand-written duplicates of API shapes are forbidden |
| One API client | Token handling, the envelope, retries and error mapping live in one module; components never `fetch` |
| Every screen has four states | Empty, loading, error and first-run (`08` §17); a screen without them is not finished |
| Error UX | Errors render the code + hint with the "copy details" action; never a raw payload or a stack |
| Accessibility is code | Labels, keyboard paths, focus order, contrast tokens and non-colour signals are requirements, not polish (`08` §18) |
| Copy from the catalog | No string literals for user-visible text; no sentence assembly; numbers formatted by the shared formatters |
| Long jobs | Progress, ETA and cancel come from the job contract (`09` §8); the UI stays responsive (`NFR-016`) |
| No feature flags | v1 has no runtime feature toggles; scope is controlled by the cut-line policy (`16` §9) |
| Determinism | No random ordering, no `Date.now()` in rendered output without a stated reason |
| Table behaviour | Virtualised grids, server-side paging, stable keys; never render 250k rows (`09` §12) |

## 11. Git workflow: branches, commits, tags

### 11.1 Branching (Addon 2 §H.1)

| Rule | Detail |
|---|---|
| Trunk-based | `main` is always green and releasable; no long-lived `dev` branch and no environment branches |
| Short-lived branches | A feature/hotfix branch lives for a session or two and merges back; if it lives longer, it is re-scoped |
| Merging | Rebase (or squash) onto `main` so history stays linear and readable; no merge commits from stale branches |
| `main` is protected | `scripts/check --fast` green before a merge; the full check before a gate/release commit; no direct broken pushes, no force-push |
| Releases | Tagged on `main` only, per `24` (`vMAJOR.MINOR.PATCH`); tags are never moved |
| Session mechanics | The working branch for an AI session is named for the session; its commits still follow the rules below |

### 11.2 Commits (Kickoff §14.4)

| Rule | Detail |
|---|---|
| Format | Conventional Commits: `type(scope): summary` — `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `chore` |
| Scope | The module, doc or area: `docs(phase-0)`, `feat(import)`, `fix(rules)`, `test(calc)` |
| Body | What and **why**, with the FR/doc references for non-obvious changes |
| Size | Small and often; one logical change per commit |
| Separation | Docs and code in **separate commits** (spec-first means the docs commit comes first) |
| Generated files | Never committed (`ui/dist`, `app/static`, `packaging/out`, coverage reports, caches) |
| Secrets | A commit containing a secret is rejected by the hook; if one slips through, it is rotated — history editing is not a fix |
| WIP | Allowed locally on a branch, never merged; the merge commit carries the real message |
| Tests | Never committed failing on `main`; a failing test exists only inside a branch that is still working |

### 11.3 Repository hygiene

- `.gitignore` covers build output, caches, virtualenvs, `node_modules`, coverage, `.env`, key files,
  client-data paths and generated sample-data outputs (`13` §12, §8.1).
- `.gitattributes` normalises line endings; a binary needs the narrow fixture exception in §8.1 or is rejected.
- No large binaries in history; installers and builds are never committed. Templates/icons and the two
  reviewed test-fixture locations are small, hashed and licence-reviewed (`SEC-045`).
- The weekly independent-history archive / second-remote policy of §8.1 is checked before product-phase gates.
- Tags and release artefacts are never re-uploaded with the same version — a re-release is a new patch
  version (`24`).

## 12. Code health guardrails (Addon 4 §I.3, `09` §15.3)

| Rule | Detail | Enforced by |
|---|---|---|
| File size | No source file > 500 LOC without a justification note in the file header | Lint + review |
| Dead code | Deleted, not commented out; zero commented-out code in the repo | Lint + review |
| `TODO`/`FIXME` | Must cite a `27` backlog ID (`TODO(BL-012): …`); an uncited marker fails the check | Lint |
| No speculative abstraction | The smallest implementation that fully satisfies the spec (`02` §3, Kickoff §14.7) | Review |
| No premature optimisation | Measure first (`14` §8); correctness beats speed in every conflict | Review |
| Function length | Keep functions small and single-purpose; extract when a second reason to change appears | Review |
| Naming | Names carry meaning (`§2.3`); no abbreviations except established domain ones (`BvA`, `GL`, `KPI`) | Review |
| Cyclic imports | Never; move shared types down the dependency graph | Lint |
| Unused dependencies | Removed in the same change as their last use | Review |
| Warnings | Zero warnings policy in `scripts/check`; a warning is either fixed or promoted to an error with a reason | `scripts/check` |
| Comments | Explain **why**, not what; a comment that restates the code is deleted | Review |
| Error paths | Every error path is deliberate; no "will never happen" branches without a comment | Review |
| Public docs | Module/class/function docstrings for anything another module calls | Review |

## 13. Review and the definition of done for a change

### 13.1 The pre-commit / pre-merge checklist

Every change (including a solo change) is checked line by line before it lands:

| # | Check |
|---|---|
| 1 | The spec/FR is quoted in the session notes, and the spec itself is updated if behaviour changed (spec-first) |
| 2 | `scripts/check --fast` is green locally; the full `scripts/check` is green before a gate/release merge |
| 3 | The change adds or updates its tests, and no test/golden file was weakened (`§1.2`) |
| 4 | Error paths return catalogued codes with safe messages (`§6.1`); nothing logs unsafe detail (`§6.3`) |
| 5 | No new dependency, pattern or top-level folder without an ADR/ADR-002 entry (`§7.1`) |
| 6 | Money/time/determinism rules honoured (`§5`) — no float in a money path, no unordered output |
| 7 | The engine boundary still holds (import-linter passes; no UI/API import crept into `engine/`) |
| 8 | Coverage bars hold for the touched area (`14` §13.2); a new engine function has its test |
| 9 | User-visible text comes from the catalog and obeys the wording rules (`08` §16) |
| 10 | `CHANGELOG` entry written (doc-updating change) and `20` traceability updated |
| 11 | Code health: no file-size violation, no `TODO` without a `27` ID, no commented-out code (`§12`) |
| 12 | Demoability: the change can be demonstrated on sample data in the phase's demo script (`16` §11.1) |

### 13.2 The Definition of Done (restated, with owners)

`02` §3.5 owns the per-feature text and `19` owns the enforcement: spec updated → tests written → works on
the sample project → error/empty/loading states handled → `20` traceability updated → `CHANGELOG` entry →
demo recipe recorded. This document adds the code-side conditions: the pre-merge checklist above and the
enforcement table below.

### 13.3 What a reviewer is allowed to say "no" to

A change is blocked by any of: a missing quote/spec change; a weakened test; an uncited `TODO`; a float in a
money path; a new dependency without an entry; a new network call; a log line with unsafe detail; a
duplicated formula or rule; a new top-level folder; a screen state without its matrix row; a message string
outside the catalog; or a file-size violation without a justification note. Nothing else blocks a change —
style is automated, not debated.

## 14. Enforcement: what fails the build and where the rule lives

| Rule area | Enforced by | Gate item |
|---|---|---|
| Format, lint, types, import boundary | `ruff format --check`, `ruff check`, `mypy`, import-linter | `scripts/check` step (`14` §13.1) |
| Test suite + coverage bars | `pytest --cov` with thresholds in `pyproject.toml` | `14` §13.2, `16` §5.1 item 2 |
| UI types/lint | `tsc --noEmit`, `eslint .` | `14` §13.1 |
| Secret scan | `scripts/check-secrets` (pre-commit + CI) | `SEC-011`, `16` §5.1 item 1 |
| Licence allow-list | `scripts/check-licenses` + the ADR-002 table | `SEC-029`, `GATE-02-09` |
| Docs link-check | `scripts/check-docs` | `16` §5.1 item 1 |
| SBOM presence | `scripts/check-sbom` at release steps | `SEC-047` |
| Fresh clone builds | `scripts/bootstrap` + `scripts/check` on a clean clone | `09` §15.2, Addon 4 §I.2, `GATE-05-12` |
| File size / dead code / `TODO` policy | lint where expressible, review otherwise | `09` §15.3, `16` §5.1 item 1 |
| The never-cut list in code terms | review + the gate checklist | `02` §3.3, `16` §9.2 |

**When a rule cannot be enforced automatically**, it is written into the review checklist (`§13.1`) rather
than left as folklore; when a rule *can* be enforced, enforcement is the deliverable — "we remembered" is
not a control.

### 14.1 The spike policy (Addon 4 §I.1, `09` §15.1)

A risky unknown gets a **timeboxed spike (≤ half a day)** with a written question, options and outcome
recorded as an ADR or a `27` entry **before** any production code is committed. Spike code lives on a
branch and is never merged into `main` (its learning is); the packaging spike is the one exception in
budget (two half-days, `16` §4) and none in rigour.

### 14.2 Where a standards violation is recorded

A violation that reaches a gate is a **defect** (`14` §14.1 severity class) or a `27` entry with a trigger —
never a silent fix that leaves the history lying. Repeated violations of the same rule are a signal that the
rule is wrong: change the standard (with a `CHANGELOG` entry) or automate it, don't keep policing it.

## 15. Open items, deferrals and assumptions

| Item | Status |
|---|---|
| CI provider and runner availability | Windows runner "where available"; otherwise local full `scripts/check` with the transcript attached (`14` §13.3) — to be confirmed by the project owner |
| Exact ruff/mypy/ESLint rule lists | Owned by the repository config files; any deviation from `§3` is a `CHANGELOG`-recorded decision |
| Pre-commit hook manager | By plain `pre-commit`; hook contents are the same scripts the CI runs (`§14`) — no separate logic |
| Monorepo tooling (task runner) | Not needed at this size; `scripts/*` are the interface (`09` §15.4) |
| Formatter for Markdown/JSON | Not enforced beyond `.editorconfig`; docs are checked by the link-check and the header rules |
| Performance linting beyond the budgets | Not enforced in code; the gate measures (`14` §8) |
| Coverage exclusions | Only generated migrations and `TYPE_CHECKING` blocks, each listed with a comment (`14` §13.2) |

**Assumptions.** (a) The engine/API/UI split of `09` §4 stays as decided; (b) the toolchain is pinned
(`ADR-002`) and the same commands run locally and in CI; (c) the standards are for one senior engineer plus
AI sessions, so automation is preferred over ceremony; (d) no external code-review requirement exists
beyond the checklist in `§13.1`.

## 16. Change control and cross-document obligations

### 16.1 Obligations this document places elsewhere

| Obligation | Owner |
|---|---|
| The import-linter contract, module map and layer table stay identical in substance here and in `09` §4 | `09` |
| `scripts/check` implements exactly the composition (format, lint, types, boundary, tests, coverage, UI, secret, licence, docs, SBOM) | `scripts/`, `14` §13.1 |
| Coverage thresholds live in `pyproject.toml`, not in prose, and match `14` §13.2 | repository config |
| Error codes, message catalog and redaction helpers are the single source used by code, API and diagnostics | `26`, `13` §7, `08` §16 |
| Every doc-changing code change updates `CHANGELOG` and `20` in the same pass | `19`, `20` |
| The fresh-clone bootstrap test and the spike policy are gate items | `16` §5.1, `09` §15 |
| Licence allow-list, `THIRD_PARTY_LICENSES.txt` and the SBOM are release artefacts | `15` §1.2/§3.2, `24` |
| The prior-version project fixture lives under `tests/fixtures/` and is maintained | `24` |
| `.gitignore`/`.gitattributes` contents match `§8`/`§8.1`/`§11.3`, including generated sample-output exclusions and reviewed test-fixture exceptions | repository config |

### 16.2 Changes to this document

| Change | Requires |
|---|---|
| A new top-level folder, layer or dependency pattern | An ADR (`09` §3), then this document, then code |
| A change to the money/time/determinism rules | A `05`/`03` change first (they own the semantics); this document follows |
| A change to the git workflow | Addon 2 §H.1 still binds; the change is recorded here with a `CHANGELOG` entry |
| A new automated check | Its failure mode and gate item recorded here and in `14` §13 |
| A rule deleted because it is wrong | Evidence that it was wrong (a violation that was actually correct practice), the rule removed in the same pass from any lint config and this document |
| Any change here | `CHANGELOG` + `SESSION_LOG` entries; the next gate re-runs `scripts/check` in full |

**Frozen constants owned by this document:** the canonical folder layout and its rules (§2.1/§2.2) · the
naming conventions (§2.3) · the formatting/lint/type configuration expectations per language (§3) · the
engine-boundary import rules and their enforcement (§4) · the money/time/determinism rules (§5) · the error
and logging conventions (§6) · the dependency/licence/supply-chain rules (§7) · the repo-hygiene rules
(§8, §11.3) · the testing conventions (§9) · the UI standards (§10) · the branching/commit/tag workflow
(§11) · the code-health guardrails (§12) · the 12-item review checklist (§13.1) · the enforcement map (§14).


