"""DEF-006 regression test (doc 28 section 3.2, log id `TST-API-09`).

DEF-006, S2: "Concurrent test runs fail intermittently due to shared SQLite DB
state | Isolated test databases per test case".

Doc 28 section 3.2, the fix rule this test exists to satisfy, quoted:

    | Fix rule | `S1`/`S2` require a regression test that fails before the fix
      (`14` §14.1); the test id goes in the log |

Doc 14 section 14.1, S2 test response: "Fix before release; regression test
added".

WHAT THIS PROVES
----------------
The defect was that `tests/conftest.py` isolated only an allow-list of test
filenames, so any other test - including every file added later - resolved
`DatabaseManager()` to the live user project directory at
`%LOCALAPPDATA%\\FP&A Month-End Copilot\\Projects\\default`. Measured at intake:
62,531 FactActual rows across 203 batches where a handful were expected, and a
full suite run that DELETED 786 KB from that file.

The regression is asserted by FINGERPRINTING THE LIVE DATABASE before and after
a real nested pytest run. Before the fix the fingerprint moved; after it, it does
not. A negative control inside the same nested session proves the mechanism is
real rather than the observation being vacuous.

Why a nested subprocess rather than an in-process check: asserting on
`os.environ` would only prove the fixture ran, not that the database was spared.
Only the fingerprint proves the outcome the defect log asks for.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# Imported from conftest, NOT recomputed here. `DatabaseManager()` cannot be used
# to find the live directory: the isolation fixture has already repointed the
# environment at tmp_path by the time test code runs, so such a call returns the
# throwaway path and the fingerprint assertions below would be vacuously green.
from conftest import REAL_FPA_PROJECT_DIR, REAL_LOCALAPPDATA, real_project_dir

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_project_dir() -> Path:
    """Where unisolated code would resolve - captured pre-patch by conftest."""
    return real_project_dir()


def _fingerprint(project_dir: Path) -> dict:
    """Size + SHA-256 of the live project files.

    Read-only: DuckDB is opened read_only and SQLite via a read-only URI, so this
    helper cannot itself mutate what it measures.
    """
    out: dict = {}
    for name in ("analytics.duckdb", "workflow.sqlite"):
        path = project_dir / name
        if not path.exists():
            out[name] = None
            continue
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        out[name] = (digest.hexdigest(), path.stat().st_size)
    return out


def _row_counts(project_dir: Path) -> dict:
    """Row counts that must not move as a result of running the suite."""
    counts: dict = {}
    db = project_dir / "analytics.duckdb"
    if db.exists():
        import duckdb

        con = duckdb.connect(str(db), read_only=True)
        try:
            for table in ("FactActual", "FactBudget"):
                try:
                    counts[table] = con.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0]
                except Exception:
                    counts[table] = None
        finally:
            con.close()

    sq = project_dir / "workflow.sqlite"
    if sq.exists():
        con = sqlite3.connect(f"file:{sq}?mode=ro&immutable=1", uri=True)
        try:
            for table in ("FactImportBatch", "MappingSuggestion"):
                try:
                    counts[table] = con.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0]
                except Exception:
                    counts[table] = None
        finally:
            con.close()
    return counts


PROBE = '''
import os
from pathlib import Path


def test_probe_is_isolated():
    """Control: this brand-new file matches no allow-list, so it can only be
    safe if the conftest isolates EVERY test rather than a list."""
    fpa = os.environ.get("FPA_PROJECT_DIR", "<unset>")
    assert "pytest_project" in fpa, f"NOT ISOLATED: FPA_PROJECT_DIR={fpa}"


def test_probe_cannot_reach_the_live_project():
    """A second control: the resolved project dir must not be the real one."""
    resolved = Path(fpa := os.environ["FPA_PROJECT_DIR"])
    live = Path(os.environ["USERPROFILE"]).parent / "AppData" / "Local" / \\
        "FP&A Month-End Copilot" / "Projects" / "default"
    assert resolved != live, f"test resolved to the live project: {resolved}"
'''


def test_suite_run_does_not_touch_the_live_project_database(tmp_path):
    """DEF-006 / TST-API-09: the live user database is untouched by a test run.

    This is the regression the defect log requires. It fails before the
    default-isolate fix and passes after it.
    """
    live_dir = _live_project_dir()

    before_fp = _fingerprint(live_dir)
    before_rows = _row_counts(live_dir)

    # A nested pytest session over a file that matches no allow-list.
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    (nested_dir / "test_def006_probe.py").write_text(PROBE, encoding="utf-8")

    res = subprocess.run(
        [sys.executable, "-m", "pytest", str(nested_dir), "-p", "no:warnings", "-q"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )

    after_fp = _fingerprint(live_dir)
    after_rows = _row_counts(live_dir)

    # The nested session must actually have run and passed; otherwise this test
    # would be vacuously green while the defect persisted.
    assert res.returncode == 0, (
        "nested isolation probe failed - the conftest is not isolating:\n"
        f"{res.stdout[-2000:]}\n{res.stderr[-2000:]}"
    )

    changed = [n for n in before_fp if before_fp[n] != after_fp[n]]
    assert not changed, (
        "DEF-006 REGRESSION: running the test suite modified the live user "
        f"database file(s) {changed}.\n"
        f"  before: {[(n, before_fp[n]) for n in changed]}\n"
        f"  after : {[(n, after_fp[n]) for n in changed]}"
    )

    moved = {k: (before_rows.get(k), after_rows.get(k))
             for k in before_rows if before_rows.get(k) != after_rows.get(k)}
    assert not moved, (
        "DEF-006 REGRESSION: row counts in the live user database changed "
        f"during a test run: {moved}"
    )


def test_conftest_isolates_by_default_not_by_allow_list():
    """Structural guard: the opt-out list must stay short and explicit.

    An allow-list is the defect. This pins the shape of the fix so a future
    edit that reintroduces a filename list fails here.
    """
    conftest = (REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")

    # The opt-out must be a named, explicit set - not a substring allow-list of
    # files to isolate.
    assert "ISOLATION_OPT_OUT" in conftest, (
        "tests/conftest.py must declare an explicit ISOLATION_OPT_OUT frozenset"
    )

    # The DEF-006 root cause was gating isolation on a filename allow-list. Pin
    # that shape out. Matching is on the GATING construct only: the literal
    # "test_api" legitimately appears in the seed-fixture helper, and forbidding
    # it outright would make this guard wrong rather than strict.
    assert "any(name in path_str" not in conftest, (
        "tests/conftest.py gates isolation on a filename allow-list; that was "
        "the DEF-006 root cause"
    )
    assert 'if "integration" in path_str' not in conftest, (
        "tests/conftest.py must not gate isolation on a path substring; "
        "isolate every test by default instead"
    )


def test_live_project_dir_is_the_user_profile_not_the_test_temp_dir():
    """Anchors the regression: we must be measuring the LIVE directory.

    If this ever resolves to a pytest temp path, the fingerprint assertions
    above would be proving nothing.
    """
    live_dir = _live_project_dir()
    live_str = str(live_dir).lower()

    assert "pytest" not in live_str, (
        f"real_project_dir() resolved to a test temp path: {live_dir}. The "
        "DEF-006 regression would then pass vacuously."
    )
    assert live_dir.name == "default"
    assert (
        REAL_LOCALAPPDATA is not None or REAL_FPA_PROJECT_DIR is not None
    ), "no unpatched project directory was captured at conftest import"
