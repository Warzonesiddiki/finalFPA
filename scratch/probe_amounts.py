"""Focused probe: does amount_at_risk for EXC-019/020 match the fixture (960000.00 / 670000.00)?"""
import csv
from decimal import Decimal
from collections import defaultdict

OPEN = [f"FY26-P{m:02d}" for m in range(1, 10)]  # as-of FY26-P09


def rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        lines = [ln for ln in fh if not ln.startswith("#")]
    return csv.DictReader(lines)


def period_of(d):
    y, m, _ = d.split("-")
    return f"FY{y[2:]}-P{int(m):02d}"


bud_cell = defaultdict(Decimal)     # (ent, acc, cc, period)
bud_pair = defaultdict(set)         # (ent, acc) -> periods with budget
for r in rows("sample-data/budget_fy26.csv"):
    bud_cell[(r["EntityCode"], r["AccountCode"], r["CostCenterCode"], r["PeriodCode"])] += Decimal(r["BudgetAmount"])
    bud_pair[(r["EntityCode"], r["AccountCode"])].add(r["PeriodCode"])

# actuals, absolute amounts (per doc 03: sum of subject rows' ABSOLUTE amounts)
abs_pair_period = defaultdict(Decimal)  # (ent, acc) -> |amount| in period
for r in rows("sample-data/d365_gl_actuals.csv"):
    ent, acc, p = r["CompanyCode"], r["MainAccount"], period_of(r["PostingDate"])
    abs_pair_period[(ent, acc, p)] += abs(Decimal(r["Debit"]) - Decimal(r["Credit"]))

print("=== EXC-020 pair coverage (open periods FY26-P01..P09) ===")
for (ent, acc), periods in sorted(bud_pair.items()):
    if acc != "5450":
        continue
    missing = [p for p in OPEN if p not in periods]
    if not missing:
        continue
    covered = [p for p in OPEN if p in periods]
    uncovered_abs = sum((abs_pair_period[(ent, acc, p)] for p in missing), Decimal(0))
    print(f"  {ent}|{acc}: covered {len(covered)}/{len(OPEN)} = "
          f"{len(covered)/len(OPEN)*100:.0f}%  missing={missing}")
    print(f"      sum |actual| over MISSING periods = {uncovered_abs}")
    print(f"      fixture amount_at_risk          = 670000.00")
    print()

print("=== EXC-019 P19 illustrative vs corpus ===")
k = ("IN01", "5500", "CC-130")
ytd_abs = sum((abs_pair_period[("IN01", "5500", p)]
               for p in OPEN
               for (e, a) in [(k[0], k[1])]), Decimal(0))
print(f"  IN01|5500|CC-130 sum |YTD actual P01..P09| = {ytd_abs}")
print(f"  fixture amount_at_risk                    = 960000.00 (illustrative)")