# Current Wave Evidence Pack Manifest

> **Quoted from Doc 16 §5.2 ("The phase evidence pack")**:
> | Artefact | Format | Where it lives |
> |---|---|---|
> | Gate checklist (§5.1 items, ticked per phase) | Markdown in the phase folder under `docs/evidence/phase-<n>/` | Repo (documents, no binaries) |
> | Test and coverage transcripts | The raw `scripts/check` output + `coverage.xml` | Attached to the gate record, not committed |
> | Performance report | `perf.json` + the baseline diff | `tests/perf/baselines/` for the baseline, the run report attached |
> | Acceptance harness report | `acceptance_report.json` | Attached |
> | Cross-artifact report | The harness's diff output | Attached |
> | Windows validation checklist | Signed checklist + screenshots (`15` §5.3) | Attached |
> | Demo script + result | `SESSION_LOG` entry | Repo |
> | Coverage-matrix snapshot | `00_INDEX` §4 rows for the phase | Repo |
> | Approval | `Phase <n> gate APPROVED — <who> — <date>` in `CHANGELOG` **and** `SESSION_LOG` | Repo |

---

## 1. Index of Assembled Evidence Items (Verified on Disk)

1. **Test Transcripts**: [`test_transcripts.md`](test_transcripts.md) — Summary of pytest test suite runs, integration tests, golden path tests, contract tests, and cross-artifact consistency checks.
2. **Build & Payload Reports**: [`build_payload_report.md`](build_payload_report.md) — PyInstaller onedir build execution, payload verification against NFR-006 (≤ 500 MB), asset inclusion, and SBOM generation.
3. **Audit Reports**: [`audit_reports.md`](audit_reports.md) — Security scan, coverage bars report (`app/engine` ≥ 90%, backend ≥ 75%), link-check report, Windows manual checklist execution, UAT dry-run results, and doc reviews.
4. **NFR Measurement Table**: [`nfr_measurement_table.md`](nfr_measurement_table.md) — Measured performance against NFR-002, NFR-004, NFR-006, NFR-007, NFR-009, and performance suite split (`pytest -m perf`).
5. **Defect Log**: [`defect_log.md`](defect_log.md) — Consolidated DEF-nnn authoritative defect log (S1–S4 severities per Doc 28 §3).
6. **Open Decisions List**: [`open_decisions.md`](open_decisions.md) — Tracked open decisions (DEC-038 through DEC-044), risk mitigations (RISK-001 through RISK-041), and OQ items awaiting confirmation.
7. **Scale Limits Analysis**: [`scale_limits_analysis_report.md`](scale_limits_analysis_report.md) — Mathematical stage-by-stage limits analysis modeling breach thresholds ($N_{\max}$) and identifying the 24-rule evaluator as earliest bottleneck at ~361k rows.
8. **250k Scale Soak Run Report**: [`250k_scale_soak_run_report.md`](250k_scale_soak_run_report.md) — Soak run report over the 250k-row scaled dataset verifying memory stability, execution timings, and throughput.
9. **API Response Time Spot Check**: [`api_response_time_spot_check_report.md`](api_response_time_spot_check_report.md) — Latency spot-check measurements across core API endpoints against NFR-003 interaction budget.
10. **Error Message UX Spot Check**: [`error_message_ux_spot_check_report.md`](error_message_ux_spot_check_report.md) — UX validation report verifying error envelopes, user messages, and hints across failure scenarios.
11. **Purge Manifest Report**: [`purge_manifest_20261003.md`](purge_manifest_20261003.md) — Pre-purge snapshot restore verification, positive proof criteria enforcement, and deleted vs kept row audit (160 test rows purged, 64,371 bank rows preserved) for live project DB.
12. **UAT Dry-Run Rehearsal Report**: [`uat_dry_run_report.md`](uat_dry_run_report.md) — Acceptance rehearsal report for scripts TST-UAT-01 through TST-UAT-06 against sample project workspace with explicit no-client-sign-off disclaimer per Doc 28 §5.2.
13. **UAT Dry-Run Execution Transcript**: [`uat_dry_run_transcript.md`](uat_dry_run_transcript.md) — Raw pytest and CLI rehearsal transcripts confirming 6/6 tests passed in 3.38s.
14. **UAT BvA Diff Register**: [`uat_bva_diffs.md`](uat_bva_diffs.md) — Tabular line-item tie-out diffing engine analytical results against manual spreadsheet baseline (0.00 numerical discrepancy).
15. **UAT Deck & Pack Parity Report**: [`uat_deck_parity.md`](uat_deck_parity.md) — Cross-artifact tie-out confirming 100% parity between Engine, Excel management pack, and PowerPoint presentation deck with Doc 28 §4.3 difference classification.
16. **Owner Decision Request Pack**: [`../packaging/owner_decision_request_pack.md`](../packaging/owner_decision_request_pack.md) — Consolidated blocking questions (`DEC-REQ-01` through `DEC-REQ-07`) with options, recommendations, and sign-offs mapped to release gates.
17. **Packaging Reports Index**: [`../packaging/README.md`](../packaging/README.md) — Comprehensive index of packaging and delivery markdown reports detailing purpose, date, and status.

---

## 2. Independent Audit Reports & Newly Landed Evidence

18. **Audit Report New-01 (Pre-Pilot Integrity)**: [`New-01_report.md`](New-01_report.md) — **VERDICT: CONDITIONAL PASS** (Hard blockers cleared, 2 S2 defects confirmed open: DEF-011 missing brand icon asset (renumbered to DEF-011; originally filed as DEF-009 before the 2026-10-03 renumber — it is the placeholder-asset defect, not the acceptance harness and not the data-quality score), DEF-011 Inno setup missing desktop shortcut).
19. **Audit Report New-01 Addendum (DEF-011 Icon)**: [`New-01_report_def011_icon.md`](New-01_report_def011_icon.md) — Technical isolation confirming `app.ico` icon asset missing from Inno installer payload.
20. **Audit Report New-02 (Delivery Manifest Reconciliation)**: [`New-02_report.md`](New-02_report.md) — Audit uncovering 2 phantom files (`pilot_plan.md`, `test_isolation_report.md`) in index and 10 unlisted evidence files on disk.
21. **Audit Report New-03 (Documentation Traceability)**: [`New-03_report.md`](New-03_report.md) — Traceability cross-check verifying cross-document linkages and requirement coverage.
22. **Audit Report New-04 (Security & Privacy Audit)**: [`New-04_report.md`](New-04_report.md) — Security verification confirming zero committed secrets, proper local-only storage, and DPAPI key wrapping.
23. **Audit Report New-05 (Vacuous-Test Sweep)**: [`New-05_report.md`](New-05_report.md) — **VERDICT: FAIL** (Identified 2 tautological/vacuous tests and 4 silent-skip test gates across the test tree).
24. **Audit Report New-06 (Generator Determinism & Seed Integrity)**: [`New-06_report.md`](New-06_report.md) — **VERDICT: PARTIAL FAIL** (Committed corpus reproducible under seed 42, but NOT under Doc 14 canonical seed 20260101; Excel outputs have wall-clock non-determinism).
25. **Audit Report New-08 (Bidirectional Traceability Audit)**: [`New-08_traceability_report.md`](New-08_traceability_report.md) — **VERDICT: FAIL** (Proves `DEC-046` through `DEC-053` exist in `docs/18` but are 0% traced in `docs/20_REQUIREMENTS_TRACEABILITY.md`, with a duplicate key collision on `DEC-046`).
26. **DEC-046..053 Traceability Audit Addendum**: [`traceability_dec046_053_report.md`](traceability_dec046_053_report.md) — Detailed raw script executions proving missing `docs/20` forward traces for recent decisions.
27. **Planted-Exception Acceptance Report (Markdown)**: [`acceptance_report.md`](acceptance_report.md) — **VERDICT: FAIL** (Planted exception recall failed at 3/32 (9.4%) due to uncommitted unbalanced `d365_gl_actuals.csv` gating).
28. **Planted-Exception Acceptance Report (JSON)**: [`acceptance_report.json`](acceptance_report.json) — Structured JSON execution payload recording 157 findings and per-rule breakdown from acceptance harness run.

---

## 3. Active Defect Regression Test Suites

29. **DEF-021 Regression Test Suite** (S1, fixed 2026-10-03; renumbered to DEF-021, originally filed as DEF-009): [`../tests/unit/test_def021_data_quality_score.py`](../tests/unit/test_def021_data_quality_score.py) — 5 tests proving `FactImportBatch.data_quality_score` is computed via `calculate_quality_score()` (05 §8 / CALC-050) rather than hardcoded to `100.0`; covers a failed High-severity check deducting and respecting the §8.2 bound of 96, a clean batch still scoring 100, and warn/fail/pass all moving the score. Measured on the real corpus: 9 checks, IMP-023 fail, score 84 (previously persisted 100.0). **VERIFIED GREEN.**
30. **DEF-011 Regression Test Suite** (S1, fixed 2026-10-03): [`../tests/unit/test_def011_asset_validity.py`](../tests/unit/test_def011_asset_validity.py) — 11 tests pinning the `scripts/build.py` precondition 4b asset validators `_is_valid_ico()` and `_validate_pptx_template()`, with positive and negative controls. Proven to reject the shipped 15-byte `ICO_PLACEHOLDER` and 16-byte `PPTX_PLACEHOLDER` stubs that previously passed a filename-only presence check and shipped inside the installer. **VERIFIED GREEN.**
31. **DEF-012 / DEF-013 / DEF-014 / DEF-016 / DEF-017 regression suites**: **NOT YET PRODUCED.** These defects are open as of 2026-10-03 and their regression tests are in flight with named owners. Per doc 28 §3.2 an S1 defect may only move to Resolved with a named regression test id, so none of these may be recorded as closed until the suite exists and is cited here.

---

## 4. Phantom Records Reconciliation (Audited Status: NOT-PRODUCED)

The following two files were previously indexed in early manifests and cited downstream, but were **never authored or committed to disk**:

- ~~`evidence/pilot_plan.md`~~ — **STATUS: NOT-PRODUCED**. Intended to document real-data pilot execution steps for GATE-13. The pilot strategy was superseded by sample-data fallback pilot execution under `DEC-053` / `RISK-002` documented in `packaging/fallback_execution_runbook.md` and `docs/28_ACCEPTANCE_TEST_REPORT.md`.
- ~~`evidence/test_isolation_report.md`~~ — **STATUS: NOT-PRODUCED**. Intended to document hermetic `tmp_path` fixture integration. Live isolation evidence was integrated directly into `tests/conftest.py` tripwires and documented in `packaging/concurrency_flake_instance_log.md` and DEF-006 closure notes.

---

## 5. Excluded Artifacts Policy (Non-Binary Repository Contract)
- **Binary Installer Files**: `.exe` installers / `.zip` portable packages under `packaging/out/` are excluded from Git repository per binary policy (verifiable locally via `scripts/build.py`).
- **Live GUI Video Recordings**: Automated UI runs execute via headless Playwright or script loops; video captures are kept locally and are not committed to git.
