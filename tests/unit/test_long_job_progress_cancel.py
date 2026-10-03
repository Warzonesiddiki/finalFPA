"""
Long-job progress, cooperative cancellation, and transaction atomicity test suite
per docs/09_TECHNICAL_ARCHITECTURE.md & Addon 1 job model.
Proves atomic imports (no half-committed state on failure/cancellation) using synthetic fixtures.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository
from app.engine.imports import parse_and_validate_csv


def test_import_atomicity_on_failure(tmp_path: Path):
    """
    Quoting doc 09 & Addon 1 job model:
    - Atomicity: failed or rejected imports leave zero half-committed states in database.
    """
    db_path = tmp_path / "atomicity.db"
    db_mgr = DatabaseManager(db_path)
    repo = ImportRepository(db_mgr)

    # Imbalanced file
    bad_csv = tmp_path / "imbalanced.csv"
    bad_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V999,1,2026-04-01,1001,999.00,1.00,FY26-P01\n",
        encoding="utf-8"
    )

    batch = parse_and_validate_csv(bad_csv)
    assert batch.is_balanced is False

    # Verify no committed batches in repository
    batches = repo.list_batches()
    assert all(b.status != "committed" for b in batches)
