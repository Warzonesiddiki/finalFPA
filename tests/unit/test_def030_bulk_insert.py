"""DEF-030 regression: batched ``INSERT`` for the analytic-store bulk load.

THE DEFECT. ``ImportRepository.commit_batch`` wrote ``FactActual`` /
``FactBudget`` with ``duckdb`` ``executemany``, which executes the prepared
statement once per row. Measured 2026-10-04 on the 26-column ``FactActual``
shape (``scratch/bench_duckdb_insert.py``):

    50,000 rows via executemany  211.70 s   ( 236 rows/s)
    50,000 rows via batched VALUES 13.45 s   (3,717 rows/s)   <- 15x

At 236 rows/s the 250k-row month-end import spent ~19 minutes inside
``commit_batch`` - measured end-to-end at 72.6 s after the fix for the same
250,040-row file - and the doc 14 section 5.2 acceptance run spent most of a
20-minute wall clock in the one statement. Nothing about the values changed:
every value is still a bound parameter, and DuckDB still applies the column
types and casts it applied before.

ATOMICITY. The single ``executemany`` was one statement and therefore one
atomic write. Chunking it into several statements must not weaken Addon 1 P12
("imports run in a staging area and commit atomically"): ``_bulk_insert`` wraps
every chunk in one explicit transaction, so an interruption leaves all rows or
none. That is what ``test_bulk_insert_rolls_back_every_chunk_on_failure`` pins,
and it fails on a chunked implementation without the explicit transaction.
"""

from __future__ import annotations

from decimal import Decimal

import duckdb
import pytest

from app.engine.imports.models import ImportBatchResult, ParsedTransaction
from app.engine.store import import_repo as import_repo_module
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository, _bulk_insert


def _batch(n_rows: int) -> tuple[ImportBatchResult, list[ParsedTransaction]]:
    txs = [
        ParsedTransaction(
            source_row_ref=f"row_{i}",
            voucher_no=f"V{i}",
            posting_date="2026-09-15",
            document_date=None,
            company_code="IN01",
            account_code="5200",
            cost_center_code="CC-100",
            project_code=None,
            vendor_code="V-1",
            invoice_no=f"I-{i}",
            description="def030 fixture",
            debit=Decimal("100.00") + Decimal(i) / Decimal("100"),
            credit=Decimal("0.00"),
            net_amount=Decimal("100.00") + Decimal(i) / Decimal("100"),
            currency_code="INR",
            period_code="FY26-P09",
        )
        for i in range(n_rows)
    ]
    batch = ImportBatchResult(
        batch_id=0,
        file_name="def030.csv",
        file_checksum="def030",
        source_type="actuals_d365",
        total_source_rows=n_rows,
        loaded_count=n_rows,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=sum((tx.debit for tx in txs), Decimal("0.00")),
        total_credit=Decimal("0.00"),
        net_imbalance=sum((tx.debit for tx in txs), Decimal("0.00")),
        checks=[],
        quarantined_rows=[],
    )
    return batch, txs


def test_commit_batch_lands_every_row_across_chunk_boundaries(tmp_path, monkeypatch):
    """Rows land even when the batch is split over many INSERT statements.

    ``INSERT_BATCH_ROWS`` is forced down to 2 so a 5-row batch crosses two
    chunk boundaries. The outcome must be identical to the single-statement
    version: same count, same exact ``Decimal`` money values (DEF-015's
    precision guarantee is re-asserted through the changed code path).
    """
    monkeypatch.setattr(import_repo_module, "INSERT_BATCH_ROWS", 2)
    db = DatabaseManager(project_dir=tmp_path)
    repo = ImportRepository(db)
    batch, txs = _batch(5)

    repo.commit_batch(batch, txs)

    conn = db.get_duckdb_connection()
    try:
        rows = conn.execute(
            "SELECT actual_id, debit, net_amount FROM FactActual ORDER BY actual_id"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 5
    # Exact Decimal equality at 2 dp, not approximately-close floats.
    for index, (actual_id, debit, net_amount) in enumerate(rows):
        expected = Decimal("100.00") + Decimal(index) / Decimal("100")
        assert actual_id > 0
        assert debit == expected.quantize(Decimal("0.01"))
        assert net_amount == debit


def test_bulk_insert_rolls_back_every_chunk_on_failure(monkeypatch):
    """A failure in a later chunk must leave zero rows, not a partial load.

    Five rows in a table whose primary key is ``id``, ``INSERT_BATCH_ROWS`` set
    to 2: statement 1 inserts rows 1-2, statement 2 inserts rows 3-4, statement
    3 carries the duplicate of row 1 and fails. Without the explicit
    transaction the first two statements would already be committed and the
    table would hold four rows - a half-loaded import, which Addon 1 P12
    forbids.
    """
    monkeypatch.setattr(import_repo_module, "INSERT_BATCH_ROWS", 2)
    conn = duckdb.connect(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, amount DECIMAL(18,2))")
        rows = [
            (1, "10.00"),
            (2, "20.00"),
            (3, "30.00"),
            (4, "40.00"),
            (1, "50.00"),  # duplicate primary key in the third chunk
        ]
        with pytest.raises(Exception):
            _bulk_insert(conn, "t", ("id", "amount"), rows)
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
    finally:
        conn.close()


def test_bulk_insert_positive_control_lands_all_rows(monkeypatch):
    """Same shape and batch size as the rollback test, but no duplicate key."""
    monkeypatch.setattr(import_repo_module, "INSERT_BATCH_ROWS", 2)
    conn = duckdb.connect(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, amount DECIMAL(18,2))")
        rows = [(1, "10.00"), (2, "20.00"), (3, "30.00"), (4, "40.00"), (5, "50.00")]
        _bulk_insert(conn, "t", ("id", "amount"), rows)
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 5
    finally:
        conn.close()


def test_bulk_insert_with_no_rows_is_a_noop():
    """An empty batch must not open a transaction or emit a statement."""
    conn = duckdb.connect(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        _bulk_insert(conn, "t", ("id",), [])
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
    finally:
        conn.close()
