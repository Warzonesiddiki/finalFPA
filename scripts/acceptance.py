"""Planted-exception acceptance CLI - doc 14 §5.2 step 6.

    "Fail the build when a bar in §5.3 is not met. A red acceptance run is a
     release-blocking defect."

EXIT CODES - three distinct outcomes, because "green" and "red" are not the only
possibilities and collapsing BLOCKED into either would be misleading:

    0  PASS     every doc 14 §5.3 bar met on a measurable corpus.
    1  FAIL     the corpus was measurable and a bar was not met.
    2  BLOCKED  the corpus precondition (doc 28 §5.0 criterion 4) is not met, so
               the §5.3 bars could not be measured at all. Never 0, never 1.

Doc 14 §5.2 names this `scripts/acceptance`; this repository names scripts with a
`.py` suffix (`build.py`, `check.py`), so the entry point is `scripts/acceptance.py`.

READ-ONLY with respect to the real project: it builds a throwaway database in a
temporary directory and never opens the live user database.

Usage:
    python scripts/acceptance.py                 # measure and report
    python scripts/acceptance.py --out evidence  # write reports under evidence/
    python scripts/acceptance.py --no-actuals    # skip corpus import (diagnostic)

    On Windows consoles prefer ``set PYTHONUTF8=1`` before running: the report
    embeds the rupee sign (Rs.), which cp1252 cannot encode. Without it the
    script reconfigures stdout/stderr to UTF-8 where possible and falls back to
    backslash-escaped output, so the verdict exit code is never masked by a
    print crash (D-20).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.engine.rules.acceptance import (  # noqa: E402
    DEFAULT_AS_OF,
    DEFAULT_SAMPLE_DIR,
    PERIOD_CODE,
    run_acceptance,
    write_reports,
)

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_BLOCKED = 2


def ensure_utf8_console() -> None:
    """D-20: make console output UTF-8-safe on Windows (cp1252) consoles.

    The acceptance markdown embeds the rupee sign (U+20B9, from the answer-key
    notes and rule details), which cp1252 cannot encode. A bare ``print`` then
    raises ``UnicodeEncodeError`` and the process exits 1, masking the designed
    verdict exit code (0 PASS / 1 FAIL / 2 BLOCKED). Prefer ``PYTHONUTF8=1``;
    where the stream supports it, reconfigure stdout/stderr to UTF-8 so the
    report prints intact. Never raises: a console fix must not change the exit
    code by itself.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
            if encoding not in ("utf8", "utf8sig"):
                reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            continue
    try:
        encoding = (getattr(sys.stdout, "encoding", "") or "").lower().replace("-", "")
        if encoding not in ("utf8", "utf8sig") and os.environ.get("PYTHONUTF8") != "1":
            sys.stderr.write(
                "hint: console encoding is "
                f"{getattr(sys.stdout, 'encoding', '?')}; "
                "set PYTHONUTF8=1 for intact rupee-sign (Rs.) output "
                "(unrepresentable glyphs fall back to backslash escapes).\n"
            )
    except Exception:
        pass


def safe_print(text: str = "", *, end: str = "\n") -> None:
    """Print without ever raising ``UnicodeEncodeError`` (D-20).

    Normal path is a plain ``print``. On a non-UTF-8 console the rupee sign
    raises; the fallback writes backslash-escaped bytes to ``stdout.buffer``
    so the CLI still exits with its verdict code (never 1-by-crash).
    """
    try:
        print(text, end=end)
    except UnicodeEncodeError:
        try:
            data = str(text).encode(
                getattr(sys.stdout, "encoding", None) or "cp1252",
                errors="backslashreplace",
            ) + end.encode("ascii", errors="replace")
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        except Exception:
            try:
                sys.stderr.write("[output suppressed: unencodable console]\n")
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(
        description="Doc 14 §5.2 planted-exception acceptance. Exits 0 on PASS, "
        "1 on FAIL, 2 when the corpus precondition blocks measurement."
    )
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=DEFAULT_SAMPLE_DIR,
        help="Corpus directory (default: sample-data)",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="Directory for acceptance_report.{json,md}"
    )
    parser.add_argument(
        "--as-of",
        default=DEFAULT_AS_OF,
        help=f"Injected run date (default: {DEFAULT_AS_OF}). No clock is read.",
    )
    parser.add_argument(
        "--period", default=PERIOD_CODE, help=f"Period under review (default: {PERIOD_CODE})"
    )
    parser.add_argument(
        "--no-actuals", action="store_true", help="Do not import actuals; diagnostics only."
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress the markdown report on stdout."
    )
    args = parser.parse_args(argv)

    report = run_acceptance(
        sample_dir=args.sample_dir,
        period=args.period,
        as_of=args.as_of,
        load_actuals=not args.no_actuals,
    )

    if args.out is not None:
        json_path, md_path = write_reports(report, args.out)
        safe_print(f"wrote {json_path}")
        safe_print(f"wrote {md_path}")

    if not args.quiet:
        from app.engine.rules.acceptance import render_markdown

        safe_print(render_markdown(report))

    safe_print(f"ACCEPTANCE: {report.verdict}")
    if report.blocked_reasons:
        safe_print(f"BARS NOT MEASURED (corpus precondition): {len(report.blocked_reasons)}")
        for reason in report.blocked_reasons:
            safe_print(f"  - {reason}")
    if report.hard_failures:
        safe_print(f"hard failures: {len(report.hard_failures)}")
    failed = [b.name for b in report.bars if b.measurable and not b.passed]
    if failed:
        safe_print(f"failed bars: {failed}")

    if report.verdict == "BLOCKED":
        return EXIT_BLOCKED
    # Doc 14 §5.2 step 6: fail the build. Never 0 on a red run.
    return EXIT_PASS if report.passed else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
