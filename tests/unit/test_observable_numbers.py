"""Unit tests for observable calculations of the twelve analyst numbers (ENG-07).

Acceptance criteria:
- The twelve canonical analyst numbers come out of app/engine, not out of a document.
- One public function per canonical number returns structured ObservableNumber data.
- Inputs and intermediate hops operate on Decimal without rounding drift.
- A test fails if any hop introduces float operations or rounding drift.
"""

from decimal import Decimal

import pytest

from app.engine.calc.math import Direction, Favourability
from app.engine.calc.observable import (
    ObservableNumber,
    get_twelve_observable_numbers,
    observe_number_1_tb_balance,
    observe_number_2_net_amount,
    observe_number_3_variance,
    observe_number_4_variance_pct,
    observe_number_5_favourability,
    observe_number_6_percentage_points,
    observe_number_7_bridge_residual,
    observe_number_8_dq_score,
    observe_number_9_gross_margin,
    observe_number_10_budget_burn,
    observe_number_11_mape_lite,
    observe_number_12_rounding_footnote,
)


def test_get_twelve_observable_numbers_returns_all_twelve():
    """Verify all 12 observable numbers are returned with correct IDs and types."""
    numbers = get_twelve_observable_numbers()
    assert len(numbers) == 12
    # Verify no float drift by checking they are exactly their Decimal values
    assert numbers[0].value == Decimal("0.00"), f"number 0 value: {numbers[0].value}"
    assert numbers[1].value == Decimal("150000.50"), f"number 1 value: {numbers[1].value}"
    assert numbers[2].value == Decimal("800000.00"), f"number 2 value: {numbers[2].value}"
    assert numbers[3].value == Decimal("8.0"), f"number 3 value: {numbers[3].value}"
    assert numbers[4].value == Favourability.FAVOURABLE, f"number 4 value: {numbers[4].value}"
    assert numbers[5].value == Decimal("1.5"), f"number 5 value: {numbers[5].value}"
    assert numbers[6].value == Decimal("16645000.00"), f"number 6 value: {numbers[6].value}"
    # number 7 is DQ score, raw score
    # Bypass type checker strictly for the test by fetching correctly
    raw = getattr(numbers[7].value, "raw_score", None)
    assert raw == Decimal("95.37815126050420168067226891"), f"number 7 raw_score: {raw}"
    assert numbers[8].value == Decimal("0.400000"), f"number 8 value: {numbers[8].value}"
    assert numbers[9].value == Decimal("0.258000"), f"number 9 value: {numbers[9].value}"
    assert numbers[10].value == Decimal("0.050000"), f"number 10 value: {numbers[10].value}"
    assert numbers[11].value == Decimal("0.01"), f"number 11 value: {numbers[11].value}"

    for idx, num in enumerate(numbers, start=1):
        assert isinstance(num, ObservableNumber)
        assert num.id == idx
        assert len(num.hops) >= 2
        d = num.to_dict()
        assert "value" in d
        assert "inputs" in d
        assert "hops" in d


def test_observe_number_1_tb_balance():
    obs = observe_number_1_tb_balance(Decimal("10800000.00"), Decimal("10800000.00"))
    assert obs.value == Decimal("0.00")
    assert obs.formula_id == "CALC-071"
    assert obs.inputs["debits"] == Decimal("10800000.00")
    assert obs.inputs["credits"] == Decimal("10800000.00")


def test_observe_number_2_net_amount():
    obs = observe_number_2_net_amount(Decimal("150000.50"), Decimal("0.00"))
    assert obs.value == Decimal("150000.50")
    assert obs.formula_id == "CALC-007"


def test_observe_number_3_variance():
    obs = observe_number_3_variance(Decimal("10800000.00"), Decimal("10000000.00"))
    assert obs.value == Decimal("800000.00")
    assert obs.formula_id == "CALC-010"


def test_observe_number_4_variance_pct():
    obs = observe_number_4_variance_pct(Decimal("10800000.00"), Decimal("10000000.00"))
    assert obs.value in (Decimal("8.0"), Decimal("8.0000"), Decimal("8.00"))
    assert obs.formula_id == "CALC-011"


def test_observe_number_5_favourability():
    obs = observe_number_5_favourability(
        Decimal("10800000.00"), Decimal("10000000.00"), Direction.HIGHER_IS_FAVOURABLE
    )
    assert obs.value == Favourability.FAVOURABLE
    assert obs.formula_id == "CALC-012"


def test_observe_number_6_percentage_points():
    obs = observe_number_6_percentage_points(Decimal("40.0"), Decimal("38.5"))
    assert obs.value == Decimal("1.5")
    assert obs.formula_id == "CALC-013"


def test_observe_number_7_bridge_residual():
    obs = observe_number_7_bridge_residual(
        Decimal("15770000.00"), [Decimal("250000.00"), Decimal("125000.00")], Decimal("500000.00")
    )
    assert obs.value == Decimal("16645000.00")
    assert obs.formula_id == "CALC-042"


def test_observe_number_8_dq_score():
    obs = observe_number_8_dq_score()
    assert hasattr(obs.value, "score") and obs.value.score == 95
    assert obs.formula_id == "CALC-050"


def test_observe_number_9_gross_margin():
    obs = observe_number_9_gross_margin(Decimal("1000000.00"), Decimal("600000.00"))
    assert obs.value in (Decimal("0.4"), Decimal("0.4000"))
    assert obs.formula_id == "KPI-001"


def test_observe_number_10_budget_burn():
    obs = observe_number_10_budget_burn(Decimal("2580000.00"), Decimal("10000000.00"))
    assert obs.value in (Decimal("0.258"), Decimal("0.2580"))
    assert obs.formula_id == "KPI-004"


def test_observe_number_11_mape_lite():
    obs = observe_number_11_mape_lite([(Decimal("100000.00"), Decimal("95000.00"))])
    assert obs.value in (Decimal("0.05"), Decimal("0.0500"))
    assert obs.formula_id == "CALC-069"


def test_observe_number_12_rounding_footnote():
    obs = observe_number_12_rounding_footnote([Decimal("10.004"), Decimal("10.004")])
    assert obs.value == Decimal("0.01")
    assert obs.formula_id == "CALC-031"


def test_falsification_float_input_rejected():
    """Falsification test: floating point inputs are rejected to prevent rounding drift."""
    with pytest.raises(AssertionError):
        observe_number_1_tb_balance(10800000.0, Decimal("10800000.00"))  # type: ignore

    with pytest.raises(AssertionError):
        observe_number_2_net_amount(150000.5, Decimal("0.00"))  # type: ignore

    with pytest.raises(AssertionError):
        observe_number_3_variance(10800000.0, Decimal("10000000.00"))  # type: ignore

    with pytest.raises(AssertionError):
        observe_number_6_percentage_points(40.0, Decimal("38.5"))  # type: ignore
