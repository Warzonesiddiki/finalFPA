"""Data quality score engine per 05_CALCULATION_SPEC.md §8 and 04 §10 (CALC-050).

Formula:
  For a batch, let R = the set of checks that ran (submitted as 'pass', 'fail' or 'warn';
  'skipped' checks are excluded from both numerator and denominator), w_c = the configurable
  weight of check c (defaults: High = 10, Medium = 5, Low = 2), and d_c = the deduction factor:
    pass: 0.0
    fail: 1.0
    warn: 0.5
    skipped: excluded from R

  score = round_half_up( 100 × ( 1 − Σ_{c∈R} ( w_c × d_c ) / Σ_{c∈R} w_c ) , 0 )

Guarantees (§8.2):
  1. Bounded: Any failed High-severity check deducts at least 10/238 ≈ 4.2%,
     so a batch with one failed High check cannot score above 96.
  2. Decomposable: The score is always displayed alongside the list of failed checks and their weights.
  3. Deterministic: Same checks + same weights -> same score.
  4. Versioned: Weight changes are project settings with history; a score always states the version.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Union


BASE_SCORE = Decimal("100")
ROUND_UNIT = Decimal("1")

# Default severity weights per 05 §8.1 and §8.3
DEFAULT_SEVERITY_WEIGHTS: Dict[str, Decimal] = {
    "high": Decimal("10"),
    "medium": Decimal("5"),
    "low": Decimal("2"),
}

# Deduction factors per 05 §8.1
DEDUCTION_FACTORS: Dict[str, Decimal] = {
    "pass": Decimal("0.0"),
    "warn": Decimal("0.5"),
    "fail": Decimal("1.0"),
}


@dataclass(frozen=True)
class CheckCatalogueEntry:
    """Canonical validation check entry per 04_SOURCE_MAPPING_AND_IMPORT_SPEC.md §10."""
    code: str
    name: str
    scope: str       # 'F' (file), 'R' (row), 'W' (warning)
    severity: str    # 'high', 'medium', 'low'
    slug: str
    default_weight: Decimal


# The complete 32 validation checks from 04 §10 and 05 §8.3
# Totals: 18 High (180 wt), 10 Medium (50 wt), 4 Low (8 wt) -> Total 32 checks, 238 wt
CHECK_CATALOGUE: Dict[str, CheckCatalogueEntry] = {
    # High severity (18 checks, weight 10 each = 180)
    "IMP-001": CheckCatalogueEntry("IMP-001", "File readable and format supported", "F", "high", "import.unreadableFile", Decimal("10")),
    "IMP-004": CheckCatalogueEntry("IMP-004", "Header row detected", "F", "high", "import.noHeaderDetected", Decimal("10")),
    "IMP-005": CheckCatalogueEntry("IMP-005", "Required columns present after mapping", "F", "high", "import.missingRequiredColumns", Decimal("10")),
    "IMP-006": CheckCatalogueEntry("IMP-006", "Duplicate column headers resolved", "F", "high", "import.duplicateHeaders", Decimal("10")),
    "IMP-007": CheckCatalogueEntry("IMP-007", "Expected sheet present (per profile)", "F", "high", "import.sheetNotFound", Decimal("10")),
    "IMP-008": CheckCatalogueEntry("IMP-008", "Data range not empty", "F", "high", "import.noDataRows", Decimal("10")),
    "IMP-009": CheckCatalogueEntry("IMP-009", "Workbook not encrypted / not unreadable", "F", "high", "import.encryptedFile", Decimal("10")),
    "IMP-010": CheckCatalogueEntry("IMP-010", "All required canonical fields mapped", "F", "high", "import.mappingIncomplete", Decimal("10")),
    "IMP-011": CheckCatalogueEntry("IMP-011", "Unmapped-row share below 90%", "F", "high", "import.unmappedThreshold", Decimal("10")),
    "IMP-014": CheckCatalogueEntry("IMP-014", "Date values parsed", "R", "high", "import.dateUnparsed", Decimal("10")),
    "IMP-015": CheckCatalogueEntry("IMP-015", "Ambiguous date formats confirmed", "F", "high", "import.ambiguousDate", Decimal("10")),
    "IMP-016": CheckCatalogueEntry("IMP-016", "Numeric values parsed", "R", "high", "import.numberUnparsed", Decimal("10")),
    "IMP-018": CheckCatalogueEntry("IMP-018", "Period resolved against the fiscal calendar", "R", "high", "import.periodNotInCalendar", Decimal("10")),
    "IMP-020": CheckCatalogueEntry("IMP-020", "Currency matches the project currency", "R", "high", "import.mixedCurrency", Decimal("10")),
    "IMP-023": CheckCatalogueEntry("IMP-023", "Debit = credit within tolerance, per file/entity/period", "F", "high", "import.balanceMismatch", Decimal("10")),
    "IMP-024": CheckCatalogueEntry("IMP-024", "Row-count reconciliation equation", "F", "high", "import.countMismatch", Decimal("10")),
    "IMP-025": CheckCatalogueEntry("IMP-025", "Control-total variance within tolerance (when provided)", "F", "high", "import.controlTotalVariance", Decimal("10")),
    "IMP-029": CheckCatalogueEntry("IMP-029", "File checksum not previously committed", "F", "high", "import.alreadyImported", Decimal("10")),

    # Medium severity (10 checks, weight 5 each = 50)
    "IMP-002": CheckCatalogueEntry("IMP-002", "File size within configured limit", "F", "medium", "import.fileTooLarge", Decimal("5")),
    "IMP-003": CheckCatalogueEntry("IMP-003", "Row count within configured limit", "F", "medium", "import.rowLimitExceeded", Decimal("5")),
    "IMP-012": CheckCatalogueEntry("IMP-012", "Dimension-string tokens parsed", "R", "medium", "import.dimensionUnparsed", Decimal("5")),
    "IMP-013": CheckCatalogueEntry("IMP-013", "Unknown/unmapped account codes", "W", "medium", "import.unknownAccounts", Decimal("5")),
    "IMP-019": CheckCatalogueEntry("IMP-019", "Dates inside configured fiscal year", "R", "medium", "import.dateOutsideFiscalYear", Decimal("5")),
    "IMP-026": CheckCatalogueEntry("IMP-026", "Budget sum matches approved total (when provided)", "F", "medium", "import.approvedTotalVariance", Decimal("5")),
    "IMP-027": CheckCatalogueEntry("IMP-027", "Within-file duplicate candidates reported", "R", "medium", "import.duplicateCandidates", Decimal("5")),
    "IMP-028": CheckCatalogueEntry("IMP-028", "Cross-batch duplicate candidates reported", "R", "medium", "import.crossBatchDuplicates", Decimal("5")),
    "IMP-031": CheckCatalogueEntry("IMP-031", "Budget coverage matrix reported", "F", "medium", "import.budgetCoverageGap", Decimal("5")),
    "IMP-032": CheckCatalogueEntry("IMP-032", "Budget/forecast duplicate lines on uniqueness key", "R", "medium", "import.duplicateBudgetLines", Decimal("5")),

    # Low severity (4 checks, weight 2 each = 8)
    "IMP-017": CheckCatalogueEntry("IMP-017", "Sign / Cr-Dr interpretation applied", "R", "low", "import.signRuleApplied", Decimal("2")),
    "IMP-021": CheckCatalogueEntry("IMP-021", "Zero-amount rows noted", "R", "low", "import.zeroAmountRows", Decimal("2")),
    "IMP-022": CheckCatalogueEntry("IMP-022", "Debit and credit not both populated", "R", "low", "import.bothDebitCredit", Decimal("2")),
    "IMP-030": CheckCatalogueEntry("IMP-030", "Inactive cost centre usage noted", "R", "low", "import.inactiveCostCentre", Decimal("2")),
}


@dataclass
class CheckDeductionDetail:
    """Detail for a single check evaluated in data quality scoring."""
    check_code: str
    check_name: str
    status: str
    severity: str
    weight: Decimal
    deduction_factor: Decimal
    deduction_amount: Decimal
    offending_count: int = 0
    skip_reason: Optional[str] = None
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_code": self.check_code,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "weight": float(self.weight),
            "deduction_factor": float(self.deduction_factor),
            "deduction_amount": float(self.deduction_amount),
            "offending_count": self.offending_count,
            "skip_reason": self.skip_reason,
            "detail": self.detail,
        }


@dataclass
class SeverityBreakdown:
    """Breakdown of checks and weights aggregated by severity level."""
    severity: str
    checks_run_count: int = 0
    checks_skipped_count: int = 0
    passed_count: int = 0
    warned_count: int = 0
    failed_count: int = 0
    total_weight: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "checks_run_count": self.checks_run_count,
            "checks_skipped_count": self.checks_skipped_count,
            "passed_count": self.passed_count,
            "warned_count": self.warned_count,
            "failed_count": self.failed_count,
            "total_weight": float(self.total_weight),
            "total_deductions": float(self.total_deductions),
        }


@dataclass
class QualityScoreResult:
    """Result of Data Quality Score calculation (CALC-050)."""
    score: int
    raw_score: Decimal
    total_weight: Decimal
    total_deductions: Decimal
    checks_run_count: int
    checks_skipped_count: int
    passed_checks: List[CheckDeductionDetail] = field(default_factory=list)
    failed_checks: List[CheckDeductionDetail] = field(default_factory=list)
    warned_checks: List[CheckDeductionDetail] = field(default_factory=list)
    skipped_checks: List[CheckDeductionDetail] = field(default_factory=list)
    all_checks: List[CheckDeductionDetail] = field(default_factory=list)
    breakdown_by_severity: Dict[str, SeverityBreakdown] = field(default_factory=dict)
    weight_set_version: str = "1.0"
    guarantee_held: bool = True

    def __int__(self) -> int:
        return self.score

    def __float__(self) -> float:
        return float(self.raw_score)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, int):
            return self.score == other
        if isinstance(other, Decimal):
            return self.raw_score == other or Decimal(self.score) == other
        return super().__eq__(other)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "raw_score": float(self.raw_score),
            "total_weight": float(self.total_weight),
            "total_deductions": float(self.total_deductions),
            "checks_run_count": self.checks_run_count,
            "checks_skipped_count": self.checks_skipped_count,
            "weight_set_version": self.weight_set_version,
            "guarantee_held": self.guarantee_held,
            "failed_checks": [c.to_dict() for c in self.failed_checks],
            "warned_checks": [c.to_dict() for c in self.warned_checks],
            "passed_checks": [c.to_dict() for c in self.passed_checks],
            "skipped_checks": [c.to_dict() for c in self.skipped_checks],
            "breakdown_by_severity": {k: v.to_dict() for k, v in self.breakdown_by_severity.items()},
        }


def _extract_field(item: Any, field_name: str, default: Any = None) -> Any:
    """Helper to extract an attribute from an object or dictionary."""
    if isinstance(item, dict):
        return item.get(field_name, default)
    return getattr(item, field_name, default)


def _resolve_check_metadata(
    raw_code: Optional[str],
    raw_name: Optional[str],
    raw_severity: Optional[str],
) -> tuple[str, str, str]:
    """Resolve code, display name, and severity using catalog defaults when possible."""
    code = (raw_code or "").strip().upper()
    cat_entry = CHECK_CATALOGUE.get(code)

    if cat_entry:
        name = raw_name or cat_entry.name
        severity = (raw_severity or cat_entry.severity).strip().lower()
    else:
        name = raw_name or code or "Custom Check"
        severity = (raw_severity or "medium").strip().lower()

    if severity not in DEFAULT_SEVERITY_WEIGHTS:
        severity = "medium"

    return code, name, severity


def _resolve_weight(
    code: str,
    severity: str,
    raw_weight: Optional[Any],
    weights_by_code: Optional[Dict[str, Any]] = None,
    weights_by_severity: Optional[Dict[str, Any]] = None,
) -> Decimal:
    """Resolve the effective Decimal weight for a validation check."""
    # 1. Check code override
    if weights_by_code and code in weights_by_code:
        return Decimal(str(weights_by_code[code]))

    # 2. Check severity override
    if weights_by_severity and severity in weights_by_severity:
        return Decimal(str(weights_by_severity[severity]))

    # 3. Explicit check instance weight
    if raw_weight is not None:
        return Decimal(str(raw_weight))

    # 4. Canonical catalog default
    if code in CHECK_CATALOGUE:
        return CHECK_CATALOGUE[code].default_weight

    # 5. Default by severity
    return DEFAULT_SEVERITY_WEIGHTS.get(severity, Decimal("5"))


def calculate_quality_score(
    checks: Union[Iterable[Any], Any],
    weights_by_code: Optional[Dict[str, Any]] = None,
    weights_by_severity: Optional[Dict[str, Any]] = None,
    weight_set_version: str = "1.0",
) -> QualityScoreResult:
    """Calculate Data Quality Score (0..100) per 05_CALCULATION_SPEC.md §8 (CALC-050).

    Args:
        checks: Iterable of check objects, reports, dicts, or an ImportBatchResult.
        weights_by_code: Optional mapping of check_code -> custom weight.
        weights_by_severity: Optional mapping of severity ('high', 'medium', 'low') -> custom weight.
        weight_set_version: Version label for the weights used.

    Returns:
        QualityScoreResult with the rounded score, raw Decimal score, and complete breakdown.
    """
    # Support passing an ImportBatchResult or container directly
    if hasattr(checks, "checks") and isinstance(checks.checks, list):
        check_list = checks.checks
    elif isinstance(checks, Iterable) and not isinstance(checks, (str, bytes)):
        check_list = list(checks)
    else:
        check_list = [checks]

    total_weight = Decimal("0")
    total_deductions = Decimal("0")
    checks_run_count = 0
    checks_skipped_count = 0

    passed_checks: List[CheckDeductionDetail] = []
    failed_checks: List[CheckDeductionDetail] = []
    warned_checks: List[CheckDeductionDetail] = []
    skipped_checks: List[CheckDeductionDetail] = []
    all_checks: List[CheckDeductionDetail] = []

    breakdowns: Dict[str, SeverityBreakdown] = {
        "high": SeverityBreakdown(severity="high"),
        "medium": SeverityBreakdown(severity="medium"),
        "low": SeverityBreakdown(severity="low"),
    }

    for item in check_list:
        raw_code = _extract_field(item, "check_code")
        raw_name = _extract_field(item, "check_name")
        raw_status = _extract_field(item, "status", "pass")
        raw_severity = _extract_field(item, "severity")
        raw_weight = _extract_field(item, "weight")
        offending_count = int(_extract_field(item, "offending_count", 0) or 0)
        skip_reason = _extract_field(item, "skip_reason")
        detail = _extract_field(item, "detail")

        code, name, severity = _resolve_check_metadata(raw_code, raw_name, raw_severity)
        status = str(raw_status).strip().lower()

        if severity not in breakdowns:
            breakdowns[severity] = SeverityBreakdown(severity=severity)
        sb = breakdowns[severity]

        weight = _resolve_weight(code, severity, raw_weight, weights_by_code, weights_by_severity)

        if status == "skipped":
            checks_skipped_count += 1
            sb.checks_skipped_count += 1
            detail_obj = CheckDeductionDetail(
                check_code=code,
                check_name=name,
                status=status,
                severity=severity,
                weight=weight,
                deduction_factor=Decimal("0.0"),
                deduction_amount=Decimal("0.0"),
                offending_count=offending_count,
                skip_reason=skip_reason,
                detail=detail,
            )
            skipped_checks.append(detail_obj)
            all_checks.append(detail_obj)
            continue

        if status not in DEDUCTION_FACTORS:
            raise ValueError(f"Unknown validation check status '{raw_status}' for check '{code}'")

        d_factor = DEDUCTION_FACTORS[status]
        deduction = weight * d_factor

        checks_run_count += 1
        total_weight += weight
        total_deductions += deduction

        sb.checks_run_count += 1
        sb.total_weight += weight
        sb.total_deductions += deduction

        detail_obj = CheckDeductionDetail(
            check_code=code,
            check_name=name,
            status=status,
            severity=severity,
            weight=weight,
            deduction_factor=d_factor,
            deduction_amount=deduction,
            offending_count=offending_count,
            skip_reason=skip_reason,
            detail=detail,
        )

        all_checks.append(detail_obj)

        if status == "pass":
            sb.passed_count += 1
            passed_checks.append(detail_obj)
        elif status == "warn":
            sb.warned_count += 1
            warned_checks.append(detail_obj)
        elif status == "fail":
            sb.failed_count += 1
            failed_checks.append(detail_obj)

    # Base score = 100
    if total_weight == Decimal("0"):
        raw_score = BASE_SCORE
    else:
        # score = 100 * (1 - sum(w_c * d_c) / sum(w_c))
        ratio = total_deductions / total_weight
        raw_score = BASE_SCORE * (Decimal("1") - ratio)
        if raw_score < Decimal("0"):
            raw_score = Decimal("0")
        elif raw_score > BASE_SCORE:
            raw_score = BASE_SCORE

    rounded_score = int(raw_score.quantize(ROUND_UNIT, rounding=ROUND_HALF_UP))

    # Guarantee check (§8.2.1): Any failed High check cannot score above 96 (under default weights)
    has_high_failure = any(c.severity == "high" for c in failed_checks)
    guarantee_held = True
    if has_high_failure and not weights_by_code and not weights_by_severity:
        # With default weights, 1 high failure deducts >= 10/238 (approx 4.2%), capping score at 96
        guarantee_held = (rounded_score <= 96)

    return QualityScoreResult(
        score=rounded_score,
        raw_score=raw_score,
        total_weight=total_weight,
        total_deductions=total_deductions,
        checks_run_count=checks_run_count,
        checks_skipped_count=checks_skipped_count,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        warned_checks=warned_checks,
        skipped_checks=skipped_checks,
        all_checks=all_checks,
        breakdown_by_severity=breakdowns,
        weight_set_version=weight_set_version,
        guarantee_held=guarantee_held,
    )


def create_f12_fixture_checks() -> List[Dict[str, Any]]:
    """Build check list corresponding to Golden Fixture F12 in 05 §12.

    Fixture F12:
      - All 32 checks run (Σ weights = 238)
      - IMP-014 (High, weight 10): fail (d = 1.0) -> deduction 10
      - IMP-021 (Low, weight 2): warn (d = 0.5) -> deduction 1
      - All other 30 checks: pass (d = 0.0)
      - Total deductions: 11
      - Raw score: 100 * (1 - 11/238) = 95.378151...
      - Displayed score: 95
    """
    checks: List[Dict[str, Any]] = []
    for code, entry in CHECK_CATALOGUE.items():
        if code == "IMP-014":
            checks.append({
                "check_code": code,
                "check_name": entry.name,
                "status": "fail",
                "severity": entry.severity,
                "weight": entry.default_weight,
                "offending_count": 8,
                "detail": "8 date values unparsed",
            })
        elif code == "IMP-021":
            checks.append({
                "check_code": code,
                "check_name": entry.name,
                "status": "warn",
                "severity": entry.severity,
                "weight": entry.default_weight,
                "offending_count": 12,
                "detail": "12 zero-amount rows noted",
            })
        else:
            checks.append({
                "check_code": code,
                "check_name": entry.name,
                "status": "pass",
                "severity": entry.severity,
                "weight": entry.default_weight,
                "offending_count": 0,
            })
    return checks
