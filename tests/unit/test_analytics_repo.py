"""Unit tests for Analytics Repository.

Per docs/03_DATA_DICTIONARY.md §5, docs/05_CALCULATION_SPEC.md §3-§7,
and docs/09_TECHNICAL_ARCHITECTURE.md §12.
"""

from decimal import Decimal
import pytest

from app.engine.store.db import DatabaseManager
from app.engine.store.analytics_repo import (
    AnalyticsRepository,
    compute_favourability,
    BvaSummaryRow,
    StatementLineSummaryRow,
)


def test_compute_favourability():
    """Verify favourability per direction (CALC-012)."""
    # Higher is favourable (revenue)
    assert compute_favourability("higher_is_favourable", Decimal("120.00"), Decimal("100.00")) == "favourable"
    assert compute_favourability("higher_is_favourable", Decimal("90.00"), Decimal("100.00")) == "unfavourable"
    assert compute_favourability("higher_is_favourable", Decimal("100.00"), Decimal("100.00")) == "neutral"

    # Lower is favourable (expense)
    assert compute_favourability("lower_is_favourable", Decimal("90.00"), Decimal("100.00")) == "favourable"
    assert compute_favourability("lower_is_favourable", Decimal("110.00"), Decimal("100.00")) == "unfavourable"
    assert compute_favourability("lower_is_favourable", Decimal("100.00"), Decimal("100.00")) == "neutral"

    # Neutral
    assert compute_favourability("neutral", Decimal("110.00"), Decimal("100.00")) == "neutral"


def test_analytics_repository_bva_queries(tmp_path):
    """Verify DuckDB analytical aggregation queries in AnalyticsRepository."""
    db_mgr = DatabaseManager(tmp_path)
    repo = AnalyticsRepository(db_mgr)

    conn = db_mgr.get_duckdb_connection()
    try:
        # Insert test account and facts
        conn.execute("""
            INSERT OR IGNORE INTO DimAccount (account_id, account_code, account_name, account_type, statement_line, favourability_direction)
            VALUES (101, '4001', 'Domestic Product Sales', 'revenue', 'Revenue', 'higher_is_favourable'),
                   (102, '5001', 'Raw Material Purchases', 'expense', 'Cost of Goods Sold', 'lower_is_favourable');
        """)
        conn.execute("""
            INSERT INTO FactActual (actual_id, import_batch_id, row_fingerprint, company_id, period_id, account_id, debit, credit, net_amount, posting_date, voucher_no, source_file_name, source_row_ref)
            VALUES (1, 1, 'fp1', 1, 9, 101, 0.00, 150000.00, -150000.00, '2026-09-15', 'V01', 'file1.csv', '1'),
                   (2, 1, 'fp2', 1, 9, 102, 60000.00, 0.00, 60000.00, '2026-09-16', 'V02', 'file1.csv', '2');
        """)
        conn.execute("""
            INSERT INTO FactBudget (budget_id, import_batch_id, company_id, period_id, account_id, amount, source_row_ref)
            VALUES (1, 1, 1, 9, 101, 140000.00, 'b1'),
                   (2, 1, 1, 9, 102, 65000.00, 'b2');
        """)
    finally:
        conn.close()

    # Query BvA summary
    paged = repo.get_bva_summary(period_id=9)
    assert paged.total == 2
    assert len(paged.items) == 2

    # Revenue account: canonical sign shows positive 150,000 actual vs 140,000 budget
    rev_row = next(r for r in paged.items if r.account_code == "4001")
    assert rev_row.actual_amount == Decimal("150000.00")
    assert rev_row.budget_amount == Decimal("140000.00")
    assert rev_row.variance_amount == Decimal("10000.00")
    assert rev_row.favourability == "favourable"

    # COGS account: 60,000 actual vs 65,000 budget (under budget = favourable)
    cogs_row = next(r for r in paged.items if r.account_code == "5001")
    assert cogs_row.actual_amount == Decimal("60000.00")
    assert cogs_row.budget_amount == Decimal("65000.00")
    assert cogs_row.variance_amount == Decimal("-5000.00")
    assert cogs_row.favourability == "favourable"

    # Query statement line rollups
    stmt_lines = repo.get_bva_statement_line_summary(period_id=9)
    assert len(stmt_lines) == 2
    rev_stmt = next(s for s in stmt_lines if s.statement_line == "Revenue")
    assert rev_stmt.actual_amount == Decimal("150000.00")
