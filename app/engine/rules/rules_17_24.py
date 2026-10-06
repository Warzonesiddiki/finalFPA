"""Exception Rules Catalog (Rules 17 to 24) per 06_EXCEPTION_RULES_CATALOG.md.

Implements:
- EXC-019: Cumulative overrun vs annual budget
- EXC-020: Budget coverage gap (entity x account x period matrix)
- EXC-021: Amount crossing approval threshold (single vs dual threshold)
- EXC-022: Round-number manual journal (multiple of 10,000, > 500k)
- EXC-023: Voucher-level imbalance (debits != credits at voucher grain)
- EXC-024: Suspense / clearing account residual balance

NOTE ON ID MAPPING: catalog EXC-017 (Material unbudgeted spend) and catalog
EXC-018 (Material variance) are already implemented in ``rules_01_08`` as
``evaluate_exc_007`` / ``evaluate_exc_008`` (engine ids EXC-007 / EXC-008 carry
``catalog_rule_id`` "EXC-017" / "EXC-018"). They are deliberately NOT
re-implemented here, to avoid double-raising findings for plantings P17/P18.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from app.engine.calc.math import quantize_money, ZERO
from app.engine.rules.rules_01_08 import (
    Finding,
    RuleContext,
    _derive_period_from_date,
    _get_val,
    _import_batch_source_types,
    _is_current_period_transaction,
    _is_expense_transaction,
    _is_general_ledger_transaction,
    _parse_date,
    _positive_transaction_amount,
)


# ==============================================================================
# Shared helpers for the budget-relationship family (EXC-019, EXC-020)
# ==============================================================================

def _fy_of(period_id: Optional[str]) -> str:
    """'FY26-P09' -> 'FY26'. The fiscal year is implied by the period (catalog EXC-019)."""
    if not period_id:
        return ""
    return period_id.split("-P")[0]


def _period_num(period_id: Optional[str]) -> int:
    """'FY26-P09' -> 9. Returns -1 for anything unparseable so it sorts first / is skipped."""
    if not period_id or "-P" not in period_id:
        return -1
    try:
        return int(period_id.split("-P")[1])
    except (IndexError, ValueError):
        return -1


def _open_periods(context: RuleContext) -> List[str]:
    """Open periods of the fiscal year of ``context.period_id``, up to and including it.

    Per catalog EXC-020 these are the periods the budget should cover for the
    year in progress (IMP-031: a period is open once it has started).
    """
    fy = _fy_of(context.period_id)
    as_of = _period_num(context.period_id)
    periods = {
        p
        for (_, _, _, p) in context.budgets.keys()
        if _fy_of(p) == fy and 0 < _period_num(p) <= as_of
    }
    return sorted(periods, key=_period_num)


# ==============================================================================
# EXC-019: Cumulative overrun vs annual budget (Catalog EXC-019)
# ==============================================================================

def evaluate_exc_019(context: RuleContext) -> List[Finding]:
    """EXC-019: Detect a line that is still inside its monthly budget but has
    already exceeded its share of the ANNUAL budget.

    Catalog 06 EXC-019. Raise when ALL of:
      ytd_actual  > ytd_budget x (1 + ytd_tolerance_pct)      [5%]
      ytd_actual >= annual_budget x annual_consumption_pct    [80%]
      ytd_actual  > amount_floor = max(absolute_floor, materiality_pct x annual_budget)

    Severity Medium, tier fuzzy, owner FP&A Analyst.
    Registers on the YTD rows for that key.
    """
    findings: List[Finding] = []
    cfg = context.config
    ytd_tolerance_pct = Decimal(str(cfg.get("EXC-019_ytd_tolerance_pct", "0.05")))  # 5%
    annual_consumption_pct = Decimal(str(cfg.get("EXC-019_annual_consumption_pct", "0.80")))  # 80%
    materiality_pct = Decimal(str(cfg.get("materiality_pct", "0.02")))  # 2%
    absolute_floor = Decimal(str(cfg.get("absolute_floor", "500000.00")))

    open_periods = _open_periods(context)
    if not open_periods:
        return findings
    as_of = _period_num(context.period_id)

    # YTD actuals by key, counting only posted rows inside the open periods (CALC-004).
    ytd_actual: Dict[Tuple[str, str, str], Decimal] = defaultdict(lambda: ZERO)
    key_rows: Dict[Tuple[str, str, str], List[Any]] = defaultdict(list)
    for tx in context.transactions:
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        acc = str(_get_val(tx, "account_code", "")).strip()
        cc = str(_get_val(tx, "cost_center_code", "")).strip()
        if not acc:
            continue
        posted = _derive_period_from_date(_parse_date(_get_val(tx, "posting_date")))
        if posted is None or _fy_of(posted) != _fy_of(context.period_id):
            continue
        if _period_num(posted) > as_of:
            continue
        amt = quantize_money(_get_val(tx, "net_amount", ZERO) or _get_val(tx, "debit", ZERO))
        key = (comp, acc, cc)
        ytd_actual[key] = quantize_money(ytd_actual[key] + amt)
        key_rows[key].append(tx)

    # Candidate keys = anything with spend YTD, or any budget line in the open periods.
    checked: Set[Tuple[str, str, str]] = set(ytd_actual.keys())
    for (comp, acc, cc, p) in context.budgets.keys():
        if p in open_periods:
            checked.add((comp, acc, cc))

    for key in sorted(checked):
        comp, acc, cc = key
        actual = ytd_actual.get(key, ZERO)

        # This rule is for an overrun against an active budget, not a missing or
        # zero current-period allocation (EXC-017/020 own those conditions).
        current_period_budget = context.budgets.get((comp, acc, cc, context.period_id))
        if current_period_budget is None or quantize_money(current_period_budget) <= ZERO:
            continue

        # YTD budget = sum of the budget lines for the open periods.
        ytd_budget = quantize_money(
            sum((context.budgets.get((comp, acc, cc, p), ZERO) for p in open_periods), ZERO)
        )
        if ytd_budget <= ZERO:
            # Without a positive YTD budget there is no "still inside its monthly
            # budget" baseline; zero-coverage pairs are EXC-020's job.
            continue

        # Annual budget: prefer the supplied annual figure, else the full-FY sum.
        annual_budget = context.annual_budgets.get((comp, acc, cc))
        if annual_budget is None:
            annual_budget = quantize_money(
                sum(
                    (
                        v
                        for (c2, a2, cc2, p), v in context.budgets.items()
                        if (c2, a2, cc2) == (comp, acc, cc) and _fy_of(p) == _fy_of(context.period_id)
                    ),
                    ZERO,
                )
            )
        annual_budget = quantize_money(annual_budget)
        if annual_budget <= ZERO:
            continue

        amount_floor = max(absolute_floor, quantize_money(materiality_pct * abs(annual_budget)))
        consumption_pct = quantize_money((actual / annual_budget) * Decimal("100"))

        # Gate 1: annual consumption already past the 80% mark.
        if actual < quantize_money(annual_budget * annual_consumption_pct):
            continue
        # Gate 2: amount must clear the floor.
        if abs(actual) <= amount_floor:
            continue
        # Gate 3: YTD actual over YTD budget by more than the tolerance.
        if actual <= quantize_money(ytd_budget * (Decimal("1") + ytd_tolerance_pct)):
            continue

        ytd_variance = quantize_money(actual - ytd_budget)
        ytd_variance_pct = quantize_money((ytd_variance / ytd_budget) * Decimal("100"))
        effective_threshold = (
            f"ytd tolerance {ytd_tolerance_pct * 100}% AND consumption >= "
            f"{annual_consumption_pct * 100}% AND amount > {amount_floor}"
        )
        detail = (
            f"YTD +INR {ytd_variance:,.2f} (+{ytd_variance_pct}%) "
            f"| annual budget INR {annual_budget:,.2f} "
            f"| {consumption_pct}% of annual budget consumed by {context.period_id}"
        )
        rows = key_rows.get(key, [])
        evidence_refs = [
            str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(rows, 1)
        ]

        findings.append(
            Finding(
                rule_id="EXC-019",
                catalog_rule_id="EXC-019",
                rule_name="Cumulative overrun vs annual budget",
                severity="Medium",
                tier="fuzzy",
                subject_key=f"{comp}|{acc}|{cc}",
                subject_display=f"{comp} / {acc} / {cc} YTD {context.period_id}",
                amount_at_risk=quantize_money(abs(actual)),
                period_id=context.period_id,
                owner_role="FP&A Analyst",
                effective_threshold=effective_threshold,
                detail=detail,
                evidence_refs=evidence_refs,
                sample_rows=rows[:5],
            )
        )

    return findings


# ==============================================================================
# EXC-020: Budget coverage gap (Catalog EXC-020)
# ==============================================================================

def evaluate_exc_020(context: RuleContext) -> List[Finding]:
    """EXC-020: Make the SHAPE of the budget visible - entity x account x period
    cells with no budget line, so a variance report is never silently incomplete.

    Catalog 06 EXC-020. Build the coverage matrix over (entity x account) for the
    open periods of the fiscal year (IMP-031). One exception per pair whose
    coverage is partial, or absent while actuals exist.

    ``include_no_actuals_pairs`` defaults to false: gaps where nothing is spent
    are informational and belong on the Check screen, not the register.
    Severity Medium, tier exact, owner FP&A Analyst.
    """
    findings: List[Finding] = []
    cfg = context.config
    min_gap_periods = int(cfg.get("EXC-020_min_coverage_gap_periods", 1))
    include_no_actuals = bool(cfg.get("EXC-020_include_no_actuals_pairs", False))

    open_periods = _open_periods(context)
    if not open_periods:
        return findings

    # Budget matrix: (entity, account) -> {period: amount} across the open periods.
    budget_by_pair: Dict[Tuple[str, str], Dict[str, Decimal]] = defaultdict(dict)
    for (comp, acc, cc, p), amount in context.budgets.items():
        if p in open_periods:
            budget_by_pair[(comp, acc)][p] = quantize_money(
                budget_by_pair[(comp, acc)].get(p, ZERO) + amount
            )

    # Which (entity, account) pairs have spend inside the open periods?
    actual_pairs: Set[Tuple[str, str]] = set()
    for tx in context.transactions:
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        acc = str(_get_val(tx, "account_code", "")).strip()
        if not acc:
            continue
        posted = _derive_period_from_date(_parse_date(_get_val(tx, "posting_date")))
        if posted is None or _fy_of(posted) != _fy_of(context.period_id):
            continue
        if posted in open_periods:
            actual_pairs.add((comp, acc))

    pairs = set(budget_by_pair.keys()) | actual_pairs
    for pair in sorted(pairs):
        comp, acc = pair
        covered = budget_by_pair.get(pair, {})
        missing = [p for p in open_periods if p not in covered]
        if not missing or len(missing) == len(open_periods) and not covered:
            continue
        if len(missing) < min_gap_periods:
            continue

        # Pairs with no spend at all are informational only (P29 precision control).
        if pair not in actual_pairs and not include_no_actuals:
            continue

        coverage_pct = quantize_money(
            (Decimal(len(covered)) / Decimal(len(open_periods))) * Decimal("100")
        )
        p_start = missing[0].split("-P")[1]
        p_end = missing[-1].split("-P")[1]
        span = f"P{p_start}-P{p_end}" if p_start != p_end else f"P{p_start}"
        # "Registers on the budget matrix for the pair": the budget actually loaded.
        budget_total = quantize_money(sum(covered.values(), ZERO))

        findings.append(
            Finding(
                rule_id="EXC-020",
                catalog_rule_id="EXC-020",
                rule_name="Budget coverage gap",
                severity="Medium",
                tier="exact",
                subject_key=f"{comp}|{acc}|{span}",
                subject_display=f"{comp} / {acc} budget coverage",
                amount_at_risk=budget_total,
                period_id=context.period_id,
                owner_role="FP&A Analyst",
                effective_threshold=(
                    f"coverage gap >= {min_gap_periods} open period(s); "
                    f"pairs without actuals excluded={not include_no_actuals}"
                ),
                detail=(
                    f"coverage {coverage_pct}% | missing "
                    f"{', '.join(missing)} | loaded budget INR {budget_total:,.2f}"
                ),
                evidence_refs=[f"budget:{comp}|{acc}|{p}={covered[p]}" for p in sorted(covered)],
                sample_rows=[],
            )
        )

    return findings


# ==============================================================================
# EXC-021: Amount crossing approval threshold (Catalog EXC-021)
# ==============================================================================

def evaluate_exc_021(context: RuleContext) -> List[Finding]:
    """EXC-021: Detect expense transactions at or above approval thresholds."""
    findings: List[Finding] = []
    # Default company approval thresholds
    dual_threshold = Decimal(str(context.config.get("EXC-021_dual_threshold", "2500000.00")))
    single_threshold = Decimal(str(context.config.get("EXC-021_single_threshold", "500000.00")))

    groups: Dict[Tuple[str, str, str], List[Any]] = {}
    source_types = _import_batch_source_types(context)

    for tx in context.transactions:
        if (
            not _is_current_period_transaction(tx, context)
            or not _is_general_ledger_transaction(tx, context, source_types)
            or not _is_expense_transaction(context, tx)
        ):
            continue
        amt = _positive_transaction_amount(tx)
        if amt >= single_threshold:
            comp = str(_get_val(tx, "company_code", "IN01")).strip()
            vch = str(_get_val(tx, "voucher_no", "")).strip()
            thresh_type = "dual" if amt >= dual_threshold else "single"
            groups.setdefault((comp, vch, thresh_type), []).append(tx)

    for (comp, vch, thresh_type), tx_list in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1])):
        total_amt = sum(_positive_transaction_amount(tx) for tx in tx_list)
        req_approval = "dual approval required" if thresh_type == "dual" else "single approval required"
        target_amt = dual_threshold if thresh_type == "dual" else single_threshold
        subject_key = f"{comp}|{vch}|{thresh_type}"
        evidence_refs = [str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)]

        findings.append(
            Finding(
                rule_id="EXC-021",
                rule_name="Amount crossing approval threshold",
                severity="High",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Voucher {vch} exceeds {thresh_type} approval threshold",
                amount_at_risk=total_amt,
                period_id=context.period_id,
                owner_role="Controller",
                effective_threshold=f"{thresh_type} threshold ₹{target_amt}",
                detail=f"Voucher {vch} contains transactions totalling ₹{total_amt} ≥ ₹{target_amt} ({req_approval})",
                evidence_refs=evidence_refs,
                catalog_rule_id="EXC-021",
            )
        )

    return findings


# ==============================================================================
# EXC-022: Round-number manual journal (Catalog EXC-022)
# ==============================================================================

def evaluate_exc_022(context: RuleContext) -> List[Finding]:
    """EXC-022: Detect large round-number manual journals."""
    findings: List[Finding] = []
    round_unit = Decimal(str(context.config.get("EXC-022_round_unit", "10000.00")))
    round_floor = Decimal(str(context.config.get("EXC-022_round_floor", "500000.00")))

    # Use current-period GL expense debits as the voucher amount; balancing
    # credits and sub-ledger rows are not additional journal exposure.
    vouchers: Dict[Tuple[str, str], List[Any]] = {}
    source_types = _import_batch_source_types(context)
    for tx in context.transactions:
        if (
            not _is_current_period_transaction(tx, context)
            or not _is_general_ledger_transaction(tx, context, source_types)
            or not _is_expense_transaction(context, tx)
        ):
            continue
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        vch = str(_get_val(tx, "voucher_no", "")).strip()
        if vch:
            vouchers.setdefault((comp, vch), []).append(tx)

    for (comp, vch), tx_list in sorted(vouchers.items(), key=lambda x: (x[0][0], x[0][1])):
        total_amt = sum(_positive_transaction_amount(tx) for tx in tx_list)
        if total_amt >= round_floor and (total_amt % round_unit) == ZERO:
            multiple = int(total_amt / round_unit)
            subject_key = f"{comp}|{vch}"
            evidence_refs = [str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)]

            findings.append(
                Finding(
                    rule_id="EXC-022",
                    rule_name="Round-number manual journal",
                    severity="Low",
                    tier="fuzzy",
                    subject_key=subject_key,
                    subject_display=f"Round-number journal {vch}",
                    amount_at_risk=total_amt,
                    period_id=context.period_id,
                    owner_role="GL Accountant",
                    effective_threshold=f"round_unit ₹{round_unit}; floor ₹{round_floor}",
                    detail=f"Voucher {vch} is an exact round number of ₹{round_unit} x {multiple} totalling ₹{total_amt}",
                    evidence_refs=evidence_refs,
                    catalog_rule_id="EXC-022",
                )
            )

    return findings


# ==============================================================================
# EXC-023: Voucher-level imbalance (Catalog EXC-023)
# ==============================================================================

def evaluate_exc_023(context: RuleContext) -> List[Finding]:
    """EXC-023: Detect vouchers where debits != credits."""
    findings: List[Finding] = []
    tolerance = Decimal(str(context.config.get("EXC-023_tolerance", "0.00")))
    min_lines = int(context.config.get("EXC-023_min_lines", 2))

    vouchers: Dict[Tuple[str, str], List[Any]] = {}
    source_types = _import_batch_source_types(context)
    for tx in context.transactions:
        if (
            not _is_current_period_transaction(tx, context)
            or not _is_general_ledger_transaction(tx, context, source_types)
        ):
            continue
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        vch = str(_get_val(tx, "voucher_no", "")).strip()
        if vch:
            vouchers.setdefault((comp, vch), []).append(tx)

    for (comp, vch), tx_list in sorted(vouchers.items(), key=lambda x: (x[0][0], x[0][1])):
        if len(tx_list) < min_lines:
            continue

        tot_debit = sum(quantize_money(_get_val(tx, "debit", ZERO)) for tx in tx_list)
        tot_credit = sum(quantize_money(_get_val(tx, "credit", ZERO)) for tx in tx_list)
        diff = quantize_money(abs(tot_debit - tot_credit))

        if diff > tolerance:
            subject_key = f"{comp}|{vch}"
            evidence_refs = [str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)]

            findings.append(
                Finding(
                    rule_id="EXC-023",
                    rule_name="Voucher-level imbalance",
                    severity="High",
                    tier="exact",
                    subject_key=subject_key,
                    subject_display=f"Voucher imbalance on {vch}",
                    amount_at_risk=diff,
                    period_id=context.period_id,
                    owner_role="GL Accountant",
                    effective_threshold=f"tolerance ₹{tolerance}",
                    detail=f"Voucher {vch} debits ₹{tot_debit} vs credits ₹{tot_credit} (imbalance: ₹{diff}) across {len(tx_list)} lines",
                    evidence_refs=evidence_refs,
                    catalog_rule_id="EXC-023",
                )
            )

    return findings


# ==============================================================================
# EXC-024: Suspense / clearing account residual (Catalog EXC-024)
# ==============================================================================

def evaluate_exc_024(context: RuleContext) -> List[Finding]:
    """EXC-024: Detect uncleared balances on accounts tagged suspense or clearing."""
    findings: List[Finding] = []
    residual_floor = Decimal(str(context.config.get("EXC-024_residual_floor", "100000.00")))
    suspense_accounts = context.config.get("suspense_accounts", {"1999", "9999", "SUSPENSE"})

    accounts: Dict[Tuple[str, str], List[Any]] = {}
    for tx in context.transactions:
        acc = str(_get_val(tx, "account_code", "")).strip()
        comp = str(_get_val(tx, "company_code", "IN01")).strip()
        if acc in suspense_accounts:
            accounts.setdefault((comp, acc), []).append(tx)

    for (comp, acc), tx_list in sorted(accounts.items(), key=lambda x: (x[0][0], x[0][1])):
        net_total = sum(quantize_money(_get_val(tx, "net_amount", ZERO)) for tx in tx_list)
        abs_net = abs(net_total)
        if abs_net >= residual_floor:
            subject_key = f"{comp}|{acc}|{context.period_id}"
            evidence_refs = [str(_get_val(tx, "source_row_ref", f"row_{i}")) for i, tx in enumerate(tx_list, 1)]

            findings.append(
                Finding(
                    rule_id="EXC-024",
                    rule_name="Suspense / clearing account residual",
                    severity="High",
                    tier="exact",
                    subject_key=subject_key,
                    subject_display=f"Residual on suspense account {acc}",
                    amount_at_risk=abs_net,
                    period_id=context.period_id,
                    owner_role="Controller",
                    effective_threshold=f"floor ₹{residual_floor}",
                    detail=f"Suspense account {acc} carries net uncleared residual of ₹{net_total} across {len(tx_list)} rows in {context.period_id}",
                    evidence_refs=evidence_refs,
                    catalog_rule_id="EXC-024",
                )
            )

    return findings


# ==============================================================================
# Batch dispatcher: catalog rules EXC-017..EXC-024
# ==============================================================================
# EXC-017 and EXC-018 are intentionally absent: they are implemented in
# rules_01_08 as evaluate_exc_007 / evaluate_exc_008 with catalog_rule_id
# "EXC-017" / "EXC-018". Including them here as well would double-raise
# findings for plantings P17 / P18.

BATCH_17_24_EVALUATORS: List[Any] = [
    evaluate_exc_019,
    evaluate_exc_020,
    evaluate_exc_021,
    evaluate_exc_022,
    evaluate_exc_023,
    evaluate_exc_024,
]


def evaluate_all_17_24(context: RuleContext) -> List[Finding]:
    """Evaluate the EXC-017..EXC-024 batch and return all findings."""
    all_findings: List[Finding] = []
    for evaluator in BATCH_17_24_EVALUATORS:
        all_findings.extend(evaluator(context))
    return all_findings
