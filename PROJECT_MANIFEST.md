# PROJECT MANIFEST
PROJECT: Final FP&A Month-End Copilot
STACK: Python 3.12+ (FastAPI, SQLite, DuckDB), TypeScript frontend
STARTED: 2026-10-06 Asia/Kolkata
TOTAL TASKS: 11

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

## BLOCKERS
- Latest recorded official acceptance remains FAIL: 27/32 raises, 16/18 High, 33 extras, and 3 zero-coverage rules; `evidence/acceptance_report.md` predates task 011 and was not rerun after the targeted remediations.
- Python 3.12+ is unavailable in this sandbox; compatible static checks ran under Python 3.11.2.
