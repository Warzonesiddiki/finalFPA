import csv
import re
from pathlib import Path

import pytest

from app.engine.store.db import AUTHORITATIVE_ACCOUNT_CODES

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DATA_DIR = REPO_ROOT / "sample-data"


def get_sample_data_account_codes():
    csv_files = [
        "d365_gl_actuals.csv",
        "bank_ledger_actuals.csv",
        "payroll_procurement_actuals.csv",
    ]

    found_codes = set()

    for filename in csv_files:
        filepath = SAMPLE_DATA_DIR / filename
        assert filepath.is_file(), f"Required sample data file missing: {filepath}"

        with open(filepath, encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            if not lines:
                continue
            # Skip the first line if it's a comment
            if lines[0].startswith("#"):
                header = lines[1].split(",")
                content = lines[2:]
            else:
                header = lines[0].split(",")
                content = lines[1:]

            reader = csv.DictReader(content, fieldnames=header)

            # Find the account column
            account_col = None
            if "MainAccount" in header:
                account_col = "MainAccount"
            elif "AccountCode" in header:
                account_col = "AccountCode"

            if not account_col:
                continue

            for row in reader:
                found_codes.add(row[account_col])
    return found_codes


def get_expected_exceptions_account_codes():
    filepath = SAMPLE_DATA_DIR / "expected_exceptions.csv"
    assert filepath.is_file(), f"Required sample data file missing: {filepath}"
    account_codes = set()
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Subject keys have format 'account|CODE'
            if "subject_key" in row:
                subject_key = row["subject_key"]
                if "account|" in subject_key:
                    match = re.search(r"account\|([^|]+)", subject_key)
                    if match:
                        account_codes.add(match.group(1))
    return account_codes


def test_dim_account_invariants():
    corpus_codes = get_sample_data_account_codes()
    key_codes = get_expected_exceptions_account_codes()

    # 1. Corpus vs DimAccount
    missing_from_dim = corpus_codes - (AUTHORITATIVE_ACCOUNT_CODES | {"5999-TEMP"})
    assert not missing_from_dim, f"Corpus accounts missing from DimAccount: {missing_from_dim}"

    # 2. Answer key vs Corpus
    missing_from_corpus = key_codes - corpus_codes
    assert not missing_from_corpus, (
        f"Answer key accounts missing from corpus: {missing_from_corpus}"
    )

    # 3. 5999-TEMP must be absent from DimAccount
    assert "5999-TEMP" not in AUTHORITATIVE_ACCOUNT_CODES, (
        "5999-TEMP must be absent from DimAccount"
    )


if __name__ == "__main__":
    pytest.main([__file__])
