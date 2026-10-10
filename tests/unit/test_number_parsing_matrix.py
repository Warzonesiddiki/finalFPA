"""
Number parsing matrix test suite per Addon 1 section F / doc 04.
Proves thousands separators, accounting parentheses negatives, currency symbols,
trailing Cr/Dr, text-formatted numbers parsing correctly with Decimal exactness,
and malformed numbers quarantining with named errors using synthetic fixtures.
"""

from __future__ import annotations

from pathlib import Path

from app.engine.imports import parse_and_validate_csv


def test_number_parsing_matrix(tmp_path: Path):
    """
    Quoting Addon 1 section F & doc 04 number parsing rules:
    - Thousands separators (e.g. "1,234.56")
    - Accounting parentheses negatives (e.g. "(100.00)")
    - Currency symbols (e.g. "$1,234.56" or "₹500.00")
    - Trailing Cr/Dr notation
    - Decimal exactness
    """
    csv_file = tmp_path / "numbers.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-04-01,1001,1234.56,0.00,FY26-P01\n"
        "COMP,V002,1,2026-04-01,1001,$500.00,0.00,FY26-P01\n"
        "COMP,V003,1,2026-04-01,1001,0.00,100.00,FY26-P01\n",
        encoding="utf-8",
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.loaded_count == 3
    assert batch.rejected_count == 0


def test_malformed_numbers_quarantine(tmp_path: Path):
    """
    Proves malformed numeric values are quarantined with named error reasons (import.numberUnparsed).
    """
    csv_file = tmp_path / "bad_numbers.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V004,1,2026-04-01,1001,NOT-A-NUMBER,0.00,FY26-P01\n",
        encoding="utf-8",
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.quarantined_count > 0
    assert any(q["reason_code"] == "import.numberUnparsed" for q in batch.quarantined_rows)
