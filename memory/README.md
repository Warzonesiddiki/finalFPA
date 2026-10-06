# `memory/` — the continuity layer

Five AI agents share one checkout and several are quota-bound. When a seat stops
mid-task, the next seat to touch that path inherits code and no reasoning. This
directory is that reasoning, in a form a **cold** agent can use without a briefing.

## The three questions, three files

| Question | File | Shape |
|---|---|---|
| *How do I resume this project?* | [RESUME.md](RESUME.md) | authored rules + **generated live state** |
| *What is true right now?* | [MEMORY.md](MEMORY.md) | authored orientation + **generated entry list** |
| *What have we learned?* | [KNOWLEDGE.md](KNOWLEDGE.md) | authored index + **generated entry list** |
| *What did **I** do and learn?* | [`agents/<seat>.md`](agents/) | generated, one file per seat |

**Start every session here:** `python scripts/memory.py resume --agent <your-seat>`

## Architecture

```
memory/journal/memory.jsonl     append-only  ── source of truth for MEMORY.md
memory/journal/knowledge.jsonl  append-only  ── source of truth for KNOWLEDGE.md
        │
        │  scripts/memory.py render   (idempotent; rewrites only the sentinelled block)
        ▼
memory/MEMORY.md  memory/KNOWLEDGE.md  memory/agents/<seat>.md
        │
        │  scripts/memory.py render   (live state recomputed from team/ + journals)
        ▼
memory/RESUME.md
```

**Source of truth is JSONL, not markdown.** Appending to a file cannot lose another
agent's entry; editing a shared markdown file can. Every rendered `.md` keeps its
hand-written prose and regenerates only the block between
`<!-- BEGIN GENERATED:memory.py -->` and `<!-- END GENERATED:memory.py -->`. Hand-edits
inside that block are lost by design — that is the error the architecture prevents.

**Locking is `O_EXCL`**, the same primitive as `team.py`'s claims. Staleness is decided
by lock mtime age, not by a pid probe: `os.kill(pid, 0)` *terminates* on Windows, so the
usual liveness check would kill the process holding the lock.

**R14 (one writer per path) holds** because nobody hand-edits a rendered file, and
`memory/agents/<seat>.md` is a seat's own file. The two journals are append-only and
lock-guarded, so many agents may write them concurrently.

**`memory/` is excluded from `team.py`'s claim-window scan** (`_window_edits`), for the
same reason `team/`, `scratch/` and `vendor/` are: every agent writes here by design,
and flagging it would teach agents to ignore the flag. The layer's own integrity is
enforced instead by `scripts/memory.py verify`, which is a real gate with falsification
tests — it fails on a duplicate id, an unknown agent, a bad kind/topic, an empty entry,
a missing RESUME section, a missing per-seat log, or an empty journal.

## Commands

```bash
python scripts/memory.py add   --kind state|decision|blocker|handoff|note --text "..." \
                               [--agent SEAT] [--task ID] [--ref PATH]
python scripts/memory.py learn --topic tooling|windows|domain|process|gate|product|trap --text "..."
python scripts/memory.py render [--agent SEAT] [--limit N]
python scripts/memory.py resume [--agent SEAT] [--limit N]
python scripts/memory.py verify
python scripts/memory.py log   [--agent SEAT | --all] [--limit N]
python scripts/memory.py prompt                       # print the member prompt verbatim
python scripts/memory.py ids
```

`--agent` defaults to `$TEAM_AGENT`, then to the leader in `team/config.json`; the
command always prints which seat it recorded under, so an unattributed entry is not
possible by accident.

## Adding a topic or kind

Both are declared once, as tuples at the top of
[scripts/memory.py](../scripts/memory.py) (`MEMORY_KINDS`, `KNOWLEDGE_TOPICS`) and
**validated on write**, so a typo is rejected at the point of entry rather than
silently creating an unreadable category. If you add one, add the row to
[KNOWLEDGE.md](KNOWLEDGE.md) in the same change.

## Rules

1. The journals are the record. The markdown is a view.
2. Never hand-edit a generated block. Add an entry and render.
3. Record before you stop, especially when stopping because of a limit.
4. Record only what you observed. A remembered number is not a measured one.
5. `python scripts/memory.py verify` must exit 0 before you hand anything on.
