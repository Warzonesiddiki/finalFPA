# Wave 5 independent A3 recompute — auditor-owned, Decimal only, ROUND_HALF_UP.
# Source under audit: docs/05_CALCULATION_SPEC.md section 12 fixtures (F1-F14) + section 8 guarantees.
# Every expected value below is transcribed FROM the document; this script recomputes from inputs.
from decimal import Decimal as D, ROUND_HALF_UP, getcontext

getcontext().prec = 50
FAILS = []
CHECKS = 0

def q(x, places):
    return x.quantize(D(places), rounding=ROUND_HALF_UP)

def chk(name, computed, doc_value):
    global CHECKS
    CHECKS += 1
    ok = (computed == doc_value)
    if not ok:
        FAILS.append(f"{name}: computed={computed} doc={doc_value}")
    print(f"{'MATCH' if ok else 'MISMATCH'}  {name}: computed={computed} doc={doc_value}")

# ---- F1: revenue variance -------------------------------------------------
a, b = D("1080000.00"), D("1000000.00")
v = a - b
chk("F1 variance", v, D("80000.00"))
chk("F1 pct_full(6dp)", q(v / abs(b), "0.000001"), D("0.080000"))
chk("F1 pct_disp(1dp)", q(v / abs(b) * 100, "0.1"), D("8.0"))
# revenue actual>budget => favourable (direction rule, stated doc)

# ---- F2: expense under budget --------------------------------------------
a, b = D("355000.00"), D("380000.00")
v = a - b
chk("F2 variance", v, D("-25000.00"))
chk("F2 pct_full(6dp)", q(v / abs(b), "0.000001"), D("-0.065789"))
chk("F2 pct_disp(1dp)", q(v / abs(b) * 100, "0.1"), D("-6.6"))

# ---- F3: expense over budget ---------------------------------------------
a, b = D("245000.00"), D("200000.00")
v = a - b
chk("F3 variance", v, D("45000.00"))
chk("F3 pct_full(6dp)", q(v / abs(b), "0.000001"), D("0.225000"))
chk("F3 pct_disp(1dp)", q(v / abs(b) * 100, "0.1"), D("22.5"))

# ---- F4/F5: zero-budget states -------------------------------------------
chk("F4 variance", D("15000.00") - D("0.00"), D("15000.00"))
chk("F5 variance", D("0.00") - D("0.00"), D("0.00"))

# ---- F6: YTD + sum-of-rounded --------------------------------------------
acts = [D("1080000.00"), D("1020500.55"), D("995300.45")]
buds = [D("1000000.00")] * 3
chk("F6 YTD actual", sum(acts), D("3095801.00"))
chk("F6 YTD budget", sum(buds), D("3000000.00"))
v = sum(acts) - sum(buds)
chk("F6 YTD variance", v, D("95801.00"))
chk("F6 pct_full(6dp)", q(v / sum(buds), "0.000001"), D("0.031934"))
chk("F6 pct_disp(1dp)", q(v / sum(buds) * 100, "0.1"), D("3.2"))
chk("F6 P08 variance", acts[1] - buds[1], D("20500.55"))
chk("F6 P09 variance", acts[2] - buds[2], D("-4699.55"))
chk("F6 sum-check", D("80000.00") + D("20500.55") - D("4699.55"), D("95801.00"))
# F6b: component ratios display
comps = [D("33.334"), D("33.333"), D("33.333")]
disp = [q(c, "0.1") for c in comps]
chk("F6b each displays 33.3", disp, [D("33.3")] * 3)
chk("F6b sum of displayed", sum(disp), D("99.9"))
chk("F6b true sum", sum(comps), D("100.000"))
chk("F6b true sum displays", q(sum(comps), "0.1"), D("100.0"))

# ---- F7: TTM --------------------------------------------------------------
ttm = [D("900000.00"), D("920000.00"), D("1010000.00"), D("880000.00"),
       D("890000.00"), D("940000.00"), D("960000.00"), D("975000.00"),
       D("985000.00"), D("1080000.00"), D("1020500.55"), D("995300.45")]
tot = sum(ttm)
chk("F7 TTM total", tot, D("11555801.00"))
avg = tot / 12
chk("F7 TTM avg displays", q(avg, "0.01"), D("962983.42"))

# ---- F8: prior-year -------------------------------------------------------
chk("F8 MTD var", D("1080000.00") - D("950000.00"), D("130000.00"))
chk("F8 MTD pct(6dp)", q(D("130000.00") / D("950000.00"), "0.000001"), D("0.136842"))
chk("F8 MTD pct disp", q(D("130000.00") / D("950000.00") * 100, "0.1"), D("13.7"))
chk("F8 YTD var", D("3095801.00") - D("2880000.00"), D("215801.00"))
chk("F8 YTD pct(6dp)", q(D("215801.00") / D("2880000.00"), "0.000001"), D("0.074931"))
chk("F8 YTD pct disp", q(D("215801.00") / D("2880000.00") * 100, "0.1"), D("7.5"))

# ---- F9: KPIs -------------------------------------------------------------
gp = D("1080000.00") - D("648000.00")
chk("F9 GP", gp, D("432000.00"))
chk("F9 GM%(6dp)", q(gp / D("1080000.00"), "0.000001"), D("0.400000"))
chk("F9 GM disp", q(gp / D("1080000.00") * 100, "0.1"), D("40.0"))
r = D("355000.00") / D("1080000.00")
chk("F9 opex(6dp)", q(r, "0.000001"), D("0.328704"))
chk("F9 opex disp", q(r * 100, "0.1"), D("32.9"))
r = D("3095801.00") / D("12000000.00")
chk("F9 burn(6dp)", q(r, "0.000001"), D("0.257983"))
chk("F9 burn disp", q(r * 100, "0.1"), D("25.8"))
r = (D("1080000.00") - D("950000.00")) / D("950000.00")
chk("F9 growth(6dp)", q(r, "0.000001"), D("0.136842"))
chk("F9 growth disp", q(r * 100, "0.1"), D("13.7"))

# ---- F10/F11: percentage points ------------------------------------------
chk("F10 pp", D("40.0") - D("38.5"), D("1.5"))
wrong = (D("40.0") - D("38.5")) / D("38.5") * 100
chk("F10 wrong-rel = 3.9% (must NOT be produced)", q(wrong, "0.1"), D("3.9"))
chk("F11 pp", D("-1.0") - D("-4.0"), D("3.0"))

# ---- F12: data-quality score ---------------------------------------------
W = 18 * 10 + 10 * 5 + 4 * 2
chk("F12 weight total", W, 238)
ded = D("10") * D("1.0") + D("2") * D("0.5")
chk("F12 deduction", ded, D("11"))
raw = D(100) * (D(1) - ded / D(238))
print(f"      F12 raw score = {raw}")
chk("F12 displayed", q(raw, "1"), D("95"))
chk("F12 row-count recon", 184494 + 8 + 0, 184502)
one_high = q(D(100) * (D(1) - D(10) / D(238)), "1")
chk("F12 guarantee: one failed High displays <= 96", one_high <= D("96"), True)
chk("F12 guarantee: 10/238 = 4.2%", q(D(10) / D(238) * 100, "0.1"), D("4.2"))

# ---- F13: materiality AND test -------------------------------------------
def f13(budget, actual, floor=D("500000"), mpct=D("0.02"), pthr=D("0.05")):
    var = actual - budget
    thr = max(floor, mpct * abs(budget))
    amt_ok = abs(var) >= thr
    pct_ok = abs(var / abs(budget)) >= pthr if budget != 0 else False
    return var, thr, amt_ok, pct_ok, (amt_ok and pct_ok)

var, thr, amt, pct, raised = f13(D("10000000.00"), D("10540000.00"))
chk("F13a var", var, D("540000.00"))
chk("F13a pct disp", q(var / D("10000000.00") * 100, "0.1"), D("5.4"))
chk("F13a threshold", thr, D("500000"))
chk("F13a raised", raised, True)
var, thr, amt, pct, raised = f13(D("1000000.00"), D("1060000.00"))
chk("F13b var", var, D("60000.00"))
chk("F13b threshold", thr, D("500000"))
chk("F13b raised (AND fails)", raised, False)
var, thr, amt, pct, raised = f13(D("40000000.00"), D("40900000.00"))
chk("F13c var", var, D("900000.00"))
chk("F13c pct disp", q(var / D("40000000.00") * 100, "0.01"), D("2.25"))
chk("F13c threshold", thr, D("800000"))
chk("F13c raised (pct fails)", raised, False)

# ---- F14: forecast arithmetic --------------------------------------------
rem = D("12000000.00") - D("9300000.00")
chk("F14a remaining", rem, D("2700000.00"))
chk("F14a per-period", rem / 3, D("900000.00"))
s = D("1080000.00") + D("1020500.55") + D("995300.45")
chk("F14b sum", s, D("3095801.00"))
avg = s / 3
print(f"      F14b avg full = {avg}")
chk("F14b avg display", q(avg, "0.01"), D("1031933.67"))
sc = avg * D("1.05")
chk("F14c scenario display", q(sc, "0.01"), D("1083530.35"))
e1 = D("1080000.00") - D("1050000.00")
e2 = D("1020500.55") - D("1032500.55")
e3 = D("995300.45") - D("989300.45")
chk("F14d signed errors", [e1, e2, e3], [D("30000.00"), D("-12000.00"), D("6000.00")])
bias = (e1 + e2 + e3) / 3
chk("F14d bias", bias, D("8000.00"))
t1 = D("30000") / D("1080000.00")
t2 = D("12000") / D("1020500.55")
t3 = D("6000") / D("995300.45")
chk("F14d term1 (6dp)", q(t1, "0.000001"), D("0.027778"))
chk("F14d term2 (6dp)", q(t2, "0.000001"), D("0.011759"))
chk("F14d term3 (6dp)", q(t3, "0.000001"), D("0.006028"))
m = (t1 + t2 + t3) / 3
print(f"      F14d MAPE raw = {m}")
chk("F14d MAPE displayed", q(m * 100, "0.1"), D("1.5"))
# doc's own rounded-term mean must also give 1.5%
mr = (D("0.027778") + D("0.011759") + D("0.006028")) / 3
chk("F14d MAPE from doc-rounded terms", q(mr * 100, "0.1"), D("1.5"))

# ---- F7 sanity on rolling-12 average full precision claim ------------------
# Doc writes "962,983.416666..." (truncated expansion of 962983 + 5/12). Verify truncation.
from decimal import ROUND_DOWN
trunc = (tot / 12 * D(1000000)).to_integral_value(rounding=ROUND_DOWN) / D(1000000)
chk("F7 avg truncated to 6dp = 962983.416666", trunc, D("962983.416666"))
chk("F7 avg exact = 962983 + 5/12", tot / 12 == D(11555801) / 12, True)

print()
print(f"TOTAL CHECKS: {CHECKS}  MISMATCHES: {len(FAILS)}")
for f in FAILS:
    print("  FAIL:", f)
