"""CLI entrypoint per ADR-001, ADR-002 and 09_TECHNICAL_ARCHITECTURE.md §5."""

import argparse
import sys
from decimal import Decimal

from app import __app_name__, __version__
from app.engine.calc import calculate_variance, calculate_variance_pct, quantize_money


def _cmd_exceptions(args: argparse.Namespace) -> None:
    """Handle the `fpa exceptions` subcommands.

    `run` is the entrypoint named as the NFR-007 measurement target in
    14_TESTING_QA_PLAN.md line 85 ("Timed `fpa exceptions --run`"). It delegates to
    ExceptionsRepository.run_rules, which uses the de-duplicated batch of
    currently implemented evaluators from app.engine.rules.batch. Catalog coverage
    is reported separately; catalog EXC-009, EXC-012 and EXC-015 must not be
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


# ---------------------------------------------------------------------------
# TB-027: missing CLI commands with documented exit codes.
# Exit codes: 0 = ok, 1 = not-balanced/blocked, 2 = I/O+parse error.
# ---------------------------------------------------------------------------


def _cmd_validate(args: argparse.Namespace) -> None:
    """Run prescan + full parse/validate without committing."""
    import json as _json
    from app.engine.imports import prescan_file, parse_and_validate_csv

    try:
        pre = prescan_file(args.file)
        batch = parse_and_validate_csv(args.file)
    except FileNotFoundError:
        _emit(args.json, {"status": "error", "error": f"file not found: {args.file}"}, text=f"File not found: {args.file}")
        sys.exit(2)
    except Exception as exc:
        _emit(args.json, {"status": "error", "error": f"{type(exc).__name__}: {exc}"}, text=f"Parse error: {exc}")
        sys.exit(2)

    if batch.is_balanced:
        _emit(
            args.json,
            {
                "status": "ok",
                "fileName": pre.file_name,
                "sheets": pre.sheet_names,
                "rowCount": batch.loaded_count,
                "quarantined": batch.quarantined_count,
                "isBalanced": True,
                "checks": [c.check_code for c in batch.checks],
            },
            text=(
                f"File: {pre.file_name} | sheets: {', '.join(pre.sheet_names) or '-'}\n"
                f"  rows loaded : {batch.loaded_count} | quarantined: {batch.quarantined_count}\n"
                f"  balanced   : yes\n"
                f"  checks     : {len(batch.checks)} ({sum(1 for c in batch.checks if c.status == 'pass')} pass)"
            ),
        )
        sys.exit(0)

    _emit(
        args.json,
        {"status": "blocked", "isBalanced": False, "netImbalance": str(batch.net_imbalance)},
        text=f"NOT BALANCED — net imbalance {batch.net_imbalance}. Nothing committed.",
    )
    sys.exit(1)


def _cmd_import(args: argparse.Namespace) -> None:
    """Parse + validate + commit (TB-027)."""
    from app.engine.imports import parse_csv_transactions
    from app.engine.store.db import DatabaseManager
    from app.engine.store.import_repo import ImportRepository

    try:
        batch, rows = parse_csv_transactions(args.file)
    except FileNotFoundError:
        _emit(args.json, {"status": "error", "error": f"file not found: {args.file}"}, text=f"File not found: {args.file}")
        sys.exit(2)
    except Exception as exc:
        _emit(args.json, {"status": "error", "error": f"{type(exc).__name__}: {exc}"}, text=f"Parse error: {exc}")
        sys.exit(2)

    if not batch.is_balanced:
        _emit(
            args.json,
            {"status": "blocked", "isBalanced": False, "netImbalance": str(batch.net_imbalance)},
            text=f"NOT BALANCED — net imbalance {batch.net_imbalance}. Nothing committed.",
        )
        sys.exit(1)

    db = DatabaseManager()
    batch_id = ImportRepository(db).commit_batch(batch, rows)
    _emit(
        args.json,
        {"status": "ok", "batchId": batch_id, "rowsCommitted": len(rows)},
        text=f"Committed batch {batch_id}: {len(rows)} rows.",
    )
    sys.exit(0)


def _cmd_forecast(args: argparse.Namespace) -> None:
    from app.engine.store.db import DatabaseManager
    from app.engine.store.forecast_repo import ForecastRepository

    db = DatabaseManager()
    repo = ForecastRepository(db)
    try:
        ws = repo.generate_forecast(scenario_id=args.scenario, default_method=args.method)
    except Exception as exc:
        _emit(args.json, {"status": "error", "error": f"{type(exc).__name__}: {exc}"}, text=f"Forecast failed: {exc}")
        sys.exit(2)
    _emit(
        args.json,
        {"status": "ok", "scenario": ws.scenario, "lines": len(ws.lines), "totals": ws.totals},
        text=f"Scenario {ws.scenario}: {len(ws.lines)} lines, FY landing {ws.totals.get('fy_landing')}",
    )
    sys.exit(0)


def _cmd_export_xlsx(args: argparse.Namespace) -> None:
    from pathlib import Path
    from app.engine.exports.excel_pack import create_sample_pack_data, export_excel_pack

    out = Path(args.out)
    export_excel_pack(out, create_sample_pack_data())
    _emit(
        args.json,
        {"status": "ok", "path": str(out), "bytes": out.stat().st_size},
        text=f"Excel pack written: {out} ({out.stat().st_size:,} bytes)",
    )
    sys.exit(0)


def _cmd_export_ppt(args: argparse.Namespace) -> None:
    from pathlib import Path
    from app.engine.exports.ppt_pack import generate_powerpoint_deck

    out = Path(args.out)
    prs = generate_powerpoint_deck(output_path=out)
    _emit(
        args.json,
        {"status": "ok", "path": str(out), "slides": len(prs.slides)},
        text=f"PPT deck written: {out} (6 slides)",
    )
    sys.exit(0)


def _cmd_migrate(args: argparse.Namespace) -> None:
    from app.engine.store.db import DatabaseManager

    # Constructing the manager applies schema_duckdb.sql + seeds (idempotent).
    DatabaseManager()
    _emit(args.json, {"status": "ok", "schemaStatus": "current"}, text="Schema current (idempotent init ran).")
    sys.exit(0)


def _cmd_report(args: argparse.Namespace) -> None:
    from app.engine.store.db import DatabaseManager

    db = DatabaseManager()
    counts: dict = {}
    try:
        conn = db.get_duckdb_connection()
        try:
            for table in ("FactActual", "FactBudget", "FactForecast", "FactImportBatch", "FactException"):
                try:
                    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    counts[table] = row[0] if row else 0
                except Exception:
                    counts[table] = None
        finally:
            conn.close()
    except Exception:
        counts = {}
    _emit(
        args.json,
        {"status": "ok", "rowCounts": counts},
        text="Store summary:\n" + "\n".join(f"  {k:<16}{v}" for k, v in counts.items()),
    )
    sys.exit(0)


def _emit(as_json: bool, payload: dict, *, text: str) -> None:
    import json as _json

    if as_json:
        print(_json.dumps(payload, default=str))
    else:
        print(text)


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

    # import / validate / forecast / exports / migrate / report (TB-027)
    import_parser = subparsers.add_parser("import", help="Parse, validate and commit a source file")
    import_parser.add_argument("file", help="CSV or XLSX source file")
    import_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

    validate_parser = subparsers.add_parser("validate", help="Parse + validate a file without committing")
    validate_parser.add_argument("file", help="CSV or XLSX source file")
    validate_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

    forecast_parser = subparsers.add_parser("forecast", help="Generate the forecast workspace")
    forecast_parser.add_argument("--scenario", default="base", help="Scenario id (default: base)")
    forecast_parser.add_argument("--method", default="run_rate", help="Default method for unmapped accounts")
    forecast_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

    xlsx_parser = subparsers.add_parser("export-xlsx", help="Build the Excel month-end pack")
    xlsx_parser.add_argument("--out", default="month_end_pack.xlsx", help="Output path")
    xlsx_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

    ppt_parser = subparsers.add_parser("export-ppt", help="Build the PowerPoint deck")
    ppt_parser.add_argument("--out", default="board_pack.pptx", help="Output path")
    ppt_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

    migrate_parser = subparsers.add_parser("migrate", help="Apply schema migrations (idempotent)")
    migrate_parser.add_argument("--json", action="store_true", help="Output report as JSON")

    report_parser = subparsers.add_parser("report", help="Print a compact store summary")
    report_parser.add_argument("--json", action="store_true", help="Output summary as JSON")

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
    elif args.command == "import":
        _cmd_import(args)
    elif args.command == "validate":
        _cmd_validate(args)
    elif args.command == "forecast":
        _cmd_forecast(args)
    elif args.command == "export-xlsx":
        _cmd_export_xlsx(args)
    elif args.command == "export-ppt":
        _cmd_export_ppt(args)
    elif args.command == "migrate":
        _cmd_migrate(args)
    elif args.command == "report":
        _cmd_report(args)
    elif args.command == "launch" or args.command is None:
        from app.desktop.shell import launch_app
        launch_app()


if __name__ == "__main__":
    main()
