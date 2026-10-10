"""Key normalisation for duplicate detection.

**Provenance: this is BUILD code, not adapted code.** It carries no ADP provenance header
because no upstream source was copied — the catalog entry that `WC-1` pre-approved
(`WS-01`, `github.com/ricothanfx/invoice-dedupe`) no longer exists (404; see `OQ-028`,
`BD-001` in `docs/32` §2 and `evidence/wc1/ws01-escalation-packet.md`). The behaviour here
was lifted from this project's own rule modules so that one implementation serves them all
(`R12`) — it is our code in our words, per `L2`/`L3`.

The normalisation clause it implements is `docs/06` `EXC-007`'s: *"Normalisation: trim,
upper-case, strip leading zeros and non-alphanumeric separators."*
"""

from __future__ import annotations

import re
from typing import Any

#: Anything that is not an ASCII letter or digit is a separator for key purposes.
_SEPARATOR_RE = re.compile(r"[^A-Z0-9]")


def normalise_alnum_upper(value: Any) -> str:
    """Trim, upper-case, and drop every non-alphanumeric separator.

    Returns ``""`` for a missing or wholly-empty value, so callers can test the result
    with a plain truthiness check to mean "this key cannot block".
    """
    if value is None:
        return ""
    text = str(value).strip().upper()
    if not text:
        return ""
    return _SEPARATOR_RE.sub("", text)


def normalise_invoice_no(invoice_no: str | None) -> str:
    """Normalise an invoice number to its blocking key (`06` `EXC-007`).

    Applies :func:`normalise_alnum_upper`, then strips leading zeros, so ``"INV-88213"``,
    ``"inv 88213"`` and ``" INV88213 "`` all block as one key.

    **Limit of the spec's clause, recorded rather than papered over:** *"strip leading
    zeros"* can only collapse zeros that sit at the **start** of the alphanumeric string.
    A prefixed number keeps its zeros, so ``"INV-00088213"`` normalises to
    ``"INV00088213"`` and does **not** block with ``"INV-88213"``. That is the clause as
    `06` writes it, and it is the behaviour this function had before extraction; widening
    it (e.g. collapsing zero runs after a prefix) would change which rows `EXC-007` raises
    on, which is an `R1` spec question, not a refactor.

    Three edge cases are deliberate and are preserved byte-for-byte from the inline
    implementation this function replaced:

    * an absent value — ``None``, ``""``, or a falsy numeric such as ``0`` — returns
      ``""``, which `EXC-007` reads as "skip this row";
    * a value made only of separators (``"---"``) strips to ``""`` at the alphanumeric
      step, but this function returns ``"0"`` rather than ``""`` — an invoice number *was*
      present on the row, so the row stays a blocking candidate whose key is the degenerate
      ``"0"``, not a row to skip;
    * a value that is all zeros is returned unchanged (``"0"`` → ``"0"``, ``"000"`` →
      ``"000"``), because there is nothing left after the zero-strip to fall back to.

    The first of those is why the falsiness test happens on the **raw** input rather than on
    the cleaned key: it keeps ``0`` ("no invoice number") distinct from ``"0"`` (an invoice
    number that happens to be a zero).
    """
    if not invoice_no:
        return ""
    cleaned = normalise_alnum_upper(invoice_no)
    if not cleaned:
        return "0"
    stripped = cleaned.lstrip("0")
    return stripped if stripped else cleaned
