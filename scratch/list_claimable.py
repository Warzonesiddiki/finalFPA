"""List claimable cards (todo, no open deps) grouped for task assignment."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import team  # noqa: E402

ts = team.tasks()
open_deps = {d for tid, t in ts.items() if t.get("status") != "done"
             for d in (t.get("deps") or []) if d in ts and ts[d].get("status") != "done"}

rows = []
for tid, t in ts.items():
    if t.get("status") != "todo":
        continue
    deps = [d for d in (t.get("deps") or []) if d in open_deps]
    if deps:
        continue
    rows.append((t.get("priority", "P9"), tid, t.get("lane", ""), t.get("title", "")))

rows.sort()
print(f"claimable (todo, no open deps): {len(rows)}")
for prio, tid, lane, title in rows:
    print(f"  {tid:11} {prio:3} {lane:13} {title[:82]}")
