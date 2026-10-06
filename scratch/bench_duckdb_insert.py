"""Measure the FactActual insert path: duckdb executemany vs polars register.

Read-only w.r.t. the project: builds a throwaway database in %TEMP%.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import duckdb
import polars as pl

N = 50_000
DDL = """
CREATE TABLE FactActual (
    actual_id BIGINT, import_batch_id BIGINT, row_fingerprint VARCHAR,
    company_id BIGINT, account_id BIGINT, cost_center_id BIGINT,
    department_id BIGINT, project_id BIGINT, vendor_id BIGINT,
    period_id BIGINT, posting_date VARCHAR, document_date VARCHAR,
    voucher_no VARCHAR, document_no VARCHAR, invoice_no VARCHAR,
    line_no BIGINT, description VARCHAR, debit DECIMAL(18,2),
    credit DECIMAL(18,2), net_amount DECIMAL(18,2), currency_code VARCHAR,
    journal_category VARCHAR, source_system VARCHAR, source_file_name VARCHAR,
    source_row_ref VARCHAR, is_zero_amount BOOLEAN
)
"""
COLS = (
    "actual_id, import_batch_id, row_fingerprint, company_id, account_id, "
    "cost_center_id, department_id, project_id, vendor_id, period_id, "
    "posting_date, document_date, voucher_no, document_no, invoice_no, line_no, "
    "description, debit, credit, net_amount, currency_code, journal_category, "
    "source_system, source_file_name, source_row_ref, is_zero_amount"
)


def make_rows(n: int) -> list[tuple]:
    out = []
    for i in range(n):
        out.append((
            i, 1, f"FP-1-VCH-{i}-1", 1, 5000, 100, None, None, 7, 9,
            "2026-09-15", "2026-09-15", f"VCH-{i}", None, f"INV-{i}", 1,
            f"Line {i}", "1234.56", "0.00", "1234.56", "INR", None, "D365",
            "d365_gl_actuals.csv", f"row {i}", False,
        ))
    return out


def bench_executemany(con) -> float:
    rows = make_rows(N)
    t = time.perf_counter()
    con.executemany(
        f"INSERT INTO FactActual ({COLS}) VALUES ({', '.join(['?'] * 26)})", rows
    )
    return time.perf_counter() - t


def bench_append(con) -> float | str:
    """DuckDB native append() with a plain list of tuples."""
    rows = make_rows(N)
    t = time.perf_counter()
    try:
        con.append("FactActual", rows)
    except Exception as exc:  # noqa: BLE001
        return f"unsupported: {type(exc).__name__}: {exc}"
    return time.perf_counter() - t


def bench_batched(con, batch: int) -> float:
    """Multi-row parameterised VALUES, `batch` rows per statement."""
    rows = make_rows(N)
    single = "(" + ", ".join(["?"] * 26) + ")"
    t = time.perf_counter()
    for start in range(0, len(rows), batch):
        chunk = rows[start:start + batch]
        values = ", ".join([single] * len(chunk))
        params = [v for row in chunk for v in row]
        con.execute(
            f"INSERT INTO FactActual ({COLS}) VALUES {values}", params
        )
    return time.perf_counter() - t


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="fpa_bench_")) / "bench.duckdb"
    con = duckdb.connect(str(tmp))
    con.execute(DDL)
    r = bench_append(con)
    print("append            " + (f"{N:,} rows: {r:8.2f}s" if isinstance(r, float) else r))
    con.execute("DELETE FROM FactActual")
    for batch in (500, 1000, 2000):
        t = bench_batched(con, batch)
        print(f"batched(x{batch:<5}) {N:,} rows: {t:8.2f}s  ({N / t:,.0f} rows/s)")
        con.execute("DELETE FROM FactActual")
    n = con.execute("SELECT COUNT(*) FROM FactActual").fetchone()[0]
    print("rows landed:", n)
    con.close()


if __name__ == "__main__":
    main()
