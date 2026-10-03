"""Import and staging repository managing atomic batch commit per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §3."""

import json
from decimal import Decimal
from typing import List, Dict, Any, Optional
import duckdb
import sqlite3

from app.engine.calc.quality_score import calculate_quality_score
from app.engine.store.db import DatabaseManager
from app.engine.imports.models import ImportBatchResult, ParsedTransaction


class ImportRepository:
    """Manages transactional commit of import batches into DuckDB and SQLite."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def commit_batch(
        self,
        batch: ImportBatchResult,
        transactions: List[ParsedTransaction],
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
        # Per 04 section 12 and IMP-023 (scope F: "Reject; show the imbalance
        # amount and the top contributing rows"), debit=credit balance is an
        # unconditional file-level reject for every source_type - there is no
        # sub-ledger exemption (section 2.2 is the source-type table, section 10
        # is the confirm step; neither grants one). Per 19 section 5.5 the spec
        # is the sole authority of record (spec-wins), so an unbalanced batch
        # commits nothing regardless of source_type.
        should_commit = bool(batch.is_balanced)

        # DEF-010 (spec-wins fix): `status` records what ACTUALLY happened to the
        # rows, and what happened is now the same for every source_type -
        # unbalanced means rejected with zero rows committed (04 section 12 /
        # IMP-023). `is_balanced` still records the measured balance fact.
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
                        total_debit, total_credit, net_imbalance, data_quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch.source_type,
                        batch.file_name,
                        batch.file_checksum,
                        0,
                        "Data",
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
                        str(dq_score),
                    ),
                )
                batch_id = cur.lastrowid

                # Insert validation checks into SQLite
                for c in batch.checks:
                    sqlite_conn.execute(
                        """
                        INSERT INTO FactValidationCheck (
                            import_batch_id, check_code, check_name, status, severity,
                            offending_count, skip_reason, detail, weight
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                if batch.source_type == "budget":
                    budget_rows = []
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

                        cc_id = None
                        if tx.cost_center_code:
                            cc_clean = tx.cost_center_code.replace("CC-", "")
                            if cc_clean.isdigit():
                                cc_id = int(cc_clean)

                        acct_id = int(tx.account_code) if tx.account_code and tx.account_code.isdigit() else 5000
                        budget_rows.append((
                            budget_id,
                            batch_id,
                            "FY26-Approved",
                            "base",
                            1,  # company_id default
                            acct_id,
                            cc_id,
                            None,  # department_id
                            None,  # project_id
                            period_id,
                            str(tx.net_amount if tx.net_amount else tx.debit),
                            tx.currency_code or "INR",
                            False,
                            tx.source_row_ref or f"line {i}",
                        ))

                    duck_conn.executemany(
                        """
                        INSERT INTO FactBudget (
                            budget_id, import_batch_id, budget_version, scenario_code,
                            company_id, account_id, cost_center_id, department_id,
                            project_id, period_id, amount, currency_code,
                            is_derived_spread, source_row_ref
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        budget_rows,
                    )
                else:
                    # Prepare rows for FactActual
                    rows_to_insert = []
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

                        cc_id = None
                        if tx.cost_center_code:
                            cc_clean = tx.cost_center_code.replace("CC-", "")
                            if cc_clean.isdigit():
                                cc_id = int(cc_clean)

                        rows_to_insert.append((
                            actual_id,
                            batch_id,
                            row_fingerprint,
                            1,  # company_id default
                            int(tx.account_code) if tx.account_code and tx.account_code.isdigit() else 5000,
                            cc_id,
                            None,  # department_id
                            None,  # project_id
                            None,  # vendor_id
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
                        ))

                    # Batch insert via DuckDB executemany
                    duck_conn.executemany(
                        """
                        INSERT INTO FactActual (
                            actual_id, import_batch_id, row_fingerprint, company_id, account_id,
                            cost_center_id, department_id, project_id, vendor_id, period_id,
                            posting_date, document_date, voucher_no, document_no, invoice_no,
                            line_no, description, debit, credit, net_amount, currency_code,
                            journal_category, source_system, source_file_name, source_row_ref,
                            is_zero_amount
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        rows_to_insert,
                    )
            finally:
                duck_conn.close()

        return batch_id

    def list_batches(self) -> List[Dict[str, Any]]:
        """Return history of all import batches from SQLite."""
        conn = self.db.get_sqlite_connection()
        try:
            cur = conn.execute("SELECT * FROM FactImportBatch ORDER BY batch_id DESC")
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_batch_detail(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """Return batch metadata, validation checks, and quarantined rows."""
        conn = self.db.get_sqlite_connection()
        try:
            cur = conn.execute("SELECT * FROM FactImportBatch WHERE batch_id = ?", (batch_id,))
            batch_row = cur.fetchone()
            if not batch_row:
                return None
            batch_dict = dict(batch_row)

            checks_cur = conn.execute("SELECT * FROM FactValidationCheck WHERE import_batch_id = ?", (batch_id,))
            checks = [dict(r) for r in checks_cur.fetchall()]

            quarantine_cur = conn.execute("SELECT * FROM QuarantineRow WHERE import_batch_id = ?", (batch_id,))
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
        incoming_rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
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
            old_totals: Dict[str, Decimal] = {}
            for row in cursor.fetchall():
                comp, period, amt = row
                old_totals[f"{comp}|{period}"] = Decimal(str(amt or 0))

            new_totals: Dict[str, Decimal] = {}
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
                diff_items.append({
                    "companyCode": comp,
                    "periodCode": period,
                    "oldTotal": str(old_amt),
                    "newTotal": str(new_amt),
                    "delta": str(delta),
                })

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
        incoming_rows: List[Dict[str, Any]],
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
