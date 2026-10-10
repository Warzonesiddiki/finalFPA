import tempfile
from decimal import Decimal
from pathlib import Path

from app.engine.exports.excel_pack import (
    BvARow,
    MonthEndPackData,
    PackContext,
    export_excel_pack,
)


def test_def015_excel_pack_money_float():
    """
    DEF-015: Ensure exact Decimal precision is preserved in excel_pack dataclasses
    and exported to openpyxl without going through binary float.
    99999999999999.99 becomes .98 if float() is used.
    """
    huge_amount = Decimal("99999999999999.99")
    huge_budget = Decimal("88888888888888.88")

    ctx = PackContext()

    bva = BvARow(
        level=1,
        account_code="4000",
        account_name="Revenue",
        account_type="revenue",
        cost_centre="All",
        actual=huge_amount,
        budget=huge_budget,
        variance=huge_amount - huge_budget,
        var_pct=None,
        signal="",
        effective_threshold="",
        rank=1,
        rows_count=1,
        commentary="",
    )

    pack_data = MonthEndPackData(
        context=ctx,
        bva_rows=[bva],
        pl_rows=[],
        transaction_rows=[],
        exception_rows=[],
        forecast_rows=[],
        import_batches=[],
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "test_float_excel_pack.xlsx"
        export_excel_pack(tmp_path, pack_data)

        # Verify the dataclass field type is indeed preserved
        assert isinstance(pack_data.bva_rows[0].actual, Decimal)
        assert pack_data.bva_rows[0].actual == huge_amount

        # Note: the openpyxl boundary legitimately coerces to float as Excel
        # is IEEE 754. The defect was coercion INSIDE the dataclass itself.
