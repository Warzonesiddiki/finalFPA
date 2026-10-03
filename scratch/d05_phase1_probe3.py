import hashlib, os

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

repo = r'C:\Users\Tahir\Documents\GitHub\finalFPA'
for f in ['sample-data/bank_ledger_actuals.csv', 'sample-data/d365_gl_actuals.csv', 'sample-data/budget_fy26.csv']:
    p = os.path.join(repo, f)
    if os.path.exists(p):
        print(f, os.path.getsize(p), sha(p))
    else:
        print(f, "MISSING")

# row counts (minus header)
for f in ['sample-data/bank_ledger_actuals.csv', 'sample-data/budget_fy26.csv']:
    p = os.path.join(repo, f)
    with open(p, 'r', encoding='utf-8', errors='replace') as fh:
        n = sum(1 for _ in fh) - 1
    print(f, "data rows:", n)

# d365 too big: count fast
p = os.path.join(repo, 'sample-data/d365_gl_actuals.csv')
with open(p, 'r', encoding='utf-8', errors='replace') as fh:
    n = sum(1 for _ in fh) - 1
print('sample-data/d365_gl_actuals.csv data rows:', n)
