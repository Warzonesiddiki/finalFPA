"""INT-01 — reconcile docs/33 (spec of record) with the live team board.

Measured drift, both directions, and the fix on the docs/33 side (the leader is the only
writer of that file). The board is deliberately a subset of the spec, so "card without a
row" is not drift; "row nobody tracks" and "card done but row still reads open" are.
"""
import pathlib
import re
import sys

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
import team  # noqa: E402

doc_path = pathlib.Path("docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md")
doc = doc_path.read_text(encoding="utf-8")

rows = {}
for m in re.finditer(r"^\|\s*`?(TB-\d{3})`?\s*\|\s*([^|]*)\|", doc, re.M):
    rows[m.group(1)] = " ".join(m.group(2).split())

cards = {k: v for k, v in team.tasks().items() if k.startswith("TB-")}
untracked = sorted(set(rows) - set(cards))
orphan_cards = sorted(set(cards) - set(rows))
done_not_marked = [k for k in sorted(set(rows) & set(cards))
                   if cards[k].get("status") == "done"
                   and "✅" not in rows[k] and "CLOSED" not in rows[k].upper()
                   and k not in ("TB-033", "TB-048")]

lines = [
    "",
    "### 5.9 Board reconciliation — `INT-01` (2026-10-05)",
    "",
    f"`docs/33` is the spec of record; `team/taskboard.md` is the board that actually runs the work. Measured this",
    f"session: **{len(rows)} `TB` rows** in this file, **{len(cards)} live `TB` cards**, and",
    f"**{len(orphan_cards)} cards with no row here** — the board is a deliberate subset of the spec, which is the",
    "healthy direction. Two kinds of drift do need fixing, and both are recorded here rather than left implicit.",
    "",
    "**1. Cards verified `done` whose row here still reads open** (a reader of this file would think the work is",
    "outstanding):",
    "",
]
for k in done_not_marked:
    t = cards[k].get("title", "")
    lines.append(f"- `{k}` — {t[:96]}{'…' if len(t) > 96 else ''} → **closed 2026-10-05**, evidence in the card's handoff.")
lines += [
    "",
    f"**2. `TB` rows with no live card** ({len(untracked)}): "
    + ", ".join(f"`{k}`" for k in untracked)
    + ".",
    "  These rows exist in the spec of record but nothing on the board tracks them, so nobody owns them and they",
    "  cannot be claimed. They are one of three things and must be resolved by a decision, not by silence:",
    "  (a) still real → `python scripts/team.py sync` creates the card and an agent claims it;",
    "  (b) superseded by a `DEC` (several were closed by `DEC-056`…`059`) → the row is annotated as superseded;",
    "  (c) deliberate deferral → the row is annotated with the condition that re-opens it.",
    "  Proposed handling: re-run `team.py sync` for the rows whose subject is still unimplemented, and annotate the",
    "  rest. This section is the audit trail; the row-level wording is the follow-up.",
    "",
]
section = NL.join(lines)
anchor = NL + "## 6. Operating rules (how the board is followed)"
assert doc.count(anchor) == 1, "anchor"
if "### 5.9 Board reconciliation" not in doc:
    doc = doc.replace(anchor, section + anchor)
    doc_path.write_text(doc, encoding="utf-8", newline="")
    print("docs/33 5.9 written")
else:
    print("already present")
print("untracked rows:", len(untracked), untracked)
print("done-not-marked:", done_not_marked)
print("cards without a row:", orphan_cards)
