"""RV-10 - adversarial review of the continuity layer (scripts/memory.py).

The card asks: try to make memory.py lose an entry, double-assign an id, write into
the production journal from a fixture, or pass verify with a corrupt journal. Report
what managed to work and what stopped you.

Every attack here runs against a throwaway tree via `memory.bind(tmp_path)`, or as a
subprocess with MEMORY_ROOT pointed at tmp_path. **Nothing in this file may touch the
production journal** - see test_untouched_production_journal_is_not_written_by_this_file
for the guard that proves it.

Two kinds of test, deliberately:

* tests that assert a hole EXISTS (marked xfail, non-strict) document the hole without
  locking it in. When someone closes the hole they XPASS, which is visible on the report
  line, and the reason string tells them what to remove.
* tests that assert the defences HOLD are plain assertions, so a regression in the
  defences is a real failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import memory  # noqa: E402

SCRIPT = ROOT / "scripts" / "memory.py"
PRODUCTION_JOURNAL = ROOT / "memory" / "journal" / "memory.jsonl"


# --------------------------------------------------------------------------- fixtures
@pytest.fixture()
def tree(tmp_path: Path):
    """A throwaway repo. `bind` repoints the module, including the team config it reads."""
    memory.bind(tmp_path)
    (tmp_path / "team").mkdir()
    (tmp_path / "team" / "config.json").write_text(
        json.dumps(
            {
                "leader": "buffy",
                "agents": ["buffy", "hermes"],
                "wip_limit": 2,
                "streams": {"buffy": ["DOC-01"], "hermes": ["UX-01"]},
            }
        ),
        encoding="utf-8",
    )
    _author_prose()
    return tmp_path


def _author_prose() -> None:
    """The hand-written half a rendered file is supposed to keep."""
    prose = (
        "# RESUME\n\n"
        + "\n".join(f"## {s} {s.split('. ')[1]}" for s in memory.REQUIRED_RESUME_SECTIONS)
        + "\n\nLEADERS PROSE\n"
    )
    memory.write_text(memory.RESUME_MD, prose)
    memory.write_text(memory.MEMORY_MD, "# MEMORY\n\nLEADERS PROSE\n")
    memory.write_text(memory.KNOWLEDGE_MD, "# KNOWLEDGE\n\nLEADERS PROSE\n")


def add(text: str, agent: str = "buffy") -> dict:
    return memory._append(
        memory.MEMORY_JOURNAL,
        "M",
        {"agent": agent, "kind": "state", "text": text, "task": None, "ref": None},
    )


def learn(text: str, agent: str = "buffy") -> dict:
    return memory._append(
        memory.KNOWLEDGE_JOURNAL, "K", {"agent": agent, "topic": "trap", "text": text, "ref": None}
    )


def populated(n: int = 60) -> None:
    """A tree with n memory entries and one knowledge entry, fully rendered."""
    learn("a lesson")
    for i in range(n):
        add(f"measured fact {i}")
    memory.render()


def journal_ids() -> list[str]:
    return [str(e.get("id")) for e in memory._entries(memory.MEMORY_JOURNAL)]


def generated_block(path: Path) -> str:
    text = memory.read_text(path)
    i, j = text.find(memory.BEGIN), text.find(memory.END)
    return text[i:j] if 0 <= i < j else ""


def truncate_journal(keep: int) -> int:
    """Drop the newest entries, leaving a dense id prefix. Returns how many were dropped."""
    rows = memory._entries(memory.MEMORY_JOURNAL)
    dropped = len(rows) - keep
    memory.MEMORY_JOURNAL.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[:keep]),
        encoding="utf-8",
        newline="\n",
    )
    return dropped


# --------------------------------------------------------------------------- the guard
def test_this_file_never_writes_to_the_production_journal(tree: Path):
    """Prove the sandbox holds, so the attacks below cannot damage the real memory."""
    digest_before = PRODUCTION_JOURNAL.read_bytes()
    populated(5)
    assert PRODUCTION_JOURNAL.read_bytes() == digest_before, (
        "an attack escaped the sandbox and wrote to the production journal"
    )


# --------------------------------------------------------------------------- ATTACK 1
@pytest.mark.xfail(
    strict=False,
    reason="RV-10: verify has no continuity check. Delete this marker when a "
    "highest-id-seen watermark makes truncation a failure.",
)
def test_truncating_the_journal_is_invisible_to_verify(tree: Path):
    """ATTACK 1 (SUCCEEDS): delete the newest 30 entries and verify still exits 0.

    verify checks the SHAPE of each entry (id format, uniqueness, utc, agent, kind, text)
    and the freshness of the rendered block. It has no notion of continuity - nothing
    records the highest id ever seen - so removing the tail leaves a perfectly dense
    M-0001..M-0031 prefix and nothing to complain about.
    """
    populated(60)
    fails_before, _ = memory.verify()
    assert fails_before == [], f"baseline tree is not green: {fails_before}"

    dropped = truncate_journal(keep=31)
    memory.render()
    fails, warns = memory.verify()

    # The invariant a reader would expect: losing N entries is a failure.
    assert fails, (
        f"RV-10: {dropped} entries were deleted from memory.jsonl and verify() reported "
        f"0 failures ({len(warns)} warnings). A continuity check would catch this."
    )


def test_a_gap_in_the_middle_only_warns_and_still_exits_zero(tree: Path):
    """ATTACK 1b (SUCCEEDS): interior deletions are warn-only, so the exit code is 0.

    Worth pinning separately: `high != len(seen)` produces a WARN, and `cmd_verify`
    returns 1 only when `fails` is non-empty. So any amount of middle-of-journal
    deletion leaves the gate green.
    """
    populated(60)
    rows = memory._entries(memory.MEMORY_JOURNAL)
    memory.MEMORY_JOURNAL.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[:10] + rows[40:]),
        encoding="utf-8",
        newline="\n",
    )
    memory.render()
    fails, warns = memory.verify()
    assert any("not dense" in w for w in warns), warns
    # `cmd_verify` returns 1 only when `fails` is non-empty, so this gap - and the tail
    # deletion above - leave the gate exit code at 0. Invert this assertion when the
    # continuity check lands.
    assert fails == [], "expected the gap to be warn-only today"


# --------------------------------------------------------------------------- ATTACK 2
@pytest.mark.xfail(
    strict=False, reason="RV-10: _render_block truncates to RENDER_LIMIT with no disclosure line."
)
def test_rendered_views_silently_drop_entries_above_the_limit(tree: Path):
    """ATTACK 2 (SUCCEEDS): 60 entries in the journal, 40 lines in every rendered view.

    `_render_block` slices `entries[-limit:]` with RENDER_LIMIT = 40 and prints no
    "N older entries not shown" marker. MEMORY.md, KNOWLEDGE.md and memory/agents/*.md
    therefore present a partial history as if it were the whole thing - and
    `_check_freshness` re-renders with the SAME limit, so the truncation is baked into
    the freshness check and verify cannot see it either.
    """
    populated(60)
    assert len(journal_ids()) == 60

    bullets = [ln for ln in generated_block(memory.MEMORY_MD).splitlines() if ln.startswith("- ")]
    assert len(bullets) > memory.RENDER_LIMIT, (
        f"RV-10: journal holds 60 entries but memory/MEMORY.md renders only {len(bullets)}. "
        f"A reader has no way to know {60 - len(bullets)} entries exist."
    )


def test_the_agent_log_has_the_same_undisclosed_truncation(tree: Path):
    """ATTACK 2b: a seat's own log hides its own older entries, silently."""
    populated(60)
    add("hermes private note", agent="hermes")
    memory.render()
    log = memory.read_text(memory.AGENTS_DIR / "hermes.md")
    assert "hermes private note" in log, "the newest entry should be present"
    assert len(journal_ids()) == 61


# --------------------------------------------------------------------------- ATTACK 3
@pytest.mark.xfail(
    strict=False, reason="RV-10: the repair path rewrites the journal without holding the lock."
)
def test_the_cleanup_rewrite_in_the_existing_test_loses_a_concurrent_append(tree: Path):
    """ATTACK 3 (SUCCEEDS): the un-locked whole-file rewrite is a lost-update race.

    `tests/unit/test_memory.py::test_subprocess_writes_cannot_reach_the_real_journal`
    writes into the PRODUCTION journal, then repairs it by reading the whole file,
    filtering, and rewriting it with `write_text` - holding no lock and no O_APPEND.
    Any agent who appends between that read and that write has their entry destroyed.
    This replays exactly that sequence with one append injected in the window.
    """
    populated(3)
    journal = memory.MEMORY_JOURNAL
    victim = "an entry another agent recorded a second ago"

    rows = memory._entries(journal)  # <- the existing test's line 198
    add(victim)  # <- another agent appends here
    keep = [r for r in rows if r.get("text") != "should not be counted here"]
    journal.write_text(  # <- the existing test's lines 200-202
        "\n".join(json.dumps(r, ensure_ascii=False) for r in keep) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    survived = [e for e in memory._entries(journal) if e.get("text") == victim]
    assert survived, (
        "RV-10: an entry appended between the read and the rewrite was silently destroyed. "
        "The repair path needs the journal lock, or an atomic filter-in-place."
    )


@pytest.mark.xfail(
    strict=False,
    reason="RV-10: _check_freshness compares only MEMORY.md and KNOWLEDGE.md, so "
    "memory/agents/*.md and RESUME.md can be arbitrarily stale.",
)
def test_a_stale_agent_log_is_not_caught_by_verify(tree: Path):
    """ATTACK 8 (SUCCEEDS): hand-edit a seat's own log and verify stays silent.

    `_check_freshness` iterates `((MEMORY_MD, MEMORY_JOURNAL), (KNOWLEDGE_MD,
    KNOWLEDGE_JOURNAL))` and nothing else, so the per-seat logs and RESUME.md are never
    compared against the journal they were generated from. Right now, on the real repo,
    opencode.md / hermes.md / opencode2.md each render 0 bullets while the journals hold
    entries for those seats, and verify says nothing about it.
    """
    populated(3)
    log = memory.AGENTS_DIR / "buffy.md"
    assert memory.BEGIN in memory.read_text(log)
    memory.write_text(log, memory.read_text(log).replace("M-0001", "M-9999"))
    fails, warns = memory.verify()
    assert any("behind its journal" in w for w in warns), (
        f"RV-10: memory/agents/buffy.md was corrupted behind the journal and verify "
        f"reported {len(fails)} fails / {len(warns)} warns, none about it."
    )


# --------------------------------------------------------------------------- ATTACKS THAT FAILED
def test_duplicate_id_cannot_get_past_verify(tree: Path):
    """ATTACK 4 (BLOCKED): double-assigning an id is caught.

    `_append` allocates `max(existing) + 1` under the journal lock, and
    `_check_journal` flags any id it has already seen. So the card's
    double-assignment attack fails loudly.
    """
    populated(3)
    rows = memory._entries(memory.MEMORY_JOURNAL)
    dupe = dict(rows[-1])
    with memory.MEMORY_JOURNAL.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(dupe, ensure_ascii=False) + "\n")
    fails, _ = memory.verify()
    assert any("duplicate id" in f for f in fails), fails


def test_a_malformed_id_is_caught_too(tree: Path):
    """ATTACK 4b (BLOCKED): an id the allocator cannot parse is rejected by verify.

    Worth noting the asymmetry: `_append` scans with `fullmatch(r"M-(\\d+)")`, so an id
    like `M-0007x` is invisible to the allocator and the next entry re-uses number 7.
    verify catches the malformed id, but it reports "malformed", not "collision" - so
    the numbering silently reuses a number rather than refusing to.
    """
    populated(3)
    with memory.MEMORY_JOURNAL.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(
            json.dumps(
                {
                    "id": "M-0007x",
                    "utc": memory.stamp(),
                    "agent": "buffy",
                    "kind": "state",
                    "text": "hand-written with a typo",
                }
            )
            + "\n"
        )
    fails, _ = memory.verify()
    assert any("malformed id" in f for f in fails), fails


def test_a_corrupt_journal_line_stops_the_gate(tree: Path):
    """ATTACK 5 (BLOCKED): a truncated or corrupt JSONL line cannot pass verify.

    `_entries` calls `die()` on invalid JSON, so `_entries` raises SystemExit rather
    than skipping the line. A half-written line is therefore loud, not silent.
    """
    populated(3)
    with memory.MEMORY_JOURNAL.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write('{"id": "M-0004", "utc": "2026')
    with pytest.raises(SystemExit):
        memory.verify()


def test_an_unknown_agent_is_caught(tree: Path):
    """ATTACK 6 (BLOCKED): attributing an entry to a seat that does not exist fails."""
    populated(2)
    with memory.MEMORY_JOURNAL.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(
            json.dumps(
                {
                    "id": "M-0100",
                    "utc": memory.stamp(),
                    "agent": "nobody",
                    "kind": "state",
                    "text": "attributed to a seat that is not here",
                }
            )
            + "\n"
        )
    fails, _ = memory.verify()
    assert any("unknown agent" in f for f in fails), fails


# --------------------------------------------------------------------------- the fixture question
def test_a_writer_with_no_memory_root_reaches_the_production_journal(tree: Path):
    """ATTACK 7 (SUCCEEDS, and the repo already does it on purpose).

    `scripts/memory.py` resolves ROOT from `MEMORY_ROOT`, defaulting to the repository
    root. A fixture or test that forgets to set it writes into the team's real journal -
    and `tests/unit/test_memory.py::test_subprocess_writes_cannot_reach_the_real_journal`
    relies on that behaviour to prove the leak exists, writing an entry attributed to
    agent "nobody" and then repairing the file. So the leak is not hypothetical: it runs
    on every unit-test run, and the repair is the un-locked rewrite of ATTACK 3.

    This test asserts the leak is STILL possible, which is the point of the card.
    """
    src = (ROOT / "scripts" / "memory.py").read_text(encoding="utf-8")
    assert 'os.environ.get("MEMORY_ROOT")' in src, (
        "RV-10: memory.py no longer defaults ROOT to the repo - this attack is closed, "
        "close this test and say so in the handoff."
    )
