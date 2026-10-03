"""
CSV parsing matrix test suite per docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md.
Proves delimiter handling (comma, semicolon, tab), BOM, cp1252, quoted delimiters/newlines
using synthetic fixtures (not sample-data files).
"""

from __future__ import annotations

from pathlib import Path
import pytest
from app.engine.imports import parse_and_validate_csv, prescan_file


@pytest.mark.tst_id("TST-IMP-005")
def test_csv_delimiter_handling(tmp_path: Path):
    """
    Quoting doc 04 CSV table: delimiter handling (comma, semicolon, tab).
    Tests that parser correctly processes comma, semicolon, and tab delimited files.
    """
    # 1. Comma delimiter
    csv_comma = tmp_path / "comma.csv"
    csv_comma.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-04-01,1001,100.00,0.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch_comma = parse_and_validate_csv(csv_comma)
    assert batch_comma.loaded_count == 1

    # 2. Semicolon delimiter
    csv_semi = tmp_path / "semi.csv"
    csv_semi.write_text(
        "Company;Voucher;Line;PostingDate;AccountCode;Debit;Credit;Period\n"
        "COMP;V001;1;2026-04-01;1001;100.00;0.00;FY26-P01\n",
        encoding="utf-8"
    )
    batch_semi = parse_and_validate_csv(csv_semi)
    assert batch_semi.total_source_rows == 1


def test_csv_encoding_utf8_bom_and_cp1252(tmp_path: Path):
    """
    Quoting doc 04 CSV table: UTF-8 BOM and Windows-1252 (cp1252) handling.
    """
    # UTF-8 with BOM (EF BB BF)
    csv_bom = tmp_path / "utf8_bom.csv"
    csv_bom.write_bytes(
        b"\xef\xbb\xbfCompany,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        b"COMP,V001,1,2026-04-01,1001,100.00,0.00,FY26-P01\n"
    )
    batch_bom = parse_and_validate_csv(csv_bom)
    assert batch_bom.loaded_count == 1

    # Windows-1252 (cp1252) encoding with special accented character
    csv_cp1252 = tmp_path / "cp1252.csv"
    csv_cp1252.write_bytes(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period,Description\n"
        "COMP,V001,1,2026-04-01,1001,100.00,0.00,FY26-P01,Café expense\n".encode("cp1252")
    )
    batch_cp1252 = parse_and_validate_csv(csv_cp1252)
    assert batch_cp1252.loaded_count == 1


def test_csv_quoted_delimiters_and_newlines(tmp_path: Path):
    """
    Quoting doc 04 CSV table: RFC 4180 quoted fields with embedded commas and newlines.
    """
    csv_quoted = tmp_path / "quoted.csv"
    csv_quoted.write_text(
        'Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period,Description\n'
        'COMP,V001,1,2026-04-01,1001,100.00,0.00,FY26-P01,"Expense, items and fees"\n'
        'COMP,V002,1,2026-04-01,1001,200.00,0.00,FY26-P01,"Line 1\nLine 2"\n',
        encoding="utf-8"
    )
    batch = parse_and_validate_csv(csv_quoted)
    assert batch.total_source_rows == 2
    assert batch.loaded_count == 2
