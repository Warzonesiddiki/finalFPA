import sqlite3
import uuid
from datetime import datetime
from typing import Any

from app.engine.store.db import DatabaseManager


class AiProvenanceStore:
    """Manages AI draft provenance, version retention, and approval workflow per doc 10 §4, §5 & §6."""

    def __init__(self, db_mgr: DatabaseManager | None = None):
        self.db_mgr = db_mgr or DatabaseManager()
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_mgr.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS AiDraftProvenance (
                    draft_id TEXT PRIMARY KEY,
                    subject_key TEXT NOT NULL,
                    period_id INTEGER NOT NULL DEFAULT 9,
                    content TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    author TEXT NOT NULL DEFAULT 'Aarti'
                );
                """
            )
            conn.commit()

    def save_draft(
        self,
        subject_key: str,
        period_id: int,
        content: str,
        model: str,
        prompt_id: str,
        prompt_version: str,
        author: str = "Aarti",
    ) -> dict[str, Any]:
        """Save a new commentary draft version while retaining all previous versions per doc 10 §5."""
        draft_id = f"aidraft_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat()

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO AiDraftProvenance (
                    draft_id, subject_key, period_id, content, model,
                    prompt_id, prompt_version, timestamp, status, author
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?)
                """,
                (
                    draft_id,
                    subject_key,
                    period_id,
                    content,
                    model,
                    prompt_id,
                    prompt_version,
                    timestamp,
                    author,
                ),
            )
            conn.commit()

        return {
            "draftId": draft_id,
            "subjectKey": subject_key,
            "periodId": period_id,
            "content": content,
            "model": model,
            "promptId": prompt_id,
            "promptVersion": prompt_version,
            "timestamp": timestamp,
            "status": "draft",
            "author": author,
        }

    def list_drafts(self, subject_key: str, period_id: int = 9) -> list[dict[str, Any]]:
        """List all retained draft versions for provenance auditing per doc 10 §4 & §5."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                SELECT * FROM AiDraftProvenance
                WHERE subject_key = ? AND period_id = ?
                ORDER BY timestamp DESC
                """,
                (subject_key, period_id),
            )
            rows = [dict(r) for r in cur.fetchall()]

        return [
            {
                "draftId": r["draft_id"],
                "subjectKey": r["subject_key"],
                "periodId": r["period_id"],
                "content": r["content"],
                "model": r["model"],
                "promptId": r["prompt_id"],
                "promptVersion": r["prompt_version"],
                "timestamp": r["timestamp"],
                "status": r["status"],
                "author": r["author"],
            }
            for r in rows
        ]

    def approve_draft(self, draft_id: str) -> dict[str, Any] | None:
        """Approve a specific draft version for inclusion in PPT export per doc 10 §6."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT subject_key, period_id FROM AiDraftProvenance WHERE draft_id = ?",
                (draft_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            subject_key, period_id = row["subject_key"], row["period_id"]

            conn.execute(
                "UPDATE AiDraftProvenance SET status = 'draft' WHERE subject_key = ? AND period_id = ?",
                (subject_key, period_id),
            )
            conn.execute(
                "UPDATE AiDraftProvenance SET status = 'approved' WHERE draft_id = ?", (draft_id,)
            )
            conn.commit()

            cur = conn.execute("SELECT * FROM AiDraftProvenance WHERE draft_id = ?", (draft_id,))
            updated = cur.fetchone()
            return (
                {
                    "draftId": updated["draft_id"],
                    "subjectKey": updated["subject_key"],
                    "periodId": updated["period_id"],
                    "content": updated["content"],
                    "model": updated["model"],
                    "promptId": updated["prompt_id"],
                    "promptVersion": updated["prompt_version"],
                    "timestamp": updated["timestamp"],
                    "status": updated["status"],
                    "author": updated["author"],
                }
                if updated
                else None
            )
