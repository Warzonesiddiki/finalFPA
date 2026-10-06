# Kickoff — how to bring an agent into the team

One file per agent in this folder is a **complete, copy-pasteable prompt**. Open the agent's own tool,
paste the whole file content as the first message, and it self-onboards: it reads the protocol, the digest,
the taskboard, takes a claim, and starts the non-stop loop.

| Tool | File to paste | Notes |
|---|---|---|
| Freebuff (this session, **leader**) | [`buffy.md`](buffy.md) | Always running; owns integration + commits |
| Google Antigravity | [`antigravity.md`](antigravity.md) | Verifier-first role. **`AWAY`** — quota ended 2026-10-05; its 8 handoffs are unreachable by rotation and need a disposition |
| opencode | [`opencode.md`](opencode.md) | Gate-tooling / engine. **Returned 2026-10-05**; briefing covers what it missed while parked |
| Freebuff #2 | [`freebuff2.md`](freebuff2.md) | Corpus / perf / packaging role |
| Fifth seat | [`hermes.md`](hermes.md) | Product / UX / spec-domain — the analyst's advocate |
| Sixth seat | [`opencode2.md`](opencode2.md) | Second implementation seat; took the opencode lane while opencode was parked, keeps it now |

Seats marked `AWAY` are listed in the `away` map in `team/config.json`. A parked seat is never
assigned work: `team.py leader` shows `AWAY`, the watchdog skips it, and
`scripts/verification_queue.py` refuses to assign it anything. Removing the entry restores it
immediately, in both directions.

## The 30-second version of the protocol (what the prompts enforce)

1. `python scripts/team.py status` → then read `team/README.md` and `team/digest.md`.
2. **Claim before editing:** `python scripts/team.py claim --agent <you> --task <ID>` (or `--title`), always
   with `--scope` paths. One writer per path, enforced — `team.py` refuses overlaps, WIP limit 2,
   leader-only files.
3. Work → verify with the **command and the number** → `handoff` → `release --handoff HO-nnn` →
   `msg` a peer to verify → the peer runs `verify --task <ID> --by <them>` → the row is `done`.
4. **Never stop.** The moment a task is released, claim the next claimable one. If nothing is claimable,
   propose a task (`team.py task add`), improve a test, or answer an open review — idling is a protocol
   violation, not a rest state.
5. Blocked? Two honest attempts → roll back to a truthful state → 3-option packet → `msg --to owner`.
6. No commits or pushes unless the owner asks in the session. Money semantics are never guessed (`R1`).

## What the owner (human) does

- Paste a kickoff file into each tool; that is all the setup those agents need.
- Read `team/taskboard.md` or run `python scripts/team.py status` to see live work at any moment.
- Anything an agent needs from you arrives in `team/inbox/owner.md`.
