"""Time each stage of the acceptance context build to find the bottleneck."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SAMPLE = ROOT / "sample-data"
FILES = ("d365_gl_actuals.csv", "bank_ledger_actuals.csv", "payroll_procurement_actuals.csv")


def log(msg):
    print(msg, flush=True)


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="fpa_time_"))
    os.environ["FPA_PROJECT_DIR"] = str(tmp)

    from app.engine.store.db import DatabaseManager
    from app.engine.store.import_repo import ImportRepository
    from app.engine.imports.parser import prescan_file, parse_csv_transactions
    from app.engine.imports.profile_binding import (
        resolve_base_profile,
        resolve_profile_for_import,
    )

    t = time.perf_counter()
    db = DatabaseManager()
    repo = ImportRepository(db)
    log(f"[{time.perf_counter()-t:6.1f}s] DatabaseManager ready")

    for name in FILES:
        path = SAMPLE / name
        t = time.perf_counter()
        prescan = prescan_file(path)
        log(f"[{time.perf_counter()-t:6.1f}s] prescan {name} rows={prescan.estimated_rows}")

        t = time.perf_counter()
        binding = resolve_profile_for_import(
            db, base_profile=resolve_base_profile(db, prescan.sample_headers))
        log(f"[{time.perf_counter()-t:6.1f}s] profile {name}")

        t = time.perf_counter()
        batch, txs = parse_csv_transactions(path, profile=binding.profile)
        log(f"[{time.perf_counter()-t:6.1f}s] parse {name} txs={len(txs)} "
            f"balanced={batch.is_balanced} can_commit={batch.can_commit}")

        t = time.perf_counter()
        repo.commit_batch(batch, txs)
        log(f"[{time.perf_counter()-t:6.1f}s] commit {name}")

    t = time.perf_counter()
    from app.engine.store.exceptions_repo import ExceptionsRepository
    ctx = ExceptionsRepository(db).build_rule_context("FY26-P09", "2026-11-12")
    log(f"[{time.perf_counter()-t:6.1f}s] build_rule_context tx={len(ctx.transactions)} "
        f"batches={len(ctx.import_batches)}")


if __name__ == "__main__":
    main()
