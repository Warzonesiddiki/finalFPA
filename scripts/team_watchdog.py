"""OPS-01 — the non-stop supervision loop for a five-agent checkout.

Every `interval_minutes` (default 20) this script:

1. regenerates the generated views (`team/taskboard.md`, `team/digest.md`), so what the
   owner reads is never stale;
2. runs `team.py check` and records its FAIL/WARN counts;
3. classifies the team into actionable states (idle seat with claimable work in its
   stream, expired claim, handoff waiting too long for a verifier, stream running dry,
   project finished) and turns each into a **logged, idempotent** action;
4. applies only the actions that are safe to apply without judgement: nudges into
   `team/inbox/<agent>.md`, escalations into `team/inbox/owner.md`, and *drafts* of new
   cards (never creates work itself without a human-visible draft line).

What it must never do, because each of those would destroy the guarantee the team is
built on: verify a handoff, accept a handoff, or commit. Verification stays a
different human-or-agent reading the numbers; a watchdog that rubber-stamps work is
worse than no watchdog at all.

Idempotence matters more than speed here: the loop may be restarted at any time, and a
nudge must not be repeated every tick. State lives in `team/log/watchdog-state.json`
and every decision is appended to `team/log/watchdog.log`.

Usage:
    python scripts/team_watchdog.py once            # one tick (this is what the test calls)
    python scripts/team_watchdog.py loop             # tick every interval until done/stopped
    python scripts/team_watchdog.py loop --interval 20 --max-ticks 0
    python scripts/team_watchdog.py status           # show the loop state and last tick
Stop a running loop by creating `team/log/watchdog.stop` (or sending SIGINT).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import team  # noqa: E402  (same directory, imported after sys.path is set)

LOG_DIR = ROOT / "team" / "log"
STATE = LOG_DIR / "watchdog-state.json"
STOP = LOG_DIR / "watchdog.stop"
LOCK = LOG_DIR / "watchdog.lock"
TICK_LOG = LOG_DIR / "watchdog.log"
DEFAULTS = {
    "interval_minutes": 20,
    "stale_verification_minutes": 30,
    "nudge_cooldown_minutes": 40,
    "idle_minutes": 25,
    "max_ticks": 0,          # 0 = until the project is complete or stopped
    "autostart_board": True,
}


# --------------------------------------------------------------------------- helpers
def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp() -> str:
    return now().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def config() -> dict:
    cfg = dict(DEFAULTS)
    raw = team.read_json(ROOT / "team" / "config.json") or {}
    cfg.update(raw.get("watchdog") or {})
    return cfg


def state_path() -> Path:
    return LOG_DIR / "watchdog-state.json"


def log_path() -> Path:
    return LOG_DIR / "watchdog.log"


def state() -> dict:
    return team.read_json(state_path()) or {"ticks": 0, "nudges": {}, "started_utc": None, "last_tick_utc": None}


def save_state(st: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    team.write_json(state_path(), st)


def log(line: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with log_path().open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{stamp()} {line}" + chr(10))
    print(f"{stamp()} {line}")


WATCHED = (ROOT / "scripts" / "team_watchdog.py",
           ROOT / "scripts" / "team.py",
           ROOT / "team" / "config.json")


def code_fingerprint() -> tuple:
    """mtime+size of the files this loop depends on. A long-running loop never
    sees a code edit, which is how a running watchdog kept nudging a seat that had just
    been marked away. Comparing before every tick turns that class of bug into a restart."""
    out = []
    for p in WATCHED:
        try:
            st = p.stat()
        except OSError:
            out.append((0, 0))
            continue
        out.append((st.st_mtime_ns, st.st_size))
    return tuple(out)


def maybe_reload(seen: tuple) -> None:
    now_fp = code_fingerprint()
    if now_fp != seen:
        log("RELOAD: team.py, team_watchdog.py or config.json changed since this loop started - re-executing to pick it up")
        os.execv(sys.executable, [sys.executable, str(ROOT / "scripts" / "team_watchdog.py"), *sys.argv[1:]])

def board_fingerprint() -> str:
    """Cheap change-detector for the generated views: mtime+size of every
    task and claim file. The board and digest only change when one of these moves."""
    h = hashlib.sha256()
    for p in sorted(list(team.TASKS.glob("*.json")) + list(team.CLAIMS.glob("*.json"))):
        try:
            st = p.stat()
        except OSError:
            continue
        h.update(f"{p.name}:{st.st_mtime_ns}:{st.st_size}".encode())
    return h.hexdigest()[:16]

def pid_alive(pid: int) -> bool:
    if sys.platform == "win32":  # pragma: no cover - platform specific
        res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
        return str(pid) in (res.stdout or "")
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_lock() -> int:
    """One loop at a time, atomically. Two instances would double-tick the board and
    clobber the state file of each other, which is exactly the kind of silent corruption a
    supervision tool must not have. A lock whose process is gone is taken over and
    logged, so a crash cannot wedge the loop forever."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                old = int(LOCK.read_text(encoding="utf-8").strip() or 0)
            except (ValueError, OSError):
                old = 0
            if old and pid_alive(old):
                log(f"REFUSED start: loop already running as pid {old}")
                return 0
            log(f"taking over the lock of dead pid {old}")
            LOCK.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(str(os.getpid()))
        return os.getpid()
    log("REFUSED start: could not acquire the loop lock")
    return 0


def release_lock() -> None:
    try:
        if LOCK.exists() and LOCK.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK.unlink(missing_ok=True)
    except OSError:  # pragma: no cover - best effort
        pass


def run(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.returncode, (res.stdout or "") + (res.stderr or "")


# --------------------------------------------------------------------------- survey
def survey() -> dict:
    """Everything the decisions below need, gathered in one pass (no side effects)."""
    cfg = team.config()
    ts, cs = team.tasks(), team.claims()
    active = [c for c in cs if team.is_active(c, cfg)]
    agents = {}
    for a in cfg["agents"]:
        hb = team.read_json(team.HB / f"{a}.json") or {}
        seen = parse_ts(hb.get("utc")) if hb.get("utc") else None
        age = int((now() - seen).total_seconds() // 60) if seen else None
        is_away = bool(cfg.get("away", {}).get(a))
        stream = [i for i in (cfg.get("streams", {}).get(a) or [])
                  if ts.get(i, {}).get("status") not in (None, "done", "review")]
        claimable_stream = [i for i in stream if team.deps_ok(ts[i], ts)
                            and ts[i].get("status", "todo") in ("todo", "in-progress")]
        agents[a] = {
            "active_claims": [c.get("task") for c in active if c.get("agent") == a],
            "idle_minutes": age,
            "stream": stream,
            "stream_claimable": claimable_stream,
            "away": is_away,
        }
    review = [{"task": t["id"], "owner": t.get("owner"), "handoff": t.get("handoff"),
               "updated_utc": t.get("updated_utc")} for t in ts.values() if t.get("status") == "review"]
    open_p0 = [t["id"] for t in ts.values()
               if t.get("status") not in ("done",) and t.get("priority") == "P0"]
    todo = [t["id"] for t in ts.values() if t.get("status") == "todo"]
    return {
        "agents": agents,
        "review": review,
        "stale_claims": [c["claim_id"] for c in cs
                         if not c.get("closed_utc") and team.expired(c, cfg)],
        "active_claims": len(active),
        "open_p0": sorted(open_p0),
        "todo_count": len(todo),
        "all_done": not todo and not open_p0,
    }


# --------------------------------------------------------------------------- decisions
def decide(s: dict, st: dict, cfg: dict) -> list[dict]:
    """Pure function: survey + previous state + config -> the list of actions.

    Kept pure so it can be tested directly; `apply` is the only part with side effects.
    """
    out: list[dict] = []
    nudges = st.get("nudges", {})
    cooldown = cfg["nudge_cooldown_minutes"] * 60
    idle_limit = cfg["idle_minutes"] * 60
    verify_limit = cfg["stale_verification_minutes"] * 60

    def cooled(key: str) -> bool:
        last = nudges.get(key)
        t = parse_ts(last) if last else None
        return t is not None and (now() - t).total_seconds() < cooldown

    for agent, info in s["agents"].items():
        if info.get("away"):
            # out of quota or offline: nagging an agent who cannot answer is noise
            continue
        if info["active_claims"]:
            continue
        if info["stream_claimable"]:
            why = ("no active claim while its stream still has claimable work: "
                   + ", ".join(info["stream_claimable"][:3]))
            out.append({"kind": "nudge", "to": agent, "key": f"idle:{agent}",
                        "text": f"Stream check: {why}. Claim the first one and start "
                                f"(`python scripts/team.py claim --agent {agent} --task "
                                f"{info['stream_claimable'][0]} --scope <paths>`). Idling with "
                                f"claimable work is a protocol violation."})
        elif not info["stream"]:
            out.append({"kind": "draft", "to": "owner", "key": f"dry:{agent}",
                        "text": f"{agent}'s stream is empty and it holds no claim. Propose the next "
                                f"card (`python scripts/team.py task add --title ... --lane ...`) or "
                                f"hand it a lane from a seat that is over-subscribed."})
        elif (info["idle_minutes"] or 0) * 60 >= idle_limit and not cooled(f"blocked:{agent}"):
            out.append({"kind": "nudge", "to": agent, "key": f"blocked:{agent}",
                        "text": "You have no active claim. If your stream's next card is blocked by a "
                                "dependency, say so to buffy with the blocking task id, or take the next "
                                "unblocked card behind it. Do not go quiet."})

    for c in s["stale_claims"]:
        out.append({"kind": "escalate", "to": "owner", "key": f"stale:{c}",
                    "text": f"Claim {c} is past its TTL with no heartbeat. It can be taken over with "
                            f"`python scripts/team.py claim --steal {c}` (the takeover is logged)."})

    for r in s["review"]:
        updated = parse_ts(r.get("updated_utc") or "")
        waited = (now() - updated).total_seconds() if updated else None
        if waited is not None and waited >= verify_limit and not cooled(f"verify:{r['task']}"):
            out.append({"kind": "escalate", "to": "owner", "key": f"verify:{r['task']}",
                        "text": f"{r['task']} has been waiting {int(waited // 60)} min for an independent "
                                f"verifier (handoff {r.get('handoff')}). Either a peer verifies it or the "
                                f"leader does, with the raw output pasted."})

    if s["all_done"] and not cooled("complete"):
        out.append({"kind": "done", "to": "owner", "key": "complete",
                    "text": "No open cards and no open P0 remain: the taskboard is empty. The loop is "
                            "stopping. Final gate state is whatever `scripts/check.py` last reported - "
                            "confirm it before declaring the project done."})
    return out


# --------------------------------------------------------------------------- apply
SAFE = {"nudge", "escalate", "draft", "done"}


def apply(actions: list[dict], st: dict, dry_run: bool = False) -> list[dict]:
    """Apply the safe actions. Refuses anything outside the allow-list by construction."""
    applied: list[dict] = []
    st.setdefault("nudges", {})
    for a in actions:
        if a["kind"] not in SAFE:
            log(f"REFUSED action of unknown kind {a['kind']!r} - the watchdog may not widen its own powers")
            continue
        applied.append(a)
        st["nudges"][a["key"]] = stamp()
        if dry_run:
            continue
        team.msg("watchdog", a["to"], a["text"])
        log(f"{a['kind'].upper()} -> {a['to']}: {a['text'][:110]}")
    return applied


def tick(dry_run: bool = False) -> dict:
    try:
        return _tick(dry_run)
    except Exception as exc:  # a supervision loop must not die silently
        log(f"TICK FAILED: {type(exc).__name__}: {exc}")
        import traceback
        log(traceback.format_exc().strip().replace(chr(10), " | "))
        return {"check_exit": -1, "check_fails": 0, "check_warns": 0, "actions": [], "all_done": False, "failed": True}


def _tick(dry_run: bool = False) -> dict:
    t0 = time.monotonic()
    cfg = config()
    st = state()
    st["ticks"] = st.get("ticks", 0) + 1
    st.setdefault("started_utc", stamp())
    st["last_tick_utc"] = stamp()
    st["board_fingerprint"] = board_fingerprint()
    code_check, out_check = run([sys.executable, "scripts/team.py", "check"])
    fails = out_check.count("  FAIL ")
    warns = out_check.count("  WARN ")
    fingerprint = board_fingerprint()
    if cfg.get("autostart_board") and fingerprint != st.get("board_fingerprint"):
        run([sys.executable, "scripts/team.py", "board"])
        run([sys.executable, "scripts/team.py", "digest"])
    s = survey()
    actions = decide(s, st, cfg)
    applied = apply(actions, st, dry_run=dry_run)
    st["last"] = {
        "check_exit": code_check, "check_fails": fails, "check_warns": warns,
        "active_claims": s["active_claims"], "todo": s["todo_count"],
        "open_p0": s["open_p0"], "actions": [f"{a['kind']}->{a['to']}" for a in applied],
        "all_done": s["all_done"],
        "board_fingerprint": st.get("board_fingerprint"),
    }
    if not dry_run:
        save_state(st)
    took = time.monotonic() - t0
    took = time.monotonic() - t0
    tick_no = st["ticks"]
    n_active = s["active_claims"]
    n_todo = s["todo_count"]
    n_actions = len(applied)
    log(f"tick #{tick_no}: check exit {code_check} ({fails} fail, {warns} warn), "
        f"{n_active} active claim(s), {n_todo} card(s) todo, "
        f"{n_actions} action(s), tick took {took:.1f}s")
    return st["last"]


def loop(interval: int, max_ticks: int, dry_run: bool = False) -> int:
    if not acquire_lock():
        return 3
    try:
        return _loop(interval, max_ticks, dry_run)
    finally:
        release_lock()


def _loop(interval: int, max_ticks: int, dry_run: bool = False) -> int:
    cfg = config()
    seen = code_fingerprint()
    interval = max(1, interval)
    n = 0
    while True:
        if STOP.exists():
            log("stop file present - loop exiting")
            STOP.unlink(missing_ok=True)
            return 0
        n += 1
        maybe_reload(seen)
        last = tick(dry_run=dry_run)
        if last.get("all_done"):
            log("project finished (no open cards, no open P0) - loop exiting")
            return 0
        if max_ticks and n >= max_ticks:
            log(f"reached --max-ticks {max_ticks} - loop exiting")
            return 0
        wake = now() + timedelta(minutes=interval)
        log(f"sleeping {interval} min; next tick due {wake.isoformat(timespec='seconds')}")
        for _ in range(interval * 60):
            if STOP.exists():
                log("stop file appeared during sleep - exiting")
                return 0
            try:
                time.sleep(1)
            except KeyboardInterrupt:  # pragma: no cover - interactive
                log("interrupted - exiting")
                return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("once", help="run a single tick")
    lp = sub.add_parser("loop", help="tick on an interval until done or stopped")
    lp.add_argument("--interval", type=int, default=0, help="minutes (default from config)")
    lp.add_argument("--max-ticks", type=int, default=0)
    lp.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="show loop state and the last tick")
    args = ap.parse_args()
    if args.cmd == "once":
        tick()
        return 0
    if args.cmd == "status":
        print(json.dumps(state().get("last", {}), indent=2, default=str))
        return 0
    return loop(args.interval or config()["interval_minutes"], args.max_ticks or config()["max_ticks"],
                args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
