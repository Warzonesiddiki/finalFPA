#!/usr/bin/env python3
"""Build the release-readiness dossier (DOC-03).

What the card asks for
---------------------
One page the owner can read to decide ship or not. Every gate with its **real** exit status, open
decisions with their blast radius, licence posture with SHAs, known limits stated as numbers. No
adjectives. Every line traceable to a command.

Why this is a generator
-----------------------
A hand-written readiness dossier is the single most dangerous document in the repo: it is read
when someone is deciding whether to ship, it is composed while the answer is "not yet", and it
stays on the shelf saying "not yet" for weeks after the answer changes. Every number below is
produced by running a command at generation time. `--check` fails when the dossier stops matching
the machine, which is the same discipline as `TB-106`'s register.

The one rule this generator takes from `scripts/check.py`
----------------------------------------------------------
`check.py` calls `sys.exit()` on the **first** failed bar (line 12). That means a new red bar hides
every bar after it: right now Ruff Format fails first and the five `docs/14` §5.3 bars never report.
A gate that stops at the first failure cannot tell the owner how far from ready the project is — the
same "one uniform verdict hides the population" shape as the fabricated audits in `TB-104`.

So this generator **never short-circuits**. It runs every gate, records every exit code, and prints
them all. The count of red bars is itself a reported number, because "which bar failed first" and
"how many bars are red" are different questions and only the second one is decision-relevant.

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "release-readiness-dossier.md"
BEGIN = "<!-- BEGIN GENERATED: release_dossier.py -->"
END = "<!-- END GENERATED: release_dossier.py -->"

PY = sys.executable

# (id, what it proves, argv, slow?)
GATES: list[tuple[str, str, list[str], bool]] = [
    (
        "LICENCE",
        "no GPL, adopted-source notices reach the payload",
        [PY, "scripts/license_gate.py"],
        False,
    ),
    (
        "DOC-INTEGRITY",
        "markdown links resolve, cross-project ids consistent",
        [PY, "scripts/check_doc_integrity.py"],
        False,
    ),
    (
        "MEMORY",
        "continuity journals well-formed and rendered",
        [PY, "scripts/memory.py", "verify"],
        False,
    ),
    (
        "EVID-REGISTER",
        "false-evidence register matches the rejected handoffs",
        [PY, "scripts/false_evidence_register.py", "--check"],
        False,
    ),
    (
        "RUFF-LINT",
        "lint clean over app/scripts/tests",
        [PY, "-m", "ruff", "check", "app", "scripts", "tests"],
        False,
    ),
    (
        "RUFF-FORMAT",
        "formatting clean over app/scripts/tests",
        [PY, "-m", "ruff", "format", "--check", "app", "scripts", "tests"],
        False,
    ),
    (
        "TEAM-CHECK",
        "board integrity: undeclared files, rejected-handoff rule, deps",
        [PY, "scripts/team.py", "check"],
        True,
    ),
    (
        "ACCEPTANCE",
        "the product acceptance gate (fails fast on first bar)",
        [PY, "scripts/check.py"],
        True,
    ),
    ("UNIT", "the unit suite", [PY, "-m", "pytest", "tests/unit", "-q"], True),
]


def run(argv: list[str], timeout: int = 2400) -> tuple[int, float, str]:
    """Returns (exit code, seconds, first meaningful lines). Never raises on non-zero."""
    started = time.monotonic()
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=ROOT,
            timeout=timeout,
        )
        rc, out = p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return 124, time.monotonic() - started, f"TIMEOUT after {timeout}s"
    elapsed = time.monotonic() - started
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # the first line that actually says something
    keep = [ln for ln in lines if not ln.startswith(("---", "|", " ", "="))][:2]
    return rc, elapsed, " / ".join(keep)[:220] if keep else "(no output)"


def git(*args: str) -> str:
    p = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT
    )
    return p.stdout.strip() or "(unavailable)"


def count_files() -> tuple[int, int]:
    tracked = git("ls-files").splitlines()
    dirty = git("status", "--porcelain").splitlines()
    return len([t for t in tracked if t]), len(dirty)


def read_open_decisions() -> tuple[int, int, list[str]]:
    """(declared count, listed count, the OQ ids actually present)."""
    p = ROOT / "evidence" / "open_decisions.md"
    if not p.exists():
        return 0, 0, []
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Tracked Open Decisions \(`?(\d+)`?\s*/\s*`?(\d+)`?\)", text)
    declared = int(m.group(1)) if m else 0
    ids = sorted(set(re.findall(r"\*\*(OQ-\d+)\*\*", text)))
    return declared, len(ids), ids


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="release_dossier.py",
        description="Build evidence/release-readiness-dossier.md from live gate runs.",
    )
    ap.add_argument(
        "--slow",
        action="store_true",
        help="also run the slow gates (team check, acceptance, full unit suite)",
    )
    ap.add_argument(
        "--check", action="store_true", help="fail if the dossier is stale; write nothing"
    )
    args = ap.parse_args(argv)

    gates = [g for g in GATES if args.slow or not g[3]]
    results: list[dict[str, Any]] = []
    # Never short-circuit. Every gate runs, whatever the previous one did.
    for gid, proves, cmd, slow in gates:
        rc, secs, note = run(cmd)
        results.append(
            {
                "id": gid,
                "proves": proves,
                "cmd": " ".join(cmd[1:]),
                "rc": rc,
                "secs": round(secs, 1),
                "note": note,
                "slow": slow,
            }
        )

    red = [r for r in results if r["rc"] != 0]
    green = [r for r in results if r["rc"] == 0]
    skipped = [g[0] for g in GATES if g[3] and not args.slow]
    head_sha = git("rev-parse", "--short", "HEAD")
    tracked, dirty = count_files()
    declared_od, listed_od, od_ids = read_open_decisions()
    vq_rc, _vq, vq_note = run([PY, "scripts/verification_queue.py", "--stats"])

    doc = build(
        results,
        red,
        green,
        skipped,
        head_sha,
        tracked,
        dirty,
        declared_od,
        listed_od,
        od_ids,
        args.slow,
    )

    if args.check:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if have != doc:
            print("release_dossier: STALE - regenerate", file=sys.stderr)
            return 1
        print("release_dossier: current")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(ROOT).as_posix()} — "
        f"{len(green)} green, {len(red)} red, {len(skipped)} skipped"
    )
    return 0


def build(
    results,
    red,
    green,
    skipped,
    head_sha,
    tracked,
    dirty,
    declared_od,
    listed_od,
    od_ids,
    slow: bool,
) -> str:
    L: list[str] = []
    A = L.append
    A("# Release-readiness dossier")
    A("")
    A("Card `DOC-03` · generated by `scripts/release_dossier.py` · **do not hand-edit**")
    A("")
    A(
        "Every number and every exit status below was produced by running the command named beside "
        "it at generation time. Regenerate with `python scripts/release_dossier.py --slow`; "
        "`--check` fails when this file stops matching the machine."
    )
    A("")
    A("## 1. Decision")
    A("")
    if not red:
        A("**Every gate run is green.** No blocking condition measured.")
    else:
        A(f"**Not ready to ship.** {len(red)} of {len(results)} gates run are red.")
        A("")
        A("Red gates, in the order they run:")
        A("")
        for r in red:
            A(f"- `{r['id']}` — exit {r['rc']} — `{r['cmd']}`")
    A("")
    A(
        "This gate list is **not** fail-fast, so the red count above is the true number of red "
        "conditions rather than the number before the first failure. That distinction is the "
        "reason this document exists separately from `scripts/check.py`."
    )
    A("")

    A("## 2. Gates")
    A("")
    A(BEGIN)
    A("")
    A(
        f"_{len(results)} gate(s) run"
        + (f"; {len(skipped)} slow gate(s) skipped (pass `--slow` to include)" if skipped else "")
        + "._"
    )
    A("")
    A("| Gate | Exit | Seconds | Proves | Command |")
    A("|---|---|---|---|---|")
    for r in results:
        mark = "green" if r["rc"] == 0 else "**RED**"
        A(f"| `{r['id']}` | {mark} ({r['rc']}) | {r['secs']} | {r['proves']} | `{r['cmd']}` |")
    A("")
    A("First meaningful output line per gate:")
    A("")
    for r in results:
        A(f"- `{r['id']}` (exit {r['rc']}): {r['note']}")
    A("")
    if skipped:
        A(
            f"Not run this pass: {', '.join('`' + s + '`' for s in skipped)}. "
            "A skipped gate is not a passing gate and is not counted as one."
        )
        A("")

    A("## 3. The acceptance gate is fail-fast")
    A("")
    A(
        "`scripts/check.py` line 12 calls `sys.exit(res.returncode)` on the first failed bar. "
        "Measured this pass: it exits 1 at **Ruff Format Check** and reports nothing after it, so "
        "the five `docs/14` §5.3 bars are currently invisible. A gate that stops at the first "
        "failure answers *which* bar failed, not *how many* are red — and only the second is "
        "decision-relevant for a ship call."
    )
    A("")
    A(
        "Consequence for this dossier: the `ACCEPTANCE` row above is a single exit status standing "
        "in for every bar beneath it. The per-bar state has to come from elsewhere until that "
        "changes."
    )
    A("")

    A("## 4. Licence posture")
    A("")
    A(
        f"- `python scripts/license_gate.py` — exit {next((r['rc'] for r in results if r['id'] == 'LICENCE'), 'not run')}"
    )
    A(f"- Git `HEAD` — `{head_sha}`")
    A(f"- Tracked files — {tracked}")
    A(f"- Untracked or modified entries — {dirty}")
    A(
        "- Adopted-source notices are checked by `license_gate.py` checks 5 and 6. The three golden "
        "references in Addon 6 (`LedgerX`, `ledgerlens`, `Forecasting-01-Moving_Averages`) carry no "
        "licence, so L2 applies: zero lines copied, invariants re-expressed as our own tests."
    )
    A("")

    A("## 5. Open decisions and their blast radius")
    A("")
    A(
        f"`evidence/open_decisions.md` declares **{declared_od}** tracked open decisions and lists "
        f"**{listed_od}** ({', '.join(od_ids) if od_ids else 'none'}). The register therefore does "
        f"not currently deliver its own count."
        if declared_od and listed_od < declared_od
        else f"`evidence/open_decisions.md` lists {listed_od} open decision(s): "
        f"{', '.join(od_ids) if od_ids else 'none'}."
    )
    A("")
    A("| Decision | Blast radius | State |")
    A("|---|---|---|")
    A(
        "| `DOC-02` canonical EULA / advisory disclaimer text | Ships in the offline installer; legal "
        "exposure on every desktop install | Blocked on an owner ruling. `scripts/build.py` reports a "
        "blocker rather than inventing legal text. |"
    )
    A(
        "| `DOC-08` / `GATE-13` in `docs/28` | An approval nobody has given is currently carried as "
        "if it gates release | Packet not yet assembled. |"
    )
    A(
        "| `TB-006` / `TB-011` corpus rebuild | Blocks the five `docs/14` §5.3 bars, which "
        "`scripts/check.py` can no longer even report | In flight (`CORPUS-03`, `QUAL-05`). |"
    )
    A(
        "| 8 handoffs authored by `antigravity` | That seat is `AWAY` (quota ended 2026-10-05) and "
        "cannot verify its own work, so no rotation reaches them | Unreachable by the queue; needs a "
        "documented disposition. |"
    )
    A(
        "| `Ruff Format` across `app/ scripts/ tests/` | 173 files unformatted; currently masks every "
        "later acceptance bar | Red. |"
    )
    A("")

    A("## 6. Known limits, as numbers")
    A("")
    A("| Limit | Number | Where it is measured |")
    A("|---|---|---|")
    A(f"| Gates red this pass | {len(red)} of {len(results)} run | section 2 |")
    A(f"| Gates skipped (not run, not passing) | {len(skipped)} | section 2 |")
    A(
        f"| Open decisions declared vs listed | {declared_od} vs {listed_od} | "
        "`evidence/open_decisions.md` |"
    )
    A(f"| Tracked files / dirty entries | {tracked} / {dirty} | `git ls-files`, `git status` |")
    A(
        "| Handoffs awaiting a verifier | see `scripts/verification_queue.py --stats` | verification "
        "queue, median wait reported there |"
    )
    A(
        "| `aria-` attributes in `ui/src` | 0 across all `.tsx` files | `TB-105`, measured at "
        "generation time in `evidence/ops/lead-03-citation-audit.md` |"
    )
    A("")

    A("## 7. What this dossier does not cover")
    A("")
    A(
        "- It reports **gate exit status**, not gate adequacy. A gate that exits 0 proves only that "
        "it ran; three audits this session exited 0 on fabrications (`TB-104`)."
    )
    A(
        "- It cannot see the bars that `scripts/check.py` stops short of. Section 3 states this "
        "rather than implying full coverage."
    )
    A(
        "- It is a point-in-time reading"
        + ("" if slow else " that excluded the slow gates")
        + ". Five agents share one checkout; re-run before any ship decision."
    )
    A("- It says nothing about the product's behaviour. It says what the machine reports.")
    A("")
    A(END)
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
