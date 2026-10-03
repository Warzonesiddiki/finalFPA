"""Read-only probe: verify EXC-019 / EXC-020 planted fixtures against sample data."""
import csv
from decimal import Decimal
from collections import defaultdict

BUDGET = r"sample-data/budget_fy26.csv"
GL = r"sample-data/d365_gl_actuals.csv"


def rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        lines = [ln for ln in fh if not ln.startswith("#")]
    return csv.DictReader(lines)


def period_of(posting_date):
    # CALC-001: fiscal period 1 = January
    y, m, _ = posting_date.split("-")
    return f"FY{y[2:]}-P{int(m):02d}"


# ---- budgets ----
bud = defaultdict(Decimal)          # (entity, cc, acct) -> total all periods
bud_periods = defaultdict(set)      # (entity, cc, acct) -> {period}
bud_cell = defaultdict(Decimal)     # (entity, cc, acct, period) -> amount
entity_periods = defaultdict(set)   # entity -> all budget periods seen
for r in rows(BUDGET):
    k = (r["EntityCode"], r["CostCenterCode"], r["AccountCode"])
    amt = Decimal(r["BudgetAmount"])
    bud[k] += amt
    bud_periods[k].add(r["PeriodCode"])
    bud_cell[(*k, r["PeriodCode"])] = amt
    entity_periods[r["EntityCode"]].add(r["PeriodCode"])

all_periods = sorted({p for s in entity_periods.values() for p in s})
print("budget periods in corpus:", all_periods)
print()

# ---- gl actuals ----
ytd_actual = defaultdict(Decimal)    # (entity, cc, acct) -> actual P01..P09
all_actual = defaultdict(Decimal)
cell_actual = defaultdict(Decimal)   # (entity, cc, acct, period) -> net
acct_periods = defaultdict(set)      # (entity, acct) -> {period}
for r in rows(GL):
    k = (r["CompanyCode"], r["CostCenter"], r["MainAccount"])
    amt = Decimal(r["Debit"]) - Decimal(r["Credit"])
    p = period_of(r["PostingDate"])
    cell_actual[(*k, p)] += amt
    acct_periods[(r["CompanyCode"], r["MainAccount"])].add(p)
    if p <= "FY26-P09":
        ytd_actual[k] += amt
    all_actual[k] += amt

print("=== EXC-019 probe: IN01/5500/CC-130 ===")
k = ("IN01", "CC-130", "5500")
print("  ytd_actual  =", ytd_actual[k])
print("  annual_budg =", bud[k])
print("  budget periods:", sorted(bud_periods[k]))
ytd_budget = sum((bud_cell[(*k, p)] for p in sorted(bud_periods[k]) if p <= "FY26-P09"), Decimal(0))
print("  ytd_budget  =", ytd_budget)
if ytd_budget:
    print("  variance    =", ytd_actual[k] - ytd_budget,
          f"({(ytd_actual[k] - ytd_budget) / ytd_budget * 100:.1f}% over)")
if bud[k]:
    print("  consumption =", f"{ytd_actual[k] / bud[k] * 100:.1f}%")
print()

print("=== EXC-020 probe: entity/account pairs with partial coverage (actuals exist) ===")
pairs = defaultdict(set)
for (e, cc, a) in set(bud_periods) | set(ytd_actual):
    pairs[(e, a)].add((cc,))
for (e, a), _ in sorted(pairs.items()):
    # union of budget periods for this entity/account (any cost centre)
    bps = {p for (ee, cc, aa), s in bud_periods.items() if ee == e and aa == a for p in s}
    aps = acct_periods.get((e, a), set())
    open_periods = [p for p in all_periods if p <= "FY26-P09"]
    if not aps:
        continue
    missing = [p for p in open_periods if p not in bps]
    if missing and bps:  # partial coverage, actuals exist
        print(f"  {e}|{a}: budget periods={sorted(bps)}")
        print(f"          actual periods ={sorted(aps)}")
        print(f"          missing (open) ={missing}  coverage="
              f"{len([p for p in open_periods if p in bps]) / len(open_periods) * 100:.0f}%")
        # actual spend booked in the missing periods, for this entity/account
        miss_actual = sum(
            (cell_actual[(e, cc, a, p)] for (cc,) in _ for p in missing), Decimal(0))
        print(f"          actual in missing periods = {miss_actual}")
        print()