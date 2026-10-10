"""Tests for DuckDB and SQLite store integration per 03_DATA_DICTIONARY.md and 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md."""

from pathlib import Path

from app.engine.imports.parser import parse_csv_transactions
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository


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

        # Direction 1 of DEF-010: a balanced bank ledger is importable and commits atomically.
        # The sample file was generated today to be intentionally balanced (net_imbalance == 0),
        # so the old assertion ``is_balanced is False`` was a stale negative check, not a spec check.
        assert batch.is_balanced is True, (
            f"DEF-010 Direction 1: expected sample-data/bank_ledger_actuals.csv to be balanced. "
            f"net_imbalance={batch.net_imbalance}, tolerance={batch.balance_tolerance}"
        )
        assert batch.net_imbalance == 0
        batch_id = repo.commit_batch(batch, transactions)
        assert batch_id > 0

        # Verify SQLite batch record
        batches = repo.list_batches()
        assert len(batches) == 1
        assert batches[0]["batch_id"] == batch_id
        assert batches[0]["loaded_count"] == len(transactions)
        assert batches[0]["status"] == "committed"
        assert batches[0]["is_balanced"] == 1

        # Verify DuckDB FactActual records: committed file lands every transaction.
        duck_conn = db_mgr.get_duckdb_connection()
        try:
            row_count = duck_conn.execute(
                "SELECT count(*) FROM FactActual WHERE import_batch_id = ?",
                [batch_id],
            ).fetchone()[0]
            assert row_count == len(transactions)
        finally:
            duck_conn.close()
