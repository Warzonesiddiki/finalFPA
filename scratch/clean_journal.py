"""One-off: strip the rows that the test suite appended to the REAL journal.

Subprocess tests resolved ROOT from the script location rather than the fixture, so
they wrote into the production journal. Kept set is pinned by id, not by pattern, so
this cannot quietly drop a real entry.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
KEEP = {f"M-{i:04d}" for i in range(1, 16)}
p = pathlib.Path("memory/journal/memory.jsonl")
rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
keep = [r for r in rows if r["id"] in KEEP]
dropped = [r for r in rows if r["id"] not in KEEP]
# Falsification: the kept set is exactly the seeded set, in order, no duplicates.
assert [r["id"] for r in keep] == sorted(KEEP), [r["id"] for r in keep]
p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in keep) + "\n",
             encoding="utf-8", newline="\n")
print(f"dropped {len(dropped)} leaked rows; {len(keep)} seeded entries remain")
