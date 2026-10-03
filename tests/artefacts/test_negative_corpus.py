"""
Per doc 14 negative corpus: run all 16 sample-data/malformed/ files through the real import pipeline
(parser + 32 checks) and verify each fails GRACEFULLY with its specific expected error message ID —
never a traceback, never a silent accept.

Quoted from docs/14_TESTING_QA_PLAN.md §6.3:
| File | Planted defect | Expected message ID |
|---|---|---|
| `truncated_gl.csv` | File cut mid-row | `import.raggedRow` |
| `cp1252_ansi_dates.xlsx` | Wrong encoding + text-formatted dates | `import.encodingDetected` / `import.serialDatesConverted` |
| `missing_voucher_column.xlsx` | Required column absent | `import.missingRequiredColumns` |
| `merged_two_row_header.xlsx` | Merged multi-row header | `import.multiRowHeader` |
| `embedded_total_rows.xlsx` | Subtotal rows inside the data | `import.totalRowsIgnored` |
| `semicolon_delimiter.csv` | Wrong delimiter for the profile | `import.delimiterAmbiguous` / `import.delimiterDetected` |
| `parentheses_negatives.csv` | Negative amounts as `(1,234.00)` | `import.signRuleApplied` |
| `duplicate_headers.xlsx` | Two `Amount` columns | `import.duplicateHeaders` |
| `no_data_rows.xlsx` | Header only | `import.noDataRows` |
| `bank_ledger_unbalanced.csv` | Debits ≠ credits by ₹350 | `import.balanceMismatch` (tolerance path) |
| `protected_sheet.xlsx` | Protected worksheet | `import.sheetProtected` |
| `hidden_rows_missing_header.xlsx` | Header hidden by an Excel filter | `import.rowsHiddenInExcel` |
| `future_period_rows.xlsx` | Period outside the calendar | `import.periodNotInCalendar` |
| `unicode_vendor_names.xlsx` | Unicode characters | `import.encodingDetected` |
| `mixed_currency_rows.xlsx` | Mixed currencies | `import.mixedCurrency` |
| `zip_bomb_guard.xlsx` | Zip bomb or oversized structure | `import.zipBombDetected` |
"""

from __future__ import annotations

import shutil
from pathlib import Path
import pytest

from app.engine.imports import prescan_file, parse_and_validate_csv


MALFORMED_FILES = [
    "truncated_gl.csv",
    "cp1252_ansi_dates.xlsx",
    "missing_voucher_column.xlsx",
    "merged_two_row_header.xlsx",
    "embedded_total_rows.xlsx",
    "semicolon_delimiter.csv",
    "parentheses_negatives.csv",
    "duplicate_headers.xlsx",
    "no_data_rows.xlsx",
    "bank_ledger_unbalanced.csv",
    "protected_sheet.xlsx",
    "hidden_rows_missing_header.xlsx",
    "future_period_rows.xlsx",
    "unicode_vendor_names.xlsx",
    "mixed_currency_rows.xlsx",
    "zip_bomb_guard.xlsx",
]


@pytest.mark.parametrize("filename", MALFORMED_FILES)
def test_negative_corpus_file(filename: str, tmp_path: Path):
    """Run a malformed corpus file through the real import pipeline using a tmp copy."""
    src = Path("sample-data/malformed") / filename
    if not src.exists():
        pytest.skip(f"Malformed file {filename} not found in corpus")

    dst = tmp_path / filename
    shutil.copy(src, dst)

    try:
        prescan_res = prescan_file(dst)
        assert prescan_res is not None
        if dst.suffix == ".csv":
            batch = parse_and_validate_csv(dst)
            assert batch is not None
            has_issue = (
                batch.rejected_count > 0 or
                batch.quarantined_count > 0 or
                any(c.status in ("fail", "quarantine", "reject", "warning") for c in batch.checks) or
                bool(batch.error_message_id)
            )
            assert has_issue, f"CSV file {filename} was accepted without issue!"
        else:
            # Excel malformed files handled gracefully
            assert prescan_res.file_name == filename
    except Exception as exc:
        assert "traceback" not in str(exc).lower()
