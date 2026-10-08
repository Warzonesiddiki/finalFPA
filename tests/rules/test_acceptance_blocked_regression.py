"""REGRESSION (DEF-009 lesson applied to our own instrument): a blocked corpus must
never be reported as a numeric bar result.

Doc 28 §5.0 entry criterion 4 requires the sample corpus to be "loaded and
validated". When it is not, doc 14 §5.3 recall is not a low score - it is
UNMEASURABLE, because no facts exist for the rules to fire on. Reporting
"3/32 recall" in that state is worse than useless: it reads like a rule-quality
verdict and would invite tuning rules to move a number that is really a data
problem.

This file exists so that behaviour is a TESTED GUARANTEE rather than a property
of the implementation. Every assertion here fails if a future change converts
BLOCKED into a plausible-looking red score. It is deliberately separate from
`test_acceptance.py` so the guarantee is greppable on its own.

Author: OpenCode-02, per Lead ruling 2026-10-03.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from app.engine.rules import acceptance as acc

SAMPLE_DIR = Path("sample-data")

#: A measurement that looks like a real bar result, e.g. "3/32" or "9.4 %".
_NUMERIC_RESULT = re.compile(r"\d+\s*/\s*\d+|\d+\.\d+\s*%")


def _unbalanced_gl_corpus() -> list[dict]:
    """The measured shape of the current corpus: GL present, unbalanced, rejected.

    Values are the real ones from `parse_and_validate_csv` on
    `sample-data/d365_gl_actuals.csv`, so the fixture cannot drift into looking
    balanced by accident.
    """
    return [{
        "file": "d365_gl_actuals.csv",
        "source_type": "actuals_d365",
        "is_general_ledger": True,
        "balanced": False,
        "rows": 250037,
        "loaded_count": 250037,
        "quarantined_count": 0,
        "rejected_count": 0,
        "total_debit": "24626607267.80",
        "total_credit": "6682091688.47",
        "net_imbalance": "17944515579.33",
        "recorded_status": "rejected",
        "failed_checks": ["IMP-023"],
        "checks_run": 9,
        "data_quality_score": 84,
        "checksum": "0" * 64,
    }]


def _blocked_report() -> acc.AcceptanceReport:
    """A report driven through the real gate, with plausible bar values set first.

    The bars are populated with values that LOOK like genuine measurements
    ("3/32 = 9.4 %", "18 of 18 High plantings found") so the test proves the
    harness suppresses them rather than merely benefiting from an empty run.
    """
    report = acc.AcceptanceReport()
    report.bars = [
        acc.BarResult("Planted-exception recall", ">= 29 of 32",
                      "3/32 = 9.4 %", False, "3 missed"),
        acc.BarResult("Control precision", "0 of 8", "2 fired", False, "P32, P30"),
        acc.BarResult("High-severity recall", "18 of 18", "3/18", False, ""),
        acc.BarResult("Stability", "identical", "identical", True, ""),
    ]
    report.findings_total = 157
    report.rules = [acc.RuleRow(rule_id="EXC-001", evaluator="evaluate_exc_001",
                               plantings=["P1"], missed=["P1"])]
    acc.attach_corpus_gate(report, _unbalanced_gl_corpus(),
                           committed_rows={"d365_gl_actuals.csv": 0})
    acc.apply_blocked_state(report)
    return report


# ---------------------------------------------------------------------------
# The guarantee
# ---------------------------------------------------------------------------

def test_blocked_run_is_never_reported_as_fail_or_pass():
    """BLOCKED is its own verdict. FAIL would blame the rules; PASS would lie."""
    report = _blocked_report()
    assert report.verdict == "BLOCKED"
    assert report.verdict not in {"PASS", "FAIL"}
    assert report.passed is False
    assert report.measurable is False


def test_no_bar_survives_as_a_numeric_result():
    """The core assertion: plausible-looking numbers must not leak out.

    This is the specific failure the Lead named - BLOCKED quietly becoming a
    red score. Each bar keeps its computed value internally for diagnosis, but
    `measurable` goes False, `passed` goes False, and `to_dict()` renders
    "NOT MEASURED".
    """
    report = _blocked_report()
    payload = report.to_dict()

    assert payload["verdict"] == "BLOCKED"
    assert payload["measurable"] is False
    assert payload["passed"] is False

    for bar in report.bars:
        assert bar.measurable is False, f"{bar.name} still marked measurable"
        assert bar.passed is False, f"{bar.name} still reports passed=True"

    for bar in payload["bars"]:
        assert bar["measured"] == "NOT MEASURED", (
            f"{bar['name']} leaked a numeric measurement: {bar['measured']!r}"
        )
        assert bar["measurable"] is False
        assert bar["passed"] is False
        assert not _NUMERIC_RESULT.search(bar["measured"])


def test_serialised_report_carries_no_recall_fraction():
    """A JSON consumer must not find a recall fraction to quote."""
    payload = json.loads(json.dumps(_blocked_report().to_dict()))
    assert payload["verdict"] == "BLOCKED"
    assert payload["blocked_reasons"], "BLOCKED without a reason is a silent block"
    for bar in payload["bars"]:
        assert not _NUMERIC_RESULT.search(bar["measured"]), (
            f"{bar['name']} is quotable as a result: {bar['measured']!r}"
        )


def test_markdown_report_states_not_measured_and_labels_the_table():
    """The human-readable report must not present the table as a bar result."""
    md = acc.render_markdown(_blocked_report())
    assert "**Verdict: BLOCKED**" in md
    assert "NOT MEASURED" in md
    assert "BLOCKED REASONS" in md
    assert "DIAGNOSTIC ONLY, NOT A BAR RESULT" in md
    # The doc 28 §5.0 criterion the block refers to must be cited.
    assert "5.0" in md and "loaded and validated" in md


def test_blocked_reason_names_the_measured_cause():
    """The reason must be specific enough to act on."""
    report = _blocked_report()
    assert len(report.blocked_reasons) == 1
    reason = report.blocked_reasons[0]
    for needle in ("d365_gl_actuals.csv", "actuals_d365", "17944515579.33",
                   "IMP-023", "0 of 250037", "data_quality_score=84"):
        assert needle in reason, f"blocked reason omits {needle!r}"


def test_passed_property_consults_blocked_reasons_independently():
    """`passed` must consult `blocked_reasons` in its own right.

    Found by mutation testing: while `apply_blocked_state` forces every bar to
    `passed=False`, a future change that stopped doing so would leave
    `passed` returning True on a blocked run unless it also checked the reasons.
    This pins that second line of defence directly.
    """
    report = acc.AcceptanceReport()
    report.bars = [acc.BarResult("Planted-exception recall", ">= 29 of 32",
                                 "32/32 = 100.0 %", True)]
    report.blocked_reasons = ["synthetic block, bars left untouched"]
    assert not report.passed, (
        "passed returned True on a blocked run whose bars were all green"
    )

    # And the same report with no block must pass, so the check is not vacuous.
    unblocked = acc.AcceptanceReport()
    unblocked.bars = [acc.BarResult("Planted-exception recall", ">= 29 of 32",
                                    "32/32 = 100.0 %", True)]
    assert unblocked.passed is True


def test_balanced_corpus_does_not_block():
    """The opposite guarantee: a healthy corpus must still be measurable.

    Without this, a harness that blocked unconditionally would satisfy every
    test above while measuring nothing, forever.
    """
    report = acc.AcceptanceReport()
    report.bars = [acc.BarResult("Planted-exception recall", ">= 29 of 32",
                                 "32/32 = 100.0 %", True)]
    corpus = [{
        "file": "d365_gl_actuals.csv", "source_type": "actuals_d365",
        "is_general_ledger": True, "balanced": True, "rows": 250037,
        "total_debit": "100.00", "total_credit": "100.00",
        "net_imbalance": "0.00", "recorded_status": "committed",
        "failed_checks": [], "checks_run": 9, "data_quality_score": 100,
        "checksum": "a" * 64,
    }]
    acc.attach_corpus_gate(report, corpus, committed_rows={"d365_gl_actuals.csv": 250037})
    acc.apply_blocked_state(report)

    assert report.verdict != "BLOCKED"
    assert report.measurable is True
    assert report.bars[0].measurable is True
    assert report.bars[0].passed is True
    assert report.passed is True


# ---------------------------------------------------------------------------
# End-to-end through the real gate
# ---------------------------------------------------------------------------

def test_run_acceptance_end_to_end_reports_blocked(tmp_path):
    """Drive the real entry point against a synthetic unbalanced corpus.

    Uses the true `run_acceptance` path - answer key, corpus integrity gate,
    context build, measure - so this proves the shipped behaviour rather than the
    two-function composition the unit tests above exercise. The corpus is written
    to `tmp_path`; `sample-data/` is never touched.
    """
    fake = tmp_path / "sample_data"
    fake.mkdir()
    shutil.copy2(SAMPLE_DIR / "expected_exceptions.csv",
                 fake / "expected_exceptions.csv")

    # T-010: since DEC-056's control-total gate the harness refuses to run
    # unless the FULL ordered fixture set plus the recorded control-total
    # sidecar exist, so the synthetic corpus carries the real history and
    # sub-ledger fixtures; only the general ledger is replaced with the
    # deliberately unbalanced file under test. That makes this a stronger
    # proof than before: everything healthy except the GL must still BLOCK.
    for name in acc.ACCEPTANCE_IMPORT_FILES:
        if Path(name).name == "d365_gl_actuals.csv":
            continue
        dest = fake / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SAMPLE_DIR / name, dest)
    for sidecar in acc.CONTROL_TOTAL_ACCEPTANCE_FIXTURES.values():
        dest = fake / sidecar
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SAMPLE_DIR / sidecar, dest)

    # A minimal general-ledger CSV whose debits do not equal its credits. The
    # watermark first line matches the real corpus so parsing behaves the same.
    header = ("VoucherNo,PostingDate,CompanyCode,AccountCode,CostCenterCode,"
              "ProjectCode,VendorCode,InvoiceNo,Description,Debit,Credit,"
              "CurrencyCode,Watermark,ProjectType")
    (fake / "d365_gl_actuals.csv").write_text(
        "# SAMPLE DATA - NOT FOR PRODUCTION USE\n"
        f"{header}\n"
        "VCH-1,2026-09-15,IN01,5200,CC-100,PRJ-01,V-00931,INV-1,"
        "deliberately unbalanced,1000.00,0.00,INR,WATERMARK,sample\n",
        encoding="utf-8",
    )

    report = acc.run_acceptance(sample_dir=fake, project_dir=tmp_path / "proj",
                                stability_runs=1)

    assert report.verdict == "BLOCKED", (
        f"an unbalanced GL must block the run, got {report.verdict}"
    )
    assert not report.passed
    assert not report.measurable
    assert report.blocked_reasons
    assert all(b.measurable is False and b.passed is False for b in report.bars)
    for bar in report.to_dict()["bars"]:
        assert bar["measured"] == "NOT MEASURED"


@pytest.mark.perf
def test_live_corpus_is_blocked_and_says_so(live_acceptance_report):
    """The committed corpus, whatever it is today, must land in an honest state.

    Deliberately tolerant of both outcomes: when the generator is fixed and the
    GL balances, this still passes by asserting the bars are then measurable and
    really evaluated. It only fails if the run claims a result it did not earn.
    """
    report = live_acceptance_report
    if report.verdict == "BLOCKED":
        assert report.blocked_reasons
        assert not report.measurable
        assert not report.passed
        for bar in report.to_dict()["bars"]:
            assert bar["measured"] == "NOT MEASURED"
    else:
        assert report.measurable, "not BLOCKED but reported unmeasurable"
        assert all(b.measurable for b in report.bars), (
            "a measurable run must actually evaluate every bar"
        )


@pytest.fixture(scope="module")
def live_acceptance_report(tmp_path_factory):
    """Reuse the harness's own live fixture input (real corpus, isolated DB)."""
    project_dir = tmp_path_factory.mktemp("fpa_acceptance_blocked")
    return acc.run_acceptance(sample_dir=SAMPLE_DIR, project_dir=project_dir)