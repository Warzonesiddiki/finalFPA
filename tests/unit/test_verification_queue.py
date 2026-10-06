"""Tests for the verification queue (scripts/verification_queue.py).

The queue exists because measurement found verification concentrated on two seats, one of which
is AWAY: 26 handoffs waiting, median 317 min, 92% of all verifications done by `antigravity` (11)
and `buffy` (1), with four seats never verifying anything.

So the tests are mostly about the refusals and the spread, not the arithmetic:

* never assign to an **AWAY** seat — assigning to `antigravity` would look like a fair rotation
  and produce nothing;
* never assign a handoff to its **author** — a self-verification is not a verification, and
  `team.py verify` requires a different agent;
* **spread**, not FIFO — a queue that always hands work to the same two seats is the bug.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import verification_queue as vq  # noqa: E402

import team  # noqa: E402

NOW = datetime(2026, 10, 5, 20, 0, tzinfo=UTC)


def handoff(directory: Path, num: int, author: str, card: str, minutes_ago: int,
            verified_by: str | None = None, rejected_by: str | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    at = (NOW - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = [
        f"# HO-{num:03d} — {card}",
        "",
        "## Claim",
        f"- claim: `{author}-20261005T0000Z-aaaa` · task: `{card}` · author: `{author}`",
        f"- opened: {at} · handed off: {at}",
        "",
        "## Evidence",
        "evidence/ops/nope.md",
        "",
    ]
    if rejected_by:
        body += [f"### Rejected by `{rejected_by}` — 2026-10-05T19:00:00Z", "Required: redo.", ""]
    if verified_by:
        body += [f"### Verified by `{verified_by}` — 2026-10-05T19:30:00Z", "Re-ran the commands.", ""]
    p = directory / f"HO-{num:03d}-{card.lower()}.md"
    p.write_text("\n".join(body), encoding="utf-8")
    return p


@pytest.fixture()
def board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A throwaway board. Repointing team.TEAM/team.HANDOFFS keeps tests off the real one."""
    teamdir = tmp_path / "team"
    (teamdir / "handoffs").mkdir(parents=True)
    monkeypatch.setattr(team, "TEAM", teamdir)
    monkeypatch.setattr(team, "HANDOFFS", teamdir / "handoffs")
    return teamdir


def configure(board: Path, agents: list[str], away: dict[str, str] | None = None) -> None:
    (board / "config.json").write_text(
        json.dumps({"agents": agents, "away": away or {}}), encoding="utf-8"
    )


# ------------------------------------------------------------------- the queue
def test_queue_excludes_rejected_handoffs(board: Path):
    configure(board, ["a", "b"])
    hd = board / "handoffs"
    handoff(hd, 1, "a", "XX-01", 60)
    handoff(hd, 2, "a", "XX-02", 60, rejected_by="b")
    ids = {r["id"] for r in vq.waiting_handoffs(NOW)}
    assert ids == {"HO-001"}, "a rejected handoff is waiting for its author, not a verifier"


def test_queue_excludes_verified_handoffs(board: Path):
    configure(board, ["a", "b"])
    hd = board / "handoffs"
    handoff(hd, 1, "a", "XX-01", 60, verified_by="b")
    handoff(hd, 2, "a", "XX-02", 60)
    ids = {r["id"] for r in vq.waiting_handoffs(NOW)}
    assert ids == {"HO-002"}


def test_queue_is_oldest_first(board: Path):
    configure(board, ["a", "b"])
    hd = board / "handoffs"
    handoff(hd, 1, "a", "XX-01", 10)
    handoff(hd, 2, "a", "XX-02", 300)
    assert [r["id"] for r in vq.waiting_handoffs(NOW)] == ["HO-002", "HO-001"]


def test_wait_is_measured_from_handoff_not_now(board: Path):
    configure(board, ["a", "b"])
    handoff(board / "handoffs", 1, "a", "XX-01", 90)
    assert vq.waiting_handoffs(NOW)[0]["wait_min"] == pytest.approx(90.0, abs=0.01)


# ------------------------------------------------------------------ refusals
def test_away_seat_is_never_eligible(board: Path):
    cfg = team.config()
    cfg["agents"] = ["a", "b"]
    cfg["away"] = {"b": "quota ended"}
    assert vq.eligible("b", {"author": "a"}, cfg) == "AWAY (quota ended)"
    assert vq.eligible("a", {"author": "a"}, cfg) == "is the author"
    assert vq.eligible("c", {"author": "a"}, cfg) == "not a configured seat"
    assert vq.eligible("a", {"author": "b"}, cfg) == "", "a different seat is eligible"


def test_never_assigns_to_the_author(board: Path):
    configure(board, ["alice", "bob", "carol"])
    handoff(board / "handoffs", 1, "alice", "XX-01", 60)
    rows = vq.propose(vq.waiting_handoffs(NOW), team.config())
    assert rows[0]["verifier"] != "alice"


def test_never_assigns_to_an_away_seat(board: Path):
    configure(board, ["alice", "bob", "carol"], away={"bob": "quota ended"})
    for n in range(1, 7):
        handoff(board / "handoffs", n, "alice", f"XX-{n:02d}", 60 + n)
    rows = vq.propose(vq.waiting_handoffs(NOW), team.config())
    assert all(r["verifier"] != "bob" for r in rows)


def test_no_eligible_seat_yields_no_assignment(board: Path):
    """The falsification case: one seat, and it wrote the thing.

    The queue must report no verifier rather than propose a self-verification, which
    `team.py verify` would reject anyway.
    """
    configure(board, ["alice"])
    handoff(board / "handoffs", 1, "alice", "XX-01", 60)
    rows = vq.propose(vq.waiting_handoffs(NOW), team.config())
    assert rows[0]["verifier"] is None
    assert rows[0]["reason"] == "no eligible seat"


# ----------------------------------------------------------------- the spread
def test_rotation_spreads_across_seats(board: Path):
    configure(board, ["alice", "bob", "carol", "dave"])
    hd = board / "handoffs"
    for n in range(1, 13):
        handoff(hd, n, ["alice", "bob", "carol", "dave"][n % 4], f"XX-{n:02d}", 60 + n)
    rows = vq.propose(vq.waiting_handoffs(NOW), team.config())
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verifier"]] = counts.get(r["verifier"], 0) + 1
    assert len(counts) == 4, f"rotation left a seat idle: {counts}"
    assert max(counts.values()) - min(counts.values()) <= 1, f"lumpy rotation: {counts}"


def test_never_verified_seat_is_preferred(board: Path):
    """A seat that has verified nothing comes before one that has."""
    configure(board, ["alice", "bob"])
    hd = board / "handoffs"
    handoff(hd, 1, "alice", "XX-01", 60, verified_by="alice")  # alice has history
    handoff(hd, 2, "alice", "XX-02", 90)
    rows = {r["id"]: r for r in vq.propose(vq.waiting_handoffs(NOW), team.config())}
    assert rows["HO-002"]["verifier"] == "bob", "bob has never verified; he goes first"


def test_verification_history_counts_only_verified(board: Path):
    configure(board, ["alice", "bob"])
    hd = board / "handoffs"
    handoff(hd, 1, "alice", "XX-01", 60, verified_by="bob")
    handoff(hd, 2, "alice", "XX-02", 60)
    assert vq.verifier_load() == {"bob": 1}


# ---------------------------------------------------------------- the service level
def test_sla_breach_is_marked(board: Path):
    configure(board, ["alice", "bob"])
    hd = board / "handoffs"
    handoff(hd, 1, "alice", "XX-01", 10)
    handoff(hd, 2, "alice", "XX-02", 200)
    rows = {r["id"]: r for r in vq.propose(vq.waiting_handoffs(NOW), team.config(), sla_min=30)}
    assert rows["HO-001"]["breach"] is False
    assert rows["HO-002"]["breach"] is True


def test_stats_flag_concentration(board: Path):
    configure(board, ["alice", "bob", "carol"])
    hd = board / "handoffs"
    for n in range(1, 5):
        handoff(hd, n, "bob", f"XX-{n:02d}", 60, verified_by="alice")
    s = vq.stats(team.config())
    assert s["distinct_verifiers"] == 1
    assert s["load_concentration"] == pytest.approx(1.0)
    assert s["never_verified"] == ["bob", "carol"]


def test_proposal_is_deterministic(board: Path):
    configure(board, ["alice", "bob", "carol"])
    hd = board / "handoffs"
    for n in range(1, 8):
        handoff(hd, n, "alice", f"XX-{n:02d}", 60 + n)
    q, cfg = vq.waiting_handoffs(NOW), team.config()
    assert vq.propose(q, cfg) == vq.propose(q, cfg)


# ----------------------------------------------------------------- the CLI
# `--for` is the path a seat actually types, and it is where the AWAY refusal has
# to survive: a seat with no quota asking what to verify must be told no.
def _run(board: Path, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = vq.main(argv)
    return code, out.getvalue(), err.getvalue()


def test_cli_for_refuses_an_away_seat(board: Path, capsys):
    configure(board, ["alice", "bob"], away={"bob": "quota ended"})
    handoff(board / "handoffs", 1, "alice", "XX-01", 60)
    code, out, _ = _run(board, ["--for", "bob"])
    assert code == 1
    assert "AWAY" in out and "quota ended" in out


def test_cli_for_refuses_an_unknown_seat(board: Path):
    configure(board, ["alice"])
    code, out, _ = _run(board, ["--for", "nobody"])
    assert code == 1
    assert "not a configured seat" in out


def test_cli_for_lists_only_what_that_seat_should_verify(board: Path):
    configure(board, ["alice", "bob", "carol"])
    hd = board / "handoffs"
    for n in range(1, 7):
        handoff(hd, n, "alice", f"XX-{n:02d}", 60 + n)
    code, out, _ = _run(board, ["--for", "bob"])
    assert code == 0
    assert "verify these next" in out
    assigned = {r["id"] for r in vq.propose(vq.waiting_handoffs(), team.config())
                if r["verifier"] == "bob"}
    for hid in assigned:
        assert hid in out, f"{hid} is assigned to bob but absent from his list"
    for line in out.splitlines()[1:]:
        hid = line.split()[0]
        assert hid in assigned, f"{hid} listed for bob but assigned elsewhere"


def test_cli_queue_renders_without_error(board: Path):
    configure(board, ["alice", "bob"])
    handoff(board / "handoffs", 1, "alice", "XX-01", 60)
    code, out, _ = _run(board, [])
    assert code == 0
    assert "verification queue" in out
    assert "HO-001" in out
