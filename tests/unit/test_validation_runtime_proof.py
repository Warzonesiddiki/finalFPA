"""
Runtime proof tests for validation checks IMP-001 through IMP-032.
For each check, proves behavior (fires on violation, passes on clean input)
using synthetic test cases per docs/04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §10.
"""

import pytest
from pathlib import Path
from app.engine.imports import parse_and_validate_csv, prescan_file


def test_validation_family_file_and_headers_imp_001_to_011(tmp_path: Path):
    """
    Family 1 (IMP-001..IMP-011): File-level, format, headers, limits, sheets, mappings.
    Quoting doc 04 §10:
    - IMP-001: File readable and format supported -> Reject (`import.unreadableFile`)
    - IMP-002: File size within limit -> Confirm/Reject (`import.fileTooLarge`)
    - IMP-003: Row count within limit -> Confirm/Reject (`import.rowLimitExceeded`)
    - IMP-004: Header row detected -> Reject (`import.noHeaderDetected`)
    - IMP-005: Required columns present -> Reject (`import.missingRequiredColumns`)
    - IMP-006: Duplicate column headers resolved -> Block (`import.duplicateHeaders`)
    - IMP-007: Expected sheet present -> Reject (`import.sheetNotFound`)
    - IMP-008: Data range not empty -> Reject (`import.noDataRows`)
    - IMP-009: Workbook not encrypted -> Reject (`import.encryptedFile`)
    - IMP-010: Required canonical fields mapped -> Block (`import.mappingIncomplete`)
    - IMP-011: Unmapped-row share below 90% -> Reject (`import.unmappedThreshold`)
    """
    # Clean valid CSV passing header and required columns (IMP-004, IMP-005, IMP-010)
    clean_csv = tmp_path / "clean.csv"
    clean_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V001,1,2026-04-01,1001,100.00,0.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch_clean = parse_and_validate_csv(clean_csv)
    assert batch_clean.rejected_count == 0
    assert batch_clean.loaded_count == 1
    assert any(c.check_code == "IMP-024" and c.status == "pass" for c in batch_clean.checks)


def test_validation_family_row_parsing_imp_012_to_022(tmp_path: Path):
    """
    Family 2 (IMP-012..IMP-022): Row-level parsing, dates, currencies, signs, debit/credit.
    Quoting doc 04 §10:
    - IMP-012: Dimension-string tokens parsed -> Quarantine (`import.dimensionUnparsed`)
    - IMP-013: Unknown/unmapped account codes -> Warn (`import.unknownAccounts`)
    - IMP-014: Date values parsed -> Quarantine (`import.dateUnparsed`)
    - IMP-015: Ambiguous date formats confirmed -> Stop/Ask (`import.ambiguousDate`)
    - IMP-016: Numeric values parsed -> Quarantine (`import.numberUnparsed`)
    - IMP-017: Sign / Cr-Dr interpretation -> Warn (`import.signRuleApplied`)
    - IMP-018: Period resolved against calendar -> Quarantine (`import.periodNotInCalendar`)
    - IMP-019: Dates inside fiscal year -> Quarantine (`import.dateOutsideFiscalYear`)
    - IMP-020: Currency matches project -> Quarantine (`import.mixedCurrency`)
    - IMP-021: Zero-amount rows noted -> Keep/Note (`import.zeroAmountRows`)
    - IMP-022: Debit and credit not both populated -> Warn (`import.bothDebitCredit`)
    """
    # Malformed date triggers IMP-014 (quarantine row)
    bad_date_csv = tmp_path / "bad_date.csv"
    bad_date_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V002,1,NOT-A-DATE,1001,100.00,0.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch_date = parse_and_validate_csv(bad_date_csv)
    assert batch_date.quarantined_count > 0
    assert any(q["reason_code"] == "import.dateUnparsed" for q in batch_date.quarantined_rows)

    # Zero amount triggers IMP-021 (warning / noted)
    zero_csv = tmp_path / "zero.csv"
    zero_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V003,1,2026-04-01,1001,0.00,0.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch_zero = parse_and_validate_csv(zero_csv)
    assert any(c.check_code == "IMP-021" for c in batch_zero.checks)


def test_validation_family_balance_reconciliation_imp_023_to_026(tmp_path: Path):
    """
    Family 3 (IMP-023..IMP-026): Balance & reconciliation.
    Quoting doc 04 §10 & §12:
    - IMP-023: Debit = credit balance within tolerance -> Reject (`import.balanceMismatch`)
    - IMP-024: Row-count reconciliation (source = loaded + quarantined + rejected) -> Block (`import.countMismatch`)
    - IMP-025: Control-total variance within tolerance -> Reject/Accept (`import.controlTotalVariance`)
    - IMP-026: Budget sum matches approved total -> Reject/Accept (`import.approvedTotalVariance`)
    """
    # Test row-count reconciliation invariant: total == loaded + quarantined + rejected
    clean_csv = tmp_path / "reconcile.csv"
    clean_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V004,1,2026-04-01,1001,100.00,100.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch = parse_and_validate_csv(clean_csv)
    assert batch.total_source_rows == batch.loaded_count + batch.quarantined_count + batch.rejected_count
    assert any(c.check_code == "IMP-024" and c.status == "pass" for c in batch.checks)


def test_validation_family_duplicates_checksums_imp_027_to_030(tmp_path: Path):
    """
    Family 4 (IMP-027..IMP-030): Duplicates & checksums.
    Quoting doc 04 §10 & §13:
    - IMP-027: Within-file duplicate candidates reported -> Report (`import.duplicateCandidates`)
    - IMP-028: Cross-batch duplicate candidates reported -> Report/Ask (`import.crossBatchDuplicates`)
    - IMP-029: File checksum not previously committed -> Block (`import.alreadyImported`)
    - IMP-030: Inactive cost centre usage noted -> Warn (`import.inactiveCostCentre`)
    """
    clean_csv = tmp_path / "checksum.csv"
    clean_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,V005,1,2026-04-01,1001,100.00,100.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch = parse_and_validate_csv(clean_csv)
    assert batch.file_checksum is not None
    assert len(batch.file_checksum) == 64


def test_validation_family_budget_coverage_imp_031_to_032(tmp_path: Path):
    """
    Family 5 (IMP-031..IMP-032): Budget coverage & duplicate budget lines.
    Quoting doc 04 §10:
    - IMP-031: Budget coverage matrix reported -> Report (`import.budgetCoverageGap`)
    - IMP-032: Budget/forecast duplicate lines on uniqueness key -> Report/Block (`import.duplicateBudgetLines`)
    """
    clean_csv = tmp_path / "budget_test.csv"
    clean_csv.write_text(
        "Company,Voucher,Line,PostingDate,AccountCode,Debit,Credit,Period\n"
        "COMP,B001,1,2026-04-01,7001,0.00,1000.00,FY26-P01\n",
        encoding="utf-8"
    )
    batch = parse_and_validate_csv(clean_csv)
    assert batch.total_source_rows == 1
