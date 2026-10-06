"""Deterministic `.xlsx` saving, shared by every generator that writes into `sample-data/`.

QUAL-05 / TB-021. This module is the single home for the rule "the file bytes are
a function of the content alone". It lives in its own module because two
generators write into the corpus — `sample-data/generate_sample_data.py` and the
repo-root `generate_tieout_template.py` — and while the second one still used a
bare `Workbook.save()`, its template changed SHA-256 on every run. A manifest
cannot fingerprint a file that moves, so the rule has to have one owner.

Before this helper was introduced, openpyxl stamped a wall-clock
`dcterms:created` into `docProps/core.xml` on every save, so the SAME logical
workbook produced a different SHA-256 on each generation. That is why the
acceptance harness originally excluded the `.xlsx` files and recorded the
limitation (`acceptance.py` `NON_REPRODUCIBLE`). This helper pins document
properties, ZIP timestamps, member order and file attributes; current generated
workbooks can therefore be fingerprinted. The checked-in `test_scale/` copies
are also included in the acceptance checksum scope as separate file paths.
"""

from __future__ import annotations

import re
import zipfile
from datetime import datetime

#: Fixed epoch stamped into every generated workbook. 2026-01-01 is inside the
#: FY26 corpus year and is chosen, not derived: nothing in the corpus reads it.
XLSX_FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0)

DEFAULT_PRODUCER = "generate_sample_data.py"


def save_deterministic(workbook, path, producer: str = DEFAULT_PRODUCER) -> None:
    """Save `workbook` so the FILE BYTES are a function of its content alone.

    Two independent clocks have to be pinned, and pinning only the first one
    still leaves the corpus non-reproducible:

    1. `docProps/core.xml` carries a wall-clock `dcterms:created`, written by
       openpyxl on every save.
    2. Every zip entry's local header carries the time the entry was written.

    Fixing (1) and not (2) is the trap: `core.xml` looks reproducible and the
    SHA-256 still moves. So the archive is rebuilt with fixed entry timestamps.

    `producer` is written into `docProps/core.xml` as the creator. It is a
    parameter so the two generators each name themselves; the default reproduces
    the bytes of the committed corpus exactly, so changing it is not free.
    """
    properties = workbook.properties
    properties.created = XLSX_FIXED_TIMESTAMP
    properties.modified = XLSX_FIXED_TIMESTAMP
    properties.lastModifiedBy = producer
    properties.creator = producer
    workbook.save(path)
    _normalise_zip_timestamps(path)


def _normalise_zip_timestamps(path) -> None:
    """Rewrite the xlsx archive: fixed entry timestamps, fixed order, fixed core.

    openpyxl re-stamps `dcterms:modified` with the wall clock inside `save()`
    itself, so setting `workbook.properties.modified` beforehand has no effect -
    the file still changes on every run even though `created` is pinned. The
    archive is therefore rebuilt after the fact with both stamps rewritten.
    """
    fixed = (XLSX_FIXED_TIMESTAMP.year, XLSX_FIXED_TIMESTAMP.month,
             XLSX_FIXED_TIMESTAMP.day, 0, 0, 0)
    stamp = XLSX_FIXED_TIMESTAMP.strftime("%Y-%m-%dT%H:%M:%SZ")
    with zipfile.ZipFile(path) as source:
        entries = []
        for info in sorted(source.infolist(), key=lambda i: i.filename):
            payload = source.read(info.filename)
            if info.filename == "docProps/core.xml":
                payload = re.sub(
                    rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)",
                    rb"\g<1>" + stamp.encode("ascii") + rb"\g<2>",
                    payload,
                )
            entries.append((info.filename, payload))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target:
        for filename, payload in entries:
            info = zipfile.ZipInfo(filename, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            target.writestr(info, payload)