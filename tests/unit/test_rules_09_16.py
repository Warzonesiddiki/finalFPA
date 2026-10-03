"""Unit tests for Exception Rules 09 to 16.

Per 06_EXCEPTION_RULES_CATALOG.md.
"""

import csv
from decimal import Decimal
from pathlib import Path

import pytest

from app.engine.imports.models import ParsedTransaction
from app.engine.rules.rules_01_08 import (
    RecurringCostRuleItem,
    RuleContext,
    period_end_from_id,
    resolve_as_of_date,
)
from app.engine.rules.rules_09_16 import (
    evaluate_all_09_16,
    evaluate_exc_009,
    evaluate_exc_010,
    evaluate_exc_011,
    evaluate_exc_012,
    evaluate_exc_013,
    evaluate_exc_014,
    evaluate_exc_015,
    evaluate_exc_016,
)

EXPECTED_EXCEPTIONS = Path("sample-data/expected_exceptions.csv")


def _fixture_subject_key(rule_id: str) -> str:
    """Read the ground-truth subject_key for `rule_id` from the sample fixture.

    The file opens with a `#` watermark comment line, which csv.DictReader would
    otherwise consume as the header row, so comment lines are stripped first.
    Reading the fixture rather than hard-coding the string means a drift on
    either side shows up as a test failure instead of a silent mismatch.
    """
    lines = [
        line
        for line in EXPECTED_EXCEPTIONS.read_text(encoding="utf-8-sig").splitlines()
        if not line.lstrip().startswith("#")
    ]
    rows = [r for r in csv.DictReader(lines) if r.get("rule_id") == rule_id]
    assert rows, f"{rule_id} has no ground-truth row in {EXPECTED_EXCEPTIONS}"
    return rows[0]["subject_key"]


def make_tx(
    source_row_ref="row_1",
    voucher_no="VCH-001",
    posting_date="2026-09-15",
    document_date=None,
    account_code="5200",
    cost_center_code="CC-100",
    vendor_code="V-001",
    debit=Decimal("0.00"),
    credit=Decimal("0.00"),
    net_amount=Decimal("0.00"),
    company_code="IN01",
) -> ParsedTransaction:
    return ParsedTransaction(
        source_row_ref=source_row_ref,
        voucher_no=voucher_no,
        posting_date=posting_date,
        company_code=company_code,
        account_code=account_code,
        cost_center_code=cost_center_code,
        project_code=None,
        vendor_code=vendor_code,
        invoice_no="INV-100",
        description="Sample expenditure",
        debit=debit,
        credit=credit,
        net_amount=net_amount,
        currency_code="INR",
        document_date=document_date,
    )


@pytest.mark.tst_id("TST-RUL-10")
def test_exc_010_cutoff_issue_raised():
    """Planting P10: prior-period document posted late into current period."""
    # Document date in August, posted in September
    tx = make_tx(
        source_row_ref="row_cut1",
        posting_date="2026-09-05",
        document_date="2026-08-28",
        debit=Decimal("320000.00"),
        net_amount=Decimal("320000.00"),
        vendor_code="V-00412",
        account_code="5450",
    )
    ctx = RuleContext(
        transactions=[tx],
        period_id="FY26-P09",
        config={"EXC-010_min_amount": "50000.00"},
    )
    findings = evaluate_exc_010(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-010"
    assert findings[0].amount_at_risk == Decimal("320000.00")
    assert "Cut-off issue" in findings[0].subject_display


@pytest.mark.tst_id("TST-RUL-11")
def test_exc_011_future_dated_posting_raised():
    """Planting P11: posting date occurs after injected as_of_date."""
    tx = make_tx(
        source_row_ref="row_fut1",
        voucher_no="VCH-2026-0930-021",
        posting_date="2026-11-30",
        debit=Decimal("175000.00"),
        net_amount=Decimal("175000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        period_id="FY26-P09",
        as_of_date="2026-11-12",
    )
    findings = evaluate_exc_011(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-011"
    assert findings[0].amount_at_risk == Decimal("175000.00")
    assert "18 days ahead" in findings[0].detail


def test_exc_011_subject_key_matches_expected_exceptions_fixture():
    """The emitted EXC-011 subject key must equal the ground-truth fixture value.

    expected_exceptions.csv P11 records `IN01|VCH-2026-0930-021` (company and
    voucher only). Doc 06 EXC-011 writes the key illustratively as
    `company_code|voucher_no|posting_date`. Per the EXC-016 precedent the fixture
    is authoritative, because the key feeds the
    sha256(rule_id|subject_key) identity hash used for re-run matching.

    This test reads the fixture rather than hard-coding the string, so it fails
    if either side drifts.
    """
    expected_key = _fixture_subject_key("EXC-011")

    tx = make_tx(
        source_row_ref="row_fut1",
        voucher_no="VCH-2026-0930-021",
        posting_date="2026-11-30",
        debit=Decimal("175000.00"),
        net_amount=Decimal("175000.00"),
    )
    ctx = RuleContext(
        transactions=[tx], period_id="FY26-P09", as_of_date="2026-11-12"
    )
    findings = evaluate_exc_011(ctx)

    assert len(findings) == 1
    assert findings[0].subject_key == expected_key
    # The posting date is a grouping input, not an identity input.
    assert findings[0].subject_key.count("|") == 1
    assert "2026-11-30" not in findings[0].subject_key
    # ...but it is still reported in the detail, which is what a reviewer reads.
    assert "2026-11-30" in findings[0].detail


def test_exc_011_grouping_by_date_is_unchanged_by_the_key_change():
    """Dropping the date from the key must NOT merge two dates for one voucher.

    The key is company|voucher, but grouping stays (company, voucher, date), so
    a voucher posted on two different future dates still yields two findings -
    they simply share an identity hash. This pins that behaviour so a future
    "simplification" of the grouping cannot silently collapse them.
    """
    early = make_tx(
        source_row_ref="row_1",
        voucher_no="VCH-SAME",
        posting_date="2026-11-20",
        debit=Decimal("100.00"),
        net_amount=Decimal("100.00"),
    )
    late = make_tx(
        source_row_ref="row_2",
        voucher_no="VCH-SAME",
        posting_date="2026-12-20",
        debit=Decimal("200.00"),
        net_amount=Decimal("200.00"),
    )
    ctx = RuleContext(
        transactions=[early, late], period_id="FY26-P09", as_of_date="2026-11-12"
    )
    findings = evaluate_exc_011(ctx)

    assert len(findings) == 2, "grouping is still per posting_date"
    assert {f.subject_key for f in findings} == {"IN01|VCH-SAME"}
    # Same identity, different detail - documented, and the reason the re-run
    # path treats the second as flagged_again rather than a new exception.
    assert len({f.identity_hash for f in findings}) == 1


@pytest.mark.tst_id("TST-RUL-13")
def test_exc_013_out_of_pattern_spike_raised():
    """Planting P13: current period spikes 4x vs historical trailing average."""
    tx = make_tx(
        source_row_ref="row_spike",
        account_code="5600",
        cost_center_code="CC-140",
        debit=Decimal("186000.00"),
        net_amount=Decimal("186000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        period_id="FY26-P09",
        config={
            "historical_averages": {"IN01|5600|CC-140": Decimal("45000.00")},
            "EXC-013_spike_ratio": Decimal("2.5"),
            "EXC-013_min_deviation": Decimal("50000.00"),
        },
    )
    findings = evaluate_exc_013(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-013"
    assert findings[0].amount_at_risk == Decimal("141000.00")  # 186k - 45k


@pytest.mark.tst_id("TST-RUL-14")
def test_exc_014_unusual_vendor_account_combination():
    """Planting P14: vendor bills unfamiliar account category."""
    tx = make_tx(
        source_row_ref="row_p14",
        vendor_code="V-00276",
        account_code="5800",
        debit=Decimal("260000.00"),
        net_amount=Decimal("260000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        period_id="FY26-P09",
        config={
            "known_vendor_accounts": {("V-00276", "5100")},
            "EXC-014_min_amount": Decimal("100000.00"),
        },
    )
    findings = evaluate_exc_014(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXC-014"
    assert findings[0].amount_at_risk == Decimal("260000.00")


# ==============================================================================
# EXC-009 - Posting date / fiscal period mismatch (catalog EXC-009)
# Doc 06: group by (batch, company, source period, derived period); High; min_rows 1.
# ==============================================================================

@pytest.mark.tst_id("TST-RUL-09")
def test_exc_009_period_mismatch_raised():
    """Planting P9: rows declare source period FY26-P09 but post in October."""
    txs = [
        make_tx(
            source_row_ref=f"row_0088{i}",
            posting_date="2026-10-09",
            account_code="5450",
            debit=Decimal("92000.00"),
            net_amount=Decimal("92000.00"),
        )
        for i in range(1, 4)
    ]
    for tx in txs:
        tx.period_code = "FY26-P09"
    ctx = RuleContext(transactions=txs, period_id="FY26-P09")
    findings = evaluate_exc_009(ctx)
    assert len(findings) == 1
    assert findings[0].catalog_rule_id == "EXC-009"
    assert findings[0].severity == "High"
    assert findings[0].amount_at_risk == Decimal("276000.00")
    assert "3 rows" in findings[0].detail


def test_exc_009_not_raised_when_period_agrees():
    tx = make_tx(posting_date="2026-09-15", net_amount=Decimal("1000.00"))
    tx.period_code = "FY26-P09"
    findings = evaluate_exc_009(RuleContext(transactions=[tx], period_id="FY26-P09"))
    assert findings == []


# ==============================================================================
# EXC-012 - Unusual negative expense / credit (catalog EXC-012)
# Doc 06: credited total above min_credit_amount and offset_ratio < 0.90.
# ==============================================================================

@pytest.mark.tst_id("TST-RUL-12")
def test_exc_012_unusual_credit_raised():
    """Planting P12: credits 680000.00 offset only by 120000.00 (17.6%)."""
    # Credits totalling 680000.00 with offsets totalling 120000.00 (17.6% offset)
    credits = [
        make_tx(
            source_row_ref='row_cr1',
            posting_date='2026-09-21',
            account_code='5400',
            cost_center_code='CC-110',
            credit=Decimal('500000.00'),
            net_amount=Decimal('-500000.00'),
        ),
        make_tx(
            source_row_ref='row_cr2',
            posting_date='2026-09-22',
            account_code='5400',
            cost_center_code='CC-110',
            credit=Decimal('180000.00'),
            net_amount=Decimal('-180000.00'),
        ),
    ]
    offsets = [
        make_tx(
            source_row_ref='row_db1',
            posting_date='2026-09-20',
            account_code='5400',
            cost_center_code='CC-110',
            debit=Decimal('80000.00'),
            net_amount=Decimal('80000.00'),
        ),
        make_tx(
            source_row_ref='row_db2',
            posting_date='2026-09-20',
            account_code='5400',
            cost_center_code='CC-110',
            debit=Decimal('40000.00'),
            net_amount=Decimal('40000.00'),
        ),
    ]
    ctx = RuleContext(transactions=credits + offsets, period_id="FY26-P09")
    findings = evaluate_exc_012(ctx)
    assert len(findings) == 1
    assert findings[0].catalog_rule_id == "EXC-012"
    assert findings[0].amount_at_risk == Decimal("680000.00")


def test_exc_012_not_raised_when_offset_by_same_period_debits():
    """Precision control P27: same-period offset clears the 0.90 ratio."""
    credits = [
        make_tx(
            source_row_ref="row_cr1",
            posting_date="2026-09-25",
            account_code="5400",
            cost_center_code="CC-115",
            credit=Decimal("50000.00"),
            net_amount=Decimal("-50000.00"),
        )
    ]
    offsets = [
        make_tx(
            source_row_ref="row_db1",
            posting_date="2026-09-26",
            account_code="5400",
            cost_center_code="CC-115",
            debit=Decimal("48000.00"),
            net_amount=Decimal("48000.00"),
        )
    ]
    ctx = RuleContext(transactions=credits + offsets, period_id="FY26-P09")
    assert evaluate_exc_012(ctx) == []


# ==============================================================================
# EXC-015 - Missing recurring cost (catalog EXC-015)
# Doc 06: no posting within tolerance_pct (10%) of expected_amount -> raise.
# ==============================================================================

def _recurring(**kwargs) -> RecurringCostRuleItem:
    base = dict(
        recurring_id="RC-001",
        name="Office Rent Andheri",
        vendor_code="V-00118",
        expected_amount=Decimal("450000.00"),
        account_code="5100",
        cost_center_code="CC-120",
        tolerance_pct=Decimal("0.10"),
    )
    base.update(kwargs)
    return RecurringCostRuleItem(**base)


@pytest.mark.tst_id("TST-RUL-15")
def test_exc_015_missing_recurring_cost_raised():
    """Planting P15(a): office rent 450000.00 absent from the period."""
    ctx = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        master_recurring_costs=[_recurring()],
        config={"EXC-006_skip_if_period_missing": False},
    )
    findings = evaluate_exc_015(ctx)
    assert len(findings) == 1
    assert findings[0].catalog_rule_id == "EXC-015"
    assert findings[0].amount_at_risk == Decimal("450000.00")
    assert findings[0].severity == "High"


def test_exc_015_within_tolerance_not_raised():
    """Precision control P32: charge posted 8% below expected is inside tolerance."""
    tx = make_tx(
        source_row_ref="row_rent",
        posting_date="2026-09-03",
        vendor_code="V-00118",
        account_code="5100",
        cost_center_code="CC-120",
        debit=Decimal("414000.00"),
        net_amount=Decimal("414000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        period_id="FY26-P09",
        master_recurring_costs=[_recurring()],
    )
    assert evaluate_exc_015(ctx) == []


def test_exc_015_disabled_without_master_list():
    """Doc 06 section 3: without the recurring-cost master the rule never guesses."""
    ctx = RuleContext(transactions=[], period_id="FY26-P09", master_recurring_costs=[])
    assert evaluate_exc_015(ctx) == []


# ==============================================================================
# EXC-016 - Missing expected accrual (catalog EXC-016)
# Doc 06: 3 stable pre-close accruals (stability_band 25%, window 5 days) but
# nothing comparable in the current period.
# ==============================================================================

PRIOR_ACCRUALS = [
    {"period_id": "FY26-P06", "company_code": "IN01", "account_code": "6100",
     "cost_center_code": "CC-120", "posting_date": "2026-06-27",
     "amount": Decimal("185000.00"), "source_row_ref": "row_h06"},
    {"period_id": "FY26-P07", "company_code": "IN01", "account_code": "6100",
     "cost_center_code": "CC-120", "posting_date": "2026-07-28",
     "amount": Decimal("185000.00"), "source_row_ref": "row_h07"},
    {"period_id": "FY26-P08", "company_code": "IN01", "account_code": "6100",
     "cost_center_code": "CC-120", "posting_date": "2026-08-27",
     "amount": Decimal("185000.00"), "source_row_ref": "row_h08"},
]


@pytest.mark.tst_id("TST-RUL-16")
def test_exc_016_missing_accrual_raised():
    """Planting P16: stable accrual pattern on 6100/CC-120 absent in FY26-P09."""
    ctx = RuleContext(
        transactions=[
            make_tx(
                source_row_ref="row_cur1",
                posting_date="2026-09-10",
                account_code="6100",
                cost_center_code="CC-120",
                debit=Decimal("42000.00"),
                net_amount=Decimal("42000.00"),
            )
        ],
        period_id="FY26-P09",
        config={"EXC-016_prior_periods": PRIOR_ACCRUALS},
    )
    findings = evaluate_exc_016(ctx)
    assert len(findings) == 1
    f = findings[0]
    assert f.catalog_rule_id == "EXC-016"
    assert f.subject_key == "IN01|6100|CC-120"
    assert f.amount_at_risk == Decimal("185000.00")
    assert f.severity == "Medium"
    assert f.tier == "fuzzy"
    assert "FY26-P06" in f.detail and "FY26-P08" in f.detail
    assert "row_h06" in f.evidence_refs


def test_exc_016_not_raised_when_accrual_posted_in_window():
    """A comparable pre-close credit in FY26-P09 clears the pattern."""
    tx = make_tx(
        source_row_ref="row_accr",
        posting_date="2026-09-28",
        account_code="6100",
        cost_center_code="CC-120",
        credit=Decimal("185000.00"),
        net_amount=Decimal("-185000.00"),
    )
    ctx = RuleContext(
        transactions=[tx],
        period_id="FY26-P09",
        config={"EXC-016_prior_periods": PRIOR_ACCRUALS},
    )
    assert evaluate_exc_016(ctx) == []


def test_exc_016_disabled_without_enough_history():
    """Doc 06 section 3: needs at least pattern_periods loaded periods."""
    ctx = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        config={"EXC-016_prior_periods": PRIOR_ACCRUALS[:2]},
    )
    assert evaluate_exc_016(ctx) == []


def test_exc_016_not_raised_when_pattern_unstable():
    """Amounts outside the 25% stability band are not a pattern."""
    unstable = [
        dict(rec, amount=Decimal("60000.00")) for rec in PRIOR_ACCRUALS[:2]
    ] + [dict(PRIOR_ACCRUALS[2], amount=Decimal("185000.00"))]
    ctx = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        config={"EXC-016_prior_periods": unstable},
    )
    assert evaluate_exc_016(ctx) == []


def test_exc_016_respects_exclusion_list():
    """Tuning path: account added to the accrual-pattern exclusion list."""
    ctx = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        config={
            "EXC-016_prior_periods": PRIOR_ACCRUALS,
            "EXC-016_excluded_keys": {"IN01|6100|CC-120"},
        },
    )
    assert evaluate_exc_016(ctx) == []


# ==============================================================================
# Batch entry point
# ==============================================================================

def test_batch_09_16_runs_all_eight_rules():
    """EXC-009..EXC-016 all execute through evaluate_all_09_16."""
    ctx = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        master_recurring_costs=[_recurring()],
        config={
            "EXC-006_skip_if_period_missing": False,
            "EXC-016_prior_periods": PRIOR_ACCRUALS,
        },
    )
    findings = evaluate_all_09_16(ctx)
    assert {f.catalog_rule_id for f in findings} == {"EXC-015", "EXC-016"}


# ==============================================================================
# EXC-011 ranking mitigation (doc 06 EXC-011 Mitigation)
#
# Quote: "Rows dated within the current open period but after the run date are the
# common legitimate case and are ranked last in the detail; rows dated beyond the
# period end are ranked first."
# ==============================================================================

def test_exc_011_ranks_beyond_period_end_first():
    """Beyond-period-end postings sort ahead of in-open-period future postings.

    Period FY26-P12 ends 2026-12-31; run date 2026-11-12.
    - VCH-B is dated 2027-01-15 -> beyond the period end -> must rank first.
    - VCH-A is dated 2026-11-20 -> inside the still-open period -> ranked last,
      even though its voucher number sorts alphabetically earlier.
    """
    beyond = make_tx(
        source_row_ref="row_beyond",
        voucher_no="VCH-B",
        posting_date="2027-01-15",
        account_code="5200",
        debit=Decimal("90000.00"),
        net_amount=Decimal("90000.00"),
    )
    within = make_tx(
        source_row_ref="row_within",
        voucher_no="VCH-A",
        posting_date="2026-11-20",
        account_code="5200",
        debit=Decimal("10000.00"),
        net_amount=Decimal("10000.00"),
    )
    ctx = RuleContext(
        transactions=[within, beyond],
        period_id="FY26-P12",
        as_of_date="2026-11-12",
    )
    findings = evaluate_exc_011(ctx)
    assert len(findings) == 2
    # Subject key is company|voucher (fixture form, per expected_exceptions.csv
    # P11 and the EXC-016 precedent). The posting date is a grouping input, not
    # an identity input.
    assert findings[0].subject_key == "IN01|VCH-B"
    assert findings[1].subject_key == "IN01|VCH-A"
    assert "beyond period end" in findings[0].detail
    assert "within the open period" in findings[1].detail


def test_exc_011_ranking_is_deterministic_across_input_order():
    """Same set, different input order, identical ranked output."""
    rows = [
        make_tx(
            source_row_ref=f"row_r{i}",
            voucher_no=f"VCH-{i:03d}",
            posting_date="2026-11-20" if i % 2 else "2027-02-01",
            debit=Decimal("1000.00"),
            net_amount=Decimal("1000.00"),
        )
        for i in range(1, 7)
    ]
    fwd = evaluate_exc_011(
        RuleContext(transactions=list(rows), period_id="FY26-P12", as_of_date="2026-11-12")
    )
    rev = evaluate_exc_011(
        RuleContext(transactions=list(reversed(rows)), period_id="FY26-P12", as_of_date="2026-11-12")
    )
    assert [f.subject_key for f in fwd] == [f.subject_key for f in rev]
    # All beyond-period-end rows precede all in-open-period rows.
    flags = ["beyond period end" in f.detail for f in fwd]
    assert flags == sorted(flags, reverse=True)


def test_exc_011_detail_shows_voucher_and_account():
    """Doc 06 mitigation: the detail shows the voucher and account."""
    tx = make_tx(
        source_row_ref="row_det",
        voucher_no="VCH-2026-0930-021",
        posting_date="2026-11-30",
        account_code="5450",
        debit=Decimal("175000.00"),
        net_amount=Decimal("175000.00"),
    )
    ctx = RuleContext(transactions=[tx], period_id="FY26-P09", as_of_date="2026-11-12")
    findings = evaluate_exc_011(ctx)
    assert len(findings) == 1
    detail = findings[0].detail
    assert "VCH-2026-0930-021" in detail
    assert "5450" in detail
    assert "18 days ahead" in detail


def test_exc_011_amount_at_risk_unchanged_by_ranking():
    """Ranking must not alter grouping or Decimal amounts."""
    txs = [
        make_tx(
            source_row_ref=f"row_g{i}",
            voucher_no="VCH-G",
            posting_date="2026-11-30",
            debit=Decimal("1000.00"),
            net_amount=Decimal("1000.00"),
        )
        for i in range(3)
    ]
    ctx = RuleContext(transactions=txs, period_id="FY26-P09", as_of_date="2026-11-12")
    findings = evaluate_exc_011(ctx)
    assert len(findings) == 1
    assert findings[0].amount_at_risk == Decimal("3000.00")


# ==============================================================================
# as_of resolution (doc 06 Purity + EXC-011 injection contract; doc 05 CALC-002)
# ==============================================================================

def test_default_as_of_resolves_to_period_end():
    """No caller as_of -> the run date is the period under review's end date.

    Doc 05 CALC-002: a transaction belongs to the period whose
    `start_date <= posting_date <= end_date`.
    """
    ctx = RuleContext(transactions=[], period_id="FY26-P09")
    assert ctx.as_of_date == "2026-09-30"

    ctx_dec = RuleContext(transactions=[], period_id="FY26-P12")
    assert ctx_dec.as_of_date == "2026-12-31"

    ctx_leap = RuleContext(transactions=[], period_id="FY28-P02")
    assert ctx_leap.as_of_date == "2028-02-29"


def test_explicit_as_of_always_wins():
    """An injected run date is never overridden by the period default."""
    ctx = RuleContext(transactions=[], period_id="FY26-P09", as_of_date="2026-11-12")
    assert ctx.as_of_date == "2026-11-12"

    # Even when DimPeriod data is present, the explicit value stands.
    ctx2 = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        as_of_date="2026-10-15",
        dim_period_end_dates={"FY26-P09": "2026-09-30"},
    )
    assert ctx2.as_of_date == "2026-10-15"

    # A date object is accepted and normalised to ISO.
    from datetime import date as _date
    ctx3 = RuleContext(transactions=[], period_id="FY26-P09", as_of_date=_date(2026, 10, 1))
    assert ctx3.as_of_date == "2026-10-01"


def test_dim_period_calendar_takes_precedence_over_fallback():
    """Doc 05 CALC-001: the fiscal calendar is data, not code.

    A March year-start FY26-P09 ends 2026-11-30, not the January-start 2026-09-30.
    """
    ctx = RuleContext(
        transactions=[],
        period_id="FY26-P09",
        dim_period_end_dates={"FY26-P09": "2026-11-30"},
    )
    assert ctx.as_of_date == "2026-11-30"


def test_resolve_as_of_date_returns_none_for_unresolvable_period():
    """No period id -> None, never a system-clock fallback (doc 06 Purity)."""
    assert resolve_as_of_date(None) is None
    assert resolve_as_of_date("not-a-period") is None


def test_resolve_as_of_date_precedence_order():
    """Explicit > DimPeriod > calendar fallback, checked directly."""
    assert resolve_as_of_date("FY26-P09", explicit_as_of="2026-12-01") == "2026-12-01"
    assert resolve_as_of_date(
        "FY26-P09",
        dim_period_end_dates={"FY26-P09": "2026-11-30"},
    ) == "2026-11-30"
    assert resolve_as_of_date("FY26-P09") == "2026-09-30"


def test_default_as_of_scopes_future_dated_to_the_period_close():
    """Period-scoped as_of means every post-period-end row is flagged.

    With as_of defaulted to the period end (2026-09-30), anything dated after the
    close is future-dated relative to that close - including December postings.
    This is the correct close semantic; it is NOT a volume reduction.
    """
    in_scope = make_tx(
        source_row_ref="row_oct",
        voucher_no="VCH-OCT",
        posting_date="2026-10-05",
        debit=Decimal("50000.00"),
        net_amount=Decimal("50000.00"),
    )
    late = make_tx(
        source_row_ref="row_dec",
        voucher_no="VCH-DEC",
        posting_date="2026-12-05",
        debit=Decimal("50000.00"),
        net_amount=Decimal("50000.00"),
    )
    default_ctx = RuleContext(transactions=[in_scope, late], period_id="FY26-P09")
    assert default_ctx.as_of_date == "2026-09-30"
    findings = evaluate_exc_011(default_ctx)
    # Both flag, and the ranking mitigation orders them deterministically.
    assert len(findings) == 2
    assert all("beyond period end" in f.detail for f in findings)
    assert [f.subject_key for f in findings] == [
        "IN01|VCH-DEC",
        "IN01|VCH-OCT",
    ]

    # An earlier explicit run date narrows the lens to rows after that date.
    earlier = RuleContext(
        transactions=[in_scope, late], period_id="FY26-P09", as_of_date="2026-11-01"
    )
    assert [f.subject_key for f in evaluate_exc_011(earlier)] == [
        "IN01|VCH-DEC"
    ]


def test_as_of_resolution_has_no_clock_dependency():
    """Doc 06 line 195: pure function of data + config, no randomness/clock.

    Two identically-constructed contexts must resolve identically, and resolving
    twice must be stable.
    """
    a = RuleContext(transactions=[], period_id="FY26-P06")
    b = RuleContext(transactions=[], period_id="FY26-P06")
    assert a.as_of_date == b.as_of_date == "2026-06-30"
    assert resolve_as_of_date("FY26-P06") == resolve_as_of_date("FY26-P06")


def test_as_of_helpers_are_exported_from_the_package():
    """RuleContext.__post_init__ calls resolve_as_of_date at construction time.

    If the symbol is ever renamed or dropped from app.engine.rules, every
    RuleContext construction raises NameError and the whole rules suite dies.
    This guards the package-level export path, not just the module path.
    """
    import app.engine.rules as pkg

    assert hasattr(pkg, "resolve_as_of_date")
    assert hasattr(pkg, "period_end_from_id")
    assert "resolve_as_of_date" in pkg.__all__
    assert pkg.resolve_as_of_date is resolve_as_of_date
    assert pkg.period_end_from_id is period_end_from_id

    # And the package-level symbol is the one the dataclass actually calls.
    assert RuleContext(transactions=[], period_id="FY26-P09").as_of_date == "2026-09-30"
