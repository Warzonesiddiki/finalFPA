"""Persistence path for catalog import rules' batch/row/control-total evidence."""

from decimal import Decimal

from app.engine.imports.models import (
    ImportBatchResult,
    ParsedTransaction,
    ValidationCheckReport,
)
from app.engine.rules.rules_catalog_001_008 import (
    evaluate_catalog_exc_001,
    evaluate_catalog_exc_002,
    evaluate_catalog_exc_003,
    evaluate_catalog_exc_006,
)
from app.engine.store.db import DatabaseManager
from app.engine.store.exceptions_repo import ExceptionsRepository
from app.engine.store.import_repo import ImportRepository


def test_import_metadata_survives_commit_and_reaches_rule_context(tmp_path):
    db = DatabaseManager(project_dir=tmp_path)
    tx = ParsedTransaction(
        source_row_ref="ledger.csv:14",
        voucher_no="VCH-14",
        posting_date="2026-09-22",
        company_code="IN02",
        account_code="5200",
        cost_center_code="CC-110",
        project_code=None,
        vendor_code="V-00931",
        invoice_no="INV-88213",
        description="test posting",
        debit=Decimal("1000.00"),
        credit=Decimal("650.00"),
        net_amount=Decimal("350.00"),
        currency_code="INR",
        line_no=7,
        period_code="FY26-P09",
    )
    control_total = {
        "scope": "gl_control_total",
        "supplied_total": "18400000.00",
        "loaded_total": "18399650.00",
        "tolerance": "0.00",
        "accepted": True,
        "acceptance_reason": (
            "Controller accepted the documented 350.00 tie-out variance"
        ),
        "accepted_by": "controller.test",
    }
    batch = ImportBatchResult(
        batch_id=0,
        file_name="d365_gl_actuals.csv",
        file_checksum="a" * 64,
        source_type="actuals_d365",
        total_source_rows=1,
        loaded_count=1,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=Decimal("18400000.00"),
        total_credit=Decimal("18399650.00"),
        net_imbalance=Decimal("350.00"),
        balance_tolerance=Decimal("500.00"),
        checks=[
            ValidationCheckReport(
                check_code="IMP-025",
                check_name="Control-total variance",
                status="warn",
                severity="high",
                offending_count=1,
                detail="A variance was explicitly accepted by the Controller",
                sample_rows=[control_total],
            )
        ],
    )

    batch_id = ImportRepository(db).commit_batch(batch, [tx])
    context = ExceptionsRepository(db).build_rule_context("FY26-P09")

    assert tx.import_batch_id == batch_id
    assert len(context.transactions) == 1
    stored_tx = context.transactions[0]
    assert stored_tx.import_batch_id == batch_id
    assert stored_tx.line_no == 7
    assert stored_tx.company_code == "IN02"
    assert stored_tx.vendor_code == "V-00931"
    assert stored_tx.invoice_no == "INV-88213"

    stored_batch = next(
        row for row in context.import_batches if row["batch_id"] == batch_id
    )
    assert stored_batch["status"] == "committed"
    assert Decimal(str(stored_batch["balance_tolerance"])) == Decimal("500.00")
    assert len(context.control_totals) == 1
    assert context.control_totals[0]["batch_id"] == batch_id

    # These rows now have enough committed provenance for the three import rules.
    imbalance = evaluate_catalog_exc_001(context)
    assert len(imbalance) == 1
    assert imbalance[0].amount_at_risk == Decimal("350.00")

    tie_out = evaluate_catalog_exc_003(context)
    assert len(tie_out) == 1
    assert tie_out[0].amount_at_risk == Decimal("-350.00")

    # EXC-002 requires two committed batches; one batch is correctly not enough.
    assert evaluate_catalog_exc_002(context) == []

    reimport = ParsedTransaction(
        source_row_ref="reexport.csv:4",
        voucher_no="VCH-REEXPORT",
        posting_date="2026-09-22",
        company_code="IN02",
        account_code="5200",
        cost_center_code="CC-110",
        project_code=None,
        vendor_code="V-00931",
        invoice_no="INV-88213",
        description="re-exported posting",
        debit=Decimal("1000.00"),
        credit=Decimal("650.00"),
        net_amount=Decimal("350.00"),
        currency_code="INR",
        line_no=1,
        period_code="FY26-P09",
    )
    reimport_batch = ImportBatchResult(
        batch_id=0,
        file_name="reexport.csv",
        file_checksum="b" * 64,
        source_type="actuals_d365",
        total_source_rows=1,
        loaded_count=1,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=Decimal("1000.00"),
        total_credit=Decimal("650.00"),
        net_imbalance=Decimal("350.00"),
        balance_tolerance=Decimal("500.00"),
    )
    ImportRepository(db).commit_batch(reimport_batch, [reimport])
    context = ExceptionsRepository(db).build_rule_context("FY26-P09")
    duplicates = evaluate_catalog_exc_002(context)

    assert len(duplicates) == 1
    assert duplicates[0].subject_key == "V-00931|INV-88213|2026-09-22|350.00"
    assert "invoice key" in duplicates[0].detail

    # Budget rows must retain their imported company code as well; otherwise an
    # IN02 budget would be misattributed to the seeded IN01 company and EXC-006
    # would falsely treat the entity as uncovered.
    budget_tx = ParsedTransaction(
        source_row_ref="budget.csv:2",
        voucher_no="BUD-1",
        posting_date="2026-09-01",
        company_code="IN02",
        account_code="5200",
        cost_center_code="CC-110",
        project_code=None,
        vendor_code=None,
        invoice_no=None,
        description="IN02 budget",
        debit=Decimal("50000.00"),
        credit=Decimal("0.00"),
        net_amount=Decimal("50000.00"),
        currency_code="INR",
        period_code="FY26-P09",
    )
    budget_batch = ImportBatchResult(
        batch_id=0,
        file_name="budget.csv",
        file_checksum="c" * 64,
        source_type="budget",
        total_source_rows=1,
        loaded_count=1,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=Decimal("50000.00"),
        total_credit=Decimal("0.00"),
        net_imbalance=Decimal("50000.00"),
    )
    ImportRepository(db).commit_batch(budget_batch, [budget_tx])
    context = ExceptionsRepository(db).build_rule_context("FY26-P09")

    assert context.annual_budgets[("IN02", "5200", "CC-110")] == Decimal("50000.00")
    assert evaluate_catalog_exc_006(context) == []
