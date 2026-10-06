"""Add the out-of-scope write guard that hermes' UX-03 handoff exposed.

`_window_edits` filtered by the claim's scopes, so a write *outside* them was invisible:
hermes held a claim scoped to `evidence/ux/screen-conformance.md` and created two scripts in
`scripts/` in the same minutes - undeclared, unclaimed, untracked. "One writer per path"
only means something if the paths outside your claim are policed too.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
Q = chr(34)
S = chr(39)
DQ = Q * 2          # two quotes
TPQ = Q * 3         # three quotes

tp = pathlib.Path("scripts/team.py")
src = tp.read_text(encoding="utf-8")

# 1. scopes become optional, so the window can be scanned tree-wide
old_sig = "def _window_edits(start, end, scopes: list[str]) -> list[str]:"
if old_sig in src:
    src = src.replace(old_sig, "def _window_edits(start, end, scopes: list[str] | None = None) -> list[str]:", 1)
    print("signature updated")
else:
    print("signature already optional")

old_hit = "        if not _scope_hit(rel, scopes):" + NL + "            continue"
if old_hit in src:
    new_hit = ("        # scopes=None means the whole tree: that is how out-of-scope writes are found"
               + NL
               + "        if scopes is not None and not _scope_hit(rel, scopes):" + NL
               + "            continue")
    src = src.replace(old_hit, new_hit, 1)
    tp.write_text(src, encoding="utf-8", newline="")
    print("scope filter made optional")
else:
    print("scope filter already optional")

# 2. the check itself
src = tp.read_text(encoding="utf-8")
if "OUTSIDE the claimed scopes" in src:
    print("out-of-scope check already present")
    raise SystemExit(0)

marker = "        for pth in sorted(_declared_changed(text)):"
assert src.count(marker) == 1, "declared-path loop anchor"
block = [
    "        # A write inside the claim window but OUTSIDE the claimed paths is worse than an",
    "        # undeclared one: it is nobody's work, so no guard can see it. (hermes' UX-03 wrote",
    "        # two scripts in scripts/ under a claim scoped to evidence/.)",
    "        allowed = [s.rstrip(" + Q + "/" + Q + ") for s in claim.get(" + Q + "scopes" + Q + ", [])]",
    "        stray = sorted(",
    "            w for w in _window_edits(start, end, None)",
    "            if w not in declared",
    "            and not any(w == s or w.startswith(s + " + Q + "/" + Q + ") for s in allowed)",
    "        )",
    "        if stray:",
    "            (fails if args.strict else warns).append(",
    "                f" + TPQ + "{f.name}: {len(stray)} file(s) written inside the claim window but OUTSIDE the "
    "claimed" + TPQ + NL
    + "                f" + TPQ + " scopes: {S.join(stray[:5])}{Q + chr(44) + Q + "  # " + Q + "{S.join(stray[:5])}" + TPQ + ")",
    "            )",
    "",
    marker,
]
src = src.replace(marker, NL.join(block), 1)
tp.write_text(src, encoding="utf-8", newline="")
print("out-of-scope write check added")
