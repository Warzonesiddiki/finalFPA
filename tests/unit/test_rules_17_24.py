import pytest
from decimal import Decimal
from app.engine.rules.rules_17_24 import (
    evaluate_exc_019,
    evaluate_exc_020,
    evaluate_exc_021,
    evaluate_exc_022,
    evaluate_exc_023,
    evaluate_exc_024,
    evaluate_all_17_24,
    _fy_of,
    _period_num,
    _open_periods,
)
from app.engine.rules.rules_01_08 import RuleContext

def test_rules_17_24_basic():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[],
        budgets={},
        config={}
    )
    assert evaluate_exc_019(ctx) == []
    assert evaluate_exc_020(ctx) == []
    assert evaluate_exc_021(ctx) == []
    assert evaluate_exc_022(ctx) == []
    assert evaluate_exc_023(ctx) == []
    assert evaluate_exc_024(ctx) == []
    assert evaluate_all_17_24(ctx) == []

def test_helpers_17_24():
    assert _fy_of("2025-P03") == "2025"
    assert _period_num("2025-P03") == 3
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[],
        budgets={
            ("IN01", "6000", "CC1", "2025-P01"): Decimal("100"),
            ("IN01", "6000", "CC1", "2025-P03"): Decimal("100"),
        },
        config={}
    )
    open_p = _open_periods(ctx)
    assert "2025-P03" in open_p

@pytest.mark.tst_id("TST-RUL-19")
def test_evaluate_exc_019():
    ctx = RuleContext(
        period_id="FY26-P03",
        transactions=[
            {"company_code": "IN01", "account_code": "6000", "cost_center_code": "CC1", "posting_date": "2026-01-15", "net_amount": Decimal("600000"), "source_row_ref": "r1"}
        ],
        budgets={
            ("IN01", "6000", "CC1", "FY26-P01"): Decimal("100000"),
            ("IN01", "6000", "CC1", "FY26-P02"): Decimal("100000"),
            ("IN01", "6000", "CC1", "FY26-P03"): Decimal("100000"),
        },
        config={"EXC-019_ytd_tolerance_pct": "0.05", "EXC-019_annual_consumption_pct": "0.80", "absolute_floor": "500000.00"}
    )
    findings = evaluate_exc_019(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-019"

@pytest.mark.tst_id("TST-RUL-20")
def test_evaluate_exc_020():
    ctx = RuleContext(
        period_id="FY26-P02",
        transactions=[
            {"company_code": "IN01", "account_code": "6000", "cost_center_code": "CC1", "posting_date": "2026-01-15", "net_amount": Decimal("100000"), "source_row_ref": "r1"}
        ],
        budgets={
            ("IN01", "6000", "CC1", "FY26-P01"): Decimal("100000"),
            ("IN01", "7000", "CC1", "FY26-P01"): Decimal("100000"),
            ("IN01", "7000", "CC1", "FY26-P02"): Decimal("100000"),
            # 6000 has P01 budget, but missing P02 while open_periods is [P01, P02]
        },
        config={"EXC-020_min_coverage_gap_periods": "1", "EXC-020_include_no_actuals_pairs": False}
    )
    findings = evaluate_exc_020(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-020"

@pytest.mark.tst_id("TST-RUL-21")
def test_evaluate_exc_021():
    # Test dual threshold with split vouchers
    ctx = RuleContext(
        period_id="FY26-P03",
        transactions=[
            {"company_code": "IN01", "account_code": "6000", "vendor_code": "VEND1", "voucher_no": "V100", "debit": Decimal("600000"), "posting_date": "2026-03-01", "source_row_ref": "r1"},
            {"company_code": "IN01", "account_code": "6000", "vendor_code": "VEND1", "voucher_no": "V101", "debit": Decimal("2000000"), "posting_date": "2026-03-01", "source_row_ref": "r2"},
        ],
        budgets={},
        config={"EXC-021_single_threshold": "500000.00", "EXC-021_dual_threshold": "2500000.00"}
    )
    findings = evaluate_exc_021(ctx)
    assert len(findings) >= 1
    assert any(f.rule_id == "EXC-021" for f in findings)

@pytest.mark.tst_id("TST-RUL-22")
def test_evaluate_exc_022():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[
            {"company_code": "IN01", "voucher_no": "V200", "debit": Decimal("1000000.00"), "source_row_ref": "r1"}
        ],
        budgets={},
        config={"EXC-022_round_unit": "10000.00", "EXC-022_round_floor": "500000.00"}
    )
    findings = evaluate_exc_022(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-022"

@pytest.mark.tst_id("TST-RUL-23")
def test_evaluate_exc_023():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[
            {"company_code": "IN01", "voucher_no": "V300", "debit": Decimal("1000.00"), "credit": Decimal("0.00"), "source_row_ref": "r1"},
            {"company_code": "IN01", "voucher_no": "V300", "debit": Decimal("0.00"), "credit": Decimal("900.00"), "source_row_ref": "r2"}
        ],
        budgets={},
        config={"EXC-023_tolerance": "0.00", "EXC-023_min_lines": 2}
    )
    findings = evaluate_exc_023(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-023"

@pytest.mark.tst_id("TST-RUL-24")
def test_evaluate_exc_024():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[
            {"company_code": "IN01", "account_code": "1999", "net_amount": Decimal("150000.00"), "source_row_ref": "r1"}
        ],
        budgets={},
        config={"EXC-024_residual_floor": "100000.00", "suspense_accounts": {"1999"}}
    )
    findings = evaluate_exc_024(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-024"
