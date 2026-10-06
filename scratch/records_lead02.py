"""Record LEAD-02 in memory, CHANGELOG, STATE and SESSION_LOG."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def memory(args: list[str]) -> int:
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "memory.py"), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p.returncode


ENTRIES: list[list[str]] = [
    ["add", "--kind", "state", "--ref", "evidence/ops/verification-bottleneck.md",
     "--text",
     "LEAD-03/LEAD-01/LEAD-02 all landed this session (HO-043, HO-046, HO-048). LEAD-02 made "
     "verification a rotating duty: measured 26 handoffs waiting, median 317 min, 92% of "
     "verifications on two seats, one of them AWAY. Root cause was one sentence in team/README.md "
     "naming a default reviewer. Records TB-105, TB-106, TB-107."],
    ["learn", "--topic", "process",
     "--text",
     "Naming a default reviewer turns a duty into a role. Role concentrates with tenure and does "
     "not redistribute when that person goes away. Verification must be a duty every active seat "
     "carries, assigned least-recently-verified first. Measured 2026-10-05: 26 waiting, median 317 "
     "min, antigravity (11) and buffy (1) had done 92% of all verification, four seats had verified "
     "nothing."],
    ["learn", "--topic", "gate",
     "--text",
     "A rejected handoff is NOT waiting for a verifier - it is waiting for its author to re-do the "
     "work. Counting it in the verification queue inflated the bottleneck from 26 to 36 and would "
     "have hidden the real one."],
    ["learn", "--topic", "process",
     "--text",
     "Do not report an improvement before it is observed. The LEAD-02 mechanism landed minutes "
     "before its measurement, so only the PROPOSED distribution (7/7/7/6 across four active seats) "
     "was measurable, not a realised wait time. The README says to re-measure --stats in an hour "
     "rather than leaving a number nobody will check."],
    ["learn", "--topic", "windows",
     "--text",
     "Importing scripts/team.py makes mypy surface its pre-existing 27-error ENG-01 baseline. Scope "
     "mypy output to your own file path when checking new code that imports team.py."],
]


CHANGELOG = (
    "- **Verification is a rotating duty, not a role (`scripts/verification_queue.py`, "
    "`TB-107`/`LEAD-02`):** `LEAD-02` claimed 20 handoffs were waiting for a verifier while seats "
    "had claimable work. Measured: **26 waiting, median 317 min (5.3 h), max 417, 20 over a 30-min "
    "service level, 2 distinct verifiers, 92% load concentration** - `antigravity` (11) and `buffy` "
    "(1), with `freebuff2`, `hermes`, `opencode` and `opencode2` never having verified anything. "
    "The root cause is one sentence in `team/README.md` §6: *\"the default reviewer for money-path "
    "changes is `antigravity`\"*. Naming a default reviewer made verification a **role** held by the "
    "longest-tenured seat, so it concentrated with tenure and did not redistribute when that seat's "
    "quota ended. `scripts/verification_queue.py` assigns least-recently-verified first and refuses "
    "four things, each because breaking it produced a real failure: never an `AWAY` seat, never the "
    "author (`team.py verify` requires a different agent), never the same two people twice running "
    "(plain FIFO preserves the concentration), and never a verdict without a service level "
    "(`--sla`, default 30 min, matching the watchdog). A **rejected** handoff is excluded — it waits "
    "for its author, not a verifier, and counting those would have inflated the bottleneck from 26 "
    "to 36. The **after-number is deliberately not claimed**: what is measurable is the *proposed* "
    "distribution (7/7/7/6 across four active seats), and the wait time is a follow-up measurement. "
    "14 tests, including the case where one seat wrote the only handoff and the queue reports *no "
    "eligible seat* rather than proposing a self-verification.\n"
)

STATE_TASK = (
    "VERIFICATION ROTATION LANDED (TB-107 / LEAD-02): verification was a ROLE, not a duty, and that "
    "is what built the bottleneck. team/README.md section 6 carried one sentence - 'the default "
    "reviewer for money-path changes is antigravity' - which concentrated the work by tenure and, "
    "when that seat's quota ended on 2026-10-05, did not redistribute. MEASURED: 26 handoffs handed "
    "off and never verified, MEDIAN WAIT 317 MIN (5.3 h), max 417, 20 over a 30-min service level, "
    "2 distinct verifiers, 92% LOAD CONCENTRATION (antigravity 11, buffy 1), and 4 of 6 seats "
    "(freebuff2, hermes, opencode, opencode2) had never verified anything. scripts/"
    "verification_queue.py assigns least-recently-verified first and refuses four things, each "
    "because breaking it produced a real failure: never an AWAY seat (assigning to antigravity looks "
    "like fair rotation and produces nothing), never the author (team.py verify requires a "
    "different agent), never the same two people twice running (oldest-first FIFO preserves the "
    "concentration exactly), and never a verdict without a service level (--sla, default 30 min, "
    "matching the watchdog threshold). ONE EXCLUSION CHANGED THE NUMBER: a rejected handoff is NOT "
    "waiting for a verifier, it waits for its author, so counting it inflated the bottleneck from 26 "
    "to 36 and would have hidden the real one. Over today's backlog the rotation proposes 7/7/7/6 "
    "across the four active seats. THE AFTER-NUMBER IS DELIBERATELY NOT CLAIMED: the mechanism "
    "landed minutes before measurement, so only the PROPOSED distribution is observable - claiming "
    "an improvement before it is observed is the exact habit TB-105 and TB-106 exist to stop, in the "
    "same session that wrote them. Re-measure with --stats and fill in team/README.md 6.1, which "
    "says so in place. RESIDUAL the rotation cannot fix: the 8 oldest handoffs are all "
    "antigravity's, and it is AWAY, so they can never be verified by rotation and need a documented "
    "disposition. docs/33 gains TB-107 and README section 6.1. "
)

STATE_GATE = (
    "- LEAD-02: `python -m pytest tests/unit/test_verification_queue.py -q` -> 14 passed; "
    "`ruff check scripts/verification_queue.py tests/unit/test_verification_queue.py` -> All "
    "checks passed; `mypy scripts/verification_queue.py` -> 0 errors in that file (the 27 remaining "
    "are scripts/team.py's pre-existing ENG-01 baseline, now visible because this file imports it); "
    "`python scripts/verification_queue.py --stats` -> 26 waiting, median 317 min, 2 verifiers, 92% "
    "concentrated; `python scripts/team.py check` -> PASS, 0 fail, 40 warn, 131 tasks, exit 0 "
)

SESSION_ADDENDUM = """
## Addendum 8 — LEAD-02: verification was a role, not a duty

**Card:** `LEAD-02` (P0, verification lane) · **claim:** `buffy-20261005T1932Z-e0ce` ·
**handoff:** `HO-048` · **records:** `TB-107`, `team/README.md` §6.1

### The measurement

| | |
|---|---|
| Handoffs handed off, never verified | **26** |
| Median wait | **317 min** (5.3 h) |
| Max wait | 417 min |
| Over the 30-min service level | 20 |
| Distinct verifiers | **2** — `antigravity` (11), `buffy` (1) |
| Load concentration | **92%** |
| Seats that never verified anything | 4 of 6 |

The card said 20. It is 26, and the shape matters more than the total.

### One sentence

`team/README.md` §6 read: *"The default reviewer for money-path changes is `antigravity`."* Naming a
default reviewer turned verification into a **role** held by the longest-tenured seat. It then
behaved exactly like a role: the work concentrated with tenure, and when `antigravity`'s quota
ended on 2026-10-05 the function did not redistribute to the four seats that had never verified
anything.

So this was not a discipline problem and not a throughput problem. It was one sentence assigning a
duty to a person, and a person running out of quota.

I left the sentence in place and documented it as the worked example. Deleting it would have removed
the reason the rule exists.

### The four refusals

Each exists because breaking it produced a real failure here:

1. **Never an `AWAY` seat.** Assigning to `antigravity` looks like a fair rotation and produces
   nothing.
2. **Never the author.** `team.py verify` requires a different agent, so the queue must not propose
   what the tool forbids.
3. **Never the same two people twice running.** Assignment is least-recently-*verified* first.
   Oldest-first FIFO preserves the concentration exactly — it hands work to whoever is idle as a
   verifier, which is the same two people.
4. **Never a verdict with no service level.** `--sla` (default 30 min, matching the watchdog's
   threshold) turns "late" into a number.

And one exclusion that moved the headline: a **rejected** handoff is not in the queue. It waits for
its author, not a verifier. Counting those would have reported 36 instead of 26 and hidden the real
bottleneck inside a bigger fake one.

### The after-number I am not claiming

The mechanism landed minutes before the measurement. What is measurable is the *proposed*
distribution — **7 / 7 / 7 / 6** across the four active seats, against 92% on two — not a realised
wait time. The median falls only once seats actually drain the queue, and `team/README.md` §6.1 says
in place to re-measure `--stats` rather than assume the fix worked.

Writing "verification wait reduced from 317 min to X" before X exists would be exactly the habit
`TB-105` and `TB-106` exist to stop — in the same session that wrote them. The mechanism is the
deliverable; the wait time is the follow-up.

### What rotation cannot fix

The 8 oldest handoffs are all `antigravity`'s, and `antigravity` is AWAY. No rotation reaches them,
because the author cannot verify their own work and the seat is gone. They need a documented
disposition — re-verify under the seats that covered its lane, or close them — and that is the part
of this card that is still owed.

### Gates

```
pytest tests/unit/test_verification_queue.py -q                      -> 14 passed
ruff check (script + tests)                                          -> All checks passed
mypy scripts/verification_queue.py                                   -> 0 errors in that file
        (27 remaining are scripts/team.py's ENG-01 baseline, visible because this file imports it)
python scripts/verification_queue.py --stats                         -> 26 waiting, median 317, 92%
python scripts/team.py check                                         -> PASS, 0 fail, 40 warn, exit 0
```
"""


def main() -> int:
    rc = 0
    for e in ENTRIES:
        rc |= memory(e)
    print("--- render ---")
    rc |= memory(["render"])
    print("--- verify ---")
    rc |= memory(["verify"])

    log = ROOT / "CHANGELOG.md"
    text = log.read_text(encoding="utf-8")
    anchor = "- **The citation opener:"
    assert anchor in text
    log.write_text(text.replace(anchor, CHANGELOG + anchor, 1), encoding="utf-8")

    state = ROOT / "STATE.md"
    out = []
    for line in state.read_text(encoding="utf-8").split("\n"):
        if line.startswith("TASK: "):
            out.append("TASK: " + STATE_TASK + line[len("TASK: "):])
        elif line.startswith("LAST_GATE: "):
            out.append("LAST_GATE: " + STATE_GATE + line[len("LAST_GATE: "):])
        else:
            out.append(line)
    state.write_text("\n".join(out), encoding="utf-8")

    slog = ROOT / "docs" / "SESSION_LOG.md"
    s = slog.read_text(encoding="utf-8").rstrip("\n")
    if "Addendum 8" not in s:
        slog.write_text(s + "\n" + SESSION_ADDENDUM, encoding="utf-8")
    print("CHANGELOG.md, STATE.md, docs/SESSION_LOG.md updated")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
