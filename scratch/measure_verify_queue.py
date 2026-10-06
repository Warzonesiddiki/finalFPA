"""Measure the verification bottleneck as it stands right now.

Every number here is computed from the board and the handoff files, so the
"before" figure in the LEAD-02 handoff is measured rather than remembered.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HD = ROOT / "team" / "handoffs"


def parse(ts: str) -> datetime:
    """Timestamps appear at second and minute precision; accept both."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"unrecognised timestamp: {ts!r}")


now = datetime.now(timezone.utc)

rows = []
for p in sorted(HD.glob("*.md")):
    text = p.read_text(encoding="utf-8", errors="replace")
    short = "-".join(p.name.split("-")[:2])
    card = p.stem.split("-", 2)[2].upper() if p.stem.count("-") >= 2 else "?"
    author = (re.search(r"author: `([^`]+)`", text) or [None, "?"])[1]
    opened = re.search(r"opened: ([0-9TZ:-]+)", text)
    handed = re.search(r"handed off: ([0-9TZ:-]+)", text)
    rejected = re.search(r"^### Rejected by", text, re.M)
    verified = re.search(r"^### Verified by `([^`]+)`", text, re.M)
    rows.append(
        {
            "id": short,
            "card": card,
            "author": author,
            "opened": parse(opened.group(1)) if opened else None,
            "handed": parse(handed.group(1)) if handed else None,
            "rejected": bool(rejected),
            "verified_by": verified.group(1) if verified else None,
        }
    )

waiting = [r for r in rows if r["handed"] and not r["verified_by"] and not r["rejected"]]
needs_reverify = [r for r in rows if r["rejected"]]

print(f"handoffs on disk:            {len(rows)}")
print(f"rejected (need a successor): {len(needs_reverify)}")
print(f"handed off, never verified:  {len(waiting)}")
print()
print("=== WAITING FOR A VERIFIER (never verified) ===")
waits = []
for r in sorted(waiting, key=lambda r: r["handed"]):
    mins = (now - r["handed"]).total_seconds() / 60
    waits.append(mins)
    print(f"  {r['id']:8} {r['card']:8} by {r['author']:12} waiting {mins:7.0f} min")
if waits:
    waits.sort()
    print()
    print(f"  median wait  {waits[len(waits)//2]:.0f} min")
    print(f"  mean wait    {sum(waits)/len(waits):.0f} min")
    print(f"  max wait     {max(waits):.0f} min")
    print(f"  over 30 min  {sum(1 for w in waits if w > 30)}")

print()
print("=== VERIFIER LOAD (who verified what) ===")
load: dict[str, int] = {}
for r in rows:
    if r["verified_by"]:
        load[r["verified_by"]] = load.get(r["verified_by"], 0) + 1
for who, n in sorted(load.items(), key=lambda kv: -kv[1]):
    print(f"  {who:14} {n}")
if not load:
    print("  (none)")

authors = {r["author"] for r in rows}
verifiers = set(load)
print()
print(f"authors: {sorted(authors)}")
print(f"distinct verifiers: {sorted(verifiers) or 'NONE'}")
print(f"authors who never verify anything: {sorted(authors - verifiers) or 'none'}")
