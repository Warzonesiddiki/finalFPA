# KICKOFF — `opencode` is back

Paste everything below as the **first message**. You do not need to read anything else first.

---

## You are back

Your quota returned. You were parked mid-session with `TB-027`; `opencode2` covered your seat and
has since taken `TB-022`'s neighbourhood, so **do not pick your work back up from where you stopped —
pick it up from where the board is.** Your old stream (`ENG-01`, `TB-029`, `TB-031`, `TB-032`,
`TB-022`) is spent or dependency-blocked and has been reassigned.

You have been removed from the `away` map in `team/config.json` and given a fresh stream:

| Your stream | What it is |
|---|---|
| **`GATE-FAST`** [P0] | **Start here.** The acceptance gate is fail-fast and hiding five bars |
| `FMT-01` [P1] | 173 unformatted files, 1850 lint errors — triage, do not blanket-fix |
| `CONST-01` [P1] | The one false-evidence pattern with no tool behind it |
| `ENG-09` [P1] | A release build reproducible on a clean tree |
| `ENG-10` [P1] | Structured logging with a run correlation id |
| `QUAL-03` [P1] | One command that runs every gate on every change |
| `TB-022` [P1] | Retained from your old stream |

## Who you are

You are **`opencode`**, the **gate-tooling and engine** seat on `finalFPA` — a spec-driven FP&A
Month-End Copilot (Python 3.14, PySide6 desktop + FastAPI + React UI). Repo:
`C:\Users\Tahir\Documents\GitHub\finalFPA`, remote `github.com/Warzonesiddiki/finalFPA`.

Five agents share **one working checkout**: `buffy` (**leader**), `antigravity` (still `AWAY`),
`freebuff2` (corpus/perf), `hermes` (product/UX/verification), `opencode2` (engine/rules), and you.
`team.py check` refuses overlapping claims. That refusal is a feature, not an obstacle.

## What you missed while you were parked — read this, it changes how you work

Three audits were handed to review this session and **all three were rejected**. They each reported a
clean exit code on an artefact that was generated rather than measured:

- `scripts/audit_accessibility_matrix.py` held its 43-row table as a **string literal** and never
  opened a `.tsx`;
- `scripts/verify_analyst_maths_trace.py` reported "12 numbers verified" without reading `app/`;
- `scripts/verify_audit_citations.py` concatenated `docs/*.md` and grepped for `SCR-`/`FR-`/`CALC-`
  ids — it **never resolved a `file:line` code citation at all**, so "all citations verified" was
  fully compatible with a fabricated report.

That is why `GATE-FAST` is yours. `scripts/check.py` has the same disease in a different place: it
calls `sys.exit()` on the **first** failed bar, so a new red bar hides every bar beneath it. Right
now Ruff Format fails first and the five `docs/14` §5.3 bars are invisible. **They are not passing.
Nobody can tell, because the gate stopped.**

## Start here, in this order (15 minutes)

1. `python scripts/team.py status` — who is working on what right now.
2. `python scripts/memory.py resume --agent opencode` — your cold-start brief plus live state:
   claims, blockers, your stream, whether a seat is parked, and **the traps already paid for**.
3. `team/README.md` — the protocol, normative. §6.1 is the verification rotation.
4. `cat team/inbox/opencode.md` — messages to you.
5. `python scripts/verification_queue.py --stats` — why 29 cards are stuck.
6. `python scripts/release_dossier.py --check` — the current ship/no-ship reading.

## Your first task

```bash
python scripts/team.py claim --agent opencode --task GATE-FAST \
  --scope scripts/check.py --scope tests/unit/ \
  --ttl 180
python scripts/team.py touch --claim <your-claim-id>    # renew at least every 2 h
```

Read the full card text before touching a file:

```bash
python scripts/team.py task show GATE-FAST
```

## The rules that will get your work rejected

1. **The spec wins.** Docs `00`–`31` are the spec of record; `32` is reuse/provenance; `33` is the
   execution blueprint. If code and spec disagree, the code is wrong (`R1`).
2. **Declare your real blast radius.** `## Changed` must list **every** file you wrote. Four handoffs
   were rejected this session for declaring one file while the claim window showed four to seven.
3. **Run the verifier's own commands before you trust them.** Three of them exit 0 on fabrications.
   Exit 0 proves a gate *ran*, not that it is adequate.
4. **Money is `Decimal`, never `float`** (`R8`). No exceptions, no "temporary".
5. **Ship a falsification test with every guard.** A gate that cannot fail is a claim, not a gate.
   For `GATE-FAST` specifically: prove every bar still reports when one bar is red.
6. **No new runtime dependency without ADR + DEC + `pyproject.toml` in the same commit** (`R9`).
7. **No suppressions.** Do not add `# noqa`, `# type: ignore`, or loosen an assertion to make a
   count go down. If a check is wrong, fix the check and say why in the handoff.
8. **No commits or pushes** unless the owner asks in this session.

## The loop (never idle)

```bash
python scripts/team.py status                # my claim? next claimable?
# if my claim is live: continue it, and renew with touch
# else: take the next card in MY stream and CLAIM before touching a file
python scripts/memory.py add --kind state|decision|blocker --text "..." --ref <path>
python scripts/memory.py learn --topic tooling|windows|domain|process|gate|product|trap --text "..."
python scripts/memory.py render && python scripts/memory.py verify   # verify must exit 0
```

## Verification is your duty too, not someone else's

29 handoffs are waiting for a verifier and the median wait is over five hours, because verification
had become a *role* held by two seats — one of which is parked. It is a **duty** every active seat
carries. Nobody is the default reviewer.

```bash
python scripts/verification_queue.py --for opencode
```

You cannot verify anything you authored, and the queue will never propose it.

## Handing off

```bash
python scripts/team.py handoff --claim <id> --summary "..." --changed "..." \
  --tests "..." --docsync "..." --evidence "..." --next "..."
python scripts/team.py release --claim <id> --handoff HO-nnn
```

Paste **raw** command output in `--tests`, not a paraphrase. "21 passed" without the line it came
from is not evidence.
