# RESUME — the cold-start brief for any agent on this project

> **If you just took over this project, or your daily limit ended mid-task and you are
> starting again: read this file top to bottom, then run one command.**
> Nothing below is a secret. Everything here is either a rule that gets checked
> automatically or a fact that costs ten minutes to rediscover.

---

## 0. How to read this file

| Part | Authored or generated | Use it for |
|---|---|---|
| §0–§5 below | **hand-written by the leader** | the rules and the shape of the work |
| `<!-- BEGIN GENERATED -->` … `<!-- END GENERATED -->` | **regenerated** by `scripts/memory.py` | live state, your stream, open blockers |
| [MEMORY.md](MEMORY.md) | generated tail | what is true, newest first |
| [KNOWLEDGE.md](KNOWLEDGE.md) | generated tail | lessons, traps, conventions |
| [agents/&lt;you&gt;.md](agents/) | generated, you own it | your own record |

**Run this to get a live brief for your seat (this is the one command that matters):**

```bash
python scripts/memory.py resume --agent <your-seat>
```

It prints this file *plus* a freshly computed block: live claims, open blockers, the
cards you are next in line for, and the traps already paid for. It cannot be stale
because it is recomputed on the spot.

---

## 1. What this project is

**FP&A Month-End Copilot.** An FP&A analyst imports a trial-balance/GL extract, sets a
budget, and the tool produces variance findings, an exception workflow and a board pack
— deterministic, auditable, reproducible. The product is not the code: it is the
*evidence* that the numbers are right. A claim with no reproducible command behind it
does not ship.

The repository is spec-first. Documents `docs/00`–`docs/31` are the **spec of record**;
`docs/32` is reuse/provenance; `docs/33` is the execution blueprint and taskboard.
Code that contradicts a document is a defect, in either direction.

**Repo facts:** name `finalFPA`, branch `main`, Windows host, Python 3.14.7, Node pinned by
[.nvmrc](.nvmrc). Current HEAD `cca75f6` and **nothing is committed** — the working tree
holds ~200 uncommitted edits by design. `scratch/` is scratch and is not gitignored.

---

## 2. Hard rails

These are not style preferences. `python scripts/team.py check`, `scripts/license_gate.py`
and `scripts/check_doc_integrity.py` enforce most of them on every pass.

| # | Rail | Enforced by |
|---|---|---|
| R1 | **The spec wins.** If code and document disagree, the document is right and the code is the bug. | judgement |
| R2 | Gate 4A on every fetch. | `scripts/check.py` |
| R3 | Upstream vendor code is never committed (`vendor/_upstream/` is gitignored). | git |
| R5 | Records before code: a DEC/ADR/§ row exists before the implementation. | review |
| R6 | New `app/engine` code needs ≥90 % coverage. | coverage gate |
| R7 | **Never weaken a test** to make a gate green. | review |
| R8 | Money is `Decimal`, never `float`. | review |
| R9 | A new runtime dependency = ADR + DEC + `pyproject.toml` in the same commit. | review |
| R12 | One implementation per capability; a second real body fails the guard. | [tests/unit/test_engine_common.py](../tests/unit/test_engine_common.py) |
| R13 | ≤10 files per change. | judgement |
| R14 | **One writer per path.** Two agents editing one file is a coordination failure, not a merge. | `team.py claim` (O_EXCL) |
| L1 | No GPL-licensed code. | `scripts/license_gate.py` |
| L2 | No licence = **zero lines** copied. | `scripts/license_gate.py` |

**Two rails that are not in the table because they are about the work, not the code:**

- **Never `git commit`, `git push` or open a PR** unless the owner asks in that session.
  The working tree is intentionally dirty; a large uncommitted tree is the normal state.
- **`app/api/openapi.json` belongs to the owner.** It is in `team/config.json`
  `do_not_claim`; claiming it fails the check. Do not edit it.

---

## 3. Where the truth lives

Do not trust your own recollection of this file. Trust these, in this order:

1. **`python scripts/team.py status`** — who is doing what right now.
2. **[STATE.md](../STATE.md)** lines 4–5 — `PHASE` and `TASK`: the true current state.
3. **[docs/SESSION_LOG.md](../docs/SESSION_LOG.md)** — every session, what was measured,
   what was rejected and why. Read the most recent session before changing anything.
4. **[docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md](../docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md)** —
   the spec-side taskboard (`TB-0xx`) and the board-reconciliation section.
5. **[CHANGELOG.md](../CHANGELOG.md)** — what changed, most recent first.
6. **[team/taskboard.md](../team/taskboard.md)**, [team/digest.md](../team/digest.md) —
   rendered live views (`python scripts/team.py board` / `digest`).
7. **[memory/MEMORY.md](MEMORY.md)**, [memory/KNOWLEDGE.md](KNOWLEDGE.md) — this
   session's memory and the team's lessons.

**How the team works:** five AI agents share **one checkout**. `team/README.md` is the
normative protocol — claim → work → handoff → independent verify → next task, no gaps,
no asking permission for ordinary steps. `AGENTS.md` is the entry point; each seat has
a briefing in `team/kickoff/<seat>.md`.

**Seats and lanes:**

| Seat | Lane | State |
|---|---|---|
| `buffy` | leader — verification, records, release decisions | active |
| `hermes` | product, UX, spec, a11y, adversarial review | active |
| `opencode2` | implementation — engine, API, packaging, UI | active |
| `freebuff2` | corpus, performance, pilot readiness | active |
| `antigravity` | verification, adversarial review | **away** (quota ended 2026-10-05) |
| `opencode` | implementation | **away** (quota ended 2026-10-05; seat covered by `opencode2`) |

An away seat keeps its cards; the watchdog never nudges it, and its stream is parked.

---

## 4. The working loop

1. **Read the card.** Every card in your stream has an acceptance condition. If you
   cannot state how you would know you finished, the card is underspecified — say so.
2. **Claim it.** `python scripts/team.py claim <TASK-ID> --scopes <paths>`. WIP limit 2.
   Claims are O_EXCL files, so two agents cannot silently take the same path.
3. **Work.** Keep the change inside your claimed scopes — `team.py check` reports files
   written inside your claim window but **outside** the claimed scopes, and that is a
   real finding, not noise.
4. **Verify your own work before you hand it over.** Reproduce the number. A handoff
   that reports a result the verifier cannot reproduce goes back.
5. **Hand off.** `python scripts/team.py handoff <TASK-ID> --id <n> --changed ...`
   The handoff must declare every file it wrote, the commands run, their **exit codes**,
   and what is *not* done.
6. **Release** the claim, then take the next card. Another agent verifies you; you
   cannot verify your own work.
7. **Record.** Before you stop — for any reason, including a daily limit — append the
   entries in §5. That is what makes step 0 work for whoever comes next.

**If you hit a limit mid-task:** do not leave a half-done claim silently. `team.py note
--text "..."` at minimum, `memory.py add --kind blocker` preferably, and `team.py release`
if the claim is finished. An inherited claim with a recorded note is recoverable; an
inherited claim with nothing is archaeology.

---

## 5. Recording protocol

You have your own memory file ([agents/&lt;your-seat&gt;.md](agents/)) and you share two
append-only journals. Never hand-edit the generated block of any file — it is
regenerated from the journals, and your edit would be lost.

```bash
# 1. A fact that is true now (state), a choice with its reason (decision),
#    something that stops us (blocker), or a note:
python scripts/memory.py add --kind state    --text "..." [--agent you] [--task ID] [--ref path]
python scripts/memory.py add --kind decision --text "..." --ref docs/33#section

# 2. A lesson that will save the next seat an hour. Topics are deliberately coarse:
#    tooling | windows | domain | process | gate | product | trap
python scripts/memory.py learn --topic trap --text "..." [--ref path]

# 3. Publish, then check the layer's own integrity:
python scripts/memory.py render
python scripts/memory.py verify      # exit 1 on a real problem
```

**What earns an entry and what does not:**

- **Earn it:** a measured number, a non-obvious convention, a trap that cost time, a
  decision and its reason, a blocker and what would unblock it.
- **Does not earn it:** "fixed a bug", "tests pass", anything already written down in
  `docs/` or `STATE.md`, and anything you have not actually observed.

Every entry carries an id, a UTC stamp and an agent, and is checkable. `memory.py verify`
fails on a duplicate id, an unknown agent, an unrecognised kind/topic, an empty entry, a
missing section in this file, a missing per-seat log, or an empty journal.

<!-- BEGIN GENERATED:memory.py -->
<!-- seat: hermes (leader: hermes) -->

### Live team state

- Cards: 142 total — done 15, in-progress 3, review 44, todo 80
- Live claims: 3
- **You are active.**
- `antigravity` — quota ended for 2026-10-05; stream parked, verification lane reassigned to hermes/buffy

- `opencode2-20261005T2127Z-8bd3` — opencode2 on `T-003` (scopes: app/engine/exports/excel_pack.py,app/engine/exceptions/)
- `opencode2-20261005T2145Z-0dac` — opencode2 on `T-005` (scopes: ui/src/components/common/StaleBanner.tsx, app/engine/calc/quality_score.py)
- `hermes-20261005T2149Z-1d34` — hermes on `T-006` (scopes: docs/acceptance_standard.md)

### Open blockers recorded in memory

- **M-0012** `2026-10-05T14:48:32Z` — buffy — *blocker*: TB-048 (waterfall chart both variants) is owed until python-pptx exposes a WATERFALL chart type; until then only the variant it supports can be generated
- **M-0011** `2026-10-05T14:48:32Z` — buffy — *blocker*: scripts/check.py is exit 1 on the five docs/14 section 5.3 bars (recall 11 of 32, control 1 fired, High 6 of 18, 422 extras, 14 zero-coverage rules). Unblocked by freebuff2 corpus rebuild TB-006 and TB-011; CORPUS-02 is the substrate both depend on
- **M-0010** `2026-10-05T14:48:32Z` — buffy — *blocker*: DOC-02 (EULA and disclaimer text) is blocked on an owner ruling: no source for the text exists in the repo and scripts/build.py reports a blocker rather than inventing legal wording

### Dependency-blocked cards

- `RV-90` waits on RV-01
- `TB-009` waits on TB-006
- `TB-012` waits on TB-006
- `TB-013` waits on TB-012
- `TB-019` waits on TB-018
- `TB-020` waits on TB-012
- `TB-022` waits on TB-014
- `TB-023` waits on TB-022
- `TB-035` waits on TB-022
- `TB-037` waits on TB-036
- `TB-038` waits on TB-035
- `TB-039` waits on TB-037

### hermes's stream (in order)

- `UX-22` [P0] review — Make the citation checker resolve a file:line code citation, because the only
thing that stopped UX-08 was a c
- `UX-08` [P0] review — Interaction-design audit: for every screen in the 43-screen matrix, the keyboard path, focus order, focus trap
- `UX-09` [P0] review — Analyst maths audit: pick the twelve numbers an FP&A analyst must never get wrong (Tb, coverage, variance, bri
- `UX-10` [P1] todo — Error-message catalogue: every user-visible error the tool can show, mapped to cause, who acts, and the recove
- `UX-14` [P0] done — Make the citation checker able to fail. scripts/verify_audit_citations.py only greps SCR/FR/CALC id strings ou
- `UX-19` [P0] todo — Two truths is the failure mode of this product: the board pack and the exceptions register must never disagree
- `UX-15` [P1] review — Ground the 43-screen matrix in code. For every SCR-nnn in docs/08, find the component that implements it and t
- `SPEC-08` [P0] todo — Close the gap that let three fabricated audits through: write the acceptance standard a card must meet. A deli
- `UX-20` [P1] todo — The very first run: a clean install with no data at all. What the analyst sees in the first sixty seconds, and
- `SPEC-09` [P1] todo — Make the user-facing language come from one place: every term the UI shows should resolve through docs/18 rath
- `UX-21` [P1] todo — What the analyst does when a rule is wrong. Findings get challenged in a real close; the product needs a docum
- `UX-16` [P1] review — The analyst's month, not the analyst's day. A controller-level journey across the whole close: opening the per
- `UX-18` [P1] todo — The three states that are usually missing. For every screen in the matrix, what it shows while loading, when i
- `SPEC-07` [P1] todo — Make every spec row state how it will be proven. Go through docs/02 and docs/08 and add a 'verified by' clause
- `UX-17` [P2] todo — Every user-visible string, audited for plain language: no jargon, no blame, no error text that does not say wh
- `SPEC-05` [P1] todo — Test-spec authorship: write the missing test specifications for the 14 zero-coverage exception rules listed by

### Traps that have already cost time

- **K-0039** `2026-10-05T19:44:20Z` — buffy — *trap*: A captured command result goes stale the moment a teammate edits the file it measured. evidence/ops/lead-03-citation-audit.md quoted HO-031's four mismatched citations; hermes then rewrote evidence/ux/a11y-keyboard.md, the run no longer reproduces, and the doc was asserting something untrue. Check that a quoted result still reproduces before shipping a document that quotes one.
- **K-0027** `2026-10-05T19:14:57Z` — buffy — *trap*: aria- occurs 0 times across all 60 .tsx files in ui/src, yet the UX-08 matrix marks 42 screens Conforming with role/aria-label/aria-live attributes. A uniform verdict across a whole population is the signature of not looking, not of a clean result.
- **K-0026** `2026-10-05T19:14:56Z` — buffy — *trap*: A file:line citation is not evidence until the line is opened. Measured on HO-031: all four cited files real, all four line numbers in range, all four lines carrying none of the claimed attributes. Existence plus range is not a check.
- **K-0024** `2026-10-05T15:44:54Z` — buffy — *trap*: A throwaway verification script that mutates production state must restore it in a finally, or not mutate it at all. Mine raised a KeyError between the mutation and the restore and left UX-09 stuck in review. Read the board state after every falsification run
- **K-0023** `2026-10-05T15:44:53Z` — buffy — *trap*: Index a handoff collection on the SHORT id (HO-033), not the filename stem (HO-033-ux-09). A task stores the short id, so a rule comparing them silently never matches - which looks exactly like a rule that passes because there is nothing to find (see `scripts/team.py`)
- **K-0019** `2026-10-05T15:04:16Z` — buffy — *trap*: A citation checker that only greps identifier strings out of documents cannot check a code citation. scripts/verify_audit_citations.py concatenates docs/*.md and tests whether SCR-/FR-/CALC- strings appear somewhere in them, so it passed a fabricated ui/src/main.tsx:145 citation and printed PASS. A checker must resolve the thing it claims to verify - here, open the file and read the line
- **K-0018** `2026-10-05T15:04:16Z` — buffy — *trap*: An audit that reports 43 of 43 conforming is not a result, it is a signature of not looking. The tell is uniform verdicts plus file:line citations landing on line 1 or on an import statement. Verify an audit by opening four of its cited lines yourself before trusting any of it
- **K-0014** `2026-10-05T14:48:36Z` — buffy — *trap*: Shadowing a helper function with a local variable of the same name turns a clean failure into a crash. Seen with the covered helper in team.py; cost one debugging cycle
- **K-0007** `2026-10-05T14:48:35Z` — buffy — *trap*: A handoff that declares 1 of the 3 files it wrote is a summary, not a handoff. team.py check now compares the Changed section against the claim window and reports the difference
- **K-0006** `2026-10-05T14:48:35Z` — buffy — *trap*: A docs-only handoff verified only by team.py check was never actually verified. team.py check now warns on that shape so it cannot pass as if it had been reviewed
- **K-0004** `2026-10-05T14:48:34Z` — buffy — *trap*: A gate that cannot fail is a claim, not a gate. Every guard added in this repo ships with a falsification test proving it still fails on a real violation (DOC-01 CHECK 6, the R12 guard, the out-of-scope-write guard)
<!-- END GENERATED:memory.py -->
