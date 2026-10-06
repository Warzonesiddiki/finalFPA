"""Print the rejection block of every rejected handoff, truncated for triage."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HD = ROOT / "team" / "handoffs"

for p in sorted(HD.glob("*.md")):
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^### Rejected by .*$", text, re.M)
    if not m:
        continue
    body = text[m.start():].strip()
    body = re.sub(r"\s+", " ", body)
    print("=" * 100)
    print(p.name)
    print(body[:900])
    print()
