#!/usr/bin/env python3
"""Open the ``file:line`` citations a report makes and show what is on each line.

Why this exists
---------------
Three audits handed to review this session (HO-031, HO-033, HO-035) each cited
code and each turned out to have measured nothing. The reviewer caught them by
*reading four cited lines by hand*. That is the only machine check in the chain
that worked, so this script is that manual step, repeatable and on demand.

What it does
------------
1. Finds ``file:line`` citations in a report (or in the evidence file a handoff
   points at, via ``--handoff HO-031``).
2. Opens each cited file and prints the line that is actually there.
3. Pulls the *claim tokens* out of the report line that carries the citation --
   backticked ``key="value"`` pairs such as ``role="main"`` -- and reports which
   of them are absent from the cited source line.
4. Exits non-zero when a cited line does not exist, or when the report claims
   something that is not on the line it cites.

The distinction it makes visible: **cited** is a string in a document;
**measured** is a line a human or a machine opened. A report with no code
citations at all has measured nothing, and this command says so by failing.

Stdlib only. No network. Reads files under the repository root.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ``path:line`` or ``path:start-end``. The path must carry a file extension so
# that clock times ("12:30") and section refs ("docs/26_API_CONTRACT.md: §5")
# do not match.
CITE_RE = re.compile(
    r"(?P<path>(?:[A-Za-z]:[\\/])?(?:[\w.\-]+[\\/])+[\w\-]+\.[A-Za-z][\w]{0,7}"
    r"|[\w\-]+\.[A-Za-z][\w]{0,7})"
    r":(?P<start>\d+)(?:-(?P<end>\d+))?"
)

# A backticked span that reads ``key=value`` / ``key="value"`` is a claim about
# the code on the cited line. Backticked ids (``SCR-001``) and backticked paths
# (``main.tsx:145``) carry no "=" and are therefore not claims.
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
CLAIM_RE = re.compile(r"^[A-Za-z][\w.\-]*\s*=\s*\S+$")
FENCE_RE = re.compile(r"^(```+|~~~+)")

SKIP_SCHEMES = ("http://", "https://", "ftp://", "//", "file://")

MAX_LINE = 200
# Plain ASCII markers: this runs on Windows consoles that are not UTF-8.
MARK = ">>"


def strip_code_fences(text: str) -> str:
    """Blank out *balanced* fenced code blocks, preserving line numbering.

    A citation inside a ``` fence is *quoted evidence* - the output of a run, an
    example, a transcript - not a claim the report makes. Without this, a
    document that quotes a citation audit gets audited by its own quote, and
    the tool cannot be written up anywhere. Inline code spans are deliberately
    NOT stripped: a backticked `path:line` in prose or a table is exactly the
    claim this command exists to check.

    Only *balanced* fences are stripped. CommonMark lets an unclosed fence run
    to the end of the document, but applying that here would let one stray
    ``` hide every citation in a file - and a checker that silently stops
    looking is worse than one that looks too hard. An unclosed fence is
    therefore treated as ordinary text.
    """
    lines = text.splitlines()
    out = list(lines)
    fence: str | None = None
    start = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if fence is None:
            m = FENCE_RE.match(stripped)
            if m:
                fence = m.group(1)
                start = i
        elif stripped.startswith(fence):
            for j in range(start, i + 1):
                out[j] = ""
            fence = None
    return "\n".join(out)


def _norm(text: str) -> str:
    """Normalise so ``role='main'``, ``role = "main"`` and ``role="main"`` all compare equal."""
    text = re.sub(r"\s+", " ", text.replace("'", '"'))
    return re.sub(r"\s*=\s*", "=", text).strip()


@dataclass
class Citation:
    """One ``file:line`` citation found in a report."""

    report_line_no: int
    report_line: str
    raw: str
    path: str
    start: int
    end: int | None
    claims: list[str] = field(default_factory=list)
    resolved: Path | None = None
    actual: str | None = None
    missing_claims: list[str] = field(default_factory=list)
    status: str = "OK"
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "OK"


def extract_claims(report_line: str) -> list[str]:
    """Backticked ``key="value"`` spans on the report line, in order, de-duplicated."""
    claims: list[str] = []
    for span in BACKTICK_RE.findall(report_line):
        span = span.strip()
        if CLAIM_RE.match(span) and span not in claims:
            claims.append(span)
    return claims


def find_citations(text: str) -> list[Citation]:
    """Every ``file:line`` citation a report *claims*, in report order.

    Fenced code blocks are skipped: a citation shown inside one is quoted
    output, not a claim.
    """
    out: list[Citation] = []
    for lineno, line in enumerate(strip_code_fences(text).splitlines(), start=1):
        for m in CITE_RE.finditer(line):
            raw = m.group(0)
            # Skip URLs -- the scheme is not a repository path.
            before = line[: m.start()]
            if any(s in before for s in SKIP_SCHEMES):
                continue
            # Skip if the path is glued to a preceding word/scheme (e.g. "xhttp:").
            if before and (before[-1].isalnum() or before[-1] in "/\\"):
                if before[-1] not in "/\\" or before.endswith(("//", "\\")):
                    continue
            path = m.group("path").replace("\\", "/")
            start = int(m.group("start"))
            end = int(m.group("end")) if m.group("end") else None
            out.append(
                Citation(
                    report_line_no=lineno,
                    report_line=line.strip(),
                    raw=raw,
                    path=path,
                    start=start,
                    end=end,
                    claims=extract_claims(line),
                )
            )
    return out


def _candidate_paths(path: str, report_path: Path) -> Iterable[Path]:
    """Where a cited path could live: repo root first, then beside the report."""
    p = Path(path)
    if p.is_absolute():
        yield p
        return
    yield ROOT / p
    yield report_path.parent / p


def resolve(cit: Citation, report_path: Path) -> None:
    """Open the cited file and record what is really on the cited line(s)."""
    for cand in _candidate_paths(cit.path, report_path):
        if cand.is_file():
            cit.resolved = cand
            break
    if cit.resolved is None:
        tried = ", ".join(str(c) for c in _candidate_paths(cit.path, report_path))
        cit.status = "FILE_MISSING"
        cit.note = f"no such file; tried {tried}"
        return

    lines = cit.resolved.read_text(encoding="utf-8", errors="replace").splitlines()
    if cit.start < 1 or cit.start > len(lines):
        cit.status = "LINE_OUT_OF_RANGE"
        cit.note = f"file has {len(lines)} lines; cited line {cit.start}"
        return

    stop = min(cit.end or cit.start, len(lines))
    body = [lines[i - 1] for i in range(cit.start, stop + 1)]
    cit.actual = "\n".join(body).strip()

    if not cit.actual.strip():
        cit.status = "BLANK_LINE"
        cit.note = f"line {cit.start} of {cit.resolved.name} is blank"

    haystack = _norm(cit.actual)
    cit.missing_claims = [c for c in cit.claims if _norm(c) not in haystack]
    if cit.missing_claims:
        cit.status = "MISMATCH"
        cit.note = (
            f"claimed on report line {cit.report_line_no} but not on "
            f"{cit.path}:{cit.start}: " + ", ".join(cit.missing_claims)
        )


def handoff_evidence_paths(handoff_id: str) -> list[Path]:
    """The files a handoff names under ``## Evidence`` and ``## Changed``."""
    matches = sorted((ROOT / "team" / "handoffs").glob(f"{handoff_id}*.md"))
    if not matches:
        raise FileNotFoundError(f"no handoff {handoff_id} in team/handoffs/")
    text = matches[0].read_text(encoding="utf-8")
    paths: list[Path] = []
    for m in re.finditer(r"^\s*[-*]?\s*(?:[\w.\-]+[\\/])+[\w\-]+\.[A-Za-z][\w]*\s*$", text, re.M):
        cand = ROOT / m.group(0).strip()
        if cand.is_file():
            paths.append(cand)
    if not paths:
        raise FileNotFoundError(f"handoff {handoff_id} names no evidence file on disk")
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _clip(text: str) -> str:
    text = text.strip()
    return text if len(text) <= MAX_LINE else text[: MAX_LINE - 1] + "..."


def render(citations: list[Citation], source_label: str, context: int) -> str:
    lines: list[str] = []
    lines.append(f"citation audit of {source_label}")
    lines.append(f"{len(citations)} citation(s) sampled")
    lines.append("")
    for i, c in enumerate(citations, start=1):
        lines.append(f"[{i}] {c.raw}")
        lines.append(f"    report line {c.report_line_no}: {_clip(c.report_line)}")
        lines.append(f"    status: {c.status}")
        if c.note:
            lines.append(f"    why:    {c.note}")
        if c.resolved is not None:
            lines.append(f"    opened: {rel_path(c.resolved)}")
        if c.actual is not None:
            body_lines = c.actual.splitlines()
            for off, body in enumerate(body_lines):
                marker = MARK if off == 0 else "  "
                lines.append(f"    {marker} {rel_path(c.resolved)}:{c.start + off} | {_clip(body)}")
            if context:
                lines.extend(_context_lines(c, context))
        if c.claims:
            lines.append(f"    claims: {', '.join(c.claims)}")
            if c.actual is None:
                # Never print "all present" when nothing was opened.
                lines.append("    absent: not checked — the cited line was never opened")
            else:
                lines.append(
                    "    absent: "
                    + (", ".join(c.missing_claims) if c.missing_claims else "none — all present")
                )
        else:
            lines.append("    claims: none on this line — cited only, nothing checked")
        lines.append("")
    return "\n".join(lines)


def rel_path(p: Path | None) -> str:
    """Repo-relative path, always with forward slashes so output is platform-free."""
    if p is None:
        return "?"
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def _context_lines(c: Citation, context: int) -> list[str]:
    if c.resolved is None:
        return []
    all_lines = c.resolved.read_text(encoding="utf-8", errors="replace").splitlines()
    cited = set(range(c.start, (c.end or c.start) + 1))
    out: list[str] = []
    for n in range(max(1, c.start - context), min(len(all_lines), c.start + context) + 1):
        if n in cited:
            continue
        out.append(f"       {rel_path(c.resolved)}:{n} | {_clip(all_lines[n - 1])}")
    return out


def audit(source: Path, limit: int | None) -> tuple[list[Citation], str]:
    text = source.read_text(encoding="utf-8", errors="replace")
    cites = find_citations(text)
    if limit is not None:
        cites = cites[:limit]
    for c in cites:
        resolve(c, source)
    return cites, rel_path(source)


def _use_utf8() -> None:
    """Windows consoles default to cp1252; report text is UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="open_cited_lines.py",
        description="Open the file:line citations a report makes and show the real line.",
    )
    ap.add_argument("report", nargs="?", help="report .md to audit")
    ap.add_argument("--handoff", help="audit the evidence files named by a handoff id, e.g. HO-031")
    ap.add_argument("--limit", type=int, default=4, help="open at most N citations (default 4; 0 = all)")
    ap.add_argument("--context", type=int, default=0, help="also show N lines either side")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    if not args.report and not args.handoff:
        ap.error("give a report path or --handoff HO-nnn")
    return args


def _collect(args: argparse.Namespace, limit: int | None) -> tuple[list[Citation], list[str]]:
    """Audit every source, or return an exit code of 1/2 via SystemExit-free sentinel."""
    if args.handoff:
        sources = handoff_evidence_paths(args.handoff.upper())
    else:
        sources = [Path(str(args.report))]

    all_cites: list[Citation] = []
    blocks: list[str] = []
    for src in sources:
        if not src.is_file():
            raise FileNotFoundError(f"no such report: {src}")
        cites, label = audit(src, limit)
        if not cites:
            raise ZeroCitations(label)
        all_cites.extend(cites)
        blocks.append(render(cites, label, args.context))
    return all_cites, blocks


class ZeroCitations(Exception):
    """Raised when a report cites no source line at all."""

    def __init__(self, label: str) -> None:
        super().__init__(label)
        self.label = label


def _emit_json(all_cites: list[Citation], checked: int, bad: list[Citation]) -> None:
    print(
        json.dumps(
            {
                "citations": len(all_cites),
                "claim_tokens_checked": checked,
                "failures": len(bad),
                "results": [
                    {
                        "raw": c.raw,
                        "report_line_no": c.report_line_no,
                        "status": c.status,
                        "note": c.note,
                        "actual": c.actual,
                        "claims": c.claims,
                        "missing_claims": c.missing_claims,
                    }
                    for c in all_cites
                ],
            },
            indent=2,
        )
    )


def _verdict(all_cites: list[Citation], checked: int, bad: list[Citation]) -> int:
    if not all_cites or bad:
        if bad:
            print("VERDICT: FAIL — a cited line does not say what the report says it says.")
        return 1
    if checked == 0:
        print("VERDICT: INCONCLUSIVE — every citation resolved, but no line carried a checkable claim.")
        return 1
    print("VERDICT: OK — every sampled citation resolved and every claim token is on its cited line.")
    return 0


def main(argv: list[str] | None = None) -> int:
    _use_utf8()
    args = _parse_args(argv)
    limit = None if args.limit == 0 else args.limit

    try:
        all_cites, blocks = _collect(args, limit)
    except ZeroCitations as exc:
        print(
            f"open_cited_lines: FAIL {exc.label} makes no file:line citation — "
            "nothing in it was measured, only asserted.",
            file=sys.stderr,
        )
        return 1
    except FileNotFoundError as exc:
        print(f"open_cited_lines: {exc}", file=sys.stderr)
        return 2

    bad = [c for c in all_cites if not c.ok]
    checked = sum(len(c.claims) for c in all_cites)

    if args.json:
        _emit_json(all_cites, checked, bad)
        return 1 if bad or checked == 0 else 0

    for b in blocks:
        print(b)
    print(f"{len(all_cites)} citation(s), {checked} claim token(s) checked, {len(bad)} failure(s)")
    return _verdict(all_cites, checked, bad)


if __name__ == "__main__":
    raise SystemExit(main())
