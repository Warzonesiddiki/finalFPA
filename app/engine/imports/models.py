"""Data structures for parsing and importing files per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Dict, Any


@dataclass
class PreScanResult:
    file_name: str
    file_size_bytes: int
    file_checksum: str
    sheet_names: List[str]
    estimated_rows: int
    detected_encoding: Optional[str] = None
    detected_delimiter: Optional[str] = None
    header_row_candidate: int = 1
    sample_headers: List[str] = field(default_factory=list)
    has_banner: bool = False
    is_encrypted: bool = False


@dataclass
class ValidationIssue:
    check_code: str  # e.g. IMP-001..IMP-032
    severity: str    # high, medium, low
    message_slug: str
    message: str
    source_row_ref: Optional[str] = None
    raw_values: Optional[Dict[str, Any]] = None


@dataclass
class ValidationCheckReport:
    check_code: str
    check_name: str
    status: str       # pass, fail, warn, skipped
    severity: str     # high, medium, low
    offending_count: int
    message_slug: Optional[str] = None
    skip_reason: Optional[str] = None
    sample_rows: List[Dict[str, Any]] = field(default_factory=list)
    detail: Optional[str] = None
    weight: Optional[Decimal] = None

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
    cost_center_code: Optional[str]
    project_code: Optional[str]
    vendor_code: Optional[str]
    invoice_no: Optional[str]
    description: Optional[str]
    debit: Decimal
    credit: Decimal
    net_amount: Decimal
    currency_code: str
    document_date: Optional[str] = None
    line_no: int = 1
    journal_category: Optional[str] = None
    raw_values: Dict[str, Any] = field(default_factory=dict)
    is_zero_amount: bool = False
    period_code: Optional[str] = None
    # Assigned on import; required for cross-batch exception checks.
    import_batch_id: Optional[int] = None


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
    checks: List[ValidationCheckReport] = field(default_factory=list)
    quarantined_rows: List[Dict[str, Any]] = field(default_factory=list)
    balance_tolerance: Decimal = Decimal("0.00")
    sheet_name: str = "Data"

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
