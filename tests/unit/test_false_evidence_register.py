"""Tests for the false-evidence register (scripts/false_evidence_register.py).

The register's whole value is that it stays true as the board moves. Two things
can make it lie, and each gets a test:

* a **new** rejection nobody has classified - the claim is that this is a hard
  error, not a silent omission, because an unclassified rejection is a pattern
  nobody has looked at;
* a **stale** pattern entry or a drifted roster - the claim is that `--check`
  catches a register that no longer matches the handoffs.

A register that quietly drifts is worse than no register, so
`test_unclassified_rejection_is_a_hard_error` is the load-bearing one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import false_evidence_register as fer  # noqa: E402


def write_handoff(dirpath: Path, name: str, author: str = "someone") -> Path:
    dirpath.mkdir(parents=True, exist_ok=True)
    p = dirpath / name
    p.write_text(
        f"# {name}\n\n## Claim\n- claim: `x-1` · task: `XX-01` · author: `{author}`\n\n"
        "## Evidence\nevidence/ops/nope.md\n\n"
        "### Rejected by `buffy` - 2026-10-05T15:01:32Z\nRequired before re-handoff: because.\n",
        encoding="utf-8",
    )
    return p


# ------------------------------------------------------------------ extraction
def test_finds_every_rejected_handoff():
    rows = fer.rejected_handoffs()
    assert len(rows) >= 10, "the board has at least ten rejections on record"
    assert {"HO-031", "HO-033", "HO-035"} <= {r["id"] for r in rows}


def test_reads_the_rejecting_agent_and_author():
    rows = {r["id"]: r for r in fer.rejected_handoffs()}
    assert rows["HO-031"]["author"] == "hermes"
    assert rows["HO-031"]["by"] == "buffy"
    assert rows["HO-031"]["task"] == "UX-08"
    assert rows["HO-031"]["when"].startswith("2026-10-05")


def test_non_rejected_handoffs_are_absent():
    ids = {r["id"] for r in fer.rejected_handoffs()}
    assert "HO-043" not in ids, "HO-043 is a clean handoff and must not appear"


# -------------------------------------------------------------------- patterns
def test_every_live_rejection_is_classified():
    assert fer.unclassified(fer.rejected_handoffs()) == []


def test_every_pattern_entry_exists_on_the_board():
    """A pattern keyed on a handoff nobody has is a row that can never recur."""
    live = {r["id"] for r in fer.rejected_handoffs()}
    stale = set(fer.PATTERNS) - live
    assert not stale, f"pattern entries for handoffs that are not rejected: {sorted(stale)}"


def test_every_pattern_has_prose_and_a_fix():
    for pat in {v[0] for v in fer.PATTERNS.values()}:
        assert pat in fer.PATTERN_TEXT, f"{pat} has no entry in PATTERN_TEXT"
        what, fix = fer.PATTERN_TEXT[pat]
        assert len(what) > 80 and len(fix) > 80, f"{pat} needs a real description and a real fix"


def test_the_three_rejections_share_one_pattern():
    """The headline claim of the register, asserted rather than asserted-in-prose."""
    pats = {hid: fer.PATTERNS[hid][0] for hid in ("HO-031", "HO-033", "HO-035")}
    assert len(set(pats.values())) == 1, f"expected one shared root cause, got {pats}"


# --------------------------------------------------------------- falsification
def test_unclassified_rejection_is_a_hard_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The claim under test: a new rejection nobody classified must not be dropped."""
    write_handoff(tmp_path / "team" / "handoffs", "HO-900-brand-new.md", "newface")
    monkeypatch.setattr(fer, "ROOT", tmp_path)
    assert fer.unclassified(fer.rejected_handoffs()) == ["HO-900"]
    with pytest.raises(SystemExit) as exc:
        fer.build()
    assert "HO-900" in str(exc.value)
    assert "new pattern" in str(exc.value)


def test_citation_audit_is_skipped_where_it_would_be_noise():
    """A hidden-blast-radius rejection must not get a verdict about citations."""
    assert "C-literal-generator" in fer.CITATION_RELEVANT
    assert "A-hidden-blast-radius" not in fer.CITATION_RELEVANT


def test_audit_evidence_reports_a_verdict_for_a_real_handoff():
    verdict, detail = fer.audit_evidence("HO-031")
    assert verdict in {"PASS", "MISMATCH", "NO CITATION", "INCONCLUSIVE"}
    assert detail


# ------------------------------------------------------------------ generation
def test_check_reports_current():
    assert fer.main(["--check"]) == 0


def test_check_fails_when_the_register_is_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    stale = tmp_path / "evidence" / "ops" / "false-evidence-register.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("this is not what the generator produces\n", encoding="utf-8")
    monkeypatch.setattr(fer, "REGISTER", stale)
    assert fer.main(["--check"]) == 1


def test_build_output_carries_the_generated_markers():
    out = fer.build()
    assert fer.BEGIN in out and fer.END in out
    assert out.count(fer.BEGIN) == 1 and out.count(fer.END) == 1


def test_build_is_deterministic():
    assert fer.build() == fer.build()
