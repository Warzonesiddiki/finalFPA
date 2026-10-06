"""Tests for the handoff `## Changed` tokeniser in scripts/team.py.

The rule this defends: a `## Changed` list is compared against the claim window and
against what exists on disk, so the tokeniser has to do two things at once that pull
in opposite directions - accept every file type a lane actually ships (a corpus lane
writes .xlsx, a packaging lane writes .pptx), and still reject a version string or a
section number that only looks like a path.

Every test below was added because the tokeniser got it wrong once. The two real
failures: `sample-data/import_history/{01.csv,02.xlsx}` was split on its own commas
and failed the existence check as a path that does not exist, and .xlsx was missing
from the allowlist, so 33 of the 55 files under sample-data/ could not be declared at
all - the gate was blind to exactly the lane that changes them most.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import team  # noqa: E402


def declared(body: str) -> set[str]:
    return team._declared_changed(f"## Changed\n{body}\n")


# --------------------------------------------------------------------------- acceptance
def test_accepts_the_extensions_every_lane_actually_ships():
    got = declared("app/engine/rules/rules_01_08.py, ui/src/main.tsx, "
                   "sample-data/gl/d365_gl_actuals.csv, "
                   "sample-data/import_history/02_gl_batch_039.xlsx, "
                   "dist/pilot-1.2.3.pptx, evidence/report.pdf, packaging/SBOM.json")
    assert got == {
        "app/engine/rules/rules_01_08.py", "ui/src/main.tsx",
        "sample-data/gl/d365_gl_actuals.csv",
        "sample-data/import_history/02_gl_batch_039.xlsx",
        "dist/pilot-1.2.3.pptx", "evidence/report.pdf", "packaging/SBOM.json",
    }


def test_accepts_a_dotfile_that_really_exists():
    assert declared(".nvmrc") == {".nvmrc"}
    assert declared("3.14.7") == set()
    assert declared("python-version") == set()


def test_accepts_a_dotted_version_string_beside_a_real_path():
    got = declared("app/cli/main.py on Python 3.14.7")
    assert got == {"app/cli/main.py"}


# --------------------------------------------------------------------------- rejection
@pytest.mark.parametrize("line", [
    "3.14.7",
    "940 passed",
    "docs/18",
    "--no-cache",
    "section 5.3",
])
def test_rejects_tokens_that_only_look_like_paths(line: str):
    assert declared(line) == set()


def test_rejects_a_remote_url():
    assert declared("https://example.com/x.py") == set()


# --------------------------------------------------------------------------- brace groups
def test_expands_a_brace_group_into_its_members():
    assert declared("sample-data/import_history/{01_bank_batch_037.csv,02_gl_batch_039.xlsx}") == {
        "sample-data/import_history/01_bank_batch_037.csv",
        "sample-data/import_history/02_gl_batch_039.xlsx",
    }


def test_expands_two_brace_groups_on_one_line():
    assert declared("a/{x.py,y.py} b/{p.md,q.md}") == {
        "a/x.py", "a/y.py", "b/p.md", "b/q.md"}


def test_expands_before_splitting_so_the_commas_inside_the_braces_do_not_break_it():
    """The regression, kept as a test: the tokeniser splits on `,`, so a brace group
    that reaches the splitter comes out as `{01_bank_batch_037.csv` and then fails the
    existence check in team.py check as a path that does not exist."""
    got = declared("sample-data/import_history/{01_bank_batch_037.csv,02_gl_batch_039.xlsx}")
    assert not any(g.startswith("{") for g in got)
    for g in got:
        assert (ROOT / g).exists(), f"{g} does not exist, so it would FAIL the check"


def test_leaves_a_plain_path_untouched():
    assert team._expand_braces("app/cli/main.py") == ["app/cli/main.py"]


# --------------------------------------------------------------------------- rejected handoffs
def test_handoff_index_and_rejection_detection():
    """A card can be released straight back into `review` with no new handoff, and then
    points at the handoff that was sent back - green over work nobody can accept."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        hd = Path(td) / "handoffs"
        hd.mkdir()
        (hd / "HO-031-ux-08.md").write_text("# HO-031\n\n## Changed\n", encoding="utf-8")
        (hd / "HO-040-ux-08.md").write_text(
            "# HO-040\n\n### Rejected by `buffy`\nRequired before re-handoff:\n",
            encoding="utf-8")
        (hd / "TEMPLATE.md").write_text("# template\n", encoding="utf-8")
        (hd / "HO-041-ux-09.md").write_text("# HO-041\n", encoding="utf-8")

        original = team.HANDOFFS
        team.HANDOFFS = hd
        try:
            idx = team.handoff_index()
            # keyed on the SHORT id, because that is what a task stores in `handoff`
            assert set(idx) == {"HO-031", "HO-040", "HO-041"}
            assert idx["HO-031"] == (31, "ux-08", hd / "HO-031-ux-08.md")
            assert team.rejected_handoffs() == {"HO-040"}
            # and the rule has to fire on the shape it exists for: a card in review
            # whose only handoff was rejected
            hidx, rej = team.handoff_index(), team.rejected_handoffs()
            tid, hid = "UX-08", "HO-040"
            newer = [h for h, (n, suf, _f) in hidx.items()
                     if suf.startswith(tid.lower()) and n > hidx[hid][0] and h not in rej]
            assert hid in rej and not newer
        finally:
            team.HANDOFFS = original
