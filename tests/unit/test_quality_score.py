"""Unit tests for Data Quality Score engine per 05_CALCULATION_SPEC.md §8 & §12 (CALC-050)."""

from decimal import Decimal

import pytest

from app.engine.calc.quality_score import (
    CHECK_CATALOGUE,
    calculate_quality_score,
    create_f12_fixture_checks,
)
from app.engine.imports.models import ImportBatchResult, ValidationCheckReport


def test_catalogue_spec_alignment():
    """Verify check catalogue has 32 checks, matching 04 §10 and 05 §8.3 exactly:
    18 High (180 wt), 10 Medium (50 wt), 4 Low (8 wt) -> Total 32 checks, 238 wt.
    """
    assert len(CHECK_CATALOGUE) == 32

    high_checks = [c for c in CHECK_CATALOGUE.values() if c.severity == "high"]
    medium_checks = [c for c in CHECK_CATALOGUE.values() if c.severity == "medium"]
    low_checks = [c for c in CHECK_CATALOGUE.values() if c.severity == "low"]

    assert len(high_checks) == 18
    assert len(medium_checks) == 10
    assert len(low_checks) == 4

    total_high_wt = sum(c.default_weight for c in high_checks)
    total_med_wt = sum(c.default_weight for c in medium_checks)
    total_low_wt = sum(c.default_weight for c in low_checks)

    assert total_high_wt == Decimal("180")
    assert total_med_wt == Decimal("50")
    assert total_low_wt == Decimal("8")
    assert (total_high_wt + total_med_wt + total_low_wt) == Decimal("238")


def test_golden_fixture_f12_exact():
    """Verify Golden Fixture F12 from 05_CALCULATION_SPEC.md §12.

    Inputs:
      - All 32 checks run (Σ weights = 238)
      - IMP-014 (High, weight 10): fail (d = 1.0) -> deduction 10
      - IMP-021 (Low, weight 2): warn (d = 0.5) -> deduction 1
      - All other 30 checks: pass (d = 0.0)
    Expected output:
      - Deduction total: 11
      - Raw score: 100 × (1 − 11/238) = 95.378151…
      - Displayed score (half-up, 0 dp): 95
      - Guarantee check: 95 ≤ 96
    """
    checks = create_f12_fixture_checks()
    result = calculate_quality_score(checks)

    # 1. Total weight and deductions
    assert result.total_weight == Decimal("238")
    assert result.total_deductions == Decimal("11")
    assert result.checks_run_count == 32
    assert result.checks_skipped_count == 0

    # 2. Raw score exact Decimal check
    expected_raw = Decimal("100") * (Decimal("1") - Decimal("11") / Decimal("238"))
    assert result.raw_score == expected_raw
    # Check prefix 95.378151...
    assert str(result.raw_score).startswith("95.378151")

    # 3. Displayed score rounded half-up to 0 dp
    assert result.score == 95
    assert int(result) == 95
    assert result == 95

    # 4. Guarantee check (§8.2.1)
    assert result.guarantee_held is True
    assert result.score <= 96

    # 5. Decomposability (§8.2.2)
    assert len(result.failed_checks) == 1
    assert result.failed_checks[0].check_code == "IMP-014"
    assert result.failed_checks[0].offending_count == 8
    assert result.failed_checks[0].weight == Decimal("10")
    assert result.failed_checks[0].deduction_amount == Decimal("10")

    assert len(result.warned_checks) == 1
    assert result.warned_checks[0].check_code == "IMP-021"
    assert result.warned_checks[0].offending_count == 12
    assert result.warned_checks[0].weight == Decimal("2")
    assert result.warned_checks[0].deduction_amount == Decimal("1")

    assert len(result.passed_checks) == 30


def test_guarantee_single_high_failure_cannot_score_above_96():
    """Verify §8.2 Guarantee 1: Any failed High check cannot score above 96."""
    # Test each of the 18 High checks failing individually
    for code, entry in CHECK_CATALOGUE.items():
        if entry.severity != "high":
            continue

        checks = []
        for c_code, c_entry in CHECK_CATALOGUE.items():
            status = "fail" if c_code == code else "pass"
            checks.append(
                {
                    "check_code": c_code,
                    "status": status,
                    "severity": c_entry.severity,
                }
            )

        result = calculate_quality_score(checks)
        # Raw score = 100 * (1 - 10/238) = 95.7983... -> rounds half-up to 96
        assert result.total_deductions == Decimal("10")
        assert result.score == 96
        assert result.score <= 96
        assert result.guarantee_held is True


def test_all_pass_gives_perfect_100():
    """All 32 checks passing should yield a score of 100."""
    checks = [{"check_code": code, "status": "pass"} for code in CHECK_CATALOGUE]
    result = calculate_quality_score(checks)

    assert result.score == 100
    assert result.raw_score == Decimal("100")
    assert result.total_deductions == Decimal("0")
    assert result.total_weight == Decimal("238")
    assert len(result.passed_checks) == 32
    assert len(result.failed_checks) == 0
    assert len(result.warned_checks) == 0


def test_all_fail_gives_zero():
    """All 32 checks failing should yield a score of 0."""
    checks = [{"check_code": code, "status": "fail"} for code in CHECK_CATALOGUE]
    result = calculate_quality_score(checks)

    assert result.score == 0
    assert result.raw_score == Decimal("0")
    assert result.total_deductions == Decimal("238")
    assert result.total_weight == Decimal("238")
    assert len(result.failed_checks) == 32


def test_skipped_checks_excluded_from_numerator_and_denominator():
    """Skipped checks must be excluded from both numerator and denominator (§8.1)."""
    # Run 30 checks, skip 2 High checks (IMP-001 and IMP-004)
    checks = []
    for code, _entry in CHECK_CATALOGUE.items():
        if code in ("IMP-001", "IMP-004"):
            checks.append(
                {
                    "check_code": code,
                    "status": "skipped",
                    "skip_reason": "Not applicable for source type",
                }
            )
        else:
            checks.append({"check_code": code, "status": "pass"})

    result = calculate_quality_score(checks)

    # Total weight should be 238 - 10 - 10 = 218
    assert result.total_weight == Decimal("218")
    assert result.total_deductions == Decimal("0")
    assert result.checks_run_count == 30
    assert result.checks_skipped_count == 2
    assert result.score == 100
    assert len(result.skipped_checks) == 2
    assert result.skipped_checks[0].skip_reason == "Not applicable for source type"


def test_all_skipped_checks_defaults_to_100():
    """When all checks are skipped, score should default to base 100."""
    checks = [{"check_code": code, "status": "skipped"} for code in CHECK_CATALOGUE]
    result = calculate_quality_score(checks)

    assert result.score == 100
    assert result.raw_score == Decimal("100")
    assert result.total_weight == Decimal("0")
    assert result.total_deductions == Decimal("0")
    assert result.checks_run_count == 0
    assert result.checks_skipped_count == 32


def test_custom_weights_by_code_and_severity():
    """Verify weight override by check code and by severity."""
    # Test severity override: High = 20, Medium = 10, Low = 4
    custom_severity_weights = {
        "high": Decimal("20"),
        "medium": Decimal("10"),
        "low": Decimal("4"),
    }
    checks = create_f12_fixture_checks()
    result = calculate_quality_score(checks, weights_by_severity=custom_severity_weights)

    # 18*20 + 10*10 + 4*4 = 360 + 100 + 16 = 476
    assert result.total_weight == Decimal("476")
    # IMP-014 fail: 20; IMP-021 warn: 4 * 0.5 = 2 -> total deductions = 22
    assert result.total_deductions == Decimal("22")
    expected_raw = Decimal("100") * (Decimal("1") - Decimal("22") / Decimal("476"))
    assert result.raw_score == expected_raw
    assert result.score == 95

    # Test specific code override
    code_overrides = {"IMP-014": Decimal("50")}
    result_override = calculate_quality_score(checks, weights_by_code=code_overrides)
    # Total weight = 238 - 10 + 50 = 278
    assert result_override.total_weight == Decimal("278")
    # Deductions = 50 + 1 = 51
    assert result_override.total_deductions == Decimal("51")


def test_validation_check_report_objects():
    """Verify interoperability with ValidationCheckReport domain models."""
    checks = [
        ValidationCheckReport(
            check_code="IMP-001",
            check_name="File readable",
            status="pass",
            severity="high",
            offending_count=0,
        ),
        ValidationCheckReport(
            check_code="IMP-014",
            check_name="Date values parsed",
            status="fail",
            severity="high",
            offending_count=5,
            detail="5 unparsed dates",
        ),
        ValidationCheckReport(
            check_code="IMP-021",
            check_name="Zero-amount rows",
            status="warn",
            severity="low",
            offending_count=2,
            detail="2 zero rows",
        ),
        ValidationCheckReport(
            check_code="IMP-025",
            check_name="Control totals",
            status="skipped",
            severity="high",
            offending_count=0,
            skip_reason="No control sheet",
        ),
    ]

    result = calculate_quality_score(checks)

    # Weights: IMP-001 (10), IMP-014 (10), IMP-021 (2) -> total weight = 22
    assert result.total_weight == Decimal("22")
    # Deductions: IMP-014 (10 * 1.0 = 10) + IMP-021 (2 * 0.5 = 1) -> 11
    assert result.total_deductions == Decimal("11")
    # Raw score = 100 * (1 - 11/22) = 50.0
    assert result.raw_score == Decimal("50")
    assert result.score == 50
    assert result.checks_run_count == 3
    assert result.checks_skipped_count == 1


def test_import_batch_result_container():
    """Verify calculate_quality_score can accept an ImportBatchResult directly."""
    batch = ImportBatchResult(
        batch_id=1,
        file_name="test.csv",
        file_checksum="abcd",
        source_type="csv",
        total_source_rows=10,
        loaded_count=10,
        quarantined_count=0,
        rejected_count=0,
        is_balanced=True,
        total_debit=Decimal("100"),
        total_credit=Decimal("100"),
        net_imbalance=Decimal("0"),
        checks=[
            ValidationCheckReport("IMP-001", "File readable", "pass", "high", 0),
            ValidationCheckReport("IMP-023", "Balanced", "pass", "high", 0),
        ],
    )

    result = calculate_quality_score(batch)
    assert result.score == 100
    assert result.total_weight == Decimal("20")


def test_case_insensitivity_and_invalid_status():
    """Status and severity should be case-insensitive; invalid status raises ValueError."""
    checks = [
        {"check_code": "imp-001", "status": "PASS", "severity": "HIGH"},
        {"check_code": "imp-014", "status": "FAIL", "severity": "High"},
        {"check_code": "imp-021", "status": "Warn", "severity": "LOW"},
        {"check_code": "imp-025", "status": "SKIPPED", "severity": "high"},
    ]
    result = calculate_quality_score(checks)
    assert result.checks_run_count == 3
    assert result.checks_skipped_count == 1
    assert len(result.passed_checks) == 1
    assert len(result.failed_checks) == 1
    assert len(result.warned_checks) == 1

    with pytest.raises(ValueError, match="Unknown validation check status 'unknown_status'"):
        calculate_quality_score([{"check_code": "IMP-001", "status": "unknown_status"}])


def test_result_to_dict_serialization():
    """Verify result serialization for API response and report integration."""
    checks = create_f12_fixture_checks()
    result = calculate_quality_score(checks)
    d = result.to_dict()

    assert d["score"] == 95
    assert isinstance(d["raw_score"], float)
    assert d["total_weight"] == 238.0
    assert d["total_deductions"] == 11.0
    assert d["checks_run_count"] == 32
    assert d["checks_skipped_count"] == 0
    assert d["guarantee_held"] is True
    assert len(d["failed_checks"]) == 1
    assert len(d["warned_checks"]) == 1
    assert len(d["passed_checks"]) == 30
    assert "high" in d["breakdown_by_severity"]
    assert "medium" in d["breakdown_by_severity"]
    assert "low" in d["breakdown_by_severity"]
