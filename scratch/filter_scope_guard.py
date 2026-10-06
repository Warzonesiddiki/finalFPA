"""Narrow the out-of-scope warn to files that no other live claim covers.

First run flagged 21 extra cases, most of them legitimate: a file another agent was
claiming at the time, or a leader-only file. The signal I want is "a file nobody claimed
was written during someone's claim window" - that is the case no other guard can catch.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
Q = chr(34)

p = pathlib.Path("scripts/team.py")
src = p.read_text(encoding="utf-8")

old = ("        allowed = [s.rstrip(" + Q + "/" + Q + ") for s in claim.get(" + Q + "scopes" + Q + ", [])]" + NL
       + "        stray = sorted(" + NL
       + "            w for w in _window_edits(start, end, None)" + NL
       + "            if w not in declared" + NL
       + "            and not any(w == s or w.startswith(s + " + Q + "/" + Q + ") for s in allowed)" + NL
       + "        )")
assert src.count(old) == 1, "stray anchor"

new = (
    "        allowed = [s.rstrip(" + Q + "/" + Q + ") for s in claim.get(" + Q + "scopes" + Q + ", [])]" + NL
    + "        # files another live claim already covers are that agent's work, not a stray" + NL
    + "        others = [s.rstrip(" + Q + "/" + Q + ")" + NL
    + "                 for c in cs if c.get(" + Q + "claim_id" + Q + ") != claim.get(" + Q + "claim_id" + Q + ")" + NL
    + "                 for s in c.get(" + Q + "scopes" + Q + ", []) if not has_glob(s)]" + NL
    + "        leader_paths = [s.rstrip(" + Q + "/" + Q + ") for s in cfg.get(" + Q + "leader_only_paths" + Q + ", [])]" + NL
    + "        covered = allowed + others + leader_paths" + NL
    + "        stray = sorted(" + NL
    + "            w for w in _window_edits(start, end, None)" + NL
    + "            if w not in declared" + NL
    + "            and not any(w == s or w.startswith(s + " + Q + "/" + Q + ") for s in covered)" + NL
    + "        )"
)
src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8", newline="")
print("stray filter narrowed")
