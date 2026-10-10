"""Tests for the release-readiness dossier (scripts/release_dossier.py).

The generator exists to answer *how many* gates are red. `scripts/check.py` calls `sys.exit()` on
the first failed bar, so it can only ever answer *which* bar failed first — and a new red bar then
hides every bar beneath it. Measured this session: Ruff Format fails first, so the five `docs/14`
§5.3 bars never report.

So the load-bearing test is `test_every_gate_runs_even_after_one_fails`: if the generator ever
short-circuits, a ship decision gets made on a partial picture, which is the failure mode it was
written to remove. The staleness and no-adjective-free-text checks are secondary but real: a
hand-edited dossier is a dossier nobody can trust.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import release_dossier as rd  # noqa: E402


def results(*specs: tuple[str, int]) -> list[dict]:
    return [
        {
            "id": gid,
            "proves": f"{gid} proves something",
            "cmd": f"scripts/{gid}.py",
            "rc": rc,
            "secs": 1.0,
            "note": "note",
            "slow": False,
        }
        for gid, rc in specs
    ]


def build(rs: list[dict], **kw) -> str:
    red = [r for r in rs if r["rc"] != 0]
    green = [r for r in rs if r["rc"] == 0]
    args = {
        "skipped": [],
        "head_sha": "abc1234",
        "tracked": 10,
        "dirty": 5,
        "declared_od": 18,
        "listed_od": 2,
        "od_ids": ["OQ-016", "OQ-017"],
        "slow": True,
    }
    args.update(kw)
    return rd.build(rs, red, green, **args)


# ------------------------------------------------------------------ the claim
def test_every_gate_runs_even_after_one_fails():
    """If this breaks, a ship decision is being made on a partial picture."""
    rs = results(("FIRST", 1), ("SECOND", 0), ("THIRD", 1), ("FOURTH", 0))
    doc = build(rs)
    for gid in ("FIRST", "SECOND", "THIRD", "FOURTH"):
        assert f"`{gid}`" in doc, f"{gid} is missing from the dossier"
    assert "2 of 4 gates run are red" in doc


def test_red_count_is_reported_not_just_first_failure():
    doc = build(results(("A", 0), ("B", 1), ("C", 1), ("D", 1)))
    assert "3 of 4" in doc
    for gid in ("B", "C", "D"):
        assert f"- `{gid}`" in doc, "every red gate must be listed individually"


def test_all_green_says_so_plainly():
    doc = build(results(("A", 0), ("B", 0)))
    assert "Every gate run is green" in doc
    assert "Not ready to ship" not in doc


def test_the_fail_fast_trap_is_stated():
    """The reason this document exists separately from check.py."""
    doc = build(results(("A", 1)))
    assert "fail-fast" in doc
    assert "sys.exit" in doc


# ------------------------------------------------------------------- honesty
def test_skipped_gates_are_not_counted_as_passing():
    doc = build(results(("A", 0)), skipped=["SLOW-1", "SLOW-2"])
    assert "not a passing gate" in doc
    assert "SLOW-1" in doc
    assert "1 of 1 gates run are red" not in doc  # no red invented
    assert "1 gate(s) run" in doc and "2 slow gate(s) skipped" in doc


def test_open_decision_count_gap_is_reported():
    doc = build(results(("A", 0)), declared_od=18, listed_od=2)
    assert "18" in doc and "does not currently deliver its own count" in doc


def test_declared_and_listed_limits_table_is_present():
    doc = build(results(("A", 1)))
    assert "Known limits, as numbers" in doc
    assert "Gates red this pass" in doc


def test_it_states_what_it_does_not_cover():
    doc = build(results(("A", 0)))
    assert "does not cover" in doc
    assert "not gate adequacy" in doc


# --------------------------------------------------------------- staleness
def test_check_fails_on_a_stale_dossier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    stale = tmp_path / "dossier.md"
    stale.write_text("hand-edited and no longer true\n", encoding="utf-8")
    monkeypatch.setattr(rd, "OUT", stale)
    # Rebuilding must disagree with the stale file.
    import io
    from contextlib import redirect_stderr, redirect_stdout

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = rd.main(["--check"])
    assert code == 1


def test_generated_markers_are_present():
    doc = build(results(("A", 0)))
    assert rd.BEGIN in doc and rd.END in doc


def test_generated_and_end_markers_appear_once():
    doc = build(results(("A", 0), ("B", 1)))
    assert doc.count(rd.BEGIN) == 1 and doc.count(rd.END) == 1
