import pytest
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from app.engine.store.import_repo import ImportRepository
from app.engine.store.db import DatabaseManager
from app.engine.imports.models import ImportBatchResult, ParsedTransaction, ValidationCheckReport

@pytest.mark.tst_id("TST-IMP-35")
def test_import_repo_commit_batch(tmp_path):
    db_mgr = DatabaseManager(project_dir=tmp_path)
    repo = ImportRepository(db_mgr)

    batch = ImportBatchResult(
        batch_id=0,
        file_name="test.csv",
        file_checksum="12345",
        source_type="trial_balance",
        total_source_rows=1,
        loaded_count=1,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=Decimal("100.00"),
        total_credit=Decimal("100.00"),
        net_imbalance=Decimal("0.00"),
        checks=[ValidationCheckReport(check_code="IMP-001", check_name="Test Check", status="pass", severity="info", offending_count=0, detail="OK", weight=Decimal("10"))],
        quarantined_rows=[]
    )
    txs = [ParsedTransaction(source_row_ref="r1", voucher_no="V1", posting_date="2025-01-15", company_code="IN01", account_code="6000", cost_center_code=None, project_code=None, vendor_code=None, invoice_no=None, description=None, debit=Decimal("100.00"), credit=Decimal("0.00"), net_amount=Decimal("100.00"), currency_code="INR", period_code="2025-P01")]

    batch_id = repo.commit_batch(batch, txs)
    assert batch_id > 0

def test_def015_import_repo_money_float(tmp_path):
    """
    DEF-015: Ensure exact Decimal precision is preserved into duckdb DECIMAL(18,2)
    without going through binary float. 99999999999999.99 becomes .98 if float() is used.
    """
    db_mgr = DatabaseManager(project_dir=tmp_path)
    duck = db_mgr.get_duckdb_connection()

    repo = ImportRepository(db_mgr)

    huge_decimal = Decimal("99999999999999.99")
    huge_budget = Decimal("88888888888888.88")

    batch_budget = ImportBatchResult(
        batch_id=0,
        file_name="budget.csv",
        file_checksum="1",
        source_type="budget",
        total_source_rows=1,
        loaded_count=1,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=huge_budget,
        total_credit=Decimal("0.00"),
        net_imbalance=huge_budget,
        checks=[],
        quarantined_rows=[]
    )
    txs_b = [ParsedTransaction(
        source_row_ref="b1", voucher_no="B1", posting_date="2026-09-01",
        company_code="IN01", account_code="4000", cost_center_code=None,
        project_code=None, vendor_code=None, invoice_no=None, description=None,
        debit=huge_budget, credit=Decimal("0.00"), net_amount=huge_budget,
        currency_code="INR", period_code="FY26-P09"
    )]
    repo.commit_batch(batch_budget, txs_b)

    batch_actual = ImportBatchResult(
        batch_id=0,
        file_name="actuals.csv",
        file_checksum="1",
        source_type="actuals_d365",
        total_source_rows=1,
        loaded_count=1,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=huge_decimal,
        total_credit=huge_decimal,
        net_imbalance=Decimal("0.00"),
        checks=[],
        quarantined_rows=[]
    )
    txs_a = [ParsedTransaction(
        source_row_ref="a1", voucher_no="A1", posting_date="2026-09-01",
        company_code="IN01", account_code="4000", cost_center_code=None,
        project_code=None, vendor_code=None, invoice_no=None, description=None,
        debit=huge_decimal, credit=Decimal("0.00"), net_amount=huge_decimal,
        currency_code="INR", period_code="FY26-P09"
    )]
    
    repo.commit_batch(batch_actual, txs_a)

    # Now let's query and assert exact Decimal equality (str from db matches exact value)
    res_actual = duck.execute("SELECT debit, credit, net_amount FROM FactActual LIMIT 1").fetchone()
    # DuckDB python client returns python Decimal for DECIMAL columns
    assert res_actual[0] == huge_decimal
    assert res_actual[1] == Decimal("0.00")
    assert res_actual[2] == huge_decimal

    res_budget = duck.execute("SELECT amount FROM FactBudget LIMIT 1").fetchone()
    assert res_budget[0] == huge_budget

def test_def015_replace_budget_money_float(tmp_path):
    """
    Ensure exact Decimal precision is preserved in replace_budget_version.
    import_repo.py L433 contained float coercion.
    """
    db_mgr = DatabaseManager(project_dir=tmp_path)
    duck = db_mgr.get_duckdb_connection()
    sqlite = db_mgr.get_sqlite_connection()
    project_root = Path(__file__).resolve().parent.parent.parent
    schema_dir = project_root / "app" / "engine" / "store"
    with open(schema_dir / "schema_duckdb.sql", "r", encoding="utf-8") as f:
        duck.execute(f.read())
    with open(schema_dir / "schema_sqlite.sql", "r", encoding="utf-8") as f:
        sqlite.executescript(f.read())

    repo = ImportRepository(db_mgr)
    
    huge_amount = Decimal("99999999999999.99")
    incoming_rows = [
        {
            "company_id": 1,
            "account_id": 4000,
            "period_id": 9,
            "amount": huge_amount, # can be passed as Decimal from upstream parse
            "currency_code": "INR"
        }
    ]
    repo.commit_budget_replace(budget_version="FY26-V2", incoming_rows=incoming_rows, batch_id=2)
    
    res = duck.execute("SELECT amount FROM FactBudget WHERE budget_version = 'FY26-V2'").fetchone()
    assert res[0] == huge_amount
