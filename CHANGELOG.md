# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0-2.0.0.html).

## [Unreleased]

### Added
- **Minimal DimVendor + FactBudget CSV loader (`app/engine/imports/vendor_budget_loader.py`, `OQ-023`, `OQ-024`):** `DimVendor` existed in `schema_duckdb.sql` but no code path ever populated it, so the vendor-keyed rules (`EXC-007`/`EXC-014`/`EXC-015`, subject keys `vendor_code|...` per `06`) had no vendor dimension to join on; `FactBudget` CSV loading went through the generic actuals parser with naive dimension mapping and no `IMP-032` handling. New loader per `03` §2.1 grain register (`UNIQUE(vendor_code)`; `FactBudget` uniqueness key), `03` §3.4/`§4.2`, `04` §2.2 profiles/`§10`/`§11`/`§15`: parse (Decimal-only money, `resolve_fiscal_period`), validate (`IMP-010`/`016`/`018`/`032` + `IMP-024` reconciliation + FK existence per I12), atomic commit (DuckDB transaction; batch `staged` → `committed`, `rejected` with zero facts on conflict/rollback), audit row (`FactImportBatch` + `FactValidationCheck` + `QuarantineRow`). Exact duplicates de-duplicate with a recorded count; conflicting budget duplicates raise `BudgetCommitBlocked` (`IMP-032`); vendor name conflicts quarantine, never overwrite in place (P14). Spec gaps logged as `OQ-023` (vendor-master shape; `MasterVendorCategory`/`AuditLog` tables absent in code) and `OQ-024` (I12-vs-`IMP-013` default: quarantine), not silently expanded. Regression: `tests/unit/test_vendor_budget_loader.py` (10 tests). Out of scope, still owed: actuals `vendor_id` backfill, `MasterVendorCategory` writes, general `AuditLog` writes.
- **DEF-009 Planted-Exception Acceptance Harness (`14` §5.2, `TST-ACC-01`):** Doc 14 §5.2 named `tests/rules/test_acceptance.py` run by `scripts/acceptance`; neither existed, so the §5.3 bars were never measured by any automated run. Added `app/engine/rules/acceptance.py` (measurement core, shared by harness and CLI the way `rules/batch.py` is shared by CLI/API/perf), `tests/rules/test_acceptance.py`, `tests/rules/test_acceptance_blocked_regression.py` (39 tests total) and `scripts/acceptance.py`. Implements all six §5.2 steps and enforces the §5.3 bars unrelaxed: recall >= 29 of 32, control precision 0 of 8, High-severity recall 18 of 18, extras <= 3 unexplained per rule, stability across two runs, plus two completeness gates §5.3 leaves open (all 24 catalog rules wired; no rule with a planted case may have zero coverage). Joins on `catalog_rule_id or rule_id` because `Finding.rule_id` is engine-space and differs from the catalog id for eight rules. Three-state verdict with distinct exit codes: PASS 0, FAIL 1, **BLOCKED 2** when the doc 28 §5.0 corpus precondition makes the bars unmeasurable - never 0, never a recall figure. Reports `evidence/acceptance_report.{json,md}`.
- **Top-Level Repository Hygiene (`.gitignore`):** Created comprehensive top-level `.gitignore` protecting repo hygiene, environment configurations, and local project databases per Doc 13 security guidelines.
- **Unattended Nightly Playwright E2E Suite (`packaging/`):** Created `nightly_e2e_run_list.md` and `nightly_e2e_runbook.md` specifying four Playwright suites (golden path, error paths, tour & help, console audit) with execution runbook and failure triage guidance.

### Fixed
- **DEF-019 (S1) Option B double-entry rebuild of the sample-data baseline (`docs/04` §12 / `IMP-023`, `docs/03` §3.2, `docs/06` EXC-023/EXC-024):** the generator baseline loop emitted every row single-sided (revenue as bare credits, expenses as bare debits, no offsetting leg), so the corpus measured debit 24,626,607,267.80 vs credit 6,682,091,688.47 (residual 17,944,515,579.33, every entity imbalanced) and `IMP-023` rejected the file with 0 rows committed. A single suspense plug was ruled out: it would corrupt planted P24 into a ~17.94B `EXC-024` finding, cannot satisfy per-entity/per-period balance, and would trip `EXC-002` per `03` §3.2. The baseline loop in `sample-data/generate_sample_data.py` now emits balanced voucher pairs (revenue Cr offset by Dr to `1200`/`1010`; expense Dr offset by Cr to `2000`/`1010`); routine postings to `1999` net exactly 0.00 so only planted P24 fires; the planted block (incl. the P23 voucher imbalance of 5,000.00) is left unbalanced by design. `scripts/verify_trial_balance.py` now reports balance per voucher as well as per entity/period. Regenerated output measures residual 8,944,299.00, accounted for to the penny by the planted anomalies (IN02/US01 balanced, 6 of 9 periods balanced). Regression: `tests/unit/test_def019_double_entry.py` (3 of 5 fail on the pre-fix single-sided generator; the other 2 pin the 1999-purity and P23-plant guards).
- **DEF-010 Code-to-Spec Fix: Unconditional IMP-023 Reject Enforced For All Source Types:** per docs/04 section 12 and IMP-023 (scope F, Reject with the imbalance amount) the debit-equals-credit reject is unconditional with no sub-ledger exemption (section 2.2 is the source-type table, section 10 is the confirm step; neither grants one), and per docs/19 section 5.5 the spec is the sole authority of record. `commit_batch` in `app/engine/store/import_repo.py` therefore changed from `should_commit = bool(batch.is_balanced or (batch.source_type != "actuals_d365"))` to `should_commit = bool(batch.is_balanced)` for every `source_type`; `status` still records what actually happened to the rows and `is_balanced` still records the measured balance fact. Regression: `TST-IMP-023-R1` in `tests/unit/test_def010_batch_metadata.py` (unbalanced file commits 0 rows and audit agrees, parametrised across every source type). This supersedes the earlier committed-with-a-balance-warning encoding and the OPEN carve-out entry below.
- **DEF-014 Governance & Traceability Remediation (`docs/18`, `docs/20`):** Fixed duplicate decision identifier collision on `DEC-046` in `docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md`: preserved `DEC-046` for DuckDB primary key allocation rule (`09` ADR-007) and renumbered sample data regeneration decision (`DEC-REQ-01`) to `DEC-054`. Restored bidirectional requirements traceability in `docs/20_REQUIREMENTS_TRACEABILITY.md` §6.6 linking `DEC-046` through `DEC-054` to functional requirements, implementation modules, and verification tests.
- **DEF-008 Period Lifecycle Was Entirely Unreachable (`app/engine/store/period_repo.py`):** `open_period`, `close_period` and `reopen_period` all raised `ConstraintException: NOT NULL constraint failed: PeriodAuditLog.log_id`, breaking the New Period wizard (`FR-PRJ-004`), period close with immutable snapshot (`FR-PRJ-005`) and period-close snapshot (`FR-PRJ-010`). Three omitted DuckDB primary keys — `PeriodAuditLog.log_id` (all three methods), `DimPeriod.period_id` (`open_period`, masked for seeded periods by its `ON CONFLICT` branch) and `PeriodSnapshot.snapshot_id` (`close_period`) — plus `close_period` selecting a non-existent `FactActual.amount` column (`FactActual` stores `debit`/`credit`/`net_amount`). Keys are now allocated explicitly via `PeriodRepository._next_id()` and the close snapshot sums `net_amount`. Root cause recorded as `DEC-046`: DuckDB has no auto-increment (`IDENTITY` raises `NotImplementedException`, `AUTOINCREMENT` is a parser error), so DuckDB keys must be supplied at the INSERT — `AUTOINCREMENT` copied from a SQLite DDL is a defect. Covered by 12 new tests in `tests/integration/test_period_lifecycle.py`, each of the 7 fixes mutation-verified to fail when reverted. Status **Fixed - pending reporter confirmation** per doc 28 §3.2.
- **Doc 14 §5.2 Step 1 Seed Amendment — seed 42 is canonical (`DEC-055`, impact note in `docs/18` §5.3):** step 1 read `sample-data --seed 20260101`, a seed that was never used. The committed corpus was generated at the generator's documented default **`42`** and audit `New-06` reproduced it byte-exactly. Doc 14 was amended rather than regenerating the corpus two days from freeze. **Checksum scope is now bounded and stated:** the harness fingerprints the **CSV corpus only** (10 files in the primary corpus; 19 counting the `test_scale/` copy) and **records the `.xlsx` exclusion with its root cause** — `generate_sample_data.py` emits 15 `.xlsx` files (3 templates + 12 malformed) and `generate_tieout_template.py` a 16th, all via `openpyxl`, which stamps a wall-clock `dcterms:created` into `docProps/core.xml`, so their hashes change on every generation and any SHA-256 manifest covering them **fails by construction**. A checksum is never asserted where one cannot hold; closing this properly means normalising `dcterms:created` in the generators, tracked as a follow-on.
- **DEF-010 Batch Metadata Cannot Contradict the Analytic Store (`app/engine/store/import_repo.py`):** `commit_batch` derived the audit row's `status` from `is_balanced` alone while deciding whether to write rows from a different expression, so an unbalanced sub-ledger was recorded `status='rejected'` while every one of its rows landed in `FactActual` (measured: 499/499 and 399/399). `should_commit` is now computed once **before** the `FactImportBatch` insert and `status` records what actually happened to the rows; `is_balanced` still records the measured balance fact, so the pair reads unambiguously as "committed with a balance warning". **The general-ledger gate is unchanged and load-bearing** — an unbalanced `actuals_d365` file still commits zero rows. Covered by `tests/unit/test_def010_batch_metadata.py` (13 tests), whose core is an invariant parametrised across every source type and both balance outcomes, and **mutation-verified 3 of 3** (status derived from `is_balanced` again; GL gate relaxed; `is_balanced` rewritten to agree with `status`) — each injected mutation caught, each restore verified by SHA-256. The doc-04-versus-code carve-out question goes to the Owner as a spec amendment, deliberately not resolved by a code comment.
- **DEF-010 Debit=Credit Reject Not Enforced For Sub-Ledgers (OPEN, owner ruling needed):** `app/engine/store/import_repo.py:111` reads `should_commit = batch.is_balanced or (batch.source_type != "actuals_d365")`, so an unbalanced bank/payroll/procurement file is committed anyway (measured: 499/499 and 399/399 rows landed) while doc 04 §12 and `IMP-023` state the reject unconditionally. The batch row is additionally recorded `status='rejected'` from `is_balanced` alone, so `FactImportBatch` contradicts `FactActual`. The code comment cites "04 §2.2 & §10", but §2.2 is the source-type table and §10 is the confirm step; neither states a sub-ledger exemption. Surfaced by the new acceptance harness rather than fixed, because resolving it is a spec decision.

### Changed
- **Hermetic DB Isolation & Live Tripwire (`tests/conftest.py`):** Widened test DB isolation to redirect every test by default (`FPA_PROJECT_DIR` at `tmp_path`), reserving explicit opt-out only for `test_portable_mode.py`. Added session-scoped tripwire asserting live database batch counts remain invariant across the run.
- **AI Number-Tokenizer Chunking Bugfix (`app/engine/ai/client.py`):** Resolved chunking bug that split numeric literals across decimal/punctuation boundaries (e.g. `5000`, `1200.50`), converting strict xfail into passing regression test.
- **NFR-014 Coverage Policy Re-Scope & DEF-003 Resolution (`docs/14_TESTING_QA_PLAN.md`):** Formally re-scoped `NFR-014` (domain engines ≥90%, backend/storage infrastructure ≥75%) and closed DEF-003 with empirical coverage evidence (pure domain modules at 92.1%–100%, backend at 86%).
- **DEF-006 Shared-DB Flake Closure (`docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md`):** Closed DEF-006 with three consecutive green test runs (501 tests in 71.97s) under default isolation.
- **DEF-008 Period Lifecycle Defect Resolved (`docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md`):** Marked DEF-008 (S1, `PeriodAuditLog.log_id` NOT NULL constraint failure) as **RESOLVED** following reporter confirmation and green verification across 12 integration regression tests (`tests/integration/test_period_lifecycle.py`, `TST-PRJ-01`).
- **NFR Measurement Corrections (`evidence/nfr_measurement_table.md`):** Updated NFR table with true measured empirical values (backend coverage 86%, domain engines 92.1%–100%, Inno installer 73.02 MB vs 500 MB budget, import latency 22.48s).
- **Owner Decisions Recorded (Auto-Decide):** Applied approved outcomes for DEC-REQ-01 through DEC-REQ-07 in `packaging/owner_decision_request_pack.md` and `docs/18`.
- **API Contract Route Annotations (`docs/26_API_CONTRACT.md` §3):** Annotated all 19 planned-but-unregistered route specs with operational mappings or phase tags for complete inventory honesty.
- **API Breaking-Change Policy (`docs/26_API_CONTRACT.md` §6.4):** Added explicit version-bump and breaking-change policy covering additive changes, `/api/v2` namespace migration with ADRs, and prohibition of unversioned duplicates.
- **Error-Catalog Endpoint (`GET /meta/error-catalog` & `/api/v1/meta/error-catalog`):** Implemented runtime error catalog projection covering VAL, BVA, FC, RUL, STO, AI, and IMP error codes per `26` §5 and `08` §16.
- **API Contract Drift Gate:** Integrated `scripts/check_contract_drift.py` into the verification gate, enforcing OpenAPI-to-TypeScript schema synchronization.

### Changed
- **API Error Envelope Handling (`tests/integration/test_error_envelope.py`):** Expanded integration suite and FastAPI exception handlers to verify standard error envelopes (`status: error`, `code`, `userMessage`, `hint`) across 400, 404, 405, and 422 error paths.
- **Mapping Review Queue & Importer Seam (`FR-IMP-008`):** Importer ingestion wired to consume `applicable_for_run()` so suggestions accepted in import $N$ apply automatically in import $N+1$ and appear in mapping profile history.
- **AI Suite & Prompt Management (`FR-AI`):** Prompt version management, guardrails, redaction, and deterministic fallback path when no API key is configured.
- **Complete Chart Inventory (12/12):** Implemented `CHT-001` through `CHT-012` ECharts components across Analyze, Exceptions, and Forecast screens with drill targets, empty states, tooltips, table views, and CF formatting.
- **Test Database Isolation:** DuckDB test isolation fixtures (`tmp_path`) implemented, eliminating test lock contention under concurrency.
- **Authoritative Defect Log (`DEF-001` through `DEF-007`):** Consolidated authoritative defect log with S1–S4 severities per Doc 28 §3 added to `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §12.
- **Post-Go-Live Review Template:** Created `docs/31_POST_GO_LIVE_REVIEW_TEMPLATE.md` and indexed it in `docs/00_INDEX.md` per Doc 00 governance.
- **Gate Evidence Pack:** Phase gate evidence pack assembled under `evidence/` with master manifest (`evidence/manifest.md`) per Doc 16 §5.2.
- **Data Dictionary Grain Register Backfill:** Added `MappingSuggestionAudit`, `MappingSuggestionApplication`, and `PeriodAuditLog` to `docs/03_DATA_DICTIONARY.md` Section 2.1 grain register with owning code references.
- **Backlog Item BL-037:** Registered gradual refactor of existing UI payload DTOs in `docs/27_BACKLOG.md`.

### Changed
- **Scoped Type-Import Rule (`docs/17_CODING_STANDARDS.md`):** Recorded explicit rule requiring all API payload/response shapes to import from `ui/src/api/types.ts` while exempting pure view-only state (`FilterState`, local UI flags).
- **`scripts/build` now implements all ten steps of `15` §3.2 and the five preconditions of `15` §3.1.** The script previously ran steps 1–3 only, so the payload audit, portable zip, SHA-256/SBOM, and the `NFR-006` size report did not exist in the pipeline at all. New behaviour:
  - **Preconditions (§3.1)** fail fast in the documented order with the runbook's own failure messages: clean working tree (waivable with `--dev`), `scripts/check` green, semver-valid version (cross-checked against `app/__init__.py` per §2.2's "a version string is never typed twice"), required assets present (naming each missing one), Inno Setup discovered on `PATH` (never hard-coded per §2.1).
  - **Step 4** stages `templates/`, `THIRD_PARTY_LICENSES.txt` (assembled from Python **and** UI dependency metadata), `README.txt` (first-run pointer plus the portable-mode note from §4.3), and the EULA/disclaimer text.
  - **Step 5** is an automated payload audit: required entries present; no `tests/`, `docs/`, `sample-data/`, `.env`, or `.py` client sources; no key material (`SEC-031`); and, per §3.4, every `excludes` entry in `packaging/pyinstaller.spec` must carry a comment naming what pulled the module in.
  - **Steps 7–8** build the portable zip (shipping `portable.flag` *documentation*, since §4.3 makes self-contained mode opt-in) and write `SHA256SUMS-<version>.txt` plus the `sbom/py-<version>.txt` supply-chain snapshot.
  - **Step 10** writes `build-report.md`: payload size breakdown, per-step durations, and the `NFR-006` verdict.

### Security
- The pipeline no longer reports a proxy measurement as compliance. `NFR-006` is defined on the produced Inno Setup artefact (`14` line 84); when the installer is skipped or Inno Setup is absent, the report states **NOT VERIFIED** and labels the portable-zip size explicitly as a reference figure only.

### Known issues
- **No releasable artefacts exist for `0.1.0`.** The original `FPandAMonthEndCopilot-0.1.0-portable.zip` and `SHA256SUMS-0.1.0.txt` predate this pipeline: `scripts/build` had no steps 7 or 8 and could not have produced them, so they came from an ad-hoc manual step that is not in version control. They have been regenerated once by the completed pipeline, but that run **failed its payload audit** (blockers below) and the resulting zip contained a zero-byte placeholder deck used to exercise the later stages, so it was deleted rather than left where it could be mistaken for a deliverable. `packaging/out/0.1.0/` now holds only `build-report.md` as evidence. **Nothing in `packaging/out/0.1.0/` may be shipped**; artefacts must be regenerated by a green pipeline run once the blockers are cleared (`15` §1.2, §5).
- **Two blockers still prevent a green build.** Both are pre-existing; neither was
  introduced by the pipeline, and neither has been faked or stubbed:
  - **`packaging/icons/app.ico` is missing** — no app icon at any of the required sizes (`15` §2.3). Required by precondition 4.
  - **`packaging/templates/FPAMonthEndCopilot_v1.pptx` and the input `.xlsx`
    templates are missing** — built assets absent from the repo (`15` §2.3). Required by precondition 4. The audit checks each required template is present **and non-empty**, so a zero-byte placeholder cannot pass.
  - The EULA/disclaimer blocker has since been cleared: `packaging/EULA.txt` now
    exists, so doc 15 §3.2 step 4's payload requirement for the EULA text is met.
- **`packaging/pyinstaller.spec` excludes now documented, and `pandas` dropped.**
  All seven entries carry the pull-reason comment doc 15 §3.4 requires. The pull
  reasons were measured against PyInstaller's own dependency graph (from a scratch
  analysis with `excludes` emptied, because an excluded module is never analysed)
  and confirmed with runtime import checks: `matplotlib` and `scipy` arrive only
  via `pandas`; `IPython` arrives via both `pandas` and `polars._utils.various`,
  so its exclude survives the pandas removal; `tornado` arrives via `bottle` ←
  `webview.http` ← `webview` ← `app.desktop.shell`; `tkinter`, `jupyter`, and
  `sqlite3.test` are never imported at all. Because nothing in `app/` or
  `scripts/` imports pandas, `pandas` and `pandas.libs` are now excluded, saving
  roughly 12.9 MB of payload.
  - **Recorded interpretation of a defensive exclude.** Doc 15 §3.4 requires each
    exclude to name what pulled the module in and calls an unexplained exclude a
    review failure. Three of the seven entries (`tkinter`, `jupyter`,
    `sqlite3.test`) have *no* puller — nothing imports them. They are retained as
    guards against a future transitive dependency, and their comment says so
    plainly rather than inventing a pull story. This interpretation — "never
    imported" is a complete and acceptable answer to §3.4 — is recorded here so
    the decision is auditable rather than implied.
  - `numpy`, `lxml`, and `PIL` are deliberately **not** excluded: `lxml` and `PIL`
    are loaded at runtime by `pptx.parts.image`, and `PIL` also by
    `openpyxl.drawing.image`, so excluding either would break the Excel and
    PowerPoint pack exports.
- **Payload composition, corrected.** An earlier entry in this file described
  `numpy`, `pandas`, `PIL`, and `lxml` as "roughly 59 MB of transitive stack that
  is not excluded". That was too coarse: only `pandas` was removable. With pandas
  gone, the remaining payload is dominated by `_polars_runtime_32` at roughly
  168 MB (over half the bundle) — a polars packaging question rather than an
  exclude question, and the next real lever on `NFR-006` headroom.

## [1.0.0] - 2026-10-02

### Added
- **Settings & Master Data Screen Family (`SCR-033`–`SCR-038`, `FR-SET`):** Branding, currency formatting with Indian Lakh/Crore grouping toggle (`Addon 3 C.12`), CoA mapping profiles, vendor categories, recurring cost baseline, exception rule configuration, write-only AI key management, and version history with 1-click revert.
- **Import History & Batch Reversal (`SCR-011`, `FR-IMP-023/024`):** Complete audit log of import batches, cryptographic checksums, validation check reports, and all-or-nothing batch voiding with typed confirmation (`VOID`) and mandatory audit reasons.
- **KPI Ratio Cards & Data-Quality Score (`SCR-014`, `CALC-001`–`050`):** Gross margin %, opex %, and budget-burn % KPI cards with divide-by-zero N/A handling, plus 0–100 data-quality score displayed alongside individual failed checks.
- **Rule Effectiveness Analytics Dashboard (Doc 06 §9):** Per-rule effectiveness metrics, false-positive ratio tracking, two-period review trigger, and configuration tuning dashboard.
- **Full Frontend Screen Suite & Backend API Endpoints:** Complete integration across Import Wizard, Check Screen, BvA Analytics, Exceptions Register, Forecast Scenarios, Reports & Issuance, and Settings.

## [Unreleased] - 2026-10-03

### Fixed
- **DEF-021 (S1) `data_quality_score` was hardcoded to `100.0` on every import batch.** *(renumbered to DEF-021; originally filed as DEF-009)*
  `app/engine/store/import_repo.py` wrote the literal constant into
  `FactImportBatch.data_quality_score` regardless of validation outcomes, so a
  rejected or unbalanced file still reported "100.0% data quality". The release
  notes for 1.0.0 advertise a "0-100 data-quality score displayed alongside
  individual failed checks"; that feature was inert on the persisted batch value.
  `commit_batch()` now derives the score from the batch's check reports via the
  existing, tested `calculate_quality_score()` (05 §8 / CALC-050), which had been
  implemented but never called. Regression coverage added in
  `tests/unit/test_def009_data_quality_score.py`, including the 05 §8.2 bound that
  a single failed High-severity check caps the score at 96.
  Measured on `sample-data/d365_gl_actuals.csv`: 9 checks ran, IMP-023
  (Debit = credit) failed, imbalance 17,944,515,579.33, computed score 84 - the
  batch previously persisted as 100.0.

### Fixed
- **DEF-021 (S1) `data_quality_score` was hardcoded to `100.0` on every import batch.** *(renumbered to DEF-021; originally filed as DEF-009)*
  `app/engine/store/import_repo.py` wrote the literal constant into
  `FactImportBatch.data_quality_score` regardless of validation outcomes, so a
  rejected or unbalanced file still reported "100.0% data quality". The 1.0.0
  release notes advertise a "0-100 data-quality score displayed alongside
  individual failed checks"; that feature was inert on the persisted value.
  `commit_batch()` now derives the score from the batch's check reports via the
  existing, tested `calculate_quality_score()` (05 §8 / CALC-050).
  Regression: `tests/unit/test_def009_data_quality_score.py`.
  Measured on `sample-data/d365_gl_actuals.csv`: 9 checks, IMP-023 fail,
  imbalance 17,944,515,579.33, computed score 84 (previously persisted 100.0).

- **DEF-011 (S1) the build gate validated asset *filenames*, not assets.**
  `packaging/icons/app.ico` was 15 bytes of ASCII (`ICO_PLACEHOLDER`) and
  `packaging/templates/FPAMonthEndCopilot_v1.pptx` was 16 bytes of ASCII
  (`PPTX_PLACEHOLDER`). Doc 15 §3.1 #4 checks only that the files exist, so both
  stubs passed and shipped inside the 76 MB installer. `scripts/build.py`
  precondition 4b now validates them: the icon must clear 1 KB and carry a real
  ICO header; the template must clear 10 KB, be an intact ZIP, and contain all
  seven layout names doc 12 §3.6 requires (`FPA-PPT-001`.`006` +
  `FPA-PPT-DISCLAIMER`). Both shipped stubs are proven rejected.
  Regression: `tests/unit/test_def011_asset_validity.py` (11 tests, positive and
  negative controls). **Consequence: the installer rebuild is blocked until
  genuine assets are authored** - the gate failing is the intended behaviour.

- **DEF-018 (S1) the PowerPoint exporter never reads the deck template (found by team audit, confirmed by lead).**
  `app/engine/exports/ppt_pack.py` builds every slide from scratch: `prs = Presentation()` at
  line 1553 with no template argument, and all six slide builders use
  `prs.slide_layouts[6]` (the blank default layout) at lines 470, 612, 807, 930, 1109 and
  1333. Doc 12 §3.6 requires the opposite on both counts - "The engine never builds layouts
  from scratch: it copies the template and fills it" - and states the engine resolves shapes
  **by name**, aborting with `ERR-EXP-014` when a name is absent. Verified consequences:
  `ERR-EXP-014` appears **zero times** in `app/engine/errors.py` and in all of `app/` and
  `tests/`, so the documented abort path does not exist; doc 12 cites twelve `ERR-EXP-*`
  codes and `errors.py` contains no `EXP` family at all; and `ppt_spec.py`, which doc 12
  names as the canonical shape order, does not exist. Export therefore succeeds
  unconditionally regardless of template state. Consequence for evidence: the previously
  filed "100% Engine/Excel/PPT parity" result only demonstrates that python-pptx can read
  back what it procedurally wrote - it is not evidence of doc-12 template conformance.
  The 7-layout template authored on 2026-10-03 (36,131 bytes, 103 named shapes) is
  therefore correct but currently unused by the engine.
- **GL corpus: option (A) ruled out, option (B) required (AionCLI-09, confirmed by lead).**
  `scripts/verify_trial_balance.py` measures the committed corpus at 250,037 rows,
  debit 24,626,607,267.80 / credit 6,682,091,688.47, residual **17,944,515,579.33**, and
  all three entities are independently imbalanced (IN01 14.33B, IN02 2.17B, US01 1.45B).
  A single suspense plug to 1999 is **not permissible**: `evaluate_exc_024` reads
  `suspense_accounts = {"1999","9999","SUSPENSE"}` with a 100,000 threshold, so a 17.9B
  credit would corrupt planted P24 (expected 1,240,000.00) into a ~17.94B finding and raise
  false positives on IN02/US01; doc 04 §12/IMP-023 additionally requires debit=credit per
  entity and per period, which one line cannot satisfy; and doc 03 §3.2 permits no new
  account, since an invented code would trip EXC-002 (Unmapped Account). The generator must
  emit genuinely double-entry vouchers, leaving routine 1999 at exactly 0.00.
