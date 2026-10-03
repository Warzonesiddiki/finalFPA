"""DEF-026: corpus <-> DimAccount integrity.

DEF-026 root cause: the seeded chart of accounts (`app/engine/store/db.py`)
omitted three balance-sheet counterpart accounts that the double-entry sample
corpus posts to -- 1010, 1200, 2000. EXC-002 (unmapped account) therefore fired
on every offsetting leg (~125,000 rows) and the engine read as catastrophically
broken when the real fault was that the corpus posted to accounts the chart did
not define. No test caught it: the committed corpus only used the original 15
accounts, so every assertion in the suite was consistent with the defect.

This module encodes both directions of the invariant, because each catches a
different failure:

  1. every account code the corpus posts to must exist in DimAccount
     (catches a missing seeded account)
  2. every account the ANSWER KEY references must exist in the corpus, and every
     PLANTED-UNMAPPED account must be ABSENT from DimAccount
     (catches the corpus and the answer key drifting apart)

The planted-unmapped set is keyed on the ENGINE rule id, not the catalog id.
Catalog EXC-004 is "Unmapped Account" but the engine implements it as
`evaluate_exc_002`; that catalog-vs-engine offset silently moved rule recall
from 25.0% to 9.4% earlier in this project, so keying the allow-list on the
catalog id would silently disable this check.

Planted-unmapped accounts are recorded as EXPECTED-UNMAPPED entries carrying
their plant reference -- never as a silent exclusion. A silent exclusion would
mean that deleting plant P4 from the answer key left this test green, i.e. the
check would lose the ability to detect the very divergence it exists to catch.
"""

import csv
import re
from pathlib import Path

import pytest

from app.engine.store.db import DatabaseManager

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTUALS_CSV = REPO_ROOT / "sample-data" / "d365_gl_actuals.csv"
BUDGET_CSV = REPO_ROOT / "sample-data" / "budget_fy26.csv"
ANSWER_KEY = REPO_ROOT / "sample-data" / "expected_exceptions.csv"
GENERATOR = REPO_ROOT / "sample-data" / "generate_sample_data.py"

# Accounts deliberately left unmapped so an exception fires on them.
# engine_rule_id -> {account_code: why it is expected to be unmapped}
EXPECTED_UNMAPPED = {
    "evaluate_exc_002": {
        "5999-TEMP": (
            "plant P4 in expected_exceptions.csv: 6 rows post to unmapped "
            "placeholder 5999-TEMP so the unmapped-account exception fires. "
            "Catalog calls this EXC-004; the engine implements it as "
            "evaluate_exc_002."
        ),
    },
}


def _read_csv_accounts(path: Path, column: str) -> set:
    """Account codes in `column`, skipping the '# ...' comment preamble."""
    accounts = set()
    with open(path, mode="r", encoding="utf-8", errors="ignore", newline="") as handle:
        for row in csv.DictReader(handle):
            value = (row.get(column) or "").strip()
            if value and not value.startswith("#"):
                accounts.add(value)
    return accounts


def _dim_account_codes(tmp_path) -> set:
    db_mgr = DatabaseManager(tmp_path)
    conn = db_mgr.get_duckdb_connection()
    try:
        return {row[0] for row in conn.execute("SELECT account_code FROM DimAccount").fetchall()}
    finally:
        conn.close()


def _answer_key_accounts() -> set:
    """Account codes the answer key references, via 'account|CODE' subject keys.

    Cost-centre references ('cost_center|CC-999') are deliberately excluded --
    they are validated against DimCostCenter, not DimAccount.
    """
    pattern = re.compile(r"account\|([A-Za-z0-9._-]+)")
    found = set()
    with open(ANSWER_KEY, mode="r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.lstrip().startswith("#"):
                continue
            found.update(pattern.findall(line))
    return found


@pytest.fixture
def corpus_accounts() -> set:
    return _read_csv_accounts(ACTUALS_CSV, "MainAccount") | _read_csv_accounts(
        BUDGET_CSV, "AccountCode"
    )


def _generator_declared_accounts() -> set:
    """Account codes the corpus generator declares in its chart table.

    `sample-data/generate_sample_data.py` is the committed source of truth for
    what the corpus WILL post to. Checking the generated CSV alone is not
    sufficient: the committed CSV predates DEF-026 and does not yet contain
    1010/1200/2000, so a CSV-only check cannot detect a missing seed until after
    the corpus has been regenerated -- at which point the omission has already
    shipped. Reading the generator's declared chart closes that window.
    """
    source = GENERATOR.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r'\("(\d{4})",\s*"[^"]+",\s*"[^"]+"\)', source))


def test_generator_chart_is_fully_seeded_in_dimaccount(tmp_path):
    """The generator's declared chart must be a subset of the seeded chart.

    This is the check that actually catches DEF-026: it reads the committed
    generator, so it fails the moment an account is dropped from the seed --
    without waiting for a corpus regeneration to reveal it.
    """
    dim_codes = _dim_account_codes(tmp_path)
    declared = _generator_declared_accounts()
    assert declared, (
        "Could not parse any account codes from "
        "sample-data/generate_sample_data.py -- the chart-table format changed "
        "and this test would pass vacuously. Update _generator_declared_accounts."
    )

    missing = declared - dim_codes
    assert not missing, (
        f"Corpus generator declares accounts absent from DimAccount: "
        f"{sorted(missing)}. EXC-002 (unmapped account) will fire on every leg "
        f"the generator posts to them. Seed them in db.py."
    )


def test_every_corpus_account_is_seeded_in_dimaccount(tmp_path, corpus_accounts):
    """Direction 1: the corpus must not post to an account the chart omits."""
    dim_codes = _dim_account_codes(tmp_path)
    expected_unmapped = set(EXPECTED_UNMAPPED["evaluate_exc_002"])

    missing = corpus_accounts - dim_codes
    undeclared = missing - expected_unmapped
    assert not undeclared, (
        "Corpus posts to accounts absent from DimAccount (EXC-002 would fire on "
        f"every such leg): {sorted(undeclared)}. Seed them in db.py, or -- if "
        "they are genuinely meant to be unmapped -- add them to "
        "EXPECTED_UNMAPPED with a plant reference. Undeclared-but-expected: "
        f"{sorted(missing & expected_unmapped)}."
    )


def test_planted_unmapped_accounts_are_actually_unmapped(tmp_path):
    """Direction 2: a plant that stops firing must fail loudly, not silently.

    If someone seeds 5999-TEMP, planting P4 stops producing its exception, and
    the answer key starts lying about what the engine will report. This test
    turns that divergence into a red build.
    """
    dim_codes = _dim_account_codes(tmp_path)
    for engine_rule_id, accounts in EXPECTED_UNMAPPED.items():
        for code, reason in accounts.items():
            assert code not in dim_codes, (
                f"{code} is seeded in DimAccount, so {engine_rule_id} can no "
                f"longer fire on it. Expected-unmapped by design: {reason} Either "
                "revert the seed or remove the plant from the answer key -- but "
                "do not leave the corpus and the key disagreeing."
            )


def test_answer_key_accounts_exist_in_the_corpus(tmp_path, corpus_accounts):
    """Direction 2 (cont): the key must not reference accounts the corpus lacks.

    Together with test_planted_unmapped_accounts_are_actually_unmapped this
    closes the loop: a missing seed and a removed plant are both red.
    """
    key_accounts = _answer_key_accounts()
    expected_unmapped = set(EXPECTED_UNMAPPED["evaluate_exc_002"])

    # Planted-unmapped accounts are referenced by the key by design; they are
    # checked against DimAccount above, not against the corpus account list.
    phantom = key_accounts - corpus_accounts - expected_unmapped
    assert not phantom, (
        f"Answer key references accounts the corpus does not post to: "
        f"{sorted(phantom)}. The key and the corpus have drifted apart."
    )
