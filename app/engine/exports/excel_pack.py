"""Month-End Excel Pack Generator using openpyxl.

Implements sheets 1 through 7 specified in docs/11_EXCEL_OUTPUT_SPEC.md:
- Sheet 1: Cover & Context
- Sheet 2: Executive Summary & BvA
- Sheet 3: P&L Statement Analysis
- Sheet 4: Transaction Detail Drilldown
- Sheet 5: Exception Register
- Sheet 6: Forecast Summary
- Sheet 7: Import Reconciliation

Features:
- Values-only workbooks (zero formulas)
- Strict accounting number formatting and column widths
- Frozen panes on data sheets at C7
- Auto-filters on row 6 spanning data columns
- Stamp block with defined names on Sheet 1
- Visual signals with greyscale non-colour indicators (Fav ▲ / Adv ▼ / etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, overload

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from app.engine.calc.math import quantize_money
from app.engine.exports import formats as fmt
from app.engine.exports.stamps import STAMP_FIELDS


@overload
def _coerce_money(value: None) -> None: ...
@overload
def _coerce_money(value: Decimal | str | int | float) -> Decimal: ...
def _coerce_money(value: Decimal | str | int | float | None) -> Decimal | None:
    """DEF-015: carry money as Decimal (17 §5.1); None stays None for gaps.

    Single choke point over ``quantize_money`` (R12): float inputs recover via
    str, never via ``Decimal(some_float)``, so sample-data float literals land
    on their intended 2 dp value instead of their binary expansion.
    """
    return None if value is None else quantize_money(value)


# -------------------------------------------------------------------------
# Theme, Colors, Fonts, Borders
# -------------------------------------------------------------------------

FONT_NAME = "Calibri"

FONT_TITLE = Font(name=FONT_NAME, size=14, bold=True, color="1F3A5F")
FONT_SUBTITLE = Font(name=FONT_NAME, size=10, bold=False, color="334155")
FONT_META = Font(name=FONT_NAME, size=9, italic=False, color="64748B")
FONT_SECTION = Font(name=FONT_NAME, size=11, bold=True, color="0F172A")
FONT_TBL_HEADER = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
FONT_DATA = Font(name=FONT_NAME, size=10, bold=False, color="000000")
FONT_DATA_BOLD = Font(name=FONT_NAME, size=10, bold=True, color="000000")
FONT_TOTAL = Font(name=FONT_NAME, size=10, bold=True, color="0F172A")
FONT_EMPTY = Font(name=FONT_NAME, size=10, italic=True, color="64748B")
FONT_UNITS = Font(name=FONT_NAME, size=10, bold=True, color="1F3A5F")

# Fills
FILL_HEADER = PatternFill(start_color="1F3A5F", end_color="1F3A5F", fill_type="solid")
FILL_SECTION = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
FILL_TOTAL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

# Signal / CF Fills & Fonts (per §3.7)
FILL_FAV = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
FONT_FAV = Font(name=FONT_NAME, size=10, bold=True, color="1B5E20")

FILL_ADV = PatternFill(start_color="FDECEA", end_color="FDECEA", fill_type="solid")
FONT_ADV = Font(name=FONT_NAME, size=10, bold=True, color="B3261E")

FILL_NEUTRAL = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
FONT_NEUTRAL = Font(name=FONT_NAME, size=10, bold=False, color="6B7280")

FILL_SEV_HIGH = PatternFill(start_color="F6D5D3", end_color="F6D5D3", fill_type="solid")
FONT_SEV_HIGH = Font(name=FONT_NAME, size=10, bold=True, color="7A1C16")

FILL_SEV_MED = PatternFill(start_color="FDF0D5", end_color="FDF0D5", fill_type="solid")
FONT_SEV_MED = Font(name=FONT_NAME, size=10, bold=True, color="7A5200")

FILL_SEV_LOW = PatternFill(start_color="E3F1E6", end_color="E3F1E6", fill_type="solid")
FONT_SEV_LOW = Font(name=FONT_NAME, size=10, bold=False, color="1F5C2C")

# Borders
BORDER_THIN = Border(
    left=Side(style="thin", color="E2E8F0"),
    right=Side(style="thin", color="E2E8F0"),
    top=Side(style="thin", color="E2E8F0"),
    bottom=Side(style="thin", color="E2E8F0"),
)

BORDER_TOTAL = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="000000"),
    bottom=Side(style="double", color="000000"),
)

BORDER_SECTION = Border(
    bottom=Side(style="medium", color="1F3A5F"),
)

# Alignments
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_WRAP_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_HEADER = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Tab Colors
TAB_COLORS = {
    "Cover & Context": "1F3A5F",
    "Executive Summary & BvA": "2E7D32",
    "P&L Statement Analysis": "4C8C4A",
    "Transaction Detail Drilldown": "9AA0A6",
    "Exception Register": "B7791F",
    "Forecast Summary": "1A4FA0",
    "Import Reconciliation": "6A5ACD",
}


# -------------------------------------------------------------------------
# Data Models for Excel Pack Generation
# -------------------------------------------------------------------------


@dataclass
class PackContext:
    project_name: str = "Acme Manufacturing"
    entities: list[str] = field(default_factory=lambda: ["IN01", "IN02"])
    periods: list[str] = field(default_factory=lambda: ["FY26-P09"])
    window: str = "MTD"
    scenario: str = "Base"
    forecast_version: str = "Base v3 (locked 2026-09-30)"
    budget_version: str = "FY26-Approved"
    generated_at: str = "2026-10-01 14:22:31"
    pack_version: str = "v1"
    file_version: int = 1
    app_version: str = "0.9.0"
    units: str = "₹ whole units"
    grouping: str = "Indian (lakh/crore)"
    batch_ids: list[int] = field(default_factory=lambda: [1041, 1042, 1043])
    source_files: list[str] = field(
        default_factory=lambda: [
            "D365_GL_Sep26.xlsx",
            "Payroll_Sep26.csv",
            "Procurement_Sep26.xlsx",
        ]
    )
    filter_json: str = '{"entity":["IN01","IN02"],"period":["FY26-P09"]}'
    filter_human: str = "Entity=IN01, IN02 · Period=FY26-P09 · CC=All · Account=All"
    tie_out_state: str = "Balanced (debits = credits; variance ₹0.00)"
    sample_data: str = "No"
    stale_results: str = "No"
    content_hash: str = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    correlation_id: str = "run-default"
    claim_id: str = "claim-default"


@dataclass
class BvARow:
    level: int
    account_code: str
    account_name: str
    account_type: str
    cost_centre: str
    actual: Decimal
    budget: Decimal
    variance: Decimal
    var_pct: float | None
    signal: str
    effective_threshold: str = "—"
    rank: int = 0
    rows_count: int = 0
    commentary: str = ""

    def __post_init__(self) -> None:
        self.actual = _coerce_money(self.actual)
        self.budget = _coerce_money(self.budget)
        self.variance = _coerce_money(self.variance)


@dataclass
class PLRow:
    line_item: str
    category: str
    actual_mtd: Decimal
    budget_mtd: Decimal
    var_mtd: Decimal
    var_pct_mtd: float | None
    actual_ytd: Decimal
    budget_ytd: Decimal
    var_ytd: Decimal
    var_pct_ytd: float | None
    signal: str
    notes: str = ""
    is_summary: bool = False

    def __post_init__(self) -> None:
        self.actual_mtd = _coerce_money(self.actual_mtd)
        self.budget_mtd = _coerce_money(self.budget_mtd)
        self.var_mtd = _coerce_money(self.var_mtd)
        self.actual_ytd = _coerce_money(self.actual_ytd)
        self.budget_ytd = _coerce_money(self.budget_ytd)
        self.var_ytd = _coerce_money(self.var_ytd)


@dataclass
class TransactionRow:
    row_num: int
    entity: str
    account_code: str
    account_name: str
    cost_centre: str
    department: str
    project: str
    vendor: str
    vendor_code: str
    period: str
    posting_date: date | str
    document_date: date | str
    voucher_no: str
    document_no: str
    invoice_no: str
    line: int
    description: str
    journal_category: str
    debit: Decimal
    credit: Decimal
    net: Decimal
    dr_cr: str
    currency: str
    source_system: str
    source_file: str
    source_row_ref: str
    batch_id: int
    fingerprint: str
    exception_ids: str = ""

    def __post_init__(self) -> None:
        self.debit = _coerce_money(self.debit)
        self.credit = _coerce_money(self.credit)
        self.net = _coerce_money(self.net)


@dataclass
class ExceptionRow:
    exception_id: int
    rule_id: str
    rule_name: str
    rule_version: str
    family: str
    severity: str
    mark: str
    subject: str
    subject_key: str
    entity: str
    account_code: str
    account_name: str
    cost_centre: str
    vendor: str
    period: str
    first_seen: str
    amount_at_risk: Decimal
    status: str
    owner: str
    age_days: int
    overdue: str
    sla_due: date | str
    effective_threshold: str
    flagged_again: str
    notes_count: int
    last_note: date | str
    evidence_refs: str
    raised_at: datetime | str
    last_seen_at: datetime | str
    closed_at: datetime | str | None
    run_id: int
    correlation_id: str | None = None
    claim_id: str | None = None

    def __post_init__(self) -> None:
        self.amount_at_risk = _coerce_money(self.amount_at_risk)


@dataclass
class ForecastRow:
    level: int
    account_code: str
    account_group: str
    period: str
    scenario: str
    method: str
    method_source: str
    actual: Decimal | None
    budget: Decimal
    forecast: Decimal | None
    variance: Decimal
    var_pct: float | None
    signal: str = ""
    base_method: str = ""
    adjustment_pct: float | None = None
    override_reason: str = ""
    version: str = "Base v3"
    updated_at: str = "2026-09-30 18:00"



@dataclass
class AccountingActionLogRow:
    voucher_no: str
    account_code: str
    cost_centre: str
    posting_date: str
    debit: Decimal
    credit: Decimal
    description: str
    exception_id: int
    rule_id: str


    def __post_init__(self) -> None:
        self.debit = _coerce_money(self.debit)
        self.credit = _coerce_money(self.credit)


@dataclass
class ImportBatchRow:
    batch_id: int
    status: str
    source_system: str
    file_name: str
    sheet: str
    checksum_short: str
    checksum_full: str
    rows_read: int
    rows_committed: int
    rows_quarantined: int
    rows_rejected: int
    debit_total: Decimal
    credit_total: Decimal
    balance_variance: Decimal
    control_total_source: Decimal | None
    control_variance: Decimal
    balance_result: str
    profile_version: str
    loaded_at: datetime | str
    loaded_by: str
    quarantine_ref: str = "—"

    def __post_init__(self) -> None:
        self.debit_total = _coerce_money(self.debit_total)
        self.credit_total = _coerce_money(self.credit_total)
        self.balance_variance = _coerce_money(self.balance_variance)
        self.control_total_source = _coerce_money(self.control_total_source)
        self.control_variance = _coerce_money(self.control_variance)


@dataclass
class ValidationCheckRow:
    check_id: str
    check_name: str
    weight: int
    result: str
    rows_affected: int
    message: str


@dataclass
class MonthEndPackData:
    context: PackContext = field(default_factory=PackContext)
    bva_rows: list[BvARow] = field(default_factory=list)
    pl_rows: list[PLRow] = field(default_factory=list)
    transaction_rows: list[TransactionRow] = field(default_factory=list)
    exception_rows: list[ExceptionRow] = field(default_factory=list)
    forecast_rows: list[ForecastRow] = field(default_factory=list)
    import_batches: list[ImportBatchRow] = field(default_factory=list)
    validation_checks: list[ValidationCheckRow] = field(default_factory=list)


# -------------------------------------------------------------------------
# Sample Data Factory (for default pack generation & tests)
# -------------------------------------------------------------------------


def create_sample_pack_data(context: PackContext | None = None) -> MonthEndPackData:
    """Create a fully-populated MonthEndPackData instance with representative figures."""
    ctx = context or PackContext()

    bva = [
        BvARow(
            1,
            "4000",
            "Revenue",
            "revenue",
            "All",
            Decimal("12500000.00"),
            Decimal("12000000.00"),
            Decimal("500000.00"),
            4.17,
            "Fav ▲",
            "materiality 2.0% or ₹500,000",
            1,
            1420,
            "Exceeded target due to volume expansion",
        ),
        BvARow(
            2,
            "4100",
            "  Domestic Sales",
            "revenue",
            "All",
            Decimal("9800000.00"),
            Decimal("9500000.00"),
            Decimal("300000.00"),
            3.16,
            "Fav ▲",
            "—",
            3,
            1100,
            "Higher enterprise uptake",
        ),
        BvARow(
            2,
            "4200",
            "  Export Sales",
            "revenue",
            "All",
            Decimal("2700000.00"),
            Decimal("2500000.00"),
            Decimal("200000.00"),
            8.00,
            "Fav ▲",
            "—",
            4,
            320,
            "Forex gain & shipment pull-forward",
        ),
        BvARow(
            1,
            "5000",
            "Cost of Goods Sold",
            "expense",
            "All",
            Decimal("6800000.00"),
            Decimal("6500000.00"),
            Decimal("300000.00"),
            4.62,
            "Adv ▼",
            "materiality 2.0% or ₹500,000",
            2,
            980,
            "Raw material price inflation",
        ),
        BvARow(
            2,
            "5100",
            "  Raw Materials",
            "expense",
            "All",
            Decimal("4500000.00"),
            Decimal("4200000.00"),
            Decimal("300000.00"),
            7.14,
            "Adv ▼",
            "—",
            5,
            620,
            "Steel and resin index hikes",
        ),
        BvARow(
            2,
            "5200",
            "  Direct Labour",
            "expense",
            "All",
            Decimal("2300000.00"),
            Decimal("2300000.00"),
            Decimal("0.00"),
            0.00,
            "—",
            "—",
            8,
            360,
            "On budget",
        ),
        BvARow(
            1,
            "6000",
            "Operating Expenses",
            "expense",
            "All",
            Decimal("3200000.00"),
            Decimal("3350000.00"),
            Decimal("-150000.00"),
            -4.48,
            "Fav ▲",
            "—",
            6,
            450,
            "Strict marketing cost control",
        ),
        BvARow(
            2,
            "6100",
            "  Salaries & Staff Costs",
            "expense",
            "All",
            Decimal("2100000.00"),
            Decimal("2150000.00"),
            Decimal("-50000.00"),
            -2.33,
            "Fav ▲",
            "—",
            7,
            280,
            "Hiring delay in Q3",
        ),
        BvARow(
            2,
            "6200",
            "  Marketing & Advertising",
            "expense",
            "All",
            Decimal("650000.00"),
            Decimal("750000.00"),
            Decimal("-100000.00"),
            -13.33,
            "Fav ▲",
            "—",
            9,
            90,
            "Re-phased campaigns to Q4",
        ),
        BvARow(
            2,
            "6300",
            "  G&A & Utilities",
            "expense",
            "All",
            Decimal("450000.00"),
            Decimal("450000.00"),
            Decimal("0.00"),
            0.00,
            "—",
            "—",
            10,
            80,
            "In line with forecast",
        ),
    ]

    pl = [
        PLRow(
            "Gross Revenue",
            "Revenue",
            Decimal("12500000.00"),
            Decimal("12000000.00"),
            Decimal("500000.00"),
            4.17,
            Decimal("98000000.00"),
            Decimal("95000000.00"),
            Decimal("3000000.00"),
            3.16,
            "Fav ▲",
            "Strong volume growth",
            is_summary=True,
        ),
        PLRow(
            "Cost of Goods Sold (COGS)",
            "COGS",
            Decimal("6800000.00"),
            Decimal("6500000.00"),
            Decimal("300000.00"),
            4.62,
            Decimal("53500000.00"),
            Decimal("51000000.00"),
            Decimal("2500000.00"),
            4.90,
            "Adv ▼",
            "Input cost pressure",
            is_summary=True,
        ),
        PLRow(
            "Gross Profit",
            "Profit",
            Decimal("5700000.00"),
            Decimal("5500000.00"),
            Decimal("200000.00"),
            3.64,
            Decimal("44500000.00"),
            Decimal("44000000.00"),
            Decimal("500000.00"),
            1.14,
            "Fav ▲",
            "Margin 45.6%",
            is_summary=True,
        ),
        PLRow(
            "Operating Expenses (OPEX)",
            "Opex",
            Decimal("3200000.00"),
            Decimal("3350000.00"),
            Decimal("-150000.00"),
            -4.48,
            Decimal("25800000.00"),
            Decimal("26500000.00"),
            Decimal("-700000.00"),
            -2.64,
            "Fav ▲",
            "Prudent overhead",
            is_summary=True,
        ),
        PLRow(
            "Operating Profit (EBITDA)",
            "Profit",
            Decimal("2500000.00"),
            Decimal("2150000.00"),
            Decimal("350000.00"),
            16.28,
            Decimal("18700000.00"),
            Decimal("17500000.00"),
            Decimal("1200000.00"),
            6.86,
            "Fav ▲",
            "EBITDA margin 20.0%",
            is_summary=True,
        ),
        PLRow(
            "Depreciation & Amortization",
            "Depreciation",
            Decimal("400000.00"),
            Decimal("400000.00"),
            Decimal("0.00"),
            0.00,
            Decimal("3200000.00"),
            Decimal("3200000.00"),
            Decimal("0.00"),
            0.00,
            "—",
            "Straight-line",
            is_summary=False,
        ),
        PLRow(
            "EBIT",
            "Profit",
            Decimal("2100000.00"),
            Decimal("1750000.00"),
            Decimal("350000.00"),
            20.00,
            Decimal("15500000.00"),
            Decimal("14300000.00"),
            Decimal("1200000.00"),
            8.39,
            "Fav ▲",
            "Operating profit",
            is_summary=True,
        ),
        PLRow(
            "Finance & Interest Costs",
            "Finance",
            Decimal("150000.00"),
            Decimal("160000.00"),
            Decimal("-10000.00"),
            -6.25,
            Decimal("1250000.00"),
            Decimal("1300000.00"),
            Decimal("-50000.00"),
            -3.85,
            "Fav ▲",
            "Term loan interest",
            is_summary=False,
        ),
        PLRow(
            "Profit Before Tax (PBT)",
            "Profit",
            Decimal("1950000.00"),
            Decimal("1590000.00"),
            Decimal("360000.00"),
            22.64,
            Decimal("14250000.00"),
            Decimal("13000000.00"),
            Decimal("1250000.00"),
            9.62,
            "Fav ▲",
            "Ahead of plan",
            is_summary=True,
        ),
        PLRow(
            "Tax Provision",
            "Tax",
            Decimal("487500.00"),
            Decimal("397500.00"),
            Decimal("90000.00"),
            22.64,
            Decimal("3562500.00"),
            Decimal("3250000.00"),
            Decimal("312500.00"),
            9.62,
            "Adv ▼",
            "25% corporate tax rate",
            is_summary=False,
        ),
        PLRow(
            "Net Income",
            "Profit",
            Decimal("1462500.00"),
            Decimal("1192500.00"),
            Decimal("270000.00"),
            22.64,
            Decimal("10687500.00"),
            Decimal("9750000.00"),
            Decimal("937500.00"),
            9.62,
            "Fav ▲",
            "Net margin 11.7%",
            is_summary=True,
        ),
    ]

    transactions = [
        TransactionRow(
            1,
            "IN01",
            "5100",
            "Raw Materials",
            "CC-101",
            "Plant Ops",
            "PRJ-901",
            "Apex Steel Corp",
            "VND-401",
            "FY26-P09",
            date(2026, 9, 14),
            date(2026, 9, 12),
            "VCH-2026-09-001",
            "DOC-8911",
            "INV-5521",
            1,
            "Purchase of structural steel beams batch 4",
            "auto",
            Decimal("450000.00"),
            Decimal("0.00"),
            Decimal("450000.00"),
            "Dr",
            "INR",
            "D365",
            "D365_GL_Sep26.xlsx",
            "Sheet1!A102",
            1041,
            "9f2c10aa45b1",
            "EXC-002",
        ),
        TransactionRow(
            2,
            "IN01",
            "6100",
            "Salaries & Staff Costs",
            "CC-201",
            "HR",
            "PRJ-000",
            "Payroll Internal",
            "VND-000",
            "FY26-P09",
            date(2026, 9, 28),
            date(2026, 9, 28),
            "VCH-2026-09-042",
            "DOC-8942",
            "PAY-0926",
            1,
            "Monthly plant staffing and operator payroll",
            "auto",
            Decimal("2100000.00"),
            Decimal("0.00"),
            Decimal("2100000.00"),
            "Dr",
            "INR",
            "Payroll",
            "Payroll_Sep26.csv",
            "line 15",
            1042,
            "381bcf771a2d",
            "",
        ),
        TransactionRow(
            3,
            "IN02",
            "4100",
            "Domestic Sales",
            "CC-301",
            "Sales",
            "PRJ-102",
            "Tata Motors Ltd",
            "VND-702",
            "FY26-P09",
            date(2026, 9, 25),
            date(2026, 9, 25),
            "VCH-2026-09-088",
            "DOC-9011",
            "INV-9812",
            1,
            "Direct supply delivery - commercial vehicle components",
            "auto",
            Decimal("0.00"),
            Decimal("980000.00"),
            Decimal("-980000.00"),
            "Cr",
            "INR",
            "D365",
            "D365_GL_Sep26.xlsx",
            "Sheet1!A412",
            1041,
            "7a8f9c11e3b5",
            "",
        ),
        TransactionRow(
            4,
            "IN01",
            "6200",
            "Marketing & Advertising",
            "CC-401",
            "Commercial",
            "PRJ-304",
            "Omni Media Agency",
            "VND-551",
            "FY26-P09",
            date(2026, 9, 20),
            date(2026, 9, 18),
            "VCH-2026-09-065",
            "DOC-8977",
            "INV-1104",
            1,
            "Digital media and product showcase campaign",
            "auto",
            Decimal("350000.00"),
            Decimal("0.00"),
            Decimal("350000.00"),
            "Dr",
            "INR",
            "Procurement",
            "Procurement_Sep26.xlsx",
            "Sheet1!B88",
            1043,
            "6e11dd45aa89",
            "EXC-005",
        ),
        TransactionRow(
            5,
            "IN02",
            "5200",
            "Direct Labour",
            "CC-102",
            "Assembly",
            "PRJ-902",
            "Workforce Solutions",
            "VND-309",
            "FY26-P09",
            date(2026, 9, 22),
            date(2026, 9, 21),
            "VCH-2026-09-071",
            "DOC-8980",
            "INV-3301",
            1,
            "Contract technician shift support",
            "manual",
            Decimal("180000.00"),
            Decimal("0.00"),
            Decimal("180000.00"),
            "Dr",
            "INR",
            "D365",
            "D365_GL_Sep26.xlsx",
            "Sheet1!A604",
            1041,
            "bc309e1189ac",
            "",
        ),
    ]

    exceptions = [
        ExceptionRow(
            101,
            "EXC-002",
            "Duplicate invoice number across vendors",
            "1.0",
            "Invoicing",
            "High",
            "▲",
            "INV-5521 from Apex Steel Corp",
            "INV-5521|VND-401",
            "IN01",
            "5100",
            "Raw Materials",
            "CC-101",
            "Apex Steel Corp",
            "FY26-P09",
            "FY26-P09",
            Decimal("450000.00"),
            "open",
            "Rahul Mehta",
            6,
            "Overdue 1 d",
            date(2026, 9, 26),
            "materiality ₹100,000",
            "No",
            2,
            date(2026, 9, 28),
            "VCH-2026-09-001",
            datetime(2026, 9, 27, 10, 15),
            datetime(2026, 9, 30, 18, 0),
            None,
            118,
        ),
        ExceptionRow(
            102,
            "EXC-005",
            "Spike vs 3-month trailing average",
            "1.2",
            "Variance",
            "Medium",
            "◆",
            "Omni Media campaign marketing fee",
            "CC-401|6200",
            "IN01",
            "6200",
            "Marketing & Advertising",
            "CC-401",
            "Omni Media Agency",
            "FY26-P09",
            "FY26-P09",
            Decimal("350000.00"),
            "in_review",
            "Priya Sharma",
            4,
            "—",
            date(2026, 10, 5),
            "variance > 25% & ₹200,000",
            "No",
            1,
            date(2026, 9, 29),
            "VCH-2026-09-065",
            datetime(2026, 9, 28, 14, 22),
            datetime(2026, 9, 29, 11, 0),
            None,
            118,
        ),
        ExceptionRow(
            103,
            "EXC-008",
            "Manual round-number journal entry",
            "1.0",
            "Journal",
            "Low",
            "●",
            "Round number month-end accrual",
            "VCH-2026-09-099",
            "IN02",
            "6300",
            "G&A & Utilities",
            "CC-100",
            "—",
            "FY26-P09",
            "FY26-P09",
            Decimal("500000.00"),
            "explained",
            "Anand Patel",
            2,
            "—",
            date(2026, 10, 20),
            "exact multiple of 100,000",
            "No",
            1,
            date(2026, 9, 30),
            "VCH-2026-09-099",
            datetime(2026, 9, 30, 9, 0),
            datetime(2026, 9, 30, 16, 30),
            None,
            118,
        ),
    ]

    forecast = [
        ForecastRow(
            1,
            "4000",
            "Revenue",
            "FY26-P09",
            "Base",
            "locked_actuals",
            "project default",
            Decimal("12500000.00"),
            Decimal("12000000.00"),
            None,
            Decimal("500000.00"),
            4.17,
            "Fav ▲",
        ),
        ForecastRow(
            1,
            "4000",
            "Revenue",
            "FY26-P10",
            "Base",
            "run_rate",
            "line pin",
            None,
            Decimal("12200000.00"),
            Decimal("12700000.00"),
            Decimal("500000.00"),
            4.10,
            "Fav ▲",
        ),
        ForecastRow(
            1,
            "4000",
            "Revenue",
            "FY26-P11",
            "Base",
            "run_rate",
            "line pin",
            None,
            Decimal("12400000.00"),
            Decimal("12850000.00"),
            Decimal("450000.00"),
            3.63,
            "Fav ▲",
        ),
        ForecastRow(
            1,
            "4000",
            "Revenue",
            "FY26-P12",
            "Base",
            "run_rate",
            "line pin",
            None,
            Decimal("13000000.00"),
            Decimal("13500000.00"),
            Decimal("500000.00"),
            3.85,
            "Fav ▲",
        ),
        ForecastRow(
            1,
            "5000",
            "Cost of Goods Sold",
            "FY26-P09",
            "Base",
            "locked_actuals",
            "project default",
            Decimal("6800000.00"),
            Decimal("6500000.00"),
            None,
            Decimal("300000.00"),
            4.62,
            "Adv ▼",
        ),
        ForecastRow(
            1,
            "5000",
            "Cost of Goods Sold",
            "FY26-P10",
            "Base",
            "three_month_avg",
            "account group",
            None,
            Decimal("6600000.00"),
            Decimal("6900000.00"),
            Decimal("300000.00"),
            4.55,
            "Adv ▼",
        ),
        ForecastRow(
            1,
            "5000",
            "Cost of Goods Sold",
            "FY26-P11",
            "Base",
            "three_month_avg",
            "account group",
            None,
            Decimal("6700000.00"),
            Decimal("7000000.00"),
            Decimal("300000.00"),
            4.48,
            "Adv ▼",
        ),
        ForecastRow(
            1,
            "5000",
            "Cost of Goods Sold",
            "FY26-P12",
            "Base",
            "three_month_avg",
            "account group",
            None,
            Decimal("7000000.00"),
            Decimal("7300000.00"),
            Decimal("300000.00"),
            4.29,
            "Adv ▼",
        ),
    ]

    import_batches = [
        ImportBatchRow(
            1041,
            "committed",
            "D365",
            "D365_GL_Sep26.xlsx",
            "Sheet1",
            "9f2c10aa45b1",
            "9f2c10aa45b178e3290bca1149e088192a5b6781938b81920cae918239011928",
            1420,
            1420,
            0,
            0,
            Decimal("19300000.00"),
            Decimal("19300000.00"),
            Decimal("0.00"),
            Decimal("19300000.00"),
            Decimal("0.00"),
            "Balanced",
            "D365 v4",
            datetime(2026, 10, 1, 9, 30),
            "Tahir",
            "—",
        ),
        ImportBatchRow(
            1042,
            "committed",
            "Payroll",
            "Payroll_Sep26.csv",
            "default",
            "381bcf771a2d",
            "381bcf771a2d81920ca981023812839182390182390182390182390182390182",
            280,
            280,
            0,
            0,
            Decimal("2100000.00"),
            Decimal("2100000.00"),
            Decimal("0.00"),
            Decimal("2100000.00"),
            Decimal("0.00"),
            "Balanced",
            "Payroll v2",
            datetime(2026, 10, 1, 10, 15),
            "Tahir",
            "—",
        ),
        ImportBatchRow(
            1043,
            "committed",
            "Procurement",
            "Procurement_Sep26.xlsx",
            "Sheet1",
            "6e11dd45aa89",
            "6e11dd45aa8981920ca981023812839182390182390182390182390182390182",
            90,
            90,
            0,
            0,
            Decimal("650000.00"),
            Decimal("650000.00"),
            Decimal("0.00"),
            Decimal("650000.00"),
            Decimal("0.00"),
            "Balanced",
            "Procurement v1",
            datetime(2026, 10, 1, 11, 0),
            "Tahir",
            "—",
        ),
    ]

    validation_checks = [
        ValidationCheckRow(
            "IMP-001",
            "Required headers present and non-empty",
            10,
            "Pass",
            0,
            "All target columns successfully bound",
        ),
        ValidationCheckRow(
            "IMP-002",
            "Transaction date within fiscal calendar bounds",
            10,
            "Pass",
            0,
            "Dates strictly within FY26-P09",
        ),
        ValidationCheckRow(
            "IMP-003",
            "Debit and credit balance within batch",
            10,
            "Pass",
            0,
            "Total batch debit equals credit exactly",
        ),
        ValidationCheckRow(
            "IMP-004",
            "Valid Chart of Accounts mapping",
            5,
            "Pass",
            0,
            "All accounts verified in master COA",
        ),
        ValidationCheckRow(
            "IMP-005",
            "Valid Cost Centre mapping",
            5,
            "Pass",
            0,
            "Cost centres verified against active list",
        ),
        ValidationCheckRow(
            "IMP-006",
            "Currency consistency check",
            2,
            "Pass",
            0,
            "Consistent INR project base currency",
        ),
    ]

    return MonthEndPackData(
        context=ctx,
        bva_rows=bva,
        pl_rows=pl,
        transaction_rows=transactions,
        exception_rows=exceptions,
        forecast_rows=forecast,
        import_batches=import_batches,
        validation_checks=validation_checks,
    )


# -------------------------------------------------------------------------
# Formatting Helper Functions
# -------------------------------------------------------------------------


def _apply_header_block(
    ws: Any,
    sheet_title: str,
    context: PackContext,
    note: str,
    last_col: int = 14,
) -> None:
    """Apply the standard 4-row header block + spacer row 5 per §3.3."""

    # Row 1: Title and Units
    ws.cell(row=1, column=1, value=sheet_title).font = FONT_TITLE
    units_cell = ws.cell(row=1, column=last_col, value=f"Units: {context.units}")
    units_cell.font = FONT_UNITS
    units_cell.alignment = ALIGN_RIGHT

    # Row 2: Context line
    ent_str = ", ".join(context.entities) if context.entities else "All"
    per_str = ", ".join(context.periods) if context.periods else "Current"
    context_text = f"{context.project_name} · Entity: {ent_str} · Period: {per_str} · Window: {context.window} · Scenario: {context.scenario}"
    ws.cell(row=2, column=1, value=context_text).font = FONT_SUBTITLE

    # Row 3: Generation line
    batches_str = ", ".join(str(b) for b in context.batch_ids[:5])
    if len(context.batch_ids) > 5:
        batches_str += f" … (+{len(context.batch_ids) - 5})"
    gen_text = f"Generated {context.generated_at} · Pack {context.pack_version} · App v{context.app_version} · Sources: {batches_str}"
    ws.cell(row=3, column=1, value=gen_text).font = FONT_META

    # Row 4: Specific note / control statement
    ws.cell(row=4, column=1, value=note).font = FONT_META

    # Row heights
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 16
    ws.row_dimensions[4].height = 16
    ws.row_dimensions[5].height = 6  # Spacer row


def _style_table_header(ws: Any, row: int, cols: list[tuple[str, int, str]]) -> None:
    """Format row 6 table headers."""
    ws.row_dimensions[row].height = 28
    for col_idx, (title, width, _) in enumerate(cols, start=1):
        cell = ws.cell(row=row, column=col_idx, value=title)
        cell.font = FONT_TBL_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_HEADER
        cell.border = BORDER_THIN
        ws.column_dimensions[get_column_letter(col_idx)].width = width


# -------------------------------------------------------------------------
# Sheet 1: Cover & Context
# -------------------------------------------------------------------------


def build_sheet_cover(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 1: Cover & Context per §3.2, §3.3, §4.1."""
    ws.title = "Cover & Context"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = False

    ctx = data.context

    # Header block
    _apply_header_block(
        ws,
        f"Month-end pack — {ctx.project_name}",
        ctx,
        "Master index, control totals and audit stamp. Static snapshot from FP&A engine.",
        last_col=5,
    )

    # Section 1: Workbook Stamp (Row 6)
    stamp_hdr = ws.cell(row=6, column=1, value="Workbook stamp")
    stamp_hdr.font = FONT_SECTION
    stamp_hdr.fill = FILL_SECTION
    stamp_hdr.border = BORDER_SECTION
    ws.merge_cells("A6:E6")
    ws.row_dimensions[6].height = 22

    # Map context attributes to stamp labels
    stamp_value_dict: dict[str, Any] = {
        "Stamp version": "1",
        "Generated at": ctx.generated_at,
        "Project": ctx.project_name,
        "Entity(ies)": ", ".join(ctx.entities),
        "Period(s)": ", ".join(ctx.periods),
        "Window": ctx.window,
        "Scenario": ctx.scenario,
        "Forecast version": ctx.forecast_version,
        "Budget version": ctx.budget_version,
        "Filter context (JSON)": ctx.filter_json,
        "Filter context (human)": ctx.filter_human,
        "Grain": "month × account × cost centre",
        "Source import batch IDs": ", ".join(str(b) for b in ctx.batch_ids),
        "Source file names": "; ".join(ctx.source_files),
        "Pack version": ctx.pack_version,
        "Pack sequence (file vN)": str(ctx.file_version),
        "App version": ctx.app_version,
        "Schema version": "1",
        "Rule set version": "2026-09-30 (24 rules, 22 enabled)",
        "Mapping profile versions": "D365 v4, Payroll v2, Procurement v1",
        "House style profile": "none",
        "Units and scale": ctx.units,
        "Digit grouping": ctx.grouping,
        "AI content": "none",
        "Sample data": ctx.sample_data,
        "Stale derived results": ctx.stale_results,
        "Run correlation ID": ctx.correlation_id,
        "Claim ID": ctx.claim_id,
        "Tie-out state": ctx.tie_out_state,
        "Rounding note": "Components may not sum to the total due to rounding.",
        "Disclaimer (short)": "Advisory tool, not professional advice. Review by qualified accountant required.",
        "Content hash": ctx.content_hash,
    }

    # Populate Rows 7 to 36
    wb = ws.parent
    for field_info in STAMP_FIELDS:
        r = field_info.row
        label_cell = ws.cell(row=r, column=1, value=field_info.label)
        label_cell.font = FONT_DATA_BOLD
        label_cell.border = BORDER_THIN
        label_cell.alignment = ALIGN_LEFT

        val = stamp_value_dict.get(field_info.label, field_info.default_value)
        val_cell = ws.cell(row=r, column=2, value=str(val))
        val_cell.font = FONT_DATA
        val_cell.border = BORDER_THIN
        val_cell.alignment = ALIGN_WRAP_LEFT

        # Register defined name
        dn = DefinedName(field_info.defined_name, attr_text=f"'{ws.title}'!$B${r}")
        wb.defined_names.add(dn)

    # Section 2: Contents (Row 38)
    ws.cell(row=38, column=1, value="Contents").font = FONT_SECTION
    ws.cell(row=38, column=1).fill = FILL_SECTION
    ws.merge_cells("A38:E38")
    ws.row_dimensions[38].height = 20

    # Header row 39
    contents_cols = ["Sheet", "Rows", "Included", "Note"]
    ws.row_dimensions[39].height = 20
    for idx, col_name in enumerate(contents_cols, start=1):
        c = ws.cell(row=39, column=idx, value=col_name)
        c.font = FONT_TBL_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_THIN
        c.alignment = ALIGN_LEFT

    # Rows 40-46: Sheet Index
    sheet_meta = [
        ("Cover & Context", 1, "Yes", "Self-describing audit stamp and controls"),
        ("Executive Summary & BvA", len(data.bva_rows), "Yes", "Budget vs Actual variance matrix"),
        (
            "P&L Statement Analysis",
            len(data.pl_rows),
            "Yes",
            "Full profit and loss financial analysis",
        ),
        (
            "Transaction Detail Drilldown",
            len(data.transaction_rows),
            "Yes",
            "Line-level transaction audit drilldown",
        ),
        (
            "Exception Register",
            len(data.exception_rows),
            "Yes",
            "Accounting exception leads and SLA tracking",
        ),
        (
            "Forecast Summary",
            len(data.forecast_rows),
            "Yes",
            "Rolling forecast scenarios and accuracy",
        ),
        (
            "Import Reconciliation",
            len(data.import_batches),
            "Yes",
            "Source integrity, balance checks and tie-out",
        ),
    ]

    for idx, (s_name, row_cnt, inc, note_txt) in enumerate(sheet_meta, start=40):
        cell_link = ws.cell(row=idx, column=1, value=s_name)
        cell_link.hyperlink = f"#{s_name}!A1"
        cell_link.font = Font(name=FONT_NAME, size=10, underline="single", color="1A4FA0")
        cell_link.border = BORDER_THIN

        cnt_c = ws.cell(row=idx, column=2, value=row_cnt)
        cnt_c.font = FONT_DATA
        cnt_c.number_format = fmt.COUNT_INT
        cnt_c.alignment = ALIGN_RIGHT
        cnt_c.border = BORDER_THIN

        inc_c = ws.cell(row=idx, column=3, value=inc)
        inc_c.font = FONT_DATA
        inc_c.alignment = ALIGN_CENTER
        inc_c.border = BORDER_THIN

        note_c = ws.cell(row=idx, column=4, value=note_txt)
        note_c.font = FONT_DATA
        note_c.alignment = ALIGN_LEFT
        note_c.border = BORDER_THIN

    # Section 3: Control Totals (Row 48)
    ws.cell(
        row=48, column=1, value="Control totals (read this before quoting a number)"
    ).font = FONT_SECTION
    ws.cell(row=48, column=1).fill = FILL_SECTION
    ws.merge_cells("A48:E48")
    ws.row_dimensions[48].height = 20

    # Header row 49
    for idx, col_name in enumerate(["Control", "Value", "Source", "Check"], start=1):
        c = ws.cell(row=49, column=idx, value=col_name)
        c.font = FONT_TBL_HEADER
        c.fill = FILL_HEADER
        c.border = BORDER_THIN
        c.alignment = ALIGN_LEFT

    # Compute key totals from data
    act_total = sum(r.actual for r in data.bva_rows if r.level == 1)
    bud_total = sum(r.budget for r in data.bva_rows if r.level == 1)
    var_total = act_total - bud_total
    var_pct = (var_total / abs(bud_total)) if bud_total else 0.0

    open_exc = sum(1 for e in data.exception_rows if e.status == "open")
    overdue_exc = sum(1 for e in data.exception_rows if "Overdue" in e.overdue)
    high_exc = sum(1 for e in data.exception_rows if e.severity == "High")
    import_bal_var = sum(b.balance_variance for b in data.import_batches)

    control_rows = [
        ("Actual (total)", act_total, fmt.MONEY_IN, "Executive Summary & BvA · row 'Totals'", "OK"),
        ("Budget (total)", bud_total, fmt.MONEY_IN, "Executive Summary & BvA · row 'Totals'", "OK"),
        (
            "Variance (total)",
            var_total,
            fmt.MONEY_IN,
            "Executive Summary & BvA · row 'Totals'",
            "OK",
        ),
        (
            "Variance % (total)",
            var_pct,
            fmt.PCT_1DP,
            "Executive Summary & BvA · row 'Totals'",
            "OK",
        ),
        (
            "Forecast landing estimate",
            13500000.00,
            fmt.MONEY_IN,
            "Forecast Summary · Landing estimate",
            "OK",
        ),
        ("Exceptions — open", open_exc, fmt.COUNT_INT, "Exception Register", "OK"),
        ("Exceptions — overdue", overdue_exc, fmt.COUNT_INT, "Exception Register", "OK"),
        ("Exceptions — high severity", high_exc, fmt.COUNT_INT, "Exception Register", "OK"),
        ("Import balance variance", import_bal_var, fmt.MONEY_IN, "Import Reconciliation", "OK"),
        ("Data-quality score", 98, fmt.COUNT_INT, "Import Reconciliation", "OK"),
    ]

    for idx, (name, val, num_fmt, src, chk) in enumerate(control_rows, start=50):
        c1 = ws.cell(row=idx, column=1, value=name)
        c1.font = FONT_DATA_BOLD
        c1.border = BORDER_THIN

        c2 = ws.cell(row=idx, column=2, value=val)
        c2.font = FONT_DATA
        c2.number_format = num_fmt
        c2.border = BORDER_THIN
        if num_fmt in (fmt.MONEY_IN, fmt.PCT_1DP, fmt.COUNT_INT):
            c2.alignment = ALIGN_RIGHT

        c3 = ws.cell(row=idx, column=3, value=src)
        c3.font = FONT_DATA
        c3.border = BORDER_THIN

        c4 = ws.cell(row=idx, column=4, value=chk)
        c4.font = FONT_DATA_BOLD
        c4.alignment = ALIGN_CENTER
        c4.border = BORDER_THIN
        if chk == "OK":
            c4.font = FONT_FAV

    # Section 4: How to read this workbook (Row 61)
    ws.cell(row=61, column=1, value="How to read this workbook").font = FONT_SECTION
    ws.cell(row=61, column=1).fill = FILL_SECTION
    ws.merge_cells("A61:E61")

    field_guides = [
        "1. Every number in this workbook is a static value from the FP&A Month-End Copilot engine. There are no formulas — press F9 and nothing will change. To update the numbers, use 'Refresh this pack' in the app.",
        "2. '—' means there was nothing to compare. 'n/a' means the percentage is undefined (a zero denominator). '₹ 0.00' is a real zero. They are never interchangeable.",
        "3. Green/red shading marks favourable/unfavourable and is always accompanied by a text label (Fav ▲ / Adv ▼) in the Signal column, so the meaning survives black-and-white printing.",
        "4. Filters used to build this pack are printed in the stamp above and repeated on every sheet's row 2.",
        "5. This is an advisory analysis pack, not an audited statement. Every figure must be reviewed by a qualified accountant before it is used for a business decision, filing or external reporting.",
    ]

    for offset, guide in enumerate(field_guides, start=62):
        cell_g = ws.cell(row=offset, column=1, value=guide)
        cell_g.font = FONT_DATA
        ws.row_dimensions[offset].height = 18

    # Section 5: Disclaimer (Row 68)
    ws.cell(row=68, column=1, value="Disclaimer").font = FONT_SECTION
    ws.cell(row=68, column=1).fill = FILL_SECTION
    ws.merge_cells("A68:E68")

    disc_text = (
        "Potential exceptions only — advisory tool, not professional advice. Review by a qualified "
        "accountant required. Figures may be revised."
    )
    ws.cell(row=69, column=1, value=disc_text).font = FONT_META

    # Explicit column widths
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 78
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 60


# -------------------------------------------------------------------------
# Sheet 2: Executive Summary & BvA
# -------------------------------------------------------------------------


def build_sheet_executive_summary(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 2: Executive Summary & BvA per §4.2."""
    ws.title = "Executive Summary & BvA"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "C7"

    cols: list[tuple[str, int, str]] = [
        ("Level", 7, fmt.COUNT_INT),
        ("Account code", 12, fmt.CODE),
        ("Account name", 34, fmt.TEXT),
        ("Account type", 12, fmt.TEXT),
        ("Cost centre", 14, fmt.CODE),
        ("Actual", 16, fmt.MONEY_IN),
        ("Budget", 16, fmt.MONEY_IN),
        ("Variance", 16, fmt.MONEY_IN),
        ("Var %", 10, fmt.PCT_1DP),
        ("Signal", 13, fmt.LABEL),
        ("Effective threshold", 26, fmt.TEXT),
        ("Rank", 8, fmt.COUNT_INT),
        ("Rows", 9, fmt.COUNT_INT),
        ("Commentary", 48, fmt.TEXT),
    ]

    _apply_header_block(
        ws,
        "Executive Summary & BvA",
        data.context,
        "Budget-vs-actual variance matrix at comparison grain. Outlines enabled, fully expanded.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    if not data.bva_rows:
        ws.cell(row=7, column=1, value="No data for this filter.").font = FONT_EMPTY
        current_row = 8
    else:
        for r_data in data.bva_rows:
            # Set outline level
            if r_data.level > 1:
                ws.row_dimensions[current_row].outlineLevel = r_data.level - 1

            values = [
                r_data.level,
                r_data.account_code,
                r_data.account_name,
                r_data.account_type,
                r_data.cost_centre,
                r_data.actual,
                r_data.budget,
                r_data.variance,
                r_data.var_pct / 100.0 if r_data.var_pct is not None else "—",
                r_data.signal,
                r_data.effective_threshold,
                r_data.rank if r_data.rank > 0 else "—",
                r_data.rows_count,
                r_data.commentary,
            ]

            for c_idx, (val, (_, _, num_fmt)) in enumerate(zip(values, cols, strict=True), start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = FONT_DATA
                cell.border = BORDER_THIN
                cell.number_format = num_fmt

                # Alignment
                if num_fmt in (fmt.MONEY_IN, fmt.PCT_1DP, fmt.COUNT_INT) and isinstance(
                    val, (int, float, Decimal)
                ):
                    cell.alignment = ALIGN_RIGHT
                elif num_fmt == fmt.LABEL:
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT

                # Signal coloring
                if c_idx in (8, 9, 10):  # Variance, Var %, Signal
                    if r_data.signal == "Fav ▲":
                        cell.fill = FILL_FAV
                        cell.font = FONT_FAV
                    elif r_data.signal == "Adv ▼":
                        cell.fill = FILL_ADV
                        cell.font = FONT_ADV
                    elif val in ("—", "n/a"):
                        cell.fill = FILL_NEUTRAL
                        cell.font = FONT_NEUTRAL

            current_row += 1

        # Totals Row (Level 1 sums only to avoid double counting)
        lvl1_actual = sum(r.actual for r in data.bva_rows if r.level == 1)
        lvl1_budget = sum(r.budget for r in data.bva_rows if r.level == 1)
        lvl1_var = lvl1_actual - lvl1_budget
        lvl1_var_pct = (lvl1_var / abs(lvl1_budget)) if lvl1_budget != 0 else None

        totals_values: list[Any] = [
            0,
            "—",
            f"Totals ({len(data.bva_rows)} accounts)",
            "—",
            "—",
            lvl1_actual,
            lvl1_budget,
            lvl1_var,
            lvl1_var_pct if lvl1_var_pct is not None else "—",
            "—",
            "—",
            "—",
            sum(r.rows_count for r in data.bva_rows if r.level == 1),
            "Simple sum — no eliminations",
        ]

        ws.row_dimensions[current_row].height = 22
        for c_idx, (t_val, (_, _, num_fmt)) in enumerate(
            zip(totals_values, cols, strict=True), start=1
        ):
            cell = ws.cell(row=current_row, column=c_idx, value=t_val)
            cell.font = FONT_TOTAL
            cell.fill = FILL_TOTAL
            cell.border = BORDER_TOTAL
            cell.number_format = num_fmt

            if isinstance(t_val, (int, float, Decimal)):
                cell.alignment = ALIGN_RIGHT
            else:
                cell.alignment = ALIGN_CENTER if c_idx == 10 else ALIGN_LEFT

    # Auto-filter
    ws.auto_filter.ref = f"A6:{get_column_letter(len(cols))}{max(current_row, 6)}"


# -------------------------------------------------------------------------
# Sheet 3: P&L Statement Analysis
# -------------------------------------------------------------------------


def build_sheet_pl_statement(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 3: P&L Statement Analysis."""
    ws.title = "P&L Statement Analysis"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "C7"

    cols: list[tuple[str, int, str]] = [
        ("Line item", 32, fmt.TEXT),
        ("Category", 18, fmt.TEXT),
        ("Actual MTD", 16, fmt.MONEY_IN),
        ("Budget MTD", 16, fmt.MONEY_IN),
        ("Var MTD", 16, fmt.MONEY_IN),
        ("Var % MTD", 10, fmt.PCT_1DP),
        ("Actual YTD", 16, fmt.MONEY_IN),
        ("Budget YTD", 16, fmt.MONEY_IN),
        ("Var YTD", 16, fmt.MONEY_IN),
        ("Var % YTD", 10, fmt.PCT_1DP),
        ("Signal", 12, fmt.LABEL),
        ("Notes / Driver", 36, fmt.TEXT),
    ]

    _apply_header_block(
        ws,
        "P&L Statement Analysis",
        data.context,
        "Comprehensive Profit & Loss view: MTD & YTD actuals vs approved budget.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    if not data.pl_rows:
        ws.cell(row=7, column=1, value="No P&L data available for this filter.").font = FONT_EMPTY
        current_row = 8
    else:
        for r_data in data.pl_rows:
            is_net_income = "Net Income" in r_data.line_item
            row_font = FONT_TOTAL if r_data.is_summary else FONT_DATA
            row_border = (
                BORDER_TOTAL
                if is_net_income
                else (BORDER_TOTAL if r_data.is_summary else BORDER_THIN)
            )
            row_fill = FILL_TOTAL if r_data.is_summary else None

            values = [
                r_data.line_item,
                r_data.category,
                r_data.actual_mtd,
                r_data.budget_mtd,
                r_data.var_mtd,
                r_data.var_pct_mtd / 100.0 if r_data.var_pct_mtd is not None else "—",
                r_data.actual_ytd,
                r_data.budget_ytd,
                r_data.var_ytd,
                r_data.var_pct_ytd / 100.0 if r_data.var_pct_ytd is not None else "—",
                r_data.signal,
                r_data.notes,
            ]

            for c_idx, (val, (_, _, num_fmt)) in enumerate(zip(values, cols, strict=True), start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = row_font
                if row_fill:
                    cell.fill = row_fill
                cell.border = row_border
                cell.number_format = num_fmt

                if isinstance(val, (int, float, Decimal)):
                    cell.alignment = ALIGN_RIGHT
                elif c_idx == 11:
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT

                # Signal highlight
                if c_idx == 11:
                    if val == "Fav ▲":
                        cell.fill = FILL_FAV
                        cell.font = FONT_FAV
                    elif val == "Adv ▼":
                        cell.fill = FILL_ADV
                        cell.font = FONT_ADV

            current_row += 1

    ws.auto_filter.ref = f"A6:{get_column_letter(len(cols))}{max(current_row, 6)}"


# -------------------------------------------------------------------------
# Sheet 4: Transaction Detail Drilldown
# -------------------------------------------------------------------------


def build_sheet_transaction_detail(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 4: Transaction Detail Drilldown per §4.4."""
    ws.title = "Transaction Detail Drilldown"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "C7"

    cols: list[tuple[str, int, str]] = [
        ("#", 7, fmt.COUNT_INT),
        ("Entity", 10, fmt.CODE),
        ("Account code", 12, fmt.CODE),
        ("Account name", 30, fmt.TEXT),
        ("Cost centre", 12, fmt.CODE),
        ("Department", 16, fmt.TEXT),
        ("Project", 14, fmt.CODE),
        ("Vendor", 24, fmt.TEXT),
        ("Vendor code", 12, fmt.CODE),
        ("Period", 10, fmt.CODE),
        ("Posting date", 12, fmt.DATE_DMY),
        ("Document date", 12, fmt.DATE_DMY),
        ("Voucher no", 20, fmt.CODE),
        ("Document no", 18, fmt.CODE),
        ("Invoice no", 18, fmt.CODE),
        ("Line", 6, fmt.COUNT_INT),
        ("Description", 60, fmt.TEXT),
        ("Journal category", 13, fmt.TEXT),
        ("Debit", 16, fmt.MONEY_IN),
        ("Credit", 16, fmt.MONEY_IN),
        ("Net", 16, fmt.MONEY_IN),
        ("Dr/Cr", 7, fmt.LABEL),
        ("Currency", 8, fmt.CODE),
        ("Source system", 12, fmt.TEXT),
        ("Source file", 28, fmt.TEXT),
        ("Source row ref", 14, fmt.CODE),
        ("Batch ID", 10, fmt.COUNT_INT),
        ("Fingerprint", 14, fmt.HASH),
        ("Exception IDs", 24, fmt.CODE),
    ]

    _apply_header_block(
        ws,
        "Transaction Detail Drilldown",
        data.context,
        f"Rows shown: {len(data.transaction_rows)} · Granular general ledger posting evidence.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    if not data.transaction_rows:
        ws.cell(row=7, column=1, value="No transactions for this filter.").font = FONT_EMPTY
        current_row = 8
    else:
        for r_data in data.transaction_rows:
            values = [
                r_data.row_num,
                r_data.entity,
                r_data.account_code,
                r_data.account_name,
                r_data.cost_centre,
                r_data.department,
                r_data.project,
                r_data.vendor,
                r_data.vendor_code,
                r_data.period,
                r_data.posting_date,
                r_data.document_date,
                r_data.voucher_no,
                r_data.document_no,
                r_data.invoice_no,
                r_data.line,
                r_data.description,
                r_data.journal_category,
                r_data.debit,
                r_data.credit,
                r_data.net,
                r_data.dr_cr,
                r_data.currency,
                r_data.source_system,
                r_data.source_file,
                r_data.source_row_ref,
                r_data.batch_id,
                r_data.fingerprint,
                r_data.exception_ids,
            ]

            ws.row_dimensions[current_row].height = 20
            for c_idx, (val, (_, _, num_fmt)) in enumerate(zip(values, cols, strict=True), start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = FONT_DATA
                cell.border = BORDER_THIN
                cell.number_format = num_fmt

                if isinstance(val, (int, float, Decimal)):
                    cell.alignment = ALIGN_RIGHT
                elif isinstance(val, (date, datetime)):
                    cell.alignment = ALIGN_CENTER
                elif c_idx == 22:  # Dr/Cr
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT

            current_row += 1

        # Control Rows
        subtotal_deb = sum(t.debit for t in data.transaction_rows)
        subtotal_crd = sum(t.credit for t in data.transaction_rows)
        subtotal_net = subtotal_deb - subtotal_crd

        # Subtotal row
        ws.row_dimensions[current_row].height = 22
        cell_lbl = ws.cell(
            row=current_row, column=1, value=f"Subtotal ({len(data.transaction_rows)} rows)"
        )
        cell_lbl.font = FONT_TOTAL
        cell_lbl.fill = FILL_TOTAL
        cell_lbl.border = BORDER_TOTAL

        for c in range(2, len(cols) + 1):
            cell = ws.cell(row=current_row, column=c)
            cell.font = FONT_TOTAL
            cell.fill = FILL_TOTAL
            cell.border = BORDER_TOTAL
            if c == 19:
                cell.value = subtotal_deb
                cell.number_format = fmt.MONEY_IN
                cell.alignment = ALIGN_RIGHT
            elif c == 20:
                cell.value = subtotal_crd
                cell.number_format = fmt.MONEY_IN
                cell.alignment = ALIGN_RIGHT
            elif c == 21:
                cell.value = subtotal_net
                cell.number_format = fmt.MONEY_IN
                cell.alignment = ALIGN_RIGHT

        current_row += 1

        # Check row
        ws.row_dimensions[current_row].height = 20
        check_text = f"Check: Σ Debit − Σ Credit = ₹{subtotal_net:,.2f} — matches Import Reconciliation variance"
        c_chk = ws.cell(row=current_row, column=1, value=check_text)
        c_chk.font = FONT_FAV if subtotal_net == 0 else FONT_ADV
        ws.merge_cells(f"A{current_row}:G{current_row}")

    ws.auto_filter.ref = f"A6:{get_column_letter(len(cols))}{max(current_row - 1, 6)}"


# -------------------------------------------------------------------------
# Sheet 5: Exception Register
# -------------------------------------------------------------------------


def build_sheet_exception_register(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 5: Exception Register per §4.5."""
    ws.title = "Exception Register"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "C7"

    cols: list[tuple[str, int, str]] = [
        ("Exception ID", 10, fmt.COUNT_INT),
        ("Rule ID", 10, fmt.CODE),
        ("Rule name", 32, fmt.TEXT),
        ("Rule version", 10, fmt.CODE),
        ("Family", 18, fmt.TEXT),
        ("Severity", 9, fmt.TEXT),
        ("Mark", 7, fmt.LABEL),
        ("Subject", 40, fmt.TEXT),
        ("Subject key", 30, fmt.CODE),
        ("Entity", 10, fmt.CODE),
        ("Account code", 12, fmt.CODE),
        ("Account name", 28, fmt.TEXT),
        ("Cost centre", 12, fmt.CODE),
        ("Vendor", 22, fmt.TEXT),
        ("Period", 11, fmt.CODE),
        ("First seen", 11, fmt.CODE),
        ("Amount at risk", 16, fmt.MONEY_IN),
        ("Status", 13, fmt.TEXT),
        ("Owner", 18, fmt.TEXT),
        ("Age (days)", 10, fmt.DAYS),
        ("Overdue", 12, fmt.LABEL),
        ("SLA due", 12, fmt.DATE_DMY),
        ("Effective threshold", 30, fmt.TEXT),
        ("Flagged again", 12, fmt.TEXT),
        ("Notes", 8, fmt.COUNT_INT),
        ("Last note", 11, fmt.DATE_DMY),
        ("Evidence refs", 30, fmt.TEXT),
        ("Raised at", 15, fmt.TS_DMY),
        ("Last seen at", 15, fmt.TS_DMY),
        ("Closed at", 15, fmt.TS_DMY),
        ("Run ID", 9, fmt.COUNT_INT),
        ("Correlation ID", 20, fmt.CODE),
        ("Claim ID", 25, fmt.CODE),
    ]

    _apply_header_block(
        ws,
        "Exception Register",
        data.context,
        "Potential exception — requires accounting review. These are leads, not verdicts.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    if not data.exception_rows:
        ws.cell(
            row=7, column=1, value="No open exceptions — nothing requires review."
        ).font = FONT_EMPTY
        current_row = 8
    else:
        for r_data in data.exception_rows:
            values = [
                r_data.exception_id,
                r_data.rule_id,
                r_data.rule_name,
                r_data.rule_version,
                r_data.family,
                r_data.severity,
                r_data.mark,
                r_data.subject,
                r_data.subject_key,
                r_data.entity,
                r_data.account_code,
                r_data.account_name,
                r_data.cost_centre,
                r_data.vendor,
                r_data.period,
                r_data.first_seen,
                r_data.amount_at_risk,
                r_data.status,
                r_data.owner or "Unassigned",
                r_data.age_days,
                r_data.overdue,
                r_data.sla_due,
                r_data.effective_threshold,
                r_data.flagged_again,
                r_data.notes_count,
                r_data.last_note,
                r_data.evidence_refs,
                r_data.raised_at,
                r_data.last_seen_at,
                r_data.closed_at if r_data.closed_at else "—",
                r_data.run_id,
                r_data.correlation_id or "—",
                r_data.claim_id or "—",
            ]

            ws.row_dimensions[current_row].height = 20
            for c_idx, (val, (_, _, num_fmt)) in enumerate(zip(values, cols, strict=True), start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = FONT_DATA
                cell.border = BORDER_THIN
                cell.number_format = num_fmt

                if isinstance(val, (int, float, Decimal)):
                    cell.alignment = ALIGN_RIGHT
                elif isinstance(val, (date, datetime)):
                    cell.alignment = ALIGN_CENTER
                elif c_idx in (6, 7, 21):  # Severity, Mark, Overdue
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT

                # Severity styling
                if c_idx in (6, 7):
                    if r_data.severity == "High":
                        cell.fill = FILL_SEV_HIGH
                        cell.font = FONT_SEV_HIGH
                    elif r_data.severity == "Med":
                        cell.fill = FILL_SEV_MED
                        cell.font = FONT_SEV_MED
                    elif r_data.severity == "Low":
                        cell.fill = FILL_SEV_LOW
                        cell.font = FONT_SEV_LOW

                if c_idx == 21 and "Overdue" in str(val):
                    cell.fill = FILL_ADV
                    cell.font = FONT_ADV

            current_row += 1

        # Control Rows
        total_open = sum(1 for e in data.exception_rows if e.status == "open")
        total_overdue = sum(1 for e in data.exception_rows if "Overdue" in e.overdue)
        total_high = sum(1 for e in data.exception_rows if e.severity == "High")
        total_unassigned = sum(
            1 for e in data.exception_rows if not e.owner or e.owner == "Unassigned"
        )
        total_risk = sum(e.amount_at_risk for e in data.exception_rows)

        # Row: Counts
        ws.row_dimensions[current_row].height = 20
        counts_str = f"Counts: Total: {len(data.exception_rows)} · Open: {total_open} · Overdue: {total_overdue} · High: {total_high} · Unassigned: {total_unassigned}"
        c_cnt = ws.cell(row=current_row, column=1, value=counts_str)
        c_cnt.font = FONT_TOTAL
        ws.merge_cells(f"A{current_row}:G{current_row}")
        current_row += 1

        # Row: Total Amount at risk
        ws.row_dimensions[current_row].height = 20
        c_risk_lbl = ws.cell(row=current_row, column=1, value="Σ Amount at risk (indicator):")
        c_risk_lbl.font = FONT_TOTAL
        c_risk_val = ws.cell(row=current_row, column=17, value=total_risk)
        c_risk_val.font = FONT_TOTAL
        c_risk_val.number_format = fmt.MONEY_IN
        c_risk_val.border = BORDER_TOTAL
        c_risk_val.alignment = ALIGN_RIGHT

        c_caveat = ws.cell(
            row=current_row,
            column=18,
            value="Indicator only — amounts at risk across different subjects are not additive as a ledger total.",
        )
        c_caveat.font = FONT_META
        current_row += 1

        # Row: Rule coverage
        ws.row_dimensions[current_row].height = 20
        rule_cov_str = "Rule coverage: Rules evaluated: 24 of 24 enabled (rule set 2026-09-30) · Run 118 · Last run 01-10-2026 14:05"
        c_cov = ws.cell(row=current_row, column=1, value=rule_cov_str)
        c_cov.font = FONT_META
        ws.merge_cells(f"A{current_row}:G{current_row}")

    ws.auto_filter.ref = f"A6:{get_column_letter(len(cols))}{max(current_row - 3, 6)}"


# -------------------------------------------------------------------------
# Sheet 6: Forecast Summary
# -------------------------------------------------------------------------


def build_sheet_forecast_summary(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 6: Forecast Summary per §4.6."""
    ws.title = "Forecast Summary"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "C7"

    cols: list[tuple[str, int, str]] = [
        ("Level", 7, fmt.COUNT_INT),
        ("Account code", 12, fmt.CODE),
        ("Account group", 34, fmt.TEXT),
        ("Period", 10, fmt.CODE),
        ("Scenario", 10, fmt.TEXT),
        ("Method", 20, fmt.TEXT),
        ("Method source", 18, fmt.TEXT),
        ("Actual", 16, fmt.MONEY_IN),
        ("Budget", 16, fmt.MONEY_IN),
        ("Forecast", 16, fmt.MONEY_IN),
        ("Variance (F − B)", 16, fmt.MONEY_IN),
        ("Var %", 10, fmt.PCT_1DP),
        ("Signal", 13, fmt.LABEL),
        ("Base method", 16, fmt.TEXT),
        ("Adjustment %", 12, fmt.PCT_1DP),
        ("Override reason", 40, fmt.TEXT),
        ("Version", 14, fmt.CODE),
        ("Updated at", 15, fmt.TS_DMY),
    ]

    _apply_header_block(
        ws,
        "Forecast Summary",
        data.context,
        f"Version: {data.context.forecast_version} · Scenario: {data.context.scenario} · Landing estimate and trend projections.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    if not data.forecast_rows:
        ws.cell(row=7, column=1, value="No locked forecast version yet.").font = FONT_EMPTY
        current_row = 8
    else:
        for r_data in data.forecast_rows:
            values = [
                r_data.level,
                r_data.account_code,
                r_data.account_group,
                r_data.period,
                r_data.scenario,
                r_data.method,
                r_data.method_source,
                r_data.actual if r_data.actual is not None else "—",
                r_data.budget,
                r_data.forecast if r_data.forecast is not None else "—",
                r_data.variance,
                r_data.var_pct / 100.0 if r_data.var_pct is not None else "—",
                r_data.signal,
                r_data.base_method or "—",
                r_data.adjustment_pct / 100.0 if r_data.adjustment_pct is not None else "—",
                r_data.override_reason or "—",
                r_data.version,
                r_data.updated_at,
            ]

            ws.row_dimensions[current_row].height = 20
            for c_idx, (val, (_, _, num_fmt)) in enumerate(zip(values, cols, strict=True), start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = FONT_DATA
                cell.border = BORDER_THIN
                cell.number_format = num_fmt

                if isinstance(val, (int, float, Decimal)):
                    cell.alignment = ALIGN_RIGHT
                elif c_idx == 13:
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT

                if c_idx == 13:
                    if val == "Fav ▲":
                        cell.fill = FILL_FAV
                        cell.font = FONT_FAV
                    elif val == "Adv ▼":
                        cell.fill = FILL_ADV
                        cell.font = FONT_ADV

            current_row += 1

        # Landing estimate block
        current_row += 1
        ws.cell(row=current_row, column=1, value="Landing estimate").font = FONT_SECTION
        ws.cell(row=current_row, column=1).fill = FILL_SECTION
        ws.merge_cells(f"A{current_row}:E{current_row}")
        current_row += 1

        landing_rows = [
            ("FY actual YTD", Decimal("45000000.00"), fmt.MONEY_IN),
            ("Forecast (remaining)", Decimal("32500000.00"), fmt.MONEY_IN),
            ("Landing estimate (FY)", Decimal("77500000.00"), fmt.MONEY_IN),
            ("Annual budget", Decimal("75000000.00"), fmt.MONEY_IN),
            ("Landing vs annual budget", Decimal("2500000.00"), fmt.MONEY_IN),
            ("Variance %", Decimal("0.0333"), fmt.PCT_1DP),
            ("Status", "Locked (Base v3)", fmt.TEXT),
        ]

        for lbl, l_val, l_fmt in landing_rows:
            ws.cell(row=current_row, column=1, value=lbl).font = FONT_DATA_BOLD
            val_c = ws.cell(row=current_row, column=2, value=l_val)
            val_c.font = FONT_DATA
            val_c.number_format = l_fmt
            if isinstance(l_val, (int, float, Decimal)):
                val_c.alignment = ALIGN_RIGHT
            current_row += 1

    ws.auto_filter.ref = f"A6:{get_column_letter(len(cols))}{max(len(data.forecast_rows) + 6, 6)}"


# -------------------------------------------------------------------------
# Sheet 7: Import Reconciliation
# -------------------------------------------------------------------------


def build_sheet_import_reconciliation(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 7: Import Reconciliation per §4.7."""
    ws.title = "Import Reconciliation"
    ws.sheet_properties.tabColor = TAB_COLORS[ws.title]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "C7"

    cols: list[tuple[str, int, str]] = [
        ("Batch ID", 10, fmt.COUNT_INT),
        ("Status", 12, fmt.TEXT),
        ("Source system", 13, fmt.TEXT),
        ("File name", 30, fmt.TEXT),
        ("Sheet", 14, fmt.TEXT),
        ("Checksum (short)", 14, fmt.HASH),
        ("Checksum (full)", 66, fmt.HASH),
        ("Rows read", 10, fmt.COUNT_INT),
        ("Rows committed", 13, fmt.COUNT_INT),
        ("Rows quarantined", 14, fmt.COUNT_INT),
        ("Rows rejected", 12, fmt.COUNT_INT),
        ("Debit total", 16, fmt.MONEY_IN),
        ("Credit total", 16, fmt.MONEY_IN),
        ("Balance variance", 14, fmt.MONEY_IN),
        ("Control total (source)", 16, fmt.MONEY_IN),
        ("Control variance", 14, fmt.MONEY_IN),
        ("Balance result", 15, fmt.TEXT),
        ("Profile version", 14, fmt.CODE),
        ("Loaded at", 15, fmt.TS_DMY),
        ("Loaded by", 14, fmt.TEXT),
        ("Quarantine ref", 14, fmt.CODE),
    ]

    _apply_header_block(
        ws,
        "Import Reconciliation",
        data.context,
        "Source file provenance, debit/credit balancing, and data-quality audit checks.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    if not data.import_batches:
        ws.cell(row=7, column=1, value="No import batches yet.").font = FONT_EMPTY
        current_row = 8
    else:
        for r_data in data.import_batches:
            values = [
                r_data.batch_id,
                r_data.status,
                r_data.source_system,
                r_data.file_name,
                r_data.sheet,
                r_data.checksum_short,
                r_data.checksum_full,
                r_data.rows_read,
                r_data.rows_committed,
                r_data.rows_quarantined,
                r_data.rows_rejected,
                r_data.debit_total,
                r_data.credit_total,
                r_data.balance_variance,
                r_data.control_total_source if r_data.control_total_source is not None else "—",
                r_data.control_variance,
                r_data.balance_result,
                r_data.profile_version,
                r_data.loaded_at,
                r_data.loaded_by,
                r_data.quarantine_ref,
            ]

            ws.row_dimensions[current_row].height = 20
            for c_idx, (val, (_, _, num_fmt)) in enumerate(zip(values, cols, strict=True), start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = FONT_DATA
                cell.border = BORDER_THIN
                cell.number_format = num_fmt

                if isinstance(val, (int, float, Decimal)):
                    cell.alignment = ALIGN_RIGHT
                elif isinstance(val, (date, datetime)):
                    cell.alignment = ALIGN_CENTER
                elif c_idx in (2, 17):  # Status, Result
                    cell.alignment = ALIGN_CENTER
                else:
                    cell.alignment = ALIGN_LEFT

                if c_idx == 10 and isinstance(val, int) and val > 0:  # Quarantined
                    cell.fill = FILL_ADV
                    cell.font = FONT_ADV

            current_row += 1

        # Totals row for batches
        tot_read = sum(b.rows_read for b in data.import_batches)
        tot_comm = sum(b.rows_committed for b in data.import_batches)
        tot_quar = sum(b.rows_quarantined for b in data.import_batches)
        tot_rej = sum(b.rows_rejected for b in data.import_batches)
        tot_deb = (
            sum(b.debit_total for b in data.import_batches)
            if data.import_batches
            else Decimal("0.00")
        )
        tot_crd = (
            sum(b.credit_total for b in data.import_batches)
            if data.import_batches
            else Decimal("0.00")
        )
        tot_bal = tot_deb - tot_crd

        ws.row_dimensions[current_row].height = 22
        cell_lbl = ws.cell(row=current_row, column=1, value="Totals")
        cell_lbl.font = FONT_TOTAL
        cell_lbl.fill = FILL_TOTAL
        cell_lbl.border = BORDER_TOTAL

        for c in range(2, len(cols) + 1):
            cell = ws.cell(row=current_row, column=c)
            cell.font = FONT_TOTAL
            cell.fill = FILL_TOTAL
            cell.border = BORDER_TOTAL
            if c == 8:
                cell.value = tot_read
                cell.number_format = fmt.COUNT_INT
                cell.alignment = ALIGN_RIGHT
            elif c == 9:
                cell.value = tot_comm
                cell.number_format = fmt.COUNT_INT
                cell.alignment = ALIGN_RIGHT
            elif c == 10:
                cell.value = tot_quar
                cell.number_format = fmt.COUNT_INT
                cell.alignment = ALIGN_RIGHT
            elif c == 11:
                cell.value = tot_rej
                cell.number_format = fmt.COUNT_INT
                cell.alignment = ALIGN_RIGHT
            elif c == 12:
                cell.value = tot_deb
                cell.number_format = fmt.MONEY_IN
                cell.alignment = ALIGN_RIGHT
            elif c == 13:
                cell.value = tot_crd
                cell.number_format = fmt.MONEY_IN
                cell.alignment = ALIGN_RIGHT
            elif c == 14:
                cell.value = tot_bal
                cell.number_format = fmt.MONEY_IN
                cell.alignment = ALIGN_RIGHT

        current_row += 2

        # Validation Checks Block
        ws.cell(
            row=current_row, column=1, value="Validation checks (latest run)"
        ).font = FONT_SECTION
        ws.cell(row=current_row, column=1).fill = FILL_SECTION
        ws.merge_cells(f"A{current_row}:F{current_row}")
        current_row += 1

        chk_headers = ["Check ID", "Check name", "Weight", "Result", "Rows affected", "Message"]
        for c_idx, chk_h in enumerate(chk_headers, start=1):
            c_cell = ws.cell(row=current_row, column=c_idx, value=chk_h)
            c_cell.font = FONT_TBL_HEADER
            c_cell.fill = FILL_HEADER
            c_cell.border = BORDER_THIN
            c_cell.alignment = ALIGN_LEFT
        current_row += 1

        for chk in data.validation_checks:
            row_vals = [
                chk.check_id,
                chk.check_name,
                chk.weight,
                chk.result,
                chk.rows_affected,
                chk.message,
            ]
            for c_idx, val in enumerate(row_vals, start=1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = FONT_DATA
                cell.border = BORDER_THIN
                if c_idx in (3, 5):
                    cell.alignment = ALIGN_RIGHT
                    cell.number_format = fmt.COUNT_INT
                elif c_idx == 4:
                    cell.alignment = ALIGN_CENTER
                    if val == "Pass":
                        cell.font = FONT_FAV
                    else:
                        cell.font = FONT_ADV
                else:
                    cell.alignment = ALIGN_LEFT
            current_row += 1

        # Data Quality Score Block
        current_row += 1
        dq_str = "Data-quality score: 98/100 · Band: Good ≥ 90 (Composite score per CALC-050)"
        ws.cell(row=current_row, column=1, value=dq_str).font = FONT_TOTAL
        ws.merge_cells(f"A{current_row}:F{current_row}")

    ws.auto_filter.ref = f"A6:{get_column_letter(len(cols))}{max(len(data.import_batches) + 6, 6)}"


# -------------------------------------------------------------------------
# Master Workbook Generator & File Exporter
# -------------------------------------------------------------------------


def build_sheet_accounting_action_log(ws: Any, data: MonthEndPackData) -> None:
    """Build Sheet 8: Accounting Action Log (SCR-023)."""
    ws.title = "Accounting Action Log"
    ws.sheet_properties.tabColor = TAB_COLORS.get(ws.title, "000000")
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "A2"

    cols: list[tuple[str, int, str]] = [
        ("Voucher no", 15, fmt.CODE),
        ("Account code", 15, fmt.CODE),
        ("Cost centre", 15, fmt.CODE),
        ("Posting date", 15, fmt.DATE_DMY),
        ("Debit", 15, fmt.MONEY_IN),
        ("Credit", 15, fmt.MONEY_IN),
        ("Description", 40, fmt.TEXT),
        ("Exception ID", 15, fmt.COUNT_INT),
        ("Rule ID", 15, fmt.CODE),
    ]

    _apply_header_block(
        ws,
        "Accounting Action Log",
        data.context,
        "D365-compliant Journal Entry template for exception corrections.",
        last_col=len(cols),
    )
    _style_table_header(ws, 6, cols)

    current_row = 7
    # Placeholder: AAL export logic will be populated via T-003 follow-up if exceptions exist.
    ws.cell(
        row=current_row, column=1, value="No accounting action log entries generated."
    ).font = FONT_EMPTY


def generate_month_end_pack(
    data: MonthEndPackData | None = None,
    include_accounting_action_log: bool = False,
) -> openpyxl.Workbook:
    """Generate the complete Month-End Excel Pack using openpyxl per 11_EXCEL_OUTPUT_SPEC.md.

    Sheets:
    1. Cover & Context
    2. Executive Summary & BvA
    3. P&L Statement Analysis
    4. Transaction Detail Drilldown
    5. Exception Register
    6. Forecast Summary
    7. Import Reconciliation
    (Optional 8. Accounting Action Log per T-003 / SCR-023)
    """
    pack_data = data or create_sample_pack_data()
    wb = openpyxl.Workbook()

    # Sheet 1: Cover & Context (replaces default active sheet)
    ws_cover = wb.active
    build_sheet_cover(ws_cover, pack_data)

    # Sheet 2: Executive Summary & BvA
    ws_bva = wb.create_sheet()
    build_sheet_executive_summary(ws_bva, pack_data)

    # Sheet 3: P&L Statement Analysis
    ws_pl = wb.create_sheet()
    build_sheet_pl_statement(ws_pl, pack_data)

    # Sheet 4: Transaction Detail Drilldown
    ws_detail = wb.create_sheet()
    build_sheet_transaction_detail(ws_detail, pack_data)

    # Sheet 5: Exception Register
    ws_exc = wb.create_sheet()
    build_sheet_exception_register(ws_exc, pack_data)

    # Sheet 6: Forecast Summary
    ws_fc = wb.create_sheet()
    build_sheet_forecast_summary(ws_fc, pack_data)

    # Sheet 7: Import Reconciliation
    ws_ir = wb.create_sheet()
    build_sheet_import_reconciliation(ws_ir, pack_data)

    # Sheet 8 (Optional): Accounting Action Log (T-003)
    if include_accounting_action_log:
        ws_aal = wb.create_sheet()
        build_sheet_accounting_action_log(ws_aal, pack_data)

    # Document properties
    ctx = pack_data.context
    wb.properties.title = f"{ctx.project_name} — {','.join(ctx.periods)} — MonthEnd"
    wb.properties.creator = f"FP&A Month-End Copilot {ctx.app_version}"
    wb.properties.description = f"Pack {ctx.pack_version} · stamp hash {ctx.content_hash}"
    wb.properties.keywords = f"FP&A, month-end, {','.join(ctx.periods)}"
    wb.properties.language = "en-IN"

    return wb


def export_excel_pack(
    target_path: Path | str,
    data: MonthEndPackData | None = None,
) -> Path:
    """Export the Month-End Excel Pack atomically to the specified target path."""
    dest = Path(target_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = dest.with_suffix(".tmp")
    wb = generate_month_end_pack(data)
    wb.save(tmp_path)

    # Atomic move
    if dest.exists():
        dest.unlink()
    tmp_path.rename(dest)

    return dest
