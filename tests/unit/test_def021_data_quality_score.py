"""DEF-021 regression: FactImportBatch.data_quality_score must be computed, not hardcoded.

Originally filed as DEF-009; renumbered to DEF-021 on 2026-10-03 because DEF-009
is authoritative in docs/28 for the acceptance-harness absence. This file was
renamed from test_def009_data_quality_score.py to match.

Before the fix, app/engine/store/import_repo.py wrote the literal 100.0 into
data_quality_score for every batch regardless of check outcomes. A rejected,
unbalanced file therefore still reported "100% data quality" to the client.

Per 05 §8 (CALC-050) the score is derived from the check reports, and §8.2
guarantee 1 states that any failed High-severity check must cap the score at 96.
"""
from decimal import Decimal

import pytest

from app.engine.imports.models import ImportBatchResult, ValidationCheckReport
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository


def _batch(checks, source_type="actuals_d365", is_balanced=True):
    return ImportBatchResult(
        batch_id=0,
        file_name="dq_probe.csv",
        file_checksum="dq-probe",
        source_type=source_type,
        total_source_rows=2,
        loaded_count=2,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=is_balanced,
        total_debit=Decimal("100.00"),
        total_credit=Decimal("0.00"),
        net_imbalance=Decimal("100.00"),
        checks=checks,
        quarantined_rows=[],
    )


def _stored_score(repo, batch_id):
    conn = repo.db.get_sqlite_connection()
    row = conn.execute(
        "SELECT data_quality_score FROM FactImportBatch WHERE batch_id = ?",
        (batch_id,),
    ).fetchone()
    conn.close()
    assert row is not None, "batch row missing from FactImportBatch"
    return Decimal(str(row[0]))


def test_failed_high_severity_check_deducts_from_score(tmp_path):
    """IMP-023 failing (severity high) must not persist a perfect score."""
    repo = ImportRepository(DatabaseManager(tmp_path / "dq_fail.db"))
    batch = _batch(
        [
            ValidationCheckReport(
                check_code="IMP-001",
                check_name="File readable",
                status="pass",
                severity="high",
                offending_count=0,
                detail="OK",
                weight=Decimal("10"),
            ),
            ValidationCheckReport(
                check_code="IMP-023",
                check_name="Debit = credit balance within tolerance",
                status="fail",
                severity="high",
                offending_count=2,
                detail="Imbalance 100.00 exceeds tolerance 0.00",
                weight=Decimal("10"),
            ),
        ],
        is_balanced=False,
    )

    batch_id = repo.commit_batch(batch, [])
    score = _stored_score(repo, batch_id)

    assert score < Decimal("100"), f"DEF-009 regression: score persisted as {score}"
    # 05 §8.2 guarantee 1: one failed high check caps the score at 96.
    assert score <= Decimal("96"), f"05 §8.2 bound violated, score={score}"


def test_clean_batch_scores_full_marks(tmp_path):
    """A batch whose checks all pass still records 100 - the fix is not a blanket deduction."""
    repo = ImportRepository(DatabaseManager(tmp_path / "dq_clean.db"))
    batch = _batch(
        [
            ValidationCheckReport(
                check_code="IMP-001",
                check_name="File readable",
                status="pass",
                severity="high",
                offending_count=0,
                detail="OK",
                weight=Decimal("10"),
            ),
            ValidationCheckReport(
                check_code="IMP-021",
                check_name="Zero-amount rows noted",
                status="pass",
                severity="low",
                offending_count=0,
                detail="OK",
                weight=Decimal("2"),
            ),
        ]
    )

    batch_id = repo.commit_batch(batch, [])
    assert _stored_score(repo, batch_id) == Decimal("100")


@pytest.mark.parametrize("status,expected_below_100", [("warn", True), ("fail", True), ("pass", False)])
def test_score_tracks_check_status(tmp_path, status, expected_below_100):
    """Score must move with check status rather than ignoring the reports."""
    repo = ImportRepository(DatabaseManager(tmp_path / f"dq_{status}.db"))
    batch = _batch(
        [
            ValidationCheckReport(
                check_code="IMP-024",
                check_name="Row-count reconciliation",
                status=status,
                severity="medium",
                offending_count=1 if status != "pass" else 0,
                detail="probe",
                weight=Decimal("5"),
            ),
        ],
        is_balanced=False,
    )

    batch_id = repo.commit_batch(batch, [])
    score = _stored_score(repo, batch_id)
    if expected_below_100:
        assert score < Decimal("100"), f"status={status} must deduct, got {score}"
    else:
        assert score == Decimal("100")