"""Tests for GATE-FAST: non-short-circuiting check.py behavior."""

import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.check as check_mod

ROOT = Path(__file__).resolve().parent.parent.parent


def test_check_main_returns_nonzero_when_any_bar_fails():
    """Verify that main() exits non-zero if any single bar fails."""

    # Mock run_command so the first check (Ruff Format) fails with exit code 1, but others pass
    def fake_run(cmd: str, desc: str) -> int:
        if "ruff format" in cmd:
            return 1
        return 0

    with (
        patch.object(check_mod, "run_command", side_effect=fake_run),
        patch.object(check_mod, "enforce_coverage_gates", return_value=0),
        patch("sys.exit"),
    ):
        rc = check_mod.main()
        assert rc != 0, "main() must return non-zero when a bar fails"


def test_every_bar_runs_even_after_failure(capsys):
    """Verify that every bar is executed and reported, even if earlier bars fail."""
    executed_commands = []

    def tracking_run(cmd: str, desc: str) -> int:
        executed_commands.append(desc)
        # Fail the very first command
        if len(executed_commands) == 1:
            return 1
        return 0

    with (
        patch.object(check_mod, "run_command", side_effect=tracking_run),
        patch.object(check_mod, "enforce_coverage_gates", return_value=0),
    ):
        rc = check_mod.main()
        assert rc != 0

    captured = capsys.readouterr().out
    # Assert that all subsequent bars still ran
    assert "Ruff Lint" in executed_commands
    assert "Mypy Strict (app/engine)" in executed_commands
    assert "UI Gate Check (ESLint (ui) + TypeScript Check (tsc --noEmit))" in executed_commands
    assert "Doc Integrity and Link Check" in executed_commands
    assert "500-LOC Code-Health Check" in executed_commands
    assert "Spec-to-Code Constants Drift Check" in executed_commands
    assert "License & Provenance Gate" in executed_commands

    # Assert that summary table reported all bars
    assert "CHECK BAR" in captured
    assert "STATUS" in captured
    assert "EXIT CODE" in captured
    assert "Validation Gate FAILED" in captured


def test_check_main_returns_zero_when_all_pass():
    """Verify that main() returns 0 when all bars succeed."""
    with (
        patch.object(check_mod, "run_command", return_value=0),
        patch.object(check_mod, "enforce_coverage_gates", return_value=0),
    ):
        rc = check_mod.main()
        assert rc == 0


class _Cp1252Stdout:
    """Fake cp1252 console.

    ``write`` encodes eagerly, so any character cp1252 cannot represent raises
    ``UnicodeEncodeError`` exactly where the real Windows console would. This is
    the gap HO-056 blocker B named: the existing tests capture stdout into a
    StringIO, where a non-ASCII marker encodes fine, so they could not see the
    crash that killed the failure branch of ``scripts/check.py``.
    """

    encoding = "cp1252"

    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def write(self, s: str) -> int:
        data = s.encode("cp1252")  # raises on unencodable chars, by construction
        self.buffer.write(data)
        return len(s)

    def flush(self) -> None:
        pass

    def text(self) -> str:
        return self.buffer.getvalue().decode("cp1252")


def test_failure_branch_prints_its_tally_on_a_cp1252_console(monkeypatch):
    """A red gate must still report how many bars failed on a cp1252 console.

    Regression for HO-056 blocker B: the failure branch used to print a U+274C
    marker, which raised ``UnicodeEncodeError`` on the project's default Windows
    console. The bar table had printed and the exit code was still 1, but the
    process died by crash instead of ``return 1``, so the "N/15 bars failed"
    tally was never seen. Every character on the failure path must therefore be
    cp1252-encodable, and the tally must be present.
    """
    executed: list[str] = []

    def tracking_run(cmd: str, desc: str) -> int:
        executed.append(desc)
        # Fail the first bar only: this is the failure branch, not the pass one.
        return 1 if len(executed) == 1 else 0

    fake = _Cp1252Stdout()
    monkeypatch.setattr(sys, "stdout", fake)
    with (
        patch.object(check_mod, "run_command", side_effect=tracking_run),
        patch.object(check_mod, "enforce_coverage_gates", return_value=0),
    ):
        rc = check_mod.main()

    assert rc == 1, "one red bar must still return non-zero"
    out = fake.text()
    assert "Validation Gate FAILED" in out
    # The table has one row more than there are run_command bars: the NFR-014
    # split-coverage bar is appended straight from enforce_coverage_gates. The
    # tally counts TABLE ROWS, so it must be 1/16 here, not 1/15 - the off-by-one
    # that made six rows of the first GATE-FAST evidence table wrong.
    rows = [ln for ln in out.splitlines() if " | PASS " in ln or " | FAIL " in ln]
    assert len(rows) == len(executed) + 1
    assert len([ln for ln in rows if " | FAIL " in ln]) == 1
    assert f"1/{len(rows)} bars failed" in out, (
        "the tally must survive a cp1252 console, not die with the print"
    )
    for desc in executed:
        assert desc in out


def test_the_cp1252_guard_actually_rejects_the_old_marker():
    """Falsification of the guard above: it must be able to fail.

    If this stops raising, ``_Cp1252Stdout`` has become a StringIO and the test
    above is decorative - it would pass with the emoji marker put back.
    """
    fake = _Cp1252Stdout()
    with pytest.raises(UnicodeEncodeError):
        fake.write("\u274c Validation Gate FAILED: 1/16 bars failed.")


# --------------------------------------------------------------------------- a missing
# measurement is not a coverage failure (HO-080 Next item (c))
def test_missing_coverage_data_is_reported_as_not_measured(monkeypatch, capsys):
    """`.coverage` absent must read as 'no measurement', never as 0.00%.

    Measured on this tree before the fix: ``enforce_coverage_gates()`` with no
    ``.coverage`` file printed ``Backend coverage 0.00% is below threshold 75.0%`` and
    returned 1 - a coverage failure asserted about a corpus it never read. HO-080 named
    this as the reason its own coverage row was reported as an artefact.
    """
    import coverage as coverage_mod

    class _NoData:
        def load(self):
            raise coverage_mod.CoverageException("No data to report.")

        def get_data(self):  # pragma: no cover - must not be reached
            raise AssertionError("get_data() called on absent coverage data")

    monkeypatch.setattr(coverage_mod, "Coverage", _NoData)
    rc = check_mod.enforce_coverage_gates()
    streams = capsys.readouterr()
    err = streams.err
    combined = streams.out + streams.err
    assert rc == check_mod.NOT_MEASURED, "a missing measurement is not a red bar"
    assert "NOT MEASURED" in err
    assert "missing measurement" in combined
    # Assert on the *reported lines*, not the bare substring: the explanation text
    # legitimately quotes "0.00%" while describing why it is no longer printed.
    assert "Backend coverage 0.00%" not in combined, (
        "reporting 0.00% asserts a coverage number never computed"
    )
    assert "Domain engines coverage 0.00%" not in combined
    assert "below threshold" not in combined, "a missing measurement is not a shortfall"


def test_empty_coverage_data_is_also_not_measured(monkeypatch, capsys):
    """The live failure mode, measured on this tree.

    With no `.coverage` file at all, ``coverage.Coverage().load()`` does NOT raise - it
    succeeds and reports zero measured files. So a fix that only catches the exception
    never fires, and the bar prints ``0/0 (0.00%)`` exactly as before. This is the
    branch that actually runs in production; the exception branch is the rare one.
    """
    import coverage as coverage_mod

    class _EmptyData:
        def measured_files(self):
            return []

    class _LoadsButEmpty:
        def load(self):
            pass

        def get_data(self):
            return _EmptyData()

    monkeypatch.setattr(coverage_mod, "Coverage", _LoadsButEmpty)
    rc = check_mod.enforce_coverage_gates()
    streams = capsys.readouterr()
    combined = streams.out + streams.err
    assert rc == check_mod.NOT_MEASURED, "an empty coverage set is not a red bar"
    assert "Backend coverage 0.00%" not in combined
    assert "below threshold" not in combined


def test_tsc_undecidable_output_is_not_a_silent_pass(capsys):
    """A tsc that fails unreadably must FAIL the bar, not be waved through.

    `_count_tsc_errors` returns `(1, False)` for that case - a non-zero count AND a flag
    saying the count is not trustworthy. If `_over_budget` checked only the number, the
    budget of 0 would fail it by accident, and raising the budget to 1 later would turn
    the same unreadable output into a pass. The flag has to be consulted explicitly.
    """
    import scripts.check_ui_gate as ui_gate

    assert ui_gate._over_budget(1, False, 1, "TypeScript errors") is True, (
        "an undecidable tsc result must fail even when its placeholder count is inside "
        "budget - otherwise raising max_tsc_errors silently converts it into a pass"
    )
    assert ui_gate._over_budget(0, True, 0, "TypeScript errors") is False
    assert ui_gate._over_budget(1, True, 0, "TypeScript errors") is True


def test_a_real_shortfall_still_reports_a_number(monkeypatch, capsys):
    """Falsification of the guard above: NOT_MEASURED must not swallow real reds.

    A bar that returns 2 whenever coverage looks odd would pass every test above while
    the coverage gate stopped working. So a tree WITH data and a genuinely low
    percentage must still be a plain FAIL at exit 1, naming the number.
    """
    import coverage as coverage_mod

    class _FakeFile:
        def __init__(self, path):
            self.path = str(path)

    class _FakeData:
        def measured_files(self):
            return [str(ROOT / "app" / "engine" / "calc" / "math.py")]

    class _FakeCov:
        def load(self):
            pass

        def get_data(self):
            return _FakeData()

        def analysis(self, filepath):
            # 10 statements, 4 missed -> 60% on both the domain and backend counts.
            return "math.py", list(range(10)), list(range(4)), ""

    monkeypatch.setattr(coverage_mod, "Coverage", _FakeCov)
    rc = check_mod.enforce_coverage_gates(domain_threshold=90.0, backend_threshold=75.0)
    out = capsys.readouterr()
    assert rc == 1, "a measured shortfall is FAIL (1), never NOT_MEASURED (2)"
    assert "60.00%" in out.out
    assert "below threshold" in out.err


def test_the_summary_table_separates_not_measured_from_fail(capsys):
    """The tally must not let an unmeasured bar read as a counted failure or a pass."""
    with (
        patch.object(check_mod, "run_command", return_value=0),
        patch.object(check_mod, "enforce_coverage_gates", return_value=check_mod.NOT_MEASURED),
    ):
        rc = check_mod.main()
    out = capsys.readouterr().out
    assert rc != 0, "an unmeasured bar means the gate is not clean"
    assert "NOT MEASURED" in out
    assert "[NOT MEASURED] 1 of 16 bars produced no measurement" in out
    assert "0/16 bars failed" in out, (
        "the unmeasured bar must not be counted as a red one either - both counts are "
        "printed separately so neither is inferred from the other"
    )


# --------------------------------------------------------------------------- tsc counts,
# it is not a flag (HO-080 Next item (b))
def test_tsc_errors_are_counted_not_inferred_from_the_exit_code():
    """`tsc` failing must report how many errors, not '1'.

    The old line was ``tsc_errors = 0 if tsc_proc.returncode == 0 else 1``, so a real
    run with 34 errors printed ``TypeScript Errors : 1`` and compared a flag against a
    budget of 0.
    """
    import scripts.check_ui_gate as ui_gate

    def proc(rc: int, out: str = "", err: str = "") -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess("npx tsc --noEmit", rc, out, err)

    assert ui_gate._count_tsc_errors(proc(0)) == (0, True)

    three = (
        "a.ts(1,1): error TS2307: Cannot find module 'x'.\n"
        "b.ts(2,1): error TS2307: Cannot find module 'y'.\n"
        "c.ts(3,1): error TS7006: Parameter 'z' implicitly has an 'any' type.\n"
    )
    assert ui_gate._count_tsc_errors(proc(2, three)) == (3, True), (
        "34 errors must print as 34, not as 1"
    )

    # Failed with nothing we can count: report it as undecidable, not as one error.
    assert ui_gate._count_tsc_errors(proc(2, "", "sh: 1: tsc: Permission denied")) == (1, False)
