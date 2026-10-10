"""
Mixed-currency handling test suite per docs/02_FUNCTIONAL_SPEC.md (E10) and docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md (§10 IMP-020).

Quoting docs/02_FUNCTIONAL_SPEC.md E10 & docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §10 IMP-020:
- E10: "Mixed-currency rows in a single-currency project -> Quarantine with the message (default per 04). Slug: import.mixedCurrency."
- IMP-020: "Currency matches the project currency. Quarantine the row, naming the currencies found. No silent conversion."
"""

from __future__ import annotations

from pathlib import Path

from app.engine.imports.parser import parse_csv_transactions


def test_mixed_currency_quarantined_with_message(tmp_path: Path):
    """
    Proves E10 / IMP-020: Mixed-currency rows (e.g. USD or EUR in an INR project)
    are quarantined, feature the message ID 'import.mixedCurrency' via canonical get_batch_slugs helper,
    and undergo zero silent conversion (they remain quarantined with their original currency).
    """
    csv_file = tmp_path / "mixed_currency.csv"
    csv_file.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Currency,Period\n"
        "COMP,V001,1,2026-04-01,1001,100.00,0.00,INR,FY26-P01\n"
        "COMP,V002,1,2026-04-01,1001,250.00,0.00,USD,FY26-P01\n"
        "COMP,V003,1,2026-04-01,1001,500.00,0.00,EUR,FY26-P01\n",
        encoding="utf-8",
    )

    # Parse with project_currency="INR"
    batch, parsed_txs = parse_csv_transactions(csv_file, project_currency="INR")

    # Row 1 (INR) should be loaded successfully (1 loaded transaction)
    assert len(parsed_txs) == 1
    assert parsed_txs[0].voucher_no == "V001"

    # Rows 2 (USD) and 3 (EUR) should be quarantined due to non-matching project currency
    assert batch.quarantined_count == 2
    assert len(batch.quarantined_rows) == 2

    # Verify canonical slug lookup via get_batch_slugs helper
    from conftest import get_batch_slugs

    slugs = get_batch_slugs(batch)
    assert "import.mixedCurrency" in slugs

    # Confirm no silent conversion occurred (quarantined rows retain original currency / raw values)
    raw_values_list = [q.get("raw_values", {}) for q in batch.quarantined_rows]
    all_values = [val for rv in raw_values_list for val in rv.values()]
    assert "USD" in all_values
    assert "EUR" in all_values
