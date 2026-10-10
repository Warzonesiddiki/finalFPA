#!/usr/bin/env python3
"""The verification queue: who verifies what, how long it has waited, and who should.

Why
---
`LEAD-02` was raised on the claim that "20 handoffs were waiting for a verifier while seats had
claimable work". Measured, it is worse, and the shape of it is the interesting part:

* 26 handoffs handed off and never verified, **median wait 316 min (5.3 h)**, max 415 min;
* verification was performed by **two** seats — `antigravity` (11) and `buffy` (1);
* `antigravity` is **AWAY**: its quota ended on 2026-10-05.

So the whole team's verification duty rested on one active seat and one seat with no quota. That
is not a discipline problem. Verification had become a *role* held by the two oldest seats rather
than a *duty* every seat carries, and when one went away the function did not redistribute.

This script makes the duty visible and rotates it:

```bash
python scripts/verification_queue.py                 # the queue, oldest first, with wait times
python scripts/verification_queue.py --stats         # who verifies, and the concentration risk
python scripts/verification_queue.py --for hermes    # what this seat should verify next
python scripts/verification_queue.py --json          # for the watchdog
```

Rules it enforces, each because breaking it produced a real failure here:

1. **Never assign to an AWAY seat.** Assigning to `antigravity` would look like a fair rotation
   and produce nothing.
2. **Never assign a handoff to its author.** A self-verification is not a verification; `team.py
   verify` requires a different agent, and the queue must not propose what the tool forbids.
3. **Least-recently-verified first.** Pure FIFO on handoff age starves the newest seat forever and
   loads the same two people forever. LRU on *verifier* recency is what breaks the concentration.
4. **A service level, not a hope.** `--sla` (default 30 min, matching the watchdog's escalation
   threshold) marks breaches so the queue has a definition of late rather than a feeling of it.

Stdlib only. Reuses `team.py`'s loaders rather than re-reading the board.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import team  # noqa: E402

DEFAULT_SLA_MIN = 30.0

# `team.py` hands back plain dicts from JSON and YAML-ish sources, so these are the
# shapes we work with. Naming them keeps the signatures readable and satisfies the
# generic-dict type check without pretending to more structure than exists.
Row = dict[str, Any]
Cfg = dict[str, Any]

TS_RE = re.compile(r"handed off: ([0-9TZ:-]+)")
AUTHOR_RE = re.compile(r"author: `([^`]+)`")
VERIFIED_RE = re.compile(r"^### Verified by `([^`]+)`", re.M)
CLAIM_RE = re.compile(r"claim: `([^`]+)`")
CARDS_RE = re.compile(r"task: `([^`]+)`")


def parse_ts(ts: str) -> datetime | None:
    """Timestamps appear at second and minute precision; accept both."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _now() -> datetime:
    return datetime.now(UTC)


def waiting_handoffs(now: datetime | None = None) -> list[Row]:
    """Handoffs that were handed off, never verified, and not rejected.

    A rejected handoff is not in the queue: it is not waiting for a verifier, it is waiting for
    its author to re-do the work. Counting those as "waiting" would inflate the bottleneck and
    hide the real one.
    """
    now = now or _now()
    rejected = team.rejected_handoffs()
    out: list[Row] = []
    for hid, (_num, suffix, path) in sorted(team.handoff_index().items()):
        if hid in rejected:
            continue
        text = team.read_handoff_text(path)
        if VERIFIED_RE.search(text):
            continue
        handed = TS_RE.search(text)
        if not handed:
            continue
        at = parse_ts(handed.group(1))
        if at is None:
            continue
        author = (AUTHOR_RE.search(text) or [None, None])[1]
        card = (CARDS_RE.search(text) or [None, None])[1]
        claim = (CLAIM_RE.search(text) or [None, None])[1]
        out.append(
            {
                "id": hid,
                "card": card or suffix.upper(),
                "author": author,
                "claim": claim,
                "handed_off": at,
                "wait_min": (now - at).total_seconds() / 60.0,
                "path": path,
            }
        )
    out.sort(key=lambda r: -r["wait_min"])  # oldest first
    return out


def verification_history() -> dict[str, list[datetime]]:
    """agent -> when they verified, newest last."""
    hist: dict[str, list[datetime]] = {}
    for _num, _suffix, path in sorted(team.handoff_index().values()):
        text = team.read_handoff_text(path)
        m = VERIFIED_RE.search(text)
        if not m:
            continue
        handed = TS_RE.search(text)
        at = parse_ts(handed.group(1)) if handed else None
        hist.setdefault(m.group(1), []).append(at or datetime.min.replace(tzinfo=UTC))
    for v in hist.values():
        v.sort()
    return hist


def verifier_load() -> dict[str, int]:
    return {a: len(v) for a, v in verification_history().items()}


def eligible(seat: str, row: Row, cfg: Cfg) -> str:
    """Why this seat cannot verify this handoff. Empty string means eligible."""
    away = cfg.get("away") or {}
    if seat in away:
        return f"AWAY ({away[seat]})"
    if seat == row["author"]:
        return "is the author"
    if seat not in (cfg.get("agents") or []):
        return "not a configured seat"
    return ""


def propose(queue: list[Row], cfg: Cfg, sla_min: float = DEFAULT_SLA_MIN) -> list[Row]:
    """Assign each waiting handoff to a verifier: LRU on verifier recency, never the author."""
    hist = verification_history()
    seats = [a for a in (cfg.get("agents") or []) if a not in (cfg.get("away") or {})]
    last_used = {a: (hist[a][-1] if hist.get(a) else None) for a in seats}
    load = {a: len(hist.get(a, [])) for a in seats}
    out: list[Row] = []
    for row in queue:
        candidates = [
            (last_used[a] is not None, last_used[a] or datetime.min.replace(tzinfo=UTC), a)
            for a in seats
            if not eligible(a, row, cfg)
        ]
        if not candidates:
            out.append({**row, "verifier": None, "reason": "no eligible seat"})
            continue
        # A seat that has never verified anything comes first (False sorts before True), then
        # least recently used, then least loaded, then name. Sorting on `c[0]` ascending is what
        # spreads the duty; sorting descending - which reads more naturally - would keep handing
        # everything to the two seats that already do all the work.
        candidates.sort(key=lambda c: (c[0], c[1], load[c[2]], c[2]))
        chosen = candidates[0][2]
        last_used[chosen] = row["handed_off"]
        load[chosen] += 1
        out.append(
            {
                **row,
                "verifier": chosen,
                "breach": row["wait_min"] > sla_min,
                "reason": f"wait {row['wait_min']:.0f} min"
                + (" — OVER SLA" if row["wait_min"] > sla_min else ""),
            }
        )
    return out


def stats(cfg: Cfg) -> dict[str, Any]:
    load = verifier_load()
    agents = list(cfg.get("agents") or [])
    away = cfg.get("away") or {}
    queue = waiting_handoffs()
    waits = sorted(r["wait_min"] for r in queue)
    authors = {r["author"] for r in queue} | set(load)
    return {
        "waiting": len(queue),
        "median_wait_min": round(waits[len(waits) // 2], 1) if waits else 0.0,
        "max_wait_min": round(max(waits), 1) if waits else 0.0,
        "over_sla": sum(1 for w in waits if w > DEFAULT_SLA_MIN),
        "seats": len(agents),
        "away": sorted(away),
        "distinct_verifiers": len(load),
        "load": dict(sorted(load.items(), key=lambda kv: -kv[1])),
        "load_concentration": (max(load.values()) / sum(load.values())) if load else 0.0,
        "never_verified": sorted(a for a in agents if a not in load),
        "authors_who_never_verify": sorted(a for a in authors if a and a not in load),
    }


def render_queue(rows: list[Row], sla_min: float) -> str:
    out = [
        f"verification queue — {len(rows)} handoff(s) handed off, never verified, not rejected",
        f"service level: {sla_min:.0f} min",
        "",
        f"{'HANDOFF':9} {'CARD':9} {'AUTHOR':13} {'WAIT':>7}  {'SHOULD VERIFY':14} NOTE",
    ]
    for r in rows:
        wait = f"{r['wait_min']:.0f}m"
        who = r.get("verifier") or "-"
        note = r.get("reason", "")
        if r.get("breach"):
            note += "  BREACH"
        out.append(f"{r['id']:9} {r['card']:9} {str(r['author']):13} {wait:>7}  {who:14} {note}")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="verification_queue.py",
        description="Who should verify what, how long it has waited, and who is carrying the load.",
    )
    ap.add_argument("--for", dest="seat", help="show only what this seat should verify next")
    ap.add_argument("--stats", action="store_true", help="verifier load and concentration")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--sla", type=float, default=DEFAULT_SLA_MIN, help="service level in minutes")
    args = ap.parse_args(argv)

    cfg = team.config()
    queue = waiting_handoffs()
    rows = propose(queue, cfg, args.sla)

    if args.seat:
        away = cfg.get("away") or {}
        if args.seat in away:
            print(f"{args.seat} is AWAY: {away[args.seat]}")
            return 1
        if args.seat not in (cfg.get("agents") or []):
            print(f"{args.seat}: not a configured seat in team/config.json")
            return 1
        mine = [r for r in rows if r.get("verifier") == args.seat]
        if not mine:
            print(f"{args.seat}: nothing assigned right now")
            return 0
        print(f"{args.seat} — verify these next, in order:")
        for r in mine:
            print(f"  {r['id']:9} {r['card']:9} by {r['author']:13} waiting {r['wait_min']:.0f}m")
        return 0

    if args.json:
        print(
            json.dumps(
                {
                    "stats": stats(cfg),
                    "queue": [
                        {
                            k: (v.isoformat() if isinstance(v, datetime) else v)
                            for k, v in r.items()
                            if k != "path"
                        }
                        for r in rows
                    ],
                },
                indent=2,
            )
        )
        return 0

    if args.stats:
        s = stats(cfg)
        print(f"waiting for a verifier:        {s['waiting']}")
        print(f"median wait:                   {s['median_wait_min']:.0f} min")
        print(f"max wait:                      {s['max_wait_min']:.0f} min")
        print(f"over SLA ({DEFAULT_SLA_MIN:.0f} min):            {s['over_sla']}")
        print()
        print(f"seats: {s['seats']}  away: {', '.join(s['away']) or 'none'}")
        print(f"distinct verifiers:            {s['distinct_verifiers']}")
        print(
            f"load concentration:            {s['load_concentration']:.0%} "
            f"({'CONCENTRATED' if s['load_concentration'] > 0.6 else 'ok'})"
        )
        print()
        print("load:")
        for who, n in s["load"].items():
            flag = "  <- AWAY" if who in (cfg.get("away") or {}) else ""
            print(f"  {who:14} {n:3}{flag}")
        print()
        print("never verified anything:", ", ".join(s["never_verified"]) or "none")
        print("authors who never verify:", ", ".join(s["authors_who_never_verify"]) or "none")
        return 0

    print(render_queue(rows, args.sla))
    print(
        f"seats: {len(cfg.get('agents') or [])}  away: "
        f"{', '.join(sorted(cfg.get('away') or {})) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
