"""Acceptance corpus import ordering required by docs/14 §5.2 step 2.

The earlier history fixtures must be committed before the main corpus, and the
later fixtures after it. Keep this as a fast structural test: full corpus imports
belong to the explicit acceptance gate, not the default unit suite.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.engine.calc import quality_score
from app.engine.imports import parser, profile_binding
from app.engine.rules import acceptance as acc
from app.engine.store import db as db_module
from app.engine.store import exceptions_repo, import_repo


def _write_control_total_sidecars(root: Path) -> None:
    """Create the recorded control-total acceptance sidecars the harness requires.

    T-010: since DEC-056's control-total gate, `build_acceptance_context`
    refuses to run unless every fixture in `CONTROL_TOTAL_ACCEPTANCE_FIXTURES`
    exists with a valid recorded decision, and the production import passes it
    to `parse_excel_transactions(control_total_acceptance=...)`. Tests that
    build their own corpus must supply the sidecar exactly like sample-data/.
    """
    for sidecar in acc.CONTROL_TOTAL_ACCEPTANCE_FIXTURES.values():
        path = root / sidecar
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "accepted_by": "test-suite",
                    "reason": ("Synthetic control-total acceptance recorded by the unit test."),
                }
            ),
            encoding="utf-8",
        )


def _stub_acceptance_imports(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    """Replace storage/parsing with recorders while exercising source orchestration."""
    database = object()
    context = object()
    committed: list[str] = []
    parser_calls: list[tuple[str, str, object]] = []
    acceptance_calls: list[tuple[str, dict[str, Any]]] = []
    profile = object()

    class FakeImportRepository:
        def __init__(self, db: object) -> None:
            assert db is database

        def commit_batch(self, batch: Any, transactions: list[Any]) -> int:
            committed.append(batch.file_name)
            return len(committed)

    class FakeExceptionsRepository:
        def __init__(self, db: object) -> None:
            assert db is database

        def build_rule_context(self, period_code: str, as_of_date: str) -> object:
            assert period_code == "FY26-P09"
            assert as_of_date == "2026-11-12"
            return context

    monkeypatch.setattr(db_module, "DatabaseManager", lambda: database)
    monkeypatch.setattr(import_repo, "ImportRepository", FakeImportRepository)
    monkeypatch.setattr(exceptions_repo, "ExceptionsRepository", FakeExceptionsRepository)
    monkeypatch.setattr(acc, "_load_budget", lambda db, repo, path: 0)

    def prescan_file(path: str | Path) -> SimpleNamespace:
        return SimpleNamespace(sample_headers=[Path(path).name])

    def resolve_base_profile(db: object, sample_headers: list[str]) -> object:
        assert db is database
        return profile

    def resolve_profile_for_import(db: object, *, base_profile: object) -> SimpleNamespace:
        assert db is database
        assert base_profile is profile
        return SimpleNamespace(profile=profile)

    def parse(
        path: str | Path,
        *,
        profile: object | None = None,
        control_total_acceptance: dict[str, Any] | None = None,
    ) -> tuple[Any, list[Any]]:
        source = Path(path)
        parser_calls.append((source.suffix.lower(), source.name, profile))
        if control_total_acceptance is not None:
            acceptance_calls.append((source.name, control_total_acceptance))
        return SimpleNamespace(file_name=source.name), [source.name]

    monkeypatch.setattr(parser, "prescan_file", prescan_file)
    monkeypatch.setattr(parser, "parse_csv_transactions", parse)
    monkeypatch.setattr(parser, "parse_excel_transactions", parse)
    monkeypatch.setattr(profile_binding, "resolve_base_profile", resolve_base_profile)
    monkeypatch.setattr(profile_binding, "resolve_profile_for_import", resolve_profile_for_import)

    return {
        "committed": committed,
        "context": context,
        "parser_calls": parser_calls,
        "acceptance_calls": acceptance_calls,
        "profile": profile,
    }


def test_acceptance_imports_history_around_main_actuals_in_documented_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """DEC-058's ordered history is needed for EXC-002/003/009 and is not optional."""
    expected = [
        *acc.IMPORT_HISTORY_BEFORE_ACTUALS,
        *acc.ACTUALS_FILES,
        *acc.IMPORT_HISTORY_AFTER_ACTUALS,
    ]
    for name in expected:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).touch()
    _write_control_total_sidecars(tmp_path)

    stubs = _stub_acceptance_imports(monkeypatch, tmp_path)
    result = acc.build_acceptance_context(
        tmp_path / "project", sample_dir=tmp_path, load_actuals=True
    )

    expected_names = [Path(name).name for name in expected]
    assert result is stubs["context"]
    assert stubs["committed"] == expected_names
    assert [name for _, name, _ in stubs["parser_calls"]] == expected_names
    assert [suffix for suffix, _, _ in stubs["parser_calls"]] == [
        ".xlsx" if name.endswith(".xlsx") else ".csv" for name in expected
    ]
    assert all(profile is stubs["profile"] for _, _, profile in stubs["parser_calls"])
    # T-010: the recorded control-total decision rides only with the fixture it
    # belongs to, and reaches the production parser as a keyword argument.
    assert stubs["acceptance_calls"] == [
        (
            "02_gl_batch_039.xlsx",
            {
                "accepted_by": "test-suite",
                "reason": ("Synthetic control-total acceptance recorded by the unit test."),
            },
        )
    ]


def test_acceptance_does_not_silently_skip_a_missing_history_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing history batch would turn cross-batch rules into false negatives."""
    expected = [
        *acc.IMPORT_HISTORY_BEFORE_ACTUALS,
        *acc.ACTUALS_FILES,
        *acc.IMPORT_HISTORY_AFTER_ACTUALS,
    ]
    missing = expected[0]
    for name in expected[1:]:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).touch()

    _stub_acceptance_imports(monkeypatch, tmp_path)
    with pytest.raises(acc.AcceptanceHarnessError, match=missing.replace("/", r"[/\\]")):
        acc.build_acceptance_context(tmp_path / "project", sample_dir=tmp_path, load_actuals=True)


def test_no_actuals_diagnostic_skips_history_and_main_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The explicit diagnostic mode must remain independent of the sample corpus."""
    stubs = _stub_acceptance_imports(monkeypatch, tmp_path)
    result = acc.build_acceptance_context(
        tmp_path / "project", sample_dir=tmp_path, load_actuals=False
    )

    assert result is stubs["context"]
    assert stubs["committed"] == []
    assert stubs["parser_calls"] == []


def test_corpus_integrity_reports_all_files_and_actual_commitability(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Every ordered input is visible; balanced-but-rejected XLSX is not green."""
    for name in acc.ACCEPTANCE_IMPORT_FILES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    _write_control_total_sidecars(tmp_path)

    calls: list[tuple[str, str]] = []
    acceptance_calls: list[tuple[str, dict[str, Any]]] = []

    def make_batch(path: str | Path) -> SimpleNamespace:
        source = Path(path)
        calls.append((source.suffix.lower(), source.name))
        is_gl = source.name in {
            "01_bank_batch_037.csv",
            "02_gl_batch_039.xlsx",
            "d365_gl_actuals.csv",
        }
        is_imbalanced = source.name in {
            "01_bank_batch_037.csv",
            "03_bank_batch_040.csv",
        }
        check_code = "IMP-025" if source.suffix == ".xlsx" else "IMP-023"
        checks = (
            [SimpleNamespace(check_code=check_code, status="fail", severity="high")]
            if is_imbalanced or source.suffix == ".xlsx"
            else []
        )
        return SimpleNamespace(
            source_type="actuals_d365" if is_gl else "actuals_procurement",
            is_balanced=not is_imbalanced,
            can_commit=not is_imbalanced and source.suffix != ".xlsx",
            balance_tolerance=Decimal("500.00"),
            total_source_rows=1,
            loaded_count=1,
            quarantined_count=0,
            rejected_count=0,
            total_debit=Decimal("1.00"),
            total_credit=Decimal("1.00"),
            net_imbalance=Decimal("0.00"),
            checks=checks,
        )

    def parse_csv(path: str | Path) -> SimpleNamespace:
        return make_batch(path)

    def parse_excel(
        path: str | Path,
        *,
        control_total_acceptance: dict[str, Any] | None = None,
    ) -> tuple[SimpleNamespace, list[Any]]:
        if control_total_acceptance is not None:
            acceptance_calls.append((Path(path).name, control_total_acceptance))
        return make_batch(path), []

    monkeypatch.setattr(parser, "parse_and_validate_csv", parse_csv)
    monkeypatch.setattr(parser, "parse_excel_transactions", parse_excel)
    monkeypatch.setattr(
        quality_score,
        "calculate_quality_score",
        lambda batch: SimpleNamespace(
            score=100,
            raw_score=Decimal("100.00"),
            failed_checks=[],
            weight_set_version="test",
        ),
    )

    rows = acc.corpus_integrity(tmp_path)
    assert [row["file"] for row in rows] == list(acc.ACCEPTANCE_IMPORT_FILES)
    assert [name for _, name in calls] == [Path(name).name for name in acc.ACCEPTANCE_IMPORT_FILES]
    # T-010: the recorded control-total decision must reach the production
    # excel parser for the fixture it belongs to, and only for that one.
    assert acceptance_calls == [
        (
            "02_gl_batch_039.xlsx",
            {
                "accepted_by": "test-suite",
                "reason": ("Synthetic control-total acceptance recorded by the unit test."),
            },
        )
    ]
    rejected_gl = next(row for row in rows if row["file"].endswith("039.xlsx"))
    assert rejected_gl["balanced"] is True
    assert rejected_gl["committable"] is False
    assert rejected_gl["recorded_status"] == "rejected"
    assert rejected_gl["failed_checks"] == ["IMP-025"]
    subledger = next(row for row in rows if row["file"].endswith("041.csv"))
    assert "DEC-056/IMP-023" in subledger["balance_gate"]


def test_balanced_but_rejected_general_ledger_blocks_complete_acceptance_measurement() -> None:
    """A failed ControlTotals gate must block even when IMP-023 balance passed."""
    report = acc.AcceptanceReport()
    report.bars = [acc.BarResult("Planted-exception recall", ">= 29 of 32", "0/32", False)]
    acc.attach_corpus_gate(
        report,
        [
            {
                "file": "02_gl_batch_039.xlsx",
                "source_type": "actuals_d365",
                "is_general_ledger": True,
                "balanced": True,
                "committable": False,
                "rows": 110,
                "loaded_count": 110,
                "recorded_status": "rejected",
                "failed_checks": ["IMP-025"],
                "checks_run": 9,
                "data_quality_score": 84,
                "total_debit": "18399650.00",
                "total_credit": "18399650.00",
                "net_imbalance": "0.00",
            }
        ],
        committed_rows={"02_gl_batch_039.xlsx": 0},
    )
    acc.apply_blocked_state(report)

    assert report.verdict == "BLOCKED"
    assert report.blocked_reasons
    assert report.corpus[0]["loaded_count"] == 0
    assert report.corpus[0]["parsed_loaded_count"] == 110
    assert "IMP-025" in report.blocked_reasons[0]
    assert "0 of 110 parsed rows" in report.blocked_reasons[0]
    assert not report.measurable
