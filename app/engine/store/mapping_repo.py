"""Mapping profile and version persistence repository per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §5 and 03_DATA_DICTIONARY.md §3.8, §5.5."""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3
import duckdb

from app.engine.store.db import DatabaseManager
from app.engine.imports.profiles import (
    MappingProfile,
    MappingProfileVersion,
    DimMapping,
    BUILTIN_PROFILES,
    compute_header_signature,
    normalize_header,
)


class MappingRepository:
    """Manages persistence, versioning, immutability, and cloning of mapping profiles.
    
    Persistence architecture per 03_DATA_DICTIONARY.md:
    - MappingProfile & MappingProfileVersion stored in SQLite (workflow state)
    - DimMapping stored in DuckDB (analytical store) and SQLite (workflow state)
    """

    def __init__(self, db_manager: DatabaseManager, auto_seed: bool = True):
        self.db = db_manager
        if auto_seed:
            self.ensure_builtin_profiles_seeded()

    def ensure_builtin_profiles_seeded(self) -> None:
        """Seed built-in profiles per 04 §5.4 if not already present."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            cur = sqlite_conn.execute("SELECT COUNT(*) FROM MappingProfile WHERE is_builtin = 1")
            count = cur.fetchone()[0]
            if count == 0:
                for p in BUILTIN_PROFILES:
                    self.save_profile(
                        profile=p,
                        change_note=f"Shipped built-in profile: {p.name}",
                        is_builtin=True,
                    )
        finally:
            sqlite_conn.close()

    def save_profile(
        self,
        profile: MappingProfile,
        change_note: str = "Initial profile creation",
        effective_from_period_id: Optional[int] = None,
        created_by: str = "system",
        is_builtin: Optional[bool] = None,
    ) -> MappingProfile:
        """Save a new mapping profile and its initial version (v1) with DimMapping entries."""
        if not profile.header_signature and profile.column_map:
            profile.header_signature = compute_header_signature(profile.column_map.keys())

        profile_is_builtin = profile.is_builtin if is_builtin is None else is_builtin

        sqlite_conn = self.db.get_sqlite_connection()
        try:
            with sqlite_conn:
                cur = sqlite_conn.execute(
                    """
                    INSERT INTO MappingProfile (
                        name, source_type, header_signature, sheet_selector, header_row,
                        delimiter, encoding, date_rule, number_rule, is_builtin
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile.name,
                        profile.source_type,
                        profile.header_signature,
                        profile.sheet_selector,
                        profile.header_row,
                        profile.delimiter,
                        profile.encoding,
                        profile.date_rule,
                        profile.number_rule,
                        1 if profile_is_builtin else 0,
                    ),
                )
                profile_id = cur.lastrowid
                profile.profile_id = profile_id
                profile.is_builtin = profile_is_builtin
                profile.version_no = 1
                profile.effective_from_period_id = effective_from_period_id

                # Definition snapshot per 03 §5.5
                definition = {
                    "name": profile.name,
                    "source_type": profile.source_type,
                    "header_signature": profile.header_signature,
                    "sheet_selector": profile.sheet_selector,
                    "header_row": profile.header_row,
                    "delimiter": profile.delimiter,
                    "encoding": profile.encoding,
                    "date_rule": profile.date_rule,
                    "number_rule": profile.number_rule,
                    "column_map": profile.column_map,
                    "transforms": profile.transforms,
                }

                sqlite_conn.execute(
                    """
                    INSERT INTO MappingProfileVersion (
                        profile_id, version_no, definition, effective_from_period_id,
                        change_note, is_current, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile_id,
                        1,
                        json.dumps(definition),
                        effective_from_period_id,
                        change_note,
                        1,
                        created_by,
                    ),
                )

                # Insert initial DimMapping rows in SQLite
                dim_rows = []
                for src_col, canon_field in profile.column_map.items():
                    transform_json = (
                        json.dumps(profile.transforms[src_col])
                        if src_col in profile.transforms
                        else None
                    )
                    cur_dim = sqlite_conn.execute(
                        """
                        INSERT INTO DimMapping (
                            profile_id, version_no, source_system, source_column,
                            canonical_field, transform, effective_from_period_id,
                            approved_by, is_active, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            profile_id,
                            1,
                            profile.source_type,
                            src_col,
                            canon_field,
                            transform_json,
                            effective_from_period_id,
                            created_by,
                            1,
                            change_note,
                        ),
                    )
                    mapping_id = cur_dim.lastrowid
                    dim_rows.append((
                        mapping_id,
                        profile_id,
                        1,
                        profile.source_type,
                        src_col,
                        canon_field,
                        transform_json,
                        effective_from_period_id,
                        created_by,
                        datetime.now(),
                        True,
                        change_note,
                    ))
        finally:
            sqlite_conn.close()

        # Insert DimMapping rows into DuckDB analytical store per 03 §3.8
        if dim_rows:
            duck_conn = self.db.get_duckdb_connection()
            try:
                duck_conn.executemany(
                    """
                    INSERT INTO DimMapping (
                        mapping_id, profile_id, version_no, source_system, source_column,
                        canonical_field, transform, effective_from_period_id, approved_by,
                        approved_at, is_active, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    dim_rows,
                )
            finally:
                duck_conn.close()

        return profile

    def create_version(
        self,
        profile_id: int,
        column_map: Dict[str, str],
        change_note: str,
        effective_from_period_id: Optional[int] = None,
        created_by: str = "system",
        transforms: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        encoding: Optional[str] = None,
        date_rule: Optional[str] = None,
        number_rule: Optional[str] = None,
        sheet_selector: Optional[str] = None,
        header_row: Optional[int] = None,
    ) -> MappingProfileVersion:
        """Create a new immutable version of a profile per 04 §5.3.
        
        Editing a profile creates a new version with effective_from_period_id and change_note.
        Built-in profiles are read-only (raises ValueError if attempted).
        """
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            with sqlite_conn:
                cur = sqlite_conn.execute(
                    "SELECT * FROM MappingProfile WHERE profile_id = ?",
                    (profile_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Profile {profile_id} not found.")

                if row["is_builtin"]:
                    raise ValueError("Built-in profiles are read-only; clone to edit.")

                # Retrieve latest version number
                cur_v = sqlite_conn.execute(
                    "SELECT MAX(version_no) FROM MappingProfileVersion WHERE profile_id = ?",
                    (profile_id,),
                )
                current_max = cur_v.fetchone()[0] or 0
                next_version_no = current_max + 1

                # Previous versions become is_current = 0
                sqlite_conn.execute(
                    "UPDATE MappingProfileVersion SET is_current = 0 WHERE profile_id = ?",
                    (profile_id,),
                )

                # Compute new signature
                new_signature = compute_header_signature(column_map.keys())

                # Resolve updated metadata or keep previous
                del_val = delimiter if delimiter is not None else row["delimiter"]
                enc_val = encoding if encoding is not None else row["encoding"]
                dt_val = date_rule if date_rule is not None else row["date_rule"]
                num_val = number_rule if number_rule is not None else row["number_rule"]
                sheet_val = sheet_selector if sheet_selector is not None else row["sheet_selector"]
                h_row_val = header_row if header_row is not None else row["header_row"]
                trans_val = transforms if transforms is not None else {}

                # Update profile record with latest metadata
                sqlite_conn.execute(
                    """
                    UPDATE MappingProfile
                    SET header_signature = ?, delimiter = ?, encoding = ?,
                        date_rule = ?, number_rule = ?, sheet_selector = ?, header_row = ?
                    WHERE profile_id = ?
                    """,
                    (new_signature, del_val, enc_val, dt_val, num_val, sheet_val, h_row_val, profile_id),
                )

                definition = {
                    "name": row["name"],
                    "source_type": row["source_type"],
                    "header_signature": new_signature,
                    "sheet_selector": sheet_val,
                    "header_row": h_row_val,
                    "delimiter": del_val,
                    "encoding": enc_val,
                    "date_rule": dt_val,
                    "number_rule": num_val,
                    "column_map": column_map,
                    "transforms": trans_val,
                }

                cur_new_v = sqlite_conn.execute(
                    """
                    INSERT INTO MappingProfileVersion (
                        profile_id, version_no, definition, effective_from_period_id,
                        change_note, is_current, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile_id,
                        next_version_no,
                        json.dumps(definition),
                        effective_from_period_id,
                        change_note,
                        1,
                        created_by,
                    ),
                )
                version_id = cur_new_v.lastrowid

                # Deactivate previous DimMapping entries in SQLite
                sqlite_conn.execute(
                    "UPDATE DimMapping SET is_active = 0 WHERE profile_id = ?",
                    (profile_id,),
                )

                dim_rows = []
                for src_col, canon_field in column_map.items():
                    transform_json = (
                        json.dumps(trans_val[src_col])
                        if src_col in trans_val
                        else None
                    )
                    cur_dim = sqlite_conn.execute(
                        """
                        INSERT INTO DimMapping (
                            profile_id, version_no, source_system, source_column,
                            canonical_field, transform, effective_from_period_id,
                            approved_by, is_active, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            profile_id,
                            next_version_no,
                            row["source_type"],
                            src_col,
                            canon_field,
                            transform_json,
                            effective_from_period_id,
                            created_by,
                            1,
                            change_note,
                        ),
                    )
                    mapping_id = cur_dim.lastrowid
                    dim_rows.append((
                        mapping_id,
                        profile_id,
                        next_version_no,
                        row["source_type"],
                        src_col,
                        canon_field,
                        transform_json,
                        effective_from_period_id,
                        created_by,
                        datetime.now(),
                        True,
                        change_note,
                    ))
        finally:
            sqlite_conn.close()

        # Update DimMapping in DuckDB
        duck_conn = self.db.get_duckdb_connection()
        try:
            duck_conn.execute(
                "UPDATE DimMapping SET is_active = FALSE WHERE profile_id = ?",
                [profile_id],
            )
            if dim_rows:
                duck_conn.executemany(
                    """
                    INSERT INTO DimMapping (
                        mapping_id, profile_id, version_no, source_system, source_column,
                        canonical_field, transform, effective_from_period_id, approved_by,
                        approved_at, is_active, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    dim_rows,
                )
        finally:
            duck_conn.close()

        return MappingProfileVersion(
            version_id=version_id,
            profile_id=profile_id,
            version_no=next_version_no,
            definition=definition,
            effective_from_period_id=effective_from_period_id,
            change_note=change_note,
            is_current=True,
            created_by=created_by,
        )

    def clone_profile(
        self,
        source_profile_id: int,
        new_name: str,
        created_by: str = "system",
    ) -> MappingProfile:
        """Clone an existing profile (especially built-ins) per 04 §5.4.
        
        Shipped profiles are read-only; clone to edit. The clone is created with
        is_builtin=False and version 1.
        """
        source_profile = self.get_active_profile_by_id(source_profile_id)
        if not source_profile:
            raise ValueError(f"Source profile {source_profile_id} not found.")

        cloned_profile = MappingProfile(
            profile_id=0,
            name=new_name,
            source_type=source_profile.source_type,
            column_map=dict(source_profile.column_map),
            delimiter=source_profile.delimiter,
            encoding=source_profile.encoding,
            header_row=source_profile.header_row,
            date_rule=source_profile.date_rule,
            number_rule=source_profile.number_rule,
            sheet_selector=source_profile.sheet_selector,
            header_signature=source_profile.header_signature,
            is_builtin=False,
            transforms=dict(source_profile.transforms),
        )

        return self.save_profile(
            profile=cloned_profile,
            change_note=f"Cloned from '{source_profile.name}' (profile_id={source_profile_id}, v{source_profile.version_no})",
            created_by=created_by,
            is_builtin=False,
        )

    def get_active_profile_by_id(
        self,
        profile_id: int,
        period_id: Optional[int] = None,
    ) -> Optional[MappingProfile]:
        """Retrieve active mapping profile by profile_id and optional period_id."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            cur = sqlite_conn.execute(
                "SELECT * FROM MappingProfile WHERE profile_id = ?",
                (profile_id,),
            )
            p_row = cur.fetchone()
            if not p_row:
                return None

            # Resolve version
            if period_id is not None:
                cur_v = sqlite_conn.execute(
                    """
                    SELECT * FROM MappingProfileVersion
                    WHERE profile_id = ?
                      AND (effective_from_period_id IS NULL OR effective_from_period_id <= ?)
                    ORDER BY (effective_from_period_id IS NOT NULL) DESC, effective_from_period_id DESC, version_no DESC
                    LIMIT 1
                    """,
                    (profile_id, period_id),
                )
            else:
                cur_v = sqlite_conn.execute(
                    """
                    SELECT * FROM MappingProfileVersion
                    WHERE profile_id = ? AND is_current = 1
                    LIMIT 1
                    """,
                    (profile_id,),
                )

            v_row = cur_v.fetchone()
            if not v_row:
                # Fallback to latest version
                cur_v = sqlite_conn.execute(
                    """
                    SELECT * FROM MappingProfileVersion
                    WHERE profile_id = ?
                    ORDER BY version_no DESC
                    LIMIT 1
                    """,
                    (profile_id,),
                )
                v_row = cur_v.fetchone()

            return self._build_profile_from_rows(p_row, v_row)
        finally:
            sqlite_conn.close()

    def get_active_profile_by_source_type(
        self,
        source_type: str,
        period_id: Optional[int] = None,
    ) -> Optional[MappingProfile]:
        """Retrieve active mapping profile by source_type and optional period_id.
        
        Prefers custom profiles (is_builtin=0) over built-in profiles (is_builtin=1).
        """
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            cur = sqlite_conn.execute(
                """
                SELECT * FROM MappingProfile
                WHERE source_type = ?
                ORDER BY is_builtin ASC, profile_id DESC
                """,
                (source_type,),
            )
            candidates = cur.fetchall()
            if not candidates:
                return None

            # Pick top candidate profile
            chosen_profile_id = candidates[0]["profile_id"]
            return self.get_active_profile_by_id(chosen_profile_id, period_id=period_id)
        finally:
            sqlite_conn.close()

    def get_profile_by_id(self, profile_id: int) -> Optional[MappingProfile]:
        """Convenience alias for get_active_profile_by_id."""
        return self.get_active_profile_by_id(profile_id)

    def get_profile_by_name(self, name: str) -> Optional[MappingProfile]:
        """Retrieve profile by unique name."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            cur = sqlite_conn.execute("SELECT profile_id FROM MappingProfile WHERE name = ?", (name,))
            row = cur.fetchone()
            if not row:
                return None
            return self.get_active_profile_by_id(row["profile_id"])
        finally:
            sqlite_conn.close()

    def list_profiles(
        self,
        source_type: Optional[str] = None,
        include_builtin: bool = True,
    ) -> List[MappingProfile]:
        """List mapping profiles with optional source_type filter."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            query = "SELECT profile_id FROM MappingProfile WHERE 1=1"
            params = []
            if source_type:
                query += " AND source_type = ?"
                params.append(source_type)
            if not include_builtin:
                query += " AND is_builtin = 0"
            query += " ORDER BY is_builtin ASC, profile_id ASC"

            cur = sqlite_conn.execute(query, params)
            rows = cur.fetchall()
            results = []
            for r in rows:
                p = self.get_active_profile_by_id(r["profile_id"])
                if p:
                    results.append(p)
            return results
        finally:
            sqlite_conn.close()

    def list_profile_versions(self, profile_id: int) -> List[MappingProfileVersion]:
        """List all versions of a mapping profile ordered by version_no."""
        sqlite_conn = self.db.get_sqlite_connection()
        try:
            cur = sqlite_conn.execute(
                """
                SELECT * FROM MappingProfileVersion
                WHERE profile_id = ?
                ORDER BY version_no ASC
                """,
                (profile_id,),
            )
            rows = cur.fetchall()
            versions = []
            for r in rows:
                defn = json.loads(r["definition"]) if isinstance(r["definition"], str) else r["definition"]
                versions.append(
                    MappingProfileVersion(
                        version_id=r["version_id"],
                        profile_id=r["profile_id"],
                        version_no=r["version_no"],
                        definition=defn,
                        effective_from_period_id=r["effective_from_period_id"],
                        change_note=r["change_note"],
                        is_current=bool(r["is_current"]),
                        created_at=r["created_at"],
                        created_by=r["created_by"],
                    )
                )
            return versions
        finally:
            sqlite_conn.close()

    def get_dim_mappings(
        self,
        profile_id: int,
        version_no: Optional[int] = None,
    ) -> List[DimMapping]:
        """Retrieve DimMapping records for a profile from DuckDB (with SQLite fallback)."""
        duck_conn = self.db.get_duckdb_connection()
        try:
            if version_no is not None:
                cur = duck_conn.execute(
                    """
                    SELECT * FROM DimMapping
                    WHERE profile_id = ? AND version_no = ?
                    ORDER BY mapping_id ASC
                    """,
                    [profile_id, version_no],
                )
            else:
                cur = duck_conn.execute(
                    """
                    SELECT * FROM DimMapping
                    WHERE profile_id = ? AND is_active = TRUE
                    ORDER BY mapping_id ASC
                    """,
                    [profile_id],
                )
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                data = dict(zip(cols, row))
                tf = data.get("transform")
                tf_dict = json.loads(tf) if tf and isinstance(tf, str) else None
                results.append(
                    DimMapping(
                        mapping_id=data["mapping_id"],
                        profile_id=data["profile_id"],
                        version_no=data["version_no"],
                        source_system=data["source_system"],
                        source_column=data["source_column"],
                        canonical_field=data["canonical_field"],
                        transform=tf_dict,
                        effective_from_period_id=data.get("effective_from_period_id"),
                        approved_by=data.get("approved_by"),
                        approved_at=str(data.get("approved_at")) if data.get("approved_at") else None,
                        is_active=bool(data.get("is_active", True)),
                        notes=data.get("notes"),
                        created_at=str(data.get("created_at")) if data.get("created_at") else None,
                    )
                )
            return results
        finally:
            duck_conn.close()

    def _build_profile_from_rows(
        self,
        p_row: sqlite3.Row,
        v_row: Optional[sqlite3.Row],
    ) -> MappingProfile:
        """Construct MappingProfile instance by merging profile row and version snapshot."""
        col_map = {}
        transforms = {}
        version_no = 1
        effective_period = None

        if v_row:
            version_no = v_row["version_no"]
            effective_period = v_row["effective_from_period_id"]
            defn = json.loads(v_row["definition"]) if isinstance(v_row["definition"], str) else v_row["definition"]
            col_map = defn.get("column_map", {})
            transforms = defn.get("transforms", {})

        return MappingProfile(
            profile_id=p_row["profile_id"],
            name=p_row["name"],
            source_type=p_row["source_type"],
            column_map=col_map,
            delimiter=p_row["delimiter"] or ",",
            encoding=p_row["encoding"] or "utf-8",
            header_row=p_row["header_row"] or 1,
            date_rule=p_row["date_rule"] or "iso",
            number_rule=p_row["number_rule"] or "standard",
            sheet_selector=p_row["sheet_selector"],
            header_signature=p_row["header_signature"],
            is_builtin=bool(p_row["is_builtin"]),
            version_no=version_no,
            effective_from_period_id=effective_period,
            transforms=transforms,
            created_at=p_row["created_at"],
        )
