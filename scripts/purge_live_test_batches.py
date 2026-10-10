import os
import sqlite3

import duckdb

project_dir = os.path.expandvars(r"%LOCALAPPDATA%\FP&A Month-End Copilot\Projects\default")
duck_path = os.path.join(project_dir, "analytics.duckdb")
sqlite_path = os.path.join(project_dir, "workflow.sqlite")

con_s = sqlite3.connect(sqlite_path)
con_d = duckdb.connect(duck_path)

# Verify before counts
actual_before = con_d.execute("SELECT count(*) FROM FactActual").fetchone()[0]
budget_before = con_d.execute("SELECT count(*) FROM FactBudget").fetchone()[0]
batches_before = con_s.execute("SELECT count(*) FROM FactImportBatch").fetchone()[0]
checks_before = con_s.execute("SELECT count(*) FROM FactValidationCheck").fetchone()[0]

print(
    f"BEFORE: FactActual={actual_before}, FactBudget={budget_before}, FactImportBatch={batches_before}, FactValidationCheck={checks_before}"
)

# 1. FactActual: delete batches with source_file_name in ('gl_api_seam.csv', 'gl_balanced.csv')
deleted_actual = con_d.execute(
    "DELETE FROM FactActual WHERE source_file_name IN ('gl_api_seam.csv', 'gl_balanced.csv')"
).fetchall()
actual_after = con_d.execute("SELECT count(*) FROM FactActual").fetchone()[0]

# 2. FactBudget: delete test rows (batch 889 and 339)
deleted_budget = con_d.execute(
    "DELETE FROM FactBudget WHERE import_batch_id IN (889, 339)"
).fetchall()
budget_after = con_d.execute("SELECT count(*) FROM FactBudget").fetchone()[0]

# 3. SQLite: test batch IDs
test_batches = [
    r[0]
    for r in con_s.execute(
        "SELECT batch_id FROM FactImportBatch WHERE file_name != 'bank_ledger_actuals.csv'"
    ).fetchall()
]

# Delete validation checks for test batches
con_s.executemany(
    "DELETE FROM FactValidationCheck WHERE import_batch_id = ?", [(b,) for b in test_batches]
)
checks_after = con_s.execute("SELECT count(*) FROM FactValidationCheck").fetchone()[0]

# Delete test import batches
con_s.executemany("DELETE FROM FactImportBatch WHERE batch_id = ?", [(b,) for b in test_batches])
batches_after = con_s.execute("SELECT count(*) FROM FactImportBatch").fetchone()[0]

con_s.commit()
con_s.close()
con_d.close()

print(
    f"AFTER: FactActual={actual_after}, FactBudget={budget_after}, FactImportBatch={batches_after}, FactValidationCheck={checks_after}"
)
print(
    f"PURGED: FactActual={actual_before - actual_after}, FactBudget={budget_before - budget_after}, FactImportBatch={batches_before - batches_after}, FactValidationCheck={checks_before - checks_after}"
)
