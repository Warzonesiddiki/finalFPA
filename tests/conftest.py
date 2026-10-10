"""Pytest root conftest: hermetic database isolation for EVERY test.

Quoted from docs/14_TESTING_QA_PLAN.md section 1.2 (The quality contract):
- Rule 2: "A red suite ends the session. Any session that touched calculation,
  import, rule, export or migration code must run the full suite."
- Rule 5: "Automate the deterministic, checklist the physical. Anything that can
  be asserted in code must be."
- Rule 8: "Failures are first-class. A test that fails only on a specific machine,
  or that is skipped, is reported at the gate with its reason - never silently
  skipped."

RULE NOTE:
"Read the dataclass first. Never guess attributes or dictionary structures;
inspect the underlying model definition (ImportBatchResult, ImportBatch, etc.)
before writing assertions."

FAILURE HISTORY (remembered-API test bugs):
- test_empty_tiny_file_handling.py and test_mixed_currency_handling.py assumed
  non-existent attributes (`batch.hardening_findings`, `batch.status`) and read
  slugs from `q_row['checks'][i]['message_slug']` instead of the top-level
  `q_row['reason_code']`. `get_batch_slugs` below standardises the lookup.

WHY ISOLATION IS THE DEFAULT, NOT AN ALLOW-LIST
------------------------------------------------
This fixture originally matched on a filename allow-list
(`['test_api', 'test_cli', 'test_ai_journey']`). Measured consequence: tests
OUTSIDE that list still resolved to the live user project directory, because
`DatabaseManager()` with no argument honours `FPA_PROJECT_DIR` / `LOCALAPPDATA`.

Observed in the user database at %LOCALAPPDATA%\\FP&A Month-End Copilot\\
Projects\\default (read-only inspection, 2026-10-02):
  * FactActual   62,531 rows across 203 distinct import_batch_id values
  * FactImportBatch 333 rows
  * MappingSuggestion 40 rows
  * One full suite run DELETED 786 KB from analytics.duckdb

A filename allow-list cannot be correct by construction: it misses every file
added after it was written, which is precisely the failure mode it was meant to
prevent. So the default here is ISOLATE EVERYTHING, with an explicit, documented
opt-out list. Adding a new test file is then safe by default.

THE OPT-OUT LIST IS DELIBERATELY SHORT
--------------------------------------
`test_portable_mode.py` needs the REAL directory-resolution logic
(`portable.flag` beside the executable, cwd vs LOCALAPPDATA), so isolating it
would test nothing. It manages its own temp directories explicitly.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.engine.store.db import DatabaseManager

#: Tests that must NOT be isolated, and why. Keep this list as short as possible:
#: every entry is a test that cannot do its job while pointed at tmp_path.
#:
#: - test_portable_mode: exercises portable.flag resolution against the real
#:   executable-adjacent layout; it creates and removes its own temp dirs.
ISOLATION_OPT_OUT: frozenset = frozenset({"test_portable_mode"})

#: The REAL user project directory, captured at conftest import time - i.e. before
#: any fixture has patched the environment.
#:
#: This exists because a test cannot discover the live directory by calling
#: `DatabaseManager()`: by the time test code runs, the isolation fixture has
#: already repointed FPA_PROJECT_DIR / LOCALAPPDATA at tmp_path, so such a call
#: returns the throwaway directory. A regression test for DEF-006 that "measures"
#: the live database through that call would fingerprint tmp_path and pass
#: vacuously - green while the defect was still present.
#:
#: Captured once, at import, so it is the unpatched value by construction.
REAL_LOCALAPPDATA: str | None = os.environ.get("LOCALAPPDATA")
REAL_FPA_PROJECT_DIR: str | None = os.environ.get("FPA_PROJECT_DIR")


def real_project_dir() -> Path:
    """The project directory that unisolated code would resolve to."""
    base = REAL_FPA_PROJECT_DIR
    if base:
        return Path(base)
    if REAL_LOCALAPPDATA:
        return Path(REAL_LOCALAPPDATA) / "FP&A Month-End Copilot" / "Projects" / "default"
    return Path.cwd() / "Projects" / "default"


def _live_batch_count() -> int | None:
    """FactImportBatch row count in the LIVE project directory.

    Read-only: SQLite is opened through a read-only URI, so this cannot itself
    mutate the number it reports. Returns None when the database is absent or
    unreadable, so the tripwire degrades to "nothing to check" rather than
    failing for an unrelated reason.
    """
    sq = real_project_dir() / "workflow.sqlite"
    if not sq.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{sq}?mode=ro&immutable=1", uri=True)
    except sqlite3.Error:
        return None
    try:
        return int(con.execute("SELECT COUNT(*) FROM FactImportBatch").fetchone()[0])
    except sqlite3.Error:
        return None
    finally:
        con.close()


#: Session-start snapshot of the live FactImportBatch count, taken once at import.
_LIVE_BATCH_COUNT_AT_START: int | None = _live_batch_count()


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001 - pytest hook signature
    """TRIPWIRE: fail the run if anything wrote to the real project database.

    Why this exists
    ---------------
    DEF-006 (shared-DB, S2) was closed on the strength of the isolation fixture.
    A later investigation then found the live database had grown by one
    `bank_ledger_actuals.csv` batch (499 rows) that could not be reproduced from
    any pytest invocation - the writer had exited before it could be observed. Six
    near-identical batches showed the leak had been running for hours.

    Isolation alone cannot catch that: it only covers processes that load this
    conftest. A relocated test file, or a run with a rootdir outside `tests/`,
    bypasses it silently. The only durable defence is to MEASURE the live
    directory across the whole session and fail if it moved.

    This converts "we believe nothing leaked" into "the suite proves nothing
    leaked, on every run" - which is what DEF-006's closure actually required.

    Deliberate scoping:
      * Count only, not file hashes - cheaper, and immune to WAL churn that a
        read-only reopen would otherwise provoke.
      * `FactImportBatch` specifically: it is the one table whose growth means
        "an import was committed", which is the failure mode that matters. Row
        counts in the fact tables change on deletes too, which would make the
        tripwire noisier without catching more.
      * A missing database is not a failure - it means there is nothing to protect.
    """
    if _LIVE_BATCH_COUNT_AT_START is None:
        return

    final = _live_batch_count()
    if final is None:
        return

    if final != _LIVE_BATCH_COUNT_AT_START:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        message = (
            "\n"
            "LIVE-DB TRIPWIRE (DEF-006): the real user project database was "
            "written during this test session.\n"
            f"  live project dir : {real_project_dir()}\n"
            f"  FactImportBatch  : {_LIVE_BATCH_COUNT_AT_START} -> {final} "
            f"(delta {final - _LIVE_BATCH_COUNT_AT_START:+d})\n"
            "  A test committed an import into the user's real project. Something "
            "bypassed the isolation fixture - most likely a test run without "
            "tests/conftest.py on its conftest path.\n"
        )
        if reporter is not None:
            reporter.write_line(message, red=True, bold=True)
        session.exitstatus = 1


def get_batch_slugs(batch: Any) -> list[str]:
    """Canonical slug lookup helper for import batches.

    Extracts message slugs from batch-level checks and quarantined rows'
    reason_codes - the two places they actually live.
    """
    slugs: list[str] = []
    if hasattr(batch, "checks") and batch.checks:
        for c in batch.checks:
            if hasattr(c, "message_slug") and c.message_slug:
                slugs.append(c.message_slug)
            elif isinstance(c, dict) and c.get("message_slug"):
                slugs.append(c.get("message_slug"))
    if hasattr(batch, "quarantined_rows") and batch.quarantined_rows:
        for q in batch.quarantined_rows:
            if isinstance(q, dict) and q.get("reason_code"):
                slugs.append(q.get("reason_code"))
    return slugs


def _seed_api_fixture_row(project_path: Path) -> None:
    """Seed the single FactActual row the API contract tests assert on.

    Kept from the original fixture so test_api.py and test_api_contract.py keep
    the row they depend on. Failures are swallowed: a schema drift here must not
    mask the real assertion failure inside the test that needs it.
    """
    db_mgr = DatabaseManager(project_path)
    duck_conn = db_mgr.get_duckdb_connection()
    try:
        duck_conn.execute(
            """
            INSERT INTO FactActual (
                actual_id, import_batch_id, row_fingerprint, source_file_name, source_row_ref,
                source_system, posting_date, voucher_no, line_no, invoice_no, document_no,
                description, debit, credit, net_amount, currency_code, journal_category,
                company_id, account_id, cost_center_id, period_id
            ) VALUES (
                1, 1, 'fp_1', 'd365_gl_actuals.csv', 'row_1', 'D365', '2026-11-15',
                'V-001', 1, 'INV-101', 'DOC-1',
                'Large unexpected expense over threshold', 600000.00, 0.00, 600000.00,
                'INR', 'GEN', 1, 1, 1, 9
            )
            """
        )
    except Exception:
        pass
    finally:
        duck_conn.close()


@pytest.fixture(autouse=True)
def hermetic_project_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
):
    """Point every test at a throwaway project directory.

    `FPA_PROJECT_DIR` takes precedence in `DatabaseManager.__init__`;
    `LOCALAPPDATA` is the fallback. Both are set so the guarantee holds whichever
    branch the resolver takes, and `DEFAULT_PROJECT_DIR` is patched as well
    because other modules still import that module attribute directly - the
    constructor no longer reads it.

    The directory deliberately does NOT mirror the production path shape
    (`Projects/default` under an `FP&A Month-End Copilot` parent). A test that
    accidentally escaped isolation should fail loudly with "file not found", not
    quietly succeed against the real project.
    """
    if request.path.stem in ISOLATION_OPT_OUT:
        # Documented opt-out: this test needs the real resolution logic.
        return None

    project_path = tmp_path / "pytest_project"
    monkeypatch.setenv("FPA_PROJECT_DIR", str(project_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr("app.engine.store.db.DEFAULT_PROJECT_DIR", project_path, raising=False)

    # Seed the row the API contract tests depend on.
    if request.path.stem in ("test_api", "test_api_contract"):
        _seed_api_fixture_row(project_path)

    return project_path
