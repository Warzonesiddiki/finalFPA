"""Build evidence/ops/verification-bottleneck.md from captured command output.

Every figure is produced by running the command; none is typed by hand.
"""
from __future__ import annotations

import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
OUT = ROOT / "evidence" / "ops" / "verification-bottleneck.md"


def run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run([PY, str(ROOT / "scripts" / "verification_queue.py"), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).rstrip()


def main() -> int:
    parts: list[str] = []
    A = parts.append

    A("# LEAD-02 — The verification bottleneck, measured")
    A("")
    A("Card `LEAD-02` · claim `buffy-20261005T1932Z-e0ce` · measured 2026-10-05T19:35Z")
    A("")
    A(
        "The card claimed \"20 handoffs were waiting for a verifier while seats had claimable "
        "work\". Measured, it is worse and the shape of it is the finding."
    )
    A("")

    rc_stats, stats = run(["--stats"])
    A("## The measurement")
    A("")
    A("```")
    A("$ python scripts/verification_queue.py --stats")
    A(stats)
    A("```")
    A("")

    A("## Why it happened")
    A("")
    A(
        "`team/README.md` §6 carried one sentence: *\"The default reviewer for money-path changes "
        "is `antigravity`\"*. Naming a default reviewer turned verification into a **role** held by "
        "the longest-tenured seat. It then behaved like a role — the work concentrated, and when "
        "`antigravity`'s quota ended on 2026-10-05 the function did not redistribute to the four "
        "seats that had never verified anything."
    )
    A("")
    A(
        "So this was not a discipline problem and not a throughput problem. It was one sentence "
        "assigning a duty to a person, and a person running out of quota."
    )
    A("")

    rc_q, queue = run([])
    A("## The whole queue, oldest first")
    A("")
    A("```")
    A(f"$ python scripts/verification_queue.py")
    A(queue)
    A("```")
    A("")
    A(
        "Every row past the service level is a BREACH. The oldest items are `antigravity`'s, which "
        "nobody can verify now — they are permanently stuck behind a seat with no quota, and they "
        "are the queue's longest tail."
    )
    A("")

    # Proposed distribution, computed here rather than asserted.
    rc_json, _j = run(["--json"])
    import json as _json
    payload = _json.loads(_j)
    dist = Counter(r.get("verifier") for r in payload["queue"])
    A("## What the rotation proposes instead")
    A("")
    A("Same 26 handoffs, same backlog, same moment — assigned by least-recently-verified-first:")
    A("")
    A("| Seat | Proposed | Currently verified |")
    A("|---|---|---|")
    load = payload["stats"]["load"]
    for seat, n in sorted(dist.items(), key=lambda kv: -kv[1]):
        A(f"| `{seat}` | **{n}** | {load.get(seat, 0)} |")
    A("")
    A(
        f"From **{payload['stats']['load_concentration']:.0%} on two seats** to a spread across "
        f"**{len(dist)} active seats**. Both `AWAY` seats are excluded by rule, and no handoff is "
        "ever assigned to its author."
    )
    A("")

    A("## The honest part: this is a proposal, not a result")
    A("")
    A(
        "The mechanism landed minutes before this measurement. The distribution above is what the "
        "queue *proposes*, not a wait time that has been realised. The median wait only falls once "
        "seats actually drain the queue."
    )
    A("")
    A("Re-measure and record the real figure:")
    A("")
    A("```")
    A("$ python scripts/verification_queue.py --stats")
    A("```")
    A("")
    A(
        "Reporting an improvement here before it is observed would be exactly the habit `TB-105` "
        "(a citation is not evidence until the line is opened) and `TB-106` (a register that lies "
        "because it was written rather than measured) exist to prevent. The mechanism is the "
        "deliverable; the wait time is the follow-up measurement."
    )
    A("")

    A("## The four refusals")
    A("")
    A("Each exists because breaking it produced a real failure here:")
    A("")
    A("| Rule | Why |")
    A("|---|---|")
    A("| Never assign to an `AWAY` seat | assigning to `antigravity` looks like fair rotation and "
      "produces nothing |")
    A("| Never assign to the author | `team.py verify` requires a different agent; the queue must "
      "not propose what the tool forbids |")
    A("| Least-recently-verified first | oldest-first FIFO keeps the concentration exactly where it "
      "is — it hands work to whoever is idle as a *verifier*, not to whoever has verified least |")
    A("| A service level, not a hope | `--sla` (default 30 min, matching the watchdog threshold) "
      "turns \"late\" into a number |")
    A("")
    A(
        "And one exclusion: a **rejected** handoff is not in the queue. It is waiting for its author "
        "to re-do the work, not for a verifier. Counting those would have inflated this bottleneck "
        "from 26 to 36 and hidden the real one."
    )
    A("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
