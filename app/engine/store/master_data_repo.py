"""Persistent master-data operations used by deterministic rules."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.engine.calc.math import ZERO, quantize_money
from app.engine.store.db import DatabaseManager


class ApprovalThresholdError(ValueError):
    """Base error for invalid or conflicting approval-threshold changes."""


class ApprovalThresholdValidationError(ApprovalThresholdError):
    """Raised when a threshold row is malformed or references an unknown scope."""


class ApprovalThresholdConflict(ApprovalThresholdError):
    """Raised when a threshold version would make resolution ambiguous."""


class ApprovalThresholdRepository:
    """Read and append effective-dated MasterApprovalThreshold versions.

    Rows are append-only and versioned by ``(threshold_id, effective_from)``.
    The threshold ID remains stable across versions; existing periods continue
    resolving to the row effective on each transaction's date.
    """

    _SCOPE_FIELDS = {
        "company": ("company_code", "company_id", "DimCompany", "company_code"),
        "account": ("account_code", "account_id", "DimAccount", "account_code"),
        "cost_center": ("cost_center_code", "cost_center_id", "DimCostCenter", "cost_center_code"),
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def list_approval_thresholds(self) -> list[dict[str, Any]]:
        """Return every active and inactive version with resolved business codes."""
        conn = self.db.get_duckdb_connection()
        try:
            rows = conn.execute(
                """
                SELECT t.threshold_id, t.scope, t.amount_threshold,
                       t.requires_dual_approval, t.effective_from, t.is_active,
                       t.created_at, t.created_by, t.change_note,
                       c.company_code, a.account_code, cc.cost_center_code
                FROM MasterApprovalThreshold t
                LEFT JOIN DimCompany c ON t.company_id = c.company_id
                LEFT JOIN DimAccount a ON t.account_id = a.account_id
                LEFT JOIN DimCostCenter cc ON t.cost_center_id = cc.cost_center_id
                ORDER BY t.scope, t.threshold_id, t.effective_from DESC
                """
            ).fetchall()
            return [
                {
                    "thresholdId": str(row[0]),
                    "scope": str(row[1]),
                    "amountThreshold": str(row[2]),
                    "requiresDualApproval": bool(row[3]),
                    "effectiveFrom": str(row[4]),
                    "isActive": bool(row[5]),
                    "createdAt": str(row[6]),
                    "createdBy": str(row[7]),
                    "changeNote": str(row[8] or ""),
                    "companyCode": row[9],
                    "accountCode": row[10],
                    "costCenterCode": row[11],
                }
                for row in rows
            ]
        finally:
            conn.close()

    def create_approval_threshold_version(
        self,
        *,
        threshold_id: str,
        scope: str,
        amount_threshold: Any,
        requires_dual_approval: bool,
        effective_from: str | date,
        change_note: str,
        is_active: bool = True,
        company_code: str | None = None,
        account_code: str | None = None,
        cost_center_code: str | None = None,
        actor: str = "session_user",
    ) -> dict[str, Any]:
        """Append one immutable, unambiguous threshold version."""
        clean_id = str(threshold_id or "").strip()
        clean_scope = str(scope or "").strip().lower()
        if not clean_id or len(clean_id) > 80 or "|" in clean_id:
            raise ApprovalThresholdValidationError(
                "thresholdId must be 1–80 characters and must not contain '|'"
            )
        if clean_scope not in self._SCOPE_FIELDS:
            raise ApprovalThresholdValidationError("scope must be company, account, or cost_center")
        try:
            amount = quantize_money(Decimal(str(amount_threshold)))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ApprovalThresholdValidationError(
                "amountThreshold must be a valid amount"
            ) from exc
        if not amount.is_finite() or amount <= ZERO:
            raise ApprovalThresholdValidationError(
                "amountThreshold must be a finite value greater than zero"
            )
        if amount > Decimal("9999999999999999.99"):
            raise ApprovalThresholdValidationError(
                "amountThreshold exceeds DECIMAL(18,2) storage range"
            )
        try:
            effective_date = (
                effective_from
                if isinstance(effective_from, date) and not isinstance(effective_from, datetime)
                else date.fromisoformat(str(effective_from).strip())
            )
        except (TypeError, ValueError) as exc:
            raise ApprovalThresholdValidationError("effectiveFrom must be an ISO date") from exc

        supplied_codes = {
            "company_code": str(company_code or "").strip(),
            "account_code": str(account_code or "").strip(),
            "cost_center_code": str(cost_center_code or "").strip(),
        }
        target_code_field, target_id_field, target_table, target_column = self._SCOPE_FIELDS[
            clean_scope
        ]
        unexpected = [
            field for field, value in supplied_codes.items() if value and field != target_code_field
        ]
        if unexpected:
            raise ApprovalThresholdValidationError(
                f"scope {clean_scope!r} accepts only {target_code_field}"
            )
        target_code = supplied_codes[target_code_field]
        if not target_code:
            raise ApprovalThresholdValidationError(
                f"{target_code_field} is required for {clean_scope!r} scope"
            )

        clean_note = str(change_note or "").strip()
        if not clean_note or len(clean_note) > 500:
            raise ApprovalThresholdValidationError("changeNote must contain 1–500 characters")
        actor_name = str(actor or "session_user").strip()[:120] or "session_user"
        conn = self.db.get_duckdb_connection()
        try:
            conn.execute("BEGIN TRANSACTION")
            dimension = conn.execute(
                f"SELECT {target_id_field}, {target_column} FROM {target_table} "
                f"WHERE lower({target_column}) = lower(?) AND is_active = TRUE",
                [target_code],
            ).fetchone()
            if not dimension:
                raise ApprovalThresholdValidationError(
                    f"No active {clean_scope} master row matches {target_code!r}"
                )
            dimension_id = int(dimension[0])
            canonical_code = str(dimension[1])

            scope_ids: tuple[int | None, int | None, int | None] = (
                dimension_id if clean_scope == "company" else None,
                dimension_id if clean_scope == "account" else None,
                dimension_id if clean_scope == "cost_center" else None,
            )
            identity = (clean_scope, *scope_ids, bool(requires_dual_approval))
            existing_identity_rows = conn.execute(
                """
                SELECT DISTINCT scope, company_id, account_id, cost_center_id,
                                requires_dual_approval
                FROM MasterApprovalThreshold
                WHERE threshold_id = ?
                """,
                [clean_id],
            ).fetchall()
            if any(tuple(row) != identity for row in existing_identity_rows):
                raise ApprovalThresholdConflict(
                    f"thresholdId {clean_id!r} already belongs to a different scope, target, or approval stage"
                )

            duplicate_version = conn.execute(
                """
                SELECT 1 FROM MasterApprovalThreshold
                WHERE threshold_id = ? AND effective_from = ?
                """,
                [clean_id, effective_date],
            ).fetchone()
            if duplicate_version:
                raise ApprovalThresholdConflict(
                    f"thresholdId {clean_id!r} already has a version effective {effective_date.isoformat()}"
                )

            competing = conn.execute(
                """
                SELECT threshold_id FROM MasterApprovalThreshold
                WHERE scope = ?
                  AND company_id IS NOT DISTINCT FROM ?
                  AND account_id IS NOT DISTINCT FROM ?
                  AND cost_center_id IS NOT DISTINCT FROM ?
                  AND requires_dual_approval = ?
                  AND effective_from = ?
                  AND threshold_id <> ?
                """,
                [clean_scope, *scope_ids, bool(requires_dual_approval), effective_date, clean_id],
            ).fetchone()
            if competing:
                raise ApprovalThresholdConflict(
                    "Another threshold row already exists for this scope, approval stage, and effective date"
                )

            conn.execute(
                """
                INSERT INTO MasterApprovalThreshold (
                    threshold_id, scope, company_id, account_id, cost_center_id,
                    amount_threshold, requires_dual_approval, effective_from,
                    is_active, created_by, change_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    clean_id,
                    clean_scope,
                    *scope_ids,
                    amount,
                    bool(requires_dual_approval),
                    effective_date,
                    bool(is_active),
                    actor_name,
                    clean_note,
                ],
            )
            created_at_row = conn.execute(
                """
                SELECT CAST(created_at AS VARCHAR)
                FROM MasterApprovalThreshold
                WHERE threshold_id = ? AND effective_from = ?
                """,
                [clean_id, effective_date],
            ).fetchone()
            conn.execute(
                """
                UPDATE DerivedDataState
                SET is_stale = TRUE,
                    reason = 'Approval-threshold configuration changed; rerun dependent rules',
                    generation = COALESCE(generation, 0) + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE state_id = 1
                """
            )
            conn.execute("COMMIT")
            return {
                "thresholdId": clean_id,
                "scope": clean_scope,
                "amountThreshold": str(amount),
                "requiresDualApproval": bool(requires_dual_approval),
                "effectiveFrom": effective_date.isoformat(),
                "isActive": bool(is_active),
                "createdAt": str(created_at_row[0]) if created_at_row else "",
                "createdBy": actor_name,
                "changeNote": clean_note,
                "companyCode": canonical_code if clean_scope == "company" else None,
                "accountCode": canonical_code if clean_scope == "account" else None,
                "costCenterCode": canonical_code if clean_scope == "cost_center" else None,
            }
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()
