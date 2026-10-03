import sqlite3, duckdb, os, hashlib, shutil

proj = os.path.join(os.path.expandvars(r'%LOCALAPPDATA%'), r'FP&A Month-End Copilot\Projects\default')
print("PROJ=" + proj)
sp = os.path.join(proj, 'workflow.sqlite')
dp = os.path.join(proj, 'analytics.duckdb')

con = sqlite3.connect('file:' + sp + '?mode=ro', uri=True)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("SQLITE TABLES:", tables)
print("batch count:", con.execute('SELECT count(*) FROM FactImportBatch').fetchone())
print("check count:", con.execute('SELECT count(*) FROM FactValidationCheck').fetchone())
cols = con.execute("PRAGMA table_info(FactImportBatch)").fetchall()
print("FactImportBatch cols:", cols)
rows = con.execute('SELECT file_name, count(*), min(batch_id), max(batch_id) FROM FactImportBatch GROUP BY file_name ORDER BY 2 DESC').fetchall()
for r in rows:
    print("FILE-GROUP:", r)
# sample distinct source types / statuses
try:
    print("STATUS-GROUP:", con.execute('SELECT status, count(*) FROM FactImportBatch GROUP BY status').fetchall())
except Exception as e:
    print("status err", e)
try:
    print("SRC-GROUP:", con.execute('SELECT source_type, count(*) FROM FactImportBatch GROUP BY source_type').fetchall())
except Exception as e:
    print("src err", e)
con.close()

dcon = duckdb.connect(dp, read_only=True)
print("DUCK TABLES:", dcon.execute("SHOW TABLES").fetchall())
print("FactActual count:", dcon.execute('SELECT count(*) FROM FactActual').fetchone())
try:
    print("FactActual files:", dcon.execute('SELECT source_file_name, count(*), min(import_batch_id), max(import_batch_id) FROM FactActual GROUP BY source_file_name ORDER BY 2 DESC').fetchall())
except Exception as e:
    print("factactual group err:", e)
for t in ['FactBudget', 'FactForecast']:
    try:
        print(t, dcon.execute(f'SELECT count(*) FROM {t}').fetchone())
    except Exception as e:
        print(t, "err", e)
dcon.close()
for f in ['analytics.duckdb', 'workflow.sqlite']:
    p = os.path.join(proj, f)
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    print(f, os.path.getsize(p), h.hexdigest())
