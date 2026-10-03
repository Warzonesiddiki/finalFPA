"""Comprehensive Behavioral Test Suite for DEF-023: Rule-Integrity Audit.

Executes each rule under 2 conditions:
1. Planted Condition: minimal synthetic transaction/context designed to satisfy the rule's formula.
2. Absent Required Input: required master table/dimension/attribute missing (checking §2.9 compliance).
"""

from decimal import Decimal
import datetime
from typing import Dict, List, Any, Optional

from app.engine.rules.rules_01_08 import (
    RuleContext,
    Finding,
    RecurringCostRuleItem,
    evaluate_exc_001,
    evaluate_exc_002,
    evaluate_exc_003,
    evaluate_exc_004,
    evaluate_exc_005,
    evaluate_exc_006,
    evaluate_exc_007,
    evaluate_exc_008,
)
from app.engine.rules.rules_09_16 import (
    evaluate_exc_009,
    evaluate_exc_010,
    evaluate_exc_011,
    evaluate_exc_012,
    evaluate_exc_013,
    evaluate_exc_014,
    evaluate_exc_015,
    evaluate_exc_016,
)
from app.engine.rules.rules_17_24 import (
    evaluate_exc_019,
    evaluate_exc_020,
    evaluate_exc_021,
    evaluate_exc_022,
    evaluate_exc_023,
    evaluate_exc_024,
)

results = []

def run_test(rule_id, func, planted_ctx, absent_ctx, doc_expected_severity, doc_dep_name):
    # Test 1: Planted
    planted_fired = False
    planted_findings = []
    planted_err = None
    try:
        planted_findings = func(planted_ctx)
        if planted_findings and len(planted_findings) > 0:
            planted_fired = True
    except Exception as e:
        planted_err = str(e)

    # Test 2: Absent
    absent_fired = False
    absent_findings = []
    absent_err = None
    try:
        absent_findings = func(absent_ctx)
        if absent_findings and len(absent_findings) > 0:
            absent_fired = True
    except Exception as e:
        absent_err = str(e)

    # Validate severity & amount on planted findings
    sev_match = "N/A"
    amt_info = "N/A"
    if planted_findings:
        f = planted_findings[0]
        sev_match = f"Observed={f.severity} (Expected={doc_expected_severity})"
        amt_info = f"amount_at_risk={f.amount_at_risk}"

    results.append({
        "rule_id": rule_id,
        "func": func.__name__,
        "planted_fired": planted_fired,
        "planted_count": len(planted_findings),
        "planted_err": planted_err,
        "absent_fired": absent_fired,
        "absent_count": len(absent_findings),
        "absent_err": absent_err,
        "doc_dep": doc_dep_name,
        "sev_match": sev_match,
        "amt_info": amt_info,
        "sample_finding": planted_findings[0] if planted_findings else None
    })

# -----------------
# 1. Code EXC-001 (Catalog EXC-007 Duplicate Invoice)
# -----------------
ctx_001_planted = RuleContext(
    transactions=[
        {"vendor_code": "V-001", "invoice_no": "INV-100", "debit": Decimal("5000.00"), "posting_date": "2026-09-10", "voucher_no": "V1", "source_row_ref": "r1"},
        {"vendor_code": "V-001", "invoice_no": "INV-100", "debit": Decimal("5000.00"), "posting_date": "2026-09-15", "voucher_no": "V2", "source_row_ref": "r2"},
    ],
    config={"EXC-001_min_amount": "100.00", "EXC-001_date_window_days": 90}
)
ctx_001_absent = RuleContext(
    transactions=[
        # Absent vendor/invoice
        {"debit": Decimal("5000.00"), "posting_date": "2026-09-10", "voucher_no": "V1"},
        {"debit": Decimal("5000.00"), "posting_date": "2026-09-15", "voucher_no": "V2"},
    ],
    config={"EXC-001_min_amount": "100.00"}
)
run_test("EXC-001 (Code) / EXC-007 (Doc06)", evaluate_exc_001, ctx_001_planted, ctx_001_absent, "High", "vendor_code, invoice_no")

# -----------------
# 2. Code EXC-002 (Catalog EXC-004 Unmapped Account)
# -----------------
ctx_002_planted = RuleContext(
    transactions=[
        {"account_code": "9999", "net_amount": Decimal("1000.00"), "voucher_no": "V1"},
    ],
    valid_accounts={"1000", "2000", "4000"}
)
ctx_002_absent = RuleContext(
    transactions=[
        {"account_code": "9999", "net_amount": Decimal("1000.00"), "voucher_no": "V1"},
    ],
    valid_accounts=None # missing chart of accounts!
)
run_test("EXC-002 (Code) / EXC-004 (Doc06)", evaluate_exc_002, ctx_002_planted, ctx_002_absent, "Medium", "DimAccount (valid_accounts)")

# -----------------
# 3. Code EXC-003 (Catalog EXC-005 Inactive Cost Center)
# -----------------
ctx_003_planted = RuleContext(
    transactions=[
        {"cost_center_code": "CC-INACTIVE", "net_amount": Decimal("2500.00"), "period_id": "2026-09", "account_code": "5000"},
    ],
    inactive_cost_centers={"CC-INACTIVE"}
)
ctx_003_absent = RuleContext(
    transactions=[
        {"cost_center_code": "CC-INACTIVE", "net_amount": Decimal("2500.00"), "period_id": "2026-09", "account_code": "5000"},
    ],
    inactive_cost_centers=None # missing cost center active status
)
run_test("EXC-003 (Code) / EXC-005 (Doc06)", evaluate_exc_003, ctx_003_planted, ctx_003_absent, "Low", "DimCostCenter (inactive list)")

# -----------------
# 4. Code EXC-004 (Catalog EXC-008 Duplicate Voucher Line)
# -----------------
ctx_004_planted = RuleContext(
    transactions=[
        {"company_code": "US01", "account_code": "5100", "net_amount": Decimal("1200.00"), "posting_date": "2026-09-12", "cost_center_code": "CC-1", "voucher_no": "V1"},
        {"company_code": "US01", "account_code": "5100", "net_amount": Decimal("1200.00"), "posting_date": "2026-09-12", "cost_center_code": "CC-1", "voucher_no": "V2"},
    ],
    config={"EXC-004_min_amount": "100.00"}
)
ctx_004_absent = RuleContext(
    transactions=[],
    config={}
)
run_test("EXC-004 (Code) / EXC-008 (Doc06)", evaluate_exc_004, ctx_004_planted, ctx_004_absent, "Medium", "None")

# -----------------
# 5. Code EXC-005 (Catalog EXC-012 Unusual Credit)
# -----------------
ctx_005_planted = RuleContext(
    transactions=[
        {"account_code": "5100", "credit": Decimal("50000.00"), "net_amount": Decimal("-50000.00"), "voucher_no": "V1", "description": "Expense reversal"},
    ],
    expense_account_prefixes=["5", "6"],
    config={"EXC-005_threshold": "10000.00"}
)
ctx_005_absent = RuleContext(
    transactions=[
        {"account_code": "5100", "credit": Decimal("50000.00"), "net_amount": Decimal("-50000.00"), "voucher_no": "V1"},
    ],
    expense_account_prefixes=None
)
run_test("EXC-005 (Code) / EXC-012 (Doc06)", evaluate_exc_005, ctx_005_planted, ctx_005_absent, "Medium", "expense_account_prefixes")

# -----------------
# 6. Code EXC-006 (Catalog EXC-015 Missing Recurring Cost)
# -----------------
ctx_006_planted = RuleContext(
    transactions=[], # Missing expected recurring cost!
    recurring_costs=[
        RecurringCostRuleItem(
            vendor_code="V-RENT",
            account_code="5200",
            expected_amount=Decimal("100000.00"),
            tolerance_pct=Decimal("0.05"),
            description="Office Rent"
        )
    ],
    period_id="2026-09"
)
ctx_006_absent = RuleContext(
    transactions=[],
    recurring_costs=[], # Missing master recurring costs list!
    period_id="2026-09"
)
run_test("EXC-006 (Code) / EXC-015 (Doc06)", evaluate_exc_006, ctx_006_planted, ctx_006_absent, "High", "Recurring cost master list")

# -----------------
# 7. Code EXC-007 (Catalog EXC-017 Material Unbudgeted Spend)
# -----------------
ctx_007_planted = RuleContext(
    transactions=[
        {"account_code": "5900", "debit": Decimal("150000.00"), "net_amount": Decimal("150000.00"), "period_id": "2026-09", "voucher_no": "V1"},
    ],
    budget_by_account={"5100": Decimal("500000.00")}, # 5900 has 0 budget!
    config={"EXC-007_threshold": "50000.00"}
)
ctx_007_absent = RuleContext(
    transactions=[
        {"account_code": "5900", "debit": Decimal("150000.00"), "net_amount": Decimal("150000.00"), "period_id": "2026-09"},
    ],
    budget_by_account=None # Missing budget table!
)
run_test("EXC-007 (Code) / EXC-017 (Doc06)", evaluate_exc_007, ctx_007_planted, ctx_007_absent, "High", "Budget (budget_by_account)")

# -----------------
# 8. Code EXC-008 (Catalog EXC-018 Material Variance)
# -----------------
ctx_008_planted = RuleContext(
    transactions=[
        {"account_code": "5100", "debit": Decimal("200000.00"), "net_amount": Decimal("200000.00"), "period_id": "2026-09", "voucher_no": "V1"},
    ],
    budget_by_account={"5100": Decimal("100000.00")}, # Actual 200k vs Budget 100k (100% variance)
    config={"EXC-008_amount_threshold": "50000.00", "EXC-008_pct_threshold": "0.20"}
)
ctx_008_absent = RuleContext(
    transactions=[
        {"account_code": "5100", "debit": Decimal("200000.00"), "net_amount": Decimal("200000.00"), "period_id": "2026-09"},
    ],
    budget_by_account=None # Missing budget table!
)
run_test("EXC-008 (Code) / EXC-018 (Doc06)", evaluate_exc_008, ctx_008_planted, ctx_008_absent, "High", "Budget (budget_by_account)")

# -----------------
# 9. Code EXC-009 (Catalog EXC-009 Period Mismatch)
# -----------------
ctx_009_planted = RuleContext(
    transactions=[
        {"posting_date": "2026-10-05", "period_id": "2026-09", "net_amount": Decimal("15000.00"), "voucher_no": "V1"},
    ]
)
ctx_009_absent = RuleContext(
    transactions=[
        {"posting_date": "2026-10-05", "net_amount": Decimal("15000.00"), "voucher_no": "V1"}, # missing period_id
    ]
)
run_test("EXC-009 (Code) / EXC-009 (Doc06)", evaluate_exc_009, ctx_009_planted, ctx_009_absent, "High", "source period column")

# -----------------
# 10. Code EXC-010 (Catalog EXC-010 Cutoff Issue)
# -----------------
ctx_010_planted = RuleContext(
    transactions=[
        {"document_date": "2026-08-28", "posting_date": "2026-09-03", "period_id": "2026-09", "net_amount": Decimal("85000.00"), "account_code": "5100", "voucher_no": "V1"},
    ],
    config={"EXC-010_min_amount": "5000.00", "EXC-010_cutoff_window_days": 7}
)
ctx_010_absent = RuleContext(
    transactions=[
        {"posting_date": "2026-09-03", "period_id": "2026-09", "net_amount": Decimal("85000.00"), "voucher_no": "V1"}, # missing document_date
    ]
)
run_test("EXC-010 (Code) / EXC-010 (Doc06)", evaluate_exc_010, ctx_010_planted, ctx_010_absent, "High", "document_date")

# -----------------
# 11. Code EXC-011 (Catalog EXC-011 Future Dated)
# -----------------
ctx_011_planted = RuleContext(
    transactions=[
        {"posting_date": "2026-10-15", "net_amount": Decimal("30000.00"), "voucher_no": "V1"},
    ],
    period_id="2026-09"
)
ctx_011_absent = RuleContext(
    transactions=[
        {"posting_date": "2026-10-15", "net_amount": Decimal("30000.00"), "voucher_no": "V1"},
    ],
    period_id=None # missing as_of / period_id
)
run_test("EXC-011 (Code) / EXC-011 (Doc06)", evaluate_exc_011, ctx_011_planted, ctx_011_absent, "Medium", "as_of / period_id")

# -----------------
# 12. Code EXC-013 (Catalog EXC-013 Trailing Spike)
# -----------------
ctx_013_planted = RuleContext(
    transactions=[
        {"account_code": "5400", "net_amount": Decimal("100000.00"), "period_id": "2026-09", "voucher_no": "V1"},
    ],
    prior_period_actuals={
        "5400": [Decimal("20000.00"), Decimal("22000.00"), Decimal("21000.00")]
    },
    config={"EXC-013_min_spike_amount": "10000.00", "EXC-013_multiplier": "2.0"}
)
ctx_013_absent = RuleContext(
    transactions=[
        {"account_code": "5400", "net_amount": Decimal("100000.00"), "period_id": "2026-09"},
    ],
    prior_period_actuals={} # Missing >= 3 prior periods!
)
run_test("EXC-013 (Code) / EXC-013 (Doc06)", evaluate_exc_013, ctx_013_planted, ctx_013_absent, "Medium", ">=3 prior periods actuals")

# -----------------
# 13. Code EXC-014 (Catalog EXC-014 Unusual Vendor -> Account)
# -----------------
ctx_014_planted = RuleContext(
    transactions=[
        {"vendor_code": "V-LEGAL", "account_code": "5800", "net_amount": Decimal("40000.00"), "voucher_no": "V1"},
    ],
    historical_vendor_accounts={
        "V-LEGAL": {"5200"} # historically only posted to 5200!
    }
)
ctx_014_absent = RuleContext(
    transactions=[
        {"vendor_code": "V-LEGAL", "account_code": "5800", "net_amount": Decimal("40000.00"), "voucher_no": "V1"},
    ],
    historical_vendor_accounts={} # Empty history!
)
run_test("EXC-014 (Code) / EXC-014 (Doc06)", evaluate_exc_014, ctx_014_planted, ctx_014_absent, "Medium", "Historical vendor-account mappings")

# -----------------
# 14. Code EXC-016 (Catalog EXC-016 Missing Accrual)
# -----------------
ctx_016_planted = RuleContext(
    transactions=[], # Current period has NO accrual!
    prior_period_accruals={
        "5150": [Decimal("30000.00"), Decimal("32000.00"), Decimal("31000.00")]
    },
    period_id="2026-09"
)
ctx_016_absent = RuleContext(
    transactions=[],
    prior_period_accruals={}, # Empty prior accrual history
    period_id="2026-09"
)
run_test("EXC-016 (Code) / EXC-016 (Doc06)", evaluate_exc_016, ctx_016_planted, ctx_016_absent, "Medium", ">=3 prior period accruals")

# -----------------
# 15. Code EXC-019 (Catalog EXC-019 Cumulative Overrun)
# -----------------
ctx_019_planted = RuleContext(
    transactions=[
        {"account_code": "5300", "net_amount": Decimal("600000.00"), "period_id": "2026-09", "voucher_no": "V1"},
    ],
    annual_budget_by_account={"5300": Decimal("500000.00")}, # Spend 600k vs Annual budget 500k
    ytd_actual_by_account={"5300": Decimal("600000.00")}
)
ctx_019_absent = RuleContext(
    transactions=[
        {"account_code": "5300", "net_amount": Decimal("600000.00"), "period_id": "2026-09"},
    ],
    annual_budget_by_account=None # Missing annual budget!
)
run_test("EXC-019 (Code) / EXC-019 (Doc06)", evaluate_exc_019, ctx_019_planted, ctx_019_absent, "Medium", "annual_budget_by_account")

# -----------------
# 16. Code EXC-020 (Catalog EXC-020 Budget Coverage Gap)
# -----------------
ctx_020_planted = RuleContext(
    transactions=[
        {"account_code": "5700", "net_amount": Decimal("10000.00"), "period_id": "2026-09", "voucher_no": "V1"},
    ],
    annual_budget_by_account={"5100": Decimal("100000.00")} # 5700 has no budget!
)
ctx_020_absent = RuleContext(
    transactions=[],
    annual_budget_by_account={}
)
run_test("EXC-020 (Code) / EXC-020 (Doc06)", evaluate_exc_020, ctx_020_planted, ctx_020_absent, "Medium", "annual_budget_by_account")

# -----------------
# 17. Code EXC-021 (Catalog EXC-021 Approval Threshold)
# -----------------
ctx_021_planted = RuleContext(
    transactions=[
        {"account_code": "5100", "net_amount": Decimal("750000.00"), "voucher_no": "V1", "approver": "ANALYST_1"},
    ],
    approval_thresholds={"ANALYST_1": Decimal("100000.00")} # Exceeds 100k threshold!
)
ctx_021_absent = RuleContext(
    transactions=[
        {"account_code": "5100", "net_amount": Decimal("750000.00"), "voucher_no": "V1"},
    ],
    approval_thresholds=None # Missing approval thresholds!
)
run_test("EXC-021 (Code) / EXC-021 (Doc06)", evaluate_exc_021, ctx_021_planted, ctx_021_absent, "High", "approval_thresholds master table")

# -----------------
# 18. Code EXC-022 (Catalog EXC-022 Round Number Journal)
# -----------------
ctx_022_planted = RuleContext(
    transactions=[
        {"account_code": "5100", "net_amount": Decimal("1000000.00"), "voucher_no": "V1", "journal_category": "MANUAL", "description": "Manual round journal"},
    ],
    config={"EXC-022_threshold": "100000.00"}
)
ctx_022_absent = RuleContext(
    transactions=[
        {"account_code": "5100", "net_amount": Decimal("123456.78"), "voucher_no": "V1"},
    ]
)
run_test("EXC-022 (Code) / EXC-022 (Doc06)", evaluate_exc_022, ctx_022_planted, ctx_022_absent, "Low", "None (optional journal_category)")

# -----------------
# 19. Code EXC-023 (Catalog EXC-023 Voucher Imbalance)
# -----------------
ctx_023_planted = RuleContext(
    transactions=[
        {"voucher_no": "V-IMB", "debit": Decimal("1000.00"), "credit": Decimal("0.00"), "net_amount": Decimal("1000.00")},
        {"voucher_no": "V-IMB", "debit": Decimal("0.00"), "credit": Decimal("800.00"), "net_amount": Decimal("-800.00")},
    ]
)
ctx_023_absent = RuleContext(
    transactions=[
        {"voucher_no": "V-BAL", "debit": Decimal("1000.00"), "credit": Decimal("0.00"), "net_amount": Decimal("1000.00")},
        {"voucher_no": "V-BAL", "debit": Decimal("0.00"), "credit": Decimal("1000.00"), "net_amount": Decimal("-1000.00")},
    ]
)
run_test("EXC-023 (Code) / EXC-023 (Doc06)", evaluate_exc_023, ctx_023_planted, ctx_023_absent, "High", "None")

# -----------------
# 20. Code EXC-024 (Catalog EXC-024 Suspense Residual)
# -----------------
ctx_024_planted = RuleContext(
    transactions=[
        {"account_code": "1999", "debit": Decimal("250000.00"), "credit": Decimal("0.00"), "net_amount": Decimal("250000.00"), "voucher_no": "V1"},
    ],
    config={"EXC-024_threshold": "100000.00"}
)
ctx_024_absent = RuleContext(
    transactions=[
        {"account_code": "1999", "debit": Decimal("250000.00"), "credit": Decimal("0.00"), "net_amount": Decimal("250000.00"), "voucher_no": "V1"},
    ],
    suspense_accounts=[] # Missing suspense account configuration/tagging
)
run_test("EXC-024 (Code) / EXC-024 (Doc06)", evaluate_exc_024, ctx_024_planted, ctx_024_absent, "High", "Suspense account list")

# Output findings summary
import json
print("\n" + "="*80)
print(f"DEF-023 BEHAVIORAL EXECUTION RESULTS ({len(results)} evaluated rules)")
print("="*80)
for r in results:
    print(f"Rule: {r['rule_id']}")
    print(f"  Evaluator: {r['func']}")
    print(f"  Planted Condition Fired: {r['planted_fired']} (Findings: {r['planted_count']}, Err: {r['planted_err']})")
    print(f"  Absent Input Behavior: Fired={r['absent_fired']} (Count: {r['absent_count']}, Err: {r['absent_err']})")
    print(f"  Severity & Amount: {r['sev_match']} | {r['amt_info']}")
    print(f"  Declared Dependency: {r['doc_dep']}")
    print("-" * 60)
