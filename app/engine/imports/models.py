"""Data structures for parsing and importing files per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class PreScanResult:
    file_name: str
    file_size_bytes: int
    file_checksum: str
    sheet_names: list[str]
    estimated_rows: int
    detected_encoding: str | None = None
    detected_delimiter: str | None = None
    header_row_candidate: int = 1
    sample_headers: list[str] = field(default_factory=list)
    has_banner: bool = False
    is_encrypted: bool = False


@dataclass
class ValidationIssue:
    check_code: str  # e.g. IMP-001..IMP-032
    severity: str  # high, medium, low
    message_slug: str
    message: str
    source_row_ref: str | None = None
    raw_values: dict[str, Any] | None = None


@dataclass
class ValidationCheckReport:
    check_code: str
    check_name: str
    status: str  # pass, fail, warn, skipped
    severity: str  # high, medium, low
    offending_count: int
    message_slug: str | None = None
    skip_reason: str | None = None
    sample_rows: list[dict[str, Any]] = field(default_factory=list)
    detail: str | None = None
    weight: Decimal | None = None

    def __post_init__(self):
        if self.weight is None:
            sev = self.severity.lower()
            if sev == "high":
                self.weight = Decimal("10.0000")
            elif sev == "medium":
                self.weight = Decimal("5.0000")
            elif sev == "low":
                self.weight = Decimal("2.0000")
            else:
                self.weight = Decimal("1.0000")


@dataclass
class ParsedTransaction:
    source_row_ref: str
    voucher_no: str
    posting_date: str
    company_code: str
    account_code: str
    cost_center_code: str | None
    project_code: str | None
    vendor_code: str | None
    invoice_no: str | None
    description: str | None
    debit: Decimal
    credit: Decimal
    net_amount: Decimal
    currency_code: str
    document_date: str | None = None
    line_no: int = 1
    journal_category: str | None = None
    raw_values: dict[str, Any] = field(default_factory=dict)
    is_zero_amount: bool = False
    period_code: str | None = None
    # Assigned on import; required for cross-batch exception checks.
    import_batch_id: int | None = None


@dataclass
class ImportBatchResult:
    batch_id: int
    file_name: str
    file_checksum: str
    source_type: str
    total_source_rows: int
    loaded_count: int
    quarantined_count: int
    rejected_count: int
    is_balanced: bool
    total_debit: Decimal
    total_credit: Decimal
    net_imbalance: Decimal
    checks: list[ValidationCheckReport] = field(default_factory=list)
    quarantined_rows: list[dict[str, Any]] = field(default_factory=list)
    balance_tolerance: Decimal = Decimal("0.00")
    sheet_name: str = "Data"
    external_batch_ref: str | None = None
    subject_namespace: str | None = None

    def __post_init__(self) -> None:
        for field_name, maximum_length in (
            ("external_batch_ref", 128),
            ("subject_namespace", 64),
        ):
            value = getattr(self, field_name)
            if value is None:
                continue
            normalized = str(value).strip()
            if not normalized:
                setattr(self, field_name, None)
                continue
            if len(normalized) > maximum_length:
                raise ValueError(f"{field_name} exceeds {maximum_length} characters")
            if "|" in normalized or any(ord(character) < 32 for character in normalized):
                raise ValueError(f"{field_name} contains a reserved delimiter or control character")
            setattr(self, field_name, normalized)
        if self.subject_namespace and not self.external_batch_ref:
            raise ValueError("subject_namespace requires external_batch_ref")

    @property
    def can_commit(self) -> bool:
        """Whether balance, critical structure, and control-total gates pass."""
        blocking_checks = {"IMP-005", "IMP-006", "IMP-008", "IMP-025"}
        if not self.is_balanced:
            return False
        return not any(
            check.check_code in blocking_checks and check.status.lower() == "fail"
            for check in self.checks
        )
