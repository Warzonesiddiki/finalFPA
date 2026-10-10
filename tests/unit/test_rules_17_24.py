from decimal import Decimal

import pytest

from app.engine.rules.rules_01_08 import ApprovalThresholdRuleItem, RuleContext
from app.engine.rules.rules_17_24 import (
    _exc021_required_input,
    _fy_of,
    _open_periods,
    _period_num,
    evaluate_all_17_24,
    evaluate_exc_019,
    evaluate_exc_020,
    evaluate_exc_021,
    evaluate_exc_022,
    evaluate_exc_023,
    evaluate_exc_024,
)


def test_rules_17_24_basic():
    ctx = RuleContext(period_id="2025-P03", transactions=[], budgets={}, config={})
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
        config={},
    )
    open_p = _open_periods(ctx)
    assert "2025-P03" in open_p


@pytest.mark.tst_id("TST-RUL-19")
def test_evaluate_exc_019():
    ctx = RuleContext(
        period_id="FY26-P03",
        transactions=[
            {
                "company_code": "IN01",
                "account_code": "6000",
                "cost_center_code": "CC1",
                "posting_date": "2026-01-15",
                "net_amount": Decimal("600000"),
                "source_row_ref": "r1",
            }
        ],
        budgets={
            ("IN01", "6000", "CC1", "FY26-P01"): Decimal("100000"),
            ("IN01", "6000", "CC1", "FY26-P02"): Decimal("100000"),
            ("IN01", "6000", "CC1", "FY26-P03"): Decimal("100000"),
        },
        config={
            "EXC-019_ytd_tolerance_pct": "0.05",
            "EXC-019_annual_consumption_pct": "0.80",
            "absolute_floor": "500000.00",
        },
    )
    findings = evaluate_exc_019(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-019"


@pytest.mark.tst_id("TST-RUL-20")
def test_evaluate_exc_020():
    ctx = RuleContext(
        period_id="FY26-P02",
        transactions=[
            {
                "company_code": "IN01",
                "account_code": "6000",
                "cost_center_code": "CC1",
                "posting_date": "2026-01-15",
                "net_amount": Decimal("100000"),
                "source_row_ref": "r1",
            }
        ],
        budgets={
            ("IN01", "6000", "CC1", "FY26-P01"): Decimal("100000"),
            ("IN01", "7000", "CC1", "FY26-P01"): Decimal("100000"),
            ("IN01", "7000", "CC1", "FY26-P02"): Decimal("100000"),
            # 6000 has P01 budget, but missing P02 while open_periods is [P01, P02]
        },
        config={"EXC-020_min_coverage_gap_periods": "1", "EXC-020_include_no_actuals_pairs": False},
    )
    findings = evaluate_exc_020(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-020"
    assert findings[0].subject_key == "IN01|6000|P02"


@pytest.mark.tst_id("TST-RUL-20")
def test_evaluate_exc_020_span():
    # Catalog 06 EXC-020 sample case (Planting P20):
    # account 5450 has budget lines for FY26-P01..P06 but none for P07..P09,
    # while actuals exist for all three months. Expected span: P07-P09, coverage 66.67%.
    ctx = RuleContext(
        period_id="FY26-P09",
        transactions=[
            {
                "company_code": "IN01",
                "account_code": "5450",
                "cost_center_code": "CC1",
                "posting_date": "2026-07-15",
                "net_amount": Decimal("50000"),
                "source_row_ref": "r1",
            },
            {
                "company_code": "IN01",
                "account_code": "5450",
                "cost_center_code": "CC1",
                "posting_date": "2026-08-15",
                "net_amount": Decimal("50000"),
                "source_row_ref": "r2",
            },
            {
                "company_code": "IN01",
                "account_code": "5450",
                "cost_center_code": "CC1",
                "posting_date": "2026-09-15",
                "net_amount": Decimal("50000"),
                "source_row_ref": "r3",
            },
        ],
        budgets={
            **{("IN01", "5450", "CC1", f"FY26-P0{i}"): Decimal("55000") for i in range(1, 7)},
            **{("IN01", "6000", "CC1", f"FY26-P0{i}"): Decimal("100000") for i in range(1, 10)},
        },
        config={"EXC-020_min_coverage_gap_periods": "1", "EXC-020_include_no_actuals_pairs": False},
    )
    findings = evaluate_exc_020(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-020"
    assert findings[0].subject_key == "IN01|5450|P07-P09"
    assert findings[0].severity == "Medium"
    assert "coverage 66.67%" in findings[0].detail
    assert "missing FY26-P07, FY26-P08, FY26-P09" in findings[0].detail
    assert findings[0].amount_at_risk == Decimal("330000.00")


@pytest.mark.tst_id("TST-RUL-21")
def test_evaluate_exc_021():
    """Doc 06 EXC-021: thresholds resolve from MasterApprovalThreshold records.

    T-010: the old fixture passed `EXC-021_single_threshold` /
    `EXC-021_dual_threshold` config keys, but the rule (and docs/06 §EXC-021)
    resolves thresholds from versioned `MasterApprovalThreshold` master records
    on `context.master_approval_thresholds`, seeded with the two company-scope
    defaults (Rs 5,00,000 single, Rs 25,00,000 dual). With config keys alone
    the rule saw no records and raised nothing, so the test was red for a
    fixture reason, not a rule reason. These records mirror the documented
    seeding and the P21 planting shape (dual crossing supersedes single).
    """
    thresholds = [
        ApprovalThresholdRuleItem(
            threshold_id="THR-SINGLE-500K",
            scope="company",
            amount_threshold=Decimal("500000.00"),
            requires_dual_approval=False,
            effective_from="2025-04-01",
            company_code="IN01",
        ),
        ApprovalThresholdRuleItem(
            threshold_id="THR-DUAL-2500K",
            scope="company",
            amount_threshold=Decimal("2500000.00"),
            requires_dual_approval=True,
            effective_from="2025-04-01",
            company_code="IN01",
        ),
    ]
    ctx = RuleContext(
        period_id="FY26-P03",
        transactions=[
            # Crosses the single threshold only.
            {
                "company_code": "IN01",
                "account_code": "6000",
                "vendor_code": "VEND1",
                "voucher_no": "V100",
                "debit": Decimal("600000"),
                "posting_date": "2026-03-01",
                "source_row_ref": "r1",
            },
            # P21 shape: crosses the dual threshold; the dual finding must
            # supersede the single one, so exactly one finding for the voucher.
            {
                "company_code": "IN01",
                "account_code": "5450",
                "vendor_code": "VEND2",
                "voucher_no": "V101",
                "debit": Decimal("2750000"),
                "posting_date": "2026-03-01",
                "source_row_ref": "r2",
            },
            # Below every threshold: no finding.
            {
                "company_code": "IN01",
                "account_code": "6000",
                "vendor_code": "VEND3",
                "voucher_no": "V102",
                "debit": Decimal("499999"),
                "posting_date": "2026-03-01",
                "source_row_ref": "r3",
            },
        ],
        budgets={},
        master_approval_thresholds=thresholds,
        config={},
    )
    findings = evaluate_exc_021(ctx)
    assert [f.subject_key for f in findings] == [
        "IN01|V100|THR-SINGLE-500K",
        "IN01|V101|THR-DUAL-2500K",
    ]
    assert all(f.rule_id == "EXC-021" and f.severity == "High" for f in findings)
    assert "single approval required" in findings[0].detail
    assert "dual approval required" in findings[1].detail
    assert findings[1].amount_at_risk == Decimal("2750000.00")


@pytest.mark.tst_id("TST-RUL-21")
def test_evaluate_exc_021_is_disabled_without_approval_thresholds_per_doc_06():
    """Doc 06 EXC-021 'Depends on': without MasterApprovalThreshold records the
    rule is disabled with a notice - it raises nothing and the required-input
    gate names the missing dependency, so the batch records DISABLED rather
    than scoring a silent, unexplained zero.
    """
    ctx = RuleContext(
        period_id="FY26-P03",
        transactions=[
            {
                "company_code": "IN01",
                "account_code": "6000",
                "voucher_no": "V100",
                "debit": Decimal("600000"),
                "posting_date": "2026-03-01",
                "source_row_ref": "r1",
            },
        ],
        budgets={},
        config={},
    )
    assert evaluate_exc_021(ctx) == []
    assert _exc021_required_input(ctx) == "EXC-021_approval_thresholds"


@pytest.mark.tst_id("TST-RUL-22")
def test_evaluate_exc_022():
    """Doc 06 EXC-022: a round manual journal above the entity baseline raises.

    T-009: the three prior periods are load-bearing, not decoration. They are the
    only path into `_exc022_inputs`' history branch, which called
    `_transaction_period(tx, context)` - two arguments into a one-argument helper.
    Without them the fixture never reached the defect and the rule's zero
    coverage on planting P22 looked like a corpus gap instead of a TypeError.
    """
    ctx = RuleContext(
        period_id="FY26-P04",
        transactions=[
            # Baseline: three prior periods of round manual journals (mean 200,000).
            {
                "company_code": "IN01",
                "voucher_no": "H001",
                "period_code": "FY26-P01",
                "journal_category": "manual",
                "net_amount": Decimal("100000.00"),
                "source_row_ref": "h1",
            },
            {
                "company_code": "IN01",
                "voucher_no": "H002",
                "period_code": "FY26-P02",
                "journal_category": "manual",
                "net_amount": Decimal("200000.00"),
                "source_row_ref": "h2",
            },
            {
                "company_code": "IN01",
                "voucher_no": "H003",
                "period_code": "FY26-P03",
                "journal_category": "manual",
                "net_amount": Decimal("300000.00"),
                "source_row_ref": "h3",
            },
            # Current period: 1,000,000 is round, above the floor and 5x the baseline.
            {
                "company_code": "IN01",
                "voucher_no": "V200",
                "period_code": "FY26-P04",
                "journal_category": "manual",
                "net_amount": Decimal("1000000.00"),
                "source_row_ref": "r1",
            },
        ],
        budgets={},
        config={
            "EXC-022_round_unit": "10000.00",
            "EXC-022_round_floor": "500000.00",
            "EXC-022_history_periods": 3,
            "EXC-022_multiple": "1.5",
        },
    )
    findings = evaluate_exc_022(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-022"
    assert findings[0].subject_key == "IN01|V200"
    assert findings[0].severity == "Low"


@pytest.mark.tst_id("TST-RUL-22")
def test_evaluate_exc_022_is_disabled_without_history_per_doc_06_section_2_9():
    """History-dependent rules are disabled, never approximated, without N periods.

    Doc 06 section 2.9: a missing prior-period baseline disables EXC-013, EXC-016
    and EXC-022 with "Needs at least N loaded periods". `evaluate_exc_022` returns
    no findings and its `REQUIRED_INPUT_CHECK` names the dependency the batch
    records as `disabled`, so a first-period project can never get a fabricated
    baseline. This is why the raise case above must load three periods: an empty
    fixture is the disabled path, not a missed detection.
    """
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[
            {
                "company_code": "IN01",
                "voucher_no": "V200",
                "debit": Decimal("1000000.00"),
                "source_row_ref": "r1",
            }
        ],
        budgets={},
        config={"EXC-022_round_unit": "10000.00", "EXC-022_round_floor": "500000.00"},
    )
    assert evaluate_exc_022(ctx) == []
    assert evaluate_exc_022.REQUIRED_INPUT_CHECK(ctx) == "EXC-022_history"


@pytest.mark.tst_id("TST-RUL-23")
def test_evaluate_exc_023():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[
            {
                "company_code": "IN01",
                "voucher_no": "V300",
                "debit": Decimal("1000.00"),
                "credit": Decimal("0.00"),
                "source_row_ref": "r1",
            },
            {
                "company_code": "IN01",
                "voucher_no": "V300",
                "debit": Decimal("0.00"),
                "credit": Decimal("900.00"),
                "source_row_ref": "r2",
            },
        ],
        budgets={},
        config={"EXC-023_tolerance": "0.00", "EXC-023_min_lines": 2},
    )
    findings = evaluate_exc_023(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-023"


@pytest.mark.tst_id("TST-RUL-24")
def test_evaluate_exc_024():
    ctx = RuleContext(
        period_id="2025-P03",
        transactions=[
            {
                "company_code": "IN01",
                "account_code": "1999",
                "net_amount": Decimal("150000.00"),
                "source_row_ref": "r1",
            }
        ],
        budgets={},
        config={"EXC-024_residual_floor": "100000.00", "suspense_accounts": {"1999"}},
    )
    findings = evaluate_exc_024(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-024"
