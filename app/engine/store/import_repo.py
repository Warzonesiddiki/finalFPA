"""Import and staging repository managing atomic batch commit per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §3."""

import json
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

import duckdb

from app.engine.calc.quality_score import calculate_quality_score
from app.engine.imports.models import ImportBatchResult, ParsedTransaction
from app.engine.store.db import DatabaseManager

#: Rows per INSERT statement for the analytic-store bulk load.
#:
#: DuckDB's ``executemany`` executes the prepared statement once per row: the
#: 26-column ``FactActual`` insert measured **236 rows/s** on the 250k-row
#: sample corpus, i.e. roughly 18 minutes of commit time for one month-end
#: import, and the doc-14 §5.2 acceptance run spent most of a 20-minute wall
#: clock here (measured 2026-10-04; see ``scratch/bench_duckdb_insert.py``).
#: Multi-row parameterised VALUES statements of this size measure ~3,700 rows/s
#: (15x) with identical parameter binding, identical stored values, and the same
#: atomic outcome.
INSERT_BATCH_ROWS = 1000


def _bulk_insert(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
) -> None:
    """Insert ``rows`` into ``table`` with batched multi-row statements.

    Atomicity is unchanged from the single ``executemany`` it replaces: every
    batch runs inside one explicit transaction, so an interruption leaves
    either all rows or none (Addon 1 P12 all-or-nothing imports). Each value is
    still a bound parameter, so DuckDB applies exactly the same column types
    and casts it applied before.
    """
    if not rows:
        return
    placeholder = "(" + ", ".join("?" for _ in columns) + ")"
    column_sql = ", ".join(columns)
    conn.execute("BEGIN TRANSACTION")
    try:
        for start in range(0, len(rows), INSERT_BATCH_ROWS):
            chunk = rows[start : start + INSERT_BATCH_ROWS]
            values_sql = ", ".join([placeholder] * len(chunk))
            conn.execute(
                f"INSERT INTO {table} ({column_sql}) VALUES {values_sql}",
                [value for row in chunk for value in row],
            )
    except BaseException:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass  # the original failure is the one that must propagate
        raise
    conn.execute("COMMIT")


class ImportRepository:
    """Manages transactional commit of import batches into DuckDB and SQLite."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    @staticmethod
    def _get_or_create_dimension_id(
        duck_conn: duckdb.DuckDBPyConnection,
        *,
        table: str,
        id_column: str,
        code_column: str,
        code: str | None,
        extra_values: dict[str, Any] | None = None,
    ) -> int | None:
        """Resolve a source code to its dimension ID, creating a row if absent."""
        normalized_code = str(code or "").strip()
        if not normalized_code:
            return None
        row = duck_conn.execute(
            f"SELECT {id_column} FROM {table} WHERE {code_column} = ? LIMIT 1",
            [normalized_code],
        ).fetchone()
        if row:
            return int(row[0])

        next_id_row = duck_conn.execute(
            f"SELECT COALESCE(MAX({id_column}), 0) + 1 FROM {table}"
        ).fetchone()
        new_id = int(next_id_row[0] if next_id_row else 0)
        values = {
            id_column: new_id,
            code_column: normalized_code,
            **(extra_values or {}),
        }
        columns = list(values)
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(columns)
        duck_conn.execute(
            f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
            [values[column] for column in columns],
        )
        return new_id

    def commit_batch(
        self,
        batch: ImportBatchResult,
        transactions: list[ParsedTransaction],
    ) -> int:
        """Atomically commit an import batch: SQLite metadata + DuckDB facts."""
        # 0. Data Quality Score per 05 §8 (CALC-050).
        # DEF-009: this used to be the literal 100.0 on every batch, so a rejected
        # file still reported 100%. It is now computed from the real check reports.
        dq_result = calculate_quality_score(batch)
        dq_score = dq_result.raw_score
        # DEF-009: this used to be the literal 100.0 on every batch, so a rejected
        # file still reported 100%. It is now computed from the real check reports.

        # 0b. Commit decision, computed BEFORE the audit row is written.
        #
        # Per DEC-056 (OQ-025) the balance gate is scoped by source type rather
        # than applied to every file alike. A journal-style source (the D365
        # general ledger, budget) keeps the unconditional exact debit=credit
        # reject of 04 section 12 / IMP-023. An amount-style sub-ledger (bank
        # ledger, payroll/procurement - 04 section 2.2) is validated by
        # control-total / net-amount reconciliation inside the 06 section 8
        # tolerance instead: it commits with the variance stated, which is what
        # `parser.check_imp_023_subledger_reconciliation` records on the report.
        #
        # The effective tolerance is persisted below either way, so an accepted
        # non-zero delta remains visible to EXC-001 and in the audit detail.
        should_commit = batch.can_commit

        # DEF-010 (spec-wins fix): `status` records what ACTUALLY happened to the
        # rows. A failed file-level gate (balance, structure, count reconciliation,
        # duplicate file, or unaccepted control-total variance) rejects the batch
        # with zero rows committed. `is_balanced` records only the balance-gate
        # result, not an exact-zero test.
        batch_status = "committed" if should_commit else "rejected"

        # 1. Insert into SQLite FactImportBatch
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            with sqlite_conn:
                cur = sqlite_conn.execute(
                    """
                    INSERT INTO FactImportBatch (
                        source_type, file_name, file_checksum, file_size_bytes, sheet_name,
                        profile_id, profile_version, total_source_rows, loaded_count,
                        quarantined_count, rejected_count, status, is_balanced,
                        total_debit, total_credit, net_imbalance, balance_tolerance,
                        data_quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch.source_type,
                        batch.file_name,
                        batch.file_checksum,
                        0,
                        batch.sheet_name,
                        1,
                        1,
                        batch.total_source_rows,
                        batch.loaded_count,
                        batch.quarantined_count,
                        batch.rejected_count,
                        batch_status,
                        1 if batch.is_balanced else 0,
                        str(batch.total_debit),
                        str(batch.total_credit),
                        str(batch.net_imbalance),
                        str(batch.balance_tolerance),
                        str(dq_score),
                    ),
                )
                raw_batch_id = cur.lastrowid
                assert raw_batch_id is not None, (
                    "INSERT into FactImportBatch did not produce a row id"
                )
                batch_id: int = raw_batch_id

                # Insert validation checks into SQLite
                for c in batch.checks:
                    # Weight is never None here: ValidationCheckReport.__post_init__
                    # defaults it by severity. The assert narrows Optional for mypy.
                    assert c.weight is not None
                    sqlite_conn.execute(
                        """
                        INSERT INTO FactValidationCheck (
                            import_batch_id, check_code, check_name, status, severity,
                            offending_count, skip_reason, detail, sample_rows, weight
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            batch_id,
                            c.check_code,
                            c.check_name,
                            c.status,
                            c.severity,
                            c.offending_count,
                            c.skip_reason,
                            c.detail,
                            (json.dumps(c.sample_rows, default=str) if c.sample_rows else None),
                            float(c.weight),
                        ),
                    )

                # Insert quarantined rows into SQLite
                for q in batch.quarantined_rows:
                    sqlite_conn.execute(
                        """
                        INSERT INTO QuarantineRow (
                            import_batch_id, target_table, source_row_ref, reason_code,
                            reason_detail, raw_values, resolution
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
                        """,
                        (
                            batch_id,
                            "FactActual",
                            q.get("source_row_ref", "unknown"),
                            q.get("reason_code", "import.error"),
                            q.get("reason_detail", "Quarantined row"),
                            json.dumps(q.get("raw_values", {})),
                        ),
                    )
        finally:
            sqlite_conn.close()

        # 2. Bulk insert transactions into DuckDB FactActual or FactBudget.
        # `should_commit` was computed at step 0b, before the audit row, so the
        # recorded status and the rows actually written cannot disagree.
        if transactions and should_commit:
            duck_conn = self.db.get_duckdb_connection()
            try:
                # One dimension cache for both branches (keys are (table, code)
                # pairs, so budget and actuals resolutions never collide).
                dimension_cache: dict[tuple[str, str], int | None] = {}
                if batch.source_type == "budget":
                    budget_rows = []

                    def resolve_budget_dimension(
                        table: str,
                        id_column: str,
                        code_column: str,
                        code: str | None,
                        extra_values: dict[str, Any] | None = None,
                    ) -> int | None:
                        normalized_code = str(code or "").strip()
                        cache_key = (table, normalized_code)
                        if cache_key not in dimension_cache:
                            dimension_cache[cache_key] = self._get_or_create_dimension_id(
                                duck_conn,
                                table=table,
                                id_column=id_column,
                                code_column=code_column,
                                code=normalized_code,
                                extra_values=extra_values,
                            )
                        return dimension_cache[cache_key]

                    for i, tx in enumerate(transactions, start=1):
                        budget_id = (batch_id * 10000000) + i
                        period_id = 9
                        if tx.period_code and "-P" in tx.period_code:
                            try:
                                period_id = int(tx.period_code.split("-P")[1])
                            except Exception:
                                period_id = 9
                        elif tx.posting_date and len(tx.posting_date) >= 7:
                            try:
                                period_id = int(tx.posting_date[5:7])
                            except Exception:
                                period_id = 9

                        company_code = tx.company_code or "IN01"
                        account_code = tx.account_code or "5000"
                        company_id = (
                            resolve_budget_dimension(
                                "DimCompany",
                                "company_id",
                                "company_code",
                                company_code,
                                {"company_name": company_code},
                            )
                            or 1
                        )
                        account_id = (
                            resolve_budget_dimension(
                                "DimAccount",
                                "account_id",
                                "account_code",
                                account_code,
                                {"account_name": account_code, "account_type": "unknown"},
                            )
                            or 5000
                        )
                        cost_center_id = resolve_budget_dimension(
                            "DimCostCenter",
                            "cost_center_id",
                            "cost_center_code",
                            tx.cost_center_code,
                            {
                                "cost_center_name": tx.cost_center_code or "",
                                "company_id": company_id,
                            },
                        )
                        budget_rows.append(
                            (
                                budget_id,
                                batch_id,
                                "FY26-Approved",
                                "base",
                                company_id,
                                account_id,
                                cost_center_id,
                                None,  # department_id
                                None,  # project_id
                                period_id,
                                str(tx.net_amount if tx.net_amount else tx.debit),
                                tx.currency_code or "INR",
                                False,
                                tx.source_row_ref or f"line {i}",
                            )
                        )

                    _bulk_insert(
                        duck_conn,
                        "FactBudget",
                        (
                            "budget_id",
                            "import_batch_id",
                            "budget_version",
                            "scenario_code",
                            "company_id",
                            "account_id",
                            "cost_center_id",
                            "department_id",
                            "project_id",
                            "period_id",
                            "amount",
                            "currency_code",
                            "is_derived_spread",
                            "source_row_ref",
                        ),
                        budget_rows,
                    )
                else:
                    # Resolve source entity/vendor codes so rule context keeps
                    # actuals at the imported business-key grain.
                    rows_to_insert = []

                    def resolve_actual_dimension(
                        table: str,
                        id_column: str,
                        code_column: str,
                        code: str | None,
                        extra_values: dict[str, Any] | None = None,
                    ) -> int | None:
                        normalized_code = str(code or "").strip()
                        cache_key = (table, normalized_code)
                        if cache_key not in dimension_cache:
                            dimension_cache[cache_key] = self._get_or_create_dimension_id(
                                duck_conn,
                                table=table,
                                id_column=id_column,
                                code_column=code_column,
                                code=normalized_code,
                                extra_values=extra_values,
                            )
                        return dimension_cache[cache_key]

                    for i, tx in enumerate(transactions, start=1):
                        # Deterministic row_id
                        actual_id = (batch_id * 10000000) + i
                        row_fingerprint = f"FP-{batch_id}-{tx.voucher_no}-{tx.line_no}"
                        period_id = 9
                        if tx.period_code and "-P" in tx.period_code:
                            try:
                                period_id = int(tx.period_code.split("-P")[1])
                            except Exception:
                                period_id = 9
                        elif tx.posting_date and len(tx.posting_date) >= 7:
                            try:
                                period_id = int(tx.posting_date[5:7])
                            except Exception:
                                period_id = 9

                        company_code = tx.company_code or "IN01"
                        account_code = tx.account_code or "5000"
                        company_id = (
                            resolve_actual_dimension(
                                "DimCompany",
                                "company_id",
                                "company_code",
                                company_code,
                                {"company_name": company_code},
                            )
                            or 1
                        )
                        account_id = (
                            resolve_actual_dimension(
                                "DimAccount",
                                "account_id",
                                "account_code",
                                account_code,
                                {"account_name": account_code, "account_type": "unknown"},
                            )
                            or 5000
                        )
                        cost_center_id = resolve_actual_dimension(
                            "DimCostCenter",
                            "cost_center_id",
                            "cost_center_code",
                            tx.cost_center_code,
                            {
                                "cost_center_name": tx.cost_center_code or "",
                                "company_id": company_id,
                            },
                        )
                        vendor_id = resolve_actual_dimension(
                            "DimVendor",
                            "vendor_id",
                            "vendor_code",
                            tx.vendor_code,
                            {"vendor_name": tx.vendor_code or ""},
                        )

                        rows_to_insert.append(
                            (
                                actual_id,
                                batch_id,
                                row_fingerprint,
                                company_id,
                                account_id,
                                cost_center_id,
                                None,  # department_id
                                None,  # project_id
                                vendor_id,
                                period_id,
                                tx.posting_date,
                                tx.document_date,
                                tx.voucher_no,
                                None,
                                tx.invoice_no,
                                tx.line_no,
                                tx.description,
                                str(tx.debit),
                                str(tx.credit),
                                str(tx.net_amount),
                                tx.currency_code,
                                tx.journal_category,
                                "D365" if "d365" in batch.source_type else "Other",
                                batch.file_name,
                                tx.source_row_ref,
                                False,
                            )
                        )

                    # Bulk insert, batched (see INSERT_BATCH_ROWS for why
                    # executemany is not used here).
                    _bulk_insert(
                        duck_conn,
                        "FactActual",
                        (
                            "actual_id",
                            "import_batch_id",
                            "row_fingerprint",
                            "company_id",
                            "account_id",
                            "cost_center_id",
                            "department_id",
                            "project_id",
                            "vendor_id",
                            "period_id",
                            "posting_date",
                            "document_date",
                            "voucher_no",
                            "document_no",
                            "invoice_no",
                            "line_no",
                            "description",
                            "debit",
                            "credit",
                            "net_amount",
                            "currency_code",
                            "journal_category",
                            "source_system",
                            "source_file_name",
                            "source_row_ref",
                            "is_zero_amount",
                        ),
                        rows_to_insert,
                    )
            finally:
                duck_conn.close()

        for tx in transactions:
            tx.import_batch_id = batch_id

        return batch_id

    def list_batches(self) -> list[dict[str, Any]]:
        """Return history of all import batches from SQLite."""
        conn = self.db.get_sqlite_connection()
        try:
            cur = conn.execute("SELECT * FROM FactImportBatch ORDER BY batch_id DESC")
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_batch_detail(self, batch_id: int) -> dict[str, Any] | None:
        """Return batch metadata, validation checks, and quarantined rows."""
        conn = self.db.get_sqlite_connection()
        try:
            cur = conn.execute("SELECT * FROM FactImportBatch WHERE batch_id = ?", (batch_id,))
            batch_row = cur.fetchone()
            if not batch_row:
                return None
            batch_dict = dict(batch_row)

            checks_cur = conn.execute(
                "SELECT * FROM FactValidationCheck WHERE import_batch_id = ?", (batch_id,)
            )
            checks = [dict(r) for r in checks_cur.fetchall()]

            quarantine_cur = conn.execute(
                "SELECT * FROM QuarantineRow WHERE import_batch_id = ?", (batch_id,)
            )
            quarantined = [dict(r) for r in quarantine_cur.fetchall()]

            batch_dict["checks"] = checks
            batch_dict["quarantinedRows"] = quarantined
            return batch_dict
        finally:
            conn.close()

    def void_batch(self, batch_id: int, reason: str) -> bool:
        """Void/reverse a batch: mark status as voided in SQLite and remove contribution from DuckDB facts."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            with sqlite_conn:
                cur = sqlite_conn.execute(
                    "SELECT status FROM FactImportBatch WHERE batch_id = ?",
                    (batch_id,),
                )
                row = cur.fetchone()
                if not row or row["status"] == "voided":
                    return False
                sqlite_conn.execute(
                    "UPDATE FactImportBatch SET status = 'voided' WHERE batch_id = ?",
                    (batch_id,),
                )
                sqlite_conn.execute(
                    """
                    INSERT INTO FactValidationCheck (
                        import_batch_id, check_code, check_name, status, severity,
                        offending_count, skip_reason, detail, weight
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch_id,
                        "CHK-VOID",
                        "Batch Void Audit",
                        "failed",
                        "Critical",
                        0,
                        None,
                        f"Batch voided by user. Reason: {reason}",
                        1.0,
                    ),
                )
        finally:
            sqlite_conn.close()

        # Remove transactions from DuckDB
        duck_conn = self.db.get_duckdb_connection()
        try:
            duck_conn.execute("DELETE FROM FactActual WHERE import_batch_id = ?", (batch_id,))
            duck_conn.execute("DELETE FROM FactBudget WHERE import_batch_id = ?", (batch_id,))
        except Exception:
            pass
        finally:
            duck_conn.close()

        return True

    def preview_budget_replace(
        self,
        budget_version: str,
        incoming_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Preview diff between current budget version and incoming budget rows per FR-IMP-028."""
        conn = self.db.get_duckdb_connection()
        try:
            existing_sql = """
            SELECT 
                COALESCE(c.company_code, 'IN01') AS company_code,
                COALESCE(p.period_code, 'FY26-P' || LPAD(CAST(fb.period_id AS VARCHAR), 2, '0')) AS period_code,
                SUM(fb.amount) AS total_amount
            FROM FactBudget fb
            LEFT JOIN DimCompany c ON fb.company_id = c.company_id
            LEFT JOIN DimPeriod p ON fb.period_id = p.period_id
            WHERE fb.budget_version = ?
            GROUP BY 1, 2
            """
            cursor = conn.execute(existing_sql, [budget_version])
            old_totals: dict[str, Decimal] = {}
            for row in cursor.fetchall():
                comp, period, amt = row
                old_totals[f"{comp}|{period}"] = Decimal(str(amt or 0))

            new_totals: dict[str, Decimal] = {}
            for r in incoming_rows:
                comp = str(r.get("company_code", "IN01"))
                period = str(r.get("period_code", r.get("period", "FY26-P01")))
                amt = Decimal(str(r.get("amount", r.get("net_amount", 0))))
                key = f"{comp}|{period}"
                new_totals[key] = new_totals.get(key, Decimal("0")) + amt

            all_keys = sorted(set(old_totals.keys()) | set(new_totals.keys()))
            diff_items = []
            old_grand = Decimal("0")
            new_grand = Decimal("0")

            for k in all_keys:
                parts = k.split("|")
                comp, period = parts[0], parts[1]
                old_amt = old_totals.get(k, Decimal("0"))
                new_amt = new_totals.get(k, Decimal("0"))
                delta = new_amt - old_amt
                old_grand += old_amt
                new_grand += new_amt
                diff_items.append(
                    {
                        "companyCode": comp,
                        "periodCode": period,
                        "oldTotal": str(old_amt),
                        "newTotal": str(new_amt),
                        "delta": str(delta),
                    }
                )

            return {
                "budgetVersion": budget_version,
                "oldGrandTotal": str(old_grand),
                "newGrandTotal": str(new_grand),
                "grandDelta": str(new_grand - old_grand),
                "items": diff_items,
            }
        finally:
            conn.close()

    def commit_budget_replace(
        self,
        budget_version: str,
        incoming_rows: list[dict[str, Any]],
        batch_id: int,
    ) -> int:
        """Atomically replace existing budget version with incoming rows per FR-IMP-028."""
        conn = self.db.get_duckdb_connection()
        try:
            conn.execute("BEGIN TRANSACTION;")
            conn.execute("DELETE FROM FactBudget WHERE budget_version = ?", [budget_version])

            insert_sql = """
            INSERT INTO FactBudget (
                budget_id, import_batch_id, budget_version, scenario_code,
                company_id, account_id, cost_center_id, department_id,
                project_id, period_id, amount, currency_code,
                is_derived_spread, source_row_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for i, r in enumerate(incoming_rows, start=1):
                budget_id = (batch_id * 10000000) + i
                comp_id = int(r.get("company_id", 1))
                acct_id = int(r.get("account_id", 5000))
                cc_id = r.get("cost_center_id")
                period_id = int(r.get("period_id", 9))
                amount = str(r.get("amount", r.get("net_amount", 0)))
                currency = str(r.get("currency_code", "INR"))
                source_ref = str(r.get("source_row_ref", f"row_{i}"))

                conn.execute(
                    insert_sql,
                    [
                        budget_id,
                        batch_id,
                        budget_version,
                        "base",
                        comp_id,
                        acct_id,
                        cc_id,
                        None,
                        None,
                        period_id,
                        amount,
                        currency,
                        False,
                        source_ref,
                    ],
                )
            conn.execute("COMMIT;")
            return len(incoming_rows)
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()
