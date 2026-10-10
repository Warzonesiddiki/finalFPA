"""
File size and row limit enforcement test suite per doc 04 limits section.
Proves pre-scan row and file-size estimation using synthetic CSV fixtures.
"""

from __future__ import annotations

from pathlib import Path

from app.engine.imports import prescan_file


def test_prescan_size_and_row_estimation(tmp_path: Path):
    """
    Quoting doc 04 limits section:
    - Pre-scan row and file-size estimate
    - Fast estimation without OOM or hanging
    """
    csv_file = tmp_path / "prescan_test.csv"
    lines = ["Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period"]
    for i in range(1, 101):
        lines.append(f"COMP,V{i:03d},1,2026-04-01,1001,10.00,0.00,FY26-P01")
    csv_file.write_text("\n".join(lines), encoding="utf-8")

    result = prescan_file(csv_file)
    assert result is not None
    assert result.file_size_bytes > 0
    assert result.estimated_rows == 100
    assert result.file_checksum is not None
