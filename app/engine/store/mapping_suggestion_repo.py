"""Persistence for the mapping review queue per 02_FUNCTIONAL_SPEC.md FR-IMP-008.

Stores `MappingSuggestion` proposals and their append-only audit trail. This
repository deliberately CANNOT apply a mapping: applying a mapping is a
`MappingRepository.create_version` / `DimMapping` write performed by the importer
on a later run (FR-IMP-008: "Suggestions are never auto-applied in the same run;
accepted mappings apply to future imports").

Doc 26 API conventions: repository methods take an explicit connection owner
(`DatabaseManager`), return plain dicts/dataclasses, and never commit a partial
state machine transition.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.engine.imports.mapping_suggestions import (
    InvalidSuggestionTransition,
    MappingSuggestion,
    STATE_SUGGESTED,
)
from app.engine.store.db import DatabaseManager


class MappingSuggestionRepository:
    """CRUD + state transitions for the mapping review queue (FR-IMP-008)."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # -- writes -----------------------------------------------------------

    def enqueue(self, suggestions: Sequence[MappingSuggestion]) -> List[MappingSuggestion]:
        """Persist a run's suggestions, deduplicating on identity_hash.

        FR-IMP-008 edge case: "the same column suggested twice (deduplicated)".
        Re-enqueueing the same (run, column) is a no-op that returns the existing
        row rather than a duplicate.
        """
        conn = self.db.get_sqlite_connection()
        stored: List[MappingSuggestion] = []
        try:
            with conn:
                for s in suggestions:
                    existing = conn.execute(
                        "SELECT * FROM MappingSuggestion WHERE identity_hash = ?",
                        (s.identity_hash,),
                    ).fetchone()
                    if existing is not None:
                        stored.append(self._row_to_suggestion(existing))
                        continue
                    cur = conn.execute(
                        """
                        INSERT INTO MappingSuggestion (
                            identity_hash, import_run_id, source_column,
                            suggested_target_field, resolved_target_field, confidence,
                            origin, state, evidence_examples, decided_by, decided_at,
                            malformed_reason
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            s.identity_hash,
                            s.import_run_id,
                            s.source_column,
                            s.suggested_target_field,
                            s.resolved_target_field,
                            str(s.confidence),
                            s.origin,
                            s.state,
                            json.dumps(s.evidence_examples, default=str),
                            s.decided_by,
                            s.decided_at,
                            s.malformed_reason,
                        ),
                    )
                    s.suggestion_id = int(cur.lastrowid)
                    stored.append(s)
        finally:
            conn.close()
        return stored

    def decide(
        self,
        suggestion_id: int,
        action: str,
        actor: str,
        new_target_field: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> MappingSuggestion:
        """Apply one FR-IMP-008 transition and write an audit row atomically.

        `action` is `accept`, `edit` or `reject`. An illegal transition raises
        `InvalidSuggestionTransition` and writes nothing.
        """
        conn = self.db.get_sqlite_connection()
        try:
            with conn:
                row = conn.execute(
                    "SELECT * FROM MappingSuggestion WHERE suggestion_id = ?",
                    (suggestion_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(f"suggestion {suggestion_id} not found")
                suggestion = self._row_to_suggestion(row)
                from_state = suggestion.state

                if action == "accept":
                    suggestion.accept(actor)
                elif action == "edit":
                    if not new_target_field:
                        raise ValueError("edit requires new_target_field")
                    suggestion.edit(new_target_field, actor)
                elif action == "reject":
                    suggestion.reject(actor, reason=reason)
                else:
                    raise ValueError(f"unknown action: {action!r}")

                conn.execute(
                    """
                    UPDATE MappingSuggestion
                    SET state = ?, resolved_target_field = ?, decided_by = ?,
                        decided_at = ?, malformed_reason = ?
                    WHERE suggestion_id = ?
                    """,
                    (
                        suggestion.state,
                        suggestion.resolved_target_field,
                        suggestion.decided_by,
                        suggestion.decided_at,
                        suggestion.malformed_reason,
                        suggestion_id,
                    ),
                )
                self._write_audit(
                    conn,
                    suggestion_id,
                    from_state,
                    suggestion.state,
                    actor,
                    action,
                    {
                        "previous_target": row["suggested_target_field"],
                        "new_target": suggestion.resolved_target_field,
                    },
                )
                return suggestion
        finally:
            conn.close()

    def bulk_decide(
        self,
        suggestion_ids: Sequence[int],
        action: str,
        actor: str,
        new_targets: Optional[Dict[int, str]] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Bulk accept/edit with an audit trail (FR-IMP-008).

        Per-item outcome is reported. A single illegal item is recorded as skipped
        and does not abort the rest, because a reviewer bulk-confirming 40 columns
        should not lose the 38 valid ones to one bad row.
        """
        new_targets = new_targets or {}
        applied: List[int] = []
        skipped: List[Dict[str, Any]] = []

        for sid in suggestion_ids:
            try:
                self.decide(
                    sid,
                    action,
                    actor,
                    new_target_field=new_targets.get(sid),
                    reason=reason,
                )
                applied.append(sid)
            except (InvalidSuggestionTransition, ValueError, KeyError) as exc:
                skipped.append({"suggestion_id": sid, "reason": str(exc)})

        return {"applied": applied, "skipped": skipped, "action": action}

    def _write_audit(
        self,
        conn: Any,
        suggestion_id: int,
        from_state: str,
        to_state: str,
        actor: str,
        action: str,
        detail: Dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO MappingSuggestionAudit (
                suggestion_id, from_state, to_state, actor, action, detail
            ) VALUES (?,?,?,?,?,?)
            """,
            (
                suggestion_id,
                from_state,
                to_state,
                actor,
                action,
                json.dumps(detail, default=str),
            ),
        )

    # -- reads ------------------------------------------------------------

    def list_suggestions(
        self,
        import_run_id: Optional[int] = None,
        state: Optional[str] = None,
        origin: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Read the queue, newest state first, for the review UI.

        FR-IMP-008: "the queue shows rule-based suggestions only" when AI is
        disabled, so callers filter on `origin`.
        """
        conn = self.db.get_sqlite_connection()
        try:
            where: List[str] = []
            params: List[Any] = []
            if import_run_id is not None:
                where.append("import_run_id = ?")
                params.append(import_run_id)
            if state:
                where.append("state = ?")
                params.append(state)
            if origin:
                where.append("origin = ?")
                params.append(origin)
            clause = f"WHERE {' AND '.join(where)}" if where else ""

            rows = conn.execute(
                f"SELECT * FROM MappingSuggestion {clause} "
                "ORDER BY confidence DESC, source_column ASC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
            total = conn.execute(
                f"SELECT COUNT(*) FROM MappingSuggestion {clause}", params
            ).fetchone()[0]

            return {
                "items": [self._row_to_suggestion(r).to_dict() for r in rows],
                "total": int(total),
                "limit": limit,
                "offset": offset,
            }
        finally:
            conn.close()

    # -- application log (write side of FR-IMP-008) ----------------------

    def record_applications(
        self,
        applications: Sequence[Dict[str, Any]],
    ) -> int:
        """Log which suggestions were baked into which profile version.

        `MappingSuggestionApplication` has UNIQUE(suggestion_id), so a
        suggestion is applied to a profile exactly once, ever. That is what makes
        `resolve_profile_for_import` idempotent across repeated runs.
        """
        if not applications:
            return 0
        conn = self.db.get_sqlite_connection()
        try:
            with conn:
                for app_row in applications:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO MappingSuggestionApplication (
                            suggestion_id, profile_id, version_no, import_run_id,
                            source_column, canonical_field
                        ) VALUES (?,?,?,?,?,?)
                        """,
                        (
                            app_row["suggestion_id"],
                            app_row["profile_id"],
                            app_row["version_no"],
                            app_row["import_run_id"],
                            app_row["source_column"],
                            app_row["canonical_field"],
                        ),
                    )
            return len(applications)
        finally:
            conn.close()

    def already_applied(self, suggestion_ids: Sequence[int]) -> set:
        """Which of these suggestions have already been applied to a profile."""
        ids = [int(i) for i in suggestion_ids]
        if not ids:
            return set()
        placeholders = ",".join("?" * len(ids))
        conn = self.db.get_sqlite_connection()
        try:
            rows = conn.execute(
                f"SELECT suggestion_id FROM MappingSuggestionApplication "
                f"WHERE suggestion_id IN ({placeholders})",
                ids,
            ).fetchall()
            return {int(r[0]) for r in rows}
        finally:
            conn.close()

    def get_applications(self, suggestion_id: int) -> List[Dict[str, Any]]:
        """Where a suggestion was applied - the profile-history link."""
        conn = self.db.get_sqlite_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM MappingSuggestionApplication "
                "WHERE suggestion_id = ? ORDER BY application_id ASC",
                (suggestion_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_suggestion(self, suggestion_id: int) -> Optional[MappingSuggestion]:
        conn = self.db.get_sqlite_connection()
        try:
            row = conn.execute(
                "SELECT * FROM MappingSuggestion WHERE suggestion_id = ?",
                (suggestion_id,),
            ).fetchone()
            return self._row_to_suggestion(row) if row else None
        finally:
            conn.close()

    def get_audit_trail(self, suggestion_id: int) -> List[Dict[str, Any]]:
        conn = self.db.get_sqlite_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM MappingSuggestionAudit WHERE suggestion_id = ? "
                "ORDER BY audit_id ASC",
                (suggestion_id,),
            ).fetchall()
            out = []
            for r in rows:
                item = dict(r)
                item["detail"] = json.loads(item["detail"]) if item.get("detail") else {}
                out.append(item)
            return out
        finally:
            conn.close()

    def count_by_state(self, import_run_id: Optional[int] = None) -> Dict[str, int]:
        """Queue summary counts for the review screen."""
        conn = self.db.get_sqlite_connection()
        try:
            if import_run_id is None:
                rows = conn.execute(
                    "SELECT state, COUNT(*) FROM MappingSuggestion GROUP BY state"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT state, COUNT(*) FROM MappingSuggestion "
                    "WHERE import_run_id = ? GROUP BY state",
                    (import_run_id,),
                ).fetchall()
            return {str(r[0]): int(r[1]) for r in rows}
        finally:
            conn.close()

    def applyable_for_run(self, import_run_id: int) -> List[MappingSuggestion]:
        """Accepted/edited suggestions from EARLIER runs that this run may apply.

        FR-IMP-008: "accepted mappings apply to future imports", so anything raised by
        this same run_id is excluded here at the query level, not merely filtered
        later. This is the read side of the no-same-run-application guarantee.
        """
        conn = self.db.get_sqlite_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM MappingSuggestion
                WHERE state IN ('accepted', 'edited')
                  AND import_run_id <> ?
                ORDER BY import_run_id ASC, source_column ASC
                """,
                (import_run_id,),
            ).fetchall()
            return [self._row_to_suggestion(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def _row_to_suggestion(row: Any) -> MappingSuggestion:
        from decimal import Decimal

        keys = row.keys() if hasattr(row, "keys") else []
        get = (lambda k: row[k]) if keys else (lambda k: row[getattr(row, f"index_{k}", 0)])

        evidence_raw = get("evidence_examples")
        try:
            evidence = json.loads(evidence_raw) if evidence_raw else []
        except (TypeError, json.JSONDecodeError):
            evidence = []

        return MappingSuggestion(
            suggestion_id=int(get("suggestion_id")),
            import_run_id=int(get("import_run_id")),
            source_column=get("source_column"),
            suggested_target_field=get("suggested_target_field"),
            resolved_target_field=get("resolved_target_field"),
            confidence=Decimal(str(get("confidence"))),
            origin=get("origin") or "rule",
            state=get("state") or STATE_SUGGESTED,
            evidence_examples=evidence,
            decided_by=get("decided_by"),
            decided_at=get("decided_at"),
            malformed_reason=get("malformed_reason"),
        )