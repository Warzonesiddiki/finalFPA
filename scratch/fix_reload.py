"""Two defects the final check found, fixed at the cause:

1. The running watchdog nudged an `away` seat (antigravity, tick #11). The loop had been
   started before the away feature existed and a long-running process never picks up code
   edits - so the loop now re-execs itself when its own code or config is newer than the
   copy it is running.
2. `team/kickoff/opencode2.md` pointed at `tests/unit/test_cli_commands.py`, which does not
   exist: TB-027 landed `app/cli/` (`__init__.py`, `__main__.py`, `main.py`) but no unit
   test. The kickoff now states what is really on disk and makes the missing test the first
   piece of work.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
Q = chr(34)

# ---------------------------------------------------------------- 1. watchdog self-reload
wp = pathlib.Path("scripts/team_watchdog.py")
src = wp.read_text(encoding="utf-8")

helper = [
    "WATCHED = (ROOT / " + Q + "scripts" + Q + " / " + Q + "team_watchdog.py" + Q + ",",
    "           ROOT / " + Q + "scripts" + Q + " / " + Q + "team.py" + Q + ",",
    "           ROOT / " + Q + "team" + Q + " / " + Q + "config.json" + Q + ")",
    "",
    "",
    "def code_fingerprint() -> tuple:",
    "    " + Q * 3 + "mtime+size of the files this loop depends on. A long-running loop never",
    "    sees a code edit, which is how a running watchdog kept nudging a seat that had just",
    "    been marked away. Comparing before every tick turns that class of bug into a restart." + Q * 3,
    "    out = []",
    "    for p in WATCHED:",
    "        try:",
    "            st = p.stat()",
    "        except OSError:",
    "            out.append((0, 0))",
    "            continue",
    "        out.append((st.st_mtime_ns, st.st_size))",
    "    return tuple(out)",
    "",
    "",
    "def maybe_reload(seen: tuple) -> None:",
    "    now_fp = code_fingerprint()",
    "    if now_fp != seen:",
    "        log(" + Q + "RELOAD: team.py, team_watchdog.py or config.json changed since this loop "
    "started - re-executing to pick it up" + Q + ")",
    "        os.execv(sys.executable, [sys.executable, str(ROOT / " + Q + "scripts" + Q
    + " / " + Q + "team_watchdog.py" + Q + "), *sys.argv[1:]])",
    "",
    "",
]
anchor = "def board_fingerprint() -> str:"
assert src.count(anchor) == 1
src = src.replace(anchor, NL.join(helper) + anchor, 1)

old = "        n += 1" + NL + "        last = tick(dry_run=dry_run)"
assert src.count(old) == 1, "loop body anchor"
new = "        n += 1" + NL + "        maybe_reload(seen)" + NL + "        last = tick(dry_run=dry_run)"
src = src.replace(old, new, 1)

old2 = "def _loop(interval: int, max_ticks: int, dry_run: bool = False) -> int:" + NL + "    cfg = config()"
assert src.count(old2) == 1, "loop header anchor"
new2 = ("def _loop(interval: int, max_ticks: int, dry_run: bool = False) -> int:" + NL
        + "    cfg = config()" + NL + "    seen = code_fingerprint()")
src = src.replace(old2, new2, 1)
wp.write_text(src, encoding="utf-8", newline="")
print("team_watchdog.py: self-reload added")

# ---------------------------------------------------------------- 2. kickoff: real paths
kp = pathlib.Path("team/kickoff/opencode2.md")
k = kp.read_text(encoding="utf-8")
old3 = ("  `app/cli/`, `tests/unit/test_cli_commands.py`. Read\n"
        "  `git status`/`git diff` first")
if old3 in k:
    k = k.replace(old3, "  `app/cli/`. Read\n  `git status`/`git diff` first")
old4 = ("Its scope was `app/cli/` and `tests/unit/test_cli_commands.py`. Read\n"
        "`git status`/`git diff` first — there may be uncommitted work already written.")
new4 = ("Its scope was `app/cli/` **and a unit test `tests/unit/test_cli_commands.py` that does not\n"
        "exist** — the package landed (`app/cli/__init__.py`, `__main__.py`, `main.py`) but the test\n"
        "did not, and the only CLI test in the tree is `tests/integration/test_cli_exceptions.py`.\n"
        "So TB-027 is half-finished: read `git status`/`git diff`, then write the missing\n"
        "`tests/unit/test_cli_commands.py` as your first act on it and say so in the handoff.")
assert old4 in k, "kickoff anchor"
k = k.replace(old4, new4)
kp.write_text(k, encoding="utf-8", newline="")
print("kickoff corrected: TB-027 is half-finished, the unit test is missing")
