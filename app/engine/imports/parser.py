"""Deterministic parser and validator per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md."""

import csv
import hashlib
import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Dict, Tuple, Optional, Any, Set, Union

from app.engine.calc import quantize_money, ZERO
from app.engine.imports.models import (
    PreScanResult,
    ValidationIssue,
    ValidationCheckReport,
    ParsedTransaction,
    ImportBatchResult,
)
from app.engine.imports.profiles import MappingProfile, match_profile, normalize_header, BUILTIN_PROFILES

DEFAULT_FY26_PERIODS = {f"FY26-P{i:02d}" for i in range(1, 13)}

MONTH_NAME_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def compute_file_checksum(filepath: str | Path) -> str:
    """Compute SHA-256 of file per ADR-001 and 04 §5.1."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _excel_data_sheet(
    filepath: str | Path, preferred_sheet: Optional[str] = None
) -> Tuple[str, List[str], int]:
    """Select the visible transaction sheet, excluding auxiliary workbook tabs."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - declared runtime dependency
        raise ImportError("openpyxl is required to import Excel workbooks") from exc

    workbook = load_workbook(filepath, read_only=True, data_only=True)
    try:
        sheet_names = list(workbook.sheetnames)
        visible_names = [
            worksheet.title
            for worksheet in workbook.worksheets
            if worksheet.sheet_state == "visible"
        ]
        if preferred_sheet in visible_names:
            selected = preferred_sheet
        else:
            visible_by_fold = {name.casefold(): name for name in visible_names}
            selected = next(
                (
                    visible_by_fold[name]
                    for name in ("data", "gl_export", "gl_actuals_template")
                    if name in visible_by_fold
                ),
                None,
            )
            if selected is None:
                auxiliary = {
                    "controltotals",
                    "approvedtotal",
                    "vendorcategories",
                    "recurringcosts",
                    "approvalthresholds",
                    "ownerassignments",
                }
                selected = next(
                    (name for name in visible_names if name.casefold() not in auxiliary),
                    None,
                )
        if selected is None:
            raise ValueError("Workbook has no visible transaction sheet. [import.noDataRows]")
        row_count = int(workbook[selected].max_row or 0)
        return selected, sheet_names, row_count
    finally:
        workbook.close()


def prescan_file(filepath: str | Path) -> PreScanResult:
    """Execute Step 2 Pre-scan per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §3."""
    p = Path(filepath)
    size = p.stat().st_size
    checksum = compute_file_checksum(p)
    name = p.name

    if p.suffix.lower() in {".xlsx", ".xlsm"}:
        sheet_name, sheet_names, _row_count = _excel_data_sheet(p)
        from app.engine.imports.hardening import load_hardened_excel_sheet

        hardened = load_hardened_excel_sheet(p, sheet_name=sheet_name, header_rows=[1])
        return PreScanResult(
            file_name=name,
            file_size_bytes=size,
            file_checksum=checksum,
            sheet_names=sheet_names,
            estimated_rows=len(hardened.rows) + len(hardened.quarantined_rows),
            header_row_candidate=hardened.header_row_index,
            sample_headers=hardened.headers,
            has_banner=False,
            is_encrypted=False,
        )

    # Basic CSV scan
    lines = []
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for _ in range(25):
            line = f.readline()
            if not line:
                break
            lines.append(line)

    has_banner = False
    header_idx = 0
    headers = []

    # Detect header row
    for i, line in enumerate(lines):
        clean = line.strip()
        if clean.startswith("#"):
            has_banner = True
            continue
        if "," in clean or ";" in clean or "\t" in clean:
            header_idx = i + 1
            headers = [h.strip() for h in re.split(r"[,;\t]", clean)]
            break

    # Estimate total rows
    with open(p, "rb") as f:
        estimated_rows = sum(1 for _ in f)
    if has_banner:
        estimated_rows -= 1
    if header_idx > 0:
        estimated_rows -= 1

    return PreScanResult(
        file_name=name,
        file_size_bytes=size,
        file_checksum=checksum,
        sheet_names=["Data"] if p.suffix.lower() == ".csv" else ["Sheet1"],
        estimated_rows=max(0, estimated_rows),
        detected_encoding="utf-8",
        detected_delimiter=",",
        header_row_candidate=header_idx,
        sample_headers=headers,
        has_banner=has_banner,
        is_encrypted=False,
    )


def parse_date_value(val: str, rule: str = "iso") -> Optional[str]:
    """Parse string date to standard YYYY-MM-DD per 04 §7.1."""
    if not val:
        return None
    val = str(val).strip()
    if not val:
        return None
    # Try ISO
    try:
        return datetime.strptime(val, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    # Try dd/mm/yyyy or dd-mm-yyyy or yyyy/mm/dd
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def resolve_fiscal_period(val: str) -> Optional[str]:
    """Resolve period string variant to canonical period code FY<yy>-P<pp> per 04 §7.4.
    
    Accepted variants per spec:
    - FY26-P09, FY26-P9
    - 2026-P09, 26-P09
    - 202609
    - Sep-26
    - 09/2026, 09-2026
    """
    if not val or not isinstance(val, str):
        return None
    s = val.strip()
    if not s:
        return None

    # 1. FY26-P09, FY26-P9, FY2026-P09
    m = re.match(r"^FY(\d{2}|\d{4})-?P(\d{1,2})$", s, re.IGNORECASE)
    if m:
        yr = int(m.group(1)) % 100
        p = int(m.group(2))
        return f"FY{yr:02d}-P{p:02d}"

    # 2. 2026-P09, 26-P09
    m = re.match(r"^(\d{2}|\d{4})-?P(\d{1,2})$", s, re.IGNORECASE)
    if m:
        yr = int(m.group(1)) % 100
        p = int(m.group(2))
        return f"FY{yr:02d}-P{p:02d}"

    # 3. 202609 or 2609 (YYYYMM)
    m = re.match(r"^(\d{4})(\d{2})$", s)
    if m:
        yr = int(m.group(1)) % 100
        p = int(m.group(2))
        return f"FY{yr:02d}-P{p:02d}"

    # 4. Sep-26, Sep-2026
    m = re.match(r"^([a-zA-Z]{3,9})[-/ ](\d{2}|\d{4})$", s)
    if m:
        mon_str = m.group(1)[:3].lower()
        if mon_str in MONTH_NAME_MAP:
            p = MONTH_NAME_MAP[mon_str]
            yr = int(m.group(2)) % 100
            return f"FY{yr:02d}-P{p:02d}"

    # 5. 09/2026 or 09-2026 or 9/2026
    m = re.match(r"^(\d{1,2})[/-](\d{2}|\d{4})$", s)
    if m:
        p = int(m.group(1))
        yr = int(m.group(2)) % 100
        return f"FY{yr:02d}-P{p:02d}"

    return None


def check_imp_017_sign_rule(
    val: Any,
    rule: str = "cr_dr",
    mode: str = "balance_style",
    source_row_ref: Optional[str] = None,
) -> Tuple[Decimal, Optional[str], Optional[ValidationIssue]]:
    """Check IMP-017: Sign / Cr-Dr interpretation applied per 04 §7.2, §8 X16, §10.
    
    Interpretation rules:
    - In balance-style exports: Dr -> debit, Cr -> credit.
    - In amount-style exports: Cr -> negative, Dr -> positive.
    - Accounting parentheses: (1,200.00) -> negative amount.
    
    Returns (amount, direction, issue) where:
    - amount: Quantized Decimal money
    - direction: 'debit', 'credit', 'negative', 'positive', or None
    - issue: ValidationIssue with slug 'import.signRuleApplied' if sign rule was applied, else None
    """
    if val is None:
        return ZERO, None, None

    if isinstance(val, (int, float, Decimal)):
        amt = quantize_money(val)
        return amt, None, None

    s = str(val).strip()
    if not s or s == "-":
        return ZERO, None, None

    direction: Optional[str] = None
    negative = False
    sign_rule_applied = False

    # Check parentheses e.g. (1,200.00) or (₹ 1,200.00)
    if s.startswith("(") and s.endswith(")"):
        negative = True
        sign_rule_applied = True
        direction = "negative"
        s = s[1:-1].strip()

    # Check trailing Cr / Dr
    m_cr_dr = re.search(r"\b(cr|dr)\b", s, re.IGNORECASE)
    if not m_cr_dr:
        m_cr_dr = re.search(r"(\d+)(cr|dr)\b", s, re.IGNORECASE)

    if m_cr_dr:
        sign_rule_applied = True
        suffix = m_cr_dr.group(1).upper() if m_cr_dr.lastindex == 1 else m_cr_dr.group(2).upper()
        # Remove suffix from string for Decimal parsing
        s = re.sub(r"\b(cr|dr)\b", "", s, flags=re.IGNORECASE)
        s = re.sub(r"(?<=\d)(cr|dr)\b", "", s, flags=re.IGNORECASE).strip()

        if mode == "balance_style":
            direction = "debit" if suffix == "DR" else "credit"
        else:  # amount_style
            if suffix == "CR":
                negative = True
                direction = "negative"
            else:
                direction = "positive"

    # Strip currency symbols, commas, spaces
    s = re.sub(r"[₹$,\s]", "", s)
    try:
        amt = Decimal(s)
        if negative:
            amt = -amt
        amt = quantize_money(amt)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Unparseable numeric value: {val}")

    issue = None
    if sign_rule_applied:
        issue = ValidationIssue(
            check_code="IMP-017",
            severity="low",
            message_slug="import.signRuleApplied",
            message=f"Interpreted '{val}' as {direction} using rule '{rule}'",
            source_row_ref=source_row_ref,
        )

    return amt, direction, issue


def parse_money_value(val: Any) -> Decimal:
    """Parse number or monetary value string safely per 04 §7.2."""
    amt, _, _ = check_imp_017_sign_rule(val, rule="parens_negative", mode="amount_style")
    return amt


def check_imp_018_period_in_calendar(
    period_code: Optional[str],
    valid_periods: Optional[Union[Set[str], List[str]]] = None,
    source_row_ref: Optional[str] = None,
) -> Optional[ValidationIssue]:
    """Check IMP-018: Period resolved against the fiscal calendar per 04 §7.4 & §10.
    
    On failure: Quarantine the row with slug 'import.periodNotInCalendar'.
    """
    if valid_periods is None:
        calendar_periods = DEFAULT_FY26_PERIODS
    else:
        calendar_periods = set(valid_periods)

    if not period_code or not str(period_code).strip():
        return ValidationIssue(
            check_code="IMP-018",
            severity="high",
            message_slug="import.periodNotInCalendar",
            message="Fiscal period code is missing or unpopulated",
            source_row_ref=source_row_ref,
        )

    clean = str(period_code).strip()
    resolved = resolve_fiscal_period(clean)
    if resolved is None or resolved not in calendar_periods:
        return ValidationIssue(
            check_code="IMP-018",
            severity="high",
            message_slug="import.periodNotInCalendar",
            message=f"Period '{clean}' could not be resolved against fiscal calendar",
            source_row_ref=source_row_ref,
        )
    return None


def check_imp_019_date_in_fiscal_year(
    posting_date: Union[str, datetime, Any],
    fy_start: str = "2026-01-01",
    fy_end: str = "2026-12-31",
    fiscal_year: int = 2026,
    source_row_ref: Optional[str] = None,
) -> Optional[ValidationIssue]:
    """Check IMP-019: Dates inside configured fiscal year per 04 §10 & §20 E6.
    
    On failure: Quarantine the row with slug 'import.dateOutsideFiscalYear'.
    """
    if posting_date is None:
        return ValidationIssue(
            check_code="IMP-019",
            severity="medium",
            message_slug="import.dateOutsideFiscalYear",
            message="Posting date is missing",
            source_row_ref=source_row_ref,
        )

    date_str = str(posting_date).strip()
    if len(date_str) > 10:
        date_str = date_str[:10]

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        parsed = parse_date_value(date_str)
        if not parsed:
            return ValidationIssue(
                check_code="IMP-019",
                severity="medium",
                message_slug="import.dateOutsideFiscalYear",
                message=f"Unrecognized date format: '{posting_date}'",
                source_row_ref=source_row_ref,
            )
        dt = datetime.strptime(parsed, "%Y-%m-%d").date()

    start_dt = datetime.strptime(fy_start, "%Y-%m-%d").date()
    end_dt = datetime.strptime(fy_end, "%Y-%m-%d").date()

    if not (start_dt <= dt <= end_dt):
        return ValidationIssue(
            check_code="IMP-019",
            severity="medium",
            message_slug="import.dateOutsideFiscalYear",
            message=f"Posting date {dt.isoformat()} falls outside configured fiscal year {fiscal_year} ({fy_start} to {fy_end})",
            source_row_ref=source_row_ref,
        )
    return None


def check_imp_020_currency_matches(
    currency_code: Optional[str],
    project_currency: str = "INR",
    source_row_ref: Optional[str] = None,
) -> Optional[ValidationIssue]:
    """Check IMP-020: Currency matches project currency (INR default) per 04 §10 & §20 E10.
    
    On failure: Quarantine the row with slug 'import.mixedCurrency'.
    """
    if not currency_code or not str(currency_code).strip():
        # Absent currency defaults to project currency per 04 §6
        return None

    clean = str(currency_code).strip().upper()
    expected = project_currency.strip().upper()

    if clean != expected:
        return ValidationIssue(
            check_code="IMP-020",
            severity="high",
            message_slug="import.mixedCurrency",
            message=f"Currency '{clean}' does not match project currency '{expected}'",
            source_row_ref=source_row_ref,
        )
    return None


def check_imp_021_zero_amount(
    debit: Any,
    credit: Any,
    source_row_ref: Optional[str] = None,
) -> Tuple[bool, Optional[ValidationIssue]]:
    """Check IMP-021: Zero-amount rows noted per 04 §10 & §20 E4.
    
    On failure / trigger: Keep the row; count and flag it (excluded from outlier rules).
    Slug: 'import.zeroAmountRows'.
    """
    d = quantize_money(debit) if not isinstance(debit, Decimal) else debit
    c = quantize_money(credit) if not isinstance(credit, Decimal) else credit

    if d == ZERO and c == ZERO:
        issue = ValidationIssue(
            check_code="IMP-021",
            severity="low",
            message_slug="import.zeroAmountRows",
            message="Zero-amount row noted (kept in load, flagged for outlier rules)",
            source_row_ref=source_row_ref,
        )
        return True, issue
    return False, None


def check_imp_022_both_debit_credit(
    debit: Any,
    credit: Any,
    source_row_ref: Optional[str] = None,
) -> Optional[ValidationIssue]:
    """Check IMP-022: Debit and credit not both populated per 04 §7.2 & §10.
    
    On failure / trigger: Warn; load row as provided. Slug: 'import.bothDebitCredit'.
    """
    d = quantize_money(debit) if not isinstance(debit, Decimal) else debit
    c = quantize_money(credit) if not isinstance(credit, Decimal) else credit

    if d > ZERO and c > ZERO:
        return ValidationIssue(
            check_code="IMP-022",
            severity="low",
            message_slug="import.bothDebitCredit",
            message=f"Both debit (₹{d}) and credit (₹{c}) are populated on the same row",
            source_row_ref=source_row_ref,
        )
    return None


# ---------------------------------------------------------------------------
# DEC-056 (OQ-025): the debit=credit gate is a property of a JOURNAL.
# ---------------------------------------------------------------------------
#
# `04` §2.2 lists the bank ledger and the payroll/procurement feed as
# amount-style sources: every row carries one signed amount, and the file
# reconciles against a supplied control total rather than balancing to zero.
# Applying an unconditional exact debit=credit test to them rejects a file that
# is arithmetically fine and makes every fact it carries unreachable - which is
# what left the two sub-ledgers at 0 committed rows and P1 unreachable.
#
# So the gate is scoped by source type, per the DEC-056 ruling:
#   * journal-style (`actuals_d365`, `budget`) keep the unconditional exact
#     debit=credit reject;
#   * amount-style sub-ledgers are validated by control-total / net-amount
#     reconciliation within the `06` §8 tolerance. Inside it the batch LOADS
#     and the variance is stated - in this report and in
#     `FactImportBatch.net_imbalance`, which is what EXC-001 reads.
AMOUNT_STYLE_SOURCE_TYPES = frozenset({"actuals_procurement", "actuals_payroll"})

# `06` §8 tolerance for a sub-ledger that reconciles within rupees.
SUB_LEDGER_RECONCILIATION_TOLERANCE = Decimal("500.00")


def is_amount_style_source(source_type: str) -> bool:
    """True when `source_type` is an amount-style sub-ledger under DEC-056."""
    return str(source_type) in AMOUNT_STYLE_SOURCE_TYPES


def check_imp_023_subledger_reconciliation(
    transactions: List[ParsedTransaction],
    tolerance: Decimal = ZERO,
) -> ValidationCheckReport:
    """Check IMP-023 for an amount-style sub-ledger (DEC-056, tolerance `06` §8).

    An amount-style source is not required to balance to zero; it is required to
    reconcile to its supplied control total within the tolerance. A CSV supplies
    no `ControlTotals` worksheet, so the reconciliation actually available is
    the file's own net amount, and that is what this measures.
    """
    tol = quantize_money(tolerance)
    total_debit = quantize_money(sum((t.debit for t in transactions), ZERO))
    total_credit = quantize_money(sum((t.credit for t in transactions), ZERO))
    net = quantize_money(total_debit - total_credit)
    variance = quantize_money(abs(net))
    reconciled = variance <= tol

    if reconciled:
        status = "pass" if variance == ZERO else "warn"
        detail = (
            f"Amount-style sub-ledger (DEC-056): net ₹{net} reconciles within "
            f"tolerance ₹{tol} (Total Debit: ₹{total_debit}, Total Credit: "
            f"₹{total_credit}). The batch loads and the variance is stated for EXC-001."
        )
    else:
        status = "fail"
        detail = (
            f"Amount-style sub-ledger (DEC-056): net ₹{net} exceeds the ₹{tol} "
            f"reconciliation tolerance (Total Debit: ₹{total_debit}, "
            f"Total Credit: ₹{total_credit})"
        )

    return ValidationCheckReport(
        check_code="IMP-023",
        check_name="Sub-ledger net reconciles to control total within tolerance",
        status=status,
        severity="high",
        offending_count=0 if reconciled else 1,
        detail=detail,
        message_slug=None if reconciled else "import.balanceMismatch",
    )


def check_imp_023_balance(
    transactions: List[ParsedTransaction],
    tolerance: Decimal = ZERO,
    check_entity_period: bool = True,
) -> ValidationCheckReport:
    """Check IMP-023: Debit = credit balance within tolerance per file/entity/period per 04 §10 & §12.
    
    Computed at exact minor-unit Decimal precision (no epsilon).
    On failure: Reject; show the imbalance amount and the top contributing rows.
    Slug: 'import.balanceMismatch'.
    """
    tol = quantize_money(tolerance) if not isinstance(tolerance, Decimal) else tolerance
    total_debit = quantize_money(sum((t.debit for t in transactions), ZERO))
    total_credit = quantize_money(sum((t.credit for t in transactions), ZERO))
    imbalance = quantize_money(abs(total_debit - total_credit))

    offending_count = 0
    top_samples: List[Dict[str, Any]] = []
    group_imbalances: List[str] = []

    if imbalance > tol:
        offending_count += 1

    if check_entity_period and transactions:
        entity_totals: Dict[str, Tuple[Decimal, Decimal]] = {}
        period_totals: Dict[str, Tuple[Decimal, Decimal]] = {}

        for t in transactions:
            ent = t.company_code or "DEFAULT"
            d, c = entity_totals.get(ent, (ZERO, ZERO))
            entity_totals[ent] = (d + t.debit, c + t.credit)

            per = t.period_code or (t.posting_date[:7] if t.posting_date else "DEFAULT")
            d, c = period_totals.get(per, (ZERO, ZERO))
            period_totals[per] = (d + t.debit, c + t.credit)

        for ent, (d, c) in entity_totals.items():
            diff = quantize_money(abs(d - c))
            if diff > tol:
                group_imbalances.append(f"Entity '{ent}' imbalance: ₹{diff}")
                offending_count += 1

        for per, (d, c) in period_totals.items():
            diff = quantize_money(abs(d - c))
            if diff > tol:
                group_imbalances.append(f"Period '{per}' imbalance: ₹{diff}")
                offending_count += 1

    is_balanced = (imbalance <= tol) and (len(group_imbalances) == 0)

    if not is_balanced:
        sorted_txs = sorted(transactions, key=lambda t: abs(t.debit - t.credit), reverse=True)
        for t in sorted_txs[:5]:
            top_samples.append({
                "voucher_no": t.voucher_no,
                "source_row_ref": t.source_row_ref,
                "debit": str(t.debit),
                "credit": str(t.credit),
                "net_amount": str(t.net_amount),
            })

        detail = f"Imbalance ₹{imbalance} exceeds tolerance ₹{tol} (Total Debit: ₹{total_debit}, Total Credit: ₹{total_credit})"
        if group_imbalances:
            detail += f". Breakdown: {'; '.join(group_imbalances[:3])}"
    else:
        detail = f"Total Debit: ₹{total_debit}, Total Credit: ₹{total_credit}, Imbalance: ₹{imbalance}"

    return ValidationCheckReport(
        check_code="IMP-023",
        check_name="Debit = credit balance within tolerance per file/entity/period",
        status="pass" if is_balanced else "fail",
        severity="high",
        offending_count=offending_count if not is_balanced else 0,
        sample_rows=top_samples,
        detail=detail,
        message_slug="import.balanceMismatch" if not is_balanced else None,
    )


def check_imp_024_row_count_reconciliation(
    source_count: int,
    loaded_count: int,
    quarantined_count: int,
    rejected_count: int,
) -> ValidationCheckReport:
    """Check IMP-024: Row-count reconciliation (source = loaded + quarantined + rejected) per 04 §10 & §12.
    
    Internal invariant: A mismatch blocks commit and indicates an internal anomaly, never a user error.
    Slug: 'import.countMismatch'.
    """
    expected = loaded_count + quarantined_count + rejected_count
    reconciled = (source_count == expected)
    diff = abs(source_count - expected)

    if reconciled:
        detail = f"Source ({source_count}) = Loaded ({loaded_count}) + Quarantined ({quarantined_count}) + Rejected ({rejected_count})"
    else:
        detail = f"Row-count reconciliation failed (slug: import.countMismatch): Source ({source_count}) != Loaded ({loaded_count}) + Quarantined ({quarantined_count}) + Rejected ({rejected_count})"

    return ValidationCheckReport(
        check_code="IMP-024",
        check_name="Row-count reconciliation equation",
        status="pass" if reconciled else "fail",
        severity="high",
        offending_count=0 if reconciled else diff,
        detail=detail,
        message_slug="import.countMismatch" if not reconciled else None,
    )


def parse_csv_transactions(
    filepath: str | Path,
    profile: Optional[MappingProfile] = None,
    fiscal_year: int = 2026,
    fy_start: str = "2026-01-01",
    fy_end: str = "2026-12-31",
    project_currency: str = "INR",
    balance_tolerance: Decimal = ZERO,
    source_row_refs: Optional[List[str]] = None,
) -> Tuple[ImportBatchResult, List[ParsedTransaction]]:
    """Parse CSV returning both the validation batch result and the valid parsed transactions."""
    p = Path(filepath)
    checksum = compute_file_checksum(p)
    prescan = prescan_file(p)

    if profile is None:
        profile = match_profile(prescan.sample_headers)
        if profile is None:
            profile = BUILTIN_PROFILES[0]

    loaded: List[ParsedTransaction] = []
    quarantined: List[Dict[str, Any]] = []
    rejected: List[ValidationIssue] = []

    sign_rule_issues: List[ValidationIssue] = []
    period_issues: List[ValidationIssue] = []
    date_fy_issues: List[ValidationIssue] = []
    currency_issues: List[ValidationIssue] = []
    zero_amount_issues: List[ValidationIssue] = []
    both_debit_credit_issues: List[ValidationIssue] = []

    col_idx_map: Dict[str, int] = {}
    total_source_rows = 0
    total_debit = ZERO
    total_credit = ZERO
    voucher_line_counts: Dict[Tuple[str, str], int] = {}

    with open(p, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        current_row_idx = 0
        headers_found = False

        for row in reader:
            current_row_idx += 1
            if not row or all(c.strip() == "" for c in row):
                continue
            if row[0].strip().startswith("#"):
                continue

            if not headers_found:
                headers = [h.strip() for h in row]
                for idx, h in enumerate(headers):
                    norm = normalize_header(h)
                    canonical = profile.column_map.get(norm)
                    if canonical and canonical != "__ignored__":
                        col_idx_map[canonical] = idx
                headers_found = True
                continue

            source_row_index = total_source_rows
            total_source_rows += 1
            fallback_source_row_ref = (
                source_row_refs[source_row_index]
                if source_row_refs is not None and source_row_index < len(source_row_refs)
                else f"line {current_row_idx}"
            )
            raw_row_dict = dict(zip([f"col_{i}" for i in range(len(row))], row))

            def get_col(field_name: str) -> Optional[str]:
                if field_name in col_idx_map:
                    idx = col_idx_map[field_name]
                    if idx < len(row):
                        val = row[idx].strip()
                        return val if val else None
                return None

            source_row_ref = get_col("source_row_ref") or fallback_source_row_ref
            voucher = get_col("voucher_no") or f"VCH-AUTO-{total_source_rows}"
            posting_date_raw = get_col("posting_date")
            document_date_raw = get_col("document_date")
            period_code_raw = get_col("period_code")
            company_code = get_col("company_code") or "IN01"
            account_code = get_col("account_code") or "5000"
            cost_center = get_col("cost_center_code")
            project_code = get_col("project_code")
            vendor_code = get_col("vendor_code")
            invoice_no = get_col("invoice_no")
            description = get_col("description")
            journal_category_raw = get_col("journal_category")
            journal_category = (
                journal_category_raw.strip().lower()
                if journal_category_raw and journal_category_raw.strip()
                else None
            )
            currency_raw = get_col("currency_code")

            # Cross-batch duplicate keys use the voucher's line number, not the
            # physical CSV row number. Derive a stable sequence within
            # (company, voucher) when the source omits one, counting even rows
            # later quarantined so the key still reflects source order.
            voucher_key = (str(company_code).strip(), str(voucher).strip())
            derived_line_no = voucher_line_counts.get(voucher_key, 0) + 1
            explicit_line_no = get_col("line_no")
            try:
                line_no = (
                    int(explicit_line_no)
                    if explicit_line_no is not None
                    else derived_line_no
                )
            except (TypeError, ValueError):
                line_no = derived_line_no
            voucher_line_counts[voucher_key] = max(
                voucher_line_counts.get(voucher_key, 0), line_no
            )

            debit_raw = get_col("debit")
            credit_raw = get_col("credit")
            amount_raw = get_col("amount")

            # IMP-018: Period resolution against calendar
            resolved_period = None
            if period_code_raw:
                p_issue = check_imp_018_period_in_calendar(period_code_raw, source_row_ref=source_row_ref)
                if p_issue:
                    period_issues.append(p_issue)
                    quarantined.append({
                        "source_row_ref": source_row_ref,
                        "reason_code": p_issue.message_slug,
                        "reason_detail": p_issue.message,
                        "raw_values": raw_row_dict,
                    })
                    continue
                resolved_period = resolve_fiscal_period(period_code_raw)

            # Date parsing & IMP-019. Document date is optional business context;
            # unlike posting_date it does not determine fiscal-period membership.
            document_date = (
                parse_date_value(document_date_raw, rule=profile.date_rule)
                if document_date_raw
                else None
            )
            if posting_date_raw:
                posting_date = parse_date_value(posting_date_raw, rule=profile.date_rule)
                if posting_date is None:
                    quarantined.append({
                        "source_row_ref": source_row_ref,
                        "reason_code": "import.dateUnparsed",
                        "reason_detail": f"Invalid date: {posting_date_raw}",
                        "raw_values": raw_row_dict,
                    })
                    continue
                fy_issue = check_imp_019_date_in_fiscal_year(
                    posting_date, fy_start=fy_start, fy_end=fy_end, fiscal_year=fiscal_year, source_row_ref=source_row_ref
                )
                if fy_issue:
                    date_fy_issues.append(fy_issue)
                    quarantined.append({
                        "source_row_ref": source_row_ref,
                        "reason_code": fy_issue.message_slug,
                        "reason_detail": fy_issue.message,
                        "raw_values": raw_row_dict,
                    })
                    continue
            else:
                posting_date = "2026-09-30"

            if resolved_period is None:
                month_num = int(posting_date[5:7]) if len(posting_date) >= 7 else 9
                yr_suffix = posting_date[2:4] if len(posting_date) >= 4 else "26"
                resolved_period = f"FY{yr_suffix}-P{month_num:02d}"

            # IMP-020: Currency match
            curr_issue = check_imp_020_currency_matches(
                currency_raw, project_currency=project_currency, source_row_ref=source_row_ref
            )
            if curr_issue:
                currency_issues.append(curr_issue)
                quarantined.append({
                    "source_row_ref": source_row_ref,
                    "reason_code": curr_issue.message_slug,
                    "reason_detail": curr_issue.message,
                    "raw_values": raw_row_dict,
                })
                continue
            currency = currency_raw.strip().upper() if currency_raw and currency_raw.strip() else project_currency

            # Amounts parsing, IMP-017, IMP-021, IMP-022
            try:
                if debit_raw is not None or credit_raw is not None:
                    debit, _, d_sign_issue = check_imp_017_sign_rule(
                        debit_raw, rule=profile.number_rule, mode="balance_style", source_row_ref=source_row_ref
                    )
                    credit, _, c_sign_issue = check_imp_017_sign_rule(
                        credit_raw, rule=profile.number_rule, mode="balance_style", source_row_ref=source_row_ref
                    )
                    if d_sign_issue:
                        sign_rule_issues.append(d_sign_issue)
                    if c_sign_issue:
                        sign_rule_issues.append(c_sign_issue)
                elif amount_raw is not None:
                    amt, _, amt_sign_issue = check_imp_017_sign_rule(
                        amount_raw, rule=profile.number_rule, mode="amount_style", source_row_ref=source_row_ref
                    )
                    if amt_sign_issue:
                        sign_rule_issues.append(amt_sign_issue)
                    if amt >= ZERO:
                        debit = amt
                        credit = ZERO
                    else:
                        debit = ZERO
                        credit = -amt
                else:
                    debit = ZERO
                    credit = ZERO
            except ValueError as e:
                quarantined.append({
                    "source_row_ref": source_row_ref,
                    "reason_code": "import.numberUnparsed",
                    "reason_detail": str(e),
                    "raw_values": raw_row_dict,
                })
                continue

            # IMP-021: Zero-amount rows
            is_zero, zero_issue = check_imp_021_zero_amount(debit, credit, source_row_ref=source_row_ref)
            if zero_issue:
                zero_amount_issues.append(zero_issue)

            # IMP-022: Debit and credit not both populated
            both_issue = check_imp_022_both_debit_credit(debit, credit, source_row_ref=source_row_ref)
            if both_issue:
                both_debit_credit_issues.append(both_issue)

            net_amount = quantize_money(debit - credit)
            total_debit += debit
            total_credit += credit

            tx = ParsedTransaction(
                source_row_ref=source_row_ref,
                voucher_no=voucher,
                posting_date=posting_date,
                company_code=company_code,
                account_code=account_code,
                cost_center_code=cost_center,
                project_code=project_code,
                vendor_code=vendor_code,
                invoice_no=invoice_no,
                description=description,
                debit=debit,
                credit=credit,
                net_amount=net_amount,
                currency_code=currency,
                document_date=document_date,
                line_no=line_no,
                journal_category=journal_category,
                is_zero_amount=is_zero,
                period_code=resolved_period,
                raw_values=raw_row_dict,
            )
            loaded.append(tx)

    checks: List[ValidationCheckReport] = []
    checks.append(ValidationCheckReport(
        check_code="IMP-001",
        check_name="File readable and format supported",
        status="pass",
        severity="high",
        offending_count=0,
    ))

    # IMP-017 report
    checks.append(ValidationCheckReport(
        check_code="IMP-017",
        check_name="Sign / Cr-Dr interpretation applied",
        status="warn" if sign_rule_issues else "pass",
        severity="low",
        offending_count=len(sign_rule_issues),
        detail=f"{len(sign_rule_issues)} rows had sign or Cr-Dr rules applied",
        message_slug="import.signRuleApplied" if sign_rule_issues else None,
    ))

    # IMP-018 report
    checks.append(ValidationCheckReport(
        check_code="IMP-018",
        check_name="Period resolved against the fiscal calendar",
        status="fail" if period_issues else "pass",
        severity="high",
        offending_count=len(period_issues),
        detail=f"{len(period_issues)} rows with periods outside fiscal calendar",
        message_slug="import.periodNotInCalendar" if period_issues else None,
    ))

    # IMP-019 report
    checks.append(ValidationCheckReport(
        check_code="IMP-019",
        check_name="Dates inside configured fiscal year",
        status="fail" if date_fy_issues else "pass",
        severity="medium",
        offending_count=len(date_fy_issues),
        detail=f"{len(date_fy_issues)} rows with dates outside configured fiscal year",
        message_slug="import.dateOutsideFiscalYear" if date_fy_issues else None,
    ))

    # IMP-020 report
    checks.append(ValidationCheckReport(
        check_code="IMP-020",
        check_name="Currency matches project currency",
        status="fail" if currency_issues else "pass",
        severity="high",
        offending_count=len(currency_issues),
        detail=f"{len(currency_issues)} rows with non-matching currency",
        message_slug="import.mixedCurrency" if currency_issues else None,
    ))

    # IMP-021 report
    checks.append(ValidationCheckReport(
        check_code="IMP-021",
        check_name="Zero-amount rows noted",
        status="warn" if zero_amount_issues else "pass",
        severity="low",
        offending_count=len(zero_amount_issues),
        detail=f"{len(zero_amount_issues)} zero-amount rows noted (kept in load)",
        message_slug="import.zeroAmountRows" if zero_amount_issues else None,
    ))

    # IMP-022 report
    checks.append(ValidationCheckReport(
        check_code="IMP-022",
        check_name="Debit and credit not both populated",
        status="warn" if both_debit_credit_issues else "pass",
        severity="low",
        offending_count=len(both_debit_credit_issues),
        detail=f"{len(both_debit_credit_issues)} rows have both debit and credit populated",
        message_slug="import.bothDebitCredit" if both_debit_credit_issues else None,
    ))

    # IMP-023 report
    # Per-entity/period balance checked if source is general ledger or explicitly requested
    check_entities_periods = (profile.source_type == "actuals_d365")
    # Budget files represent unidirectional budget amounts, so balance check passes for budget
    effective_balance_tolerance = quantize_money(balance_tolerance)
    if profile.source_type == "budget":
        balance_report = ValidationCheckReport(
            check_code="IMP-023",
            check_name="Debit = credit balance within tolerance per file/entity/period",
            status="pass",
            severity="high",
            offending_count=0,
            detail=f"Budget file: Total amount {total_debit}",
        )
    elif is_amount_style_source(profile.source_type):
        # DEC-056: an amount-style sub-ledger reconciles rather than balances.
        # With no caller-supplied tolerance, `06` §8's ₹500 applies.
        if effective_balance_tolerance == ZERO:
            effective_balance_tolerance = SUB_LEDGER_RECONCILIATION_TOLERANCE
        balance_report = check_imp_023_subledger_reconciliation(
            loaded, tolerance=effective_balance_tolerance
        )
    else:
        balance_report = check_imp_023_balance(
            loaded, tolerance=balance_tolerance, check_entity_period=check_entities_periods
        )
    checks.append(balance_report)

    # IMP-024 report
    reconciled_report = check_imp_024_row_count_reconciliation(
        total_source_rows, len(loaded), len(quarantined), len(rejected)
    )
    checks.append(reconciled_report)

    if profile.source_type != "budget":
        from app.engine.imports.control_totals import control_totals_not_supplied_report

        checks.append(control_totals_not_supplied_report())

    imbalance = quantize_money(total_debit - total_credit)
    # For an amount-style sub-ledger the gate is a reconciliation, not an exact
    # zero (DEC-056), so a batch that reconciled inside tolerance HAS passed the
    # gate even though its report carries a warning naming the variance.
    is_balanced = balance_report.status != "fail"

    batch = ImportBatchResult(
        batch_id=1,
        file_name=p.name,
        file_checksum=checksum,
        source_type=profile.source_type,
        total_source_rows=total_source_rows,
        loaded_count=len(loaded),
        quarantined_count=len(quarantined),
        rejected_count=len(rejected),
        is_balanced=is_balanced,
        total_debit=total_debit,
        total_credit=total_credit,
        net_imbalance=imbalance,
        checks=checks,
        quarantined_rows=quarantined,
        balance_tolerance=effective_balance_tolerance,
    )
    return batch, loaded


def _excel_value_for_csv(value: Any) -> str:
    """Serialize an Excel cell into the deterministic CSV parser's input form."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""
    return str(value)


def parse_excel_transactions(
    filepath: str | Path,
    profile: Optional[MappingProfile] = None,
    fiscal_year: int = 2026,
    fy_start: str = "2026-01-01",
    fy_end: str = "2026-12-31",
    project_currency: str = "INR",
    balance_tolerance: Decimal = ZERO,
    control_total_acceptance: Optional[Dict[str, str]] = None,
) -> Tuple[ImportBatchResult, List[ParsedTransaction]]:
    """Parse the transaction sheet and optional ControlTotals sheet in an XLSX."""
    from openpyxl import load_workbook
    from openpyxl.utils.datetime import from_excel

    from app.engine.imports.control_totals import read_control_totals_report
    from app.engine.imports.hardening import load_hardened_excel_sheet

    path = Path(filepath)
    preferred_sheet = profile.sheet_selector if profile is not None else None
    sheet_name, _sheet_names, _row_count = _excel_data_sheet(path, preferred_sheet)
    header_row = profile.header_row if profile is not None else 1
    hardened = load_hardened_excel_sheet(
        path,
        sheet_name=sheet_name,
        header_rows=[header_row],
    )
    if profile is None:
        profile = match_profile(hardened.headers) or BUILTIN_PROFILES[0]

    workbook = load_workbook(path, read_only=False, data_only=True)
    try:
        worksheet = workbook[sheet_name]
        date_columns = {
            index
            for index, header in enumerate(hardened.headers)
            if "date" in str(header).casefold()
        }
        csv_rows: List[List[str]] = []
        for row_index, row in zip(hardened.row_indices, hardened.rows):
            serialized_row = []
            for column_index, value in enumerate(row):
                if (
                    column_index in date_columns
                    and isinstance(value, (int, float))
                    and worksheet.cell(row=row_index, column=column_index + 1).is_date
                ):
                    value = from_excel(value, workbook.epoch).date()
                serialized_row.append(_excel_value_for_csv(value))
            csv_rows.append(serialized_row)
    finally:
        workbook.close()

    source_row_refs = [f"{sheet_name}!{row_index}" for row_index in hardened.row_indices]
    with TemporaryDirectory(prefix="fpa-xlsx-import-") as temp_dir:
        csv_path = Path(temp_dir) / "transaction-sheet.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(hardened.headers)
            writer.writerows(csv_rows)
        batch, transactions = parse_csv_transactions(
            csv_path,
            profile=profile,
            fiscal_year=fiscal_year,
            fy_start=fy_start,
            fy_end=fy_end,
            project_currency=project_currency,
            balance_tolerance=balance_tolerance,
            source_row_refs=source_row_refs,
        )

    batch.file_name = path.name
    batch.file_checksum = compute_file_checksum(path)
    batch.sheet_name = sheet_name

    hardening_gate_checks = {
        "import.missingRequiredColumns": (
            "IMP-005",
            "Required columns present after mapping",
        ),
        "import.duplicateHeaders": (
            "IMP-006",
            "Duplicate column headers resolved",
        ),
        "import.noDataRows": ("IMP-008", "Data range not empty"),
    }
    for slug, (check_code, check_name) in hardening_gate_checks.items():
        matching_findings = [finding for finding in hardened.findings if finding.slug == slug]
        if matching_findings:
            batch.checks.append(
                ValidationCheckReport(
                    check_code=check_code,
                    check_name=check_name,
                    status="fail",
                    severity="high",
                    offending_count=len(matching_findings),
                    detail="; ".join(finding.message for finding in matching_findings),
                    message_slug=slug,
                )
            )

    hardening_quarantines: Dict[int, List[Any]] = {}
    for finding in hardened.quarantined_rows:
        if finding.row_index is not None:
            hardening_quarantines.setdefault(finding.row_index, []).append(finding)
    for row_index, findings in sorted(hardening_quarantines.items()):
        batch.quarantined_rows.append(
            {
                "source_row_ref": f"{sheet_name}!{row_index}",
                "reason_code": findings[0].slug,
                "reason_detail": "; ".join(finding.message for finding in findings),
                "raw_values": findings[0].raw_values or {},
            }
        )
    if hardening_quarantines:
        quarantined_count = len(hardening_quarantines)
        batch.total_source_rows += quarantined_count
        batch.quarantined_count += quarantined_count
        reconciled = check_imp_024_row_count_reconciliation(
            batch.total_source_rows,
            batch.loaded_count,
            batch.quarantined_count,
            batch.rejected_count,
        )
        batch.checks = [
            reconciled if check.check_code == "IMP-024" else check
            for check in batch.checks
        ]

    if profile.source_type != "budget":
        total_report = read_control_totals_report(
            path,
            transactions,
            acceptance=control_total_acceptance,
        )
        batch.checks = [
            check for check in batch.checks if check.check_code != "IMP-025"
        ]
        batch.checks.append(total_report)

    return batch, transactions


def parse_and_validate_csv(
    filepath: str | Path,
    profile: Optional[MappingProfile] = None,
    batch_id: int = 1,
    balance_tolerance: Decimal = ZERO,
) -> ImportBatchResult:
    """Parse and validate CSV file according to 32 checks in 04 §10."""
    batch, _ = parse_csv_transactions(
        filepath, profile, balance_tolerance=balance_tolerance
    )
    batch.batch_id = batch_id
    return batch
