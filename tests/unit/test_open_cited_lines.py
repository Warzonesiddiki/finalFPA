"""Tests for the citation opener (scripts/open_cited_lines.py).

The command exists because three audits cited code and measured nothing, and the
only thing that caught them was a human opening four cited lines by hand. So the
tests come in two halves:

* **behaviour** - citations are found, the cited line is opened, claims are
  compared against what is really there;
* **falsification** - a report that currently *passes* fails the moment its
  cited source line stops saying what the report claims. A checker that cannot
  fail is a claim, not a checker (KNOWLEDGE.md, K-0004), so `test_passing_report
  _fails_when_the_cited_line_changes` is the test that matters most: it is the
  rejection of HO-031 turned into an assertion.

Both directions are covered on purpose: `test_honest_control_passes` fails if
the command ever starts failing everything, which is the other way a gate rots.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import open_cited_lines as ocl  # noqa: E402

REAL_ROOT = ocl.ROOT


@pytest.fixture()
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A throwaway repo. Repointing ROOT keeps every test off the real sources."""
    monkeypatch.setattr(ocl, "ROOT", tmp_path)
    (tmp_path / "ui" / "src").mkdir(parents=True)
    (tmp_path / "team" / "handoffs").mkdir(parents=True)
    return tmp_path


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = ocl.main(list(argv))
    return code, out.getvalue(), err.getvalue()


# ------------------------------------------------------------------- extraction
def test_finds_file_line_citations(tree: Path):
    write(tree / "ui/src/main.tsx", "line1\nline2\nline3\n")
    rep = write(
        tree / "report.md",
        '| a | `role="main"` | `ui/src/main.tsx:2` |\n'
        '| b | `role="dialog"` | `ui/src/main.tsx:3` |\n',
    )
    cites = ocl.find_citations(rep.read_text(encoding="utf-8"))
    assert [c.path for c in cites] == ["ui/src/main.tsx", "ui/src/main.tsx"]
    assert [c.start for c in cites] == [2, 3]
    assert cites[0].report_line_no == 1


def test_default_limit_is_four(tree: Path):
    write(tree / "ui/src/main.tsx", "\n".join(f"l{i}" for i in range(1, 30)))
    body = "".join(f"row {i} `ui/src/main.tsx:{i}`\n" for i in range(1, 11))
    rep = write(tree / "report.md", body)
    cites, _ = ocl.audit(rep, limit=4)
    assert len(cites) == 4


def test_limit_zero_means_all(tree: Path):
    write(tree / "ui/src/main.tsx", "\n".join(f"l{i}" for i in range(1, 30)))
    rep = write(tree / "report.md", "".join(f"r{i} `ui/src/main.tsx:{i}`\n" for i in range(1, 11)))
    cites, _ = ocl.audit(rep, limit=None)
    assert len(cites) == 10


def test_range_citation_reads_every_line(tree: Path):
    write(tree / "ui/src/main.tsx", "a\nb\nc\nd\ne\n")
    rep = write(tree / "report.md", "claim `ui/src/main.tsx:2-4`\n")
    cites, _ = ocl.audit(rep, limit=None)
    assert cites[0].actual == "b\nc\nd"


def test_urls_are_not_citations(tree: Path):
    rep = write(tree / "report.md", "see https://registry.npmjs.org/x:443 and //cdn/y:12\n")
    assert ocl.find_citations(rep.read_text(encoding="utf-8")) == []


def test_section_refs_are_not_citations(tree: Path):
    rep = write(tree / "report.md", "docs/26_API_CONTRACT.md: §5 error catalogue\n")
    assert ocl.find_citations(rep.read_text(encoding="utf-8")) == []


def test_only_key_value_backticks_become_claims(tree: Path):
    line = '| `SCR-001` | `Escape` | `ui/src/main.tsx:1` | `aria-label="Home"` |'
    assert ocl.extract_claims(line) == ['aria-label="Home"']


def test_fenced_citations_are_quoted_output_not_claims(tree: Path):
    """A report must be able to quote a citation audit inside itself.

    Found the hard way: the LEAD-03 write-up embeds the command's own output and
    the command failed on its own quotes. Quoted output is not a claim.
    """
    text = "cited: `ui/src/main.tsx:2`\n```\n>> ui/src/main.tsx:9 | fabricated\n```\n"
    cites = ocl.find_citations(text)
    assert [c.start for c in cites] == [2]


def test_fence_stripping_preserves_line_numbers(tree: Path):
    text = "one\n```\nfenced\n```\ntwo `ui/src/main.tsx:5`\n"
    cites = ocl.find_citations(text)
    assert cites[0].report_line_no == 5, "reported line numbers must survive fence stripping"


def test_tilde_fences_are_stripped(tree: Path):
    text = "~~~\nquoted `ui/src/main.tsx:3`\n~~~\n"
    assert ocl.find_citations(text) == []


def test_unclosed_fence_does_not_swallow_the_document(tree: Path):
    """One stray ``` must not hide every citation after it.

    CommonMark runs an unclosed fence to end of document. Doing that here would
    let a typo silence the checker on a real report - the one failure mode a
    verification tool must not have.
    """
    text = "real `ui/src/main.tsx:1`\n```\nstray fence\nalso real `ui/src/main.tsx:3`\n"
    assert [c.start for c in ocl.find_citations(text)] == [1, 3]


def test_a_document_quoting_the_audit_passes(tree: Path):
    """End to end: prose citation true, fenced false, run is green."""
    write(tree / "ui/src/main.tsx", "x\nLOCK_TIMEOUT = 60.0\n")
    rep = write(
        tree / "report.md",
        "The constant is `LOCK_TIMEOUT=60.0` at `scripts/m.py:2`.\n"
        "Previously it was wrong:\n"
        "```\n"
        "    >> scripts/m.py:2 | LOCK_TIMEOUT = 999\n"
        "    status: MISMATCH\n"
        "```\n",
    )
    write(tree / "scripts/m.py", "x\nLOCK_TIMEOUT = 60.0\n")
    code, out, _ = run(str(rep))
    assert code == 0, out


# ------------------------------------------------------------------- resolution
def test_match_passes(tree: Path):
    write(tree / "ui/src/main.tsx", 'x\n<main role="main">\ny\n')
    rep = write(tree / "report.md", 'row `role="main"` at `ui/src/main.tsx:2`\n')
    code, out, _ = run(str(rep))
    assert code == 0
    assert "VERDICT: OK" in out


def test_mismatch_detected(tree: Path):
    write(tree / "ui/src/main.tsx", 'x\nconst [a, b] = useState("")\ny\n')
    rep = write(tree / "report.md", 'row `role="main"` at `ui/src/main.tsx:2`\n')
    code, out, _ = run(str(rep))
    assert code == 1
    assert "MISMATCH" in out
    assert 'role="main"' in out


def test_file_missing_status(tree: Path):
    rep = write(tree / "report.md", "row `ui/src/nope.tsx:1`\n")
    code, out, _ = run(str(rep))
    assert code == 1
    assert "FILE_MISSING" in out
    assert "all present" not in out, "a line that was never opened cannot be 'all present'"


def test_unopened_line_never_reports_all_present(tree: Path):
    """The false-green guard: absence of evidence must not read as evidence."""
    rep = write(tree / "report.md", 'row `role="main"` at `ui/src/nope.tsx:1`\n')
    code, out, _ = run(str(rep))
    assert code == 1
    assert "all present" not in out
    assert "never opened" in out


def test_line_out_of_range_status(tree: Path):
    write(tree / "ui/src/main.tsx", "only\none\n")
    rep = write(tree / "report.md", "row `ui/src/main.tsx:99`\n")
    code, out, _ = run(str(rep))
    assert code == 1
    assert "LINE_OUT_OF_RANGE" in out


def test_blank_line_status(tree: Path):
    write(tree / "ui/src/main.tsx", "a\n\nb\n")
    rep = write(tree / "report.md", "row `ui/src/main.tsx:2`\n")
    code, out, _ = run(str(rep))
    assert code == 1
    assert "BLANK_LINE" in out


def test_report_with_no_citations_fails(tree: Path):
    rep = write(tree / "report.md", "# All twelve numbers verified.\n\nNothing cited.\n")
    code, _, err = run(str(rep))
    assert code == 1
    assert "nothing in it was measured" in err


def test_missing_report_exits_two(tree: Path):
    code, _, err = run(str(tree / "absent.md"))
    assert code == 2
    assert "no such report" in err


def test_prints_the_real_line(tree: Path):
    write(tree / "ui/src/main.tsx", "x\nTHE ACTUAL SOURCE TEXT\n")
    rep = write(tree / "report.md", "row `ui/src/main.tsx:2`\n")
    _, out, _ = run(str(rep))
    assert "THE ACTUAL SOURCE TEXT" in out


def test_context_lines_shown(tree: Path):
    write(tree / "ui/src/main.tsx", "one\ntwo\nthree\nfour\n")
    rep = write(tree / "report.md", "row `ui/src/main.tsx:3`\n")
    _, out, _ = run(str(rep), "--context", "1")
    assert "two" in out and "four" in out


# ------------------------------------------------------------- normalisation
@pytest.mark.parametrize(
    "source,claim",
    [
        ('<main role="main">', 'role="main"'),
        ("<main role='main'>", 'role="main"'),
        ("MARK = 1", "MARK=1"),
        ("MARK=1", "MARK = 1"),
    ],
)
def test_quote_and_spacing_normalisation(tree: Path, source: str, claim: str):
    write(tree / "ui/src/main.tsx", f"x\n{source}\n")
    rep = write(tree / "report.md", f"row `{claim}` at `ui/src/main.tsx:2`\n")
    code, _, _ = run(str(rep))
    assert code == 0, f"{source!r} should satisfy claim {claim!r}"


# ------------------------------------------------------------------- handoff
def test_handoff_mode_resolves_evidence_file(tree: Path):
    write(tree / "ui/src/main.tsx", 'x\nrole="main"\n')
    ev = write(tree / "evidence/ux/a11y.md", 'row `role="main"` at `ui/src/main.tsx:2`\n')
    write(
        tree / "team/handoffs/HO-099-ux-99.md",
        f"# HO-099\n\n## Evidence\n{ev.relative_to(tree).as_posix()}\n",
    )
    code, out, _ = run("--handoff", "HO-099")
    assert code == 0
    assert "a11y.md" in out


def test_unknown_handoff_exits_two(tree: Path):
    code, _, err = run("--handoff", "HO-000")
    assert code == 2
    assert "no handoff" in err


# ---------------------------------------------------------------------- output
def test_json_output_is_valid_and_consistent(tree: Path):
    write(tree / "ui/src/main.tsx", 'x\nrole="main"\ny\nconst a = 1\n')
    rep = write(
        tree / "report.md",
        'good `role="main"` at `ui/src/main.tsx:2`\nbad `role="dialog"` at `ui/src/main.tsx:4`\n',
    )
    code, out, _ = run(str(rep), "--json")
    payload = json.loads(out)
    assert code == 1
    assert payload["citations"] == 2
    assert payload["failures"] == 1
    assert payload["results"][0]["status"] == "OK"
    assert payload["results"][1]["missing_claims"] == ['role="dialog"']


def test_cited_but_nothing_checked_is_not_a_pass(tree: Path):
    write(tree / "ui/src/main.tsx", "x\nconst a = 1\n")
    rep = write(tree / "report.md", "row `SCR-001` at `ui/src/main.tsx:2`\n")
    code, out, _ = run(str(rep))
    assert code == 1
    assert "INCONCLUSIVE" in out
    assert "cited only, nothing checked" in out


# -------------------------------------------------------------- falsification
def test_passing_report_fails_when_the_cited_line_changes(tree: Path):
    """The rejection of HO-031 as an assertion.

    A report that passes must stop passing when the line it cites stops saying
    what it claims. If this test ever needs changing to stay green, the checker
    has been weakened.
    """
    write(tree / "ui/src/main.tsx", 'x\n<div role="main">\ny\n')
    rep = write(tree / "report.md", 'row `role="main"` at `ui/src/main.tsx:2`\n')

    code, _, _ = run(str(rep))
    assert code == 0, "fixture must start green, or it proves nothing"

    # The claim is still true, just three lines further down. The citation is now wrong.
    write(tree / "ui/src/main.tsx", 'x\n<div className="x">\ny\n<div role="main">\n')
    code, out, _ = run(str(rep))
    assert code == 1, "report must fail once the cited line no longer carries the claim"
    assert 'role="main"' in out


def test_honest_control_passes(tree: Path):
    """The other direction: the gate must be able to return green.

    Guards against the failure mode where a checker is tightened until every
    report fails, which looks strict and measures nothing.
    """
    write(tree / "ui/src/main.tsx", 'x\nrole="main"\ny\n')
    rep = write(tree / "report.md", 'row `role="main"` at `ui/src/main.tsx:2`\n')
    code, out, _ = run(str(rep))
    assert code == 0
    assert "VERDICT: OK" in out


def test_shipped_fixtures_agree_with_their_names():
    """evidence/ops/ ships one false fixture and one true fixture.

    Guards the fixtures themselves: if someone 'fixes' the fabricated one to
    make a demo look better, the demo is lying again. Deliberately does NOT use
    the ``tree`` fixture - these reports cite repo-relative paths, so they must
    resolve against the real root.
    """
    false_fixture = ROOT / "evidence/ops/lead-03-control-fixture.md"
    true_fixture = ROOT / "evidence/ops/lead-03-honest-control.md"
    if not (false_fixture.exists() and true_fixture.exists()):
        pytest.skip("fixtures not present in this checkout")
    monkey = pytest.MonkeyPatch()
    try:
        monkey.setattr(ocl, "ROOT", ROOT)
        assert ocl.main([str(false_fixture), "--limit", "0"]) == 1
        assert ocl.main([str(true_fixture), "--limit", "0"]) == 0
    finally:
        monkey.undo()


def test_real_root_is_restored():
    assert ocl.ROOT == REAL_ROOT
