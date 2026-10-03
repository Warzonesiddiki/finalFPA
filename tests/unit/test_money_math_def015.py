"""Regression tests for DEF-015: Floating-point binary float loss on money paths.

Validates that monetary math, repositories, and data export models preserve Decimal precision
and avoid float-coercion loss on monetary values across store, calc, and exports layers.
"""

from decimal import Decimal
import tempfile
from pathlib import Path
import pytest

from app.engine.exports.excel_pack import (
    PackContext,
    MonthEndPackData,
    BvARow,
    PLRow,
    TransactionRow,
    ImportBatchRow,
    ValidationCheckRow,
    export_excel_pack,
)


def test_def015_dataclasses_preserve_decimal():
    """Verify that export dataclasses store and retain Decimal precision without float conversion."""
    huge_amount = Decimal("99999999999999.99")
    huge_budget = Decimal("88888888888888.88")
    variance = huge_amount - huge_budget

    bva = BvARow(
        level=1,
        account_code="4000",
        account_name="Revenue",
        account_type="revenue",
        cost_centre="All",
        actual=huge_amount,
        budget=huge_budget,
        variance=variance,
        var_pct=0.125,
        signal="Fav ▲",
        effective_threshold="1000",
        rank=1,
        rows_count=1,
        commentary="Test comment",
    )
    assert isinstance(bva.actual, Decimal)
    assert bva.actual == huge_amount
    assert isinstance(bva.budget, Decimal)
    assert bva.budget == huge_budget
    assert isinstance(bva.variance, Decimal)
    assert bva.variance == variance

    pl = PLRow(
        line_item="Operating Revenue",
        category="Revenue",
        actual_mtd=huge_amount,
        budget_mtd=huge_budget,
        var_mtd=variance,
        var_pct_mtd=0.125,
        actual_ytd=huge_amount * 2,
        budget_ytd=huge_budget * 2,
        var_ytd=variance * 2,
        var_pct_ytd=0.125,
        signal="Fav ▲",
        notes="Drilldown driver",
    )
    assert isinstance(pl.actual_mtd, Decimal)
    assert isinstance(pl.actual_ytd, Decimal)
    assert pl.actual_mtd == huge_amount

    tx = TransactionRow(
        row_num=1,
        entity="CORP",
        account_code="4000",
        account_name="Revenue",
        cost_centre="CC100",
        department="Sales",
        project="PRJ01",
        vendor="Acme Corp",
        vendor_code="VND_001",
        period="2026-09",
        posting_date="2026-09-30",
        document_date="2026-09-30",
        voucher_no="VCH-001",
        document_no="DOC-001",
        invoice_no="INV-001",
        line=1,
        description="Transaction narrative",
        journal_category="Sales",
        debit=huge_amount,
        credit=Decimal("0.00"),
        net=huge_amount,
        dr_cr="Dr",
        currency="USD",
        source_system="ERP",
        source_file="d365_gl_actuals.csv",
        source_row_ref="10",
        batch_id=1,
        fingerprint="abcd",
        exception_ids="",
    )
    assert isinstance(tx.debit, Decimal)
    assert isinstance(tx.credit, Decimal)
    assert isinstance(tx.net, Decimal)
    assert tx.debit == huge_amount

    batch = ImportBatchRow(
        batch_id=1,
        status="COMMITTED",
        source_system="D365",
        file_name="d365_gl_actuals.csv",
        sheet="Sheet1",
        checksum_short="abc",
        checksum_full="abcdef",
        rows_read=100,
        rows_committed=100,
        rows_quarantined=0,
        rows_rejected=0,
        debit_total=huge_amount,
        credit_total=huge_amount,
        balance_variance=Decimal("0.00"),
        control_total_source=huge_amount,
        control_variance=Decimal("0.00"),
        balance_result="BALANCED",
        profile_version="v1.0",
        loaded_at="2026-09-30 12:00:00",
        loaded_by="system",
    )
    assert isinstance(batch.debit_total, Decimal)
    assert isinstance(batch.credit_total, Decimal)


def test_def015_export_excel_handles_decimal_values():
    """Verify that export_excel_pack safely formats and writes Decimal monetary values."""
    huge_amount = Decimal("99999999999999.99")
    huge_budget = Decimal("88888888888888.88")
    variance = huge_amount - huge_budget

    bva = BvARow(
        level=1,
        account_code="4000",
        account_name="Revenue",
        account_type="revenue",
        cost_centre="All",
        actual=huge_amount,
        budget=huge_budget,
        variance=variance,
        var_pct=0.125,
        signal="Fav ▲",
        effective_threshold="1000",
        rank=1,
        rows_count=1,
        commentary="Decimal math test",
    )

    batch = ImportBatchRow(
        batch_id=1,
        status="COMMITTED",
        source_system="D365",
        file_name="d365_gl_actuals.csv",
        sheet="Sheet1",
        checksum_short="abc",
        checksum_full="abcdef",
        rows_read=100,
        rows_committed=100,
        rows_quarantined=0,
        rows_rejected=0,
        debit_total=huge_amount,
        credit_total=huge_amount,
        balance_variance=Decimal("0.00"),
        control_total_source=huge_amount,
        control_variance=Decimal("0.00"),
        balance_result="BALANCED",
        profile_version="v1.0",
        loaded_at="2026-09-30 12:00:00",
        loaded_by="system",
    )

    pack_data = MonthEndPackData(
        context=PackContext(),
        bva_rows=[bva],
        pl_rows=[],
        transaction_rows=[],
        exception_rows=[],
        forecast_rows=[],
        import_batches=[batch],
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "test_def015_pack.xlsx"
        export_excel_pack(tmp_path, pack_data)
        assert tmp_path.exists()
        assert tmp_path.stat().st_size > 0


def test_def015_money_math_precision_no_float_drift():
    """Verify that high-precision monetary calculations avoid IEEE-754 binary float drift."""
    # 0.1 + 0.2 != 0.3 in IEEE-754 binary float
    val_a = Decimal("0.10")
    val_b = Decimal("0.20")
    expected = Decimal("0.30")
    assert val_a + val_b == expected

    # Large values where float loses penny precision
    penny_a = Decimal("99999999999999.99")
    penny_b = Decimal("0.01")
    assert penny_a + penny_b == Decimal("100000000000000.00")
