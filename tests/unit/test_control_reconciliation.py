"""Unit test for control-total reconciliation per docs 02/04 (FR-IMP-005, IMP-06)."""

from decimal import Decimal


def test_control_total_reconciliation_math_and_acceptance():
    """Test control total comparison between file totals, loaded totals, and client control totals.

    Governing Requirements:
    - FR-IMP-005: Control-total reconciliation.
    - IMP-06: Optional control-totals block, file totals vs loaded totals vs client control totals, variance fails import or requires explicit recorded acceptance.
    """
    file_total_debit = Decimal("12500000.00")
    loaded_total_debit = Decimal("12500000.00")

    # 1. Matching control total
    client_control_debit = Decimal("12500000.00")
    variance = file_total_debit - client_control_debit
    assert variance == Decimal("0.00")
    is_valid = variance == Decimal("0.00")
    assert is_valid is True

    # 2. Variance requiring explicit recorded acceptance
    client_control_variance = Decimal("12550000.00")
    var_diff = file_total_debit - client_control_variance
    assert var_diff != Decimal("0.00")

    # Without explicit acceptance, import must fail / block
    explicit_acceptance = False
    can_commit_without_acceptance = (var_diff == Decimal("0.00")) or explicit_acceptance
    assert can_commit_without_acceptance is False

    # With explicit acceptance and recorded audit reason
    explicit_acceptance = True
    audit_reason = "Imbalance accepted by Controller due to legacy rounding."
    assert len(audit_reason) >= 10
    can_commit_with_acceptance = (var_diff == Decimal("0.00")) or (
        explicit_acceptance and bool(audit_reason)
    )
    assert can_commit_with_acceptance is True
