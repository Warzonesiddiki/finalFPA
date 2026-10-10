"""End-to-end proof of the FR-IMP-008 importer seam.

FR-IMP-008 (doc 02 line 305) acceptance criterion, quoted:

    "a suggestion accepted during import N is applied automatically in import
    N+1 and appears in the mapping profile history."

These tests walk the whole path with no mocking of the apply step:

    import N   -> unmapped column surfaces a suggestion -> human accepts
    import N+1 -> resolve_profile_for_import folds it into the profile ->
                  a NEW profile version is created (the history entry) ->
                  parsing the same file now populates the newly mapped field

and assert the two properties that make this safe: the suggestion is NOT applied
to the run that raised it, and re-resolving on later runs is idempotent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.imports.mapping_suggestions import build_suggestion_queue
from app.engine.imports.parser import parse_csv_transactions
from app.engine.imports.profile_binding import (
    next_import_run_id,
    resolve_profile_for_import,
    unmapped_columns_for_headers,
    verify_run_id_prediction,
)
from app.engine.imports.profiles import BUILTIN_PROFILES, normalize_header
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository
from app.engine.store.mapping_repo import MappingRepository
from app.engine.store.mapping_suggestion_repo import MappingSuggestionRepository

# A GL-shaped file whose `Cost Centre Ref` column is NOT in the shipped D365 map
# (which only knows "cost center" / "costcenter"). Debit and credit balance so the
# batch commits cleanly per 04 section 2.2.
CSV_BODY = (
    "Voucher,Posting Date,Company Code,Account,Cost Centre Ref,Debit,Credit,Description\n"
    "V-1,2026-09-02,IN01,6100,CC-120,1000.00,0.00,rent\n"
    "V-2,2026-09-03,IN01,6100,CC-120,0.00,1000.00,rent reversal\n"
)

UNMAPPED_COLUMN = "Cost Centre Ref"
TARGET_FIELD = "cost_center_code"


@pytest.fixture
def db(tmp_path) -> DatabaseManager:
    # DatabaseManager(tmp_path), NOT the shared default project dir: DuckDB is
    # single-writer and this test commits real rows.
    return DatabaseManager(tmp_path)


@pytest.fixture
def csv_file(tmp_path) -> Path:
    f = tmp_path / "gl_seam.csv"
    f.write_text(CSV_BODY, encoding="utf-8")
    return f


def _accept_suggestion(db: DatabaseManager, run_id: int, column: str, target: str):
    """Simulate import N raising a suggestion and a human accepting it."""
    repo = MappingSuggestionRepository(db)
    queue = build_suggestion_queue(
        run_id,
        [{"source_column": column, "target_field": target, "confidence": "0.93"}],
    )
    stored = repo.enqueue(queue)[0]
    return repo.decide(stored.suggestion_id, "accept", "Aarti")


# ---------------------------------------------------------------------------
# Trigger: the queue is surfaced only for files with unmapped columns
# ---------------------------------------------------------------------------


def test_unmapped_column_is_detected(csv_file):
    """FR-IMP-008: "When a file has unmapped columns ..."."""
    headers = CSV_BODY.splitlines()[0].split(",")
    assert UNMAPPED_COLUMN in unmapped_columns_for_headers(BUILTIN_PROFILES[0], headers)


def test_fully_mapped_file_surfaces_no_queue(csv_file):
    """A file with no unmapped columns must not raise a review queue."""
    headers = ["Voucher", "Posting Date", "Account", "Debit", "Credit"]
    assert unmapped_columns_for_headers(BUILTIN_PROFILES[0], headers) == []


def test_column_is_actually_unmapped_before_acceptance(csv_file):
    """Precondition: the field is empty on import N, populated on N+1."""
    _, before = parse_csv_transactions(csv_file, profile=BUILTIN_PROFILES[0])
    assert all(t.cost_center_code is None for t in before)


# ---------------------------------------------------------------------------
# THE ACCEPTANCE CRITERION: accepted in N, applied in N+1
# ---------------------------------------------------------------------------


def test_suggestion_accepted_in_run_n_applies_in_run_n_plus_one(db, csv_file):
    run_n = next_import_run_id(db)
    _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)

    # Import N+1 resolves the profile; the suggestion from N is folded in.
    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    assert [s.source_column for s in binding.applied] == [UNMAPPED_COLUMN]
    assert binding.version_no is not None
    assert binding.changed

    # The parser now picks the column up: this is the "applied automatically"
    # half, observed through the real parse path.
    _, after = parse_csv_transactions(csv_file, profile=binding.profile)
    assert {t.cost_center_code for t in after} == {"CC-120"}


def test_applied_mapping_appears_in_profile_history(db):
    """FR-IMP-008: "... and appears in the mapping profile history"."""
    run_n = next_import_run_id(db)
    suggestion = _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)

    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )

    versions = MappingRepository(db).list_profile_versions(binding.profile.profile_id)
    latest = next(v for v in versions if v.version_no == binding.version_no)

    assert latest.change_note.startswith("Applied 1 accepted mapping suggestion")
    assert UNMAPPED_COLUMN in latest.change_note
    assert TARGET_FIELD in latest.change_note
    assert f"#{suggestion.suggestion_id}" in latest.change_note
    # The version is the current one, so the next import resolves to it.
    assert latest.is_current

    # And the application log links the suggestion to that exact version.
    app_log = MappingSuggestionRepository(db).get_applications(suggestion.suggestion_id)
    assert len(app_log) == 1
    assert app_log[0]["version_no"] == binding.version_no
    assert app_log[0]["profile_id"] == binding.profile.profile_id
    assert app_log[0]["canonical_field"] == TARGET_FIELD


def test_normalized_header_is_used_as_the_map_key(db):
    """Profile column_map keys are normalized headers (doc 04 section 5.2).

    A reviewer may type "Cost  Centre Ref"; it must land on the same key the
    parser looks up, or the mapping would silently never apply.
    """
    run_n = next_import_run_id(db)
    _accept_suggestion(db, run_n, "  Cost   Centre Ref  ", TARGET_FIELD)

    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    assert binding.profile.column_map[normalize_header(UNMAPPED_COLUMN)] == TARGET_FIELD


# ---------------------------------------------------------------------------
# THE SAFETY PROPERTY: never applied to the run that raised it
# ---------------------------------------------------------------------------


def test_suggestion_is_not_applied_to_its_own_run(db):
    """FR-IMP-008: "Suggestions are never auto-applied in the same run"."""
    run_n = next_import_run_id(db)
    suggestion = _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)

    # Resolving for run N itself must find nothing to apply...
    same_run = resolve_profile_for_import(db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n)
    assert same_run.applied == []
    assert same_run.version_no is None
    assert same_run.changed is False

    # ...and must not have created a version, so run N's own file is parsed with
    # the profile as it stood before the suggestion existed.
    assert same_run.profile.column_map.get(normalize_header(UNMAPPED_COLUMN)) is None

    # The suggestion is still pending, not consumed.
    assert (
        MappingSuggestionRepository(db).get_suggestion(suggestion.suggestion_id).state == "accepted"
    )


def test_full_import_sequence_n_then_n_plus_one(db, csv_file):
    """The literal scenario, driven through commit_batch rather than by hand."""
    # ---- import N: file has an unmapped column, parsed with the base profile.
    run_n = next_import_run_id(db)
    batch_n, txs_n = parse_csv_transactions(csv_file, profile=BUILTIN_PROFILES[0])
    import_repo = ImportRepository(db)
    batch_id_n = import_repo.commit_batch(batch_n, txs_n)

    # The predicted run id is the id actually committed (single-writer import).
    predicted, max_committed = verify_run_id_prediction(db)
    assert batch_id_n == run_n == max_committed
    assert predicted == max_committed + 1

    assert all(t.cost_center_code is None for t in txs_n)

    # A reviewer accepts the suggestion raised by run N.
    _accept_suggestion(db, batch_id_n, UNMAPPED_COLUMN, TARGET_FIELD)

    # ---- import N+1: resolution folds the accepted suggestion in.
    binding = resolve_profile_for_import(db, base_profile=BUILTIN_PROFILES[0])
    assert binding.import_run_id == batch_id_n + 1
    assert [s.source_column for s in binding.applied] == [UNMAPPED_COLUMN]

    batch_n1, txs_n1 = parse_csv_transactions(csv_file, profile=binding.profile)
    batch_id_n1 = import_repo.commit_batch(batch_n1, txs_n1)

    assert batch_id_n1 == batch_id_n + 1
    assert {t.cost_center_code for t in txs_n1} == {"CC-120"}


# ---------------------------------------------------------------------------
# Idempotence: re-resolving must not churn the profile history
# ---------------------------------------------------------------------------


def test_repeated_imports_do_not_create_new_versions(db):
    """A suggestion is applied once, not once per subsequent import.

    Without the UNIQUE(suggestion_id) application log, every later import would
    create another identical version and the profile history would be useless.
    """
    run_n = next_import_run_id(db)
    _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)

    first = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    assert first.applied
    profile_id = first.profile.profile_id
    versions_after_first = len(MappingRepository(db).list_profile_versions(profile_id))

    for offset in (2, 3, 4):
        later = resolve_profile_for_import(
            db, base_profile=first.profile, import_run_id=run_n + offset
        )
        assert later.applied == [], f"run offset {offset} re-applied the suggestion"
        assert len(later.already_applied) == 1
        assert later.version_no is None

    assert len(MappingRepository(db).list_profile_versions(profile_id)) == versions_after_first


def test_accepting_a_matching_suggestion_creates_no_version(db):
    """An accept that changes nothing must not pollute the profile history."""
    run_n = next_import_run_id(db)
    # "Account" is ALREADY mapped to account_code in the shipped D365 profile.
    _accept_suggestion(db, run_n, "Account", "account_code")

    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    # Nothing to apply, so no clone, no version, and the shipped profile is
    # still what the next import parses with.
    assert binding.applied == []
    assert binding.cloned_from_builtin is False
    assert binding.version_no is None
    assert binding.profile.profile_id == BUILTIN_PROFILES[0].profile_id
    assert len(MappingRepository(db).list_profiles()) == len(BUILTIN_PROFILES)


def test_undecided_and_rejected_suggestions_never_apply(db):
    run_n = next_import_run_id(db)
    repo = MappingSuggestionRepository(db)

    suggested_only = repo.enqueue(
        build_suggestion_queue(
            run_n,
            [
                {
                    "source_column": "Still Pending",
                    "target_field": "project_code",
                    "confidence": "0.5",
                }
            ],
        )
    )[0]
    rejected = repo.enqueue(
        build_suggestion_queue(
            run_n,
            [
                {
                    "source_column": "Rejected Col",
                    "target_field": "project_code",
                    "confidence": "0.6",
                }
            ],
        )
    )[0]
    repo.decide(rejected.suggestion_id, "reject", "Aarti")

    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    assert binding.applied == []
    assert suggested_only.state == "suggested"


def test_edited_suggestion_applies_the_human_choice_not_the_proposal(db, csv_file):
    """FR-IMP-008 `suggested -> edited`: the human's target wins."""
    run_n = next_import_run_id(db)
    repo = MappingSuggestionRepository(db)
    stored = repo.enqueue(
        build_suggestion_queue(
            run_n,
            [
                {
                    "source_column": UNMAPPED_COLUMN,
                    "target_field": "project_code",
                    "confidence": "0.4",
                }
            ],
        )
    )[0]
    repo.decide(stored.suggestion_id, "edit", "Aarti", new_target_field=TARGET_FIELD)

    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    assert binding.profile.column_map[normalize_header(UNMAPPED_COLUMN)] == TARGET_FIELD

    _, txs = parse_csv_transactions(csv_file, profile=binding.profile)
    assert {t.cost_center_code for t in txs} == {"CC-120"}
    assert all(t.project_code is None for t in txs)


# ---------------------------------------------------------------------------
# Built-in profiles are read-only; the apply path clones rather than failing
# ---------------------------------------------------------------------------


def test_builtin_profile_is_cloned_not_edited(db):
    """doc 04 section 5.4: "Built-in profiles are read-only; clone to edit"."""
    run_n = next_import_run_id(db)
    _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)

    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    assert binding.cloned_from_builtin is True

    mapping_repo = MappingRepository(db)
    edited = mapping_repo.get_active_profile_by_id(binding.profile.profile_id)
    assert edited.is_builtin is False

    # The shipped profile is untouched: still v1, still read-only.
    shipped = mapping_repo.get_active_profile_by_id(BUILTIN_PROFILES[0].profile_id)
    assert shipped.version_no == 1
    assert shipped.column_map.get(normalize_header(UNMAPPED_COLUMN)) is None
    with pytest.raises(ValueError, match="read-only"):
        mapping_repo.create_version(
            profile_id=BUILTIN_PROFILES[0].profile_id,
            column_map=dict(shipped.column_map),
            change_note="should not be possible",
        )


def test_builtin_clone_is_reused_not_recreated(db):
    """A second application round reuses the clone instead of cloning again."""
    run_n = next_import_run_id(db)
    _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)

    first = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )
    _accept_suggestion(db, run_n + 1, "Project Ref", "project_code")
    second = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 2
    )

    assert first.profile.profile_id == second.profile.profile_id
    assert second.cloned_from_builtin is False  # nothing new to clone


# ---------------------------------------------------------------------------
# Committed facts reflect the applied mapping
# ---------------------------------------------------------------------------


def test_committed_actual_carries_the_applied_cost_center(db, csv_file):
    run_n = next_import_run_id(db)
    _accept_suggestion(db, run_n, UNMAPPED_COLUMN, TARGET_FIELD)
    binding = resolve_profile_for_import(
        db, base_profile=BUILTIN_PROFILES[0], import_run_id=run_n + 1
    )

    batch, txs = parse_csv_transactions(csv_file, profile=binding.profile)
    batch_id = ImportRepository(db).commit_batch(batch, txs)

    conn = db.get_duckdb_connection()
    try:
        rows = conn.execute(
            "SELECT cost_center_id FROM FactActual WHERE import_batch_id = ?",
            [batch_id],
        ).fetchall()
    finally:
        conn.close()

    assert rows, "no FactActual rows were committed"
    assert {r[0] for r in rows} == {120}  # CC-120 -> 120
