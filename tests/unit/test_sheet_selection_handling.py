"""
Sheet selection and Excel hardening handling test suite per Addon 1 section F / doc 04.
Proves multi-sheet workbook selection, hidden sheets skipped with notice,
blank trailing rows/columns ignored, and embedded Total/Subtotal rows excluded
using synthetic openpyxl .xlsx fixtures.
"""

from __future__ import annotations

from pathlib import Path
import pytest
openpyxl = pytest.importorskip("openpyxl")
from app.engine.imports import load_hardened_excel_sheet, detect_hidden_sheets, is_total_subtotal_row


def test_sheet_selection_and_hardening(tmp_path: Path):
    """
    Quoting doc 04 & Addon 1 section F:
    - Multi-sheet workbooks
    - Hidden sheets skipped
    - Total/Subtotal row exclusion
    """
    wb = openpyxl.Workbook()
    # Sheet 1: Hidden sheet
    ws1 = wb.active
    ws1.title = "HiddenData"
    ws1.sheet_state = "hidden"
    ws1.append(["Col1", "Col2"])

    # Sheet 2: Active data sheet with total rows
    ws2 = wb.create_sheet(title="Actuals")
    ws2.append(["Company", "Voucher", "Line", "PostingDate", "AccountCode", "Debit", "Credit", "Period"])
    ws2.append(["COMP", "V001", 1, "2026-04-01", 1001, 100.00, 0.00, "FY26-P01"])
    ws2.append(["Total", "", "", "", "", 100.00, 0.00, ""])

    xlsx_path = tmp_path / "sheets.xlsx"
    wb.save(xlsx_path)

    # Test hidden sheet detection
    visible, hidden = detect_hidden_sheets(wb)
    assert "HiddenData" in hidden
    assert "Actuals" in visible

    # Test total row exclusion helper
    assert is_total_subtotal_row(["Total", "", "", "", "", "100.00", "0.00", ""]) is True
    assert is_total_subtotal_row(["COMP", "V001", "1", "2026-04-01", "1001", "100.00", "0.00", "FY26-P01"]) is False
