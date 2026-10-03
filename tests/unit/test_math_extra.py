import pytest
from decimal import Decimal
from app.engine.calc.math import (
    format_percentage_points,
    check_sum_of_rounded_discrepancy,
    Direction,
    Favourability,
    DisplayScale,
    NegativeFormat,
    GroupingFormat,
    RatioState,
)

def test_math_extensions():
    assert format_percentage_points("1.56", 1, True) == "+1.6 pp"
    assert format_percentage_points("-1.54", 1, True) == "-1.5 pp"
    assert format_percentage_points("0.0", 1, True) == "0.0 pp"

    res, disc, note = check_sum_of_rounded_discrepancy([Decimal("10.12"), Decimal("20.34")], Decimal("30.47"), 2)
    assert res is True
    assert note is not None

    res2, disc2, note2 = check_sum_of_rounded_discrepancy([Decimal("10.12"), Decimal("20.35")], Decimal("30.47"), 2)
    assert res2 is False
    assert note2 is None

    assert Direction.HIGHER_IS_FAVOURABLE == "higher_is_favourable"
    assert Favourability.FAVOURABLE == "favourable"
    assert DisplayScale.MILLIONS == 1_000_000
    assert NegativeFormat.PARENTHESES == "parentheses"
    assert GroupingFormat.INTERNATIONAL == "international"
    assert RatioState.VALID == "valid"
