"""
Date parsing matrix test suite per docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §7.1.
Proves ISO, dd-mm-yyyy, dd/mm/yyyy, yyyy/mm/dd parsing using synthetic fixtures.
"""

from __future__ import annotations

from pathlib import Path

from app.engine.imports import parse_and_validate_csv
from app.engine.imports.parser import parse_date_value


def test_date_parsing_formats():
    """
    Quoting doc 04 §7.1:
    - ISO format: YYYY-MM-DD
    - European/UK formats: DD/MM/YYYY, DD-MM-YYYY
    - ISO slashes: YYYY/MM/DD
    """
    assert parse_date_value("2026-04-15") == "2026-04-15"
    assert parse_date_value("15/04/2026") == "2026-04-15"
    assert parse_date_value("15-04-2026") == "2026-04-15"
    assert parse_date_value("2026/04/15") == "2026-04-15"
    assert parse_date_value("invalid-date") is None
    assert parse_date_value("") is None


def test_date_parsing_in_csv_imports(tmp_path: Path):
    """
    Proves end-to-end import processing of various date formats via synthetic CSV files.
    """
    csv_file = tmp_path / "dates.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-04-01,1001,100.00,0.00,FY26-P01\n"
        "COMP,V002,1,15/04/2026,1001,200.00,0.00,FY26-P01\n"
        "COMP,V003,1,20-04-2026,1001,300.00,0.00,FY26-P01\n",
        encoding="utf-8",
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.loaded_count == 3
    assert batch.rejected_count == 0
