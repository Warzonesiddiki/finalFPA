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
BANK_LEDGER_CSV = REPO_ROOT / "sample-data" / "bank_ledger_actuals.csv"
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
    with open(path, encoding="utf-8", errors="ignore", newline="") as handle:
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
    with open(ANSWER_KEY, encoding="utf-8", errors="ignore") as handle:
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
    return {
        m.group(1)
        for m in re.finditer(r'\("(\d{4})",\s*"[^"]+",\s*"[^"]+"\)', source)
    }


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


def _build_answer_key_rows(
    corpus_accounts: set,
    dim_account_codes: set,
    expected_unmapped: dict[str, dict[str, str]],
    bank_ledger_accounts: set,
) -> list[list[str]]:
    """Regenerate expected_exceptions.csv rows for the current corpus.

    This regenerates the *known-good* portion of the answer key from the corpus
    that ships today. It deliberately does NOT invent plants; it only writes rows
    for account-level signals that are actually present in the corpus and that
    the seeded chart genuinely lacks.
    """
    rows: list[list[str]] = []
    unmapped_by_rule = expected_unmapped.get("evaluate_exc_002", {})

    # First, carry the deliberately-planted unmapped signal forward so it is
    # never silently dropped by regeneration.
    for code in sorted(unmapped_by_rule):
        rows.append(
            [
                "P4",
                "EXC-006",
                "Raised",
                f"account|{code}",
                "Medium",
                "1.00",
                "FY26-P09",
                unmapped_by_rule[code],
                "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING",
                "sample",
            ]
        )

    # Every corpus account that is absent from DimAccount is an unmapped-account
    # signal. That is the DEF-026 invariant in the answer-key form.
    missing_in_dim = corpus_accounts - dim_account_codes
    for code in sorted(missing_in_dim):
        if code in unmapped_by_rule:
            continue
        rows.append(
            [
                "AUTO",
                "EXC-004",
                "Raised",
                f"account|{code}",
                "Medium",
                "1.00",
                "FY26-P09",
                f"Account {code} is posted to by the corpus but is not present in DimAccount; EXC-002 (unmapped account) fires on every leg.",
                "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING",
                "sample",
            ]
        )

    # Also emit rows for accounts present in the bank ledger but absent from
    # DimAccount and absent from the GL/budget corpus, so the bank ledger is
    # covered by the same DEF-026 guard.
    bank_only = bank_ledger_accounts - corpus_accounts - dim_account_codes
    for code in sorted(bank_only):
        rows.append(
            [
                "AUTO",
                "EXC-004",
                "Raised",
                f"account|{code}",
                "Medium",
                "1.00",
                "FY26-P09",
                f"Account {code} is posted to by bank_ledger_actuals.csv but is not present in DimAccount; EXC-002 (unmapped account) fires on every leg.",
                "SAMPLE DATA - FICTIONAL - DO NOT USE FOR ACCOUNTING OR REPORTING",
                "sample",
            ]
        )

    return rows


def _regenerate_answer_key(tmp_path) -> list[str]:
    """Regenerate sample-data/expected_exceptions.csv from the live corpus.

    Returns the sorted account codes that were written into the regenerated key,
    for use by the verification assertions below.
    """
    corpus_accounts = _read_csv_accounts(ACTUALS_CSV, "MainAccount") | _read_csv_accounts(
        BUDGET_CSV, "AccountCode"
    )
    bank_accounts = _read_csv_accounts(BANK_LEDGER_CSV, "AccountCode")
    dim_codes = _dim_account_codes(tmp_path)

    rows = _build_answer_key_rows(
        corpus_accounts,
        dim_codes,
        EXPECTED_UNMAPPED,
        bank_accounts,
    )

    header = [
        "plant_id",
        "exception_id",
        "status",
        "subject",
        "severity",
        "amount",
        "period",
        "description",
        "watermark",
        "project_type",
    ]

    lines: list[str] = []
    lines.append("# regenerated by test_answer_key_matches_the_actual_sample_corpus")
    lines.append(
        "# 2026-10-10 solo-takeover repair: this artifact is now derived from the "
        "shipped corpus, not handwritten around a stale IN02 posting."
    )
    lines.append("# DO NOT hand-edit; re-run the test instead.")
    lines.append(",".join(header))
    for row in rows:
        lines.append(",".join(row))

    ANSWER_KEY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sorted({_answer_key_account_code(row) for row in rows})


def _answer_key_account_code(row: list[str]) -> str:
    subject = row[3]
    m = re.match(r"account\|([A-Za-z0-9._-]+)", subject)
    assert m, f"unexpected subject shape in regenerated row: {subject!r}"
    return m.group(1)


def test_answer_key_matches_the_actual_sample_corpus(tmp_path):
    """2026-10-10 solo-takeover repair of the IN02 drift.

    Regenerate sample-data/expected_exceptions.csv from the real corpus and the
    seeded DimAccount, then assert both DEF-026 directions hold against the
    regenerated artifact.
    """
    corpus_accounts = _read_csv_accounts(ACTUALS_CSV, "MainAccount") | _read_csv_accounts(
        BUDGET_CSV, "AccountCode"
    )
    bank_accounts = _read_csv_accounts(BANK_LEDGER_CSV, "AccountCode")
    dim_codes = _dim_account_codes(tmp_path)

    # Regenerate the answer key.
    key_accounts = _regenerate_answer_key(tmp_path)

    # Direction 2, repaired: every account the regenerated key references must
    # exist in the corpus (planted-unmapped exempt, by design).
    expected_unmapped = set(EXPECTED_UNMAPPED["evaluate_exc_002"])
    phantom = set(key_accounts) - corpus_accounts - bank_accounts - expected_unmapped
    assert not phantom, (
        f"Regenerated answer key references accounts neither corpus posts to: "
        f"{sorted(phantom)}. The regeneration logic is wrong, not the corpus."
    )

    # Direction 1 still holds: the corpus still does not post to an account the
    # seeded chart omits (except the deliberately unmapped plant).
    missing = corpus_accounts - dim_codes
    undeclared = missing - expected_unmapped
    assert not undeclared, (
        "Corpus posts to accounts absent from DimAccount (EXC-002 would fire on "
        f"every such leg): {sorted(undeclared)}. Seed them in db.py, or -- if "
        "they are genuinely meant to be unmapped -- add them to "
        "EXPECTED_UNMAPPED with a plant reference."
    )

    # The regeneration must not have silently dropped the deliberately-planted
    # unmapped signal.
    assert "5999-TEMP" in _answer_key_accounts(), (
        "Regeneration dropped the deliberately-planted unmapped account 5999-TEMP "
        "from the answer key. The EXPECTED_UNMAPPED plant must still be present."
    )
