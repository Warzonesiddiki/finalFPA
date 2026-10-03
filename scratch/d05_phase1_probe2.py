import sqlite3, duckdb, os, hashlib

proj = os.path.join(os.path.expandvars(r'%LOCALAPPDATA%'), r'FP&A Month-End Copilot\Projects\default')
sp = os.path.join(proj, 'workflow.sqlite')
dp = os.path.join(proj, 'analytics.duckdb')

con = sqlite3.connect('file:' + sp + '?mode=ro', uri=True)
print("== NON-BANK BATCHES ==")
for r in con.execute("SELECT batch_id, source_type, file_name, file_checksum, file_size_bytes, total_source_rows, loaded_count, quarantined_count, rejected_count, status, is_balanced, created_at FROM FactImportBatch WHERE file_name != 'bank_ledger_actuals.csv' ORDER BY batch_id"):
    print(r)
print("== BANK BATCHES (id, loaded, status, created) ==")
rows = con.execute("SELECT batch_id, loaded_count, total_source_rows, status, is_balanced, created_at FROM FactImportBatch WHERE file_name='bank_ledger_actuals.csv' ORDER BY batch_id").fetchall()
print("bank batch count:", len(rows))
print("bank loaded sum:", sum(r[1] for r in rows))
print("first 5:", rows[:5])
print("last 5:", rows[-5:])
print("ids:", [r[0] for r in rows][:10], "...", [r[0] for r in rows][-10:])
print("distinct loaded values:", sorted(set(r[1] for r in rows)))
print("distinct status:", set((r[3], r[4]) for r in rows))
con.close()

dcon = duckdb.connect(dp, read_only=True)
print("== FactActual per batch ==")
try:
    rows = dcon.execute('SELECT import_batch_id, count(*) FROM FactActual GROUP BY import_batch_id ORDER BY import_batch_id').fetchall()
    print("n batches with facts:", len(rows))
    print("total:", sum(r[1] for r in rows))
    print("first 5:", rows[:5])
    print("last 5:", rows[-5:])
    print("distinct counts:", sorted(set(r[1] for r in rows)))
except Exception as e:
    print("err", e)
print("== FactBudget per batch ==")
try:
    rows = dcon.execute('SELECT import_batch_id, count(*) FROM FactBudget GROUP BY import_batch_id ORDER BY import_batch_id').fetchall()
    print("FactBudget groups:", rows)
except Exception as e:
    print("err", e)
print("== FactBudget cols ==")
try:
    print(dcon.execute('DESCRIBE FactBudget').fetchall())
except Exception as e:
    print("err", e)
print("== FactForecast ==")
try:
    print(dcon.execute('SELECT * FROM FactForecast LIMIT 10').fetchall())
    print(dcon.execute('DESCRIBE FactForecast').fetchall())
except Exception as e:
    print("err", e)
dcon.close()
