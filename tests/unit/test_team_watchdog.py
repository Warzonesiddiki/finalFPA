"""Tests for the OPS-01 supervision watchdog's decision logic.

`decide` is pure, so every rule is tested without touching an inbox, and the
allow-list in `apply` is tested by trying to make the watchdog verify a handoff -
it must refuse, because a watchdog that rubber-stamps work is worse than none.
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import team_watchdog as wd  # noqa: E402


def cfg(**over):
    base = dict(wd.DEFAULTS)
    base.update(over)
    return base


def agent_info(claims=(), stream=(), claimable=(), idle=0):
    return {"active_claims": list(claims), "idle_minutes": idle,
            "stream": list(stream), "stream_claimable": list(claimable)}


def survey(agents=None, review=(), stale=(), todo=3, p0=("TB-001",), all_done=False):
    return {
        "agents": agents or {},
        "review": list(review),
        "stale_claims": list(stale),
        "active_claims": sum(len(a["active_claims"]) for a in (agents or {}).values()),
        "open_p0": list(p0),
        "todo_count": todo,
        "all_done": all_done,
    }


def test_idle_seat_with_claimable_work_is_nudged():
    s = survey({"hermes": agent_info(stream=["UX-02", "UX-03"], claimable=["UX-02"])})
    actions = wd.decide(s, {"nudges": {}}, cfg())
    assert [a["kind"] for a in actions] == ["nudge"]
    assert actions[0]["to"] == "hermes"
    assert "UX-02" in actions[0]["text"]


def test_a_working_seat_is_never_nudged():
    s = survey({"opencode": agent_info(claims=["TB-016"], stream=["ENG-01"], claimable=["ENG-01"], idle=99)})
    assert wd.decide(s, {"nudges": {}}, cfg()) == []


def test_empty_stream_produces_a_draft_for_the_owner_not_a_nudge():
    s = survey({"freebuff2": agent_info(idle=30)})
    actions = wd.decide(s, {"nudges": {}}, cfg())
    assert [a["kind"] for a in actions] == ["draft"]
    assert actions[0]["to"] == "owner"
    assert "task add" in actions[0]["text"]


def test_blocked_seat_is_nudged_once_then_cooled_down():
    s = survey({"buffy": agent_info(stream=["TB-022"], claimable=[], idle=40)})
    st = {"nudges": {}}
    first = wd.decide(s, st, cfg())
    assert [a["key"] for a in first] == ["blocked:buffy"]
    # simulate the nudge having been applied: the same tick must stay silent
    st["nudges"]["blocked:buffy"] = wd.stamp()
    assert wd.decide(s, st, cfg()) == []


def test_expired_claim_is_escalated_with_the_takeover_command():
    s = survey({"antigravity": agent_info(claims=["TB-007"])}, stale=["antigravity-20261005T1051Z-f2cb"])
    actions = wd.decide(s, {"nudges": {}}, cfg())
    assert [a["kind"] for a in actions] == ["escalate"]
    assert "--steal antigravity-20261005T1051Z-f2cb" in actions[0]["text"]


def test_handoff_waiting_too_long_is_escalated_but_not_before():
    old = (wd.now() - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent = (wd.now() - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    waited = [{"task": "TB-008", "owner": "antigravity", "handoff": "HO-011", "updated_utc": old}]
    fresh = [{"task": "TB-025", "owner": "opencode", "handoff": "HO-013", "updated_utc": recent}]
    assert [a["key"] for a in wd.decide(survey(review=waited), {"nudges": {}}, cfg())] == ["verify:TB-008"]
    assert wd.decide(survey(review=fresh), {"nudges": {}}, cfg()) == []


def test_completion_is_announced_once_and_ends_the_loop():
    s = survey({"buffy": agent_info(claims=["TB-022"])}, todo=0, p0=(), all_done=True)
    st = {"nudges": {}}
    actions = wd.decide(s, st, cfg())
    assert [a["kind"] for a in actions] == ["done"]
    st["nudges"]["complete"] = wd.stamp()
    assert wd.decide(s, st, cfg()) == []


def test_watchdog_cannot_verify_or_accept_work(monkeypatch, tmp_path):
    """The allow-list is the safety property: even a bug in decide() cannot make the
    loop rubber-stamp a handoff, because only these four kinds are applied."""
    for kind in ("verify", "accept", "release_done", "commit"):
        applied = wd.apply([{"kind": kind, "to": "owner", "key": "x", "text": "t"}],
                           {"nudges": {}}, dry_run=True)
        assert applied == [], kind
    assert set(wd.SAFE) == {"nudge", "escalate", "draft", "done"}


def test_survey_reads_the_real_board_without_raising():
    """A smoke test against the live tree: the survey must work on the real files."""
    s = wd.survey()
    assert set(s["agents"]) == set(wd.team.config()["agents"])
    assert isinstance(s["todo_count"], int)
    assert s["active_claims"] >= 0


def test_config_has_the_owners_twenty_minute_cadence():
    assert wd.config()["interval_minutes"] == 20


def test_only_one_loop_can_run_at_a_time(monkeypatch, tmp_path):
    """Two loops would double-tick the board and clobber each other's state file, so
    the second start must be refused - and a lock left by a dead pid must be taken
    over rather than wedging the loop forever."""
    log_dir = tmp_path / "log"
    monkeypatch.setattr(wd, "LOG_DIR", log_dir)
    monkeypatch.setattr(wd, "LOCK", log_dir / "watchdog.lock")
    assert wd.acquire_lock() == os.getpid()
    assert wd.acquire_lock() == 0                      # refused while we are alive
    log_dir.mkdir(parents=True, exist_ok=True)
    wd.LOCK.write_text(str(os.getpid() + 999999), encoding="utf-8")   # a dead pid
    assert wd.acquire_lock() == os.getpid()            # taken over
    wd.release_lock()
    assert not wd.LOCK.exists()


def test_a_failing_tick_is_logged_instead_of_killing_the_loop(monkeypatch, tmp_path):
    """A supervision loop must never die silently: the exception is logged with its
    traceback, and the caller gets a failed tick rather than a dead process."""
    log_dir = tmp_path / "log"
    monkeypatch.setattr(wd, "LOG_DIR", log_dir)
    monkeypatch.setattr(wd, "STATE", log_dir / "watchdog-state.json")

    def boom(cmd, *a, **k):
        raise OSError("subprocess exploded")

    monkeypatch.setattr(wd, "run", boom)
    last = wd.tick()
    assert last["failed"] is True
    assert last["check_exit"] == -1
    assert "TICK FAILED" in (log_dir / "watchdog.log").read_text(encoding="utf-8")


def test_an_away_seat_is_never_nudged():
    """A seat that is out of quota cannot answer a nudge, so a loop that pings it all
    day trains the team to ignore the loop. An away seat is skipped entirely."""
    info = agent_info(stream=["RV-02"], claimable=["RV-02"], idle=600)
    info["away"] = True
    s = survey({"antigravity": info})
    assert wd.decide(s, {"nudges": {}}, cfg()) == []


def test_the_same_seat_is_nudged_when_it_is_not_away():
    """The away flag must not become a permanent mute: drop it and the nudge returns."""
    s = survey({"antigravity": agent_info(
        stream=["RV-02"], claimable=["RV-02"], idle=600)})
    assert [a["to"] for a in wd.decide(s, {"nudges": {}}, cfg())] == ["antigravity"]
