"""Unit and golden tests for import parser and validation checks per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md."""

import pytest
from pathlib import Path
from app.engine.imports import prescan_file, parse_and_validate_csv, compute_file_checksum
from app.engine.calc import ZERO


@pytest.mark.tst_id("TST-IMP-001")
def test_compute_file_checksum():
    sample_file = Path("sample-data/bank_ledger_actuals.csv")
    if sample_file.exists():
        checksum = compute_file_checksum(sample_file)
        assert len(checksum) == 64


@pytest.mark.tst_id("TST-IMP-002")
def test_prescan_d365():
    sample_file = Path("sample-data/d365_gl_actuals.csv")
    if sample_file.exists():
        res = prescan_file(sample_file)
        assert res.file_name == "d365_gl_actuals.csv"
        assert res.has_banner is True
        assert res.estimated_rows > 100000
        assert "Voucher" in res.sample_headers


@pytest.mark.tst_id("TST-IMP-003")
def test_parse_and_validate_bank_ledger():
    sample_file = Path("sample-data/bank_ledger_actuals.csv")
    if sample_file.exists():
        batch = parse_and_validate_csv(sample_file)
        assert batch.total_source_rows > 0
        # Check rule P13: total_source_rows == loaded + quarantined + rejected
        assert batch.total_source_rows == batch.loaded_count + batch.quarantined_count + batch.rejected_count
        # Find check IMP-024
        check_24 = next(c for c in batch.checks if c.check_code == "IMP-024")
        assert check_24.status == "pass"


def test_parse_and_validate_malformed_date():
    malformed_file = Path("sample-data/malformed/malformed_date.csv")
    if malformed_file.exists():
        batch = parse_and_validate_csv(malformed_file)
        # Should have quarantined rows due to unparseable date
        assert batch.quarantined_count > 0
        assert any(q["reason_code"] == "import.dateUnparsed" for q in batch.quarantined_rows)
        # Equation source = loaded + quarantined + rejected must still hold
        assert batch.total_source_rows == batch.loaded_count + batch.quarantined_count + batch.rejected_count
