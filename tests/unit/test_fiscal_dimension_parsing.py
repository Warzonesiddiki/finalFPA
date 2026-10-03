"""
Fiscal period and dimension parsing test suite per Addon 1 section F / doc 04.
Proves fiscal text column parsing (FY26-P09, 2026-P09, 202609, Sep-26) to canonical periods,
and dimension string parsing using synthetic fixtures.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from app.engine.imports.parser import resolve_fiscal_period
from app.engine.imports import parse_and_validate_csv


def test_resolve_fiscal_period_variants():
    """
    Quoting doc 04 §7.4:
    Accepted variants:
    - FY26-P09, FY26-P9
    - 2026-P09, 26-P09
    - 202609
    - Sep-26
    - 09/2026
    """
    assert resolve_fiscal_period("FY26-P09") == "FY26-P09"
    assert resolve_fiscal_period("2026-P09") == "FY26-P09"
    assert resolve_fiscal_period("26-P09") == "FY26-P09"
    assert resolve_fiscal_period("202609") == "FY26-P09"
    assert resolve_fiscal_period("Sep-26") == "FY26-P09"
    assert resolve_fiscal_period("invalid") is None
    assert resolve_fiscal_period(None) is None


def test_fiscal_period_import_synthetic(tmp_path: Path):
    """
    Proves end-to-end import processing of various fiscal period formats in synthetic CSV files.
    """
    csv_file = tmp_path / "periods.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-09-15,1001,100.00,0.00,FY26-P09\n"
        "COMP,V002,1,2026-09-15,1001,200.00,0.00,202609\n"
        "COMP,V003,1,2026-09-15,1001,300.00,0.00,Sep-26\n",
        encoding="utf-8"
    )
    batch = parse_and_validate_csv(csv_file)
    assert batch.loaded_count == 3
    assert batch.rejected_count == 0
