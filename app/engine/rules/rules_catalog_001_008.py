"""Catalog rules EXC-001, EXC-002, EXC-003, EXC-006 and EXC-008.

The historical ``rules_01_08`` module contains eight engine-numbered functions
whose ``Finding.catalog_rule_id`` values map to different catalog entries. These
five evaluators implement the catalog IDs that were absent from the batch rather
than reusing those engine-numbered functions.

All money arithmetic stays in ``Decimal``. Import-integrity rules consume the
persisted batch / validation metadata on ``RuleContext``; an absent optional
control-total block disables EXC-003 with a notice instead of passing silently.
"""

from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal
from typing import Any

from app.engine.calc.math import ZERO, quantize_money
from app.engine.dedupe import count_distinct, iter_candidate_groups
from app.engine.rules.rules_01_08 import Finding, RuleContext, _get_val


def _value(item: Any, name: str, default: Any = None) -> Any:
    """Read either a dict-shaped metadata row or an object attribute."""
    return _get_val(item, name, default)


def _text(item: Any, name: str, default: str = "") -> str:
    value = _value(item, name, default)
    return default if value is None else str(value).strip()


def _money(value: Any, default: Decimal = ZERO) -> Decimal:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return quantize_money(value)
    return quantize_money(Decimal(str(value)))


def _batch_id(batch: Any) -> str | None:
    value = _value(batch, "batch_id")
    return None if value is None else str(value)


def _committed_batches(context: RuleContext) -> dict[str, Any]:
    return {
        batch_id: batch
        for batch in context.import_batches
        if (batch_id := _batch_id(batch)) is not None
        and _text(batch, "status").lower() == "committed"
    }


def _period_order(period_code: Any) -> tuple[int, int] | None:
    """Return (fiscal year, period number) for the documented FYyy-Pnn form."""
    match = re.fullmatch(r"FY(\d{2,4})-P(\d{1,2})", str(period_code or "").strip(), re.IGNORECASE)
    if not match:
        return None
    year = int(match.group(1))
    if year < 100:
        year += 2000
    return year, int(match.group(2))


def _transaction_period(tx: Any, context: RuleContext) -> tuple[int, int] | None:
    period = _period_order(_value(tx, "period_code"))
    if period is not None:
        return period

    posting_date = _text(tx, "posting_date")[:10]
    if len(posting_date) != 10:
        return None
    try:
        year, month = int(posting_date[:4]), int(posting_date[5:7])
    except ValueError:
        return None

    # Prefer the injected fiscal calendar where available; it is data, not code.
    calendar_matches = []
    for code, end_date in context.dim_period_end_dates.items():
        period_order = _period_order(code)
        end_text = str(end_date)[:10]
        if period_order and len(end_text) == 10 and posting_date <= end_text:
            calendar_matches.append((end_text, period_order))
    if calendar_matches:
        return min(calendar_matches, key=lambda item: item[0])[1]
    return year, month


def _in_run_fiscal_year_ytd(tx: Any, context: RuleContext) -> bool:
    run_period = _period_order(context.period_id)
    tx_period = _transaction_period(tx, context)
    if run_period is None or tx_period is None:
        return False
    return tx_period[0] == run_period[0] and tx_period[1] <= run_period[1]


def _in_run_period(tx: Any, context: RuleContext, run_period: tuple[int, int]) -> bool:
    return _transaction_period(tx, context) == run_period


def _period_budget_keys(context: RuleContext, fiscal_year: int) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for key in context.budgets:
        if len(key) != 4:
            continue
        company, account, _cost_center, period = key
        order = _period_order(period)
        if order is not None and order[0] == fiscal_year:
            keys.add((str(company), str(account)))
    # ``annual_budgets`` is already scoped to the loaded fiscal year by the
    # repository. Keep zero-valued entries: presence of a line, not its amount,
    # is the coverage fact EXC-006 needs.
    for key in context.annual_budgets:
        if len(key) == 3:
            company, account, _cost_center = key
            keys.add((str(company), str(account)))
    return keys


def _batch_subject(batch: Any, batch_id: str) -> str:
    """Build a stable batch identity when the source supplies one."""
    explicit_subject = _text(batch, "subject_key")
    if explicit_subject:
        return explicit_subject

    external_ref = _text(batch, "external_batch_ref")
    namespace = _text(batch, "subject_namespace")
    if external_ref and namespace:
        return f"{external_ref}|{namespace}"
    return external_ref or batch_id


# ---------------------------------------------------------------------------
# EXC-001 — Import imbalance
# ---------------------------------------------------------------------------


def evaluate_catalog_exc_001(context: RuleContext) -> list[Finding]:
    """Raise once for each committed import batch with a non-zero imbalance."""
    findings: list[Finding] = []
    configured_tolerance = context.config.get("EXC-001_balance_tolerance")

    for batch in context.import_batches:
        if _text(batch, "status").lower() != "committed":
            continue
        batch_id = _batch_id(batch)
        if batch_id is None:
            continue

        debit = _money(_value(batch, "total_debit"))
        credit = _money(_value(batch, "total_credit"))
        recorded_imbalance = _value(batch, "net_imbalance")
        imbalance = (
            _money(recorded_imbalance)
            if recorded_imbalance is not None
            else quantize_money(debit - credit)
        )
        if imbalance == ZERO and debit != credit:
            imbalance = quantize_money(debit - credit)
        if imbalance == ZERO:
            continue

        tolerance_value = _value(batch, "balance_tolerance")
        if tolerance_value is None:
            tolerance_value = configured_tolerance
        tolerance = _money(tolerance_value, ZERO)
        batch_transactions = [
            tx for tx in context.transactions if str(_value(tx, "import_batch_id", "")) == batch_id
        ]
        top_rows = sorted(
            batch_transactions,
            key=lambda tx: abs(_money(_value(tx, "debit")) - _money(_value(tx, "credit"))),
            reverse=True,
        )[:5]
        sample_rows = [
            {
                "voucher_no": _text(tx, "voucher_no"),
                "source_row_ref": _text(tx, "source_row_ref"),
                "debit": str(_money(_value(tx, "debit"))),
                "credit": str(_money(_value(tx, "credit"))),
            }
            for tx in top_rows
        ]
        evidence_refs = [
            _text(tx, "source_row_ref") for tx in top_rows if _text(tx, "source_row_ref")
        ]
        file_name = _text(batch, "file_name", "import batch")
        subject_key = _batch_subject(batch, batch_id)
        total_debit = debit
        total_credit = credit
        findings.append(
            Finding(
                rule_id="EXC-001",
                catalog_rule_id="EXC-001",
                rule_name="Import imbalance (debits ≠ credits)",
                severity="High",
                tier="exact",
                subject_key=subject_key,
                subject_display=f"Unbalanced import batch {batch_id}: {file_name}",
                amount_at_risk=abs(imbalance),
                period_id=_text(batch, "period_id", context.period_id) or context.period_id,
                owner_role="GL Accountant",
                effective_threshold=f"balance_tolerance ₹{tolerance}",
                detail=(
                    f"Committed batch {batch_id} has debit ₹{total_debit}, "
                    f"credit ₹{total_credit}, and net imbalance ₹{imbalance}; "
                    f"import tolerance was ₹{tolerance}. "
                    "The largest contributing rows are listed below."
                ),
                evidence_refs=evidence_refs,
                sample_rows=sample_rows,
            )
        )

    return findings


# ---------------------------------------------------------------------------
# EXC-002 — Cross-batch duplicate rows
# ---------------------------------------------------------------------------


def _transaction_amount(tx: Any) -> Decimal:
    net = _money(_value(tx, "net_amount"))
    if net != ZERO:
        return abs(net)
    return abs(_money(_value(tx, "debit")) - _money(_value(tx, "credit")))


def _batch_sort_key(batch: Any) -> tuple[str, str]:
    created_at = _text(batch, "created_at")
    batch_id = _batch_id(batch) or ""
    return created_at, batch_id


def _cross_batch_findings_for_key(
    context: RuleContext,
    batch_by_id: dict[str, Any],
    key_builder,
    *,
    secondary: bool,
    matched_row_pairs: set[tuple[int, int]],
) -> list[Finding]:
    grouped: dict[tuple[Any, ...], dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
    for tx in context.transactions:
        batch_id = str(_value(tx, "import_batch_id", ""))
        if batch_id not in batch_by_id:
            continue
        key = key_builder(tx)
        if key is not None:
            grouped[key][batch_id].append(tx)

    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    ordered_ids = sorted(batch_by_id, key=lambda bid: _batch_sort_key(batch_by_id[bid]))
    position = {batch_id: index for index, batch_id in enumerate(ordered_ids)}

    for key, by_batch in grouped.items():
        present = [batch_id for batch_id in ordered_ids if by_batch.get(batch_id)]
        for later_id in present:
            later_rows = by_batch[later_id]
            previous_ids = [
                earlier_id for earlier_id in present if position[earlier_id] < position[later_id]
            ]
            if not previous_ids:
                continue
            for later_tx in later_rows:
                matching_old = []
                for earlier_id in previous_ids:
                    for earlier_tx in by_batch[earlier_id]:
                        pair = (id(earlier_tx), id(later_tx))
                        if secondary and pair in matched_row_pairs:
                            continue
                        matching_old.append((earlier_id, earlier_tx, pair))
                if not matching_old:
                    continue

                # One catalog finding per overlapping business subject, even if
                # the same later row appears in more than one earlier batch.
                if secondary:
                    vendor, invoice, posting_date, amount = key
                    subject_key = f"{vendor}|{invoice}|{posting_date}|{amount}"
                else:
                    company, voucher, line_no = key
                    subject_key = f"{company}|{voucher}|{line_no}"
                candidate_key = (subject_key, later_id)
                candidate = candidates.setdefault(
                    candidate_key,
                    {
                        "earlier": {},
                        "later": {},
                        "key_type": "invoice" if secondary else "voucher",
                    },
                )
                candidate["later"][id(later_tx)] = later_tx
                for earlier_id, earlier_tx, pair in matching_old:
                    candidate["earlier"].setdefault(id(earlier_tx), (earlier_id, earlier_tx))
                    if not secondary:
                        matched_row_pairs.add(pair)

    findings: list[Finding] = []
    for (subject_key, later_id), candidate in sorted(candidates.items()):
        later_batch = batch_by_id[later_id]
        earlier_entries = sorted(
            candidate["earlier"].values(),
            key=lambda item: _batch_sort_key(batch_by_id[item[0]]),
        )
        if not earlier_entries:
            continue
        earlier_id = earlier_entries[0][0]
        earlier_batch = batch_by_id[earlier_id]
        older_date = _text(earlier_batch, "created_at", "unknown import date")
        later_rows = list(candidate["later"].values())
        overlap_amount = quantize_money(sum((_transaction_amount(tx) for tx in later_rows), ZERO))
        evidence_refs = sorted(
            {
                _text(tx, "source_row_ref")
                for _old_id, tx in earlier_entries + [(later_id, tx) for tx in later_rows]
                if _text(tx, "source_row_ref")
            }
        )
        sample_rows = []
        for old_id, old_tx in earlier_entries:
            sample_rows.append(
                {
                    "batch_id": old_id,
                    "source_row_ref": _text(old_tx, "source_row_ref"),
                    "voucher_no": _text(old_tx, "voucher_no"),
                    "posting_date": _text(old_tx, "posting_date"),
                    "amount": str(_transaction_amount(old_tx)),
                }
            )
        for later_tx in later_rows:
            sample_rows.append(
                {
                    "batch_id": later_id,
                    "source_row_ref": _text(later_tx, "source_row_ref"),
                    "voucher_no": _text(later_tx, "voucher_no"),
                    "posting_date": _text(later_tx, "posting_date"),
                    "amount": str(_transaction_amount(later_tx)),
                }
            )

        findings.append(
            Finding(
                rule_id="EXC-002",
                catalog_rule_id="EXC-002",
                rule_name="Cross-batch duplicate rows",
                severity="High",
                tier="exact",
                subject_key=subject_key,
                subject_display=(f"Overlapping {candidate['key_type']} row {subject_key}"),
                amount_at_risk=overlap_amount,
                period_id=_text(later_batch, "period_id", context.period_id) or context.period_id,
                owner_role="GL Accountant",
                effective_threshold="min_overlap_rows 1; include_voided_batches false",
                detail=(
                    "This batch overlaps earlier committed batch "
                    f"{earlier_id} (imported {older_date}); "
                    f"{len(later_rows)} row(s) matched the {candidate['key_type']} key."
                ),
                evidence_refs=evidence_refs,
                sample_rows=sample_rows,
            )
        )
    return findings


def evaluate_catalog_exc_002(context: RuleContext) -> list[Finding]:
    """Compare committed rows across batches using both documented business keys."""
    batch_by_id = _committed_batches(context)
    if len(batch_by_id) < 2:
        return []

    def voucher_key(tx: Any) -> tuple[Any, ...] | None:
        company = _text(tx, "company_code")
        voucher = _text(tx, "voucher_no")
        line_no = _value(tx, "line_no")
        if not company or not voucher or line_no is None:
            return None
        return company, voucher, int(line_no)

    def invoice_key(tx: Any) -> tuple[Any, ...] | None:
        vendor = _text(tx, "vendor_code")
        invoice = _text(tx, "invoice_no").upper()
        posting_date = _text(tx, "posting_date")[:10]
        if not vendor or not invoice or not posting_date:
            return None
        amount = _transaction_amount(tx)
        return vendor, invoice, posting_date, f"{amount:.2f}"

    matched_row_pairs: set[tuple[int, int]] = set()
    findings = _cross_batch_findings_for_key(
        context,
        batch_by_id,
        voucher_key,
        secondary=False,
        matched_row_pairs=matched_row_pairs,
    )
    findings.extend(
        _cross_batch_findings_for_key(
            context,
            batch_by_id,
            invoice_key,
            secondary=True,
            matched_row_pairs=matched_row_pairs,
        )
    )
    # The same identity can match a voucher and invoice key only when the source
    # has repeated rows that are distinct by one key; keep one deterministic hit.
    unique: dict[str, Finding] = {}
    for finding in findings:
        unique.setdefault(finding.subject_key, finding)
    return [unique[key] for key in sorted(unique)]


evaluate_catalog_exc_002.REQUIRED_INPUT_COUNTS = {"committed_import_batches": 2}
evaluate_catalog_exc_002.REQUIRED_INPUT_NOTICES = {
    "committed_import_batches": "Requires at least two committed batches",
}


# ---------------------------------------------------------------------------
# EXC-003 — Cross-system tie-out variance
# ---------------------------------------------------------------------------


def evaluate_catalog_exc_003(context: RuleContext) -> list[Finding]:
    """Compare loaded totals with persisted optional client control totals."""
    findings: list[Finding] = []
    batch_by_id = {
        batch_id: batch
        for batch in context.import_batches
        if (batch_id := _batch_id(batch)) is not None
    }
    committed_ids = set(_committed_batches(context))
    configured_tolerance = context.config.get("EXC-003_control_total_tolerance", ZERO)

    for total in context.control_totals:
        batch_id = str(_value(total, "batch_id", ""))
        if batch_id and batch_by_id and batch_id not in committed_ids:
            continue
        supplied = _money(_value(total, "supplied_total"))
        loaded = _money(_value(total, "loaded_total"))
        variance = quantize_money(loaded - supplied)
        tolerance_value = _value(total, "tolerance", configured_tolerance)
        tolerance = _money(tolerance_value)
        if abs(variance) <= tolerance:
            continue

        scope = _text(total, "scope", _text(total, "control_total_scope", "file"))
        batch_record = batch_by_id.get(batch_id)
        stable_batch_ref = (
            _text(total, "external_batch_ref")
            or _text(batch_record, "external_batch_ref")
            or batch_id
        )
        subject_key = _text(total, "subject_key") or f"{stable_batch_ref}|{scope}"
        findings.append(
            Finding(
                rule_id="EXC-003",
                catalog_rule_id="EXC-003",
                rule_name="Cross-system tie-out variance",
                severity="High",
                tier="exact",
                subject_key=subject_key,
                subject_display=(f"Control-total variance for batch {batch_id} ({scope})"),
                amount_at_risk=variance,
                period_id=_text(total, "period_id", context.period_id) or context.period_id,
                owner_role="Controller",
                effective_threshold=f"control_total_tolerance ₹{tolerance}",
                detail=(
                    f"File-level control total supplied ₹{supplied}; "
                    f"loaded total ₹{loaded}; variance ₹{variance} "
                    f"(loaded minus supplied), beyond tolerance ₹{tolerance}."
                ),
                evidence_refs=[_text(total, "source_row_ref")]
                if _text(total, "source_row_ref")
                else [],
                sample_rows=[dict(total)] if isinstance(total, dict) else [],
            )
        )
    return findings


evaluate_catalog_exc_003.REQUIRED_INPUTS = ("control_totals",)
evaluate_catalog_exc_003.REQUIRED_INPUT_NOTICES = {
    "control_totals": "No control-totals block supplied",
}


# ---------------------------------------------------------------------------
# EXC-006 — Entity/account actuals without a fiscal-year budget line
# ---------------------------------------------------------------------------


def evaluate_catalog_exc_006(context: RuleContext) -> list[Finding]:
    """Raise material actuals at the configured scope with no annual budget line."""
    run_period = _period_order(context.period_id)
    if run_period is None:
        return []

    excluded_accounts_config = context.config.get("EXC-006_excluded_accounts", ())
    if isinstance(excluded_accounts_config, str):
        excluded_accounts_config = (excluded_accounts_config,)
    excluded_accounts = {str(account).strip() for account in excluded_accounts_config}
    scope_grain = str(context.config.get("EXC-006_scope_grain", "entity_account")).strip().lower()
    if scope_grain not in {"entity", "account", "entity_account"}:
        raise ValueError(f"Unsupported EXC-006 scope_grain: {scope_grain}")

    ytd_rows: list[tuple[Any, str, str, Decimal]] = []
    entity_ytd: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for tx in context.transactions:
        if not _in_run_fiscal_year_ytd(tx, context):
            continue
        company = _text(tx, "company_code")
        account = _text(tx, "account_code")
        if not company or not account or account in excluded_accounts:
            continue
        net = _money(_value(tx, "net_amount"))
        amount = abs(net)
        if amount == ZERO:
            continue
        ytd_rows.append((tx, company, account, amount))
        entity_ytd[company] = quantize_money(entity_ytd[company] + amount)

    if not ytd_rows:
        return []

    budgeted_entity_accounts = _period_budget_keys(context, run_period[0])
    groups: dict[tuple[str, ...], list[tuple[Any, str, str, Decimal]]] = defaultdict(list)
    for record in ytd_rows:
        _tx, company, account, _amount = record
        if scope_grain == "entity":
            if any(b_company == company for b_company, _b_account in budgeted_entity_accounts):
                continue
            group_key = (company,)
        elif scope_grain == "account":
            if any(b_account == account for _b_company, b_account in budgeted_entity_accounts):
                continue
            group_key = (account,)
        else:
            if (company, account) in budgeted_entity_accounts:
                continue
            group_key = (company, account)
        groups[group_key].append(record)

    absolute_floor = _money(
        context.config.get(
            "EXC-006_absolute_floor",
            context.config.get("absolute_floor", "500000.00"),
        )
    )
    materiality_pct = Decimal(
        str(
            context.config.get(
                "EXC-006_materiality_pct",
                context.config.get("materiality_pct", "0.02"),
            )
        )
    )
    configured_minimum = context.config.get("EXC-006_min_ytd_amount")

    findings: list[Finding] = []
    for key, records in sorted(groups.items()):
        companies = {row[1] for row in records}
        entity_amount = quantize_money(
            sum((entity_ytd.get(company, ZERO) for company in companies), ZERO)
        )
        threshold = (
            _money(configured_minimum)
            if configured_minimum is not None
            else max(absolute_floor, quantize_money(materiality_pct * entity_amount))
        )
        ytd_amount = quantize_money(sum((row[3] for row in records), ZERO))
        if ytd_amount < threshold:
            continue

        accounts = sorted({row[2] for row in records})
        tx_rows = [row[0] for row in records]
        if scope_grain == "entity":
            subject_key = f"entity|{key[0]}"
            subject_display = f"Entity {key[0]} has actuals without budget coverage"
        elif scope_grain == "account":
            subject_key = f"account|{key[0]}"
            subject_display = f"Account {key[0]} has actuals without budget coverage"
        else:
            subject_key = f"entity_account|{key[0]}|{key[1]}"
            subject_display = (
                f"Entity {key[0]} / account {key[1]} has actuals without budget coverage"
            )

        evidence_refs = sorted(
            {_text(tx, "source_row_ref") for tx in tx_rows if _text(tx, "source_row_ref")}
        )
        sample_rows = [
            {
                "source_row_ref": _text(tx, "source_row_ref"),
                "company_code": _text(tx, "company_code"),
                "account_code": _text(tx, "account_code"),
                "period_code": _text(tx, "period_code"),
                "net_amount": str(_money(_value(tx, "net_amount"))),
            }
            for tx in tx_rows[:20]
        ]
        findings.append(
            Finding(
                rule_id="EXC-006",
                catalog_rule_id="EXC-006",
                rule_name="Entity or account with actuals but no budget",
                severity="Medium",
                tier="exact",
                subject_key=subject_key,
                subject_display=subject_display,
                amount_at_risk=ytd_amount,
                period_id=context.period_id,
                owner_role="FP&A Analyst",
                effective_threshold=(
                    f"min_ytd_amount ₹{threshold}; scope_grain {scope_grain}; "
                    f"fiscal_year FY{run_period[0] % 100:02d}"
                ),
                detail=(
                    f"YTD actuals are ₹{ytd_amount} across {len(tx_rows)} posting(s), "
                    "with no budget line for the fiscal year. "
                    f"Accounts: {', '.join(accounts)}. "
                    f"Materiality threshold: ₹{threshold}."
                ),
                evidence_refs=evidence_refs,
                sample_rows=sample_rows,
            )
        )
    return findings


evaluate_catalog_exc_006.REQUIRED_INPUTS = ("annual_budgets",)


# ---------------------------------------------------------------------------
# EXC-008 — Possible duplicate voucher line
# ---------------------------------------------------------------------------


def evaluate_catalog_exc_008(context: RuleContext) -> list[Finding]:
    """Find identical same-day lines posted in different vouchers."""
    run_period = _period_order(context.period_id)
    if run_period is None:
        return []

    # Block by the catalog's EXC-008 key: (company, account, absolute amount, posting date,
    # cost centre, net sign). The rule owns the key, the in-period filter and the
    # "at least two distinct vouchers" requirement; `dedupe.blocking` owns the grouping and
    # deterministic ordering so this rule and EXC-007 block the same way (R12).
    BlockKey = tuple[str, str, Decimal, str, str, int]
    keyed: list[tuple[BlockKey, Any]] = []
    for tx in context.transactions:
        if not _in_run_period(tx, context, run_period):
            continue
        company = _text(tx, "company_code")
        account = _text(tx, "account_code")
        cost_center = _text(tx, "cost_center_code")
        posting_date = _text(tx, "posting_date")[:10]
        voucher = _text(tx, "voucher_no")
        net = _money(_value(tx, "net_amount"))
        amount = abs(net)
        if not company or not account or not posting_date or not voucher or amount == ZERO:
            continue
        sign = 1 if net > ZERO else -1
        keyed.append(((company, account, amount, posting_date, cost_center, sign), tx))

    absolute_floor = _money(
        context.config.get(
            "EXC-008_absolute_floor",
            context.config.get("absolute_floor", "500000.00"),
        )
    )
    materiality_pct = Decimal(
        str(
            context.config.get(
                "EXC-008_materiality_pct",
                context.config.get("materiality_pct", "0.02"),
            )
        )
    )
    configured_minimum = context.config.get("EXC-008_min_amount")
    account_budget: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    annual_budget_accounts: set[tuple[str, str]] = set()
    for (company, account, _cost_center), amount in context.annual_budgets.items():
        key = (str(company), str(account))
        annual_budget_accounts.add(key)
        account_budget[key] = quantize_money(account_budget[key] + _money(amount))
    for (company, account, _cost_center, period), amount in context.budgets.items():
        period_order = _period_order(period)
        key = (str(company), str(account))
        if period_order and period_order[0] == run_period[0] and key not in annual_budget_accounts:
            account_budget[key] = quantize_money(account_budget[key] + _money(amount))

    findings: list[Finding] = []
    for (
        company,
        account,
        amount,
        posting_date,
        cost_center,
        _sign,
    ), found in iter_candidate_groups(
        keyed,
        key_of=lambda item: item[0],
        # `06` EXC-008: `require_different_voucher = true`. Rows in the same voucher are
        # normal multi-line postings and are excluded -- the requirement that removes the
        # largest class of false positives.
        is_candidate=lambda _key, rows: (
            count_distinct(rows, lambda item: _text(item[1], "voucher_no")) >= 2
        ),
        order_by=lambda group: group[0],
    ):
        rows = [item[1] for item in found]
        # Presentation only: the voucher list the finding shows the reviewer. Every row here
        # already passed the `not voucher: continue` filter above, so no blank can appear.
        vouchers = sorted({_text(tx, "voucher_no") for tx in rows})
        budget = abs(account_budget.get((company, account), ZERO))
        threshold = (
            _money(configured_minimum)
            if configured_minimum is not None
            else max(absolute_floor, quantize_money(materiality_pct * budget))
        )
        if amount < threshold:
            continue

        subject_key = f"{company}|{account}|{amount:.2f}|{posting_date}|{cost_center}"
        evidence_refs = sorted(
            {_text(tx, "source_row_ref") for tx in rows if _text(tx, "source_row_ref")}
        )
        sample_rows = [
            {
                "source_row_ref": _text(tx, "source_row_ref"),
                "voucher_no": _text(tx, "voucher_no"),
                "posting_date": posting_date,
                "company_code": company,
                "account_code": account,
                "cost_center_code": cost_center,
                "amount": str(amount),
            }
            for tx in rows
        ]
        findings.append(
            Finding(
                rule_id="EXC-008",
                catalog_rule_id="EXC-008",
                rule_name="Possible duplicate voucher line",
                severity="Medium",
                tier="exact",
                subject_key=subject_key,
                subject_display=(
                    f"Possible duplicate line: {company} / {account} / "
                    f"{posting_date} / ₹{amount} across vouchers {', '.join(vouchers)}"
                ),
                amount_at_risk=amount,
                period_id=context.period_id,
                owner_role="GL Accountant",
                effective_threshold=(
                    f"min_amount ₹{threshold}; require_different_voucher true; "
                    f"account_budget ₹{budget}"
                ),
                detail=(
                    f"The same ₹{amount} {('debit' if _sign > 0 else 'credit')} "
                    f"to account {account} and cost centre {cost_center or '—'} "
                    f"on {posting_date} appears in {len(vouchers)} vouchers: "
                    f"{', '.join(vouchers)}."
                ),
                evidence_refs=evidence_refs,
                sample_rows=sample_rows,
            )
        )
    return findings


evaluate_catalog_exc_008.REQUIRED_INPUTS = ("transactions",)


CATALOG_RULES_001_008_REGISTRY = [
    {
        "catalog_id": "EXC-001",
        "name": "Import imbalance",
        "evaluator": evaluate_catalog_exc_001,
    },
    {
        "catalog_id": "EXC-002",
        "name": "Cross-batch duplicate rows",
        "evaluator": evaluate_catalog_exc_002,
    },
    {
        "catalog_id": "EXC-003",
        "name": "Cross-system tie-out variance",
        "evaluator": evaluate_catalog_exc_003,
    },
    {
        "catalog_id": "EXC-006",
        "name": "Entity/account actuals without budget",
        "evaluator": evaluate_catalog_exc_006,
    },
    {
        "catalog_id": "EXC-008",
        "name": "Possible duplicate voucher line",
        "evaluator": evaluate_catalog_exc_008,
    },
]

BATCH_CATALOG_001_008_EVALUATORS = tuple(
    entry["evaluator"] for entry in CATALOG_RULES_001_008_REGISTRY
)
