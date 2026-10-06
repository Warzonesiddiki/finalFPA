# PROJECT MANIFEST
PROJECT: Final FP&A Month-End Copilot
STACK: Python 3.12+ (FastAPI, SQLite, DuckDB), TypeScript frontend
STARTED: 2026-10-06 Asia/Kolkata
TOTAL TASKS: 12

## DECISIONS LOG
- [2026-10-06] DECISION: Persist optional external batch references beside integer IDs — stable identities must survive fresh acceptance databases.
- [2026-10-06] DECISION: Keep fixture acceptance outside uploaded workbook data — only the harness may supply a recorded test decision.
- [2026-10-06] DECISION: Balance rejected history fixtures with non-planted reconciliation legs — preserve planted rows and stable line identities.
- [2026-10-06] DECISION: Map bank DocNumber to transaction voucher identity — prevent account-wide false cross-batch matches.
- [2026-10-06] DECISION: Map optional D365 DocumentDate into parsed transactions and keep P10 identity keys from the answer key — cutoff detection needs source dates without re-keying expected results.
- [2026-10-06] DECISION: Derive EXC-013 baselines and EXC-016 accrual history from committed period rows when no rule history is injected — production has no separate history configuration.
- [2026-10-06] DECISION: Reserve controlled spike/accrual keys and isolate structural fixture vouchers — preserve planted amounts while preventing routine traffic and balancing rows from manufacturing findings.
- [2026-10-06] DECISION: Scope budget/approval/voucher checks to current-period GL rows and debit-side expense exposure — sub-ledger feeds, offsets, prior periods, and balance-sheet accounts are not GL expense approvals.
- [2026-10-06] DECISION: Derive EXC-016 history only from a stable one-voucher-per-period GL expense pattern when no explicit history is configured — routine month-end traffic is not an accrual pattern.
- [2026-10-06] DECISION: Store period-specific measured budget values, preserve explicit zero-coverage rows, and keep the three precision-control annual envelopes — align EXC-018/019/020 with their distinct period, annual, and coverage scopes.
- [2026-10-06T17:01:08Z] DECISION: Define project-level completion using the ten binary Definition-of-Done criteria in `docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md` §2.1; the 80% target is 8/10 fully evidenced criteria, not a task-checkbox or unverified FR count.
- [2026-10-06T17:01:08Z] DECISION: Acceptance checksums cover all `.csv`, `.xlsx`, and `.json` data artifacts by relative path; include the history-acceptance sidecar and report SHA-256 values, without claiming a golden generator checksum that is not committed.
- [2026-10-06T17:01:08Z] DECISION: Sort `extras_by_rule` before acceptance-report serialization so identical finding sets produce stable JSON key order; do not change findings, thresholds, or acceptance bars.

## TASKS
[x] 001  app/engine/store/schema_sqlite.sql + app/engine/store/db.py  deps: —  notes: Added optional external_batch_ref/subject_namespace columns, legacy ALTER migration, and lookup index; py_compile + diff check pass.
[x] 002  app/engine/imports/models.py + app/engine/store/import_repo.py  deps: 001  notes: Added validated optional external_batch_ref/subject_namespace fields and persisted both with each batch; py_compile + diff check pass.
[x] 003  app/engine/store/exceptions_repo.py + app/engine/rules/rules_catalog_001_008.py + app/engine/rules/rules_01_08.py  deps: 002  notes: EXC-001/003/009 now use persisted source-side identities; py_compile + diff check pass.
[x] 004  app/engine/rules/acceptance.py  deps: 002,003  notes: Added deterministic source IDs and strict sidecar acceptance loading for the synthetic P3 workbook; compile + diff checks pass.
[x] 005  app/engine/imports/profiles.py + app/engine/imports/parser.py + app/engine/imports/control_totals.py  deps: 004  notes: Mapped optional SourceRowRef/PeriodCode, bank DocNumber identity, and deterministic acceptance timestamps; py_compile + DB rule smoke pass.
[x] 006  sample-data/generate_sample_data.py  deps: 005  notes: Derives 037/040 balancing legs and writes deterministic P3 acceptance sidecar; regenerated history fixtures from this source.
[x] 007  sample-data/import_history/01_bank_batch_037.csv  deps: 006  notes: Now balanced 95,500.00 debit/credit; production parser reports committable.
[x] 008  sample-data/import_history/02_gl_batch_039.xlsx + sample-data/import_history/02_gl_batch_039.acceptance.json  deps: 006  notes: Debit control total accepted with recorded actor/reason/time; production parser reports committable.
[x] 009  sample-data/import_history/03_bank_batch_040.csv  deps: 006  notes: Nine planted October rows retain P09 and stable row refs; balancing deposit makes batch committable.
[x] 010  Build and source-integrity verification  deps: 001–009  notes: Changed-module compile, TODO scan, and diff checks pass; Ruff reports 413 legacy findings but none on added/changed lines. Official acceptance is measurable, not passing: 27/32 raises, 16/18 High, 33 extras, and 3 zero-coverage rules; stability is identical and all history imports commit. General test suite remains deferred.
[x] 011  app/engine/imports/profiles.py + parser.py; app/engine/rules/rules_01_08.py, rules_09_16.py, rules_17_24.py; sample-data/generate_sample_data.py + GL/budget fixtures  deps: 010  notes: Wired DocumentDate/P10 keys, controlled P13 baselines, data-derived P16 accruals, current-period GL control scope, and period-specific budgets; py_compile and targeted parser/rule smoke pass with 037/039 GL history; official acceptance not rerun and general suite remains deferred.
[ ] 012  app/engine/rules/acceptance.py; sample-data/xlsx_deterministic.py; docs/14, docs/18, docs/33, CHANGELOG.md  deps: 011  notes: Full `.csv`/`.xlsx`/`.json` SHA-256 scope and stable extras ordering implemented; 17 legacy XLSX archives normalized with data payload preserved; targeted stdlib archive audit passed 33/33 CRC/timestamp/idempotence checks; production `checksum_scope` AST smoke passed 56/56 files with the acceptance sidecar included. Current-code official acceptance and same-seed generator test remain unrun because `.venv` is absent and `.python-version` pins 3.14.7 while system Python is 3.11.2.

## CORE SCOPE MEASUREMENT

**Denominator:** the ten project Definition-of-Done criteria D1–D10 in `docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md` §2.1. This is the project-level release denominator, not the 11/12 session tasks, the 24-rule wiring count, or the 156-row traceability inventory. Each criterion is binary and counts complete only when its implementation and relevant current acceptance evidence are both available. **80% target = at least 8/10 criteria complete.**

**Current evidence baseline (2026-10-06): 0/10 fully verified complete.** This is an evidence score, not a claim that no implementation exists. Stale status summaries and historical reports do not count as current passes; incomplete or unverified criteria do not receive partial credit.

| Criterion | Current status | Evidence / reason not counted complete |
|---|---|---|
| D1 Phase-0 gates and integrated coverage matrix | UNVERIFIED | `docs/00_INDEX.md` reports green, but no fresh independent gate reconciliation was run; `evidence/manifest.md` contains stale acceptance claims. |
| D2 All seven planted-exception bars, twice | FAIL (last persisted run) | `evidence/acceptance_report.md`: 27/32 recall, 16/18 High, 33 extras, 3 zero-coverage. It predates task 011; no current official result is available. |
| D3 Full quality gate with every required step | UNVERIFIED | General/full suite was not run (per QA instruction); compatible project interpreter/dependencies are absent. |
| D4 Engine ≥90% and backend ≥75% coverage | UNVERIFIED | Coverage evidence is dated 2026-10-03 and predates task 011; no current coverage run. |
| D5 All NFRs measured against current code | UNVERIFIED | `evidence/nfr_measurement_table.md` is dated 2026-10-03; current post-task-011 measurements are unavailable. |
| D6 Zero open S1/S2 at UAT entry | UNVERIFIED | Defect/status summaries conflict and have not been reconciled against current regression evidence. |
| D7 Golden/oracle/cross-artifact equality | UNVERIFIED | Existing parity evidence is historical; no post-task-011 rerun. |
| D8 Fresh-clone and real-Windows evidence | UNVERIFIED | This Linux sandbox cannot provide the required current Windows 11 checklist/screenshots. |
| D9 Docs 00–32 complete and free of stale claims | FAIL | Current repo contains known stale/contradictory status records; selected acceptance and determinism notes were reconciled, but no full documentation audit was run. |
| D10 Real-data pilot, signed UAT, and go-live | PENDING | `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` records the real-data pilot/UAT/go-live as pending client inputs and approvals. |

**Priority to reach the target without lowering gates:** (1) provision the project-pinned Python environment, then run the official acceptance once after the current fixes and review every miss/extra; preserve answer-key keys and source-specific import gates. (2) Close rule recall/false-positive gaps with finding-level evidence, including EXC-010/013/016 and EXC-017/021/022/023; never suppress or re-key. (3) Verify period/budget calculations, exception lifecycle, transactional storage, and migrations. (4) Reconcile API/OpenAPI/CLI, frontend workflows, exports, and end-to-end reporting. (5) Re-measure security, deterministic artifacts, performance and NFRs on the pinned runtime. (6) Complete real-data pilot, UAT and go-live only with client data and required sign-offs.

## BLOCKERS
- The persisted official acceptance result is FAIL (27/32 raises, 16/18 High, 33 extras, 3 zero-coverage) and predates task 011/PR #3. The targeted P10/P13/P16 smoke in task 011 is not official evidence; do not claim a pass until the official gate is rerun.
- Runtime mismatch: `.venv/bin/python` is absent; `.python-version` is `3.14.7`; system Python is `3.11.2`; `pyproject.toml` requires Python `>=3.12`. The official acceptance and same-seed generator test were not run under an unsupported interpreter.
- Full/general QA suite remains deferred as explicitly directed. D1, D3–D8, and D10 are not counted complete without current evidence; D9 remains known-failing until a broader doc/status reconciliation.
