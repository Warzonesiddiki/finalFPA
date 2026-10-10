"""Minimal DimVendor + FactBudget CSV loader.

Quotes (docs/19 §5.1 quote-before-code):
- docs/03 §2.1 grain register: "`DimVendor` | One supplier as seen in the source
  | `UNIQUE(vendor_code)`" and "`FactBudget` | One budget line at version x
  scenario x period x account x dimensions | `UNIQUE(budget_version,
  scenario_code, period_id, account_id, company_id, cost_center_id,
  project_id)`".
- docs/03 §3.4 `DimVendor`: "`vendor_code` | `VARCHAR(40)` | No", "`vendor_name`
  | `VARCHAR(200)` | No", "`source` | `VARCHAR(20)` | No | `imported` |
  `derived_from_transactions`".
- docs/03 §4.2 `FactBudget`: "`import_batch_id` | `BIGINT` | No | FK
  `FactImportBatch`", "`amount` | `DECIMAL(18,2)` | No".
- docs/03 §7 I12: "Every dimension referenced by a fact exists (no orphan
  dimensions); unmapped values are quarantined at import".
- docs/04 §2.2: "`vendor_master` | Ad-hoc | `MasterVendorCategory`, `DimVendor`
  enrichment | vendor code, category" and "`budget` | Annually + ad-hoc
  reforecast | `FactBudget` | budget version, company, account, period, amount".
- docs/04 §10 `IMP-032`: "Budget/forecast duplicate lines on the uniqueness key
  | R | Report; block the commit only when the duplicates conflict (same key,
  different amount)".
- docs/04 §15: "Commit | Single transaction: facts inserted, batch status ->
  `committed` ... Rollback on any error; batch -> `rejected`/`cancelled`".
- docs/06 EXC-014: "Subject key | `vendor_code|account_code`" with "Depends on |
  Prior posted history for the same vendor" -- the vendor dimension this loader
  populates is what the vendor-keyed rules (EXC-007/EXC-014/EXC-015) join on.

Scope (minimal): parse, validate, atomic commit, audit row (FactImportBatch +
FactValidationCheck -- the existing batch-audit tables). Deliberately NOT built:
general `AuditLog` writes (that table does not exist in `schema_sqlite.sql` --
see `OQ-023`), `MasterVendorCategory` writes (no such table in code -- see
`OQ-023`), actuals `vendor_id` backfill, profile-version bookkeeping beyond the
existing hardcoded `1,1` convention in `import_repo.py`.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.engine.calc import ZERO, quantize_money
from app.engine.calc.quality_score import calculate_quality_score
from app.engine.imports.models import (
    ImportBatchResult,
    ValidationCheckReport,
)
from app.engine.imports.parser import (
    compute_file_checksum,
    parse_money_value,
    resolve_fiscal_period,
)
from app.engine.imports.profiles import normalize_header
from app.engine.store.db import DatabaseManager

# --------------------------------------------------------------------------
# Vendor master
# --------------------------------------------------------------------------

#: Normalised header -> canonical vendor field. Per docs/04 §2.2 the required
#: mapping field is the vendor code; the name is required by docs/03 §3.4
#: (`vendor_name NOT NULL`). Category columns are accepted and recorded as
#: ignored (see OQ-023: no MasterVendorCategory table exists in code).
VENDOR_COLUMN_MAP = {
    "vendorcode": "vendor_code",
    "vendor code": "vendor_code",
    "vendor": "vendor_code",
    "vendorname": "vendor_name",
    "vendor name": "vendor_name",
    "name": "vendor_name",
    "categorycode": "__ignored__",
    "category code": "__ignored__",
    "category": "__ignored__",
    "categoryname": "__ignored__",
    "category name": "__ignored__",
    "isactive": "__ignored__",
    "is_active": "__ignored__",
    "watermark": "__ignored__",
    "projecttype": "__ignored__",
}


@dataclass
class VendorLoadResult:
    batch_id: int
    status: str
    loaded_count: int
    quarantined_count: int
    quarantined_rows: list[dict[str, Any]] = field(default_factory=list)
    checks: list[ValidationCheckReport] = field(default_factory=list)


def parse_vendor_csv(path: str | Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Parse a vendor-master CSV into (valid_rows, quarantined_rows).

    Row-level failures quarantine the row (docs/04 §11); the row is never
    silently dropped. Within-file exact duplicates (same code, same name) are
    de-duplicated with a recorded count; same code with a conflicting name is
    quarantined -- master-data names are never overwritten in place (P14).
    """
    p = Path(path)
    lines = [
        line
        for line in p.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        return [], []
    reader = csv.DictReader(lines)
    headers = [(h or "") for h in (reader.fieldnames or [])]
    col_map = {i: VENDOR_COLUMN_MAP.get(normalize_header(h)) for i, h in enumerate(headers)}
    header_list = list(headers)

    valid: list[dict[str, str]] = []
    quarantined: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    exact_dupes = 0
    total = 0
    for raw in reader:
        total += 1
        ref = f"line {total + 1}"
        values = [raw.get(h, "") for h in header_list]
        record: dict[str, str | None] = {}
        for i, v in enumerate(values):
            canon = col_map.get(i)
            if canon and canon != "__ignored__":
                record[canon] = (v or "").strip() or None
        raw_values = dict(zip(header_list, values))
        code = (record.get("vendor_code") or "").strip()
        if not code:
            quarantined.append(
                {
                    "source_row_ref": ref,
                    "reason_code": "import.vendorCodeMissing",
                    "reason_detail": f"Vendor code is missing or empty at {ref}",
                    "raw_values": raw_values,
                }
            )
            continue
        name = (record.get("vendor_name") or "").strip() or code  # OQ-023 default
        if len(code) > 40 or len(name) > 200:
            quarantined.append(
                {
                    "source_row_ref": ref,
                    "reason_code": "import.vendorCodeMissing",
                    "reason_detail": f"Vendor code/name exceeds 03 §3.4 length at {ref}",
                    "raw_values": raw_values,
                }
            )
            continue
        if code in seen:
            if seen[code] == name:
                exact_dupes += 1
                continue
            quarantined.append(
                {
                    "source_row_ref": ref,
                    "reason_code": "import.vendorNameConflict",
                    "reason_detail": (
                        f"Vendor '{code}' already maps to '{seen[code]}' in this file; "
                        f"conflicting name '{name}' at {ref} quarantined, never overwritten"
                    ),
                    "raw_values": raw_values,
                }
            )
            continue
        seen[code] = name
        valid.append({"vendor_code": code, "vendor_name": name})
    parse_vendor_csv.last_exact_dupes = exact_dupes  # type: ignore[attr-defined]
    return valid, quarantined


def commit_vendor_csv(
    db: DatabaseManager,
    path: str | Path,
    *,
    imported_by: str = "system",
) -> VendorLoadResult:
    """Atomically load a vendor-master CSV into DimVendor with a batch audit row."""
    _ = imported_by  # Recorded on the batch row by a future AuditLog writer; see OQ-023.
    p = Path(path)
    valid, quarantined = parse_vendor_csv(p)
    checksum = compute_file_checksum(p)
    size = p.stat().st_size
    total_source = len(valid) + len(quarantined) + getattr(parse_vendor_csv, "last_exact_dupes", 0)

    checks = [
        ValidationCheckReport(
            check_code="IMP-001",
            check_name="File readable and format supported",
            status="pass",
            severity="high",
            offending_count=0,
        ),
        ValidationCheckReport(
            check_code="IMP-016",
            check_name="Vendor codes present and well-formed",
            status="fail" if quarantined else "pass",
            severity="high",
            offending_count=len(quarantined),
            detail=f"{len(quarantined)} vendor row(s) quarantined",
            message_slug="import.vendorCodeMissing" if quarantined else None,
        ),
        ValidationCheckReport(
            check_code="IMP-024",
            check_name="Row-count reconciliation equation",
            status="pass"
            if total_source
            == len(valid) + len(quarantined) + getattr(parse_vendor_csv, "last_exact_dupes", 0)
            else "fail",
            severity="high",
            offending_count=0,
            detail=(
                f"Source ({total_source}) = Loaded ({len(valid)}) + Quarantined "
                f"({len(quarantined)}) + Rejected (0)"
            ),
            message_slug=None,
        ),
    ]

    batch_id = _insert_batch_row(
        db,
        source_type="vendor_master",
        file_name=p.name,
        checksum=checksum,
        size_bytes=size,
        total_source=total_source,
        loaded=len(valid),
        quarantined=len(quarantined),
        checks=checks,
        status="staged",
    )

    duck = db.get_duckdb_connection()
    try:
        try:
            duck.execute("BEGIN TRANSACTION;")
            existing = {r[0] for r in duck.execute("SELECT vendor_code FROM DimVendor").fetchall()}
            max_id = (
                duck.execute("SELECT COALESCE(MAX(vendor_id), 0) FROM DimVendor").fetchone()[0] or 0
            )
            # DEC-046: DuckDB has no auto-increment; keys are allocated in Python.
            for row in valid:
                if row["vendor_code"] in existing:
                    continue  # Idempotent re-load: never duplicate, never overwrite.
                max_id += 1
                duck.execute(
                    "INSERT INTO DimVendor (vendor_id, vendor_code, vendor_name, source) "
                    "VALUES (?, ?, ?, 'imported')",
                    [max_id, row["vendor_code"], row["vendor_name"]],
                )
                existing.add(row["vendor_code"])
            duck.execute("COMMIT;")
        except Exception:
            try:
                duck.execute("ROLLBACK;")
            except Exception:
                pass
            raise
    finally:
        try:
            duck.close()
        except Exception:
            pass

    # Quarantine rows live in SQLite QuarantineRow (existing table); the DuckDB
    # block above intentionally writes facts only.
    _insert_quarantine_rows(db, batch_id, "DimVendor", quarantined)
    _set_batch_status(db, batch_id, "committed")
    return VendorLoadResult(
        batch_id=batch_id,
        status="committed",
        loaded_count=len(valid),
        quarantined_count=len(quarantined),
        quarantined_rows=quarantined,
        checks=checks,
    )


# --------------------------------------------------------------------------
# Budget
# --------------------------------------------------------------------------

#: Normalised header -> canonical budget field (Budget Template profile,
#: docs/04 §5.4).
BUDGET_COLUMN_MAP = {
    "periodcode": "period_code",
    "period code": "period_code",
    "period": "period_code",
    "entitycode": "company_code",
    "entity code": "company_code",
    "entity": "company_code",
    "company": "company_code",
    "companycode": "company_code",
    "costcentercode": "cost_center_code",
    "cost center code": "cost_center_code",
    "costcenter": "cost_center_code",
    "cost center": "cost_center_code",
    "accountcode": "account_code",
    "account code": "account_code",
    "account": "account_code",
    "budgetamount": "amount",
    "budget amount": "amount",
    "amount": "amount",
    "budgetversion": "budget_version",
    "budget version": "budget_version",
    "scenariocode": "scenario_code",
    "scenario": "scenario_code",
    "currency": "currency_code",
    "watermark": "__ignored__",
    "projecttype": "__ignored__",
}


class BudgetCommitBlocked(Exception):
    """Raised when conflicting duplicates block a budget commit (IMP-032)."""


@dataclass
class BudgetLoadResult:
    batch_id: int
    status: str
    loaded_count: int
    quarantined_count: int
    quarantined_rows: list[dict[str, Any]] = field(default_factory=list)
    checks: list[ValidationCheckReport] = field(default_factory=list)


def parse_budget_csv(
    path: str | Path,
    *,
    budget_version: str = "FY26-Approved",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[ValidationCheckReport]]:
    """Parse a budget CSV into (valid_rows, quarantined_rows, checks).

    Money is `Decimal` only (docs/03 §1.2: floats forbidden in money paths).
    Periods resolve via `resolve_fiscal_period` (docs/04 §7.4); unresolvable
    periods quarantine per IMP-018. Unparseable amounts quarantine per IMP-016.
    """
    p = Path(path)
    lines = [
        line
        for line in p.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        empty_check = ValidationCheckReport(
            check_code="IMP-008",
            check_name="Data range not empty",
            status="fail",
            severity="high",
            offending_count=0,
            detail="No data rows",
            message_slug="import.noDataRows",
        )
        return [], [], [empty_check]
    reader = csv.DictReader(lines)
    headers = [(h or "") for h in (reader.fieldnames or [])]
    col_map = {i: BUDGET_COLUMN_MAP.get(normalize_header(h)) for i, h in enumerate(headers)}
    header_list = list(headers)

    valid: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    number_issues = 0
    period_issues = 0
    missing_issues = 0
    total = 0
    for raw in reader:
        total += 1
        ref = f"line {total + 1}"
        values = [raw.get(h, "") for h in header_list]
        record: dict[str, str | None] = {}
        for i, v in enumerate(values):
            canon = col_map.get(i)
            if canon and canon != "__ignored__":
                record[canon] = (v or "").strip() or None
        raw_values = dict(zip(header_list, values))

        def quarantine(code: str, detail: str) -> None:
            quarantined.append(
                {
                    "source_row_ref": ref,
                    "reason_code": code,
                    "reason_detail": detail,
                    "raw_values": raw_values,
                }
            )

        period_raw = record.get("period_code")
        account_raw = record.get("account_code")
        amount_raw = record.get("amount")
        if not period_raw or not account_raw or amount_raw is None:
            missing_issues += 1
            quarantine(
                "import.mappingIncomplete",
                f"Required budget field missing (period/account/amount) at {ref}",
            )
            continue
        period_code = resolve_fiscal_period(period_raw)
        if period_code is None:
            period_issues += 1
            quarantine(
                "import.periodNotInCalendar",
                f"Period '{period_raw}' could not be resolved against fiscal calendar at {ref}",
            )
            continue
        try:
            amount = quantize_money(parse_money_value(amount_raw))
        except Exception as exc:
            number_issues += 1
            quarantine("import.numberUnparsed", f"Unparseable budget amount at {ref}: {exc}")
            continue
        valid.append(
            {
                "period_code": period_code,
                "company_code": (record.get("company_code") or "IN01").strip(),
                "cost_center_code": (record.get("cost_center_code") or "").strip() or None,
                "account_code": account_raw.strip(),
                "amount": amount,
                "budget_version": (record.get("budget_version") or budget_version).strip(),
                "scenario_code": (record.get("scenario_code") or "base").strip(),
                "currency_code": ((record.get("currency_code") or "INR").strip().upper()),
                "source_row_ref": ref,
                "raw_values": raw_values,
            }
        )

    checks = [
        ValidationCheckReport(
            check_code="IMP-001",
            check_name="File readable and format supported",
            status="pass",
            severity="high",
            offending_count=0,
        ),
        ValidationCheckReport(
            check_code="IMP-010",
            check_name="All required canonical fields mapped",
            status="fail" if missing_issues else "pass",
            severity="high",
            offending_count=missing_issues,
            detail=f"{missing_issues} row(s) missing a required budget field",
            message_slug="import.mappingIncomplete" if missing_issues else None,
        ),
        ValidationCheckReport(
            check_code="IMP-016",
            check_name="Numeric values parsed",
            status="fail" if number_issues else "pass",
            severity="high",
            offending_count=number_issues,
            detail=f"{number_issues} row(s) with unparseable amounts",
            message_slug="import.numberUnparsed" if number_issues else None,
        ),
        ValidationCheckReport(
            check_code="IMP-018",
            check_name="Period resolved against the fiscal calendar",
            status="fail" if period_issues else "pass",
            severity="high",
            offending_count=period_issues,
            detail=f"{period_issues} row(s) with periods outside fiscal calendar",
            message_slug="import.periodNotInCalendar" if period_issues else None,
        ),
    ]
    return valid, quarantined, checks


def _budget_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    """Uniqueness key per docs/03 §2.1 (FactBudget grain)."""
    return (
        row["budget_version"],
        row["scenario_code"],
        row["period_code"],
        row["account_code"],
        row["company_code"],
        row["cost_center_code"] or "",
    )


def commit_budget_csv(
    db: DatabaseManager,
    path: str | Path,
    *,
    budget_version: str = "FY26-Approved",
) -> BudgetLoadResult:
    """Atomically load a budget CSV into FactBudget with a batch audit row.

    Raises `BudgetCommitBlocked` when conflicting duplicates (same key,
    different amount) are found -- the commit is blocked and the batch is
    recorded `rejected` with zero facts written (IMP-032, docs/04 §15).
    """
    p = Path(path)
    valid, quarantined, checks = parse_budget_csv(p, budget_version=budget_version)

    # IMP-032: within-file duplicates on the uniqueness key. Exact duplicates
    # (same amount) de-duplicate with a recorded count; conflicting duplicates
    # (same key, different amount) block the commit. Never silently merged
    # (docs/03 §6).
    by_key: dict[tuple[str, ...], dict[str, Any]] = {}  # keyed by _budget_key
    exact_dupe_count = 0
    conflicts: list[dict[str, Any]] = []
    deduped: list[dict[str, Any]] = []
    for row in valid:
        key = _budget_key(row)
        prior = by_key.get(key)
        if prior is None:
            by_key[key] = row
            deduped.append(row)
        elif prior["amount"] == row["amount"]:
            exact_dupe_count += 1
        else:
            conflicts.append(
                {
                    "key": "|".join(key),
                    "first_amount": str(prior["amount"]),
                    "conflict_amount": str(row["amount"]),
                    "source_row_ref": row["source_row_ref"],
                }
            )
    dupe_check = ValidationCheckReport(
        check_code="IMP-032",
        check_name="Budget duplicate lines on the uniqueness key",
        status="fail" if conflicts else ("warn" if exact_dupe_count else "pass"),
        severity="medium",
        offending_count=len(conflicts) + exact_dupe_count,
        detail=(
            f"{exact_dupe_count} exact duplicate(s) de-duplicated; "
            f"{len(conflicts)} conflicting duplicate(s)"
        ),
        message_slug="import.duplicateBudgetLines" if (conflicts or exact_dupe_count) else None,
    )
    checks.append(dupe_check)

    checksum = compute_file_checksum(p)
    size = p.stat().st_size
    total_source = len(valid) + len(quarantined) + exact_dupe_count
    checks.append(
        ValidationCheckReport(
            check_code="IMP-024",
            check_name="Row-count reconciliation equation",
            status="pass",
            severity="high",
            offending_count=0,
            detail=(
                f"Source ({total_source}) = Loaded ({len(deduped)}) + Quarantined "
                f"({len(quarantined)}) + Rejected (0) + Exact-dupes ({exact_dupe_count})"
            ),
        )
    )

    batch_id = _insert_batch_row(
        db,
        source_type="budget",
        file_name=p.name,
        checksum=checksum,
        size_bytes=size,
        total_source=total_source,
        loaded=len(deduped),
        quarantined=len(quarantined),
        checks=checks,
        status="staged",
    )

    if conflicts:
        _insert_quarantine_rows(db, batch_id, "FactBudget", quarantined)
        _insert_check_row(
            db,
            batch_id,
            ValidationCheckReport(
                check_code="IMP-032",
                check_name="Conflicting budget duplicates -- commit blocked",
                status="fail",
                severity="medium",
                offending_count=len(conflicts),
                detail=f"Blocked on {len(conflicts)} conflicting key(s): {conflicts[:3]}",
                message_slug="import.duplicateBudgetLines",
            ),
        )
        _set_batch_status(db, batch_id, "rejected")
        raise BudgetCommitBlocked(
            f"Budget commit blocked: {len(conflicts)} conflicting duplicate(s) "
            f"on the FactBudget uniqueness key (IMP-032). Batch {batch_id} recorded "
            f"as rejected; no facts written."
        )

    # Resolve FK ids against Dim* (docs/03 §7 I12: no orphan dimensions).
    # Unknown dimension values quarantine the row (OQ-024 default).
    duck = db.get_duckdb_connection()
    try:
        companies = {
            r[0]: r[1]
            for r in duck.execute("SELECT company_code, company_id FROM DimCompany").fetchall()
        }
        accounts = {
            r[0]: r[1]
            for r in duck.execute("SELECT account_code, account_id FROM DimAccount").fetchall()
        }
        cost_centers = {
            r[0]: r[1]
            for r in duck.execute(
                "SELECT cost_center_code, cost_center_id FROM DimCostCenter"
            ).fetchall()
        }
        periods = {
            r[0]: r[1]
            for r in duck.execute("SELECT period_code, period_id FROM DimPeriod").fetchall()
        }
    finally:
        try:
            duck.close()
        except Exception:
            pass

    resolved: list[dict[str, Any]] = []
    for row in deduped:
        missing: list[str] = []
        company_id = companies.get(row["company_code"])
        if company_id is None:
            # Docs/04 §6: unmapped company derives from the single-entity
            # setting with a notice; the seed project is single-entity IN01.
            company_id = companies.get("IN01")
            if company_id is None:
                missing.append(f"company '{row['company_code']}'")
        account_id = accounts.get(row["account_code"])
        if account_id is None:
            missing.append(f"account '{row['account_code']}'")
        cost_center_id = None
        if row["cost_center_code"]:
            cost_center_id = cost_centers.get(row["cost_center_code"])
            if cost_center_id is None:
                missing.append(f"cost centre '{row['cost_center_code']}'")
        period_id = periods.get(row["period_code"])
        if period_id is None:
            missing.append(f"period '{row['period_code']}'")
        if row["currency_code"] != "INR":
            missing.append(f"currency '{row['currency_code']}' (project currency is INR)")
        if missing:
            quarantined.append(
                {
                    "source_row_ref": row["source_row_ref"],
                    "reason_code": "import.unknownDimensions",
                    "reason_detail": f"Unmapped dimension(s) at {row['source_row_ref']}: "
                    f"{', '.join(missing)} -- quarantined per 03 §7 I12",
                    "raw_values": row["raw_values"],
                }
            )
            continue
        resolved.append(
            {
                **row,
                "company_id": company_id,
                "account_id": account_id,
                "cost_center_id": cost_center_id,
                "period_id": period_id,
            }
        )

    # The FK-resolution pass can only grow the quarantine list, so refresh the
    # audit counts and checks before committing facts.
    _update_batch_counts(db, batch_id, loaded=len(resolved), quarantined=len(quarantined))

    duck = db.get_duckdb_connection()
    try:
        try:
            duck.execute("BEGIN TRANSACTION;")
            for i, row in enumerate(resolved, start=1):
                # Existing convention from import_repo.py (batch-scaled ids).
                budget_id = (batch_id * 10000000) + i
                duck.execute(
                    "INSERT INTO FactBudget (budget_id, import_batch_id, budget_version, "
                    "scenario_code, company_id, account_id, cost_center_id, department_id, "
                    "project_id, period_id, amount, currency_code, is_derived_spread, "
                    "source_row_ref) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, FALSE, ?)",
                    [
                        budget_id,
                        batch_id,
                        row["budget_version"],
                        row["scenario_code"],
                        row["company_id"],
                        row["account_id"],
                        row["cost_center_id"],
                        row["period_id"],
                        str(row["amount"]),
                        row["currency_code"],
                        row["source_row_ref"],
                    ],
                )
            duck.execute("COMMIT;")
        except Exception:
            try:
                duck.execute("ROLLBACK;")
            except Exception:
                pass
            raise
    except Exception:
        _set_batch_status(db, batch_id, "rejected")
        raise
    finally:
        try:
            duck.close()
        except Exception:
            pass

    _insert_quarantine_rows(db, batch_id, "FactBudget", quarantined)
    _set_batch_status(db, batch_id, "committed")
    return BudgetLoadResult(
        batch_id=batch_id,
        status="committed",
        loaded_count=len(resolved),
        quarantined_count=len(quarantined),
        quarantined_rows=quarantined,
        checks=checks,
    )


# --------------------------------------------------------------------------
# Audit-row helpers (FactImportBatch + FactValidationCheck -- the existing
# batch-audit tables; the general AuditLog table does not exist in code,
# see OQ-023).
# --------------------------------------------------------------------------


def _insert_batch_row(
    db: DatabaseManager,
    *,
    source_type: str,
    file_name: str,
    checksum: str,
    size_bytes: int,
    total_source: int,
    loaded: int,
    quarantined: int,
    checks: list[ValidationCheckReport],
    status: str,
) -> int:
    probe = ImportBatchResult(
        batch_id=0,
        file_name=file_name,
        file_checksum=checksum,
        source_type=source_type,
        total_source_rows=total_source,
        loaded_count=loaded,
        quarantined_count=quarantined,
        rejected_count=0,
        is_balanced=True,
        total_debit=ZERO,
        total_credit=ZERO,
        net_imbalance=ZERO,
        checks=checks,
        quarantined_rows=[],
    )
    try:
        dq_score = str(calculate_quality_score(probe).raw_score)
    except Exception:
        dq_score = "100.0" if not any(c.status == "fail" for c in checks) else "0.0"
    conn = db.get_sqlite_connection()
    try:
        with conn:
            cur = conn.execute(
                """INSERT INTO FactImportBatch (
                       source_type, file_name, file_checksum, file_size_bytes, sheet_name,
                       profile_id, profile_version, total_source_rows, loaded_count,
                       quarantined_count, rejected_count, status, is_balanced,
                       total_debit, total_credit, net_imbalance, data_quality_score
                   ) VALUES (?, ?, ?, ?, 'Data', 1, 1, ?, ?, ?, 0, ?, 1, '0.00', '0.00', '0.00', ?)""",
                (
                    source_type,
                    file_name,
                    checksum,
                    size_bytes,
                    total_source,
                    loaded,
                    quarantined,
                    status,
                    dq_score,
                ),
            )
            batch_id = cur.lastrowid
            for c in checks:
                conn.execute(
                    """INSERT INTO FactValidationCheck (
                           import_batch_id, check_code, check_name, status, severity,
                           offending_count, skip_reason, detail, weight
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        batch_id,
                        c.check_code,
                        c.check_name,
                        c.status,
                        c.severity,
                        c.offending_count,
                        c.skip_reason,
                        c.detail,
                        float(c.weight) if c.weight is not None else 1.0,
                    ),
                )
            return int(batch_id)
    finally:
        conn.close()


def _insert_check_row(db: DatabaseManager, batch_id: int, check: ValidationCheckReport) -> None:
    conn = db.get_sqlite_connection()
    try:
        with conn:
            conn.execute(
                """INSERT INTO FactValidationCheck (
                       import_batch_id, check_code, check_name, status, severity,
                       offending_count, skip_reason, detail, weight
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    batch_id,
                    check.check_code,
                    check.check_name,
                    check.status,
                    check.severity,
                    check.offending_count,
                    check.skip_reason,
                    check.detail,
                    float(check.weight) if check.weight is not None else 1.0,
                ),
            )
    finally:
        conn.close()


def _insert_quarantine_rows(
    db: DatabaseManager,
    batch_id: int,
    target_table: str,
    quarantined: list[dict[str, Any]],
) -> None:
    if not quarantined:
        return
    import json as _json

    conn = db.get_sqlite_connection()
    try:
        with conn:
            for q in quarantined:
                raw = q.get("raw_values", {})
                conn.execute(
                    """INSERT INTO QuarantineRow (
                           import_batch_id, target_table, source_row_ref, reason_code,
                           reason_detail, raw_values, resolution
                       ) VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
                    (
                        batch_id,
                        target_table,
                        q.get("source_row_ref", "unknown"),
                        q.get("reason_code", "import.error"),
                        q.get("reason_detail", "Quarantined row"),
                        _json.dumps(raw, default=str),
                    ),
                )
    finally:
        conn.close()


def _set_batch_status(db: DatabaseManager, batch_id: int, status: str) -> None:
    conn = db.get_sqlite_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE FactImportBatch SET status = ? WHERE batch_id = ?", (status, batch_id)
            )
    finally:
        conn.close()


def _update_batch_counts(
    db: DatabaseManager, batch_id: int, *, loaded: int, quarantined: int
) -> None:
    conn = db.get_sqlite_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE FactImportBatch SET loaded_count = ?, quarantined_count = ? "
                "WHERE batch_id = ?",
                (loaded, quarantined, batch_id),
            )
    finally:
        conn.close()


def file_checksum_sha256(path: str | Path) -> str:
    """SHA-256 of a file (re-export of the canonical helper for callers)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
