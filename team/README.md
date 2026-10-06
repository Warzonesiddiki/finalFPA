# `team/` — the five-agent workbench

> **Status:** live · **Created:** 2026-10-05 · **Folder owner:** `buffy` (team leader)
> **This is** the coordination layer for five agents working in **one shared checkout**.
> **This is not** a spec, a taskboard, or a decision log. `docs/00`–`33` stay the spec of record (`R1`),
> `docs/33` stays the taskboard, `docs/18` the decision register, `docs/SESSION_LOG.md` the session memory.
> If anything here disagrees with a doc, **the doc wins** and this folder gets corrected.

---

## 0. The team

| Agent | Tool | Suggested lane (who to expect, never exclusive) |
|---|---|---|
| `buffy` | Freebuff (leader) | Integration + money paths (`app/engine/**`), **leader-only** files (see §4), final verification, the single committer |
| `antigravity` | Google Antigravity | Adversarial verification and spec-conformance review (`tests/**`, `evidence/**`); can own any implementation lane it claims |
| `opencode` | opencode | Implementation lanes the leader delegates (`app/**`); refactors that must ship with their tests |
| `freebuff2` | Freebuff (second instance) | Corpus and data (`sample-data/**`, generator `scripts/**`), performance measurement, packaging |
| `hermes` | any agent tool (fifth seat) | **The analyst's advocate** — `ui/**`, `app/api/**`, the `01`/`02`/`05`/`08` product clauses, the month-end journey (`UX-01`), prior-art requirements mining |

Any agent may claim any path; the lane column only says who to expect. **Claims decide**, and
`scripts/team.py check` fails on overlap.

## 1. The one rule

**Never edit a path you do not hold an active claim on.** One writer per path at all times — this is the
operational form of the project's `R14` single-writer rail. *Reading* is always free.

Corollary: a claim is a promise. If you cannot finish and verify inside the TTL, `touch` it or release it
with a handoff — never leave a half-landed edit and an expired claim.

## 2. Session start, in order

1. `python scripts/team.py status` — who is alive, what is claimed, what is stale, orphan edits.
2. `team/digest.md` — the generated context capsule (milestone, red bars, active claims, next step).
3. `docs/33` §6.1's session-start reads; the board's open milestone decides the work.
4. **Claim before the first edit:** `python scripts/team.py claim --agent <you> "<title>" --scope <path> [--scope <path>] --kind <docs|engine|tests|evidence|infra|corpus|commit> [--task TB-nnn]`
5. Read `team/lessons.md` once per session — it exists so four agents do not each rediscover the same trap.

## 3. Task lifecycle

```
proposed ──claim──▶ in-progress ──handoff──▶ review ──(different agent verifies)──▶ done
                        │
                        └── blocked ──▶ escalation (§7): question to the owner in team/inbox/owner.md
```

* **WIP limit: 2 active claims per agent** (one in progress + one in review). `check` enforces it.
* **Review is a hard gate.** A handoff moves to `done` only after an agent **other than the author**
  reproduces the verification numbers and records them in the same handoff file (new `## Verification by
  reviewer` block). An unreviewed handoff is not done; it is *claimed*.
* Evidence lives where the project already puts it (`evidence/<slug>/`); handoffs point at it, never
  duplicate it.

## 4. Claim protocol

```bash
python scripts/team.py claim --agent opencode "EXC-013 magnitude rule review" \
    --scope app/engine/rules/rules_09_16.py --scope tests/unit/test_rules_09_16.py \
    --kind engine --task TB-nnn --ttl 120
python scripts/team.py touch --claim opencode-20261005T1412Z-9f3a   # renew heartbeat
python scripts/team.py release --claim <id> [--done]
python scripts/team.py handoff --claim <id> --summary ... --changed ... --tests ... --docsync ... --evidence ... --next ...
```

* Claims are files under `team/claims/` created with `O_EXCL` (atomic; no shared register to race on).
* **TTL + heartbeat.** `touch` (or any `team.py` command by the owner) renews. Past the TTL the claim is
  **stale**; see below.
* **Stale takeover (never silent):** an agent may take a stale claim only with
  `python scripts/team.py claim --steal <claim_id> ...`, which logs the takeover and messages the previous
  owner. Silent stealing is a protocol violation.
* **Leader-only paths.** `docs/18_*`, `docs/33_*`, `docs/SESSION_LOG.md`, `CHANGELOG.md`, `STATE.md`,
  `docs/00_INDEX.md`, `team/**`, and `project prompt/**` are written by `buffy` only. Everyone else's
  changes to those files go **as content in a handoff**, and the leader lands them. This is deliberate:
  those files are the integration surface where four writers cause unresolvable merge damage. (`check`
  fails on a violation.)
* **`kind=commit`** claims are leader-only and require the owner's explicit go-ahead in the session; the
  repo rule "no commit/push unless asked" is unchanged by this folder.

## 5. Handoff — the only acceptable way to stop mid-work

`team.py handoff` writes `team/handoffs/HO-nnn-<slug>.md` with these **required** sections (checked by
`team.py check`): `## Claim`, `## Changed`, `## Verification`, `## Doc-sync`, `## Evidence`, `## Next`.

* **`## Changed`** lists real paths; anything under `app/` or `scripts/` obliges `## Verification` to carry
  **measured numbers** (command + result), not adjectives.
* **`## Doc-sync`** mirrors Addon 6 §8's table: which of the 11 rows apply and were updated (or
  `docs-only: no behaviour change`). This is the single highest-value habit in this repo — the register
  repair recorded in this session (`docs/18` `D-13`) is exactly what a missed doc-sync row costs.
* **`## Evidence`** lists paths that must exist on disk (checked). Docs-only work may write
  `evidence: none (docs-only)`.
* A handoff that omits a section is invalid; `check` fails and the work is not reviewable.

## 6. Independent verification (the quality lever)

Every completed claim gets a reviewer who did **not** write the code. The reviewer:

1. re-runs the claimed command(s) and pastes the **raw result**, not a paraphrase;
2. reads the diff against the spec doc that governs it (`06` for rules, `12` for deck, `03`/`04` for
   import, …) and states which clause decides each non-obvious choice;
3. tries to falsify the claim: the mutation habit this repo already uses (revert the fix → the test must
   fail; if it still passes, the test is decorative).

The default reviewer for money-path changes is `antigravity`; a rule/engine change may be peer-verified by
anyone except its author.

### 6.1 Verification is a rotating duty, not a role (`LEAD-02`, `TB-107`)

The sentence above — "the default reviewer for money-path changes is `antigravity`" — is how this
team built a bottleneck, and it is worth keeping as an example. Naming a default reviewer made
verification a **role**, held by whoever was longest-tenured. It then behaved like a role: the work
concentrated, and when that seat went `AWAY` the function did not redistribute.

Measured on 2026-10-05, before the fix:

| | |
|---|---|
| Handoffs handed off, never verified | **26** |
| Median wait | **317 min** (5.3 h) |
| Max wait | 417 min |
| Over the 30-min service level | 20 |
| Distinct verifiers | **2** — `antigravity` (11), `buffy` (1) |
| Load concentration | **92%** |
| Seats that had never verified anything | 4 of 6 — `freebuff2`, `hermes`, `opencode`, `opencode2` |

Two seats carried the whole team's verification, and one of them had no quota left.

**The rule now:** verification is a duty every active seat carries. Nobody is the default reviewer.
Before claiming new work — or at least before finishing it — drain the queue:

```bash
python scripts/verification_queue.py              # the queue, oldest first, with wait times
python scripts/verification_queue.py --for <seat> # what this seat should verify next
python scripts/verification_queue.py --stats      # verifier load and concentration
```

The queue assigns, and refuses four things, each because breaking it produced a real failure here:

1. **Never an `AWAY` seat.** Assigning to `antigravity` looks like a fair rotation and produces
   nothing.
2. **Never the author.** A self-verification is not a verification; `team.py verify` requires a
   different agent, so the queue must not propose what the tool forbids.
3. **Never the same two people twice running.** Assignment is least-recently-verified first, so a
   seat that has never verified anything is offered work before a seat that has done eleven. Plain
   oldest-first FIFO keeps the concentration exactly where it is.
4. **Never a verdict with no service level behind it.** `--sla` (default 30 min, matching the
   watchdog's escalation threshold) marks a breach, so "late" is a number rather than a feeling.

A rejected handoff is **not** in the queue: it is waiting for its author to re-do the work, not for
a verifier. Counting those would have inflated this bottleneck from 26 to 36 and hidden the real one.

**On the after-number, honestly:** what is measurable now is the *proposed* distribution, not a
realised one — the mechanism landed minutes ago. Running the queue over today's backlog assigns
**7 / 7 / 6 / 6** across the four active seats instead of queueing 26 items behind one person. The
wait time only comes down once seats actually drain it, so re-measure with `--stats` in an hour and
record the real figure here. Claiming the improvement before it is observed would be precisely the
habit `TB-105` and `TB-106` exist to stop.

## 7. Escalation (the ≤ 3-option rule)

When blocked: make at most **two** honest attempts, then **roll back to a truthful state**, then write the
packet (`evidence/<slug>/…-packet.md`): measured facts · what was tried · exactly **3 options** with a
recommended default · acceptance-gate impact. Send it with
`python scripts/team.py msg --from <you> --to owner "<one-line ask>"`, and record it in `docs/18` as an
`OQ-` when it is a spec question (`Addon 6` §14's tiers still govern: Tier C stops for the owner).

Never guess on money semantics, never weaken a test, never edit the spec to fit the code (`R1`, `R7`).

## 8. Git rules (unchanged by this folder)

* No `commit`/`push`/`reset`/`clean`/branch surgery unless the **owner explicitly asks in the session**.
* If a commit is authorised, the leader takes the `kind=commit` claim, verifies every active claim is
  released or handed off, runs the gates, and commits **only** the files named in handoffs.
* Never discard another agent's uncommitted work. If in doubt, leave it and say so in the handoff.

## 9. Security and honesty

* **No client data, credentials, tokens, or personal data in `team/`** (`13` governs). Sample data only.
* The team folder is coordination, not evidence: a claim is not proof, a handoff is not a test result.
  Claims about numbers require the number and the command that produced it.

## 10. Checks (zero-compromise invariants, machine-enforced)

```bash
python scripts/team.py check          # invariants; exit 0 clean, 1 violated
python scripts/team.py check --strict # also treats unclaimed working-tree edits as violations
```

Checked: claim files parse · known agents only · **no overlapping active scopes** · WIP limit · TTL/stale
reporting · leader-only paths · every `TB-nnn` mentioned exists in `docs/33` · handoff sections complete ·
evidence paths exist · **orphan edits** (working-tree changes no active claim covers) · digest freshness.

`team/board.md` and `team/digest.md` are **generated** by `team.py` — never hand-edit them; hand-editing a
derived view is how two sources of truth start.

## 11. Subagents and fan-out (how to use extra capacity without breaking one-writer)

Any agent may run subagents. The rules are short because the failure mode is obvious:
two writers on one file is how a spec-driven repo loses its evidence.

1. **Subagents never claim.** Only the named agent claims, and the claim's scopes must cover every path a
   subagent touches. `check` cannot see a subagent, so the parent is the single writer of record.
2. **Parallel is for breadth, not for one file.** Split work by *row* or *item* (one screen per subagent, one
   FR per subagent, one prior-art repo per subagent) so each subagent owns distinct output. Never let two
   subagents write the same file, and never split one function across two writers.
3. **Read-only fan-out needs no claim at all** - surveys, conformance matrices, citations, timings. These are
   the cheapest way to add hours of coverage and the safest: nothing is written but one merged report.
4. **Each subagent returns proof, not opinion:** the file it wrote (or `no file`) and the exact command with its
   raw output. A subagent reporting "done" is not a deliverable until the parent has run the command itself.
5. **The parent consolidates and hands off.** The handoff lists every file the fan-out produced, so the
   claim-window completeness check in `team.py check` can prove the list is honest.
6. **Same rails apply.** `R1` spec wins, `R7` never weaken a test, `R14` one writer per path, no commits, no
   client data, every number carries the command that produced it. A subagent is not exempt from any of them.

Reported capacity today: `hermes` may run many parallel read-only audits (its lane is product and spec
conformance); `antigravity` may parallelise verification and falsification passes. Both should spend that
capacity on the board, not on chat.
