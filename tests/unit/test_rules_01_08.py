"""Unit tests for Exception Rules 01 to 08 per 06_EXCEPTION_RULES_CATALOG.md."""

import hashlib
from decimal import Decimal

import pytest

from app.engine.imports.models import ParsedTransaction
from app.engine.rules.rules_01_08 import (
    RecurringCostRuleItem,
    RuleContext,
    evaluate,
    evaluate_all,
    evaluate_exc_001,
    evaluate_exc_002,
    evaluate_exc_003,
    evaluate_exc_004,
    evaluate_exc_005,
    evaluate_exc_006,
    evaluate_exc_007,
    evaluate_exc_008,
)


def make_tx(
    source_row_ref="row_1",
    voucher_no="VCH-001",
    posting_date="2026-09-15",
    company_code="IN01",
    account_code="5200",
    cost_center_code="CC-100",
    vendor_code=None,
    invoice_no=None,
    debit=Decimal("0.00"),
    credit=Decimal("0.00"),
    net_amount=Decimal("0.00"),
    currency_code="INR",
    period_code=None,
    raw_values=None,
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
        description="Test line",
        debit=debit,
        credit=credit,
        net_amount=net_amount,
        currency_code=currency_code,
        raw_values=raw_values or {},
    )


# ==============================================================================
# Rule 01: EXC-001 Duplicate Invoice Candidate
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-01")
@pytest.mark.tst("TST-RUL-01")
def test_exc_001_duplicate_invoice_raised():
    """Planting P7: Vendor V-00931 invoice INV-88213 posted twice within 90 days."""
    tx1 = make_tx(
        source_row_ref="row_101",
        voucher_no="VCH-2026-0912-004",
        posting_date="2026-09-14",
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
        net_amount=Decimal("45000.00"),
    )
    tx2 = make_tx(
        source_row_ref="row_102",
        voucher_no="VCH-2026-0918-011",
        posting_date="2026-09-18",
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
        net_amount=Decimal("45000.00"),
    )

    ctx = RuleContext(transactions=[tx1, tx2], period_id="FY26-P09")
    findings = evaluate_exc_001(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-001"
    assert f.catalog_rule_id == "EXC-007"
    assert f.severity == "High"
    assert f.subject_key == "V-00931|INV-88213"
    assert f.amount_at_risk == Decimal("45000.00")
    assert f.owner_role == "Accounts Payable"
    assert set(f.evidence_refs) == {"row_101", "row_102"}
    expected_hash = hashlib.sha256(b"EXC-001|V-00931|INV-88213").hexdigest()
    assert f.identity_hash == expected_hash


def test_exc_001_precision_control_distinct_invoice():
    """Planting P25: Legitimate second invoice with distinct number not raised."""
    tx1 = make_tx(
        source_row_ref="row_101",
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
        net_amount=Decimal("45000.00"),
    )
    tx2 = make_tx(
        source_row_ref="row_102",
        vendor_code="V-00931",
        invoice_no="INV-88214",
        debit=Decimal("45000.00"),
        net_amount=Decimal("45000.00"),
    )

    ctx = RuleContext(transactions=[tx1, tx2], period_id="FY26-P09")
    findings = evaluate_exc_001(ctx)
    assert len(findings) == 0


def test_exc_001_date_window_exceeded():
    """Candidate postings exceeding date_window_days (e.g. 120 days) not raised."""
    tx1 = make_tx(
        posting_date="2026-05-01",
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
    )
    tx2 = make_tx(
        posting_date="2026-09-18",
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
    )

    ctx = RuleContext(
        transactions=[tx1, tx2], period_id="FY26-P09", config={"EXC-001_date_window_days": 90}
    )
    findings = evaluate_exc_001(ctx)
    assert len(findings) == 0


# ==============================================================================
# Rule 02: EXC-002 Unmapped GL Account
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-02")
@pytest.mark.tst("TST-RUL-02")
def test_exc_002_unmapped_account_raised():
    """Planting P4: 6 rows post to unmapped placeholder account 5999-TEMP."""
    txs = [
        make_tx(
            source_row_ref=f"row_{i}",
            account_code="5999-TEMP",
            debit=Decimal("7050.00"),
            net_amount=Decimal("7050.00"),
        )
        for i in range(1, 7)
    ]

    ctx = RuleContext(
        transactions=txs,
        dim_accounts={"5999-TEMP": {"is_mapped": False, "is_placeholder": True}},
        period_id="FY26-P09",
    )
    findings = evaluate_exc_002(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-002"
    assert f.catalog_rule_id == "EXC-004"
    assert f.severity == "Medium"
    assert f.subject_key == "account|5999-TEMP"
    assert f.amount_at_risk == Decimal("42300.00")
    assert len(f.evidence_refs) == 6


@pytest.mark.tst_id("TST-RUL-02B")
def test_exc_002_unmapped_cost_center_raised():
    """Planting P4b: 2 rows post to placeholder cost centre CC-999."""
    txs = [
        make_tx(
            source_row_ref=f"row_{i}",
            cost_center_code="CC-999",
            debit=Decimal("14000.00"),
            net_amount=Decimal("14000.00"),
        )
        for i in range(1, 3)
    ]

    ctx = RuleContext(
        transactions=txs,
        dim_cost_centers={"CC-999": {"owner_name": "Unassigned", "is_active": True}},
        period_id="FY26-P09",
    )
    findings = evaluate_exc_002(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-002"
    assert f.catalog_rule_id == "EXC-004"
    assert f.severity == "Medium"
    assert f.subject_key == "cost_center|CC-999"
    assert f.amount_at_risk == Decimal("28000.00")
    assert len(f.evidence_refs) == 2


def test_exc_002_mapped_account_not_raised():
    """Properly mapped account in chart of accounts should not raise."""
    tx = make_tx(account_code="5100", debit=Decimal("50000.00"), net_amount=Decimal("50000.00"))
    ctx = RuleContext(
        transactions=[tx],
        dim_accounts={"5100": {"is_mapped": True, "is_placeholder": False}},
    )
    assert len(evaluate_exc_002(ctx)) == 0


# ==============================================================================
# Rule 03: EXC-003 Inactive Cost Centre Usage
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-03")
def test_exc_003_inactive_cost_centre_raised():
    """Planting P5: Inactive cost centre CC-950 receives postings totalling ₹96,500.00."""
    txs = [
        make_tx(
            source_row_ref=f"row_{i}",
            cost_center_code="CC-950",
            debit=Decimal("24125.00"),
            net_amount=Decimal("24125.00"),
        )
        for i in range(1, 5)
    ]

    ctx = RuleContext(
        transactions=txs,
        dim_cost_centers={"CC-950": {"is_active": False}},
        period_id="FY26-P09",
    )
    findings = evaluate_exc_003(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-003"
    assert f.catalog_rule_id == "EXC-005"
    assert f.severity == "Low"
    assert f.subject_key == "cost_center|CC-950"
    assert f.amount_at_risk == Decimal("96500.00")
    assert f.owner_role == "Cost Centre Owner"


def test_exc_003_active_cost_centre_not_raised():
    """Active cost centre should not be flagged."""
    tx = make_tx(
        cost_center_code="CC-100", debit=Decimal("25000.00"), net_amount=Decimal("25000.00")
    )
    ctx = RuleContext(
        transactions=[tx],
        dim_cost_centers={"CC-100": {"is_active": True}},
        period_id="FY26-P09",
    )
    assert len(evaluate_exc_003(ctx)) == 0


# ==============================================================================
# Rule 04: EXC-004 Posting-date vs Period Mismatch
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-04")
def test_exc_004_period_mismatch_raised():
    """Planting P9: October-dated row declares source period FY26-P09."""
    tx = make_tx(
        source_row_ref="row_00882",
        posting_date="2026-10-15",  # October -> FY26-P10
        debit=Decimal("92000.00"),
        net_amount=Decimal("92000.00"),
        raw_values={"batch_id": "batch_040", "period": "FY26-P09"},
    )

    ctx = RuleContext(transactions=[tx], period_id="FY26-P09")
    findings = evaluate_exc_004(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-004"
    assert f.catalog_rule_id == "EXC-009"
    assert f.severity == "High"
    assert f.amount_at_risk == Decimal("92000.00")
    assert f.owner_role == "GL Accountant"


def test_exc_004_matching_period_not_raised():
    """Posting date in September 2026 matching FY26-P09 should not be flagged."""
    tx = make_tx(
        posting_date="2026-09-20",  # September -> FY26-P09
        debit=Decimal("50000.00"),
        raw_values={"period": "FY26-P09"},
    )
    ctx = RuleContext(transactions=[tx], period_id="FY26-P09")
    assert len(evaluate_exc_004(ctx)) == 0


# ==============================================================================
# Rule 05: EXC-005 Unusual Negative Expense / Credit
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-05")
def test_exc_005_unusual_credit_raised():
    """Planting P12: Account 5400/CC-110 receives credits ₹680,000 with offset only ₹120,000 (17.6%)."""
    tx_credit = make_tx(
        source_row_ref="row_c1",
        account_code="5400",
        cost_center_code="CC-110",
        credit=Decimal("680000.00"),
        net_amount=Decimal("-680000.00"),
    )
    tx_debit = make_tx(
        source_row_ref="row_d1",
        account_code="5400",
        cost_center_code="CC-110",
        debit=Decimal("120000.00"),
        net_amount=Decimal("120000.00"),
    )

    ctx = RuleContext(
        transactions=[tx_credit, tx_debit],
        dim_accounts={"5400": {"account_type": "EXPENSE"}},
        period_id="FY26-P09",
        config={
            "EXC-005_min_credit_amount": Decimal("500000.00"),
            "EXC-005_offset_ratio": Decimal("0.90"),
        },
    )
    findings = evaluate_exc_005(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-005"
    assert f.catalog_rule_id == "EXC-012"
    assert f.severity == "Medium"
    assert f.subject_key == "IN01|5400|CC-110"
    assert f.amount_at_risk == Decimal("680000.00")


def test_exc_005_precision_control_offset_above_threshold():
    """Planting P27: Accrual and same-period reversal exceeding offset ratio (100% offset) not raised."""
    tx_credit = make_tx(
        account_code="5400",
        cost_center_code="CC-115",
        credit=Decimal("500000.00"),
        net_amount=Decimal("-500000.00"),
    )
    tx_debit = make_tx(
        account_code="5400",
        cost_center_code="CC-115",
        debit=Decimal("500000.00"),
        net_amount=Decimal("500000.00"),
    )

    ctx = RuleContext(
        transactions=[tx_credit, tx_debit],
        dim_accounts={"5400": {"account_type": "EXPENSE"}},
        period_id="FY26-P09",
        config={
            "EXC-005_min_credit_amount": Decimal("500000.00"),
            "EXC-005_offset_ratio": Decimal("0.90"),
        },
    )
    assert len(evaluate_exc_005(ctx)) == 0


def test_exc_005_ignores_different_period_debits():
    """Debits in different periods cannot offset current period credits."""
    tx_credit = make_tx(
        account_code="5400",
        cost_center_code="CC-110",
        credit=Decimal("680000.00"),
        net_amount=Decimal("-680000.00"),
        posting_date="2026-09-25",
    )
    tx_debit_prior = make_tx(
        account_code="5400",
        cost_center_code="CC-110",
        debit=Decimal("10000000.00"),
        net_amount=Decimal("10000000.00"),
        posting_date="2026-08-15",
    )

    ctx = RuleContext(
        transactions=[tx_credit, tx_debit_prior],
        dim_accounts={"5400": {"account_type": "EXPENSE"}},
        period_id="FY26-P09",
        config={
            "EXC-005_min_credit_amount": Decimal("500000.00"),
            "EXC-005_offset_ratio": Decimal("0.90"),
        },
    )
    findings = evaluate_exc_005(ctx)
    assert len(findings) == 1
    assert findings[0].subject_key == "IN01|5400|CC-110"


# ==============================================================================
# Rule 06: EXC-006 Missing Recurring Cost
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-06")
def test_exc_006_missing_recurring_cost_raised():
    """Planting P15: Recurring office rent ₹450,000 missing in P09."""
    recurring_item = RecurringCostRuleItem(
        recurring_id="REC-001",
        name="Office Rent Andheri",
        vendor_code="V-00118",
        expected_amount=Decimal("450000.00"),
        tolerance_pct=Decimal("0.10"),
    )

    # Some unrelated transaction in the period
    tx_other = make_tx(
        vendor_code="V-99999", debit=Decimal("20000.00"), net_amount=Decimal("20000.00")
    )

    ctx = RuleContext(
        transactions=[tx_other],
        master_recurring_costs=[recurring_item],
        period_id="FY26-P09",
    )
    findings = evaluate_exc_006(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-006"
    assert f.catalog_rule_id == "EXC-015"
    assert f.severity == "High"
    assert f.subject_key == "V-00118|Office_Rent_Andheri"
    assert f.amount_at_risk == Decimal("450000.00")


def test_exc_006_precision_control_within_tolerance():
    """Planting P32: Recurring charge posted within 10% tolerance (8% below) not raised."""
    recurring_item = RecurringCostRuleItem(
        recurring_id="REC-002",
        name="Security Services",
        vendor_code="V-00118",
        expected_amount=Decimal("100000.00"),
        tolerance_pct=Decimal("0.10"),  # 10%
    )
    # Actual posting of 92,000 is 8% below expected (within 10% tolerance)
    tx = make_tx(vendor_code="V-00118", debit=Decimal("92000.00"), net_amount=Decimal("92000.00"))

    ctx = RuleContext(
        transactions=[tx],
        master_recurring_costs=[recurring_item],
        period_id="FY26-P09",
    )
    assert len(evaluate_exc_006(ctx)) == 0


# ==============================================================================
# Rule 07: EXC-007 Material Unbudgeted Spend (Catalog EXC-017)
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-07")
@pytest.mark.tst_id("TST-RUL-17")
def test_exc_007_unbudgeted_spend_raised():
    """Planting P17: Cost centre CC-160 has ₹840,000 spend with zero FY26 budget line."""
    tx = make_tx(
        company_code="IN01",
        account_code="5450",
        cost_center_code="CC-160",
        debit=Decimal("840000.00"),
        net_amount=Decimal("840000.00"),
    )

    ctx = RuleContext(
        transactions=[tx],
        annual_budgets={("IN01", "5450", "CC-160"): Decimal("0.00")},
        period_id="FY26-P09",
        config={"EXC-007_materiality_amount": Decimal("500000.00")},
    )
    findings = evaluate_exc_007(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-007"
    assert f.catalog_rule_id == "EXC-017"
    assert f.severity == "High"
    assert f.subject_key == "IN01|5450|CC-160"
    assert f.amount_at_risk == Decimal("840000.00")


def test_exc_007_spend_with_budget_not_raised():
    """Spend on account with budget line should not be raised by EXC-007."""
    tx = make_tx(
        company_code="IN01",
        account_code="5450",
        cost_center_code="CC-160",
        debit=Decimal("840000.00"),
        net_amount=Decimal("840000.00"),
    )

    ctx = RuleContext(
        transactions=[tx],
        annual_budgets={("IN01", "5450", "CC-160"): Decimal("1000000.00")},
        period_id="FY26-P09",
    )
    assert len(evaluate_exc_007(ctx)) == 0


# ==============================================================================
# Rule 08: EXC-008 Material Variance Over Threshold (Catalog EXC-018)
# ==============================================================================


@pytest.mark.tst_id("TST-RUL-08")
@pytest.mark.tst_id("TST-RUL-18")
def test_exc_008_material_variance_canonical_f13a():
    """Planting P18: Account 5200/CC-100 actual 10,540,000 vs budget 10,000,000 (+5.4%, +₹540,000)."""
    tx = make_tx(
        company_code="IN01",
        account_code="5200",
        cost_center_code="CC-100",
        debit=Decimal("10540000.00"),
        net_amount=Decimal("10540000.00"),
    )

    ctx = RuleContext(
        transactions=[tx],
        budgets={("IN01", "5200", "CC-100", "FY26-P09"): Decimal("10000000.00")},
        period_id="FY26-P09",
        config={
            "EXC-008_materiality_pct": Decimal("0.02"),
            "EXC-008_absolute_floor": Decimal("500000.00"),
            "EXC-008_pct_threshold": Decimal("5.0"),
        },
    )
    findings = evaluate_exc_008(ctx)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "EXC-008"
    assert f.catalog_rule_id == "EXC-018"
    assert f.severity == "High"
    assert f.subject_key == "IN01|5200|CC-100"
    assert f.amount_at_risk == Decimal("540000.00")


def test_exc_008_precision_control_p29_fails_amount_floor():
    """Planting P29 (F13b): +6.0% variance but below ₹500,000 absolute floor (AND-test fails)."""
    tx = make_tx(
        company_code="IN01",
        account_code="5200",
        cost_center_code="CC-105",
        debit=Decimal("1060000.00"),
        net_amount=Decimal("1060000.00"),
    )

    ctx = RuleContext(
        transactions=[tx],
        budgets={
            ("IN01", "5200", "CC-105", "FY26-P09"): Decimal("1000000.00")
        },  # var = +60,000 (+6.0%)
        period_id="FY26-P09",
        config={
            "EXC-008_materiality_pct": Decimal("0.02"),
            "EXC-008_absolute_floor": Decimal("500000.00"),
            "EXC-008_pct_threshold": Decimal("5.0"),
        },
    )
    assert len(evaluate_exc_008(ctx)) == 0


def test_exc_008_precision_control_p30_fails_pct_threshold():
    """Planting P30 (F13c): ₹900,000 variance but +2.25% is below 5.0% threshold (AND-test fails)."""
    tx = make_tx(
        company_code="IN01",
        account_code="5200",
        cost_center_code="CC-110",
        debit=Decimal("40900000.00"),
        net_amount=Decimal("40900000.00"),
    )

    ctx = RuleContext(
        transactions=[tx],
        budgets={
            ("IN01", "5200", "CC-110", "FY26-P09"): Decimal("40000000.00")
        },  # var = +900,000 (+2.25%)
        period_id="FY26-P09",
        config={
            "EXC-008_materiality_pct": Decimal("0.02"),
            "EXC-008_absolute_floor": Decimal("500000.00"),
            "EXC-008_pct_threshold": Decimal("5.0"),
        },
    )
    assert len(evaluate_exc_008(ctx)) == 0


# ==============================================================================
# Engine Determinism & Aggregate Evaluator Tests
# ==============================================================================


def test_evaluate_all_determinism():
    """Running evaluate() twice with same context must produce identical findings."""
    tx1 = make_tx(
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
        net_amount=Decimal("45000.00"),
        posting_date="2026-09-14",
    )
    tx2 = make_tx(
        vendor_code="V-00931",
        invoice_no="INV-88213",
        debit=Decimal("45000.00"),
        net_amount=Decimal("45000.00"),
        posting_date="2026-09-18",
    )

    ctx = RuleContext(transactions=[tx1, tx2], period_id="FY26-P09")
    run1 = evaluate(ctx)
    run2 = evaluate_all(ctx)

    assert len(run1) == len(run2)
    for f1, f2 in zip(run1, run2):
        assert f1.identity_hash == f2.identity_hash
        assert f1.rule_id == f2.rule_id
        assert f1.amount_at_risk == f2.amount_at_risk
