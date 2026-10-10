"""Close the FR-IMP-008 seam between the mapping review queue and the importer.

FR-IMP-008 (doc 02 line 305) acceptance criterion, quoted:

    "a suggestion accepted during import N is applied automatically in import
    N+1 and appears in the mapping profile history."

This module owns the "applied automatically" half. The queue (`mapping_suggestions`)
proposes and a human decides; this module takes a human's decision and writes it
into a mapping profile version via `MappingRepository.create_version`, so the next
parse picks it up.

WHY A SEPARATE MODULE
---------------------
`MappingSuggestionRepository` deliberately CANNOT apply anything - keeping "propose"
and "apply" apart is what makes the Addon 3 C.1 guarantee ("AI may only PROPOSE")
auditable. The bridge belongs here, in the import path, where applying is an
explicit, requested act.

THE ONE INVARIANT THAT MATTERS
------------------------------
`MappingSuggestionRepository.applyable_for_run(run_id)` excludes suggestions
raised BY that same run (`import_run_id <> ?`). So calling this resolver with the
current run's id can never apply a suggestion the current run produced. The
same-run guarantee is therefore enforced at the query level, not by a filter that
could be forgotten.

ORDER OF OPERATIONS IN ONE IMPORT
---------------------------------
1. `next_import_run_id()` gives the id the batch is ABOUT to be committed under.
2. `resolve_profile_for_import()` folds in every accepted/edited suggestion from a
   STRICTLY EARLIER run, returning the profile the parser should use.
3. Parse and commit. The committed batch gets exactly that id.

Steps 1 and 2 share the same predicted id, which is why a suggestion raised during
import N can never be seen by import N itself: at step 2 of run N the query
excludes run N.

RUN ID PREDICTION ASSUMPTION
----------------------------
`next_import_run_id()` reads `MAX(FactImportBatch.batch_id) + 1`. This is exact
because imports are serialized single-writer SQLite operations - the same
assumption the rest of the import path already makes. `commit_batch` returns the
authoritative id, so callers that can compare should; `verify_run_id_prediction()`
does that comparison and reports drift rather than hiding it.

IDEMPOTENCE
-----------
`MappingSuggestionApplication` is UNIQUE on `suggestion_id`. Once a suggestion has
been baked into a profile version it is never applied again, so re-resolving the
profile on runs N+1, N+2, ... produces the SAME column map and does NOT bump the
profile version each time. Without this, every subsequent import would create a new
version forever and the profile history would be meaningless.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engine.imports.mapping_suggestions import MappingSuggestion
from app.engine.imports.profiles import MappingProfile, normalize_header
from app.engine.store.db import DatabaseManager
from app.engine.store.mapping_repo import MappingRepository
from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

#: Deterministic suffix for the editable clone of a built-in profile. Reusing one
#: name means a second application round reuses the existing clone instead of
#: littering the profile list with a new copy per run.
REVIEWED_PROFILE_SUFFIX = " (reviewed)"


@dataclass
class ProfileBindingResult:
    """Outcome of resolving the effective profile for one import run."""

    profile: MappingProfile | None
    import_run_id: int
    applied: list[MappingSuggestion] = field(default_factory=list)
    already_applied: list[MappingSuggestion] = field(default_factory=list)
    version_no: int | None = None
    cloned_from_builtin: bool = False

    @property
    def changed(self) -> bool:
        return bool(self.applied)

    def to_dict(self) -> dict[str, Any]:
        return {
            "importRunId": self.import_run_id,
            "profileId": self.profile.profile_id if self.profile else None,
            "profileName": self.profile.name if self.profile else None,
            "versionNo": self.version_no,
            "changed": self.changed,
            "clonedFromBuiltin": self.cloned_from_builtin,
            "applied": [
                {
                    "suggestionId": s.suggestion_id,
                    "sourceColumn": s.source_column,
                    "targetField": s.effective_target_field,
                    "state": s.state,
                }
                for s in self.applied
            ],
            "alreadyApplied": [s.suggestion_id for s in self.already_applied],
        }


def next_import_run_id(db_manager: DatabaseManager) -> int:
    """The `FactImportBatch.batch_id` the next commit will receive.

    Used both when enqueuing suggestions for a run and when resolving that run's
    profile, so both sides agree on the run's identity.
    """
    conn = db_manager.get_sqlite_connection()
    try:
        row = conn.execute("SELECT MAX(batch_id) FROM FactImportBatch").fetchone()
        return int(row[0] or 0) + 1
    finally:
        conn.close()


def verify_run_id_prediction(db_manager: DatabaseManager) -> tuple[int, int]:
    """(predicted_next_id, max_committed_id).

    A caller that has just committed can compare its actual batch id against the
    prediction made earlier. Equality is expected under single-writer imports;
    a caller that sees drift should log it, not silently re-key suggestions.
    """
    conn = db_manager.get_sqlite_connection()
    try:
        row = conn.execute("SELECT MAX(batch_id) FROM FactImportBatch").fetchone()
        max_committed = int(row[0] or 0)
        return max_committed + 1, max_committed
    finally:
        conn.close()


def resolve_base_profile(
    db_manager: DatabaseManager,
    sample_headers: list[str],
    source_type: str = "actuals_d365",
) -> MappingProfile | None:
    """Pick the profile to fold accepted suggestions into, before parsing.

    Fingerprint match first (doc 04 section 5.1), then fall back to the active
    profile for `source_type`.

    The fallback is not cosmetic: `match_profile` returns None whenever a file's
    headers do not fingerprint-match a shipped profile, and a caller that passed
    None straight through would silently skip the whole seam - an accepted
    suggestion would then never apply, and the reason would be invisible. Since
    the fallback profile is what the parser would use anyway, folding suggestions
    into it is always the correct target.
    """
    from app.engine.imports.profiles import match_profile

    matched = match_profile(sample_headers)
    if matched is not None:
        return matched
    return MappingRepository(db_manager).get_active_profile_by_source_type(source_type)


def _changed_entries(
    column_map: dict[str, str],
    pending: list[MappingSuggestion],
) -> dict[str, str]:
    """Entries the merge would actually add or change.

    Empty means the accepted suggestions agree with the profile as it stands, so
    applying them is a genuine no-op.
    """
    out: dict[str, str] = {}
    for s in pending:
        key = normalize_header(s.source_column)
        value = s.effective_target_field
        if column_map.get(key) != value:
            out[key] = value
    return out


def _ensure_editable_profile(
    mapping_repo: MappingRepository,
    base_profile: MappingProfile | None,
) -> tuple[MappingProfile | None, bool]:
    """Return a writable profile, cloning a built-in one if needed.

    `create_version` refuses built-in profiles ("Built-in profiles are read-only;
    clone to edit", doc 04 section 5.4). The clone is looked up by deterministic
    name first so repeated applications reuse it.
    """
    if base_profile is None:
        return None, False

    if not base_profile.is_builtin:
        return mapping_repo.get_active_profile_by_id(base_profile.profile_id), False

    clone_name = f"{base_profile.name}{REVIEWED_PROFILE_SUFFIX}"
    existing = mapping_repo.get_profile_by_name(clone_name)
    if existing is not None:
        return mapping_repo.get_active_profile_by_id(existing.profile_id), False

    cloned = mapping_repo.clone_profile(
        source_profile_id=base_profile.profile_id,
        new_name=clone_name,
        created_by="mapping_review_queue",
    )
    return cloned, True


def resolve_profile_for_import(
    db_manager: DatabaseManager,
    base_profile: MappingProfile | None = None,
    import_run_id: int | None = None,
    created_by: str = "mapping_review_queue",
) -> ProfileBindingResult:
    """Fold every applyable accepted suggestion into the profile for this run.

    Returns the profile the importer should parse with. When nothing is applyable
    the base profile is returned untouched and NO version is created - an import
    with no accepted suggestions must not dirty the profile history.

    Steps:
      1. `applyable_for_import_run(run_id)` - accepted/edited, raised by an EARLIER
         run. This is the no-same-run guarantee.
      2. Drop any already applied (idempotence).
      3. Merge `normalized source_column -> resolved_target_field` over the
         existing column map.
      4. `MappingRepository.create_version` - the single apply point, which is
         what makes the change "appear in the mapping profile history".
    """
    run_id = int(import_run_id) if import_run_id is not None else next_import_run_id(db_manager)

    suggestion_repo = MappingSuggestionRepository(db_manager)
    applyable = suggestion_repo.applyable_for_run(run_id)

    if not applyable:
        return ProfileBindingResult(profile=base_profile, import_run_id=run_id)

    seen = suggestion_repo.already_applied([s.suggestion_id for s in applyable if s.suggestion_id])
    pending = [s for s in applyable if s.suggestion_id not in seen]
    already = [s for s in applyable if s.suggestion_id in seen]

    if not pending:
        # Everything was applied on an earlier run. Return the profile as-is and
        # do NOT create a version - this is what keeps repeated imports from
        # bumping the version forever.
        return ProfileBindingResult(
            profile=base_profile,
            import_run_id=run_id,
            already_applied=already,
        )

    if base_profile is None:
        return ProfileBindingResult(profile=None, import_run_id=run_id, already_applied=already)

    # Check whether the merge would change anything BEFORE touching the profile
    # store. A reviewer accepting a suggestion that already matches the current
    # mapping is a no-op for parsing: it must not clone a profile, bump a
    # version, or pollute the profile history.
    if not _changed_entries(base_profile.column_map, pending):
        return ProfileBindingResult(
            profile=base_profile,
            import_run_id=run_id,
            already_applied=already,
        )

    # auto_seed defaults True: cloning a built-in profile reads it from the DB,
    # so the shipped profiles must exist there. Seeding is idempotent.
    mapping_repo = MappingRepository(db_manager)
    profile, cloned = _ensure_editable_profile(mapping_repo, base_profile)
    if profile is None:
        return ProfileBindingResult(profile=None, import_run_id=run_id, already_applied=already)

    merged: dict[str, str] = dict(profile.column_map)
    for s in pending:
        merged[normalize_header(s.source_column)] = s.effective_target_field

    changed_map = _changed_entries(profile.column_map, pending)
    if not changed_map:
        return ProfileBindingResult(
            profile=profile,
            import_run_id=run_id,
            already_applied=already,
            cloned_from_builtin=cloned,
        )

    change_note = (
        f"Applied {len(pending)} accepted mapping suggestion(s) from import run(s) "
        f"{sorted({s.import_run_id for s in pending})}: "
        + ", ".join(
            f"{s.source_column} -> {s.effective_target_field} (#{s.suggestion_id}, {s.state})"
            for s in pending
        )
        + f". Applied automatically by import run {run_id} per FR-IMP-008."
    )

    version = mapping_repo.create_version(
        profile_id=profile.profile_id,
        column_map=merged,
        change_note=change_note,
        created_by=created_by,
    )

    suggestion_repo.record_applications(
        [
            {
                "suggestion_id": s.suggestion_id,
                "profile_id": profile.profile_id,
                "version_no": version.version_no,
                "import_run_id": run_id,
                "source_column": s.source_column,
                "canonical_field": s.effective_target_field,
            }
            for s in pending
        ]
    )

    return ProfileBindingResult(
        profile=mapping_repo.get_active_profile_by_id(profile.profile_id),
        import_run_id=run_id,
        applied=pending,
        already_applied=already,
        version_no=version.version_no,
        cloned_from_builtin=cloned,
    )


def unmapped_columns_for_headers(
    profile: MappingProfile | None,
    headers: list[str],
) -> list[str]:
    """Source columns in `headers` the profile does not map.

    This is the trigger condition FR-IMP-008 names: "When a file has unmapped
    columns ... AI may propose mappings". The queue is surfaced only for files
    with at least one of these.
    """
    if profile is None:
        return [h.strip() for h in headers if h.strip()]
    column_map = profile.column_map
    return [h.strip() for h in headers if h.strip() and normalize_header(h) not in column_map]
