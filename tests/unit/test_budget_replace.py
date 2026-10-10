"""Unit tests for budget re-import with diff summary and atomic replacement.

FR-IMP-028 · P1 · Phase 1 — Budget re-import replaces a version atomically:
Re-importing a budget for the same version replaces the previous version's lines
in an atomic transaction; never merges silently. After re-import, no orphan lines
from the previous version exist, and the diff summary (old vs new totals by entity/period
with deltas) is presented before commit.
"""

from decimal import Decimal

from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository


def test_budget_replace_diff_and_atomic():
    db = DatabaseManager()
    repo = ImportRepository(db)

    # Setup initial budget version FY26-Approved
    initial_rows = [
        {
            "company_code": "IN01",
            "period_code": "FY26-P01",
            "amount": 100000,
            "company_id": 1,
            "account_id": 5000,
            "period_id": 1,
        },
        {
            "company_code": "IN01",
            "period_code": "FY26-P02",
            "amount": 150000,
            "company_id": 1,
            "account_id": 5000,
            "period_id": 2,
        },
    ]
    repo.commit_budget_replace("FY26-Approved", initial_rows, batch_id=888)

    # Incoming rows for replacement (P01 changed to 120,000, P03 added)
    incoming_rows = [
        {
            "company_code": "IN01",
            "period_code": "FY26-P01",
            "amount": 120000,
            "company_id": 1,
            "account_id": 5000,
            "period_id": 1,
        },
        {
            "company_code": "IN01",
            "period_code": "FY26-P03",
            "amount": 200000,
            "company_id": 1,
            "account_id": 5000,
            "period_id": 3,
        },
    ]

    # Test preview diff
    diff = repo.preview_budget_replace("FY26-Approved", incoming_rows)
    assert diff["budgetVersion"] == "FY26-Approved"
    assert Decimal(diff["oldGrandTotal"]) == Decimal("250000")
    assert Decimal(diff["newGrandTotal"]) == Decimal("320000")
    assert Decimal(diff["grandDelta"]) == Decimal("70000")

    # Test commit replacement (replace-not-merge)
    committed_count = repo.commit_budget_replace("FY26-Approved", incoming_rows, batch_id=889)
    assert committed_count == 2

    # Verify no orphan lines from old P02 exist and P03 is present
    conn = db.get_duckdb_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM FactBudget WHERE budget_version = 'FY26-Approved'"
        ).fetchone()[0]
        assert count == 2
        p02_count = conn.execute(
            "SELECT COUNT(*) FROM FactBudget WHERE budget_version = 'FY26-Approved' AND period_id = 2"
        ).fetchone()[0]
        assert p02_count == 0
    finally:
        conn.close()
