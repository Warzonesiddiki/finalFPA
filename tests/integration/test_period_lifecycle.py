"""Regression tests for the period lifecycle (FR-PRJ-004 / FR-PRJ-005 / FR-PRJ-010).

DEFECT UNDER TEST. `PeriodRepository.open_period`, `close_period` and
`reopen_period` all raised before this was fixed, so the whole lifecycle was
unreachable:

    ConstraintException: NOT NULL constraint failed: PeriodAuditLog.log_id

`PeriodAuditLog.log_id` is `INTEGER PRIMARY KEY` with no IDENTITY and no
DEFAULT, and all three INSERTs omitted the column. The same class of defect
also hit `DimPeriod.period_id` in `open_period` and `PeriodSnapshot.snapshot_id`
in `close_period`, and `close_period` additionally selected a non-existent
`FactActual.amount` column.

Doc 03 §2.1 grain register, line 140, quoted:

    | `PeriodAuditLog` | One audit event for period close or snapshot action |
      `UNIQUE(audit_id)` (`period_repo.py:56`) |

Doc 02, quoted from the `period_repo` module docstring:

    FR-PRJ-004: New Period wizard (open period, source-load checklist, carry
      forward mappings/assumptions never numbers).
    FR-PRJ-005: Period close with immutable snapshot + typed reopen (audited).
    FR-PRJ-010: Period-close snapshot.

NOTE - doc/code divergence, flagged not fixed: doc 03 line 140 names the key
column `audit_id`; the code has always used `log_id`. Renaming a column is
outside this fix, so it is recorded here for the owner rather than changed
silently.

Doc 09 §3 (ADR-007) requires hand-written SQL with no ORM, and ADR-004 is the
single-user per-user data directory; both are why the key is allocated in Python
(see `PeriodRepository._next_id`).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import pytest

from app.engine.store.db import DatabaseManager
from app.engine.store.period_repo import PeriodRepository

# A fiscal year that is NOT in the FY26 seed, so the INSERT branch of
# `open_period` runs instead of the ON CONFLICT DO UPDATE branch.
NEW_FY = 2027
NEW_CODE = "FY27-P01"


@pytest.fixture()
def repo(tmp_path: Path) -> PeriodRepository:
    """A PeriodRepository over the throwaway project DB conftest already built."""
    return PeriodRepository(DatabaseManager())


def _audit_rows(repo: PeriodRepository) -> list:
    conn = repo.db.get_duckdb_connection()
    try:
        return conn.execute(
            "SELECT log_id, period_id, action, reason, performed_by "
            "FROM PeriodAuditLog ORDER BY log_id"
        ).fetchall()
    finally:
        conn.close()


def _insert_actual(repo: PeriodRepository, *, period_id: int, net_amount: str) -> None:
    """One minimal FactActual row; net_amount is what the close snapshot sums."""
    conn = repo.db.get_duckdb_connection()
    try:
        conn.execute(
            """
            INSERT INTO FactActual (actual_id, import_batch_id, row_fingerprint,
                company_id, account_id, period_id, posting_date, voucher_no,
                net_amount, source_file_name, source_row_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [900001, 1, f"fp-{period_id}-{net_amount}", 1, 5200, period_id,
             "2026-09-15", "VCH-TEST-001", net_amount, "unit_test.csv",
             "row_1"],
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# open_period
# ---------------------------------------------------------------------------

def test_open_period_creates_a_genuinely_new_period(repo: PeriodRepository):
    """FR-PRJ-004. A period_code absent from the seed must be created.

    Regression: `open_period` omitted `DimPeriod.period_id`, so this raised
    `NOT NULL constraint failed: DimPeriod.period_id`. The seeded FY26 periods
    hid the bug because their ON CONFLICT branch discards the value - which is
    why only a NEW fiscal year exposed it.
    """
    before = len(repo.list_periods())

    dto = repo.open_period(NEW_FY, 1, NEW_CODE, NEW_CODE,
                           "2027-01-01", "2027-01-31", {"carry": "maps"})

    assert dto is not None
    assert dto.period_code == NEW_CODE
    assert dto.fiscal_year == NEW_FY
    assert dto.status == "open"
    assert dto.start_date == "2027-01-01"
    assert dto.end_date == "2027-01-31"
    assert len(repo.list_periods()) == before + 1
    assert repo.get_period(dto.period_id) is not None


def test_open_period_writes_an_audit_row(repo: PeriodRepository):
    """Doc 03 §2.1: PeriodAuditLog holds one audit event per period action."""
    dto = repo.open_period(NEW_FY, 1, NEW_CODE, NEW_CODE,
                           "2027-01-01", "2027-01-31", {"carry": "maps"})

    rows = _audit_rows(repo)
    opens = [r for r in rows if r[2] == "open_wizard"]
    assert len(opens) == 1
    log_id, period_id, action, reason, performed_by = opens[0]
    assert period_id == dto.period_id
    assert action == "open_wizard"
    assert json.loads(reason) == {"carry": "maps"}
    assert performed_by == "system"
    assert isinstance(log_id, int)


def test_open_period_on_an_already_seeded_period(repo: PeriodRepository):
    """The ON CONFLICT branch must still reopen a period that already exists."""
    dto = repo.open_period(2026, 9, "FY26-P09", "FY26-P09",
                           "2026-09-01", "2026-09-30", {})

    assert dto.period_code == "FY26-P09"
    assert dto.status == "open"
    # Updating an existing period must not duplicate it.
    codes = [p.period_code for p in repo.list_periods()]
    assert codes.count("FY26-P09") == 1
    assert len(_audit_rows(repo)) == 1


# ---------------------------------------------------------------------------
# close_period
# ---------------------------------------------------------------------------

def test_close_period_snapshots_and_audits(repo: PeriodRepository):
    """FR-PRJ-005 / FR-PRJ-010: close writes an immutable snapshot + audit event."""
    _insert_actual(repo, period_id=9, net_amount="1000.00")

    dto = repo.close_period(9, closed_by="Aarti")

    assert dto.status == "closed"
    assert dto.closed_at is not None

    conn = repo.db.get_duckdb_connection()
    try:
        snaps = conn.execute(
            "SELECT snapshot_id, period_id, snapshot_json, snapshot_hash "
            "FROM PeriodSnapshot ORDER BY snapshot_id"
        ).fetchall()
    finally:
        conn.close()

    assert len(snaps) == 1
    snapshot_id, period_id, snapshot_json, snapshot_hash = snaps[0]
    assert isinstance(snapshot_id, int)
    assert period_id == 9
    # FR-PRJ-010 "immutable": the hash must verify against the stored JSON.
    assert snapshot_hash == hashlib.sha256(
        snapshot_json.encode("utf-8")).hexdigest()
    payload = json.loads(snapshot_json)
    assert payload["period_code"] == "FY26-P09"

    closes = [r for r in _audit_rows(repo) if r[2] == "close"]
    assert len(closes) == 1
    assert closes[0][1] == 9
    assert closes[0][4] == "Aarti"


def test_close_period_snapshot_totals_come_from_net_amount(repo: PeriodRepository):
    """Regression: close_period summed a non-existent `FactActual.amount`.

    `Binder Error: Referenced column "amount" not found in FROM clause!` made
    close unreachable before any key was involved. FactActual stores debit,
    credit and net_amount; net_amount is the amount column.
    """
    _insert_actual(repo, period_id=9, net_amount="1234.56")

    repo.close_period(9, closed_by="tester")

    conn = repo.db.get_duckdb_connection()
    try:
        snapshot_json = conn.execute(
            "SELECT snapshot_json FROM PeriodSnapshot"
        ).fetchone()[0]
    finally:
        conn.close()

    totals = json.loads(snapshot_json)["totals"]
    assert totals == {"5200": "1234.56"}


def test_close_period_raises_for_an_unknown_period(repo: PeriodRepository):
    with pytest.raises(ValueError, match="not found"):
        repo.close_period(9999, closed_by="tester")


# ---------------------------------------------------------------------------
# reopen_period
# ---------------------------------------------------------------------------

def test_reopen_period_requires_a_typed_reason(repo: PeriodRepository):
    """FR-PRJ-005 "typed reopen (audited)": a real reason is mandatory."""
    repo.close_period(9, closed_by="tester")

    with pytest.raises(ValueError, match="audit reason"):
        repo.reopen_period(9, "no", "tester")

    with pytest.raises(ValueError, match="audit reason"):
        repo.reopen_period(9, "   ", "tester")

    # The guard runs before any write, so the period is still closed.
    assert repo.get_period(9).status == "closed"


def test_reopen_period_reopens_and_audits(repo: PeriodRepository):
    repo.close_period(9, closed_by="tester")
    assert repo.get_period(9).status == "closed"

    dto = repo.reopen_period(9, "Restatement approved by CFO", "Aarti")

    assert dto.status == "open"
    assert dto.closed_at is None

    reopens = [r for r in _audit_rows(repo) if r[2] == "reopen"]
    assert len(reopens) == 1
    assert reopens[0][1] == 9
    assert reopens[0][3] == "Restatement approved by CFO"
    assert reopens[0][4] == "Aarti"


def test_full_open_close_reopen_cycle_leaves_one_audit_row_per_action(
    repo: PeriodRepository,
):
    """Doc 03: one audit event per period close or snapshot action."""
    repo.open_period(NEW_FY, 1, NEW_CODE, NEW_CODE,
                     "2027-01-01", "2027-01-31", {})
    period_id = repo.get_period(
        next(p.period_id for p in repo.list_periods() if p.period_code == NEW_CODE)
    ).period_id

    repo.close_period(period_id, closed_by="Aarti")
    repo.reopen_period(period_id, "Correcting a bad close", "Aarti")
    repo.close_period(period_id, closed_by="Aarti")

    actions = [r[2] for r in _audit_rows(repo)]
    assert actions == ["open_wizard", "close", "reopen", "close"]


# ---------------------------------------------------------------------------
# The keys themselves
# ---------------------------------------------------------------------------

def test_audit_log_ids_are_unique_and_monotonic(repo: PeriodRepository):
    """The defect was an omitted key; this pins that ids are now real and unique."""
    repo.open_period(NEW_FY, 1, NEW_CODE, NEW_CODE, "2027-01-01", "2027-01-31", {})
    period_id = repo.get_period(
        next(p.period_id for p in repo.list_periods() if p.period_code == NEW_CODE)
    ).period_id
    repo.close_period(period_id, closed_by="Aarti")
    repo.reopen_period(period_id, "Correcting a bad close", "Aarti")

    ids = [r[0] for r in _audit_rows(repo)]
    assert len(ids) == 3
    assert len(set(ids)) == 3, "audit log ids must be unique (doc 03 UNIQUE key)"
    assert ids == sorted(ids)


def test_next_id_starts_at_one_on_an_empty_table(repo: PeriodRepository):
    assert repo._next_id(repo.db.get_duckdb_connection(),
                         "PeriodAuditLog", "log_id") == 1


def test_duckdb_rejects_an_omitted_key_so_the_supplied_id_stays_load_bearing(
    repo: PeriodRepository,
):
    """Guard on the root cause, not just the symptom.

    If a future DuckDB release grows real auto-increment, or someone adds a
    DEFAULT to the DDL, this test starts failing and prompts a decision. Until
    then it documents why every INSERT in this module has to supply its key.
    """
    conn = repo.db.get_duckdb_connection()
    try:
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO PeriodAuditLog (period_id, action, reason, performed_by) "
                "VALUES (9, 'close', 'x', 'y')"
            )
        with pytest.raises(duckdb.ConstraintException):
            conn.execute(
                "INSERT INTO PeriodSnapshot (period_id, snapshot_json, snapshot_hash) "
                "VALUES (9, '{}', 'hash')"
            )
    finally:
        conn.close()