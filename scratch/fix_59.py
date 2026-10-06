"""Refine docs/33 5.9: the last four TB rows are closure records by design, not untracked work."""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)

p = pathlib.Path("docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md")
doc = p.read_text(encoding="utf-8")

old_start = doc.index("**2. `TB` rows with no live card**")
old_end = doc.index(NL + "## 6. Operating rules")
block = doc[old_start:old_end]

# split: closure/done-log rows (TB-099..TB-102 and the TB-101/102 records) vs real queue rows
queue_rows = [k for k in re.findall(r"TB-\d{3}", block) if int(k.split("-")[1]) < 99]
log_rows = [k for k in re.findall(r"TB-\d{3}", block) if int(k.split("-")[1]) >= 99]

new = (
    "**2. `TB` rows with no live card** - two different situations, deliberately separated:"
    + NL
    + NL
    + "  (a) *real queue rows nobody owns* (" + str(len(queue_rows)) + "): "
    + ", ".join("`" + k + "`" for k in queue_rows) + "."
    + NL
    + "  (b) *closure records* (" + str(len(log_rows)) + "): "
    + ", ".join("`" + k + "`" for k in log_rows)
    + " - these were written as done-log rows (what landed and the measured numbers), not as queue items, so"
    + " having no card is correct by design and must not be \"fixed\" by creating one."
    + NL
    + NL
    + "  For (a) the rule is that a row nobody tracks cannot be claimed, so each is one of three things and must be"
    + NL
    + "  resolved by a decision, not by silence: still real -> `python scripts/team.py sync` creates the card and an"
    + NL
    + "  agent claims it; superseded by a `DEC` (several were closed by `DEC-056`…`059`) -> annotate the row;"
    + NL
    + "  deliberate deferral -> annotate the condition that re-opens it. Follow-up: re-run `sync` for the rows whose"
    + NL
    + "  subject is still unimplemented and annotate the rest."
    + NL
)
doc = doc[:old_start] + new + doc[old_end:]
p.write_text(doc, encoding="utf-8", newline="")
print("queue rows:", len(queue_rows), queue_rows)
print("closure rows:", len(log_rows), log_rows)
