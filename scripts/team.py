"""``team.py`` — the coordination layer for the four-agent team (see ``team/README.md``).

Stdlib only (no new dependency, R9/ADR-002). Windows-safe UTF-8 output (cp1252 cannot print the
project's unicode). Nothing here changes product behaviour; `scripts/check.py` is untouched by design
(its contents are specified in `14` §13.1 — wiring this in would be a spec change).

Commands
--------
  status                          who is alive, what is claimed, what is stale, next claimable task
  tasks [--all]                   print the task queue
  task add --title T [--tb TB-nnn] [--priority P1] [--deps d1,d2] [--lane L] [--by A]
  task show <id> | task set <id> --status S [--note ...]
  claim --agent A (--task ID | --title T) [--scope P]... [--kind K] [--ttl N] [--steal CLAIM_ID]
  touch --claim ID
  release --claim ID [--handoff HO-nnn] [--done] [--note ...]
  handoff --claim ID --summary S --changed P --tests S --docsync S --evidence S --next S
  verify --task ID --by AGENT [--handoff HO-nnn] [--note ...]
  msg --from A --to B --text T        (B may be `owner`)
  note --text T                       (append-only team log)
  board | digest                      regenerate the derived views
  check [--strict]                    machine-enforced invariants; exit 1 on violation
  sync                                import new open TB rows from docs/33 as tasks (never clobbers)
  preflight --capability TEXT         Addon 6 §1 decision-tree check for a capability

Files it owns: team/claims/*.json (atomic, O_EXCL), team/tasks/*.json, team/handoffs/HO-*.md,
team/inbox/*.md, team/log/<date>.md, team/state/heartbeat/*.json, team/taskboard.md, team/digest.md.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
TEAM = ROOT / "team"
CLAIMS = TEAM / "claims"
TASKS = TEAM / "tasks"
HANDOFFS = TEAM / "handoffs"
INBOX = TEAM / "inbox"
LOGS = TEAM / "log"
HB = TEAM / "state" / "heartbeat"
DOC33 = ROOT / "docs" / "33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md"

DEFAULTS = {
    "leader": "buffy",
    "agents": ["buffy", "antigravity", "opencode", "freebuff2"],
    "wip_limit": 2,
    "default_ttl_minutes": 120,
    "agent_idle_minutes": 30,
    "leader_only_paths": ["docs/18_GLOSSARY_ASSUMPTIONS_OPEN_QUESTIONS.md", "docs/SESSION_LOG.md",
                          "docs/33_EXECUTION_BLUEPRINT_AND_TASKBOARD.md", "docs/00_INDEX.md",
                          "CHANGELOG.md", "STATE.md", "team/", "project prompt/"],
    "orphan_ignore": [".coverage", "coverage.xml", "evidence/acceptance_report.json",
                      "evidence/acceptance_report.md", "scratch/", "memory/", "*.pyc",
                      "__pycache__/", ".pytest_cache/", "*.log"],
    "lanes": {},
}
TASK_STATUSES = ("todo", "blocked", "claimed", "in-progress", "review", "done")
HANDOFF_SECTIONS = ("## Claim", "## Changed", "## Verification", "## Doc-sync", "## Evidence", "## Next")


# --------------------------------------------------------------------------- helpers
def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(dt: datetime | None = None) -> str:
    return (dt or now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return now().strftime("%Y-%m-%d")


def config() -> dict:
    cfg = dict(DEFAULTS)
    f = TEAM / "config.json"
    if f.exists():
        try:
            cfg.update(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            die(f"team/config.json is not valid JSON: {exc}")
    return cfg


def die(msg: str, code: int = 2) -> "None":
    print(f"ERROR: {msg}")
    sys.exit(code)


def ensure_dirs() -> None:
    for d in (CLAIMS, TASKS, HANDOFFS, INBOX, LOGS, HB):
        d.mkdir(parents=True, exist_ok=True)


def norm(path: str) -> str:
    return path.replace("\\", "/").strip().strip('"').rstrip("/")


def has_glob(s: str) -> bool:
    return any(ch in s for ch in "*?[")


def _base(s: str) -> str:
    return norm(s).split("*")[0].split("?")[0].split("[")[0].rstrip("/")


def scopes_overlap(a: str, b: str) -> bool:
    """Conservative path-overlap test: false positives are cheap, collisions are not."""
    na, nb = norm(a), norm(b)
    if na == nb:
        return True
    ba, bb = _base(na), _base(nb)
    if ba == bb:
        return True
    if ba and bb and (ba.startswith(bb + "/") or bb.startswith(ba + "/")):
        return True
    if has_glob(na) and fnmatch.fnmatch(nb, na):
        return True
    if has_glob(nb) and fnmatch.fnmatch(na, nb):
        return True
    # glob on one side, literal nested under the glob's base
    if has_glob(na) and bb and (bb == ba or bb.startswith(ba + "/")):
        return True
    if has_glob(nb) and ba and (ba == bb or ba.startswith(bb + "/")):
        return True
    return False


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def claims() -> list[dict]:
    out = []
    if CLAIMS.exists():
        for f in sorted(CLAIMS.glob("*.json")):
            c = read_json(f)
            if c:
                c["_file"] = str(f)
                out.append(c)
    return out


def tasks() -> dict[str, dict]:
    out = {}
    if TASKS.exists():
        for f in sorted(TASKS.glob("*.json")):
            t = read_json(f)
            if t and t.get("id"):
                out[t["id"]] = t
    return out


def claim_by_id(cid: str) -> dict:
    for c in claims():
        if c.get("claim_id") == cid:
            return c
    die(f"no such claim: {cid}")


def is_active(c: dict, cfg: dict) -> bool:
    """A claim blocks paths only while it is live: not released/closed, not past its TTL."""
    return not c.get("closed_utc") and not expired(c, cfg)


def expired(c: dict, cfg: dict) -> bool:
    try:
        hb = datetime.strptime(c.get("heartbeat_utc", ""), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True
    return now() > hb + timedelta(minutes=int(c.get("ttl_minutes", cfg["default_ttl_minutes"])))


def heartbeat(agent: str, note: str = "") -> None:
    write_json(HB / f"{agent}.json", {"agent": agent, "utc": stamp(), "note": note})


def log_note(agent: str, text: str) -> None:
    ensure_dirs()
    f = LOGS / f"{today()}.md"
    if not f.exists():
        f.write_text(f"# Team log — {today()}\n\n", encoding="utf-8", newline="\n")
    with f.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"- `{stamp()}` **{agent}** — {text}\n")


def tb_ids_in_docs33() -> set[str]:
    if not DOC33.exists():
        return set()
    return set(re.findall(r"TB-\d{3}", DOC33.read_text(encoding="utf-8")))


def git_changed_paths() -> list[str]:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return []
    if r.returncode != 0:
        return []
    paths = []
    for line in r.stdout.splitlines():
        if len(line) < 4:
            continue
        p = line[3:].strip()
        if " -> " in p:  # rename
            p = p.split(" -> ", 1)[1]
        paths.append(norm(p.strip('"')))
    return paths


def covered(path: str, active: list[dict], cfg: dict) -> bool:
    for pat in cfg.get("orphan_ignore", []):
        if covered_by_pattern(path, pat):
            return True
    for c in active:
        for s in c.get("scopes", []):
            if covered_by_pattern(path, s):
                return True
    return False


def _section(text: str, heading: str) -> str:
    """Body of one markdown section (up to the next `## ` heading)."""
    m = re.search(rf"^{re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)", text, re.M)
    return m.group(1) if m else ""


def covered_by_pattern(path: str, pattern: str) -> bool:
    p, pat = norm(path), norm(pattern)
    if p == pat:
        return True
    if pat.endswith("/") and p.startswith(pat):
        return True
    if has_glob(pat):
        return fnmatch.fnmatch(p, pat) or fnmatch.fnmatch("/" + p, pat)
    return p.startswith(pat + "/")


def next_handoff_id() -> str:
    n = 1
    for f in HANDOFFS.glob("HO-*.md"):
        m = re.match(r"HO-(\d+)", f.name)
        if m:
            n = max(n, int(m.group(1)) + 1)
    return f"HO-{n:03d}"


def write_handoff_atomic(start_id: str, body: str, hint: str) -> tuple[str, str]:
    """Create a handoff so that **no two files ever share an id**.

    The atomic unit is the *number*, not the filename: two agents writing different slugs would
    otherwise both get ``HO-004-something`` and ``verify --handoff HO-004`` would be ambiguous (which
    happened once on 2026-10-05). A ``HO-nnn.lock`` sentinel created with ``O_EXCL`` is the lock; the
    number advances whenever the sentinel or any existing file for that number is present.
    """
    n = int(start_id.split("-")[1])
    while True:
        hid = f"HO-{n:03d}"
        lock = HANDOFFS / f"{hid}.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            n += 1
            continue
        os.close(fd)
        taken = [HANDOFFS / f"{hid}.md"] + list(HANDOFFS.glob(f"{hid}-*.md"))
        if any(p.exists() for p in taken):
            lock.unlink(missing_ok=True)
            n += 1
            continue
        path = HANDOFFS / f"{hid}-{hint}.md"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body.replace("__HID__", hid))
        lock.unlink(missing_ok=True)
        return hid, path.name


def resolve_handoff(hid: str) -> Path:
    """Exactly one handoff, or an error: an id matching two files is not verifiable."""
    exact = HANDOFFS / f"{hid}.md"
    if exact.exists():
        return exact
    matches = sorted(HANDOFFS.glob(f"{hid}*.md"))
    if not matches:
        die(f"handoff {hid} not found in team/handoffs/")
    if len(matches) > 1:
        die(f"handoff id {hid} is ambiguous: {[m.name for m in matches]} - pass a longer prefix")
    return matches[0]


def slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:n] or "work"


# --------------------------------------------------------------------------- commands
def cmd_status(args: argparse.Namespace) -> int:
    cfg = config()
    cs, ts = claims(), tasks()
    act = [c for c in cs if is_active(c, cfg)]
    stale = [c for c in cs if not c.get("closed_utc") and expired(c, cfg)]
    print(f"== TEAM STATUS  {stamp()} ==")
    print("Agents                last seen        active claims")
    for a in cfg["agents"]:
        hb = read_json(HB / f"{a}.json") or {}
        last = hb.get("utc")
        if last:
            try:
                dt = datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                mins = int((now() - dt).total_seconds() // 60)
                seen = f"{mins} min ago" if mins < 120 else f"{mins // 60} h ago"
            except ValueError:
                seen = last
        else:
            seen = "never"
        mine = [c for c in act if c.get("agent") == a]
        label = ", ".join(f"{c.get('task') or c.get('claim_id')}" for c in mine) or "-"
        print(f"  {a:<20}{seen:<17}{label}")
    print(f"Claims: {len(act)} active, {len(stale)} stale")
    for c in act:
        left = int(c.get("ttl_minutes", cfg["default_ttl_minutes"]))
        print(f"  {c.get('claim_id'):<34}{c.get('agent'):<14}{(c.get('task') or '-'):<10}"
              f"{c.get('kind', ''):<10}scopes={', '.join(c.get('scopes', []))[:80]} ttl={left}m")
    for c in stale:
        print(f"  STALE {c.get('claim_id')} ({c.get('agent')}) — takeover with: "
              f"team.py claim --steal {c.get('claim_id')}")
    by = {}
    for t in ts.values():
        by[t.get("status", "todo")] = by.get(t.get("status", "todo"), 0) + 1
    print("Tasks: " + "  ".join(f"{k} {v}" for k, v in sorted(by.items())) or "Tasks: none")
    claimable = [t for t in ts.values() if t.get("status", "todo") == "todo" and deps_ok(t, ts)]
    claimable.sort(key=lambda t: (t.get("priority", "P3"), t.get("id", "")))
    if claimable:
        t = claimable[0]
        print(f"Next claimable: {t['id']} [{t.get('priority', 'P3')}] {t.get('lane', '')} — {t.get('title', '')[:90]}")
    orphans = [p for p in git_changed_paths() if not covered(p, act, cfg)]
    print(f"Working-tree edits not covered by an active claim: {len(orphans)}"
          + (f" (e.g. {', '.join(orphans[:5])})" if orphans else ""))
    return 0


def cmd_tasks(args: argparse.Namespace) -> int:
    ts = tasks()
    show = [t for t in ts.values() if args.all or t.get("status", "todo") != "done"]
    show.sort(key=lambda t: (t.get("status", "todo") != "todo", t.get("priority", "P3"), t.get("id", "")))
    print(f"{'ID':<9}{'P':<4}{'STATUS':<12}{'OWNER':<14}{'LANE':<12}TITLE")
    for t in show:
        print(f"{t.get('id',''):<9}{t.get('priority','P3'):<4}{t.get('status','todo'):<12}"
              f"{(t.get('owner') or '-'):<14}{(t.get('lane') or '-'):<12}{t.get('title','')[:80]}")
    return 0


def cmd_task_add(args: argparse.Namespace) -> int:
    cfg = config()
    ts = tasks()
    if args.tb:
        tid = args.tb
    else:
        nums = [int(m.group(1)) for t in ts if (m := re.fullmatch(r"T-(\d{3})", t))]
        tid = f"T-{max(nums, default=0) + 1:03d}"
        while (TASKS / f"{tid}.json").exists():
            tid = f"T-{int(tid.split('-')[1]) + 1:03d}"
    if args.tb and tid in tasks():
        print(f"task {tid} already present")
        return 0
    t = {"id": tid, "title": args.title, "source": "docs/33" if args.tb else (args.by or "team"),
         "priority": args.priority, "status": "todo", "owner": None, "claim_id": None,
         "deps": [d for d in (args.deps or "").split(",") if d.strip()],
         "lane": args.lane or "", "created_utc": stamp(), "updated_utc": stamp(),
         "history": [{"utc": stamp(), "agent": args.by or "?", "event": "created"}]}
    write_json(TASKS / f"{tid}.json", t)
    log_note(args.by or "?", f"task created: `{tid}` — {args.title}")
    print(f"task {tid} created")
    return 0


def cmd_task_set(args: argparse.Namespace) -> int:
    ts = tasks()
    if args.id not in ts:
        die(f"no such task: {args.id}")
    t = ts[args.id]
    if args.status:
        if args.status not in TASK_STATUSES:
            die(f"status must be one of {TASK_STATUSES}")
        t["status"] = args.status
    if args.priority:
        t["priority"] = args.priority
    if args.lane:
        t["lane"] = args.lane
    if args.note:
        t.setdefault("history", []).append({"utc": stamp(), "agent": args.by or "?", "event": args.note})
    t["updated_utc"] = stamp()
    write_json(TASKS / f"{args.id}.json", t)
    print(f"{args.id} → {t['status']}")
    return 0


def deps_ok(t: dict, ts: dict[str, dict]) -> bool:
    for d in t.get("deps", []):
        dep = ts.get(d)
        if dep is None:
            continue  # unknown dep (e.g. a milestone label) — not a blocker here
        if dep.get("status") != "done":
            return False
    return True


def cmd_claim(args: argparse.Namespace) -> int:
    cfg = config()
    ensure_dirs()
    agent = args.agent
    if agent not in cfg["agents"]:
        die(f"unknown agent {agent!r}; add it to team/config.json first")
    ts, cs = tasks(), claims()
    act = [c for c in cs if is_active(c, cfg)]

    # steal path
    if args.steal:
        old = claim_by_id(args.steal)
        if not expired(old, cfg):
            die(f"{args.steal} is still live (heartbeat {old.get('heartbeat_utc')}); it cannot be stolen")
        log_note(agent, f"STALE TAKEOVER of `{args.steal}` from {old.get('agent')}")
        msg(agent, str(old.get("agent")), f"I am taking over your stale claim {args.steal} "
                                         f"(heartbeat {old.get('heartbeat_utc')}, TTL {old.get('ttl_minutes')}m).")
        old["agent"] = agent
        old["heartbeat_utc"] = stamp()
        old.setdefault("history", []).append({"utc": stamp(), "agent": agent, "event": "steal"})
        write_json(Path(old["_file"]), {k: v for k, v in old.items() if k != "_file"})
        if old.get("task") and old["task"] in ts:
            ts[old["task"]]["owner"] = agent
            write_json(TASKS / f"{old['task']}.json", ts[old["task"]])
        print(f"stole {args.steal}; you now hold it (scopes: {', '.join(old.get('scopes', []))})")
        return 0

    if args.task:
        if args.task not in ts:
            die(f"no such task: {args.task} (see `team.py tasks`)")
        t = ts[args.task]
        if t.get("status") in ("claimed", "in-progress") and t.get("owner") != agent:
            die(f"{args.task} is already held by {t.get('owner')} (status {t.get('status')})")
        if t.get("status") == "done":
            die(f"{args.task} is done; create a new task or reopen it with `task set`")
        if not deps_ok(t, ts) and not args.force:
            missing = [d for d in t.get("deps", []) if ts.get(d, {}).get("status") != "done"]
            die(f"{args.task} is not claimable yet: deps not done: {missing} (--force to override, logged)")
        title, scopes = t.get("title", args.task), list(args.scope or [])
    else:
        if not args.title:
            die("give --task ID or --title TEXT")
        title, scopes = args.title, list(args.scope or [])
        t = None
    if not scopes:
        die("at least one --scope PATH is required (a claim is a promise about paths)")

    # WIP + overlap + leader-only checks
    mine = [c for c in act if c.get("agent") == agent]
    if len(mine) >= int(cfg["wip_limit"]) and not args.force:
        die(f"WIP limit {cfg['wip_limit']} reached for {agent}: release or hand off first "
            f"({', '.join(c.get('claim_id', '') for c in mine)})")
    for c in act:
        for s1 in scopes:
            for s2 in c.get("scopes", []):
                if scopes_overlap(s1, s2):
                    die(f"scope {s1} overlaps {s2} in {c.get('claim_id')} held by {c.get('agent')}; "
                        f"wait for release or take over if stale")
    for p in cfg.get("do_not_claim", []):
        for s in scopes:
            if scopes_overlap(s, p):
                die(f"{s} is off-limits ({p}): it is the owner's own file, not the team's — never claim it")
    if agent != cfg["leader"]:
        for p in cfg["leader_only_paths"]:
            for s in scopes:
                if covered_by_pattern(_base(s) or s, p) or covered_by_pattern(p, s) or scopes_overlap(s, p):
                    die(f"{s} is leader-only ({p}); put the change in a handoff and message {cfg['leader']}")

    cid = f"{agent}-{now().strftime('%Y%m%dT%H%MZ')}-{secrets.token_hex(2)}"
    c = {"claim_id": cid, "agent": agent, "task": t["id"] if t else None, "title": title,
         "kind": args.kind or ("engine" if any(s.startswith("app/") for s in scopes) else "docs"),
         "scopes": scopes, "opened_utc": stamp(), "heartbeat_utc": stamp(),
         "ttl_minutes": int(args.ttl or cfg["default_ttl_minutes"]),
         "notes": args.note or "", "history": [{"utc": stamp(), "agent": agent, "event": "claimed"}]}
    path = CLAIMS / f"{cid}.json"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # atomic: cannot race another claim
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
    if t is not None:
        t["status"] = "in-progress"
        t["owner"] = agent
        t["claim_id"] = cid
        t.setdefault("history", []).append({"utc": stamp(), "agent": agent, "event": "claimed"})
        t["updated_utc"] = stamp()
        write_json(TASKS / f"{t['id']}.json", t)
    heartbeat(agent, f"claimed {t['id'] if t else title}")
    log_note(agent, f"claimed `{t['id'] if t else title}` ({cid}); scopes: {', '.join(scopes)}")
    print(f"claimed {cid}\n  task: {t['id'] if t else title}\n  scopes: {', '.join(scopes)}\n"
          f"  ttl: {c['ttl_minutes']}m — renew with `team.py touch --claim {cid}`")
    return 0


def cmd_touch(args: argparse.Namespace) -> int:
    c = claim_by_id(args.claim)
    c["heartbeat_utc"] = stamp()
    c.setdefault("history", []).append({"utc": stamp(), "agent": args.agent or c.get("agent"), "event": "touch"})
    write_json(Path(c["_file"]), {k: v for k, v in c.items() if k != "_file"})
    heartbeat(args.agent or c.get("agent", "?"), f"touch {args.claim}")
    print(f"{args.claim} heartbeat renewed ({stamp()})")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    c = claim_by_id(args.claim)
    ts = tasks()
    if args.handoff:
        resolve_handoff(args.handoff)
    if args.done and not args.handoff:
        die("--done requires --handoff HO-nnn (the review gate: a handoff must exist before done)")
    c["closed_utc"] = stamp()
    c["closed_note"] = args.note or ("done" if args.done else "released")
    c["heartbeat_utc"] = stamp()
    c.setdefault("history", []).append({"utc": stamp(), "agent": args.agent or c.get("agent"),
                                        "event": "done" if args.done else "released"})
    write_json(Path(c["_file"]), {k: v for k, v in c.items() if k != "_file"})
    if c.get("task") and c["task"] in ts:
        t = ts[c["task"]]
        t["status"] = "review" if args.handoff else ("done" if args.done else "todo")
        if t["status"] == "todo":
            t["owner"], t["claim_id"] = None, None
        t["handoff"] = args.handoff
        t.setdefault("history", []).append({"utc": stamp(), "agent": c.get("agent"),
                                            "event": f"release ({t['status']})"})
        t["updated_utc"] = stamp()
        write_json(TASKS / f"{c['task']}.json", t)
    log_note(c.get("agent", "?"), f"released `{args.claim}`{' (handoff ' + args.handoff + ')' if args.handoff else ''}"
                                  f"{' — ' + args.note if args.note else ''}")
    print(f"released {args.claim}")
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    c = claim_by_id(args.claim)
    body = f"""# __HID__ — {c.get('title')}

## Claim
- claim: `{c.get('claim_id')}` · task: `{c.get('task') or '-'}` · author: `{c.get('agent')}`
- scopes: {', '.join('`' + s + '`' for s in c.get('scopes', []))}
- opened: {c.get('opened_utc')} · handed off: {stamp()}

## Changed
{args.changed}

## Verification
{args.tests}

## Doc-sync
{args.docsync}

## Evidence
{args.evidence}

## Next
{args.next}

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff __HID__ --note "<what was reproduced>"`)_
"""
    hid, fname = write_handoff_atomic(next_handoff_id(), body,
                                      slug(c.get("task") or c.get("title", "work")))
    c["handoff"] = hid
    c.setdefault("history", []).append({"utc": stamp(), "agent": args.agent or c.get("agent"), "event": f"handoff {hid}"})
    write_json(Path(c["_file"]), {k: v for k, v in c.items() if k != "_file"})
    log_note(c.get("agent", "?"), f"handoff `{hid}` ({fname})")
    print(f"wrote team/handoffs/{fname}\nnow release: team.py release --claim {c.get('claim_id')} --handoff {hid}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    ts = tasks()
    if args.task not in ts:
        die(f"no such task: {args.task}")
    t = ts[args.task]
    if t.get("owner") and t.get("owner") == args.by:
        die("self-verification is not verification: the reviewer must differ from the author")
    hid = args.handoff or t.get("handoff")
    if not hid:
        die("no handoff on this task; the author must write one first")
    hf = resolve_handoff(hid)
    block = (f"\n### Verified by `{args.by}` — {stamp()}\n"
             f"{args.note or 'commands re-run; result reproduced'}\n")
    with hf.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(block)
    t["status"] = "done"
    t.setdefault("history", []).append({"utc": stamp(), "agent": args.by, "event": f"verified via {hid}"})
    t["updated_utc"] = stamp()
    write_json(TASKS / f"{args.task}.json", t)
    log_note(args.by, f"verified `{args.task}` via `{hid}`")
    print(f"{args.task} → done (verified by {args.by})")
    return 0


def msg(frm: str, to: str, text: str) -> None:
    ensure_dirs()
    f = INBOX / f"{to}.md"
    if not f.exists():
        f.write_text(f"# Inbox — `{to}`\n\n> Append-only. Other agents write here (via `team.py msg`); "
                     f"`{to}` reads it at session start.\n\n", encoding="utf-8", newline="\n")
    with f.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"- **{stamp()}** from `{frm}`: {text}\n")


def cmd_reject(args: argparse.Namespace) -> int:
    """Bounce a handoff back to its author with required actions, and re-arm their claim.

    The non-stop loop needs both directions. Without this, a reviewer can only accept,
    so a rejected handoff either sits in `review` forever or the author idles while the
    pipeline stalls. Rejecting restores the author's claim (closed_utc cleared) so the
    work continues immediately under the same one-writer scopes, and the reason is
    written into the handoff itself so the next attempt cannot silently repeat it.
    """
    ts = tasks()
    if args.task not in ts:
        die(f"no such task: {args.task}")
    t = ts[args.task]
    if t.get("owner") == args.by:
        die("self-rejection is not review: the reviewer must differ from the author")
    if not args.actions or len(args.actions) < 80:
        die("--actions must state what to fix (>= 80 chars); a rejection without actions is noise")
    hid = args.handoff or t.get("handoff")
    if not hid:
        die(f"no handoff on `{args.task}`; nothing to reject")
    hf = resolve_handoff(hid)
    author = t.get("owner") or "unassigned"
    block = (f"\n### Rejected by `{args.by}` — {stamp()}\n"
             f"Required before re-handoff:\n\n{args.actions}\n")
    with hf.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(block)
    t["status"] = "in-progress"
    t.setdefault("history", []).append({"utc": stamp(), "agent": args.by, "event": f"rejected via {hid}"})
    t["updated_utc"] = stamp()
    write_json(TASKS / f"{args.task}.json", t)
    # re-arm the author's claim so their scopes stay reserved and they keep the work
    for c in claims():
        if c.get("task") == args.task and c.get("agent") == author and not c.get("closed_utc"):
            break
    else:
        c = next((c for c in claims() if c.get("task") == args.task and c.get("agent") == author), None)
        if c is not None:
            c["closed_utc"] = None
            c["closed_note"] = f"re-armed by {args.by} rejection"
            c["heartbeat_utc"] = stamp()
            c.setdefault("history", []).append({"utc": stamp(), "agent": args.by, "event": "re-armed"})
            write_json(Path(c["_file"]), {k: v for k, v in c.items() if k != "_file"})
    log_note(args.by, f"REJECTED `{args.task}` via `{hid}` — returned to {author}")
    msg(args.by, author, f"`{args.task}` came back from {hid}. Required before re-handoff:\n\n{args.actions}\n"
                        f"Your claim is re-armed — continue, do not release the scopes.")
    print(f"{args.task} → in-progress (rejected by {args.by}; claim re-armed for {author})")
    return 0


def cmd_msg(args: argparse.Namespace) -> int:
    if not (INBOX / f"{args.to}.md").exists() and args.to != "owner":
        cfg = config()
        if args.to not in cfg["agents"]:
            die(f"unknown recipient {args.to!r} (agents: {cfg['agents']}; or `owner`)")
    msg(args.from_, args.to, args.text)
    print(f"message appended to team/inbox/{args.to}.md")
    return 0


def cmd_note(args: argparse.Namespace) -> int:
    log_note(args.agent or "?", args.text)
    print("logged")
    return 0


def cmd_board(args: argparse.Namespace) -> int:
    cfg = config()
    ts, cs = tasks(), claims()
    act = {c["claim_id"]: c for c in cs if is_active(c, cfg)}
    lines = [f"# Team taskboard (generated by `scripts/team.py board` — do not hand-edit)",
             "",
             f"> Generated {stamp()} · source of truth: `team/tasks/*.json` + `team/claims/*.json` · "
             f"the project taskboard is `docs/33` (`TB-nnn`); rows here mirror it and add team ownership.",
             "",
             "| ID | P | Status | Owner | Lane | Task | Claim |",
             "|---|---|---|---|---|---|---|"]
    order = sorted(ts.values(), key=lambda t: (t.get("status", "todo") == "done",
                                               t.get("priority", "P3"), t.get("id", "")))
    for t in order:
        lines.append(f"| `{t.get('id')}` | {t.get('priority', 'P3')} | {t.get('status', 'todo')} | "
                     f"{t.get('owner') or '—'} | {t.get('lane') or '—'} | {t.get('title', '')[:120]} | "
                     f"{t.get('claim_id') or '—'} |")
    live = [c for c in cs if c["claim_id"] in act]
    lines += ["", "## Active claims", ""]
    if live:
        lines += ["| Claim | Agent | Scopes | Renewed | TTL |", "|---|---|---|---|---|"]
        for c in live:
            lines.append(f"| `{c['claim_id']}` | {c['agent']} | {', '.join(c.get('scopes', []))} | "
                         f"{c.get('heartbeat_utc')} | {c.get('ttl_minutes')}m |")
    else:
        lines.append("_(none)_")
    lines += ["", "## Queue rules (see `team/README.md` §2–§4)", "",
              "- Claim with `python scripts/team.py claim --agent <you> --task <ID>` — never edit unclaimed paths.",
              "- Finish → `handoff` → `release --handoff` → a **different** agent runs "
              "`verify --task <ID> --by <them>` → row becomes `done`.",
              "- Blocked? `task set <ID> --status blocked --note \"why\"` + `msg --to owner`.",
              ""]
    (TEAM / "taskboard.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"wrote team/taskboard.md ({len(ts)} tasks, {len(live)} active claims)")
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    cfg = config()
    state = (ROOT / "STATE.md").read_text(encoding="utf-8", errors="replace") if (ROOT / "STATE.md").exists() else ""
    head = {}
    for line in state.splitlines()[:6]:
        m = re.match(r"^(LEVEL|PHASE|TASK|LAST_GATE|ESCALATIONS):\s*(.*)$", line)
        if m:
            head[m.group(1)] = m.group(2)
    act = [c for c in claims() if is_active(c, config())]
    ts = tasks()
    claimable = sorted([t for t in ts.values() if t.get("status", "todo") == "todo" and deps_ok(t, ts)],
                       key=lambda t: (t.get("priority", "P3"), t.get("id", "")))[:6]
    tail = []
    logf = LOGS / f"{today()}.md"
    if logf.exists():
        tail = [ln for ln in logf.read_text(encoding="utf-8").splitlines() if ln.startswith("- ")][-6:]
    out = [f"# Team digest (generated by `scripts/team.py digest` — do not hand-edit)", "",
           f"> Generated {stamp()}. Capsule for a context-lost agent: read this, then `team/README.md`, "
           f"then claim. The spec of record is `docs/00`–`33`; this page only points.",
           "", "## Where the project stands"]
    for k in ("LEVEL", "PHASE", "LAST_GATE"):
        if k in head:
            out.append(f"- **{k}:** {head[k]}")
    if "TASK" in head:
        out.append(f"- **TASK:** {head['TASK']}")
    if "ESCALATIONS" in head:
        out.append(f"- **ESCALATIONS:** {head['ESCALATIONS'][:600]}")
    out += ["", "## Live work"]
    if act:
        out += [f"- `{c['claim_id']}` **{c['agent']}** — {c.get('title')} "
                f"({', '.join(c.get('scopes', []))[:120]})" for c in act]
    else:
        out.append("- (no active claims — the board is free)")
    out += ["", "## Claimable now (highest priority first)", ""]
    out += [f"- `{t['id']}` [{t.get('priority', 'P3')}] {t.get('lane', '')} — {t.get('title', '')[:110]}"
            for t in claimable] or ["- (none)"]
    out += ["", "## Recent team log", ""]
    out += tail or ["- (empty)"]
    out += ["", "## Non-negotiables (from the contract, not this file)", "",
            "- `R1` spec wins · `R7` never weaken a test · `R8` Decimal money · `R5` records before code · "
            "`R14` one writer per path (this folder's claims are that rule made operable).",
            "- No commits/pushes without the owner's explicit instruction in the session.",
            "- Every number needs the command that produced it.", ""]
    (TEAM / "digest.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print("wrote team/digest.md")
    return 0


def cmd_leader(args: argparse.Namespace) -> int:
    """Leader view: who is working, who is idle, what is claimable, what needs a verifier.

    The anti-idle instrument: an agent with no active claim is either not started, has finished, or
    has stalled. All three need an action from the leader, so they are printed as actions.
    """
    cfg = config()
    ts, cs = tasks(), claims()
    act = [c for c in cs if is_active(c, cfg)]
    stale = [c for c in cs if not c.get("closed_utc") and expired(c, cfg)]
    print(f"== LEADER VIEW {stamp()} ==")
    print(f"{'agent':<14}{'state':<12}{'last seen':<14}claims / task")
    idle = []
    for a in cfg["agents"]:
        mine = [c for c in act if c.get("agent") == a]
        hb = read_json(HB / f"{a}.json") or {}
        age = None
        if hb.get("utc"):
            try:
                age = int((now() - datetime.strptime(hb["utc"], "%Y-%m-%dT%H:%M:%SZ")
                           .replace(tzinfo=timezone.utc)).total_seconds() // 60)
            except ValueError:
                age = None
        seen = "never" if age is None else (f"{age} min ago" if age < 120 else f"{age // 60} h ago")
        away = cfg.get("away", {}).get(a)
        state = "working" if mine else ("AWAY" if away else "IDLE")
        if not mine and not away:
            idle.append(a)
        detail = ", ".join(f"{c.get('task') or c['claim_id']}" for c in mine) or "-"
        print(f"  {a:<12}{state:<12}{seen:<14}{detail}")
    claimable = [t for t in ts.values() if t.get("status", "todo") == "todo" and deps_ok(t, ts)]
    claimable.sort(key=lambda t: (t.get("priority", "P3"), t.get("id", "")))
    hot = [t for t in claimable if t.get("priority") in ("P0", "P1")]
    review = [t for t in ts.values() if t.get("status") == "review"]
    prefer = cfg.get("prefer", {})
    streams = cfg.get("streams", {})
    if streams:
        print(chr(10) + "  Streams (next up in queue; * = a dep is still open):")
        for a, ids in streams.items():
            nxt = []
            for tid in ids:
                t = ts.get(tid)
                # `review` means handed off and awaiting a verifier: it is not the
                # author's to re-claim, so it must not sit in a queue as "next up"
                if t is None or t.get("status") in ("done", "review"):
                    continue
                nxt.append(tid + ("" if deps_ok(t, ts) else "*"))
                if len(nxt) == 3:
                    break
            print(f"    {a:<12}{' -> '.join(nxt) if nxt else '(EMPTY: must propose new tasks)'}")
    print(f"\nClaimable: {len(claimable)} ({len(hot)} at P0/P1) · awaiting a verifier: {len(review)} · "
          f"stale claims: {len(stale)}")
    print("\nACTIONS")
    if idle and hot:
        for a in idle:
            lane_match = sorted(hot, key=lambda t: (0 if t.get("lane") in prefer.get(a, []) else 1,
                                                   t.get("priority", "P3"), t.get("id", "")))[0]
            print(f"  nudge {a}: claim {lane_match['id']} [{lane_match.get('priority')}] "
                  f"{lane_match.get('lane', '')} — {lane_match.get('title', '')[:80]}")
            print(f"        python scripts/team.py msg --from {cfg['leader']} --to {a} "
                  f"--text \"Claim {lane_match['id']} ({lane_match.get('title', '')[:70]}) and start.\"")
    elif idle:
        print(f"  IDLE agents with nothing P0/P1 claimable: {', '.join(idle)} — "
              f"review {len(review)} items or propose a task (`team.py task add`).")
    for t in review:
        print(f"  verifier needed for {t['id']} (author {t.get('owner')}, handoff {t.get('handoff')})")
    for c in stale:
        print(f"  stale claim {c['claim_id']} ({c.get('agent')}) — takeover: team.py claim --steal {c['claim_id']}")
    if not idle and not review and not stale:
        print("  everyone is working; nothing waiting on the leader.")
    return 0


PLACEHOLDERS = {"tbd", "n/a", "na", "none", "-", "--", "todo", "see above",
               "same as above", "no spec change", "none needed",
               "no doc-sync needed", "docs-only: no behaviour change"}

# Extensions a `## Changed` entry may name. It is an allowlist so a version string or a
# section number cannot masquerade as a path. It must cover what the lanes actually
# ship: the corpus lane is mostly .xlsx (33 of 55 files under sample-data/), and the
# packaging lane emits .pptx/.pdf - without those the declaration was silently dropped
# and the handoff-integrity gate was blind to exactly the files those lanes change.
EXT_RE = re.compile(
    r"\.(py|md|json|toml|ini|cfg|yaml|yml|txt|csv|ts|tsx|js|mjs|html|lock|sql|sh"
    r"|xlsx|xlsm|xls|parquet|duckdb|db|pptx|docx|pdf|svg|png|jpe?g|gif|webp|zip)$",
    re.IGNORECASE,
)


def _body(text: str, head: str) -> str:
    """Content of a `## Heading` section, minus nested headings and the reviewer
    template, so `present` can be told apart from `actually written`."""
    out = []
    for line in _section(text, head).splitlines():
        s = line.strip()
        if s.startswith("#") or s.startswith("_("):
            continue
        out.append(line)
    return "\n".join(out).strip()


def _expand_braces(tok: str) -> list[str]:
    """`a/{x.csv,y.csv}` -> [`a/x.csv`, `a/y.csv`].

    A brace group is one path a human wrote, but the tokeniser splits on the commas
    inside it and produces fragments like `{01_bank_batch_037.csv`, which then fail
    the existence check as a path that does not exist. Expanding keeps the author's
    meaning and keeps the check honest. Nested groups are expanded to one level at a
    time, which is what a hand-written declaration ever uses.
    """
    m = re.search(r"\{([^{}]*)\}", tok)
    if not m:
        return [tok]
    head, tail = tok[: m.start()], tok[m.end():]
    out: list[str] = []
    for part in m.group(1).split(","):
        out.extend(_expand_braces(head + part.strip() + tail))
    return out


def _declared_changed(text: str) -> set[str]:
    """Repo-relative paths declared under `## Changed` (back-ticked or bare, one per
    line or comma/slash-separated). Non-path tokens (versions, section refs) are
    rejected by the extension allowlist, so `3.14.7` and `docs/18` cannot masquerade."""
    found: set[str] = set()
    for line in _section(text, "## Changed").splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        # Brace groups are expanded BEFORE the split: they contain the commas the
        # tokeniser splits on, so expanding afterwards only ever sees fragments.
        for chunk in _expand_braces(s):
            for raw in re.split(r"[`\s,;]+", chunk):
                _add_declared(found, raw.strip("(").rstrip(".,;:'\""))
    return found


def _add_declared(found: set[str], tok: str) -> None:
    if not tok or tok.startswith("http"):
        return
    if "/" in tok and not EXT_RE.search(tok):
        return          # looks like a path but has no code/doc extension
    if not EXT_RE.search(tok):
        # dotfiles have no code extension (.nvmrc, .python-version) - accept them
        # only when they really exist, so a version string still cannot pass
        if not (tok.startswith(".") and "/" not in tok and (ROOT / tok).exists()):
            return      # version, section number, count, flag name
    found.add(norm(tok))


def _parse_ts(value):
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except Exception:
        return None


def _scope_hit(rel: str, scopes: list[str]) -> bool:
    for s in scopes:
        s = norm(s).rstrip("/")
        if has_glob(s):
            if fnmatch(rel, s):
                return True
        elif rel == s or rel.startswith(s + "/"):
            return True
    return False


def _window_edits(start, end, scopes: list[str] | None = None) -> list[str]:
    """Repo files modified inside a claim window that fall under that claim's scopes.

    This is what makes `## Changed` trustworthy: a handoff that declares one file
    while the window touched six is a summary, not a handoff. The coordination layer
    (team/, memory/, scratch/, vendor/) is excluded because every agent writes to it.
    memory/ is in that class by design - each seat appends its own continuity record
    during ordinary work; its integrity is gated separately by `memory.py verify`."""
    if not start:
        return []
    end = end or now()
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", "scratch/", "team/", "memory/", "vendor/",
                           "node_modules/", "ui/node_modules/", "ui/dist/",
                           ".ruff_cache/", ".mypy_cache/", ".pytest_cache/", ".vite/",
                           "dist/", "build/", "coverage/", "htmlcov/")) or rel == ".coverage":
            continue
        if rel.endswith((".pyc", ".log")) or "__pycache__" in rel:
            continue
        # scopes=None means the whole tree: that is how out-of-scope writes are found
        if scopes is not None and not _scope_hit(rel, scopes):
            continue
        m = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        if start <= m <= end + timedelta(minutes=2):
            hits.append(rel)
    return sorted(hits)


def handoff_index() -> dict[str, tuple[int, str, Path]]:
    """handoff id -> (number, task suffix, path), for every handoff on disk.

    Keyed on the *short* id (`HO-033`) because that is what a task stores in its
    `handoff` field; the file is `HO-033-ux-09.md`. Keying on the full stem made the
    rejected-handoff rule silently compare `HO-031` against `HO-031-ux-08` and never
    fire - the same shape as a checker that checks a different thing than it claims.
    """
    out: dict[str, tuple[int, str, Path]] = {}
    if not HANDOFFS.exists():
        return out
    for f in sorted(HANDOFFS.glob("HO-*.md")):
        m = re.match(r"HO-(\d+)(?:-(.+))?\.md$", f.name)
        if m:
            out[f"HO-{int(m.group(1)):03d}"] = (int(m.group(1)), (m.group(2) or "").lower(), f)
    return out


def rejected_handoffs() -> set[str]:
    """Handoffs that carry a rejection block, i.e. that a reviewer sent back."""
    return {hid for hid, (_n, _t, f) in handoff_index().items()
            if "### Rejected by" in read_handoff_text(f)}


def read_handoff_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def cmd_check(args: argparse.Namespace) -> int:
    cfg = config()
    fails: list[str] = []
    warns: list[str] = []
    cs, ts = claims(), tasks()
    act = [c for c in cs if is_active(c, cfg)]
    known = set(cfg["agents"])
    tb33 = tb_ids_in_docs33()
    hidx = handoff_index()
    rej = rejected_handoffs()

    for c in cs:
        if not c.get("claim_id") or not c.get("agent") or not c.get("scopes"):
            fails.append(f"claim file malformed: {Path(c['_file']).name}")
            continue
        if c.get("agent") not in known:
            fails.append(f"claim {c['claim_id']} uses unknown agent {c.get('agent')!r}")
    for i, a in enumerate(act):
        for b in act[i + 1:]:
            for s1 in a.get("scopes", []):
                for s2 in b.get("scopes", []):
                    if scopes_overlap(s1, s2):
                        # R14 forbids two *writers* on one path, not one writer holding two
                        # claims: a same-agent pair is still one writer, and the WIP limit
                        # already bounds how many tasks that agent may hold at once.
                        if a.get("agent") == b.get("agent"):
                            continue
                        fails.append(f"OVERLAP: {s1} ({a['claim_id']}, {a.get('agent')}) vs "
                                     f"{s2} ({b['claim_id']}, {b.get('agent')})")
    per: dict[str, int] = {}
    for c in act:
        per[c["agent"]] = per.get(c["agent"], 0) + 1
    for a, n in per.items():
        if n > int(cfg["wip_limit"]):
            fails.append(f"WIP limit: {a} holds {n} active claims (limit {cfg['wip_limit']})")
    for c in act:
        for s in c.get("scopes", []):
            for p in cfg.get("do_not_claim", []):
                if scopes_overlap(s, p):
                    fails.append(f"off-limits: {c['agent']} claims {s} ({p} belongs to the owner, not the team)")
    for c in act:
        if c.get("agent") != cfg["leader"]:
            for s in c.get("scopes", []):
                for p in cfg["leader_only_paths"]:
                    if scopes_overlap(s, p):
                        fails.append(f"leader-only: {c['agent']} claims {s} ({p} is {cfg['leader']}-only)")
    for c in act:
        for field in ("task",):
            v = c.get(field)
            if v and re.fullmatch(r"TB-\d{3}", str(v)) and v not in tb33:
                warns.append(f"claim {c['claim_id']} references {v}, which is not in docs/33")
    for t in ts.values():
        if t.get("source") == "docs/33" and t.get("id") not in tb33:
            warns.append(f"task {t.get('id')} says source docs/33 but is not there anymore")
        if t.get("status") == "review" and not t.get("handoff"):
            fails.append(f"task {t.get('id')} is in review without a handoff")
        # A card can be released straight back into `review` after a rejection, with no
        # new handoff. It then points at the handoff that was sent back, so it looks
        # verifiable and is not: the board is green over work nobody can accept.
        if t.get("status") == "review" and t.get("handoff") in rej:
            tid_l = str(t.get("id", "")).lower()
            newer = [h for h, (n, suf, _f) in hidx.items()
                     if suf.startswith(tid_l) and n > hidx[str(t["handoff"])][0]
                     and h not in rej]
            if not newer:
                fails.append(
                    f"task {t.get('id')} is in review on `{t['handoff']}`, which was "
                    f"rejected and has no successor handoff - it is not verifiable")
    for t in ts.values():
        for d in t.get("deps", []):
            if re.fullmatch(r"TB-\d{3}", d) and d in ts and ts[d].get("status") != "done" \
                    and t.get("status") in ("in-progress", "review", "done"):
                warns.append(f"{t['id']} is {t['status']} while dep {d} is {ts[d].get('status')}")
    for f in sorted(HANDOFFS.glob("HO-*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for sec in HANDOFF_SECTIONS:
            if sec not in text:
                fails.append(f"{f.name}: missing required section {sec}")
            else:
                content = _body(text, sec)
                if len(content) < 12 or content.lower() in PLACEHOLDERS:
                    # Present but empty is a rubber stamp: each section exists to carry a
                    # claim a peer can falsify, so a header or a stub must not pass.
                    fails.append(f"{f.name}: section {sec} is present but empty "
                                 f"({len(content)} chars of content)")
        claim_blk = _section(text, "## Claim")
        cm = re.search(r"claim:\s*`([^`]+)`", claim_blk)
        claim = claim_by_id(cm.group(1)) if cm else None
        if claim is not None:
            start = _parse_ts(claim.get("opened_utc"))
            hm = re.search(r"handed off:\s*([0-9T:Z+-]+)", claim_blk)
            end = _parse_ts(hm.group(1)) if hm else _parse_ts(claim.get("closed_utc"))
            touched = _window_edits(start, end, claim.get("scopes", []))
            declared = _declared_changed(text)
            undeclared = [w for w in touched if w not in declared]
            if undeclared:
                (fails if args.strict else warns).append(
                    f"{f.name}: {len(undeclared)} file(s) changed inside the claim window but not "
                    f"declared under '## Changed': {', '.join(undeclared[:6])}")
            ver = _body(text, "## Verification").lower()
            if touched and not [w for w in touched if w.endswith((".py", ".ts", ".tsx", ".js"))] \
                    and "team.py" in ver and "pytest" not in ver:
                warns.append(f"{f.name}: docs-only handoff verified only by the coordination command "
                             f"(`team.py check`); the deliverable's own content was not re-checked")
        # A write inside the claim window but OUTSIDE the claimed paths is worse than an
        # undeclared one: it is nobody's work, so no guard can see it. (hermes' UX-03 wrote
        # two scripts in scripts/ under a claim scoped to evidence/.)
        allowed = [s.rstrip("/") for s in claim.get("scopes", [])]
        # files another live claim already covers are that agent's work, not a stray
        others = [s.rstrip("/")
                 for c in cs if c.get("claim_id") != claim.get("claim_id")
                 for s in c.get("scopes", []) if not has_glob(s)]
        leader_paths = [s.rstrip("/") for s in cfg.get("leader_only_paths", [])]
        covered_scopes = allowed + others + leader_paths
        stray = sorted(
            w for w in _window_edits(start, end, None)
            if w not in declared
            and not any(w == s or w.startswith(s + "/") for s in covered_scopes)
        )
        if stray:
            (fails if args.strict else warns).append(
                f"""{f.name}: {len(stray)} file(s) written inside the claim window but OUTSIDE the claimed"""
                f" scopes: {', '.join(stray[:5])}")

        for pth in sorted(_declared_changed(text)):
            # A bare file name carries no directory, so it cannot be resolved from the
            # repo root; the claim-window rule above is what proves the list is complete.
            if has_glob(pth) or "/" not in pth:
                continue
            if not (ROOT / pth).exists():
                fails.append(f"{f.name}: declared changed path does not exist: {pth}")
        # Evidence paths (only inside ## Evidence) must exist on disk.
        for ev in re.findall(r"(evidence/[\w./-]+)", _section(text, "## Evidence")):
            if not (ROOT / ev.rstrip(".") ).exists():
                fails.append(f"{f.name}: evidence path does not exist: {ev}")
        # The first back-ticked path of every ## Changed bullet must exist (unless marked removed).
        for line in _section(text, "## Changed").splitlines():
            m = re.match(r"^\s*-\s+`([^`]+)`", line)
            if not m:
                continue
            p = norm(m.group(1))
            if any(t in line.lower() for t in ("removed", "deleted")) or has_glob(p):
                continue
            # Only enforce on real files: a bare `docs/18` is a document-number reference,
            # not a path, and a directory without an extension carries no file to check.
            if not Path(p).suffix:
                continue
            if not (ROOT / p).exists():
                fails.append(f"{f.name}: changed path does not exist: {p}")
    orphans = [p for p in git_changed_paths() if not covered(p, act, cfg)]
    if orphans:
        (fails if args.strict else warns).append(
            f"{len(orphans)} working-tree edit(s) not covered by an active claim: {', '.join(orphans[:8])}")
    claimable_hot = [t for t in ts.values() if t.get("status", "todo") == "todo" and deps_ok(t, ts)
                     and t.get("priority") in ("P0", "P1")]
    without_claim = [a for a in cfg["agents"] if not any(c.get("agent") == a for c in act)]
    # an agent with unclaimed work in its own stream is not starving, however few
    # unclaimed P0/P1 tasks exist on the whole board
    for a in list(without_claim):
        if [i for i in cfg.get("streams", {}).get(a, [])
                if ts.get(i, {}).get("status") not in (None, "done")]:
            without_claim.remove(a)
    if without_claim and len(claimable_hot) < len(without_claim):
        warns.append(f"STARVATION: {len(without_claim)} agent(s) without a claim "
                     f"({', '.join(without_claim)}) but only {len(claimable_hot)} P0/P1 task(s) claimable "
                     f"— run `python scripts/team.py leader` for the action list")
    dig = TEAM / "digest.md"
    if dig.exists() and (ROOT / "STATE.md").exists() and (ROOT / "STATE.md").stat().st_mtime > dig.stat().st_mtime:
        warns.append("team/digest.md is older than STATE.md — run `python scripts/team.py digest`")
    print(f"team check — {'FAIL' if fails else 'PASS'} ({len(act)} active claims, {len(ts)} tasks, "
          f"{len(fails)} fail, {len(warns)} warn)")
    for x in fails:
        print(f"  FAIL {x}")
    for x in warns:
        print(f"  WARN {x}")
    return 1 if fails else 0


def cmd_sync(args: argparse.Namespace) -> int:
    if not DOC33.exists():
        die("docs/33 not found")
    ts = tasks()
    added = 0
    status_map = {"⬜": "todo", "🚧": "in-progress", "✅": "done"}
    for line in DOC33.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\| `(TB-\d{3})` \| (.+?) \| (.+?) \| ([⬜🚧✅]?) \| (.+?) \|$", line)
        if not m:
            continue
        tid, title, _refs, st, depcell = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        if tid in ts:
            continue
        deps = re.findall(r"TB-\d{3}", depcell)
        ts[tid] = {"id": tid, "title": title.strip(), "source": "docs/33", "priority": args.default_priority,
                   "status": status_map.get(st, "todo"), "owner": None, "claim_id": None, "deps": deps,
                   "lane": "", "created_utc": stamp(), "updated_utc": stamp(),
                   "history": [{"utc": stamp(), "agent": "sync", "event": "imported from docs/33"}]}
        write_json(TASKS / f"{tid}.json", ts[tid])
        added += 1
    print(f"sync: {added} new task(s) imported from docs/33; queue now {len(tasks())}.")
    if added:
        print("review priorities/owners with `team.py tasks`; rows the leader has not triaged stay P3.")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    cap = args.capability
    words = [w for w in re.split(r"[^A-Za-z0-9_]+", cap) if len(w) > 3]
    print(f"== preflight: {cap} ==")
    reg = (ROOT / "docs" / "32_REUSE_AND_PROVENANCE.md")
    hits = []
    if reg.exists():
        for i, line in enumerate(reg.read_text(encoding="utf-8").splitlines(), 1):
            if any(w.lower() in line.lower() for w in words):
                hits.append(f"docs/32:{i} {line[:150]}")
    print(f"-- reuse registry hits: {len(hits)}")
    for h in hits[:10]:
        print("   " + h)
    code = []
    for w in words:
        try:
            r = subprocess.run(["git", "-c", "core.quotePath=false", "grep", "-n", "-i", "--", w],
                               cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            for line in r.stdout.splitlines()[:6]:
                code.append(line)
        except OSError:
            pass
    print(f"-- existing code hits: {len(code)}")
    for c in code[:12]:
        print("   " + c[:160])
    print("-- Addon 6 §1 decision tree (in order):")
    print("   1) is the capability already implemented here? → R12: wire it, do not re-write")
    print("   2) does the catalog (ADDON_6 §3, WS-01…WS-X) cover it with a GO license? → REUSE (S0–S10, ADP row)")
    print("   3) nothing fits → BUILD, but write the BD row in docs/32 §2 first: capability, spec quote,")
    print("      sources searched, why none fit, chosen approach")
    print("   rails: licence gate before any copy · ≤10 files (R13) · no new dep without R9 ·"
          " no spec edit to fit code (R1) · records before code (R5)")
    return 0


# --------------------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="team", description="Four-agent coordination (see team/README.md)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("tasks"); s.add_argument("--all", action="store_true"); s.set_defaults(fn=cmd_tasks)
    s = sub.add_parser("task"); ts = s.add_subparsers(dest="task_cmd", required=True)
    a = ts.add_parser("add")
    a.add_argument("--title", required=True); a.add_argument("--tb"); a.add_argument("--priority", default="P3")
    a.add_argument("--deps"); a.add_argument("--lane"); a.add_argument("--by"); a.set_defaults(fn=cmd_task_add)
    a = ts.add_parser("set")
    a.add_argument("id"); a.add_argument("--status", choices=TASK_STATUSES); a.add_argument("--priority")
    a.add_argument("--lane"); a.add_argument("--note"); a.add_argument("--by"); a.set_defaults(fn=cmd_task_set)
    a = ts.add_parser("show")
    a.add_argument("id"); a.set_defaults(fn=lambda ns: (print(json.dumps(tasks().get(ns.id, {}), indent=2)), 0)[1])

    s = sub.add_parser("claim")
    s.add_argument("--agent", required=True); s.add_argument("--task"); s.add_argument("--title")
    s.add_argument("--scope", action="append"); s.add_argument("--kind"); s.add_argument("--ttl", type=int)
    s.add_argument("--note"); s.add_argument("--steal"); s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_claim)
    s = sub.add_parser("touch"); s.add_argument("--claim", required=True); s.add_argument("--agent")
    s.set_defaults(fn=cmd_touch)
    s = sub.add_parser("release")
    s.add_argument("--claim", required=True); s.add_argument("--handoff"); s.add_argument("--done", action="store_true")
    s.add_argument("--note"); s.add_argument("--agent"); s.set_defaults(fn=cmd_release)
    s = sub.add_parser("handoff")
    s.add_argument("--claim", required=True); s.add_argument("--summary", default="")
    for opt in ("changed", "tests", "docsync", "evidence", "next"):
        s.add_argument(f"--{opt}", default="")
    s.add_argument("--agent"); s.set_defaults(fn=cmd_handoff)
    s = sub.add_parser("verify")
    s.add_argument("--task", required=True); s.add_argument("--by", required=True); s.add_argument("--handoff")
    s.add_argument("--note"); s.set_defaults(fn=cmd_verify)
    s = sub.add_parser("reject")
    s.add_argument("--task", required=True); s.add_argument("--by", required=True); s.add_argument("--handoff")
    s.add_argument("--actions", required=True); s.set_defaults(fn=cmd_reject)
    s = sub.add_parser("msg")
    s.add_argument("--from", dest="from_", required=True); s.add_argument("--to", required=True)
    s.add_argument("--text", required=True); s.set_defaults(fn=cmd_msg)
    s = sub.add_parser("note"); s.add_argument("--text", required=True); s.add_argument("--agent")
    s.set_defaults(fn=cmd_note)
    s = sub.add_parser("board"); s.set_defaults(fn=cmd_board)
    s = sub.add_parser("leader"); s.set_defaults(fn=cmd_leader)
    s = sub.add_parser("digest"); s.set_defaults(fn=cmd_digest)
    s = sub.add_parser("check"); s.add_argument("--strict", action="store_true"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("sync"); s.add_argument("--default-priority", default="P3"); s.set_defaults(fn=cmd_sync)
    s = sub.add_parser("preflight"); s.add_argument("--capability", required=True); s.set_defaults(fn=cmd_preflight)
    return p


def main(argv: list[str] | None = None) -> int:
    ensure_dirs()
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
