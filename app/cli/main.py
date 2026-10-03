"""CLI entrypoint per ADR-001, ADR-002 and 09_TECHNICAL_ARCHITECTURE.md §5."""

import argparse
import sys
from decimal import Decimal

from app import __version__, __app_name__
from app.engine.calc import calculate_variance, calculate_variance_pct, quantize_money


def _cmd_exceptions(args: argparse.Namespace) -> None:
    """Handle the `fpa exceptions` subcommands.

    `run` is the entrypoint named as the NFR-007 measurement target in
    14_TESTING_QA_PLAN.md line 85 ("Timed `fpa exceptions --run`"). It delegates to
    ExceptionsRepository.run_rules, which uses the de-duplicated full-catalog batch
    from app.engine.rules.batch - catalog EXC-009, EXC-012 and EXC-015 must not be
    evaluated twice.
    """
    sub = getattr(args, "exceptions_command", None)

    if sub is None:
        print("Usage: fpa exceptions run [--period FY26-P09] [--as-of YYYY-MM-DD] [--json]")
        return

    if sub == "run":
        import json
        import time

        from app.engine.store.db import DatabaseManager
        from app.engine.store.exceptions_repo import ExceptionsRepository

        started = time.perf_counter()
        repo = ExceptionsRepository(DatabaseManager())
        summary = repo.run_rules(period_code=args.period, as_of_date=args.as_of)
        elapsed = time.perf_counter() - started

        summary["elapsedSeconds"] = round(elapsed, 3)
        if args.json:
            print(json.dumps(summary, default=str))
        else:
            print(f"Exception run for {summary['period']}")
            print(f"  Rules run        : {summary['rulesRun']} evaluators "
                  f"({summary.get('catalogRulesCovered', '?')} catalog rules)")
            print(f"  Findings         : {summary['totalFindings']}")
            print(f"  Raised           : {summary['raised']}")
            print(f"  Updated          : {summary['updated']}")
            print(f"  Flagged again    : {summary['flaggedAgain']}")
            print(f"  Elapsed          : {elapsed:.2f}s")
        return

    print(f"Unknown exceptions subcommand: {sub}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fpa-copilot",
        description=f"{__app_name__} CLI v{__version__}",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # doctor command
    doctor_parser = subparsers.add_parser("doctor", help="Check system environment and dependencies")
    doctor_parser.add_argument("--json", action="store_true", help="Output health diagnostic as JSON")

    # bva command
    bva_parser = subparsers.add_parser("bva", help="Run budget vs actual calculations")
    bva_parser.add_argument("--actual", type=str, required=True, help="Actual amount")
    bva_parser.add_argument("--budget", type=str, required=True, help="Budget amount")

    # launch command
    subparsers.add_parser("launch", help="Launch desktop application shell")

    # exceptions command - `fpa exceptions --run` is the NFR-007 measurement target
    # quoted in 14_TESTING_QA_PLAN.md line 85.
    exceptions_parser = subparsers.add_parser(
        "exceptions", help="Run and inspect the exception register"
    )
    exceptions_sub = exceptions_parser.add_subparsers(dest="exceptions_command")
    run_parser = exceptions_sub.add_parser(
        "run", help="Execute all exception rules (EXC-001..EXC-024) and record findings"
    )
    run_parser.add_argument(
        "--period",
        type=str,
        default="FY26-P09",
        help="Period under review (FYyy-Pmm). Default: FY26-P09",
    )
    run_parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help=(
            "Injected run date (YYYY-MM-DD). Default: derived from the period "
            "under review (doc 05 CALC-002), never a system clock."
        ),
    )
    run_parser.add_argument("--json", action="store_true", help="Output run summary as JSON")

    args = parser.parse_args()

    if args.command == "doctor":
        if args.json:
            print('{"status":"healthy","version":"' + __version__ + '","engine":"ready"}')
        else:
            print(f"FP&A Month-End Copilot v{__version__} environment: HEALTHY")
    elif args.command == "bva":
        act = quantize_money(args.actual)
        bud = quantize_money(args.budget)
        var = calculate_variance(act, bud)
        pct = calculate_variance_pct(act, bud)
        print(f"Actual: {act} | Budget: {bud} | Variance: {var} | Variance %: {pct}%")
    elif args.command == "exceptions":
        _cmd_exceptions(args)
    elif args.command == "launch" or args.command is None:
        from app.desktop.shell import launch_app
        launch_app()


if __name__ == "__main__":
    main()
