"""Repair the mangled warning line in scripts/team.py (one line, line-based surgery)."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
S = chr(39)
Q = chr(34)

p = pathlib.Path("scripts/team.py")
lines = p.read_text(encoding="utf-8").splitlines()
hit = None
for i, l in enumerate(lines):
    if "S.join" in l or "Q + chr(44)" in l:
        hit = i
        break
if hit is None:
    print("nothing to repair")
    raise SystemExit(0)

indent = " " * (len(lines[hit]) - len(lines[hit].lstrip()))
replacement = (
    indent + "f" + Q + " scopes: {" + S + ", " + S + ".join(stray[:5])}" + Q + ")"
)
lines[hit] = replacement
p.write_text(chr(10).join(lines) + chr(10), encoding="utf-8", newline="")
print("repaired line", hit + 1, "->", replacement.strip())
