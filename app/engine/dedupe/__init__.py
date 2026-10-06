"""Duplicate-detection primitives: key normalisation and candidate blocking.

**Provenance: BUILD code** (`BD-001` in `docs/32` §2). Addon 6 v2 §9 pre-approved `WC-1` as
a COPY-EDIT of catalog entry `WS-01`, but that repository no longer exists — ``git clone``
returns *"Repository not found"* (exit 128) and no renamed successor could be found. The
owner ruled the BUILD path on 2026-10-05 (`OQ-028`), so nothing here is copied from anyone:
the behaviour was lifted out of this project's own rule modules in our own words and tests
(`L2`/`L3`), and no file carries an ADP provenance header.

The capability `docs/06` actually needs is *exact*-Tier duplicate detection, and it is here:

* :mod:`~app.engine.dedupe.normalize` — `EXC-007`'s normalisation clause ("trim, upper-case,
  strip leading zeros and non-alphanumeric separators");
* :mod:`~app.engine.dedupe.blocking` — the candidate grouping every duplicate rule performs,
  once instead of per rule (`R12`).

**Not built, deliberately: a weighted/fuzzy scorer.** No `06` rule requires one. All three
duplicate rules are Tier ``exact``, and the eight ``fuzzy``-Tier rules (`EXC-013`…`EXC-022`)
are magnitude, pairing, completeness, budget-relationship and controls rules — none is a
text-similarity problem. `06` keeps duplicate detection exact *on purpose* to protect
precision (`EXC-007`'s mitigation notes partial-amount duplicates are "deliberately out of
scope for v1 to keep precision high"), and a fuzzy match in a duplicate path would move
those rules off Tier ``exact``, which `R1` forbids. See `OQ-028` for the full reasoning and
`WC-1`'s escalation packet for the candidate sources that were rejected.
"""

from app.engine.dedupe.blocking import (
    CandidatePredicate,
    Group,
    count_distinct,
    group_by_key,
    iter_candidate_groups,
)
from app.engine.dedupe.normalize import normalise_alnum_upper, normalise_invoice_no

__all__ = [
    "CandidatePredicate",
    "Group",
    "count_distinct",
    "group_by_key",
    "iter_candidate_groups",
    "normalise_alnum_upper",
    "normalise_invoice_no",
]
