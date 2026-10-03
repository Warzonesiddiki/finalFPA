# Purge Manifest: Live Project DB Test-Origin Artifacts

**Date:** 2026-10-03  
**Operator / Slot:** AionCLI-08 (`01a0fd52-408e-7cc1-9ba4-6236ca6e2fe2`)  
**Authorization:** Task `#01a10092-120c-76e2-94d9-0352630c35a7` / Owner Auto-Decide (`purge-test-batches`)  
**Pre-Purge Backup Snapshot:** `backups/snapshot_20261002_233619/`  

---

## 1. Pre-Purge Integrity Verification

Before altering any records in the live project directory (`%LOCALAPPDATA%\FP&A Month-End Copilot\Projects\default`), SHA-256 hashes and restore viability were verified against the secured snapshot.

### Hash Audit
| Target Database | Live DB SHA-256 (Pre-Purge) | Snapshot SHA-256 | Verification Result |
|---|---|---|---|
| `analytics.duckdb` | `0ea33f81e3a992cb5e9854490f209594f78fa5c2929e7102e3b2b8529f5f0857` | `d7dc4762cba674d85e7fc71dbff636e05391d8ebfc2194c6f3796556e48e897a` | Expected diff (Session 010 live writes outside pytest, e.g. Batch 340) |
| `workflow.sqlite` | `37180bc41dbcbca035dbb70bc9cecaee36f9c968945cf45a160862085352c88f` | `b33e4cfc8dff7ec2896503c5d6480c5cbcfb0dfbbf7ce47b74f075dafa391d90` | Expected diff (Session 010 live writes outside pytest, e.g. Batch 340) |

### Snapshot Restore Verification
A test restore into an isolated temporary directory confirmed both snapshot files mount and read cleanly:
- `analytics.duckdb`: 64,533 `FactActual` rows, all 13 core dimension and fact tables intact.
- `workflow.sqlite`: 340 `FactImportBatch` rows, all 20 tables readable and consistent.

---

## 2. Proof Criteria & Boundary Enforcement

Under the binding owner purge conditions:
1. **Burden on Deletion**: Rows deleted **only** on positive proof of test-origin identity (e.g. `gl_api_seam.csv`, `gl_balanced.csv`, synthetic test budgets).
2. **Preservation of Candidate Real Data**: All rows originating from `bank_ledger_actuals.csv` (129 committed batches containing 64,371 rows) strictly preserved.
3. **No Orphan Dependents**: Related child records in `FactValidationCheck` linked to purged import batches removed synchronously.

---

## 3. Purge Execution Results

### Summary Breakdown
| Table / Artifact | Before Count | After Count | Purged Count | Status | Notes |
|---|---|---|---|---|---|
| `DuckDB FactActual` | 64,531 | 64,371 | **160** | **Purged** | Positively identified test fixtures (`gl_api_seam.csv`, `gl_balanced.csv`) |
| `DuckDB FactBudget` | 4 | 0 | **4** | **Purged** | Test batches 889 and 339 |
| `DuckDB FactForecast` | 13 | 13 | **0** | **Preserved** | Forecast scenarios intact |
| `SQLite FactImportBatch` | 341 | 129 | **212** | **Purged** | 212 test-origin batches deleted; exactly 129 `bank_ledger_actuals.csv` batches preserved |
| `SQLite FactValidationCheck` | 2,997 | 1,089 | **1,908** | **Purged** | Purged checks belonging to deleted batches; exactly 1,089 checks preserved |

### Final Categorization
- **Purged**: 160 `FactActual` rows, 4 `FactBudget` rows, 212 `FactImportBatch` records, 1,908 `FactValidationCheck` records.
- **Quarantined**: 0 rows (no ambiguous unproven records found; all records were either provably test-origin fixtures or candidate `bank_ledger_actuals.csv` data).
- **Kept**: 64,371 `FactActual` rows across 129 batches (all `bank_ledger_actuals.csv`), 13 `FactForecast` rows, 129 `FactImportBatch` entries, 1,089 `FactValidationCheck` entries.

---

## 4. Post-Purge Verification

1. `SELECT DISTINCT source_file_name FROM FactActual` returns exclusively: `bank_ledger_actuals.csv`.
2. Total `FactActual` row count: `64,371` (129 batches × 499 rows).
3. DuckDB and SQLite integrity checks confirmed zero database corruption.
