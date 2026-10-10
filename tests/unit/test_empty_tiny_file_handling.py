"""
Empty and tiny file handling test suite per docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md.

Quoting docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §8 (X22) and edge-case matrix (E3, E4, E12):
- E3 / X22 (Header-only 0-row file): "Data-range emptiness after the header. Rejected by default with the zero-activity override path." (Slug: import.noDataRows).
- E4 (Zero-amount rows): "Zero-amount rows noted; keep the row, count and flag it (excluded from outlier rules)." (Slug: import.zeroAmountRows / IMP-021).
- E12 / Single-row files: "Fully supported; no minimum-size assumption anywhere in the pipeline."
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from app.engine.imports import parse_and_validate_csv
from app.engine.imports.hardening import load_hardened_excel_sheet


def test_header_only_csv_rejected(tmp_path: Path):
    """
    Proves E3 / X22: Header-only CSV file (0 data rows) has 0 loaded rows and 0 source rows.
    """
    csv_file = tmp_path / "header_only.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n", encoding="utf-8"
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.loaded_count == 0
    assert batch.total_source_rows == 0


def test_zero_amount_rows_kept_and_flagged(tmp_path: Path):
    """
    Proves E4: Zero-amount rows (Debit = 0, Credit = 0) are kept and successfully loaded.
    """
    csv_file = tmp_path / "zero_amounts.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-04-01,1001,0.00,0.00,FY26-P01\n"
        "COMP,V002,1,2026-04-01,1001,500.00,0.00,FY26-P01\n",
        encoding="utf-8",
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.loaded_count == 2


def test_single_row_file_supported(tmp_path: Path):
    """
    Proves E12: Single-row files (header + exactly 1 data row) are fully supported
    with no minimum-size restriction.
    """
    csv_file = tmp_path / "single_row.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-04-01,1001,123.45,0.00,FY26-P01\n",
        encoding="utf-8",
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.loaded_count == 1
    assert batch.total_source_rows == 1


def test_header_only_excel_rejected(tmp_path: Path):
    """
    Proves E3 / X22 for Excel: Header-only Excel workbook (0 data rows) triggers import.noDataRows.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Actuals"
    ws.append(
        ["Company", "Voucher", "Line", "PostingDate", "AccountCode", "Debit", "Credit", "Period"]
    )
    xlsx_path = tmp_path / "no_data_rows.xlsx"
    wb.save(xlsx_path)

    hardened = load_hardened_excel_sheet(xlsx_path, sheet_name="Actuals")
    slugs = [f.slug for f in hardened.findings]
    assert "import.noDataRows" in slugs
    assert len(hardened.rows) == 0
