"""Candidate blocking for duplicate detection.

**Provenance: this is BUILD code, not adapted code.** No ADP provenance header, because no
upstream source was copied — see `normalize.py`'s module note and `BD-001` in `docs/32` §2.

Blocking is the step that turns a row set into *candidate groups*: rows that share every
field the rule's subject key is built from become one group, and a group only becomes an
exception if it passes the rule's own predicate. `docs/06` gives every duplicate rule this
shape — `EXC-007` groups by `(vendor_code, normalised invoice_no, amount)`, `EXC-008` by
`(company, account, absolute amount, posting date, cost centre, net sign)`, `EXC-002` by
voucher and invoice keys. Only the key changes; the blocking is the same, so it lives here
once and the rules supply their own key function (`R12`).

**Boundary with the rules.** This module owns grouping, candidate selection and ordering —
nothing else. Thresholds (`min_amount`, `date_window_days`), subject-key strings, severities
and evidence rows are the rule's business and stay in the rule, because they depend on
`RuleContext` and the catalog text rather than on dedupe mechanics.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable, Iterator, Sequence
from typing import Any, TypeVar

K = TypeVar("K", bound=Hashable)
R = TypeVar("R")

#: A group a candidate predicate may inspect: its key and its member rows, in input order.
Group = tuple[K, list[R]]
#: ``(key, rows) -> is this group an exception candidate?``
CandidatePredicate = Callable[[K, Sequence[R]], bool]


def group_by_key(rows: Iterable[R], key_of: Callable[[R], K]) -> dict[K, list[R]]:
    """Block ``rows`` by ``key_of``, keeping input order inside each group.

    Rows whose ``key_of`` raises are the caller's problem, not this function's: a rule that
    cannot build a key for a row is expected to skip that row before calling here, which is
    how the catalog's "invoice numbers are often absent in payroll data, which simply yields
    no candidates for those rows" (`EXC-007`) is realised.

    The returned mapping preserves **first-seen insertion order**, so a caller that does not
    sort still gets the same output for the same input.
    """
    groups: dict[K, list[R]] = defaultdict(list)
    for row in rows:
        groups[key_of(row)].append(row)
    return groups


def iter_candidate_groups(
    rows: Iterable[R],
    key_of: Callable[[R], K],
    is_candidate: CandidatePredicate[R],
    order_by: Callable[[Group[R]], Any] | None = None,
) -> Iterator[Group[R]]:
    """Yield ``(key, rows)`` for the groups that pass ``is_candidate``.

    Args:
        rows: The rule's candidate row set, already filtered to the rows the rule considers
            (in period, expense side, non-empty key fields — the rule decides).
        key_of: Builds the blocking key for one row.
        is_candidate: Receives ``(key, rows)`` and returns whether the group is worth
            raising. Rules use this for their structural requirements — "≥ 2 rows" for
            `EXC-007`, "at least two *different* vouchers" for `EXC-008`.
        order_by: Optional sort key over ``(key, rows)``. Supply one to make the rule's
            finding order independent of input order; omit it to iterate in first-seen
            order.

    Yields:
        One ``(key, rows)`` pair per candidate group.

    Ordering matters to `TST-PPT-08`-style determinism and to the acceptance harness, which
    compares a finding list: the same corpus must always produce the same sequence, which is
    why ``order_by`` exists rather than falling back to dict order implicitly.
    """
    groups = group_by_key(rows, key_of)
    items: Iterable[Group[R]] = groups.items()
    if order_by is not None:
        items = sorted(items, key=order_by)
    for key, members in items:
        if is_candidate(key, members):
            yield key, members


def count_distinct(rows: Iterable[R], value_of: Callable[[R], Any]) -> int:
    """How many distinct values ``value_of`` yields over ``rows``.

    The structural test both duplicate rules need: `EXC-008` requires
    ``require_different_voucher = true``, expressed as *"at least two distinct vouchers"*,
    and `EXC-002` counts overlapping rows the same way. Blank values are ignored, so a row
    with no voucher number cannot manufacture a second distinct voucher.
    """
    seen = {value for value in (value_of(row) for row in rows) if value not in (None, "")}
    return len(seen)
