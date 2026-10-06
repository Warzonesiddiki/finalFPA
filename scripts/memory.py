#!/usr/bin/env python3
"""Continuity layer: the memory an agent keeps, the knowledge the team keeps, and
the brief a *cold* agent reads to resume this project after its daily limit ends.

Why this exists
---------------
Five AI agents share one checkout and several of them are quota-bound. When a seat
stops mid-task, the next seat to touch that path starts with no memory at all: the
code is there, the reasoning behind it is not. The repo already had the answer to
*what is true* (docs/, STATE.md, team/); it had nothing for *what we know*.

Design, and the two rails that shaped it
----------------------------------------
1. Append-only JSONL journals are the source of truth. `MEMORY.md`, `KNOWLEDGE.md`,
   `RESUME.md` and `memory/agents/*.md` are *rendered* from them. A rendered file can
   never lose an entry to a concurrent writer, because nothing is ever edited in place
   except a sentinel-delimited block whose body is regenerated from the journal.
2. One writer per path (R14). The journals are append-only and lock-guarded (O_EXCL,
   exactly like team.py's claims), so many agents may write the same journal safely.
   The rendered per-agent log is the one file an agent owns outright.

Commands
--------
  memory.py add    --kind K --text "..." [--agent A] [--task ID] [--ref PATH]
  memory.py learn  --topic T --text "..." [--agent A] [--ref PATH]
  memory.py render
  memory.py resume [--agent A] [--limit N]      # print the cold-start brief
  memory.py verify                              # the gate; exit 1 on a real problem
  memory.py log   [--agent A] [--limit N]
  memory.py ids

Stdlib only, no runtime dependency (R9 untouched). Windows-safe: every write pins
encoding="utf-8" and newline="\n".
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
# MEMORY_ROOT rebinds the whole module to another tree. It exists so a subprocess
# test (or a dry run) cannot silently write into the production journal: the
# first version of the concurrency test resolved ROOT from __file__ and leaked
# 72 rows into the real one.
ROOT = Path(os.environ.get("MEMORY_ROOT") or SCRIPT_DIR.parents[0]).resolve()
MEM = ROOT / "memory"
JOURNAL = MEM / "journal"
AGENTS_DIR = MEM / "agents"
LOCKS = MEM / "locks"

MEMORY_JOURNAL = JOURNAL / "memory.jsonl"
KNOWLEDGE_JOURNAL = JOURNAL / "knowledge.jsonl"

MEMORY_MD = MEM / "MEMORY.md"
KNOWLEDGE_MD = MEM / "KNOWLEDGE.md"
RESUME_MD = MEM / "RESUME.md"

BEGIN = "<!-- BEGIN GENERATED:memory.py -->"
END = "<!-- END GENERATED:memory.py -->"

# Entry kinds. `state` is "what is true now", `decision` is "we chose and why",
# `blocker` is "what stops us", `handoff` is "work handed to a peer".
MEMORY_KINDS = ("state", "decision", "blocker", "handoff", "note")
# Knowledge topics. Deliberately coarse: a topic is a filing decision, not a taxonomy.
KNOWLEDGE_TOPICS = ("tooling", "windows", "domain", "process", "gate", "product", "trap")

# 60s, not 5s: under real contention every loser re-checks the lock, and on Windows each
# stat is scanned, so a burst of writers can spend most of the timeout queueing rather
# than waiting. Timing out loses an entry, which is worse than waiting.
LOCK_TIMEOUT = 60.0
LOCK_STALE_SECONDS = 60.0
# One number for the published window: a rendered file is stale iff re-rendering
# would change it, so the freshness check and the renderer must agree on it.
RENDER_LIMIT = 40
LOCK_BACKOFF_START = 0.02
LOCK_BACKOFF_CAP = 0.5


# --------------------------------------------------------------------------- basics
def now() -> datetime:
    return datetime.now(UTC)


def stamp(dt: datetime | None = None) -> str:
    return (dt or now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _rel(path: Path) -> str:
    """Repo-relative when possible. Safe when the module is bound to a fixture tree."""
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


def write_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(body, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def bind(root: Path) -> None:
    """Point the whole module at another tree.

    Used by tests/unit/test_memory.py so a fake repo can be built in tmp_path, and
    available for a dry run against a scratch directory. Everything below resolves
    its path through these globals at call time, so rebinding is enough. `team` is
    still imported from the real scripts directory, so the *live* half of RESUME.md
    always reflects the real team, not the fixture.
    """
    global MEM, JOURNAL, AGENTS_DIR, LOCKS
    global MEMORY_JOURNAL, KNOWLEDGE_JOURNAL
    global MEMORY_MD, KNOWLEDGE_MD, RESUME_MD, PROMPT_MD, ROOT
    root = Path(root)
    ROOT = root.resolve()
    MEM = root / "memory"
    JOURNAL = MEM / "journal"
    AGENTS_DIR = MEM / "agents"
    LOCKS = MEM / "locks"
    MEMORY_JOURNAL = JOURNAL / "memory.jsonl"
    KNOWLEDGE_JOURNAL = JOURNAL / "knowledge.jsonl"
    MEMORY_MD = MEM / "MEMORY.md"
    KNOWLEDGE_MD = MEM / "KNOWLEDGE.md"
    RESUME_MD = MEM / "RESUME.md"
    PROMPT_MD = MEM / "CONTINUITY_PROMPT.md"


def team_config() -> dict[str, Any]:
    """Team roster, read live from team/config.json (never duplicated - R12)."""
    cfg: dict[str, Any] = {"leader": "buffy", "agents": ["buffy"], "wip_limit": 2}
    raw = read_text(ROOT / "team" / "config.json")
    if raw:
        try:
            cfg.update(json.loads(raw))
        except json.JSONDecodeError as exc:
            die(f"{_rel(ROOT / 'team' / 'config.json')} is not valid JSON: {exc}")
    return cfg


def resolve_agent(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("TEAM_AGENT", "").strip()
    if env:
        return env
    return str(team_config()["leader"])


# --------------------------------------------------------------------------- locking
def _lock_stale(path: Path) -> bool:
    """Age-based staleness, deliberately not pid-based.

    `os.kill(pid, 0)` is a *terminate* on Windows for any signal other than
    CTRL_C_EVENT/CTRL_BREAK_EVENT, so the usual liveness probe would kill the very
    process holding the lock. mtime age is portable and cannot do that.
    """
    try:
        age = time.time() - path.stat().st_mtime
    except OSError:
        return True
    return age > LOCK_STALE_SECONDS


@contextlib.contextmanager
def _lock(name: str, timeout: float = LOCK_TIMEOUT) -> Iterator[None]:
    LOCKS.mkdir(parents=True, exist_ok=True)
    path = LOCKS / f"{name}.lock"
    deadline = time.monotonic() + timeout
    backoff = LOCK_BACKOFF_START
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _lock_stale(path):
                with contextlib.suppress(OSError):
                    path.unlink()
                continue
            if time.monotonic() > deadline:
                die(f"memory lock {name!r} is held; {path} - "
                    f"delete it by hand if you are sure no other agent is mid-write")
            # Back off instead of polling flat: a dozen agents contending on one
            # lock made every loser re-stat the file 20x a second, which on Windows
            # (each stat scanned) was slower than the write being protected.
            time.sleep(backoff)
            backoff = min(backoff * 1.6, LOCK_BACKOFF_CAP)
            continue
        with contextlib.suppress(OSError):
            os.write(fd, f"{os.getpid()}\n".encode())
            os.close(fd)
        break
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            path.unlink()


# --------------------------------------------------------------------------- journal
def _entries(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.exists():
        return out
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            die(f"{_rel(path)} line {n} is not valid JSON: {exc}")
        if not isinstance(obj, dict):
            die(f"{_rel(path)} line {n} is not a JSON object")
        out.append(obj)
    return out


def _append(path: Path, prefix: str, obj: dict[str, Any]) -> dict[str, Any]:
    """Append one entry under the lock, assigning the next id from what is on disk."""
    with _lock(path.stem):
        existing = _entries(path)
        nxt = 1
        for e in existing:
            m = re.fullmatch(rf"{prefix}-(\d+)", str(e.get("id", "")))
            if m:
                nxt = max(nxt, int(m.group(1)) + 1)
        obj = {"id": f"{prefix}-{nxt:04d}", "utc": stamp(), **obj}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return obj


# --------------------------------------------------------------------------- render
def _fence(body: str) -> str:
    return f"{BEGIN}\n{body.rstrip()}\n{END}\n"


def _splice(text: str, body: str) -> str:
    """Replace only the generated block; hand-written prose around it survives."""
    i, j = text.find(BEGIN), text.find(END)
    if i == -1 or j == -1 or j < i:
        return text.rstrip("\n") + "\n\n" + _fence(body)
    return text[:i] + _fence(body) + text[j + len(END) + 1 :]


def _bullet(e: dict[str, Any]) -> str:
    bits = [f"**{e.get('id', '?')}** `{e.get('utc', '?')}`"]
    who = e.get("agent", "?")
    if who:
        bits.append(who)
    kind = e.get("kind") or e.get("topic")
    if kind:
        bits.append(f"*{kind}*")
    task = e.get("task")
    if task:
        bits.append(f"task `{task}`")
    line = " — ".join(bits)
    text = str(e.get("text", "")).replace("\n", " ").strip()
    ref = e.get("ref")
    tail = f" (see `{ref}`)" if ref else ""
    return f"- {line}: {text}{tail}"


def _render_block(entries: list[dict[str, Any]], limit: int, newest_first: bool = True) -> str:
    rows = entries[-limit:] if newest_first else entries[:limit]
    if newest_first:
        rows = list(reversed(rows))
    return "\n".join(_bullet(e) for e in rows) if rows else "_(no entries yet)_"


def _agent_log_body(agent: str, limit: int) -> str:
    aliases = {agent}
    # Resolve aliases for 'union-based attribution' based on legacy configs or UI defaults
    if agent == "buffy":
        aliases.add("Aion CLI")
    mem = [e for e in _entries(MEMORY_JOURNAL) if str(e.get("agent")) in aliases]
    kno = [e for e in _entries(KNOWLEDGE_JOURNAL) if str(e.get("agent")) in aliases]
    out = [f"## {agent} — recorded knowledge", ""]
    out.append(_render_block(kno, limit) if kno else "_(nothing recorded yet)_")
    out += ["", f"## {agent} — memory", ""]
    out.append(_render_block(mem, limit) if mem else "_(nothing recorded yet)_")
    return "\n".join(out)


def _resume_body(agent: str, limit: int) -> str:
    """The generated half of RESUME.md: live state, so it can never go stale."""
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    import team  # noqa: PLC0415 - local import keeps module import side-effect free

    cfg: dict[str, Any] = dict(team.DEFAULTS)
    cfg.update(team_config())  # team's own defaults, then the bound config
    cs = team.claims()
    active = [c for c in cs if team.is_active(c, cfg)]
    ts = team.tasks()
    by_status: dict[str, int] = {}
    for t in ts.values():
        by_status[str(t.get("status"))] = by_status.get(str(t.get("status")), 0) + 1

    recent = sorted(active, key=lambda c: str(c.get("heartbeat_utc", "")))
    claims_rows = [
        f"- `{c.get('claim_id')}` — {c.get('agent')} on `{c.get('task')}` "
        f"(scopes: {', '.join(c.get('scopes', [])) or '—'})"
        for c in recent
    ] or ["_(no live claims — every seat is idle; take the top of your stream)_"]

    blocked = [t for t in ts.values() if t.get("status") in ("blocked", "todo") and t.get("deps")]
    blocked_rows = [
        f"- `{t['id']}` waits on {', '.join(str(d) for d in t['deps'])}"
        for t in sorted(blocked, key=lambda x: str(x["id"]))
    ][:12] or ["_(no dependency-blocked cards)_"]

    mine = [x for x in cfg.get("streams", {}).get(agent, []) if x in ts]
    mine_rows = [
        f"- `{tid}` [{ts[tid].get('priority')}] {ts[tid].get('status')}"
        f" — {str(ts[tid].get('title'))[:110]}"
        for tid in mine
    ] or [f"_(no stream configured for {agent}; ask the leader)_"]

    kno = [e for e in _entries(KNOWLEDGE_JOURNAL) if e.get("topic") == "trap"][-limit:]
    trap_rows = [_bullet(e) for e in reversed(kno)] or [
        "_(none recorded yet - add them with: python scripts/memory.py learn --topic trap --text ...)_"
    ]

    blockers = [e for e in _entries(MEMORY_JOURNAL) if e.get("kind") == "blocker"][-limit:]
    blocker_rows = [_bullet(e) for e in reversed(blockers)] or ["_(none recorded)_"]

    away = {str(k): str(v) for k, v in (cfg.get("away") or {}).items()}
    away_rows = [f"- `{a}` — {why}" for a, why in sorted(away.items())]

    parts = [
        f"<!-- seat: {agent} (leader: {cfg['leader']}) -->",
        "",
        "### Live team state",
        "",
        f"- Cards: {len(ts)} total — " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())),
        f"- Live claims: {len(active)}",
        f"- **You are {'AWAY' if agent in away else 'active'}.**"
        + (f" Reason recorded: {away[agent]}" if agent in away else ""),
        *away_rows,
        "",
        *claims_rows,
        "",
        "### Open blockers recorded in memory",
        "",
        *blocker_rows,
        "",
        "### Dependency-blocked cards",
        "",
        *blocked_rows,
        "",
        f"### {agent}'s stream (in order)",
        "",
        *mine_rows,
        "",
        "### Traps that have already cost time",
        "",
        *trap_rows,
    ]
    return "\n".join(parts)


def render(agent: str = "buffy", limit: int = 40) -> list[Path]:
    """Regenerate every derived file. Safe to run at any time; never loses an entry."""
    written: list[Path] = []

    mem = _entries(MEMORY_JOURNAL)
    kno = _entries(KNOWLEDGE_JOURNAL)
    for path, body in (
        (MEMORY_MD, _render_block(mem, limit)),
        (KNOWLEDGE_MD, _render_block(kno, limit)),
    ):
        write_text(path, _splice(read_text(path), body))
        written.append(path)

    for a in [str(x) for x in team_config()["agents"]]:
        p = AGENTS_DIR / f"{a}.md"
        write_text(p, _splice(read_text(p), _agent_log_body(a, limit)))
        written.append(p)

    write_text(RESUME_MD, _splice(read_text(RESUME_MD), _resume_body(agent, limit)))
    written.append(RESUME_MD)
    return written


# --------------------------------------------------------------------------- verify
REQUIRED_RESUME_SECTIONS = (
    "## 0. How to read this file",
    "## 1. What this project is",
    "## 2. Hard rails",
    "## 3. Where the truth lives",
    "## 4. The working loop",
    "## 5. Recording protocol",
)


def _check_journal(path: Path, prefix: str, field: str, allowed: tuple[str, ...],
                   known: set[str]) -> tuple[list[str], list[str]]:
    """Shape check for one journal. Split out of verify() to keep each branch testable."""
    fails: list[str] = []
    warns: list[str] = []
    rel = _rel(path)
    if not path.exists():
        return [f"{rel} is missing"], warns
    seen: set[str] = set()
    high = 0
    for e in _entries(path):
        eid = str(e.get("id", ""))
        if not re.fullmatch(rf"{prefix}-\d{{4,}}", eid):
            fails.append(f"{rel}: malformed id {eid!r} (want {prefix}-NNNN)")
            continue
        if eid in seen:
            fails.append(f"{rel}: duplicate id {eid}")
        seen.add(eid)
        high = max(high, int(eid.split("-")[1]))
        if not str(e.get("utc", "")).endswith("Z"):
            fails.append(f"{rel}: {eid} has no UTC stamp ({e.get('utc')!r})")
        agent = str(e.get("agent", ""))
        if agent not in known:
            fails.append(f"{rel}: {eid} attributed to unknown agent {agent!r}")
        val = e.get(field)
        if val not in allowed:
            fails.append(f"{rel}: {eid} has {field}={val!r}; expected one of {list(allowed)}")
        if not str(e.get("text", "")).strip():
            fails.append(f"{rel}: {eid} has an empty text")
    if seen and high != len(seen):
        warns.append(f"{rel}: ids are not dense (highest {high}, {len(seen)} entries)")
    return fails, warns


def _check_files(known: set[str]) -> list[str]:
    fails: list[str] = []
    for a in sorted(known):
        p = AGENTS_DIR / f"{a}.md"
        if not p.exists():
            fails.append(f"memory/agents/{a}.md is missing (every seat must own a log)")
        elif BEGIN not in read_text(p):
            fails.append(f"memory/agents/{a}.md has no generated block - run `memory.py render`")
    for path in (MEMORY_MD, KNOWLEDGE_MD, RESUME_MD):
        if not path.exists():
            fails.append(f"{_rel(path)} is missing")
        elif BEGIN not in read_text(path):
            fails.append(f"{_rel(path)} has no generated block - run `memory.py render`")
    fails += _check_resume_sections()
    if not _entries(MEMORY_JOURNAL):
        fails.append("memory/journal/memory.jsonl is empty - the team has no recorded memory")
    if not _entries(KNOWLEDGE_JOURNAL):
        fails.append("memory/journal/knowledge.jsonl is empty - the team has no recorded knowledge")
    return fails


def _check_resume_sections() -> list[str]:
    """A cold agent must find every section, so a lost heading is a build failure."""
    resume = read_text(RESUME_MD)
    if not resume:
        return []
    return [f"memory/RESUME.md is missing the section '{sec}' - a cold agent needs it to "
            f"resume without asking"
            for sec in REQUIRED_RESUME_SECTIONS if sec not in resume]


def _check_freshness() -> list[str]:
    """The rendered block must equal a fresh render of the journal it came from."""
    warns: list[str] = []
    for path, journal in ((MEMORY_MD, MEMORY_JOURNAL), (KNOWLEDGE_MD, KNOWLEDGE_JOURNAL)):
        if not path.exists():
            continue
        fresh = _splice(read_text(path), _render_block(_entries(journal), RENDER_LIMIT))
        if read_text(path) != fresh:
            warns.append(f"{_rel(path)} is behind its journal - "
                         f"run `python scripts/memory.py render`")
    return warns


def verify() -> tuple[list[str], list[str]]:
    """The gate. Returns (fails, warns); every check below is falsifiable."""
    known = {str(a) for a in team_config()["agents"]}
    fails: list[str] = []
    warns: list[str] = []
    for path, prefix, field, allowed in (
        (MEMORY_JOURNAL, "M", "kind", MEMORY_KINDS),
        (KNOWLEDGE_JOURNAL, "K", "topic", KNOWLEDGE_TOPICS),
    ):
        f, w = _check_journal(path, prefix, field, allowed, known)
        fails += f
        warns += w
    fails += _check_files(known)
    warns += _check_freshness()
    return fails, warns


# --------------------------------------------------------------------------- renderers
def _print_brief(agent: str, limit: int) -> int:
    body = read_text(RESUME_MD)
    print(body if body.strip() else "memory/RESUME.md is empty - run `python scripts/memory.py render`")
    print("\n" + "=" * 78)
    print(f"LIVE BRIEF for seat '{agent}' (regenerated now, never stale)")
    print("=" * 78)
    print(_resume_body(agent, limit))
    return 0


def _print_log(agent: str, limit: int) -> int:
    for title, path in (("MEMORY", MEMORY_JOURNAL), ("KNOWLEDGE", KNOWLEDGE_JOURNAL)):
        rows = [e for e in _entries(path) if not agent or e.get("agent") == agent]
        print(f"\n== {title} ({len(rows)} entries{' for ' + agent if agent else ''}) ==")
        print(_render_block(rows, limit) if rows else "_(none)_")
    return 0


# --------------------------------------------------------------------------- commands
def cmd_add(args: argparse.Namespace) -> int:
    agent = resolve_agent(args.agent)
    if args.kind not in MEMORY_KINDS:
        die(f"--kind must be one of {list(MEMORY_KINDS)}")
    if not args.text.strip():
        die("--text must not be empty")
    e = _append(MEMORY_JOURNAL, "M", {
        "agent": agent, "kind": args.kind, "text": args.text.strip(),
        "task": args.task, "ref": args.ref,
    })
    print(f"{e['id']} recorded ({agent}/{args.kind}) - run `python scripts/memory.py render` to publish")
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    agent = resolve_agent(args.agent)
    if args.topic not in KNOWLEDGE_TOPICS:
        die(f"--topic must be one of {list(KNOWLEDGE_TOPICS)}")
    if not args.text.strip():
        die("--text must not be empty")
    e = _append(KNOWLEDGE_JOURNAL, "K", {
        "agent": agent, "topic": args.topic, "text": args.text.strip(), "ref": args.ref,
    })
    print(f"{e['id']} recorded ({agent}/{args.topic}) - run `python scripts/memory.py render` to publish")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    for p in render(resolve_agent(args.agent), args.limit):
        print(f"wrote {_rel(p)}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    return _print_brief(resolve_agent(args.agent), args.limit)


def cmd_verify(args: argparse.Namespace) -> int:
    fails, warns = verify()
    for w in warns:
        print(f"WARN {w}")
    for f in fails:
        print(f"FAIL {f}")
    print(f"memory: {len(fails)} fail, {len(warns)} warn")
    return 1 if fails else 0


def cmd_log(args: argparse.Namespace) -> int:
    return _print_log(resolve_agent(args.agent) if args.all else args.agent, args.limit)


PROMPT_MD = MEM / "CONTINUITY_PROMPT.md"
PROMPT_FROM = "## Paste from here"
PROMPT_TO = "## Paste to here"


def cmd_prompt(args: argparse.Namespace) -> int:
    """Print the member prompt verbatim - one command to copy it to every seat."""
    text = read_text(PROMPT_MD)
    i, j = text.find(PROMPT_FROM), text.find(PROMPT_TO)
    if i == -1 or j == -1 or j < i:
        die(f"{_rel(PROMPT_MD)} lost its '{PROMPT_FROM}' / '{PROMPT_TO}' delimiters")
    print(text[i + len(PROMPT_FROM):j].strip())
    return 0


def cmd_ids(args: argparse.Namespace) -> int:
    for path in (MEMORY_JOURNAL, KNOWLEDGE_JOURNAL):
        print(f"{_rel(path)}: {len(_entries(path))} entries")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="memory.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add", help="record one memory entry")
    s.add_argument("--kind", required=True, choices=list(MEMORY_KINDS))
    s.add_argument("--text", required=True)
    s.add_argument("--agent")
    s.add_argument("--task")
    s.add_argument("--ref")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("learn", help="record one knowledge entry (a lesson, a trap, a convention)")
    s.add_argument("--topic", required=True, choices=list(KNOWLEDGE_TOPICS))
    s.add_argument("--text", required=True)
    s.add_argument("--agent")
    s.add_argument("--ref")
    s.set_defaults(fn=cmd_learn)

    s = sub.add_parser("render", help="regenerate MEMORY/KNOWLEDGE/RESUME/agent logs")
    s.add_argument("--agent")
    s.add_argument("--limit", type=int, default=40)
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("resume", help="print the cold-start brief")
    s.add_argument("--agent")
    s.add_argument("--limit", type=int, default=12)
    s.set_defaults(fn=cmd_resume)

    s = sub.add_parser("verify", help="integrity gate")
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("log", help="show recorded entries")
    s.add_argument("--agent")
    s.add_argument("--all", action="store_true")
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("prompt", help="print the standing prompt for a team member")
    s.set_defaults(fn=cmd_prompt)

    s = sub.add_parser("ids", help="count entries per journal")
    s.set_defaults(fn=cmd_ids)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.fn(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())