"""Splice a clean tick-summary log statement into scripts/team_watchdog.py.

The line-based repair exists because the previous statement was mangled in transit;
this file is written with write_file (which preserves quoting) and applied with plain
line surgery, then the result is compiled and tested.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
DQ = chr(34)

TARGET = pathlib.Path("scripts/team_watchdog.py")
lines = TARGET.read_text(encoding="utf-8").splitlines()

start = None
for idx, line in enumerate(lines):
    if line.strip().startswith("summary = ("):
        start = idx
        break
if start is None:
    raise SystemExit("anchor not found: no summary = ( line")

end = None
for idx in range(start, len(lines)):
    if lines[idx].strip() == "log(summary)":
        end = idx
        break
if end is None:
    raise SystemExit("anchor not found: no log(summary) line")

q = DQ
block = [
    "    took = time.monotonic() - t0",
    "    tick_no = st[" + q + "ticks" + q + "]",
    "    n_active = s[" + q + "active_claims" + q + "]",
    "    n_todo = s[" + q + "todo_count" + q + "]",
    "    n_actions = len(applied)",
    "    log(f" + q + "tick #{tick_no}: check exit {code_check} ({fails} fail, {warns} warn), " + q,
    "        f" + q + "{n_active} active claim(s), {n_todo} card(s) todo, " + q,
    "        f" + q + "{n_actions} action(s), tick took {took:.1f}s" + q + ")",
]
lines[start:end + 1] = block
TARGET.write_text(chr(10).join(lines) + chr(10), encoding="utf-8", newline="")
print("replaced lines", start + 1, "to", end + 1)
print(chr(10).join(block))
