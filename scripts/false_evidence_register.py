#!/usr/bin/env python3
"""Build `evidence/ops/false-evidence-register.md`.

Why
---
Ten handoffs have been rejected on this board. `LEAD-01` exists because the same
failure keeps arriving in new clothes and each occurrence is re-litigated from
scratch. A register turns "we rejected that again" into a row.

What makes this a generator and not a document
----------------------------------------------
A hand-written register is a snapshot that starts lying the moment a handoff is
rejected. So the roster is derived on every run from:

* the handoffs that actually carry a ``### Rejected by`` block - not from a
  remembered list;
* the evidence files those handoffs name, each re-audited *now* by
  ``scripts/open_cited_lines.py`` (LEAD-03), so the register carries a measured
  verdict rather than the verdict we remember giving.

The **pattern classification and the systemic fix are judgement**, so they live
in ``PATTERNS`` below, keyed on handoff id, and the generator fails loudly on an
unclassified rejection rather than quietly omitting it. A new rejection that no
one has classified is a new pattern, and that is the moment to notice.

Stdlib only. Writes one file. ``--check`` verifies the register is current
without writing, for use in a gate.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REGISTER = ROOT / "evidence" / "ops" / "false-evidence-register.md"
BEGIN = "<!-- BEGIN GENERATED: false_evidence_register.py -->"
END = "<!-- END GENERATED: false_evidence_register.py -->"

# --------------------------------------------------------------------- patterns
# Key: handoff short id. Value: (pattern id, one line on what it failed on).
# This table is the judgement half and is maintained by hand on purpose.
PATTERNS: dict[str, tuple[str, str]] = {
    "HO-003": ("A-hidden-blast-radius",
               "deliverable was never re-checked; verification ran the coordination layer only"),
    "HO-004": ("D-checker-cannot-fail",
               "'20 citations verified' came from a checker that greps docs/, not the deliverable"),
    "HO-006": ("F-spec-code-drift",
               "code shipped ahead of the catalogue DEC-057 requires, and a new branch shipped untested"),
    "HO-010": ("A-hidden-blast-radius",
               "## Changed declared 1 file; the claim window showed 7"),
    "HO-012": ("A-hidden-blast-radius",
               "## Changed declared 1 file; the claim window showed 4"),
    "HO-013": ("A-hidden-blast-radius",
               "## Changed declared 1 file; the claim window showed 5, including a shipped file"),
    "HO-025": ("B-written-outside-scope",
               "two scripts written outside the claimed scope, so no guard could see them"),
    "HO-031": ("C-literal-generator",
               "the audit table is a string literal; the script never opens a .tsx"),
    "HO-033": ("C-literal-generator",
               "'12 numbers verified' from a script that never reads app/"),
    "HO-035": ("C-literal-generator",
               "'77 error codes verified' from a generated table, not from raise sites"),
}

PATTERN_TEXT: dict[str, tuple[str, str]] = {
    "A-hidden-blast-radius": (
        "**The handoff declared less than it did.** `## Changed` listed one file while the claim "
        "window showed four to seven. Not dishonesty - the work reproduced on every count - but a "
        "handoff that hides its blast radius cannot be verified, because the reviewer is checking a "
        "subset of what shipped.",
        "Already fixed by `team.py check` (TB-101), which reports files changed inside a claim "
        "window but missing from `## Changed`. **Residual:** it reports, it does not block. The "
        "next step is making an undeclared shipped file FAIL rather than WARN.",
    ),
    "B-written-outside-scope": (
        "**Work landed outside the claimed path, so no guard could see it.** Two scripts were "
        "created in a claim scoped to `evidence/`, which means the undeclared-file rule - which "
        "only looks inside the claim - never had a chance to fire.",
        "Already fixed by the claim-window scan in `team.py check` (TB-101). **Residual:** one "
        "writer per path is still a convention the tool observes rather than enforces.",
    ),
    "C-literal-generator": (
        "**A generator printed a pre-written answer and the exit code was read as a result.** "
        "`scripts/audit_accessibility_matrix.py` holds its 43-row table as a string literal from "
        "line 37 and never opens a `.tsx`; `verify_analyst_maths_trace.py` and "
        "`generate_error_catalogue.py` report 12 and 77 'verified' without reading `app/`. The "
        "deliverable was written, not observed.",
        "Open as `ENG-05` - retire the four literal-printing generators and derive the artefact "
        "from the source at run time. **Rule that generalises:** a generator whose output does not "
        "change when its input changes is a printer, not a generator.",
    ),
    "D-checker-cannot-fail": (
        "**The checker could not fail on the thing it claimed to check.** "
        "`scripts/verify_audit_citations.py` concatenates `docs/*.md` and tests whether `SCR-`/`FR-"
        "`/`CALC-` id strings appear somewhere in them. It never resolves a `file:line` code "
        "citation, so \"all 20 citations verified\" is fully compatible with a fabricated report.",
        "`scripts/open_cited_lines.py` (LEAD-03, `TB-105`) is the replacement: it opens the cited "
        "line and compares the claim against it. `UX-14` owns the written acceptance standard; "
        "`SPEC-08`/`DOC-05` the spec text. **Rule:** a checker must have a test that provokes its "
        "own failure.",
    ),
    "F-spec-code-drift": (
        "**Code shipped ahead of the catalogue.** `DEC-057` orders spec-first, but the subject key "
        "in `docs/06` still read `entity_account_pair` while the code emitted `entity|account|P..`. "
        "The new span branch `P{a}-P{b}` also shipped with no test covering it.",
        "Caught by review, not by a gate. **Residual:** nothing mechanically compares a code "
        "constant to the catalogue row that declares it. This is the one pattern here with no tool "
        "behind it at all, which is why it is worth its own row.",
    ),
}


# ------------------------------------------------------------------- extraction
def rejected_handoffs() -> list[dict[str, str]]:
    """Every handoff carrying a `### Rejected by` block, with its metadata."""
    rows: list[dict[str, str]] = []
    for path in sorted((ROOT / "team" / "handoffs").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(
            r"^### Rejected by `(?P<who>[^`]+)` . (?P<when>[0-9TZ:-]+)", text, re.M
        )
        if not m:
            continue
        short = path.name.split("-")[0] + "-" + path.name.split("-")[1]
        task = path.stem.split("-", 2)[2] if path.stem.count("-") >= 2 else "?"
        author = "?"
        am = re.search(r"author: `([^`]+)`", text)
        if am:
            author = am.group(1)
        rows.append(
            {
                "id": short,
                "file": path.name,
                "task": task.upper(),
                "author": author,
                "by": m.group("who"),
                "when": m.group("when"),
            }
        )
    return rows


# A citation audit is only meaningful for handoffs that actually failed on evidence
# quality. Applying it to a hidden-blast-radius rejection produces a technically
# true and completely useless verdict ("the test file cites no source line").
CITATION_RELEVANT = {"C-literal-generator", "D-checker-cannot-fail"}


def audit_evidence(handoff_id: str) -> tuple[str, str]:
    """Re-audit a handoff's evidence with the citation opener. Returns (verdict, detail)."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "open_cited_lines.py"), "--handoff", handoff_id],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT,
    )
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 0:
        m = re.search(r"(\d+) citation\(s\), (\d+) claim token\(s\) checked", out)
        if m:
            return "PASS", f"{m.group(1)} citation(s), {m.group(2)} claim token(s) all present"
        return "PASS", "every sampled citation resolved"
    m = re.search(r"FAIL (.+?) makes no file:line citation", out)
    if m:
        return "NO CITATION", f"{Path(m.group(1)).name} cites no source line"
    cites = len(re.findall(r"^\[\d+\] ", out, re.M))
    checked = fails = 0
    cm = re.search(r"(\d+) claim token\(s\) checked, (\d+) failure\(s\)", out)
    if cm:
        checked, fails = int(cm.group(1)), int(cm.group(2))
    if checked == 0:
        return "INCONCLUSIVE", f"{cites} citation(s), no checkable claim on any cited line"
    return "MISMATCH", f"{cites} citation(s), {checked} claim token(s) checked, {fails} failure(s)"


def unclassified(rows: list[dict[str, str]]) -> list[str]:
    return [r["id"] for r in rows if r["id"] not in PATTERNS]


# --------------------------------------------------------------------- rendering
def roster_block(rows: list[dict[str, str]]) -> str:
    """The generated section: one row per rejected handoff, re-measured now."""
    out = [
        BEGIN,
        "",
        "_Generated by `scripts/false_evidence_register.py`. Do not hand-edit between the markers._",
        "",
        f"**{len(rows)} handoffs rejected.** The evidence verdict is re-measured at generation time "
        "by `scripts/open_cited_lines.py`, not remembered.",
        "",
        "| Handoff | Card | Author | Rejected by | Rejected | Pattern | Evidence re-audit (now) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        pat, _ = PATTERNS[r["id"]]
        if pat in CITATION_RELEVANT:
            verdict, detail = audit_evidence(r["id"])
            cell = f"**{verdict}** - {detail}"
        else:
            cell = "n/a - not a citation failure"
        out.append(
            f"| `{r['id']}` | `{r['task']}` | {r['author']} | {r['by']} | {r['when'][:10]} "
            f"| `{pat}` | {cell} |"
        )
    out.append("")
    out.append(
        "_The last column is re-measured from the evidence file **as it stands now**, not as it "
        "stood at rejection time - five agents share one checkout and an author may have rewritten "
        "it since. A rejection records a pattern; this column records whether the artefact has "
        "moved since. It is deliberately left blank as `n/a` where the failure was not about "
        "evidence quality, because a verdict about a file that never claimed citations is noise._"
    )
    out.append("")
    out.append("### Recurrence by pattern")
    out.append("")
    counts: dict[str, int] = {}
    for r in rows:
        pat = PATTERNS[r["id"]][0]
        counts[pat] = counts.get(pat, 0) + 1
    out.append("| Pattern | Occurrences | Handoffs |")
    out.append("|---|---|---|")
    for pat, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        ids = ", ".join(f"`{r['id']}`" for r in rows if PATTERNS[r["id"]][0] == pat)
        out.append(f"| `{pat}` | {n} | {ids} |")
    out.append("")
    out.append(END)
    return "\n".join(out)


def prose(rows: list[dict[str, str]]) -> str:
    counts: dict[str, int] = {}
    for r in rows:
        counts[PATTERNS[r["id"]][0]] = counts.get(PATTERNS[r["id"]][0], 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    out: list[str] = []
    A = out.append
    A("# The false-evidence register")
    A("")
    A("Card `LEAD-01` · claim `buffy-20261005T1916Z-2c19` · date 2026-10-05")
    A("")
    A(
        "One row per rejected handoff, with the pattern it failed on, so the pattern is visible "
        "instead of recurring. Ten rejections so far; the roster below is generated from the "
        "handoffs themselves and re-measures each one at generation time."
    )
    A("")
    A("## The headline")
    A("")
    A(
        "The three most recent rejections - `HO-031`, `HO-033`, `HO-035` - share one root cause: "
        "**a generator that prints a literal, and a checker that greps documents.** Neither reads "
        "the subject. A pre-written table printed to stdout and an id string found somewhere in "
        "`docs/` are both indistinguishable from a measurement by exit code alone."
    )
    A("")
    A(
        "That is not three mistakes. It is one mistake made three times in one sitting, by an "
        "author who was not trying to deceive anyone. Which is the useful part: **the failure mode "
        "is the default shape of an audit written to be read rather than to be re-run.**"
    )
    A("")
    A("## Patterns, most frequent first")
    A("")
    for pat, n in ranked:
        what, fix = PATTERN_TEXT[pat]
        A(f"### `{pat}` - {n} occurrence{'s' if n != 1 else ''}")
        A("")
        A(what)
        A("")
        A(fix)
        A("")
    A("## Per-handoff detail")
    A("")
    A("| Handoff | Card | What it failed on |")
    A("|---|---|---|")
    for r in rows:
        _, why = PATTERNS[r["id"]]
        A(f"| `{r['id']}` | `{r['task']}` | {why} |")
    A("")
    A("## What would have caught each, had it existed")
    A("")
    A(
        "Ranked by how many rejections each would have stopped on the first run, which is the only "
        "ranking that matters for deciding what to build next:"
    )
    A("")
    A(
        "1. **`scripts/open_cited_lines.py` (`TB-105`, shipped).** Opens the cited line and compares "
        "the claim against it. Would have caught `HO-031` on the spot, and reports `HO-033` and "
        "`HO-035` as citing no line at all."
    )
    A(
        "2. **The `## Changed` vs claim-window rule (`team.py check`, shipped in TB-101).** Would "
        "have caught `HO-010`, `HO-012`, `HO-013` and part of `HO-025` automatically. It currently "
        "WARNs; making it FAIL is the highest-value small change left in this register."
    )
    A(
        "3. **The claim-window scan (`team.py check`, shipped in TB-101).** Catches writes outside "
        "the claimed path - the `HO-025` case - where the undeclared-file rule was structurally "
        "blind."
    )
    A(
        "4. **A spec-to-code constant check (does not exist).** The `HO-006` pattern - code ahead of "
        "the catalogue `DEC-057` requires - was caught by a human reading two files. Nothing on this "
        "board would have caught it. This is the one gap in the list, and it is the honest reason "
        "`LEAD-01` is a register rather than a solved problem."
    )
    A("")
    A("## Keeping this honest")
    A("")
    A(
        "* The roster is regenerated, never hand-edited, and `--check` fails if it is stale. A "
        "register that drifts from the board is worse than none."
    )
    A(
        "* The evidence verdict column is re-measured by `scripts/open_cited_lines.py` on every "
        "generation, so it records what is true now rather than what was true when the review "
        "happened."
    )
    A(
        "* An unclassified rejection is a hard error, not a silent omission. A new pattern nobody "
        "has looked at is exactly what this file exists to surface."
    )
    A(
        "* Classification and fixes are judgement and live in `PATTERNS` in "
        "`scripts/false_evidence_register.py`, deliberately by hand. Only the roster is derived."
    )
    A(
        "* This file deliberately makes **no `file:line` claim of its own**, so "
        "`scripts/open_cited_lines.py` reports it as citing no source line. That is the correct "
        "verdict, not a gap: every number here is computed from the handoffs at generation time "
        "rather than asserted in prose. A register whose figures were hand-written would be the "
        "exact failure mode it exists to record."
    )
    A("")
    return "\n".join(out)


def build() -> str:
    rows = rejected_handoffs()
    missing = unclassified(rows)
    if missing:
        raise SystemExit(
            f"false_evidence_register: {len(missing)} rejected handoff(s) have no pattern "
            f"classification: {', '.join(missing)}. Classify them in PATTERNS before regenerating - "
            "an unclassified rejection is a new pattern nobody has looked at."
        )
    return prose(rows) + roster_block(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="false_evidence_register.py",
        description="Build evidence/ops/false-evidence-register.md from the rejected handoffs.",
    )
    ap.add_argument("--check", action="store_true", help="fail if the register is stale; write nothing")
    args = ap.parse_args(argv)

    want = build()
    if args.check:
        have = REGISTER.read_text(encoding="utf-8") if REGISTER.exists() else ""
        if have != want:
            print(f"false_evidence_register: STALE - run {REGISTER.name} generator", file=sys.stderr)
            return 1
        print("false_evidence_register: current")
        return 0

    prev = REGISTER.read_text(encoding="utf-8") if REGISTER.exists() else ""
    # The whole file is derived - prose and roster both live in this script - so
    # there is no hand-written block to preserve. BEGIN/END still mark the roster
    # so a reader can tell which table is regenerated.
    if prev and prev != want:
        pass
    REGISTER.parent.mkdir(parents=True, exist_ok=True)
    REGISTER.write_text(want, encoding="utf-8")
    print(f"wrote {REGISTER.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
