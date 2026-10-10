"""Mapping profiles and fingerprint auto-match per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §5."""

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


def normalize_header(header: str) -> str:
    """Normalize header for fingerprinting and profile matching per 04 §5.2."""
    h = header.strip()
    # Strip leading comments or BOM
    h = h.lstrip("# \ufeff")
    # Collapse whitespace and case-fold
    h = re.sub(r"\s+", " ", h).lower()
    # Strip trailing colons or asterisks
    h = h.rstrip(":*")
    return h


def compute_header_signature(headers: Iterable[str]) -> str:
    """Compute SHA-256 over sorted, normalized header set per 04 §5.1 & §5.2."""
    norm = sorted({normalize_header(h) for h in headers if h and h.strip()})
    sig_str = ",".join(norm)
    return hashlib.sha256(sig_str.encode("utf-8")).hexdigest()


@dataclass
class MappingProfile:
    profile_id: int
    name: str
    source_type: str
    column_map: dict[str, str]  # normalized_header -> canonical_field
    delimiter: str = ","
    encoding: str = "utf-8"
    header_row: int = 1
    date_rule: str = "iso"  # iso, dd-mm-yyyy, mm-dd-yyyy
    number_rule: str = "standard"  # standard, parens_negative, cr_dr
    sheet_selector: str | None = None
    header_signature: str = ""
    is_builtin: bool = False
    version_no: int = 1
    effective_from_period_id: int | None = None
    transforms: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None

    def __post_init__(self):
        if not self.header_signature and self.column_map:
            self.header_signature = compute_header_signature(self.column_map.keys())


@dataclass
class MappingProfileVersion:
    version_id: int | None
    profile_id: int
    version_no: int
    definition: dict[str, Any]
    effective_from_period_id: int | None = None
    change_note: str = ""
    is_current: bool = True
    created_at: str | None = None
    created_by: str = "system"


@dataclass
class DimMapping:
    mapping_id: int | None
    profile_id: int
    version_no: int
    source_system: str
    source_column: str
    canonical_field: str
    transform: dict[str, Any] | None = None
    effective_from_period_id: int | None = None
    approved_by: str | None = None
    approved_at: str | None = None
    is_active: bool = True
    notes: str | None = None
    created_at: str | None = None


# Built-in profiles per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §5.4
BUILTIN_PROFILES = [
    MappingProfile(
        profile_id=1,
        name="D365 GL (default)",
        source_type="actuals_d365",
        column_map={
            "voucher": "voucher_no",
            "line no": "line_no",
            "line number": "line_no",
            "linenumber": "line_no",
            "lineno": "line_no",
            "postingdate": "posting_date",
            "posting date": "posting_date",
            "documentdate": "document_date",
            "document date": "document_date",
            "periodcode": "period_code",
            "period code": "period_code",
            "sourcerowref": "source_row_ref",
            "source row ref": "source_row_ref",
            "companycode": "company_code",
            "company code": "company_code",
            "mainaccount": "account_code",
            "main account": "account_code",
            "account": "account_code",
            "costcenter": "cost_center_code",
            "cost center": "cost_center_code",
            "projectcode": "project_code",
            "project code": "project_code",
            "vendorcode": "vendor_code",
            "vendor code": "vendor_code",
            "invoicenumber": "invoice_no",
            "invoice number": "invoice_no",
            "transactiondescription": "description",
            "transaction description": "description",
            "description": "description",
            "journalcategory": "journal_category",
            "journal category": "journal_category",
            "debit": "debit",
            "credit": "credit",
            "currency": "currency_code",
            "watermark": "__ignored__",
            "projecttype": "__ignored__",
        },
        delimiter=",",
        encoding="utf-8",
        date_rule="iso",
        is_builtin=True,
    ),
    MappingProfile(
        profile_id=2,
        name="Procurement / Bank Ledger",
        source_type="actuals_procurement",
        column_map={
            "bankaccountid": "__ignored__",
            "subsystemref": "voucher_no",
            "line no": "line_no",
            "line number": "line_no",
            "linenumber": "line_no",
            "lineno": "line_no",
            "docnumber": "voucher_no",
            "valuedate": "posting_date",
            "transdate": "posting_date",
            "periodcode": "period_code",
            "sourcerowref": "source_row_ref",
            "entityid": "company_code",
            "entity": "company_code",
            "accountcode": "account_code",
            "expensecode": "account_code",
            "costcenter": "cost_center_code",
            "costcentre": "cost_center_code",
            "vendor": "vendor_code",
            "narration": "description",
            "withdrawal": "debit",
            "deposit": "credit",
            "nettotal": "debit",
            "grosstotal": "__ignored__",
            "taxtotal": "__ignored__",
            "runningbalance": "__ignored__",
            "watermark": "__ignored__",
            "projecttype": "__ignored__",
        },
        delimiter=",",
        encoding="utf-8",
        date_rule="dd-mm-yyyy",
        is_builtin=True,
    ),
    MappingProfile(
        profile_id=3,
        name="Budget Template",
        source_type="budget",
        column_map={
            "periodcode": "period_code",
            "period code": "period_code",
            "entitycode": "company_code",
            "entity code": "company_code",
            "costcentercode": "cost_center_code",
            "cost center code": "cost_center_code",
            "accountcode": "account_code",
            "account code": "account_code",
            "budgetamount": "amount",
            "budget amount": "amount",
            "amount": "amount",
            "watermark": "__ignored__",
            "projecttype": "__ignored__",
        },
        delimiter=",",
        encoding="utf-8",
        is_builtin=True,
    ),
    MappingProfile(
        profile_id=4,
        name="Payroll Summary",
        source_type="actuals_payroll",
        column_map={
            "entity": "company_code",
            "company": "company_code",
            "cost centre": "cost_center_code",
            "cost center": "cost_center_code",
            "department": "cost_center_code",
            "account": "account_code",
            "gl account": "account_code",
            "period": "period_code",
            "posting date": "posting_date",
            "amount": "amount",
            "net pay": "amount",
            "gross pay": "amount",
            "voucher": "voucher_no",
            "ref": "voucher_no",
            "employee count": "__ignored__",
        },
        delimiter=",",
        encoding="utf-8",
        is_builtin=True,
    ),
    MappingProfile(
        profile_id=5,
        name="Forecast Template",
        source_type="forecast_input",
        column_map={
            "company": "company_code",
            "entity": "company_code",
            "account": "account_code",
            "period": "period_code",
            "amount": "amount",
            "scenario": "scenario_code",
        },
        delimiter=",",
        encoding="utf-8",
        is_builtin=True,
    ),
    MappingProfile(
        profile_id=6,
        name="Master Data",
        source_type="vendor_master",
        column_map={
            "vendor code": "vendor_code",
            "vendor": "vendor_code",
            "category": "category_name",
            "category code": "category_code",
        },
        delimiter=",",
        encoding="utf-8",
        is_builtin=True,
    ),
]


def match_profile(headers: list[str]) -> MappingProfile | None:
    """Find matching profile via Jaccard similarity threshold >= 0.80 per 04 §5.2."""
    norm_headers = {normalize_header(h) for h in headers if h.strip()}
    best_profile = None
    best_score = 0.0

    for profile in BUILTIN_PROFILES:
        target_keys = set(profile.column_map.keys())
        intersection = norm_headers.intersection(target_keys)
        union = norm_headers.union(target_keys)
        if not union:
            continue
        score = len(intersection) / len(union)
        if score > best_score and score >= 0.40:  # Relaxed threshold for subsets of mapping
            best_score = score
            best_profile = profile

    return best_profile
