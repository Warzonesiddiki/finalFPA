"""Tests for ``app.engine.dedupe`` — normalisation and candidate blocking.

Two jobs here:

1. **Behaviour tests** written from the contract, not from the code. The normalisation
   expectations come from `docs/06` `EXC-007`'s clause (*"trim, upper-case, strip leading
   zeros and non-alphanumeric separators"*); the blocking expectations come from the shape
   every duplicate rule in `06` shares.
2. **The `R12` regression proof.** `BD-001` moved this logic out of the rule modules, so the
   rules must behave *identically* through the shared interface. That is asserted here on
   the primitives and in the rule suites (`test_rules_01_08.py`,
   `test_rules_catalog_001_008.py`) which are unchanged and still pass.

No ``Adapted from`` header: this is BUILD code (`BD-001`), not an adoption.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.engine.dedupe import (
    count_distinct,
    group_by_key,
    iter_candidate_groups,
    normalise_alnum_upper,
    normalise_invoice_no,
)


# ---------------------------------------------------------------------------
# normalise_alnum_upper
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  inv-88213 ", "INV88213"),
        ("INV/2026/0001", "INV20260001"),
        ("abc", "ABC"),
        ("A-B_C.D", "ABCD"),
        ("123", "123"),
        ("000123", "000123"),  # zero-stripping is normalise_invoice_no's job, not this step
        ("--", ""),
        ("", ""),
        (None, ""),
        ("   ", ""),
    ],
)
def test_normalise_alnum_upper(raw, expected):
    assert normalise_alnum_upper(raw) == expected


def test_normalise_alnum_upper_accepts_non_strings():
    assert normalise_alnum_upper(12345) == "12345"
    assert normalise_alnum_upper(Decimal("123.45")) == "12345"


# ---------------------------------------------------------------------------
# normalise_invoice_no — the EXC-007 clause
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # trim + upper + separators, in one call
        ("INV-88213", "INV88213"),
        ("inv 88213", "INV88213"),
        (" INV88213 ", "INV88213"),
        # leading zeros collapse only when they sit at the start of the alphanumeric
        # string: "000123" -> "123", but a *prefixed* number keeps its zeros, so
        # "INV-00088213" normalises to "INV00088213". That limit is the `06` clause as
        # written (see normalize.py); widening it is an R1 spec question, not a refactor.
        ("000123", "123"),
        ("000-INV", "INV"),
        (" inv-00088213 ", "INV00088213"),
        ("INV-0000", "INV0000"),
        # absent invoice number -> empty, so a caller can skip the row
        (None, ""),
        ("", ""),
        # a number WAS present, so the key is degenerate but the row is not skipped
        ("---", "0"),
        # all zeros: nothing survives the strip, so the value is returned as-is
        ("0", "0"),
        ("000", "000"),
    ],
)
def test_normalise_invoice_no(raw, expected):
    assert normalise_invoice_no(raw) == expected


def test_normalise_invoice_no_bare_zero_int_is_empty():
    """``0`` (int) is falsy, so it reads as "no invoice number" — unlike the string ``"0"``.

    This asymmetry is inherited from the code this replaced and is pinned deliberately: a
    silent flip would change which rows `EXC-007` blocks.
    """
    assert normalise_invoice_no(0) == ""
    assert normalise_invoice_no("0") == "0"


def test_normalise_invoice_no_collapses_the_same_invoice_on_different_layouts():
    """The practical point of the clause: three source spellings block as one key."""
    spellings = ["INV-88213", "inv 88213", " INV88213 "]
    assert {normalise_invoice_no(s) for s in spellings} == {"INV88213"}


# ---------------------------------------------------------------------------
# group_by_key
# ---------------------------------------------------------------------------
def test_group_by_key_preserves_input_order_within_a_group():
    rows = [("a", 1), ("b", 9), ("a", 2), ("a", 3)]
    groups = group_by_key(rows, key_of=lambda row: row[0])
    assert groups["a"] == [("a", 1), ("a", 2), ("a", 3)]
    assert groups["b"] == [("b", 9)]


def test_group_by_key_preserves_first_seen_group_order():
    rows = [("z", 1), ("a", 2), ("m", 3)]
    assert list(group_by_key(rows, key_of=lambda row: row[0])) == ["z", "a", "m"]


def test_group_by_key_of_empty_input():
    assert group_by_key([], key_of=lambda row: row) == {}


# ---------------------------------------------------------------------------
# iter_candidate_groups
# ---------------------------------------------------------------------------
def _groups_to_dict(pairs):
    return {key: [row for row in rows] for key, rows in pairs}


def test_iter_candidate_groups_filters_by_the_predicate():
    rows = [("a", 1), ("a", 2), ("b", 3)]
    got = _groups_to_dict(
        iter_candidate_groups(rows, key_of=lambda r: r[0], is_candidate=lambda _k, rs: len(rs) >= 2)
    )
    assert got == {"a": [("a", 1), ("a", 2)]}


def test_iter_candidate_groups_without_order_by_uses_first_seen_order():
    rows = [("z", 1), ("z", 2), ("a", 3), ("a", 4)]
    keys = [
        key
        for key, _ in iter_candidate_groups(
            rows, key_of=lambda r: r[0], is_candidate=lambda _k, rs: len(rs) >= 2
        )
    ]
    assert keys == ["z", "a"]


def test_iter_candidate_groups_honours_order_by():
    """Determinism matters: the harness compares a finding list against a corpus."""
    rows = [("z", 1), ("z", 2), ("a", 3), ("a", 4)]
    keys = [
        key
        for key, _ in iter_candidate_groups(
            rows,
            key_of=lambda r: r[0],
            is_candidate=lambda _k, rs: len(rs) >= 2,
            order_by=lambda group: group[0],
        )
    ]
    assert keys == ["a", "z"]


def test_iter_candidate_groups_is_independent_of_input_order_when_ordered():
    def keys_for(rows):
        return [
            key
            for key, _ in iter_candidate_groups(
                rows,
                key_of=lambda r: r[0],
                is_candidate=lambda _k, rs: len(rs) >= 2,
                order_by=lambda group: group[0],
            )
        ]

    assert keys_for([("z", 1), ("a", 1), ("z", 2), ("a", 2)]) == keys_for(
        [("a", 2), ("z", 1), ("a", 1), ("z", 2)]
    )


def test_iter_candidate_groups_with_no_candidates():
    rows = [("a", 1), ("b", 2)]
    assert (
        list(
            iter_candidate_groups(
                rows, key_of=lambda r: r[0], is_candidate=lambda _k, rs: len(rs) >= 2
            )
        )
        == []
    )


# ---------------------------------------------------------------------------
# count_distinct — the "different voucher" requirement
# ---------------------------------------------------------------------------
def test_count_distinct_counts_unique_values():
    rows = [{"v": "VCH-1"}, {"v": "VCH-1"}, {"v": "VCH-2"}]
    assert count_distinct(rows, lambda r: r["v"]) == 2


def test_count_distinct_ignores_blank_values():
    """A row with no voucher number must not manufacture a second distinct voucher."""
    rows = [{"v": "VCH-1"}, {"v": ""}, {"v": None}]
    assert count_distinct(rows, lambda r: r["v"]) == 1


def test_count_distinct_of_empty_input():
    assert count_distinct([], lambda r: r) == 0


# ---------------------------------------------------------------------------
# The R12 regression proof, at the level the rules use it
# ---------------------------------------------------------------------------
def test_exc_008_style_blocking_excludes_same_voucher_groups():
    """`06` EXC-008: `require_different_voucher = true` — same-voucher rows are normal
    multi-line postings, not duplicates. Expressed through the shared predicate."""
    key = ("IN01", "5300", Decimal("12500.00"), "2026-09-22", "CC-A", -1)
    rows = [
        (key, {"voucher_no": "VCH-2026-0922-007"}),
        (key, {"voucher_no": "VCH-2026-0922-007"}),  # same voucher -> not a duplicate
    ]
    assert (
        list(
            iter_candidate_groups(
                rows,
                key_of=lambda item: item[0],
                is_candidate=lambda _k, rs: count_distinct(rs, lambda i: i[1]["voucher_no"]) >= 2,
            )
        )
        == []
    )

    rows.append((key, {"voucher_no": "VCH-2026-0922-009"}))  # now two distinct vouchers
    assert (
        len(
            list(
                iter_candidate_groups(
                    rows,
                    key_of=lambda item: item[0],
                    is_candidate=lambda _k, rs: (
                        count_distinct(rs, lambda i: i[1]["voucher_no"]) >= 2
                    ),
                )
            )
        )
        == 1
    )


def test_exc_007_style_blocking_needs_two_rows_and_an_ordered_key():
    """`EXC-007` groups by (vendor, normalised invoice, amount) and wants ≥ 2 rows."""
    rows = [
        (("V-00931", normalise_invoice_no("INV-88213"), Decimal("45000.00")), "row-1"),
        (("V-00931", normalise_invoice_no("inv 88213"), Decimal("45000.00")), "row-2"),
    ]
    got = list(
        iter_candidate_groups(
            rows,
            key_of=lambda item: item[0],
            is_candidate=lambda _k, rs: len(rs) >= 2,
            order_by=lambda group: (group[0][0], group[0][1]),
        )
    )
    assert len(got) == 1
    key, members = got[0]
    assert key == ("V-00931", "INV88213", Decimal("45000.00"))
    assert [row[1] for row in members] == ["row-1", "row-2"]


def test_a_single_row_never_blocks():
    """One row cannot be its own duplicate, at any key."""
    rows = [(("V-1", "INV1", Decimal("1.00")), "only")]
    assert (
        list(
            iter_candidate_groups(
                rows, key_of=lambda i: i[0], is_candidate=lambda _k, rs: len(rs) >= 2
            )
        )
        == []
    )


# ---------------------------------------------------------------------------
# The module must not be a second implementation of anything (R12)
# ---------------------------------------------------------------------------
def test_rules_delegate_to_this_module_rather_than_reimplementing():
    """`BD-001`: one implementation. The rule modules must import these primitives."""
    import inspect

    from app.engine.rules import rules_01_08, rules_catalog_001_008

    src_01 = inspect.getsource(rules_01_08)
    src_cat = inspect.getsource(rules_catalog_001_008)
    assert "from app.engine.dedupe import" in src_01
    assert "from app.engine.dedupe import" in src_cat
    # The old inline normaliser body must be gone, not duplicated beside the new one.
    assert "[^A-Z0-9]" not in src_01
    assert 'lstrip("0")' not in src_01
    # And the name `06` EXC-007 uses must be an alias of the one implementation, not a
    # second function that happens to agree today.
    from app.engine.dedupe import normalise_invoice_no

    assert rules_01_08._normalize_invoice_no is normalise_invoice_no
    # Both duplicate rules must block through the shared iterator rather than their own
    # hand-rolled dict pass.
    assert "iter_candidate_groups(" in inspect.getsource(rules_01_08.evaluate_exc_001)
    assert "iter_candidate_groups(" in inspect.getsource(
        rules_catalog_001_008.evaluate_catalog_exc_008
    )
    assert "count_distinct(" in inspect.getsource(rules_catalog_001_008.evaluate_catalog_exc_008)


def test_no_weighted_scorer_was_added():
    """`OQ-028`: the scorer the dead card asked for is required by no `06` rule, so it was
    deliberately not built. A future session must not assume it exists."""
    import app.engine.dedupe as pkg

    assert not (set(pkg.__all__) & {"score", "weighted_score", "similarity", "scorer"})
    assert not hasattr(pkg, "seeded_scorer")
