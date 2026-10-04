"""Database manager managing DuckDB and SQLite split per ADR-001, ADR-004 and ADR-007."""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional
import duckdb

DEFAULT_PROJECT_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / "FP&A Month-End Copilot" / "Projects" / "default"


AUTHORITATIVE_ACCOUNT_CODES = {
    '4000', '4100', '4200', '5000', '5100', '5200', '5300', '5400',
    '5450', '5500', '5600', '5800', '6100', '6300', '1999',
    '1010', '1200', '2000', '1020'
}


class DatabaseManager:
    """Encapsulates DuckDB analytics store and SQLite workflow state store."""

    def __init__(self, project_dir: Optional[Path] = None):
        env_dir = os.environ.get("FPA_PROJECT_DIR")
        if project_dir:
            self.project_dir = Path(project_dir)
        elif env_dir:
            self.project_dir = Path(env_dir)
        else:
            exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
            if (exe_dir / "portable.flag").exists():
                self.project_dir = exe_dir / "data" / "default"
            else:
                local_app_data = os.environ.get("LOCALAPPDATA")
                if local_app_data:
                    self.project_dir = Path(local_app_data) / "FP&A Month-End Copilot" / "Projects" / "default"
                else:
                    self.project_dir = Path.cwd() / "Projects" / "default"

        self.project_dir.mkdir(parents=True, exist_ok=True)

        self.duckdb_path = self.project_dir / "analytics.duckdb"
        self.sqlite_path = self.project_dir / "workflow.sqlite"

        self._init_sqlite()
        self._init_duckdb()

    def _init_sqlite(self) -> None:
        """Initialize SQLite workflow tables."""
        ddl_path = Path(__file__).parent / "schema_sqlite.sql"
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            if ddl_path.exists():
                conn.executescript(ddl_path.read_text(encoding="utf-8"))

            # Migration guard: Add newly added columns if FactException already existed
            batch_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(FactImportBatch);").fetchall()
            }
            if "balance_tolerance" not in batch_columns:
                conn.execute(
                    "ALTER TABLE FactImportBatch ADD COLUMN balance_tolerance "
                    "TEXT NOT NULL DEFAULT '0.00';"
                )

            cursor = conn.execute("PRAGMA table_info(FactException);")
            existing_cols = {row[1] for row in cursor.fetchall()}
            migrations = [
                ("owner_name", "TEXT"),
                ("period_id", "INTEGER"),
                ("subject_key", "TEXT"),
                ("subject_display", "TEXT"),
                ("amount_at_risk", "TEXT DEFAULT '0.00'"),
                ("effective_threshold", "TEXT"),
                ("evidence_refs", "TEXT"),
                ("sample_rows", "TEXT"),
                ("first_seen_date", "TEXT"),
                ("last_seen_date", "TEXT"),
                ("flagged_again", "INTEGER NOT NULL DEFAULT 0"),
            ]
            for col_name, col_type in migrations:
                if col_name not in existing_cols:
                    try:
                        conn.execute(f"ALTER TABLE FactException ADD COLUMN {col_name} {col_type};")
                    except Exception:
                        pass

    def _init_duckdb(self) -> None:
        """Initialize DuckDB analytics tables and seed baseline fiscal calendar."""
        ddl_path = Path(__file__).parent / "schema_duckdb.sql"
        try:
            conn = duckdb.connect(str(self.duckdb_path))
        except Exception:
            # If another connection holds the lock, try connecting in read-only or retry briefly
            try:
                conn = duckdb.connect(str(self.duckdb_path), read_only=True)
                conn.close()
                return
            except Exception:
                return

        try:
            if ddl_path.exists():
                conn.execute(ddl_path.read_text(encoding="utf-8"))
            # Seed default fiscal calendar for FY26
            conn.execute("""
                INSERT OR IGNORE INTO DimPeriod (period_id, fiscal_year, period_number, period_code, period_label, start_date, end_date)
                VALUES 
                (1, 2026, 1, 'FY26-P01', 'Jan-26', '2026-01-01', '2026-01-31'),
                (2, 2026, 2, 'FY26-P02', 'Feb-26', '2026-02-01', '2026-02-28'),
                (3, 2026, 3, 'FY26-P03', 'Mar-26', '2026-03-01', '2026-03-31'),
                (4, 2026, 4, 'FY26-P04', 'Apr-26', '2026-04-01', '2026-04-30'),
                (5, 2026, 5, 'FY26-P05', 'May-26', '2026-05-01', '2026-05-31'),
                (6, 2026, 6, 'FY26-P06', 'Jun-26', '2026-06-01', '2026-06-30'),
                (7, 2026, 7, 'FY26-P07', 'Jul-26', '2026-07-01', '2026-07-31'),
                (8, 2026, 8, 'FY26-P08', 'Aug-26', '2026-08-01', '2026-08-31'),
                (9, 2026, 9, 'FY26-P09', 'Sep-26', '2026-09-01', '2026-09-30'),
                (10, 2026, 10, 'FY26-P10', 'Oct-26', '2026-10-01', '2026-10-31'),
                (11, 2026, 11, 'FY26-P11', 'Nov-26', '2026-11-01', '2026-11-30'),
                (12, 2026, 12, 'FY26-P12', 'Dec-26', '2026-12-01', '2026-12-31');
            """)
            # Seed default company
            conn.execute("""
                INSERT OR IGNORE INTO DimCompany (company_id, company_code, company_name)
                VALUES (1, 'IN01', 'Alpha Industries Pvt Ltd');
            """)
            # Seed default accounts per 03_DATA_DICTIONARY and sample-data master
            conn.execute("""
                INSERT OR IGNORE INTO DimAccount (account_id, account_code, account_name, account_type, statement_line, favourability_direction)
                VALUES 
                (4000, '4000', 'Product Sales Revenue', 'revenue', 'Revenue', 'higher_is_favourable'),
                (4100, '4100', 'Consulting & Services Revenue', 'revenue', 'Revenue', 'higher_is_favourable'),
                (4200, '4200', 'Maintenance & Subscription Revenue', 'revenue', 'Revenue', 'higher_is_favourable'),
                (5000, '5000', 'Cost of Goods Sold - Hardware', 'expense', 'Cost of Goods Sold', 'lower_is_favourable'),
                (5100, '5100', 'Salaries & Direct Wages', 'expense', 'Cost of Goods Sold', 'lower_is_favourable'),
                (5200, '5200', 'Repairs and Maintenance', 'expense', 'Cost of Goods Sold', 'lower_is_favourable'),
                (5300, '5300', 'Travel & Entertainment', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (5400, '5400', 'Rent & Occupancy', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (5450, '5450', 'Contractor & Freelance Services', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (5500, '5500', 'Software & Cloud Subscriptions', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (5600, '5600', 'Office Supplies & Disposables', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (5800, '5800', 'Marketing Campaigns & Advertising', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (6100, '6100', 'Legal & Professional Fees (Accruals)', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (6300, '6300', 'Bank & Administrative Fees', 'expense', 'Operating Expenses', 'lower_is_favourable'),
                (1999, '1999', 'Suspense & Clearing Account', 'balance_sheet', 'Balance Sheet / Suspense', 'neutral'),
                -- DEF-026: counterpart accounts for the double-entry corpus (EXC-002 was firing on
                -- ~125,000 offsetting legs because these were absent from DimAccount).
                -- Names and types quoted from sample-data/generate_sample_data.py:52-54.
                (1010, '1010', 'Operating Bank Account', 'asset', 'Balance Sheet / Cash & Bank', 'neutral'),
                (1200, '1200', 'Accounts Receivable Trade', 'asset', 'Balance Sheet / Receivables', 'neutral'),
                (2000, '2000', 'Trade Accounts Payable', 'liability', 'Balance Sheet / Payables', 'neutral'),
                (1020, '1020', 'Bank Settlement Account', 'asset', 'Balance Sheet / Cash & Bank', 'neutral');
            """)
            # Seed default cost centers
            conn.execute("""
                INSERT OR IGNORE INTO DimCostCenter (cost_center_id, cost_center_code, cost_center_name, department_name)
                VALUES
                (100, 'CC-100', 'Executive & Management', 'Executive'),
                (110, 'CC-110', 'Product Development & Eng', 'Engineering'),
                (120, 'CC-120', 'Cloud Operations & IT', 'IT'),
                (130, 'CC-130', 'Direct Sales', 'Sales'),
                (140, 'CC-140', 'Marketing & Growth', 'Marketing'),
                (150, 'CC-150', 'Customer Support', 'Support'),
                (160, 'CC-160', 'Finance & Accounting', 'Finance'),
                (170, 'CC-170', 'People & HR', 'HR'),
                (180, 'CC-180', 'Legal & Compliance', 'Legal'),
                (190, 'CC-190', 'Facilities & Workplace', 'Facilities'),
                (999, 'CC-999', 'Unassigned Shared Pool', 'Unassigned');
            """)
        finally:
            conn.close()

    def get_duckdb_connection(self) -> duckdb.DuckDBPyConnection:
        """Get DuckDB connection for analytical queries with retry / fallback for concurrent locks."""
        import time
        for attempt in range(3):
            try:
                return duckdb.connect(str(self.duckdb_path))
            except Exception:
                if attempt == 2:
                    return duckdb.connect(str(self.duckdb_path), read_only=True)
                time.sleep(0.1)
        return duckdb.connect(str(self.duckdb_path), read_only=True)

    def get_sqlite_connection(self) -> sqlite3.Connection:
        """Get SQLite connection for workflow updates."""
        conn = sqlite3.connect(str(self.sqlite_path))
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def duckdb_conn(self) -> duckdb.DuckDBPyConnection:
        return self.get_duckdb_connection()

    @property
    def sqlite_conn(self) -> sqlite3.Connection:
        return self.get_sqlite_connection()
