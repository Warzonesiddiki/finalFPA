"""Make a tick cheap enough for a 20-minute cadence.

Measured: a tick costs ~143 s, most of it in the three subprocesses it spawns
(`team.py check`, `board`, `digest`). The board only changes when a task or claim
file changes, so the fingerprint below skips the two render passes when nothing moved.
`check` still runs every tick - that is the part that must never be skipped.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
DQ = chr(34)

TARGET = pathlib.Path("scripts/team_watchdog.py")
src = TARGET.read_text(encoding="utf-8")

helper = [
    "def board_fingerprint() -> str:",
    "    " + DQ + DQ + DQ + "Cheap change-detector for the generated views: mtime+size of every",
    "    task and claim file. The board and digest only change when one of these moves." + DQ + DQ,
    "    h = hashlib.sha256()",
    "    for p in sorted(list(team.TASKS.glob(" + DQ + "*.json" + DQ + ")) + list(team.CLAIMS.glob(" + DQ + "*.json" + DQ + "))):",
    "        try:",
    "            st = p.stat()",
    "        except OSError:",
    "            continue",
    "        h.update(f" + DQ + "{p.name}:{st.st_mtime_ns}:{st.st_size}" + DQ + ".encode())",
    "    return h.hexdigest()[:16]",
    "",
    "",
]

anchor = "def pid_alive(pid: int) -> bool:"
assert src.count(anchor) == 1
src = src.replace(anchor, chr(10).join(helper) + anchor, 1)

old = (
    "    if cfg.get(" + chr(34) + "autostart_board" + chr(34) + "):"
)
assert src.count(old) == 1, "autostart anchor"
new = (
    "    fingerprint = board_fingerprint()"
    + chr(10)
    + "    if cfg.get(" + chr(34) + "autostart_board" + chr(34) + ") and fingerprint != st.get("
    + chr(34) + "board_fingerprint" + chr(34) + "):"
)
src = src.replace(old, new, 1)

# record the fingerprint so the next tick can compare, and say whether it re-rendered
a = '    st["last_tick_utc"] = stamp()'
assert src.count(a) == 1
src = src.replace(a, a + chr(10) + '    st["board_fingerprint"] = board_fingerprint()', 1)

b = '        "all_done": s["all_done"],'
assert src.count(b) == 1
src = src.replace(b, b + chr(10) + '        "board_fingerprint": st.get("board_fingerprint"),', 1)

if "import hashlib" not in src:
    src = src.replace("import json" + chr(10), "import hashlib" + chr(10) + "import json" + chr(10), 1)

TARGET.write_text(src, encoding="utf-8", newline="")
print("patched: board/digest only re-render when a task or claim file moved")
