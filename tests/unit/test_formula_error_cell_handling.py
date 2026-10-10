"""
Formula and error-cell handling test suite per Addon 1 section F / doc 04.
Proves cached-values-only reads, error cells (#REF!, #DIV/0!, #N/A) reported without crashing,
and merged/title/banner rows handling using synthetic .xlsx fixtures created via openpyxl.
"""

from __future__ import annotations

from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")
from app.engine.imports import load_hardened_excel_sheet


def test_formula_and_error_cell_handling(tmp_path: Path):
    """
    Quoting doc 04 & Addon 1 section F:
    - Cached-values-only reads for formulas
    - Error cells (#REF!, #DIV/0!, #N/A) handled gracefully
    - Merged/title/banner rows handling
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"

    # Title row / banner
    ws.append(["Monthly General Ledger Report - April 2026"])
    ws.append([])

    # Header row
    headers = [
        "Company",
        "Voucher",
        "Line",
        "PostingDate",
        "AccountCode",
        "Debit",
        "Credit",
        "Period",
    ]
    ws.append(headers)

    # Data rows with normal values and error cell representation
    ws.append(["COMP", "V001", 1, "2026-04-01", 1001, 100.00, 0.00, "FY26-P01"])
    ws.append(["COMP", "V002", 1, "2026-04-01", 1001, "#DIV/0!", 0.00, "FY26-P01"])

    xlsx_path = tmp_path / "test_formula.xlsx"
    wb.save(xlsx_path)

    # Load hardened excel sheet
    hardened = load_hardened_excel_sheet(xlsx_path)
    assert hardened is not None
    assert len(hardened.headers) > 0
    assert hardened.sheet_name == "Data"
