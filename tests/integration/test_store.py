"""Tests for DuckDB and SQLite store integration per 03_DATA_DICTIONARY.md and 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md."""

import shutil
import tempfile
from pathlib import Path
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository
from app.engine.imports.parser import parse_csv_transactions


def test_database_manager_initialization(tmp_path):
    db_mgr = DatabaseManager(tmp_path)
    assert db_mgr.duckdb_path.exists()
    assert db_mgr.sqlite_path.exists()

    duck_conn = db_mgr.get_duckdb_connection()
    try:
        count = duck_conn.execute("SELECT count(*) FROM DimPeriod").fetchone()[0]
        assert count == 12
    finally:
        duck_conn.close()


def test_atomic_import_commit(tmp_path):
    db_mgr = DatabaseManager(tmp_path)
    repo = ImportRepository(db_mgr)

    sample_file = Path("sample-data/bank_ledger_actuals.csv")
    if sample_file.exists():
        batch, transactions = parse_csv_transactions(sample_file)
        # DEF-010 code-to-spec: unbalanced file commits nothing (universal reject).
        assert batch.is_balanced is False
        batch_id = repo.commit_batch(batch, transactions)
        assert batch_id > 0

        # Verify SQLite batch record
        batches = repo.list_batches()
        assert len(batches) == 1
        assert batches[0]["batch_id"] == batch_id
        assert batches[0]["loaded_count"] == len(transactions)
        assert batches[0]["status"] == "rejected"
        assert batches[0]["is_balanced"] == 0

        # Verify DuckDB FactActual records: rejected file lands 0 rows (atomic)
        duck_conn = db_mgr.get_duckdb_connection()
        try:
            row_count = duck_conn.execute(
                "SELECT count(*) FROM FactActual WHERE import_batch_id = ?",
                [batch_id],
            ).fetchone()[0]
            assert row_count == 0
        finally:
            duck_conn.close()

