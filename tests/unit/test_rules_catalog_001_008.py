"""Unit coverage for the catalog-native EXC-001/002/003/006/008 evaluators."""

from decimal import Decimal

import pytest

from app.engine.imports.models import ParsedTransaction
from app.engine.imports.parser import parse_csv_transactions
from app.engine.imports.profiles import BUILTIN_PROFILES
from app.engine.rules.batch import evaluate_all_rules_detailed
from app.engine.rules.rules_01_08 import RuleContext
from app.engine.rules.rules_catalog_001_008 import (
    evaluate_catalog_exc_001,
    evaluate_catalog_exc_002,
    evaluate_catalog_exc_003,
    evaluate_catalog_exc_006,
    evaluate_catalog_exc_008,
)


def make_tx(
    *,
    source_row_ref="row-1",
    voucher_no="VCH-1",
    line_no=1,
    posting_date="2026-09-22",
    period_code="FY26-P09",
    company_code="IN01",
    account_code="5300",
    cost_center_code="CC-110",
    vendor_code=None,
    invoice_no=None,
    debit=Decimal("0.00"),
    credit=Decimal("0.00"),
    import_batch_id=None,
):
    return ParsedTransaction(
        source_row_ref=source_row_ref,
        voucher_no=voucher_no,
        posting_date=posting_date,
        company_code=company_code,
        account_code=account_code,
        cost_center_code=cost_center_code,
        project_code=None,
        vendor_code=vendor_code,
        invoice_no=invoice_no,
        description="fixture",
        debit=debit,
        credit=credit,
        net_amount=debit - credit,
        currency_code="INR",
        line_no=line_no,
        period_code=period_code,
        import_batch_id=import_batch_id,
    )


def batch(batch_id, *, status="committed", **overrides):
    row = {
        "batch_id": batch_id,
        "file_name": "bank_ledger_actuals.csv",
        "source_type": "actuals_procurement",
        "status": status,
        "is_balanced": True,
        "total_debit": Decimal("18450200.00"),
        "total_credit": Decimal("18449850.00"),
        "net_imbalance": Decimal("350.00"),
        "balance_tolerance": Decimal("500.00"),
        "created_at": f"2026-10-{int(batch_id):02d}T10:00:00",
    }
    row.update(overrides)
    return row


def test_parser_assigns_voucher_line_numbers_and_retains_balance_tolerance(tmp_path):
    csv_path = tmp_path / "ledger.csv"
    csv_path.write_text(
        "Voucher,Posting date,Company code,Main account,Cost center,"
        "Debit,Credit,Currency\n"
        "VCH-1,2026-09-22,IN01,5300,CC-110,100,0,INR\n"
        "VCH-1,2026-09-22,IN01,5300,CC-110,150,0,INR\n"
        "VCH-2,2026-09-22,IN01,5300,CC-110,100,0,INR\n",
        encoding="utf-8",
    )

    result, rows = parse_csv_transactions(
        csv_path,
        profile=BUILTIN_PROFILES[0],
        balance_tolerance=Decimal("500.00"),
    )

    assert [row.line_no for row in rows] == [1, 2, 1]
    assert result.balance_tolerance == Decimal("500.00")
    assert result.is_balanced is True


def test_parser_keeps_source_line_sequence_across_quarantined_rows(tmp_path):
    csv_path = tmp_path / "quarantined-line.csv"
    csv_path.write_text(
        "Voucher,Posting date,Company code,Main account,Cost center,"
        "Debit,Credit,Currency\n"
        "VCH-1,not-a-date,IN01,5300,CC-110,100,0,INR\n"
        "VCH-1,2026-09-22,IN01,5300,CC-110,100,0,INR\n",
        encoding="utf-8",
    )

    _result, rows = parse_csv_transactions(csv_path, profile=BUILTIN_PROFILES[0])

    assert len(rows) == 1
    assert rows[0].line_no == 2


@pytest.mark.tst_id("TST-RUL-01")
def test_exc_001_prefers_the_batch_persisted_tolerance_over_current_config():
    ctx = RuleContext(
        import_batches=[batch(41, subject_key="batch_041|bank_ledger")],
        config={"EXC-001_balance_tolerance": Decimal("0.00")},
    )

    findings = evaluate_catalog_exc_001(ctx)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "EXC-001"
    assert finding.catalog_rule_id == "EXC-001"
    assert finding.subject_key == "batch_041|bank_ledger"
    assert finding.severity == "High"
    assert finding.owner_role == "GL Accountant"
    assert finding.amount_at_risk == Decimal("350.00")
    assert finding.effective_threshold == "balance_tolerance ₹500.00"
    assert "import tolerance was ₹500.00" in finding.detail


def test_exc_001_falls_back_to_config_for_legacy_batches_without_tolerance():
    legacy_batch = batch(42)
    legacy_batch.pop("balance_tolerance")
    ctx = RuleContext(
        import_batches=[legacy_batch],
        config={"EXC-001_balance_tolerance": Decimal("100.00")},
    )

    findings = evaluate_catalog_exc_001(ctx)

    assert len(findings) == 1
    assert findings[0].effective_threshold == "balance_tolerance ₹100.00"


def test_exc_001_ignores_rejected_voided_and_balanced_batches():
    rejected = batch(1, status="rejected")
    voided = batch(2, status="voided")
    balanced = batch(3, total_credit=Decimal("18450200.00"), net_imbalance=Decimal("0.00"))
    ctx = RuleContext(import_batches=[rejected, voided, balanced])

    assert evaluate_catalog_exc_001(ctx) == []


@pytest.mark.tst_id("TST-RUL-02")
def test_exc_002_detects_primary_voucher_line_overlap_across_committed_batches():
    old = make_tx(
        source_row_ref="old.csv:12",
        voucher_no="VCH-2026-0915-001",
        line_no=1,
        debit=Decimal("45000.00"),
        import_batch_id=37,
    )
    reexport = make_tx(
        source_row_ref="new.csv:8",
        voucher_no="VCH-2026-0915-001",
        line_no=1,
        debit=Decimal("45000.00"),
        import_batch_id=41,
    )
    ctx = RuleContext(
        transactions=[old, reexport],
        import_batches=[
            batch(37, file_name="batch_037.csv", created_at="2026-10-03T10:00:00"),
            batch(41, file_name="batch_041.csv", created_at="2026-10-04T10:00:00"),
        ],
    )

    findings = evaluate_catalog_exc_002(ctx)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "EXC-002"
    assert finding.catalog_rule_id == "EXC-002"
    assert finding.subject_key == "IN01|VCH-2026-0915-001|1"
    assert finding.amount_at_risk == Decimal("45000.00")
    assert "earlier committed batch 37" in finding.detail
    assert set(finding.evidence_refs) == {"old.csv:12", "new.csv:8"}


def test_exc_002_secondary_invoice_key_detects_a_different_voucher():
    old = make_tx(
        source_row_ref="old.csv:1",
        voucher_no="VCH-OLD",
        posting_date="2026-09-15",
        vendor_code="V-00931",
        invoice_no="INV-44",
        debit=Decimal("9000.00"),
        import_batch_id=37,
    )
    new = make_tx(
        source_row_ref="new.csv:1",
        voucher_no="VCH-NEW",
        posting_date="2026-09-15",
        vendor_code="V-00931",
        invoice_no="INV-44",
        debit=Decimal("9000.00"),
        import_batch_id=41,
    )
    ctx = RuleContext(
        transactions=[old, new],
        import_batches=[
            batch(37, created_at="2026-10-03T10:00:00"),
            batch(41, created_at="2026-10-04T10:00:00"),
        ],
    )

    findings = evaluate_catalog_exc_002(ctx)

    assert len(findings) == 1
    assert findings[0].subject_key == "V-00931|INV-44|2026-09-15|9000.00"
    assert "invoice key" in findings[0].detail


def test_exc_002_is_disabled_with_a_notice_when_fewer_than_two_batches_exist():
    result = evaluate_all_rules_detailed(
        RuleContext(import_batches=[batch(1)]),
        batch=(evaluate_catalog_exc_002,),
    )

    assert result.executions[0].status == "disabled"
    assert result.executions[0].notice == "Requires at least two committed batches"


def test_exc_002_does_not_flag_rows_repeated_only_within_one_batch():
    rows = [
        make_tx(
            source_row_ref=f"same:{line}",
            line_no=line,
            debit=Decimal("100.00"),
            import_batch_id=37,
        )
        for line in (1, 2)
    ]
    ctx = RuleContext(transactions=rows, import_batches=[batch(37)])

    assert evaluate_catalog_exc_002(ctx) == []


def test_exc_003_measures_loaded_minus_supplied_and_keeps_variance_sign():
    ctx = RuleContext(
        control_totals=[
            {
                "batch_id": 39,
                "scope": "gl_control_total",
                "supplied_total": Decimal("18400000.00"),
                "loaded_total": Decimal("18399650.00"),
                "tolerance": Decimal("0.00"),
            }
        ],
        import_batches=[batch(39)],
    )

    findings = evaluate_catalog_exc_003(ctx)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "EXC-003"
    assert finding.catalog_rule_id == "EXC-003"
    assert finding.subject_key == "39|gl_control_total"
    assert finding.amount_at_risk == Decimal("-350.00")
    assert finding.owner_role == "Controller"


def test_exc_003_ignores_control_totals_from_rejected_batch():
    ctx = RuleContext(
        control_totals=[
            {
                "batch_id": 39,
                "scope": "gl_control_total",
                "supplied_total": Decimal("1000.00"),
                "loaded_total": Decimal("650.00"),
                "tolerance": Decimal("0.00"),
            }
        ],
        import_batches=[batch(39, status="rejected")],
    )

    assert evaluate_catalog_exc_003(ctx) == []


def test_exc_003_does_not_raise_within_control_tolerance():
    ctx = RuleContext(
        control_totals=[
            {
                "batch_id": 39,
                "scope": "gl_control_total",
                "supplied_total": Decimal("18400000.00"),
                "loaded_total": Decimal("18399650.00"),
                "tolerance": Decimal("500.00"),
            }
        ]
    )

    assert evaluate_catalog_exc_003(ctx) == []


def test_exc_003_is_disabled_with_explicit_notice_without_control_totals():
    result = evaluate_all_rules_detailed(RuleContext(), batch=(evaluate_catalog_exc_003,))

    assert result.executions[0].status == "disabled"
    assert result.executions[0].notice == "No control-totals block supplied"


@pytest.mark.tst_id("TST-RUL-06")
def test_exc_006_raises_for_material_actuals_without_any_annual_entity_budget():
    tx = make_tx(
        source_row_ref="orphan.csv:8",
        company_code="IN02",
        account_code="5200",
        debit=Decimal("450000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        annual_budgets={("IN01", "5200", "CC-100"): Decimal("1.00")},
        period_id="FY26-P09",
        config={
            "EXC-006_scope_grain": "entity",
            "EXC-006_absolute_floor": Decimal("0.00"),
            "EXC-006_materiality_pct": Decimal("0.00"),
        },
    )

    findings = evaluate_catalog_exc_006(ctx)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "EXC-006"
    assert finding.catalog_rule_id == "EXC-006"
    assert finding.subject_key == "entity|IN02"
    assert finding.amount_at_risk == Decimal("450000.00")
    assert finding.severity == "Medium"


def test_exc_006_uses_entity_account_scope_by_default():
    tx = make_tx(company_code="IN02", account_code="5200", debit=Decimal("600000.00"))
    ctx = RuleContext(
        transactions=[tx],
        annual_budgets={("IN01", "5200", "CC-100"): Decimal("1.00")},
        period_id="FY26-P09",
        config={"EXC-006_absolute_floor": Decimal("0.00")},
    )

    findings = evaluate_catalog_exc_006(ctx)

    assert len(findings) == 1
    assert findings[0].subject_key == "entity_account|IN02|5200"
    assert "scope_grain entity_account" in findings[0].effective_threshold


def test_exc_006_treats_a_zero_value_budget_line_as_coverage():
    tx = make_tx(company_code="IN02", account_code="5200", debit=Decimal("450000.00"))
    ctx = RuleContext(
        transactions=[tx],
        annual_budgets={("IN02", "5200", "CC-110"): Decimal("0.00")},
        period_id="FY26-P09",
        config={"EXC-006_absolute_floor": Decimal("0.00")},
    )

    assert evaluate_catalog_exc_006(ctx) == []


def test_exc_006_excludes_actuals_after_the_period_under_review():
    tx = make_tx(
        company_code="IN02",
        account_code="5200",
        period_code="FY26-P10",
        posting_date="2026-10-02",
        debit=Decimal("900000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        annual_budgets={("IN01", "5200", "CC-110"): Decimal("1.00")},
        period_id="FY26-P09",
        config={"EXC-006_absolute_floor": Decimal("0.00")},
    )

    assert evaluate_catalog_exc_006(ctx) == []


@pytest.mark.tst_id("TST-RUL-08")
def test_exc_008_raises_same_line_amount_on_different_vouchers_when_material():
    txs = [
        make_tx(
            source_row_ref=f"p8-{index}",
            voucher_no=voucher,
            debit=Decimal("600000.00"),
        )
        for index, voucher in enumerate(("VCH-A", "VCH-B"), start=1)
    ]
    ctx = RuleContext(
        transactions=txs,
        annual_budgets={("IN01", "5300", "CC-110"): Decimal("1000000.00")},
        period_id="FY26-P09",
        config={
            "EXC-008_absolute_floor": Decimal("0.00"),
            "EXC-008_materiality_pct": Decimal("0.02"),
        },
    )

    findings = evaluate_catalog_exc_008(ctx)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "EXC-008"
    assert finding.catalog_rule_id == "EXC-008"
    assert finding.subject_key == "IN01|5300|600000.00|2026-09-22|CC-110"
    assert finding.amount_at_risk == Decimal("600000.00")
    assert set(finding.evidence_refs) == {"p8-1", "p8-2"}


def test_exc_008_does_not_flag_repeated_lines_inside_one_voucher():
    txs = [
        make_tx(
            source_row_ref=f"p26-{line}",
            voucher_no="VCH-SAME",
            line_no=line,
            debit=Decimal("600000.00"),
        )
        for line in (1, 2)
    ]
    ctx = RuleContext(
        transactions=txs,
        annual_budgets={("IN01", "5300", "CC-110"): Decimal("1000000.00")},
        config={"EXC-008_absolute_floor": Decimal("0.00")},
    )

    assert evaluate_catalog_exc_008(ctx) == []


def test_exc_008_only_checks_the_period_under_review():
    txs = [
        make_tx(
            source_row_ref="prior-1",
            voucher_no="VCH-A",
            period_code="FY26-P08",
            posting_date="2026-08-22",
            debit=Decimal("600000.00"),
        ),
        make_tx(
            source_row_ref="prior-2",
            voucher_no="VCH-B",
            period_code="FY26-P08",
            posting_date="2026-08-22",
            debit=Decimal("600000.00"),
        ),
    ]
    ctx = RuleContext(
        transactions=txs,
        annual_budgets={("IN01", "5300", "CC-110"): Decimal("1000000.00")},
        period_id="FY26-P09",
        config={"EXC-008_absolute_floor": Decimal("0.00")},
    )

    assert evaluate_catalog_exc_008(ctx) == []


def test_exc_008_does_not_group_identical_amounts_across_cost_centers():
    txs = [
        make_tx(
            source_row_ref="cc-a",
            voucher_no="VCH-A",
            cost_center_code="CC-110",
            debit=Decimal("600000.00"),
        ),
        make_tx(
            source_row_ref="cc-b",
            voucher_no="VCH-B",
            cost_center_code="CC-120",
            debit=Decimal("600000.00"),
        ),
    ]
    ctx = RuleContext(
        transactions=txs,
        annual_budgets={("IN01", "5300", "CC-110"): Decimal("1000000.00")},
        config={"EXC-008_absolute_floor": Decimal("0.00")},
    )

    assert evaluate_catalog_exc_008(ctx) == []


def test_exc_008_sums_monthly_budgets_when_annual_budget_is_absent():
    txs = [
        make_tx(
            source_row_ref=f"monthly-budget-{index}",
            voucher_no=voucher,
            debit=Decimal("1000.00"),
        )
        for index, voucher in enumerate(("VCH-A", "VCH-B"), start=1)
    ]
    ctx = RuleContext(
        transactions=txs,
        budgets={
            ("IN01", "5300", "CC-110", "FY26-P01"): Decimal("40000.00"),
            ("IN01", "5300", "CC-110", "FY26-P02"): Decimal("40000.00"),
        },
        period_id="FY26-P09",
        config={
            "EXC-008_absolute_floor": Decimal("0.00"),
            "EXC-008_materiality_pct": Decimal("0.02"),
        },
    )

    assert evaluate_catalog_exc_008(ctx) == []


def test_exc_008_default_absolute_floor_suppresses_small_exact_duplicates():
    txs = [make_tx(voucher_no=voucher, debit=Decimal("12500.00")) for voucher in ("VCH-A", "VCH-B")]
    ctx = RuleContext(
        transactions=txs,
        annual_budgets={("IN01", "5300", "CC-110"): Decimal("100000.00")},
    )

    assert evaluate_catalog_exc_008(ctx) == []
