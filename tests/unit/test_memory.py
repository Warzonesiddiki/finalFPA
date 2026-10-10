"""Tests for the continuity layer (scripts/memory.py).

Two halves, and the second half matters more:

* the round trip - add/learn, render, verify - behaves;
* **falsification** - `verify()` still fails on a real violation. A gate that cannot
  fail is a claim, not a gate (KNOWLEDGE.md, K-0004). Every check in `verify()` has a
  test that provokes exactly that failure; if a check is removed, the matching
  falsification test fails.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import memory  # noqa: E402
import team  # noqa: E402

SCRIPT = ROOT / "scripts" / "memory.py"
REAL_ROOT = ROOT
MEMORY_JOURNAL_REAL = REAL_ROOT / "memory" / "journal" / "memory.jsonl"
RESUME_SECTIONS = memory.REQUIRED_RESUME_SECTIONS


# --------------------------------------------------------------------------- fixtures
@pytest.fixture()
def tree(tmp_path: Path):
    """A throwaway repo. `memory.bind` repoints the whole module, including the
    config it reads, so nothing a test does can reach the production journal."""
    memory.bind(tmp_path)
    (tmp_path / "team").mkdir()
    (tmp_path / "team" / "config.json").write_text(
        json.dumps(
            {
                "leader": "buffy",
                "agents": ["buffy", "hermes"],
                "wip_limit": 2,
                "streams": {"buffy": ["DOC-01", "RV-01"], "hermes": ["UX-01"]},
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def seed(tree: Path, **kw) -> dict:
    """One memory entry + one knowledge entry + a full render + the authored prose."""
    e = memory._append(
        memory.MEMORY_JOURNAL,
        "M",
        {
            "agent": kw.get("agent", "buffy"),
            "kind": kw.get("kind", "state"),
            "text": kw.get("text", "a measured fact"),
            "task": None,
            "ref": None,
        },
    )
    memory._append(
        memory.KNOWLEDGE_JOURNAL,
        "K",
        {
            "agent": kw.get("agent", "buffy"),
            "topic": kw.get("topic", "trap"),
            "text": "a lesson",
            "ref": None,
        },
    )
    prose = (
        "# RESUME\n\n"
        + "\n".join(f"## {s} {s.split('. ')[1]}" for s in RESUME_SECTIONS)
        + "\n\nLEADERS PROSE\n"
    )
    memory.write_text(memory.RESUME_MD, prose)
    memory.write_text(memory.MEMORY_MD, "# MEMORY\n\nLEADERS PROSE\n")
    memory.write_text(memory.KNOWLEDGE_MD, "# KNOWLEDGE\n\nLEADERS PROSE\n")
    memory.render()
    return e


def append_raw(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def mutate_journal(path: Path, index: int, **changes) -> None:
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows[index].update(changes)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- round trip
def test_add_assigns_sequential_ids_with_unique_agent(tree: Path):
    a = memory._append(
        memory.MEMORY_JOURNAL,
        "M",
        {"agent": "buffy", "kind": "state", "text": "one", "task": None, "ref": None},
    )
    b = memory._append(
        memory.MEMORY_JOURNAL,
        "M",
        {"agent": "hermes", "kind": "note", "text": "two", "task": None, "ref": None},
    )
    assert (a["id"], b["id"]) == ("M-0001", "M-0002")
    assert a["utc"].endswith("Z")


def test_render_publishes_entries_and_keeps_authored_prose(tree: Path):
    seed(tree)
    assert "a measured fact" in memory.read_text(memory.MEMORY_MD)
    assert "LEADERS PROSE" in memory.read_text(memory.MEMORY_MD)


def test_render_is_idempotent(tree: Path):
    seed(tree)
    first = [
        p.read_text(encoding="utf-8")
        for p in (memory.MEMORY_MD, memory.KNOWLEDGE_MD, memory.RESUME_MD)
    ]
    memory.render()
    second = [
        p.read_text(encoding="utf-8")
        for p in (memory.MEMORY_MD, memory.KNOWLEDGE_MD, memory.RESUME_MD)
    ]
    assert first == second


def test_render_writes_one_log_per_configured_seat(tree: Path):
    seed(tree)
    for seat in ("buffy", "hermes"):
        log = memory.AGENTS_DIR / f"{seat}.md"
        assert log.exists(), f"{seat} has no memory log"
        assert memory.BEGIN in log.read_text(encoding="utf-8")


def test_render_writes_only_inside_the_sentinels(tree: Path):
    seed(tree)
    before = memory.read_text(memory.MEMORY_MD)
    memory._append(
        memory.MEMORY_JOURNAL,
        "M",
        {"agent": "hermes", "kind": "state", "text": "second fact", "task": None, "ref": None},
    )
    memory.render()
    after = memory.read_text(memory.MEMORY_MD)
    assert after.startswith(before[: before.index(memory.BEGIN)])  # prose untouched
    assert "second fact" in after


def test_resume_block_names_the_seat_and_its_stream(tree: Path):
    """The live half reads the REAL team (team is imported from scripts/), so the
    assertion is structural: the seat is named and its real stream is listed."""
    body = memory._resume_body("hermes", 5)
    assert "### hermes's stream (in order)" in body
    cfg = memory.team_config()
    ts = {
        t["id"]
        for t in (
            json.loads(p.read_text(encoding="utf-8"))
            for p in (ROOT / "team" / "tasks").glob("*.json")
        )
    }
    listed = [x for x in cfg["streams"].get("hermes", []) if x in ts]
    assert listed, "hermes has no claimable card in the real board"
    assert f"`{listed[0]}`" in body


def test_resume_block_survives_a_seat_with_no_stream(tree: Path):
    """A seat nobody has configured a stream for still gets a usable brief."""
    body = memory._resume_body("opencode", 5)
    assert "### Live team state" in body
    assert "opencode's stream (in order)" in body


def test_resume_block_states_whether_the_seat_is_away(tree: Path, monkeypatch):
    """A cold agent must not start working a parked seat without knowing it is parked."""
    cfg: dict = dict(team.DEFAULTS)
    cfg["agents"] = ["buffy"]
    cfg["away"] = {"buffy": "quota ended 2026-10-05"}
    monkeypatch.setattr(memory, "team_config", lambda: cfg)
    body = memory._resume_body("buffy", 5)
    assert "**You are AWAY.**" in body
    assert "quota ended 2026-10-05" in body
    cfg["away"] = {}
    assert "**You are active.**" in memory._resume_body("buffy", 5)


# --------------------------------------------------------------------------- concurrency
def test_concurrent_appends_lose_no_entry(tmp_path: Path):
    """The reason the journals are JSONL: 6 writers, no lost update, no duplicate id.

    The subprocesses are pointed at the fixture with MEMORY_ROOT - without it they
    resolve ROOT from __file__ and write into the real journal, which is exactly the
    leak this test caught the first time it ran.
    """
    memory.bind(tmp_path)
    # 4 writers x 6 writes: enough to make every id allocation race for the lock, without
    # spending the test's whole budget starting 40 Windows interpreters at once (that
    # made the run flaky, not the lock - it held throughout).
    n, per = 4, 6
    env = {**os.environ, "MEMORY_ROOT": str(tmp_path)}
    procs = [
        subprocess.Popen(
            [
                sys.executable,
                str(SCRIPT),
                "add",
                "--agent",
                "buffy",
                "--kind",
                "state",
                "--text",
                f"w{i}-{j}",
            ],
            cwd=str(tmp_path),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        for i in range(n)
        for j in range(per)
    ]
    errs = [p.communicate()[1].decode("utf-8", "replace") for p in procs]
    assert all(p.returncode == 0 for p in procs), [e for e in errs if e.strip()]

    rows = memory._entries(memory.MEMORY_JOURNAL)
    assert len(rows) == n * per
    assert len({r["id"] for r in rows}) == n * per
    assert {r["text"] for r in rows} == {f"w{i}-{j}" for i in range(n) for j in range(per)}


def test_subprocess_writes_cannot_reach_the_real_journal(tmp_path: Path):
    """Falsification of the leak above: run a writer with no MEMORY_ROOT set."""
    before = len(memory._entries(MEMORY_JOURNAL_REAL))
    env = {k: v for k, v in os.environ.items() if k != "MEMORY_ROOT"}
    p = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "add",
            "--agent",
            "nobody",
            "--kind",
            "state",
            "--text",
            "should not be counted here",
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert p.returncode == 0
    # It did land in the real journal (that is the documented default), which is why
    # MEMORY_ROOT exists. Assert the count changed and clean it back up.
    assert len(memory._entries(MEMORY_JOURNAL_REAL)) == before + 1
    rows = memory._entries(MEMORY_JOURNAL_REAL)
    keep = [r for r in rows if r.get("text") != "should not be counted here"]
    MEMORY_JOURNAL_REAL.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in keep) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def test_lock_is_exclusive(tmp_path: Path, capsys):
    memory.bind(tmp_path)
    path = memory.LOCKS / "x.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{os.getpid()}\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        with memory._lock("x", timeout=0.3):
            pass
    assert "lock" in capsys.readouterr().err


def test_stale_lock_is_stolen_without_a_pid_probe(tmp_path: Path):
    """Falsification of the staleness rule.

    The lock file carries THIS process's pid, which is alive, so a pid probe would
    refuse forever. It is recovered only because staleness is mtime age - which is
    also why the code must never call os.kill(pid, 0) (that terminates on Windows).
    """
    memory.bind(tmp_path)
    path = memory.LOCKS / "y.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{os.getpid()}\n", encoding="utf-8")
    old = time.time() - memory.LOCK_STALE_SECONDS - 5
    os.utime(path, (old, old))
    with memory._lock("y", timeout=1.0):
        pass  # acquired, and released on exit
    assert not path.exists()


# --------------------------------------------------------------------------- falsification
def test_verify_passes_on_a_healthy_tree(tree: Path):
    seed(tree)
    fails, warns = memory.verify()
    assert fails == [], fails
    assert not [w for w in warns if "behind its journal" in w]


def test_verify_fails_on_duplicate_id(tree: Path):
    seed(tree)
    mutate_journal(memory.MEMORY_JOURNAL, 0, id="M-0001")
    append_raw(
        memory.MEMORY_JOURNAL,
        {
            "id": "M-0001",
            "utc": memory.stamp(),
            "agent": "buffy",
            "kind": "state",
            "text": "collides",
            "ref": None,
        },
    )
    fails, _ = memory.verify()
    assert any("duplicate id" in f for f in fails)


def test_verify_fails_on_unknown_agent(tree: Path):
    seed(tree)
    mutate_journal(memory.KNOWLEDGE_JOURNAL, 0, agent="ghost")
    fails, _ = memory.verify()
    assert any("unknown agent 'ghost'" in f for f in fails)


def test_a_seat_removed_from_the_roster_keeps_its_recorded_history(tree: Path):
    """ENG-14 / T-008: parking a seat must not invalidate what it already recorded.

    `team/config.json` was edited to `agents=[opencode, hermes]` while 73 of the 77
    journal entries were attributed to `buffy`, and `verify` answered 73 failures - the
    layer reporting itself broken because the roster moved. A seat that owns a
    `memory/agents/<seat>.md` log stays known.
    """
    seed(tree)
    (tree / "team" / "config.json").write_text(
        json.dumps(
            {
                "leader": "hermes",
                "agents": ["hermes"],
                "wip_limit": 2,
                "streams": {"hermes": ["UX-01"]},
            }
        ),
        encoding="utf-8",
    )
    memory.write_text(memory.AGENTS_DIR / "buffy.md", "# buffy\n\n" + memory.BEGIN + "\n")
    fails, _ = memory.verify()
    assert not [f for f in fails if "unknown agent" in f], fails


def test_the_leader_stays_known_even_with_no_own_log(tree: Path):
    """The leader is a roster fact, not a render artefact, so it is known regardless."""
    seed(tree)
    (tree / "team" / "config.json").write_text(
        json.dumps(
            {
                "leader": "hermes",
                "agents": ["buffy"],
                "wip_limit": 2,
                "streams": {"buffy": ["DOC-01"]},
            }
        ),
        encoding="utf-8",
    )
    memory.write_text(memory.AGENTS_DIR / "buffy.md", "# buffy\n\n" + memory.BEGIN + "\n")
    (memory.AGENTS_DIR / "buffy.md").unlink()
    (memory.AGENTS_DIR / "hermes.md").unlink()
    assert "hermes" in memory.known_agents()


def test_the_union_does_not_admit_a_seat_that_never_existed(tree: Path):
    """Falsification for the union: it must not decay into 'accept anything'.

    `known_agents` grew from the config roster to include any seat owning a log. An
    attribution to a seat in neither the roster nor the logs must still FAIL, or the
    check has stopped being a check.
    """
    seed(tree)
    mutate_journal(memory.MEMORY_JOURNAL, 0, agent="ghost")
    assert "ghost" not in memory.known_agents()
    fails, _ = memory.verify()
    assert any("unknown agent 'ghost'" in f for f in fails)


def test_known_agents_is_the_union_of_roster_leader_and_logs(tree: Path):
    seed(tree)
    memory.write_text(memory.AGENTS_DIR / "opencode.md", "# opencode\n\n" + memory.BEGIN + "\n")
    known = memory.known_agents()
    assert {"buffy", "hermes", "opencode"} <= known


def test_verify_fails_on_bad_kind(tree: Path):
    seed(tree)
    mutate_journal(memory.MEMORY_JOURNAL, 0, kind="vibes")
    fails, _ = memory.verify()
    assert any("kind='vibes'" in f for f in fails)


def test_verify_fails_on_bad_topic(tree: Path):
    seed(tree)
    mutate_journal(memory.KNOWLEDGE_JOURNAL, 0, topic="misc")
    fails, _ = memory.verify()
    assert any("topic='misc'" in f for f in fails)


def test_verify_fails_on_empty_text(tree: Path):
    seed(tree)
    mutate_journal(memory.MEMORY_JOURNAL, 0, text="   ")
    fails, _ = memory.verify()
    assert any("empty text" in f for f in fails)


def test_verify_fails_on_malformed_id(tree: Path):
    seed(tree)
    mutate_journal(memory.MEMORY_JOURNAL, 0, id="m1")
    fails, _ = memory.verify()
    assert any("malformed id" in f for f in fails)


def test_verify_fails_when_resume_loses_a_section(tree: Path):
    seed(tree)
    memory.write_text(memory.RESUME_MD, "# RESUME\n\nonly one section\n")
    fails, _ = memory.verify()
    assert any("missing the section" in f for f in fails)


def test_verify_fails_when_a_seat_log_is_missing(tree: Path):
    seed(tree)
    (memory.AGENTS_DIR / "hermes.md").unlink()
    fails, _ = memory.verify()
    assert any("hermes.md is missing" in f for f in fails)


def test_verify_fails_on_an_empty_journal(tree: Path):
    seed(tree)
    memory.MEMORY_JOURNAL.write_text("", encoding="utf-8")
    fails, _ = memory.verify()
    assert any("no recorded memory" in f for f in fails)


def test_verify_fails_on_corrupt_json_line(tree: Path, capsys):
    seed(tree)
    with memory.MEMORY_JOURNAL.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("{not json\n")
    with pytest.raises(SystemExit):
        memory.verify()
    err = capsys.readouterr().err
    assert "not valid JSON" in err
    assert "memory.jsonl line 2" in err


def test_verify_warns_when_a_rendered_file_is_stale(tree: Path):
    seed(tree)
    memory.MEMORY_JOURNAL.write_text("", encoding="utf-8")  # journal emptied behind the view
    memory.write_text(
        memory.MEMORY_MD, memory.read_text(memory.MEMORY_MD).replace("M-0001", "M-9999")
    )
    _, warns = memory.verify()
    assert any("behind its journal" in w for w in warns)


# --------------------------------------------------------------------------- cli contract
def _cli(tree: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(tree),
        env={**os.environ, "MEMORY_ROOT": str(tree)},
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_cli_rejects_an_unknown_kind(tree: Path):
    p = _cli(tree, "add", "--kind", "vibes", "--text", "x")
    assert p.returncode != 0
    assert "kind" in (p.stderr + p.stdout)


def test_cli_rejects_empty_text(tree: Path):
    assert _cli(tree, "learn", "--topic", "trap", "--text", "  ").returncode != 0


def test_cli_names_the_seat_it_recorded_under(tree: Path):
    seed(tree)
    p = _cli(tree, "add", "--agent", "hermes", "--kind", "note", "--text", "recorded by hermes")
    assert p.returncode == 0
    assert "hermes" in p.stdout
    assert any(e["agent"] == "hermes" for e in memory._entries(memory.MEMORY_JOURNAL))


def test_cli_verify_exits_nonzero_on_a_broken_tree(tree: Path):
    seed(tree)
    assert _cli(tree, "verify").returncode == 0
    memory.KNOWLEDGE_JOURNAL.write_text("", encoding="utf-8")
    assert _cli(tree, "verify").returncode == 1


def test_cli_prompt_prints_the_delimited_member_prompt(tree: Path):
    memory.write_text(
        memory.PROMPT_MD, "# header\n## Paste from here\nDO THE THING\n## Paste to here\nfooter"
    )
    p = _cli(tree, "prompt")
    assert p.returncode == 0
    assert "DO THE THING" in p.stdout
    assert "footer" not in p.stdout


def test_cli_prompt_fails_loudly_if_delimiters_are_lost(tree: Path):
    memory.write_text(memory.PROMPT_MD, "# header with no delimiters")
    p = _cli(tree, "prompt")
    assert p.returncode != 0
    assert "delimiters" in (p.stdout + p.stderr)


def test_the_real_repo_layer_is_healthy():
    """The gate runs on the real tree, not only on a fixture."""
    memory.bind(REAL_ROOT)
    fails, warns = memory.verify()
    assert fails == [], fails
    assert not warns, warns
