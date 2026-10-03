"""Minimal DimVendor + FactBudget CSV loader tests.

Quotes under test (docs/19 §5.1 quote-before-code):
- docs/03 §2.1: "`DimVendor` | One supplier as seen in the source |
  `UNIQUE(vendor_code)`"; "`FactBudget` | One budget line at version x scenario
  x period x account x dimensions | `UNIQUE(budget_version, scenario_code,
  period_id, account_id, company_id, cost_center_id, project_id)`".
- docs/04 §11: row-level failure quarantines the row, never drops it; and §10
  `IMP-032`: conflicting duplicates (same key, different amount) block the
  commit while exact duplicates de-duplicate with a recorded count.
- docs/04 §15: commit is a single transaction -- rollback on any error, batch
  recorded `rejected`, no partial facts.
- docs/06 EXC-014 subject key `vendor_code|account_code`: the vendor dimension
  this loader populates is what the vendor-keyed rules join on.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from app.engine.imports.vendor_budget_loader import (
    BudgetCommitBlocked,
    commit_budget_csv,
    commit_vendor_csv,
    parse_budget_csv,
    parse_vendor_csv,
)
from app.engine.store.db import DatabaseManager


VENDOR_CSV = """VendorCode,VendorName,Category
V-00276,Staffing Services Ltd,Staffing
V-00931,Sunrise Facilities LLP,Facilities
V-00412,City Power Utility,Utilities
"""

VENDOR_CSV_MISSING_CODE = """VendorCode,VendorName
V-00276,Staffing Services Ltd
,No Code Vendor
"""

VENDOR_CSV_CONFLICT = """VendorCode,VendorName
V-00276,Staffing Services Ltd
V-00276,A Different Name Ltd
V-00276,Staffing Services Ltd
"""

BUDGET_CSV = """PeriodCode,EntityCode,CostCenterCode,AccountCode,BudgetAmount
FY26-P09,IN01,CC-100,5200,1000000.00
FY26-P09,IN01,CC-110,5300,500000.00
"""

BUDGET_CSV_BAD_ROWS = """PeriodCode,EntityCode,CostCenterCode,AccountCode,BudgetAmount
FY26-P09,IN01,CC-100,5200,1000000.00
NOT-A-PERIOD,IN01,CC-100,5200,100.00
FY26-P09,IN01,CC-100,5300,not-a-number
FY26-P09,IN01,CC-100,9999,10.00
"""

BUDGET_CSV_EXACT_DUPES = """PeriodCode,EntityCode,CostCenterCode,AccountCode,BudgetAmount
FY26-P09,IN01,CC-100,5200,1000000.00
FY26-P09,IN01,CC-100,5200,1000000.00
"""

BUDGET_CSV_CONFLICT = """PeriodCode,EntityCode,CostCenterCode,AccountCode,BudgetAmount
FY26-P09,IN01,CC-100,5200,1000000.00
FY26-P09,IN01,CC-100,5200,2000000.00
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _duck_counts(db: DatabaseManager, table: str) -> int:
    conn = db.get_duckdb_connection()
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def _batch_row(db: DatabaseManager, batch_id: int) -> dict:
    conn = db.get_sqlite_connection()
    try:
        row = conn.execute(
            "SELECT * FROM FactImportBatch WHERE batch_id = ?", (batch_id,)).fetchone()
        assert row is not None
        return dict(row)
    finally:
        conn.close()


# --- DimVendor -------------------------------------------------------------

def test_vendor_happy_path_populates_dim_vendor(tmp_path):
    db = DatabaseManager(project_dir=tmp_path / "proj")
    res = commit_vendor_csv(db, _write(tmp_path, "vendors.csv", VENDOR_CSV))
    assert res.status == "committed"
    assert res.loaded_count == 3 and res.quarantined_count == 0
    conn = db.get_duckdb_connection()
    try:
        rows = conn.execute(
            "SELECT vendor_code, vendor_name, source FROM DimVendor ORDER BY vendor_code").fetchall()
    finally:
        conn.close()
    assert [(r[0], r[1]) for r in rows] == [
        ("V-00276", "Staffing Services Ltd"),
        ("V-00412", "City Power Utility"),
        ("V-00931", "Sunrise Facilities LLP"),
    ]
    assert all(r[2] == "imported" for r in rows)
    batch = _batch_row(db, res.batch_id)
    assert batch["source_type"] == "vendor_master" and batch["status"] == "committed"
    assert batch["total_source_rows"] == batch["loaded_count"] == 3


def test_vendor_missing_code_quarantined_never_dropped(tmp_path):
    db = DatabaseManager(project_dir=tmp_path / "proj")
    res = commit_vendor_csv(db, _write(tmp_path, "v.csv", VENDOR_CSV_MISSING_CODE))
    assert res.loaded_count == 1 and res.quarantined_count == 1
    assert res.quarantined_rows[0]["reason_code"] == "import.vendorCodeMissing"
    assert _duck_counts(db, "DimVendor") == 1


def test_vendor_name_conflict_quarantined_exact_dupe_deduped(tmp_path):
    valid, quarantined = parse_vendor_csv(_write(tmp_path, "v.csv", VENDOR_CSV_CONFLICT))
    assert len(valid) == 1
    assert any(q["reason_code"] == "import.vendorNameConflict" for q in quarantined)
    db = DatabaseManager(project_dir=tmp_path / "proj")
    res = commit_vendor_csv(db, _write(tmp_path, "v2.csv", VENDOR_CSV_CONFLICT))
    assert res.loaded_count == 1 and res.quarantined_count == 1
    assert _duck_counts(db, "DimVendor") == 1


def test_vendor_reload_is_idempotent(tmp_path):
    db = DatabaseManager(project_dir=tmp_path / "proj")
    path = _write(tmp_path, "vendors.csv", VENDOR_CSV)
    commit_vendor_csv(db, path)
    res2 = commit_vendor_csv(db, path)
    assert res2.status == "committed"
    assert _duck_counts(db, "DimVendor") == 3  # UNIQUE(vendor_code): no duplicates


def test_vendor_keyed_rule_dependency_joinable(tmp_path):
    """EXC-014 subject key is `vendor_code|account_code`: the rule needs the
    vendor dimension row to exist for the planted vendor V-00276."""
    db = DatabaseManager(project_dir=tmp_path / "proj")
    commit_vendor_csv(db, _write(tmp_path, "vendors.csv", VENDOR_CSV))
    conn = db.get_duckdb_connection()
    try:
        row = conn.execute(
            "SELECT vendor_id FROM DimVendor WHERE vendor_code = 'V-00276'").fetchone()
    finally:
        conn.close()
    assert row is not None and row[0] is not None


# --- FactBudget ------------------------------------------------------------

def test_budget_happy_path_with_fk_resolution(tmp_path):
    db = DatabaseManager(project_dir=tmp_path / "proj")
    res = commit_budget_csv(db, _write(tmp_path, "b.csv", BUDGET_CSV))
    assert res.status == "committed"
    assert res.loaded_count == 2 and res.quarantined_count == 0
    conn = db.get_duckdb_connection()
    try:
        rows = conn.execute(
            "SELECT budget_version, scenario_code, company_id, account_id, "
            "cost_center_id, period_id, amount FROM FactBudget ORDER BY account_id").fetchall()
    finally:
        conn.close()
    assert rows[0][:6] == ("FY26-Approved", "base", 1, 5200, 100, 9)
    assert rows[0][6] == Decimal("1000000.00")
    assert rows[1][6] == Decimal("500000.00")
    batch = _batch_row(db, res.batch_id)
    assert batch["source_type"] == "budget" and batch["status"] == "committed"
    assert batch["total_source_rows"] == 2


def test_budget_bad_rows_quarantined_per_imp016_imp018_and_unknown_dims(tmp_path):
    db = DatabaseManager(project_dir=tmp_path / "proj")
    res = commit_budget_csv(db, _write(tmp_path, "b.csv", BUDGET_CSV_BAD_ROWS))
    assert res.status == "committed"
    assert res.loaded_count == 1 and res.quarantined_count == 3
    codes = {q["reason_code"] for q in res.quarantined_rows}
    assert "import.periodNotInCalendar" in codes      # NOT-A-PERIOD (IMP-018)
    assert "import.numberUnparsed" in codes           # not-a-number (IMP-016)
    assert "import.unknownDimensions" in codes        # account 9999 (03 §7 I12)
    assert _duck_counts(db, "FactBudget") == 1


def test_budget_exact_duplicates_deduped(tmp_path):
    db = DatabaseManager(project_dir=tmp_path / "proj")
    res = commit_budget_csv(db, _write(tmp_path, "b.csv", BUDGET_CSV_EXACT_DUPES))
    assert res.status == "committed" and res.loaded_count == 1
    assert _duck_counts(db, "FactBudget") == 1
    assert any(c.check_code == "IMP-032" for c in res.checks)


def test_budget_conflicting_duplicates_block_commit_atomically(tmp_path):
    """IMP-032: same key, different amount blocks the commit; the batch is
    recorded `rejected` and zero facts are written (docs/04 §15)."""
    db = DatabaseManager(project_dir=tmp_path / "proj")
    with pytest.raises(BudgetCommitBlocked):
        commit_budget_csv(db, _write(tmp_path, "b.csv", BUDGET_CSV_CONFLICT))
    assert _duck_counts(db, "FactBudget") == 0
    conn = db.get_sqlite_connection()
    try:
        batches = conn.execute("SELECT status FROM FactImportBatch").fetchall()
    finally:
        conn.close()
    assert len(batches) == 1 and batches[0][0] == "rejected"


def test_budget_money_exact_no_float(tmp_path):
    """docs/03 §1.2: floats forbidden in money paths -- 0.1+0.2 style values
    persist exactly."""
    db = DatabaseManager(project_dir=tmp_path / "proj")
    csv_text = ("PeriodCode,EntityCode,CostCenterCode,AccountCode,BudgetAmount\n"
                "FY26-P09,IN01,CC-100,5200,123456.78\n")
    res = commit_budget_csv(db, _write(tmp_path, "b.csv", csv_text))
    assert res.loaded_count == 1
    conn = db.get_duckdb_connection()
    try:
        amt = conn.execute("SELECT amount FROM FactBudget").fetchone()[0]
    finally:
        conn.close()
    assert amt == Decimal("123456.78")
