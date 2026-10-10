"""Exception Rules Catalog (Rules 01 to 08) implementation per 06_EXCEPTION_RULES_CATALOG.md.

Implements:
- EXC-001: Duplicate invoice candidate (Catalog EXC-007)
- EXC-002: Unmapped GL account (Catalog EXC-004)
- EXC-003: Inactive cost centre usage (Catalog EXC-005)
- EXC-004: Posting-date vs period mismatch (Catalog EXC-009)
- EXC-005: Unusual negative expense / credit (Catalog EXC-012)
- EXC-006: Missing recurring cost (Catalog EXC-015)
- EXC-007: Material unbudgeted spend (Catalog EXC-017)
- EXC-008: Material variance over threshold (Catalog EXC-018)
"""

from __future__ import annotations

import calendar
import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.engine.calc.math import ZERO, quantize_money
from app.engine.dedupe import iter_candidate_groups, normalise_invoice_no


@dataclass
class RecurringCostRuleItem:
    """Master recurring cost record per 06_EXCEPTION_RULES_CATALOG §4 EXC-015."""

    recurring_id: str
    name: str
    vendor_code: str
    expected_amount: Decimal
    account_code: str | None = None
    cost_center_code: str | None = None
    tolerance_pct: Decimal = Decimal("0.10")  # 10%
    frequency: str = "monthly"
    is_active: bool = True
    last_posted_period: str | None = None


@dataclass
class ApprovalThresholdRuleItem:
    """Effective-dated approval threshold master record for EXC-021."""

    threshold_id: str
    scope: str
    amount_threshold: Decimal
    requires_dual_approval: bool
    effective_from: str
    is_active: bool = True
    company_code: str | None = None
    account_code: str | None = None
    cost_center_code: str | None = None


@dataclass
class Finding:
    """Exception finding raised by a rule per 06_EXCEPTION_RULES_CATALOG §2 and 03_DATA_DICTIONARY §5.2."""

    rule_id: str
    rule_name: str
    severity: str  # High, Medium, Low
    tier: str  # exact, fuzzy
    subject_key: str
    subject_display: str
    amount_at_risk: Decimal
    period_id: str
    owner_role: str
    effective_threshold: str
    detail: str
    evidence_refs: list[str] = field(default_factory=list)
    sample_rows: list[dict[str, Any]] = field(default_factory=list)
    catalog_rule_id: str | None = None
    identity_hash: str = ""

    def __post_init__(self) -> None:
        if not self.identity_hash:
            # SHA-256(rule_id + '|' + subject_key) per §2.2 and 03 §5.2
            key_str = f"{self.rule_id}|{self.subject_key}"
            self.identity_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
        self.amount_at_risk = quantize_money(self.amount_at_risk)


@dataclass
class RuleContext:
    """Context and dependencies passed into exception rule evaluators."""

    transactions: list[Any] = field(default_factory=list)
    # (company_code, account_code, cost_center_code, period_id) -> budget Decimal
    budgets: dict[tuple[str, str, str, str], Decimal] = field(default_factory=dict)
    # (company_code, account_code, cost_center_code) -> annual budget Decimal
    annual_budgets: dict[tuple[str, str, str], Decimal] = field(default_factory=dict)
    # account_code -> dict with metadata (is_mapped, is_placeholder, account_type, etc.)
    dim_accounts: dict[str, dict[str, Any]] = field(default_factory=dict)
    # cost_center_code -> dict with metadata (is_active, owner_name, etc.)
    dim_cost_centers: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Inactive cost centres set
    inactive_cost_centers: set[str] = field(default_factory=set)
    # Recurring costs from master data.
    master_recurring_costs: list[RecurringCostRuleItem] = field(default_factory=list)
    # Persisted import-batch metadata; used by catalog EXC-001 / EXC-002.
    import_batches: list[dict[str, Any]] = field(default_factory=list)
    # Structured IMP-025 details from optional ControlTotals blocks; used by EXC-003.
    control_totals: list[dict[str, Any]] = field(default_factory=list)
    period_id: str = "FY26-P09"
    # Doc 06 line 195 Purity: "no clock beyond an injected `as_of` date".
    # Doc 06 line 422 (EXC-011 Logic): the run date is "injected - never a raw
    # system clock inside the rule".
    # Default None means "resolve from the period under review" (see
    # resolve_as_of_date below); an explicit value from the caller always wins.
    as_of_date: str | None = None
    project_id: str = "sample"
    # Optional DimPeriod-derived period ends, per doc 05 CALC-001: the fiscal
    # calendar is data, not code. When supplied these take precedence over the
    # FYyy-Pmm fallback so a non-January year-start or 4-4-5 calendar resolves
    # from the real calendar rather than an assumption.
    dim_period_end_dates: dict[str, str] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    # Effective-dated approval thresholds from MasterApprovalThreshold (EXC-021).
    master_approval_thresholds: list[ApprovalThresholdRuleItem] = field(default_factory=list)

    @property
    def committed_import_batches(self) -> list[dict[str, Any]]:
        """Import batches whose rows are in the analytic store."""
        return [
            batch
            for batch in self.import_batches
            if str(_get_val(batch, "status", "")).strip().lower() == "committed"
        ]

    def __post_init__(self) -> None:
        # Resolve the injected as_of exactly once, at context construction, so no
        # evaluator ever reads a clock.
        self.as_of_date = resolve_as_of_date(
            period_id=self.period_id,
            explicit_as_of=self.as_of_date,
            dim_period_end_dates=self.dim_period_end_dates,
        )


def _get_val(tx: Any, field_name: str, default: Any = None) -> Any:
    """Retrieve attribute or dict key gracefully."""
    if isinstance(tx, dict):
        return tx.get(field_name, default)
    return getattr(tx, field_name, default)


def _parse_date(date_val: Any) -> date | None:
    """Parse date from date object or ISO string."""
    if not date_val:
        return None
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    try:
        clean_str = str(date_val).strip()[:10]
        return date.fromisoformat(clean_str)
    except Exception:
        return None


def _derive_period_from_date(d: date | None) -> str | None:
    """Derive standard fiscal period FYyy-Pmm from date per CALC-001 (default: period 1 = January)."""
    if d is None:
        return None
    year = d.year
    month = d.month
    fy_str = f"FY{str(year)[-2:]}"
    p_str = f"P{month:02d}"
    return f"{fy_str}-{p_str}"


_GL_SOURCE_TYPES = frozenset(
    {
        "actuals_d365",
        "actuals_gl",
        "actuals_general_ledger",
        "general_ledger",
    }
)


def _transaction_period(tx: Any) -> str:
    """Resolve a transaction's fiscal period from its persisted code or posting date."""
    raw_period = _get_val(tx, "period_code")
    period = str(raw_period).strip() if raw_period is not None else ""
    if period and period.lower() != "none":
        return period
    return _derive_period_from_date(_parse_date(_get_val(tx, "posting_date"))) or ""


def _is_current_period_transaction(tx: Any, context: RuleContext) -> bool:
    """Whether a row belongs to this rule run's period (missing dates stay in-scope)."""
    period = _transaction_period(tx)
    return not period or period == str(context.period_id).strip()


def _import_batch_source_types(context: RuleContext) -> dict[str, str]:
    """Index persisted import metadata for source-appropriate GL rules."""
    return {
        str(_get_val(batch, "batch_id", "")): str(_get_val(batch, "source_type", ""))
        .strip()
        .lower()
        for batch in context.import_batches
        if _get_val(batch, "batch_id") is not None
    }


def _is_general_ledger_transaction(
    tx: Any, context: RuleContext, source_types: dict[str, str] | None = None
) -> bool:
    """Exclude sub-ledger rows from controls whose thresholds are GL-budget scoped."""
    batch_id = _get_val(tx, "import_batch_id")
    if batch_id is None:
        return True
    source_types = source_types if source_types is not None else _import_batch_source_types(context)
    source_type = source_types.get(str(batch_id))
    if not source_type:
        return True
    configured = context.config.get("EXC_general_ledger_source_types", _GL_SOURCE_TYPES)
    if isinstance(configured, str):
        configured = (configured,)
    allowed = {str(value).strip().lower() for value in configured}
    return source_type in allowed


def _is_expense_transaction(context: RuleContext, tx: Any) -> bool:
    """Use DimAccount when available; direct rule contexts may omit the dimension."""
    if not context.dim_accounts:
        return True
    account = str(_get_val(tx, "account_code", "")).strip()
    metadata = context.dim_accounts.get(account)
    return bool(metadata and str(metadata.get("account_type", "")).strip().lower() == "expense")


def _positive_transaction_amount(tx: Any) -> Decimal:
    """Debit-side amount for spend/approval controls; expense credits are not commitments."""
    raw_net = _get_val(tx, "net_amount")
    try:
        net = Decimal(str(raw_net)) if raw_net is not None else ZERO
    except Exception:
        net = ZERO
    if net == ZERO:
        try:
            net = Decimal(str(_get_val(tx, "debit", ZERO))) - Decimal(
                str(_get_val(tx, "credit", ZERO))
            )
        except Exception:
            net = ZERO
    return quantize_money(max(net, ZERO))


def period_end_from_id(period_id: str | None) -> date | None:
    """Resolve an `FYyy-Pmm` period id to its calendar period-end date.

    Doc 05 CALC-002: a transaction belongs to the period whose
    `start_date <= posting_date <= end_date`, so the period end is the natural
    boundary for a period-scoped run date. Doc 05 CALC-001 states the fiscal
    calendar is data, not code; this helper is only the fallback used when no
    `DimPeriod` row is supplied, and it implements the documented default
    (fiscal year start = January, 12 periods). Returns None when the id is not in
    the expected form so callers skip rather than guess.
    """
    if not period_id:
        return None
    m = re.match(r"^FY(\d{2})-P(\d{2})$", str(period_id).strip())
    if not m:
        return None
    month = int(m.group(2))
    if month < 1 or month > 12:
        return None
    year = 2000 + int(m.group(1))
    return date(year, month, calendar.monthrange(year, month)[1])


def resolve_as_of_date(
    period_id: str | None,
    explicit_as_of: Any | None = None,
    dim_period_end_dates: dict[str, Any] | None = None,
) -> str | None:
    """Resolve the injected run date for a rule run, as an ISO date string.

    Precedence, highest first:

    1. `explicit_as_of` - a caller-supplied run date always wins, verbatim. This
       is the doc 06 EXC-011 "the run date, injected" contract: the caller owns
       the value and the engine never second-guesses it.
    2. `dim_period_end_dates[period_id]` - the real calendar per doc 05 CALC-001
       ("the fiscal calendar is data, not code ... every window below is defined
       in terms of DimPeriod rows").
    3. `period_end_from_id(period_id)` - the documented January-start default.

    When no period id can be resolved either, returns None rather than falling
    back to the system clock: doc 06 line 195 forbids a clock, and doc 06 EXC-011
    treats a missing as_of as "the rule cannot evaluate" (evaluate_exc_011 already
    returns no findings in that case) instead of silently inventing a date.
    """
    if explicit_as_of:
        parsed = _parse_date(explicit_as_of)
        # Pass through an explicit value even if unparseable, so a malformed
        # caller input surfaces as a visible rule miss rather than a silent swap.
        return str(explicit_as_of) if parsed is None else parsed.isoformat()

    if dim_period_end_dates and period_id:
        raw = dim_period_end_dates.get(str(period_id).strip())
        if raw:
            parsed = _parse_date(raw)
            if parsed is not None:
                return parsed.isoformat()

    end = period_end_from_id(period_id)
    return end.isoformat() if end else None


# R12 (`BD-001`): invoice-number normalisation now has exactly one implementation, in
# `app/engine/dedupe/normalize.py`, shared with every other duplicate rule. This alias is
# kept because the name is referenced in `06` EXC-007's own wording and by this module's
# callers; it delegates rather than re-implementing.
_normalize_invoice_no = normalise_invoice_no


# ==============================================================================
# Rule 01: EXC-001 Duplicate invoice candidate (Catalog EXC-007)
# ==============================================================================


def evaluate_exc_001(context: RuleContext) -> list[Finding]:
    """EXC-001: Detect duplicate vendor invoice candidates."""
    findings: list[Finding] = []
    date_window_days = int(context.config.get("EXC-001_date_window_days", 90))
    min_amount = Decimal(str(context.config.get("EXC-001_min_amount", "0.00")))
    exact_amount_match = bool(context.config.get("EXC-001_exact_amount_match", True))

    # Block expense-side debit rows by (vendor_code, normalised invoice_no, amount).
    # The rule owns the key and the "≥ 2 rows" structural test; the grouping, candidate
    # selection and deterministic ordering come from `dedupe.blocking` (R12).
    keyed_rows: list[tuple[tuple[str, str, Decimal], Any]] = []
    for tx in context.transactions:
        vendor_code = _get_val(tx, "vendor_code")
        invoice_no = _get_val(tx, "invoice_no")
        debit = quantize_money(_get_val(tx, "debit", ZERO))
        net_amount = quantize_money(_get_val(tx, "net_amount", ZERO))

        # Expense-side debit row
        amount = debit if debit > ZERO else (net_amount if net_amount > ZERO else ZERO)
        if not vendor_code or not invoice_no or amount <= ZERO:
            continue

        norm_inv = normalise_invoice_no(invoice_no)
        if not norm_inv:
            continue

        amt_key = amount if exact_amount_match else ZERO
        keyed_rows.append(((str(vendor_code).strip(), norm_inv, amt_key), tx))

    for (vendor_code, norm_inv, amt_key), tx_list in iter_candidate_groups(
        keyed_rows,
        key_of=lambda item: item[0],
        is_candidate=lambda _key, rows: len(rows) >= 2,
        order_by=lambda group: (group[0][0], group[0][1]),
    ):
        tx_list = [item[1] for item in tx_list]

        dates = [_parse_date(_get_val(tx, "posting_date")) for tx in tx_list]
        valid_dates = [d for d in dates if d is not None]
        if valid_dates:
            min_d = min(valid_dates)
            max_d = max(valid_dates)
            day_gap = (max_d - min_d).days
            if day_gap > date_window_days:
                continue

        first_amt = quantize_money(
            _get_val(tx_list[0], "debit") or _get_val(tx_list[0], "net_amount")
        )
        if first_amt < min_amount:
            continue

        # Subject key format matches catalog and expected_exceptions.csv: V-00931|INV-88213
        orig_invoice = str(_get_val(tx_list[0], "invoice_no")).strip()
        subject_key = f"{vendor_code}|{orig_invoice}"
        evidence_refs = [
            str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
        ]
        vouchers = [str(_get_val(tx, "voucher_no", "")) for tx in tx_list]
        date_strs = [str(_get_val(tx, "posting_date", "")) for tx in tx_list]

        detail = (
            f"Duplicate invoice {orig_invoice} posted on {', '.join(date_strs)} "
            f"across {len(tx_list)} vouchers ({', '.join(vouchers)})"
        )

        findings.append(
            Finding(
                rule_id="EXC-001",
                rule_name="Possible duplicate invoice",
                severity="High",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Duplicate invoice {orig_invoice} for vendor {vendor_code}",
                amount_at_risk=first_amt,
                period_id=context.period_id,
                owner_role="Accounts Payable",
                effective_threshold=f"date_window_days {date_window_days}; exact_amount_match {exact_amount_match}",
                detail=detail,
                evidence_refs=evidence_refs,
                sample_rows=[
                    {
                        "source_row_ref": _get_val(tx, "source_row_ref"),
                        "voucher_no": _get_val(tx, "voucher_no"),
                        "posting_date": _get_val(tx, "posting_date"),
                        "amount": str(
                            quantize_money(_get_val(tx, "debit") or _get_val(tx, "net_amount"))
                        ),
                    }
                    for tx in tx_list
                ],
                catalog_rule_id="EXC-007",
            )
        )

    return findings


# ==============================================================================
# Rule 02: EXC-002 Unmapped GL account (Catalog EXC-004)
# ==============================================================================


def evaluate_exc_002(context: RuleContext) -> list[Finding]:
    """EXC-002: Detect postings to unmapped GL accounts or placeholder dimensions."""
    findings: list[Finding] = []
    min_rows = int(context.config.get("EXC-002_min_rows", 1))
    min_amount = Decimal(str(context.config.get("EXC-002_min_amount", "0.00")))

    # Group unmapped transactions by dimension_type and source_value
    unmapped_account_groups: dict[str, list[Any]] = {}
    unmapped_cc_groups: dict[str, list[Any]] = {}

    for tx in context.transactions:
        acc = str(_get_val(tx, "account_code", "")).strip()
        cc = str(_get_val(tx, "cost_center_code", "")).strip()

        if acc:
            is_unmapped_acc = False
            if context.dim_accounts:
                meta_acc = context.dim_accounts.get(acc)
                if meta_acc is None:
                    is_unmapped_acc = True
                elif meta_acc.get("is_mapped") is False or meta_acc.get("is_placeholder") is True:
                    is_unmapped_acc = True
            else:
                # Pattern matching when dim_accounts master table is not injected
                if any(
                    term in acc.upper() for term in ["TEMP", "UNKNOWN", "UNMAPPED", "DORMANT"]
                ) or acc.startswith("9999"):
                    is_unmapped_acc = True

            if is_unmapped_acc:
                unmapped_account_groups.setdefault(acc, []).append(tx)

        if cc:
            is_unmapped_cc = False
            if context.dim_cost_centers:
                meta_cc = context.dim_cost_centers.get(cc)
                if meta_cc is None:
                    is_unmapped_cc = True
                elif (
                    meta_cc.get("is_mapped") is False
                    or meta_cc.get("is_placeholder") is True
                    or meta_cc.get("owner_name") == "Unassigned"
                    or cc.startswith("CC-999")
                ):
                    is_unmapped_cc = True
            else:
                if any(
                    term in cc.upper() for term in ["TEMP", "UNKNOWN", "UNMAPPED", "UNASSIGNED"]
                ) or cc.startswith("CC-999"):
                    is_unmapped_cc = True

            if is_unmapped_cc:
                unmapped_cc_groups.setdefault(cc, []).append(tx)

    for acc, tx_list in sorted(unmapped_account_groups.items(), key=lambda x: x[0]):
        if len(tx_list) < min_rows:
            continue

        total_amount = sum(
            quantize_money(abs(_get_val(tx, "net_amount", ZERO) or _get_val(tx, "debit", ZERO)))
            for tx in tx_list
        )
        total_amount = quantize_money(total_amount)
        if total_amount < min_amount:
            continue

        subject_key = f"account|{acc}"
        evidence_refs = [
            str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
        ]

        findings.append(
            Finding(
                rule_id="EXC-002",
                rule_name="Unmapped GL account or dimension",
                severity="Medium",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Unmapped GL Account {acc}",
                amount_at_risk=total_amount,
                period_id=context.period_id,
                owner_role="FP&A Analyst",
                effective_threshold=f"min_rows {min_rows}; min_amount ₹{min_amount}",
                detail=f"{len(tx_list)} rows post to unmapped placeholder account {acc} (total ₹{total_amount})",
                evidence_refs=evidence_refs,
                sample_rows=[
                    {
                        "source_row_ref": _get_val(tx, "source_row_ref"),
                        "voucher_no": _get_val(tx, "voucher_no"),
                        "account_code": acc,
                        "amount": str(
                            quantize_money(_get_val(tx, "net_amount") or _get_val(tx, "debit"))
                        ),
                    }
                    for tx in tx_list[:5]
                ],
                catalog_rule_id="EXC-004",
            )
        )

    for cc, tx_list in sorted(unmapped_cc_groups.items(), key=lambda x: x[0]):
        if len(tx_list) < min_rows:
            continue

        total_amount = sum(
            quantize_money(abs(_get_val(tx, "net_amount", ZERO) or _get_val(tx, "debit", ZERO)))
            for tx in tx_list
        )
        total_amount = quantize_money(total_amount)
        if total_amount < min_amount:
            continue

        subject_key = f"cost_center|{cc}"
        evidence_refs = [
            str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
        ]

        findings.append(
            Finding(
                rule_id="EXC-002",
                rule_name="Unmapped GL account or dimension",
                severity="Medium",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Unmapped Cost Center {cc}",
                amount_at_risk=total_amount,
                period_id=context.period_id,
                owner_role="FP&A Analyst",
                effective_threshold=f"min_rows {min_rows}; min_amount ₹{min_amount}",
                detail=f"{len(tx_list)} rows post to unmapped placeholder cost center {cc} (total ₹{total_amount})",
                evidence_refs=evidence_refs,
                sample_rows=[
                    {
                        "source_row_ref": _get_val(tx, "source_row_ref"),
                        "voucher_no": _get_val(tx, "voucher_no"),
                        "cost_center_code": cc,
                        "amount": str(
                            quantize_money(_get_val(tx, "net_amount") or _get_val(tx, "debit"))
                        ),
                    }
                    for tx in tx_list[:5]
                ],
                catalog_rule_id="EXC-004",
            )
        )

    return findings


# ==============================================================================
# Rule 03: EXC-003 Inactive cost centre usage (Catalog EXC-005)
# ==============================================================================


def evaluate_exc_003(context: RuleContext) -> list[Finding]:
    """EXC-003: Detect postings to inactive, dormant or closed cost centres."""
    findings: list[Finding] = []
    min_amount = Decimal(str(context.config.get("EXC-003_min_amount", "0.00")))
    ignore_credit_only = bool(context.config.get("EXC-003_ignore_credit_only", False))

    inactive_cc_set: set[str] = set(context.inactive_cost_centers)
    for cc, meta in context.dim_cost_centers.items():
        if meta.get("is_active") is False:
            inactive_cc_set.add(cc)

    groups: dict[str, list[Any]] = {}

    for tx in context.transactions:
        cc = str(_get_val(tx, "cost_center_code", "")).strip()
        if not cc:
            continue

        if cc in inactive_cc_set or "INACTIVE" in cc.upper() or cc == "CC-950":
            net_amt = quantize_money(_get_val(tx, "net_amount", ZERO))
            debit = quantize_money(_get_val(tx, "debit", ZERO))
            credit = quantize_money(_get_val(tx, "credit", ZERO))
            if ignore_credit_only and debit == ZERO and credit > ZERO:
                continue
            if net_amt != ZERO or debit != ZERO or credit != ZERO:
                groups.setdefault(cc, []).append(tx)

    for cc, tx_list in sorted(groups.items(), key=lambda x: x[0]):
        total_amount = sum(
            quantize_money(abs(_get_val(tx, "net_amount", ZERO) or _get_val(tx, "debit", ZERO)))
            for tx in tx_list
        )
        total_amount = quantize_money(total_amount)
        if total_amount < min_amount:
            continue

        subject_key = f"cost_center|{cc}"
        evidence_refs = [
            str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
        ]

        findings.append(
            Finding(
                rule_id="EXC-003",
                rule_name="Inactive cost centre usage",
                severity="Low",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Inactive Cost Centre {cc}",
                amount_at_risk=total_amount,
                period_id=context.period_id,
                owner_role="Cost Centre Owner",
                effective_threshold=f"min_amount ₹{min_amount}; ignore_credit_only {ignore_credit_only}",
                detail=f"{cc} (marked inactive) receives {len(tx_list)} postings in {context.period_id} totalling ₹{total_amount}",
                evidence_refs=evidence_refs,
                sample_rows=[
                    {
                        "source_row_ref": _get_val(tx, "source_row_ref"),
                        "voucher_no": _get_val(tx, "voucher_no"),
                        "cost_center_code": cc,
                        "amount": str(
                            quantize_money(_get_val(tx, "net_amount") or _get_val(tx, "debit"))
                        ),
                    }
                    for tx in tx_list[:5]
                ],
                catalog_rule_id="EXC-005",
            )
        )

    return findings


# ==============================================================================
# Rule 04: EXC-004 Posting-date vs period mismatch (Catalog EXC-009)
# ==============================================================================


def evaluate_exc_004(context: RuleContext) -> list[Finding]:
    """EXC-004: Detect transactions whose source-declared period disagrees with posting date."""
    findings: list[Finding] = []
    min_rows = int(context.config.get("EXC-004_min_rows", 1))
    min_amount = Decimal(str(context.config.get("EXC-004_min_amount", "0.00")))
    batches_by_id = {
        str(_get_val(batch, "batch_id")): batch
        for batch in context.import_batches
        if _get_val(batch, "batch_id") is not None
    }

    # Group by (company_code, declared_period, derived_period)
    groups: dict[tuple[str, str, str], list[Any]] = {}

    for tx in context.transactions:
        posting_d = _parse_date(_get_val(tx, "posting_date"))
        if not posting_d:
            continue

        derived_period = _derive_period_from_date(posting_d)
        raw_vals = _get_val(tx, "raw_values") or {}
        declared_period = (
            _get_val(tx, "period_code")
            or raw_vals.get("period")
            or raw_vals.get("source_period")
            or context.period_id
        )

        company_code = str(_get_val(tx, "company_code", "IN01")).strip()

        if declared_period and derived_period and declared_period != derived_period:
            key = (company_code, declared_period, derived_period)
            groups.setdefault(key, []).append(tx)

    for (comp, decl_p, deriv_p), tx_list in sorted(
        groups.items(), key=lambda x: (x[0][0], x[0][1])
    ):
        if len(tx_list) < min_rows:
            continue

        total_amount = sum(
            quantize_money(abs(_get_val(tx, "net_amount", ZERO) or _get_val(tx, "debit", ZERO)))
            for tx in tx_list
        )
        total_amount = quantize_money(total_amount)
        if total_amount < min_amount:
            continue

        first_transaction = tx_list[0]
        internal_batch_id = _get_val(first_transaction, "import_batch_id")
        batch_record = batches_by_id.get(str(internal_batch_id))
        batch_reference = (
            _get_val(batch_record, "external_batch_ref")
            or _get_val(first_transaction, "batch_id")
            or internal_batch_id
            or "batch_040"
        )
        batch_id = str(batch_reference)
        first_row_ref = str(_get_val(first_transaction, "source_row_ref") or "row_00882")
        subject_key = f"{batch_id}|{first_row_ref}"
        evidence_refs = [
            str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
        ]

        findings.append(
            Finding(
                rule_id="EXC-004",
                rule_name="Posting date / fiscal period mismatch",
                severity="High",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Period Mismatch {decl_p} vs {deriv_p}",
                amount_at_risk=total_amount,
                period_id=context.period_id,
                owner_role="GL Accountant",
                effective_threshold=f"min_rows {min_rows}; min_amount ₹{min_amount}",
                detail=f"{len(tx_list)} rows declare source period {decl_p} but posting dates fall in {deriv_p} (total ₹{total_amount})",
                evidence_refs=evidence_refs,
                sample_rows=[
                    {
                        "source_row_ref": _get_val(tx, "source_row_ref"),
                        "voucher_no": _get_val(tx, "voucher_no"),
                        "posting_date": str(_get_val(tx, "posting_date")),
                        "amount": str(
                            quantize_money(_get_val(tx, "net_amount") or _get_val(tx, "debit"))
                        ),
                    }
                    for tx in tx_list[:5]
                ],
                catalog_rule_id="EXC-009",
            )
        )

    return findings


# ==============================================================================
# Rule 05: EXC-005 Unusual negative expense / credit (Catalog EXC-012)
# ==============================================================================


def evaluate_exc_005(context: RuleContext) -> list[Finding]:
    """EXC-005: Detect unusual negative expenses/credits to expense accounts."""
    findings: list[Finding] = []
    min_credit_amount = Decimal(str(context.config.get("EXC-005_min_credit_amount", "500000.00")))
    offset_ratio_threshold = Decimal(str(context.config.get("EXC-005_offset_ratio", "0.90")))

    # Filter and group by (company_code, account_code, cost_center_code) within the same period (doc 06 EXC-012)
    groups: dict[tuple[str, str, str], list[Any]] = {}

    current_period = str(context.period_id).strip() if context.period_id else None

    for tx in context.transactions:
        tx_p = _get_val(tx, "period_code")
        tx_period = str(tx_p).strip() if tx_p is not None else ""
        if not tx_period or tx_period == "None":
            p_date = _parse_date(_get_val(tx, "posting_date"))
            if p_date:
                tx_period = _derive_period_from_date(p_date) or ""

        if current_period and tx_period and tx_period != current_period:
            continue

        acc = str(_get_val(tx, "account_code", "")).strip()
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        cc = str(_get_val(tx, "cost_center_code", "")).strip()

        # Target expense accounts: starting with 5 or 6, or meta account_type=='EXPENSE'
        meta = context.dim_accounts.get(acc, {})
        acc_type = meta.get("account_type", "").upper()
        is_expense = (acc_type == "EXPENSE") or (acc.startswith("5") or acc.startswith("6"))

        if is_expense:
            groups.setdefault((comp, acc, cc), []).append(tx)

    for (comp, acc, cc), tx_list in sorted(
        groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])
    ):
        credit_rows: list[Any] = []
        total_credit_abs = ZERO
        total_debit = ZERO

        for tx in tx_list:
            net_amt = quantize_money(_get_val(tx, "net_amount", ZERO))
            debit = quantize_money(_get_val(tx, "debit", ZERO))
            credit = quantize_money(_get_val(tx, "credit", ZERO))

            if net_amt < ZERO or credit > debit:
                c_amt = abs(net_amt) if net_amt < ZERO else (credit - debit)
                total_credit_abs += c_amt
                credit_rows.append(tx)
            else:
                d_amt = net_amt if net_amt > ZERO else (debit - credit)
                total_debit += d_amt

        if total_credit_abs >= min_credit_amount:
            offset_ratio = (
                (total_debit / total_credit_abs) if total_credit_abs > ZERO else Decimal("1.0")
            )
            if offset_ratio < offset_ratio_threshold:
                subject_key = f"{comp}|{acc}|{cc}"
                evidence_refs = [
                    str(_get_val(tx, "source_row_ref", f"row_{i}"))
                    for i, tx in enumerate(credit_rows, 1)
                ]
                pct_offset = quantize_money(offset_ratio * Decimal("100"))

                findings.append(
                    Finding(
                        rule_id="EXC-005",
                        rule_name="Unusual negative expense / credit",
                        severity="Medium",
                        tier="exact",
                        subject_key=subject_key,
                        subject_display=f"Negative Expense on {acc}/{cc}",
                        amount_at_risk=total_credit_abs,
                        period_id=context.period_id,
                        owner_role="Cost Centre Owner",
                        effective_threshold=f"min_credit_amount ₹{min_credit_amount}; offset_ratio {offset_ratio_threshold}",
                        detail=(
                            f"Unusual negative expense credits ₹{total_credit_abs} offset only "
                            f"₹{total_debit} ({pct_offset}%), below {offset_ratio_threshold * 100}%"
                        ),
                        evidence_refs=evidence_refs,
                        sample_rows=[
                            {
                                "source_row_ref": _get_val(tx, "source_row_ref"),
                                "voucher_no": _get_val(tx, "voucher_no"),
                                "account_code": acc,
                                "cost_center_code": cc,
                                "amount": str(
                                    quantize_money(
                                        _get_val(tx, "net_amount") or _get_val(tx, "credit")
                                    )
                                ),
                            }
                            for tx in credit_rows[:5]
                        ],
                        catalog_rule_id="EXC-012",
                    )
                )

    return findings


# ==============================================================================
# Rule 06: EXC-006 Missing recurring cost (Catalog EXC-015)
# ==============================================================================


def evaluate_exc_006(context: RuleContext) -> list[Finding]:
    """EXC-006: Detect missing expected recurring expenses (rent, software, subscriptions)."""
    findings: list[Finding] = []
    default_tolerance_pct = Decimal(str(context.config.get("EXC-006_tolerance_pct", "0.10")))
    skip_if_period_missing = bool(context.config.get("EXC-006_skip_if_period_missing", True))

    if skip_if_period_missing and not context.transactions:
        return findings

    for item in sorted(context.master_recurring_costs, key=lambda x: (x.vendor_code, x.name)):
        if not item.is_active:
            continue

        tolerance = Decimal(str(getattr(item, "tolerance_pct", default_tolerance_pct)))
        expected = quantize_money(item.expected_amount)

        # Match transactions by vendor and optional account/cost_centre
        candidates = [
            tx
            for tx in context.transactions
            if str(_get_val(tx, "vendor_code", "")).strip() == item.vendor_code
            and (
                not item.account_code
                or str(_get_val(tx, "account_code", "")).strip() == item.account_code
            )
            and (
                not item.cost_center_code
                or str(_get_val(tx, "cost_center_code", "")).strip() == item.cost_center_code
            )
        ]

        matched = False
        closest_candidate: Decimal | None = None
        closest_diff: Decimal | None = None

        for tx in candidates:
            net_amt = quantize_money(_get_val(tx, "net_amount", ZERO))
            debit = quantize_money(_get_val(tx, "debit", ZERO))
            credit = quantize_money(_get_val(tx, "credit", ZERO))
            val = abs(net_amt) if net_amt != ZERO else (debit if debit != ZERO else credit)
            val = quantize_money(val)

            diff = abs(val - expected)
            if expected > ZERO and (diff / expected) <= tolerance:
                matched = True
                break

            if closest_diff is None or diff < closest_diff:
                closest_diff = diff
                closest_candidate = val

        if not matched:
            name_slug = item.name.replace(" ", "_")
            subject_key = f"{item.vendor_code}|{name_slug}"
            diff_text = (
                f"nearest candidate ₹{closest_candidate} ({quantize_money((abs(closest_candidate - expected) / expected) * Decimal('100'))}% diff)"
                if closest_candidate is not None and expected > ZERO
                else "no matching postings found"
            )

            detail = (
                f"Monthly recurring {item.name} ₹{expected} missing in {context.period_id} "
                f"({diff_text})"
            )

            evidence_refs = [
                str(_get_val(tx, "source_row_ref", f"row_{i}"))
                for i, tx in enumerate(candidates, 1)
            ]

            findings.append(
                Finding(
                    rule_id="EXC-006",
                    rule_name="Missing recurring cost",
                    severity="High",
                    tier="fuzzy",
                    subject_key=subject_key,
                    subject_display=f"Missing recurring {item.name} ({item.vendor_code})",
                    amount_at_risk=expected,
                    period_id=context.period_id,
                    owner_role="Accounts Payable",
                    effective_threshold=f"tolerance_pct {quantize_money(tolerance * Decimal('100'))}%",
                    detail=detail,
                    evidence_refs=evidence_refs,
                    sample_rows=[
                        {
                            "vendor_code": item.vendor_code,
                            "expected_amount": str(expected),
                            "tolerance_pct": str(tolerance),
                        }
                    ],
                    catalog_rule_id="EXC-015",
                )
            )

    return findings


# ==============================================================================
# Rule 07: EXC-007 Material unbudgeted spend (Catalog EXC-017)
# ==============================================================================


def evaluate_exc_007(context: RuleContext) -> list[Finding]:
    """EXC-007: Detect material spend on accounts or cost centres with zero budget for the year."""
    findings: list[Finding] = []
    materiality_amount = Decimal(str(context.config.get("EXC-007_materiality_amount", "500000.00")))

    # Group current-period GL expense rows by (company_code, account_code, cost_center_code).
    groups: dict[tuple[str, str, str], list[Any]] = {}
    source_types = _import_batch_source_types(context)

    for tx in context.transactions:
        if (
            not _is_current_period_transaction(tx, context)
            or not _is_general_ledger_transaction(tx, context, source_types)
            or not _is_expense_transaction(context, tx)
        ):
            continue
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        acc = str(_get_val(tx, "account_code", "")).strip()
        cc = str(_get_val(tx, "cost_center_code", "")).strip()
        if not acc:
            continue
        groups.setdefault((comp, acc, cc), []).append(tx)

    for (comp, acc, cc), tx_list in sorted(
        groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])
    ):
        actual = sum(_positive_transaction_amount(tx) for tx in tx_list)
        actual = quantize_money(actual)

        # Check annual budget: if key has annual budget > 0 or period budget > 0, it's not unbudgeted
        ann_budget = context.annual_budgets.get((comp, acc, cc))
        if ann_budget is None:
            # Check period budgets across all periods
            matching_budgets = [
                b
                for (c, a, cc_code, p), b in context.budgets.items()
                if c == comp and a == acc and cc_code == cc
            ]
            ann_budget = sum(matching_budgets, ZERO) if matching_budgets else ZERO

        if ann_budget == ZERO and actual >= materiality_amount:
            subject_key = f"{comp}|{acc}|{cc}"
            evidence_refs = [
                str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
            ]

            findings.append(
                Finding(
                    rule_id="EXC-007",
                    rule_name="Material unbudgeted spend",
                    severity="High",
                    tier="fuzzy",
                    subject_key=subject_key,
                    subject_display=f"Unbudgeted Spend on {acc}/{cc}",
                    amount_at_risk=actual,
                    period_id=context.period_id,
                    owner_role="FP&A Analyst",
                    effective_threshold=f"materiality_amount ₹{materiality_amount}",
                    detail=f"Spend of ₹{actual} on {acc}/{cc} with zero FY26 budget line",
                    evidence_refs=evidence_refs,
                    sample_rows=[
                        {
                            "source_row_ref": _get_val(tx, "source_row_ref"),
                            "voucher_no": _get_val(tx, "voucher_no"),
                            "account_code": acc,
                            "cost_center_code": cc,
                            "actual_amount": str(actual),
                        }
                        for tx in tx_list[:5]
                    ],
                    catalog_rule_id="EXC-017",
                )
            )

    return findings


# ==============================================================================
# Rule 08: EXC-008 Material variance over threshold (Catalog EXC-018)
# ==============================================================================


def evaluate_exc_008(context: RuleContext) -> list[Finding]:
    """EXC-008: Detect material variances satisfying mandatory AND-test (amount AND %)."""
    findings: list[Finding] = []
    materiality_pct = Decimal(str(context.config.get("EXC-008_materiality_pct", "0.02")))  # 2%
    absolute_floor = Decimal(str(context.config.get("EXC-008_absolute_floor", "500000.00")))
    pct_threshold = Decimal(str(context.config.get("EXC-008_pct_threshold", "5.0")))  # 5.0%

    # Aggregate actuals by (company_code, account_code, cost_center_code) for context.period_id
    actuals: dict[tuple[str, str, str], Decimal] = {}
    actual_txs: dict[tuple[str, str, str], list[Any]] = {}

    source_types = _import_batch_source_types(context)
    for tx in context.transactions:
        if (
            not _is_current_period_transaction(tx, context)
            or not _is_general_ledger_transaction(tx, context, source_types)
            or not _is_expense_transaction(context, tx)
        ):
            continue
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        acc = str(_get_val(tx, "account_code", "")).strip()
        cc = str(_get_val(tx, "cost_center_code", "")).strip()
        if not acc:
            continue
        key = (comp, acc, cc)
        amt = quantize_money(_get_val(tx, "net_amount", ZERO) or _get_val(tx, "debit", ZERO))
        actuals[key] = quantize_money(actuals.get(key, ZERO) + amt)
        actual_txs.setdefault(key, []).append(tx)

    # Check expense-account budgets for the current period. Balance-sheet and
    # revenue budgets are outside this expense-variance rule's scope.
    checked_keys: set[tuple[str, str, str]] = set(actuals.keys())
    for comp, acc, cc, p in context.budgets.keys():
        metadata = context.dim_accounts.get(acc) if context.dim_accounts else None
        if p == context.period_id and (
            not context.dim_accounts
            or (metadata and str(metadata.get("account_type", "")).strip().lower() == "expense")
        ):
            checked_keys.add((comp, acc, cc))

    for key in sorted(checked_keys, key=lambda x: (x[0], x[1], x[2])):
        comp, acc, cc = key
        actual = actuals.get(key, ZERO)
        budget = quantize_money(context.budgets.get((comp, acc, cc, context.period_id), ZERO))

        # If budget is 0, skip (handled by unbudgeted spend rule EXC-007)
        if budget == ZERO:
            continue

        variance = quantize_money(actual - budget)
        abs_variance = abs(variance)
        abs_budget = abs(budget)

        variance_pct = quantize_money((variance / abs_budget) * Decimal("100"))
        abs_variance_pct = abs(variance_pct)

        effective_materiality_threshold = max(
            absolute_floor, quantize_money(materiality_pct * abs_budget)
        )

        # Mandatory AND test per §4 EXC-018:
        # |variance| >= max(absolute_floor, materiality_pct * |budget|) AND |variance_pct| >= pct_threshold
        if abs_variance >= effective_materiality_threshold and abs_variance_pct >= pct_threshold:
            subject_key = f"{comp}|{acc}|{cc}"
            tx_list = actual_txs.get(key, [])
            evidence_refs = [
                str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)
            ]

            sign_var = "+" if variance > ZERO else ""
            sign_pct = "+" if variance_pct > ZERO else ""
            pct_display = f"{materiality_pct * Decimal('100')}%"

            findings.append(
                Finding(
                    rule_id="EXC-008",
                    rule_name="Material variance (amount and %)",
                    severity="High",
                    tier="fuzzy",
                    subject_key=subject_key,
                    subject_display=f"Material Variance on {acc}/{cc}",
                    amount_at_risk=abs_variance,
                    period_id=context.period_id,
                    owner_role="FP&A Analyst",
                    effective_threshold=f"materiality {pct_display} or ₹{absolute_floor}; AND pct {pct_threshold}%",
                    detail=(
                        f"Canonical case: Var {sign_var}₹{abs_variance} ({sign_pct}{abs_variance_pct}%) "
                        f"satisfies materiality AND-test (threshold ₹{effective_materiality_threshold} & {pct_threshold}%)"
                    ),
                    evidence_refs=evidence_refs,
                    sample_rows=[
                        {
                            "company_code": comp,
                            "account_code": acc,
                            "cost_center_code": cc,
                            "actual": str(actual),
                            "budget": str(budget),
                            "variance": str(variance),
                            "variance_pct": str(variance_pct),
                        }
                    ],
                    catalog_rule_id="EXC-018",
                )
            )

    return findings


# ==============================================================================
# Aggregate Evaluator
# ==============================================================================

RULES_REGISTRY = [
    {
        "rule_id": "EXC-001",
        "catalog_id": "EXC-007",
        "name": "Possible duplicate invoice",
        "evaluator": evaluate_exc_001,
    },
    {
        "rule_id": "EXC-002",
        "catalog_id": "EXC-004",
        "name": "Unmapped GL account or dimension",
        "evaluator": evaluate_exc_002,
    },
    {
        "rule_id": "EXC-003",
        "catalog_id": "EXC-005",
        "name": "Inactive cost centre usage",
        "evaluator": evaluate_exc_003,
    },
    {
        "rule_id": "EXC-004",
        "catalog_id": "EXC-009",
        "name": "Posting date / fiscal period mismatch",
        "evaluator": evaluate_exc_004,
    },
    {
        "rule_id": "EXC-005",
        "catalog_id": "EXC-012",
        "name": "Unusual negative expense / credit",
        "evaluator": evaluate_exc_005,
    },
    {
        "rule_id": "EXC-006",
        "catalog_id": "EXC-015",
        "name": "Missing recurring cost",
        "evaluator": evaluate_exc_006,
    },
    {
        "rule_id": "EXC-007",
        "catalog_id": "EXC-017",
        "name": "Material unbudgeted spend",
        "evaluator": evaluate_exc_007,
    },
    {
        "rule_id": "EXC-008",
        "catalog_id": "EXC-018",
        "name": "Material variance (amount and %)",
        "evaluator": evaluate_exc_008,
    },
]


BATCH_01_08_EVALUATORS = (
    evaluate_exc_001,
    evaluate_exc_002,
    evaluate_exc_003,
    evaluate_exc_004,
    evaluate_exc_005,
    evaluate_exc_006,
    evaluate_exc_007,
    evaluate_exc_008,
)


def evaluate_all(context: RuleContext) -> list[Finding]:
    """Execute all Rules 01 to 08 deterministically."""
    all_findings: list[Finding] = []
    for evaluator in BATCH_01_08_EVALUATORS:
        all_findings.extend(evaluator(context))
    return all_findings


# Convenience entrypoint per implementation contract
def evaluate(context: RuleContext) -> list[Finding]:
    """Convenience alias for evaluate_all per contract §2.12."""
    return evaluate_all(context)
