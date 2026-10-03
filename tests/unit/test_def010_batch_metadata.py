"""DEF-010 regression: a committed batch must never record `status='rejected'`.

THE DEFECT. `ImportRepository.commit_batch` computed the batch's `status` from
`is_balanced` alone:

    status = "committed" if batch.is_balanced else "rejected"

but decided whether to actually write the rows from a different expression:

    should_commit = batch.is_balanced or (batch.source_type != "actuals_d365")

For an unbalanced SUB-LEDGER those disagree. Measured before the fix:
`bank_ledger_actuals.csv` and `payroll_procurement_actuals.csv` were both
recorded `status='rejected'` while **every one of their rows was written to
`FactActual`** (499/499 and 399/399). `FactImportBatch` therefore contradicted
`FactActual` - an audit-integrity defect regardless of which spec is right,
because the audit trail is what an auditor reads.

THE FIX (spec-wins, docs/19 section 5.5). `should_commit` is computed once,
before the audit row is written, as `bool(batch.is_balanced)` for EVERY
source_type - doc 04 section 12 / IMP-023 (scope F, "Reject") states the
debit=credit reject unconditionally with no sub-ledger exemption - and
`status` records what actually happened to the rows. `is_balanced` still
records the measured balance fact. The earlier "committed with a balance
warning" encoding for unbalanced sub-ledgers is superseded: an unbalanced
file of any source type now commits zero rows and is recorded `rejected`.

RESOLVED PER DOCS/19 SECTION 5.5 (spec-wins). The doc-04-versus-code question -
whether doc 04 section 12 / `IMP-023` rejects sub-ledgers at all - is answered
by the spec text itself: IMP-023 is scope F with outcome Reject and section 12
states debit=credit per file with no sub-ledger exemption, so the code was
brought into compliance. `test_unbalanced_general_ledger_commits_nothing_and_is_rejected`
still pins the GL gate, and `test_tst_imp_023_r1_*` pins the same gate for
every other source type.
"""

from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from app.engine.imports.models import ImportBatchResult, ParsedTransaction
from app.engine.store.db import DatabaseManager
from app.engine.store.import_repo import ImportRepository

SOURCE_TYPES = ("actuals_d365", "actuals_payroll", "actuals_procurement")


def _transactions(n: int = 3) -> list[ParsedTransaction]:
    return [
        ParsedTransaction(
            source_row_ref=f"row_{i}", voucher_no=f"V{i}",
            posting_date="2026-09-15", document_date=None, company_code="IN01",
            account_code="5200", cost_center_code="CC-100", project_code=None,
            vendor_code="V-1", invoice_no="I-1", description="def010 fixture",
            debit=Decimal("100.00"), credit=Decimal("0.00"),
            net_amount=Decimal("100.00"), currency_code="INR",
            period_code="FY26-P09", raw_values={},
        )
        for i in range(n)
    ]


def _commit(tmp_path: Path, source_type: str, is_balanced: bool, n: int = 3):
    """Import one synthetic batch and return (batch_row, facts_written)."""
    db = DatabaseManager()
    batch = ImportBatchResult(
        batch_id=1, file_name=f"{source_type}.csv", file_checksum="c" * 64,
        source_type=source_type, total_source_rows=n, loaded_count=n,
        quarantined_count=0, rejected_count=0, is_balanced=is_balanced,
        total_debit=Decimal("100.00"), total_credit=Decimal("40.00"),
        net_imbalance=Decimal("60.00"),
    )
    batch_id = ImportRepository(db).commit_batch(batch, _transactions(n))

    sq = sqlite3.connect(str(db.sqlite_path))
    sq.row_factory = sqlite3.Row
    row = dict(sq.execute(
        "SELECT status, is_balanced, source_type FROM FactImportBatch "
        "WHERE batch_id = ?", (batch_id,)).fetchone())
    sq.close()

    conn = db.get_duckdb_connection()
    try:
        # Scoped to THIS batch: a test may commit more than once into the same
        # throwaway project dir, and an unscoped COUNT would be cumulative and
        # would report a phantom contradiction on the second commit.
        facts = conn.execute(
            "SELECT COUNT(*) FROM FactActual WHERE import_batch_id = ?",
            [batch_id],
        ).fetchone()[0]
    finally:
        conn.close()
    return row, facts


# ---------------------------------------------------------------------------
# The invariant
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("source_type", SOURCE_TYPES)
@pytest.mark.parametrize("is_balanced", [True, False])
def test_committed_batch_never_records_rejected(tmp_path, source_type, is_balanced):
    """`status='rejected'` with rows in `FactActual` must be impossible.

    Parametrised across every source type and both balance outcomes so the
    invariant is checked as a property of `commit_batch`, not as three
    hand-picked examples that could miss a fourth combination.
    """
    row, facts = _commit(tmp_path, source_type, is_balanced)

    if facts > 0:
        assert row["status"] != "rejected", (
            f"audit-integrity contradiction: {source_type} "
            f"(is_balanced={is_balanced}) wrote {facts} FactActual rows but recorded "
            f"status='rejected'. This is DEF-010."
        )
        assert row["status"] == "committed"


@pytest.mark.parametrize("source_type", SOURCE_TYPES)
def test_rejected_batch_commits_no_rows(tmp_path, source_type):
    """The converse: nothing may be rejected AND written."""
    for is_balanced in (True, False):
        row, facts = _commit(tmp_path, source_type, is_balanced)
        if row["status"] == "rejected":
            assert facts == 0, (
                f"{source_type} recorded 'rejected' but wrote {facts} rows"
            )


# ---------------------------------------------------------------------------
# The GL gate is load-bearing and unchanged
# ---------------------------------------------------------------------------

def test_unbalanced_general_ledger_commits_nothing_and_is_rejected(tmp_path):
    """Doc 04 §12 / IMP-023: an unbalanced GL must still commit zero rows.

    Guards the fix against over-reach. If someone ever "fixes" DEF-010 by
    dropping the GL gate, this fails.
    """
    row, facts = _commit(tmp_path, "actuals_d365", is_balanced=False)

    assert row["status"] == "rejected"
    assert row["is_balanced"] == 0
    assert facts == 0, "the general-ledger balance gate was relaxed"


def test_balanced_general_ledger_commits_and_records_committed(tmp_path):
    row, facts = _commit(tmp_path, "actuals_d365", is_balanced=True)

    assert row["status"] == "committed"
    assert row["is_balanced"] == 1
    assert facts == 3


# ---------------------------------------------------------------------------
# The pair must stay self-describing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("source_type", ["actuals_payroll", "actuals_procurement"])
def test_unbalanced_subledger_is_rejected_and_commits_nothing(
    tmp_path, source_type,
):
    """TST-IMP-023-R1 (sub-ledger half): doc 04 section 12 / IMP-023 rejects
    unbalanced files unconditionally - no sub-ledger exemption.

    `status` must be `rejected`, `is_balanced` must still record the measured
    balance fact (0), and zero rows may land in `FactActual`.
    """
    row, facts = _commit(tmp_path, source_type, is_balanced=False)

    assert row["status"] == "rejected", (
        f"DEF-010 spec-wins fix missing: unbalanced {source_type} must reject"
    )
    assert row["is_balanced"] == 0, (
        "is_balanced was rewritten to agree with status; it must keep recording "
        "the measured balance fact"
    )
    assert facts == 0, (
        f"unbalanced {source_type} must commit zero rows per IMP-023"
    )


@pytest.mark.parametrize("source_type", SOURCE_TYPES)
def test_tst_imp_023_r1_unbalanced_file_commits_zero_rows_and_audit_agrees(
    tmp_path, source_type,
):
    """TST-IMP-023-R1: an unbalanced file of EVERY source type commits 0 rows
    and the audit row agrees (`status='rejected'`, `is_balanced=0`).

    Doc 04 section 11 (reject vs quarantine): a file-level failure means
    "Nothing is committed. The batch is recorded as `rejected` ... and the
    file is not added to the analytic model". IMP-023 (debit = credit) is
    scope F with outcome Reject, so it is such a failure for GL and
    sub-ledgers alike.
    """
    row, facts = _commit(tmp_path, source_type, is_balanced=False)

    assert facts == 0, (
        f"TST-IMP-023-R1: unbalanced {source_type} committed {facts} rows"
    )
    assert row["status"] == "rejected", (
        f"TST-IMP-023-R1: unbalanced {source_type} recorded "
        f"status={row['status']!r}, expected 'rejected'"
    )
    assert row["is_balanced"] == 0