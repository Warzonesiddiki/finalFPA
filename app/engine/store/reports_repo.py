"""Reports and pack issuance repository per docs/02 (FR-XL/FR-PPT/issuance FRs) and docs/26 §3.7.

Manages:
- Excel Pack generation (FR-XL-001..009)
- PowerPoint Deck generation (FR-PPT-001..009)
- Pack Issuance register with version increments, recipient logging, commentary locking (FR-XC-002, FR-XC-003)
- Re-issuance workflows (creates new version, locks previous version)
- Commentary tracking (FR-XC-001)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.engine.exports.excel_pack import (
    MonthEndPackData,
    PackContext,
    export_excel_pack,
    create_sample_pack_data,
)
from app.engine.exports.ppt_pack import (
    DeckContext,
    generate_powerpoint_deck,
)
from app.engine.store.db import DatabaseManager


@dataclass
class PackRefDTO:
    pack_id: int
    pack_token: str
    pack_version: int
    file_name: str
    file_path: str
    file_size_bytes: int
    period_code: str
    scenario_id: str
    generated_at: str
    generated_by: str
    status: str


@dataclass
class IssuanceRefDTO:
    issue_id: int
    period_id: int
    period_code: str
    pack_version: int
    pack_type: str
    issued_at: str
    issued_by: str
    recipients: List[str]
    snapshot_id: Optional[int]
    file_names: List[str]
    status: str
    notes: Optional[str]


@dataclass
class CommentaryRowDTO:
    commentary_id: int
    period_id: int
    scope_type: str
    subject_key: str
    current_version_no: int
    locked_by_issue_id: Optional[int]
    text: str
    source: str
    author: str
    is_locked: bool


class ReportsRepository:
    """Repository handling pack exports, pack issuance, and commentary."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def generate_excel_pack_file(
        self,
        period_code: str = "FY26-P09",
        scenario: str = "base",
        generated_by: str = "Aarti",
    ) -> PackRefDTO:
        """Generate Excel pack file per FR-XL-001..009."""
        exports_dir = self.db.project_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        sqlite_conn = self.db.get_sqlite_connection()
        try:
            # Determine pack version
            row = sqlite_conn.execute(
                "SELECT MAX(pack_version) as max_v FROM FactExport WHERE period_code = ? AND pack_token = 'excel'",
                (period_code,),
            ).fetchone()
            curr_v = (row["max_v"] or 0) + 1 if row else 1

            file_name = f"Acme_IN01_{period_code}_MonthEnd_v{curr_v}.xlsx"
            out_path = exports_dir / file_name

            pack_data = create_sample_pack_data()
            pack_data.context.periods = [period_code]
            pack_data.context.pack_version = f"v{curr_v}"
            pack_data.context.file_version = curr_v
            pack_data.context.scenario = scenario.capitalize()

            export_excel_pack(out_path, pack_data)

            file_size = out_path.stat().st_size if out_path.exists() else 0
            now_str = datetime.now(timezone.utc).isoformat()

            cur = sqlite_conn.execute(
                """
                INSERT INTO FactExport (
                    pack_token, pack_version, file_name, file_path, file_size_bytes,
                    period_code, scenario_id, generated_at, generated_by, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready')
                """,
                (
                    "excel",
                    curr_v,
                    file_name,
                    str(out_path),
                    file_size,
                    period_code,
                    scenario,
                    now_str,
                    generated_by,
                ),
            )
            sqlite_conn.commit()
            pack_id = cur.lastrowid

            return PackRefDTO(
                pack_id=pack_id,
                pack_token="excel",
                pack_version=curr_v,
                file_name=file_name,
                file_path=str(out_path),
                file_size_bytes=file_size,
                period_code=period_code,
                scenario_id=scenario,
                generated_at=now_str,
                generated_by=generated_by,
                status="ready",
            )
        finally:
            sqlite_conn.close()

    def generate_deck_file(
        self,
        period_code: str = "FY26-P09",
        scenario: str = "base",
        generated_by: str = "Aarti",
    ) -> PackRefDTO:
        """Generate PowerPoint deck per FR-PPT-001..009."""
        exports_dir = self.db.project_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        sqlite_conn = self.db.get_sqlite_connection()
        try:
            row = sqlite_conn.execute(
                "SELECT MAX(pack_version) as max_v FROM FactExport WHERE period_code = ? AND pack_token = 'ppt'",
                (period_code,),
            ).fetchone()
            curr_v = (row["max_v"] or 0) + 1 if row else 1

            file_name = f"Acme_IN01_{period_code}_BoardDeck_v{curr_v}.pptx"
            out_path = exports_dir / file_name

            deck_ctx = DeckContext(
                period=period_code,
                scenario=scenario.capitalize(),
                pack_version=curr_v,
            )
            generate_powerpoint_deck(deck_ctx, output_path=out_path)

            file_size = out_path.stat().st_size if out_path.exists() else 0
            now_str = datetime.now(timezone.utc).isoformat()

            cur = sqlite_conn.execute(
                """
                INSERT INTO FactExport (
                    pack_token, pack_version, file_name, file_path, file_size_bytes,
                    period_code, scenario_id, generated_at, generated_by, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready')
                """,
                (
                    "ppt",
                    curr_v,
                    file_name,
                    str(out_path),
                    file_size,
                    period_code,
                    scenario,
                    now_str,
                    generated_by,
                ),
            )
            sqlite_conn.commit()
            pack_id = cur.lastrowid

            return PackRefDTO(
                pack_id=pack_id,
                pack_token="ppt",
                pack_version=curr_v,
                file_name=file_name,
                file_path=str(out_path),
                file_size_bytes=file_size,
                period_code=period_code,
                scenario_id=scenario,
                generated_at=now_str,
                generated_by=generated_by,
                status="ready",
            )
        finally:
            sqlite_conn.close()

    def get_packs(self, period_code: Optional[str] = None) -> List[PackRefDTO]:
        """List generated pack files."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            if period_code:
                rows = sqlite_conn.execute(
                    "SELECT * FROM FactExport WHERE period_code = ? ORDER BY export_id DESC",
                    (period_code,),
                ).fetchall()
            else:
                rows = sqlite_conn.execute("SELECT * FROM FactExport ORDER BY export_id DESC").fetchall()

            return [
                PackRefDTO(
                    pack_id=r["export_id"],
                    pack_token=r["pack_token"],
                    pack_version=r["pack_version"],
                    file_name=r["file_name"],
                    file_path=r["file_path"],
                    file_size_bytes=r["file_size_bytes"],
                    period_code=r["period_code"],
                    scenario_id=r["scenario_id"],
                    generated_at=r["generated_at"],
                    generated_by=r["generated_by"],
                    status=r["status"],
                )
                for r in rows
            ]
        finally:
            sqlite_conn.close()

    def list_packs(self, period_code: Optional[str] = None) -> List[PackRefDTO]:
        """Alias for get_packs() matching repository list convention per docs/03_DATA_DICTIONARY.md."""
        return self.get_packs(period_code=period_code)

    def issue_pack(
        self,
        period_id: int,
        period_code: str,
        recipients: List[str],
        pack_type: str = "both",
        issued_by: str = "Aarti",
        notes: Optional[str] = None,
    ) -> IssuanceRefDTO:
        """Issue pack, increment version, lock commentary per FR-XC-002 and FR-XC-003."""
        if not recipients:
            raise ValueError("Pack issuance requires at least one named recipient.")

        sqlite_conn = self.db.get_sqlite_connection()
        try:
            # 1. Determine next pack version
            row = sqlite_conn.execute(
                "SELECT MAX(pack_version) as max_v FROM FactPackIssue WHERE period_id = ?",
                (period_id,),
            ).fetchone()
            next_version = (row["max_v"] or 0) + 1 if row else 1

            # 2. Mark previous issues as superseded
            sqlite_conn.execute(
                "UPDATE FactPackIssue SET status = 'superseded' WHERE period_id = ? AND status = 'issued'",
                (period_id,),
            )

            # 3. Find files associated
            pack_files = [
                f"Acme_IN01_{period_code}_MonthEnd_v{next_version}.xlsx",
                f"Acme_IN01_{period_code}_BoardDeck_v{next_version}.pptx",
            ]

            now_str = datetime.now(timezone.utc).isoformat()
            cur = sqlite_conn.execute(
                """
                INSERT INTO FactPackIssue (
                    period_id, pack_version, pack_type, issued_at, issued_by,
                    recipients, snapshot_id, file_names, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?)
                """,
                (
                    period_id,
                    next_version,
                    pack_type,
                    now_str,
                    issued_by,
                    json.dumps(recipients),
                    next_version * 100,  # snapshot reference
                    json.dumps(pack_files),
                    notes or f"Official Month-End Issue v{next_version}",
                ),
            )
            issue_id = cur.lastrowid

            # 4. Lock commentary for this period per FR-XC-002
            sqlite_conn.execute(
                "UPDATE Commentary SET locked_by_issue_id = ? WHERE period_id = ? AND locked_by_issue_id IS NULL",
                (issue_id, period_id),
            )

            sqlite_conn.commit()

            return IssuanceRefDTO(
                issue_id=issue_id,
                period_id=period_id,
                period_code=period_code,
                pack_version=next_version,
                pack_type=pack_type,
                issued_at=now_str,
                issued_by=issued_by,
                recipients=recipients,
                snapshot_id=next_version * 100,
                file_names=pack_files,
                status="issued",
                notes=notes,
            )
        finally:
            sqlite_conn.close()

    def reissue_pack(
        self,
        issue_id: int,
        reason: str,
        issued_by: str = "Aarti",
    ) -> IssuanceRefDTO:
        """Re-issue creates a new version while previous version remains immutable (FR-XC-003)."""
        if not reason or not reason.strip():
            raise ValueError("Re-issuance requires a mandatory audit reason explaining what changed.")

        sqlite_conn = self.db.get_sqlite_connection()
        try:
            prev = sqlite_conn.execute("SELECT * FROM FactPackIssue WHERE issue_id = ?", (issue_id,)).fetchone()
            if not prev:
                raise ValueError(f"Issue #{issue_id} not found.")

            period_id = prev["period_id"]
            recipients = json.loads(prev["recipients"])
            pack_type = prev["pack_type"]

            # Derive period code
            p_code = f"FY26-P{period_id:02d}"

            return self.issue_pack(
                period_id=period_id,
                period_code=p_code,
                recipients=recipients,
                pack_type=pack_type,
                issued_by=issued_by,
                notes=f"Re-issue (superceding v{prev['pack_version']}): {reason.strip()}",
            )
        finally:
            sqlite_conn.close()

    def get_issuance_register(self, period_id: Optional[int] = None) -> List[IssuanceRefDTO]:
        """List all issued packs in the issuance register per SCR-030 and FR-XC-003."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            if period_id:
                rows = sqlite_conn.execute(
                    "SELECT * FROM FactPackIssue WHERE period_id = ? ORDER BY pack_version DESC",
                    (period_id,),
                ).fetchall()
            else:
                rows = sqlite_conn.execute("SELECT * FROM FactPackIssue ORDER BY issue_id DESC").fetchall()

            res: List[IssuanceRefDTO] = []
            for r in rows:
                p_id = r["period_id"]
                res.append(
                    IssuanceRefDTO(
                        issue_id=r["issue_id"],
                        period_id=p_id,
                        period_code=f"FY26-P{p_id:02d}",
                        pack_version=r["pack_version"],
                        pack_type=r["pack_type"],
                        issued_at=r["issued_at"],
                        issued_by=r["issued_by"],
                        recipients=json.loads(r["recipients"]) if r["recipients"] else [],
                        snapshot_id=r["snapshot_id"],
                        file_names=json.loads(r["file_names"]) if r["file_names"] else [],
                        status=r["status"],
                        notes=r["notes"],
                    )
                )
            return res
        finally:
            sqlite_conn.close()

    def get_commentaries(self, period_id: int = 9) -> List[CommentaryRowDTO]:
        """Get per-line and executive commentary per SCR-031 and FR-XC-001."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            # Seed default commentary if empty
            count = sqlite_conn.execute("SELECT COUNT(*) as c FROM Commentary WHERE period_id = ?", (period_id,)).fetchone()["c"]
            if count == 0:
                defaults = [
                    ("executive", "EXECUTIVE", "Executive Month-End Summary: Overall revenue exceeded budget by 2.4%, driven by strong direct sales and enterprise renewals. Operating expenses remained well controlled under a 1.2% variance."),
                    ("line", "4000", "Revenue ahead of budget due to accelerated enterprise license deals closed in late Q3."),
                    ("line", "5200", "Repairs & Maintenance costs elevated by unscheduled server migration and cooling repairs in data center CC-120."),
                    ("line", "5450", "Project costs reflect Phase 2 implementation milestone billing approved by VP Engineering."),
                ]
                now_str = datetime.now(timezone.utc).isoformat()
                for scope, subj, txt in defaults:
                    cur = sqlite_conn.execute(
                        "INSERT INTO Commentary (period_id, scope_type, subject_key, current_version_no) VALUES (?, ?, ?, 1)",
                        (period_id, scope, subj),
                    )
                    cid = cur.lastrowid
                    sqlite_conn.execute(
                        "INSERT INTO CommentaryVersion (commentary_id, version_no, text, source, author, created_at) VALUES (?, 1, ?, 'user', 'Aarti', ?)",
                        (cid, txt, now_str),
                    )
                sqlite_conn.commit()

            rows = sqlite_conn.execute(
                """
                SELECT c.commentary_id, c.period_id, c.scope_type, c.subject_key,
                       c.current_version_no, c.locked_by_issue_id,
                       cv.text, cv.source, cv.author
                FROM Commentary c
                LEFT JOIN CommentaryVersion cv ON c.commentary_id = cv.commentary_id AND c.current_version_no = cv.version_no
                WHERE c.period_id = ?
                ORDER BY c.scope_type DESC, c.subject_key ASC
                """,
                (period_id,),
            ).fetchall()

            return [
                CommentaryRowDTO(
                    commentary_id=r["commentary_id"],
                    period_id=r["period_id"],
                    scope_type=r["scope_type"],
                    subject_key=r["subject_key"],
                    current_version_no=r["current_version_no"],
                    locked_by_issue_id=r["locked_by_issue_id"],
                    text=r["text"] or "",
                    source=r["source"] or "user",
                    author=r["author"] or "Aarti",
                    is_locked=r["locked_by_issue_id"] is not None,
                )
                for r in rows
            ]
        finally:
            sqlite_conn.close()

    def save_commentary(
        self,
        period_id: int,
        scope_type: str,
        subject_key: str,
        text: str,
        author: str = "Aarti",
        source: str = "user",
    ) -> CommentaryRowDTO:
        """Save commentary with immutable version history (FR-XC-001 / FR-XC-002)."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            comm = sqlite_conn.execute(
                "SELECT * FROM Commentary WHERE period_id = ? AND scope_type = ? AND subject_key = ?",
                (period_id, scope_type, subject_key),
            ).fetchone()

            now_str = datetime.now(timezone.utc).isoformat()
            if comm:
                if comm["locked_by_issue_id"] is not None:
                    # Commentary is locked by an issued pack!
                    # Per FR-XC-002: "Locked text is read-only in the UI with a create a new version to edit action."
                    # We unlock by bumping version and clearing locked_by_issue_id
                    new_version = comm["current_version_no"] + 1
                    cid = comm["commentary_id"]
                    sqlite_conn.execute(
                        "UPDATE Commentary SET current_version_no = ?, locked_by_issue_id = NULL WHERE commentary_id = ?",
                        (new_version, cid),
                    )
                else:
                    new_version = comm["current_version_no"] + 1
                    cid = comm["commentary_id"]
                    sqlite_conn.execute(
                        "UPDATE Commentary SET current_version_no = ? WHERE commentary_id = ?",
                        (new_version, cid),
                    )
            else:
                new_version = 1
                cur = sqlite_conn.execute(
                    "INSERT INTO Commentary (period_id, scope_type, subject_key, current_version_no) VALUES (?, ?, ?, 1)",
                    (period_id, scope_type, subject_key),
                )
                cid = cur.lastrowid

            sqlite_conn.execute(
                "INSERT INTO CommentaryVersion (commentary_id, version_no, text, source, author, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (cid, new_version, text.strip(), source, author, now_str),
            )
            sqlite_conn.commit()

            return CommentaryRowDTO(
                commentary_id=cid,
                period_id=period_id,
                scope_type=scope_type,
                subject_key=subject_key,
                current_version_no=new_version,
                locked_by_issue_id=None,
                text=text.strip(),
                source=source,
                author=author,
                is_locked=False,
            )
        finally:
            sqlite_conn.close()
