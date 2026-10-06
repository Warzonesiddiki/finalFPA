"""Planted-exception acceptance harness (doc 14 §5.2).

Doc 14 §5.2 contract, summarized here (the earlier XLSX exclusion was superseded
on 2026-10-06):

    ### 5.2 The harness

    `tests/rules/test_acceptance.py` (L3), run by `scripts/acceptance`:

    1. **Corpus fingerprint:** the checked-in sample project was generated from
       the canonical seed (`sample-data --seed 42`). `run_acceptance` fingerprints
       it; it does not regenerate the corpus or assert against a golden digest.
       The generator's two-run reproducibility check lives separately in
       `tests/unit/test_corpus_determinism.py`. Before evaluating, the harness
       records SHA-256 digests for every `.csv`, `.xlsx`, and `.json` data artefact
       under `sample-data/`, keyed by relative path. Generated workbooks use the
       deterministic saver; the report makes the exact scope and exclusions visible.
    2. **Full engine run** over the sample data with default thresholds, every
       rule enabled. DEC-058 requires earlier import-history batches before the
       main actuals and later history batches afterwards.
    3. **Join** raised exceptions to the answer key on `(rule_id, subject_key)`.
    4. **Classify** every raise: *expected* (in the key), *control* (a
       `P25`…`P32` subject), or *extra*.
    5. **Report** to `acceptance_report.json` and a human-readable
       `acceptance_report.md`: counts by severity, the miss list with each
       rule's threshold reasoning, the extra-findings list with the false-positive
       log reference, and the controls result.
    6. **Fail the build** when a bar in §5.3 is not met. A red acceptance run is
       a **release-blocking** defect.

Doc 14 §5.3, quoted verbatim (the bars this module enforces; none are relaxed):

    | Bar | Value | Notes |
    |---|---|---|
    | Planted-exception recall | **>= 90 %** of the 32 raises (>= 29) | `06` §8.3 |
    | Control precision | **0 of 8** controls may raise | `06` §8.3 - any
      control raise is a P0 defect in the rule's precision filter |
    | High-severity recall | **18 of 18** High plantings found | `14`-owned
      stricter bar: a missed High is a control failure, not a statistic |
    | Extra findings | Every extra raise justified in the false-positive log |
      `06` §8.3; a rule with > 3 unexplained findings is tuned or documented
      before the gate |
    | Stability | Two consecutive runs produce identical raise sets |
      Determinism (no ordering/seed effects) |

Doc 28 §5.0 entry criterion 4, quoted verbatim, which gates whether the corpus
may be measured at all:

    | 4 | Sample data corpus (250k rows) loaded and validated | Validation
      reports and data-quality scores recorded for each imported file |

DESIGN NOTES - traps this harness exists to make impossible to repeat.

1. **The join key is `catalog_rule_id or rule_id`, never `rule_id` alone.**
   `Finding.rule_id` is ENGINE-space. For the eight catalog rules carried inside
   `BATCH_01_08_EVALUATORS` the engine id differs from the catalog id (engine
   `evaluate_exc_005` is catalog `EXC-012`), so joining on `rule_id` compares two
   different namespaces. Measured on this corpus that mistake moves recall from
   25.0 % to 9.4 % with the engine completely unchanged.
2. **Every ordered import is checked for commitability before the verdict.**
   Journal balance, the DEC-056 sub-ledger tolerance, and control-total failures
   can each prevent a history fixture from reaching `FactActual`. A rejected GL
   fixture therefore blocks interpretation of the §5.3 bars; rejected sub-ledger
   fixtures are named as divergences. Neither is disguised as a rule-logic miss.
3. **Nothing is skipped.** No `pytest.skip`, no `xfail`, no early return on a
   broken corpus. A missing prerequisite is a failure with a message.

READ-ONLY. This module parses `sample-data/` and writes only into the throwaway
project directory it is given. It never opens the live user database.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Corpus / answer-key locations
# --------------------------------------------------------------------------

DEFAULT_SAMPLE_DIR = Path("sample-data")
ANSWER_KEY_NAME = "expected_exceptions.csv"
BUDGET_NAME = "budget_fy26.csv"

#: Ordered history imports required by docs/14 §5.2 step 2 and DEC-058.
#: 037/039 establish the earlier committed state; 040/041 are later sub-ledgers
#: whose plantings must be evaluated after the main source files are loaded.
IMPORT_HISTORY_BEFORE_ACTUALS = (
    "import_history/01_bank_batch_037.csv",
    "import_history/02_gl_batch_039.xlsx",
)
IMPORT_HISTORY_AFTER_ACTUALS = (
    "import_history/03_bank_batch_040.csv",
    "import_history/04_bank_batch_041.csv",
)

#: Actuals files that carry the main planted cases. `test_comment.csv` is a
#: parser edge-case fixture, not part of the 40 plantings.
ACTUALS_FILES = (
    "d365_gl_actuals.csv",
    "bank_ledger_actuals.csv",
    "payroll_procurement_actuals.csv",
)

#: Exact import order matters: EXC-002 compares a later batch with earlier
#: committed rows; the batch-040/041 plantings follow the main actuals.
ACCEPTANCE_IMPORT_FILES = (
    *IMPORT_HISTORY_BEFORE_ACTUALS,
    *ACTUALS_FILES,
    *IMPORT_HISTORY_AFTER_ACTUALS,
)

#: Stable source-side identities for history fixtures; integer database keys are
#: deliberately excluded from answer-key subject identities.
ACCEPTANCE_BATCH_IDENTITIES: Dict[str, Tuple[str, Optional[str]]] = {
    "import_history/01_bank_batch_037.csv": ("batch_037", "general_ledger"),
    "import_history/02_gl_batch_039.xlsx": ("batch_039", None),
    "import_history/03_bank_batch_040.csv": ("batch_040", "bank_ledger"),
    "import_history/04_bank_batch_041.csv": ("batch_041", "bank_ledger"),
}

#: Explicitly recorded decision for the synthetic over-tolerance P3 control total.
#: It is kept beside the fixture and supplied only by this acceptance harness.
CONTROL_TOTAL_ACCEPTANCE_FIXTURES = {
    "import_history/02_gl_batch_039.xlsx": (
        "import_history/02_gl_batch_039.acceptance.json"
    ),
}

#: The period every planted case is asserted against (doc 14 §5.1 answer key
#: carries `period` per row; all 40 rows are FY26-P09).
PERIOD_CODE = "FY26-P09"

#: ASSUMPTION, stated because doc 14 does not specify a run date.
#: Doc 14 §5.2 step 2 says only "with default thresholds, every rule enabled".
#: The answer key's P11 note reads "Posting on 30-Nov-2026 is 18 days ahead of
#: run date", and 2026-11-30 minus 18 days is 2026-11-12, so the corpus was
#: authored against an as_of of 2026-11-12. That is the only run date derivable
#: from the spec, so it is the default here. It is passed in explicitly rather
#: than read from a clock: doc 06 line 195 requires "no clock beyond an injected
#: `as_of` date".
DEFAULT_AS_OF = "2026-11-12"

#: Doc 14 §5.4 per-rule map, transcribed verbatim. Used to cross-check the
#: answer key, NOT as the source of truth: doc 14 §5.1 line 221-222 states
#: "`sample-data/expected_exceptions.csv` is the answer key". Divergences are
#: reported, never silently reconciled.
DOC14_SECTION_5_4_CONTROLS: Dict[str, Tuple[str, ...]] = {
    "EXC-007": ("P25",),
    "EXC-008": ("P26",),
    "EXC-012": ("P27",),
    "EXC-013": ("P28",),
    "EXC-015": ("P32",),
    "EXC-018": ("P29", "P30"),
    "EXC-021": ("P31",),
}

CATALOG_RULE_IDS: Tuple[str, ...] = tuple(f"EXC-{i:03d}" for i in range(1, 25))

#: Doc 14 §5.3, restated as code. These are the numbers; they are not derived
#: and not negotiable at runtime.
BAR_RECALL_MIN_HITS = 29          # ">= 90 % of the 32 raises (>= 29)"
BAR_CONTROL_RAISES_MAX = 0        # "0 of 8 controls may raise"
BAR_HIGH_SEVERITY_REQUIRED = 18   # "18 of 18 High plantings found"
BAR_UNEXPLAINED_EXTRAS_PER_RULE = 3   # "a rule with > 3 unexplained findings"


class AcceptanceHarnessError(RuntimeError):
    """Raised when the harness cannot legitimately measure the bars.

    Deliberately an error, not a skip: doc 14 §5.2 step 6 makes a red
    acceptance run release-blocking, so an unmeasurable run is a failure.
    """


# --------------------------------------------------------------------------
# Result shapes
# --------------------------------------------------------------------------

@dataclass
class BarResult:
    """One doc 14 §5.3 bar. `passed` is computed, never supplied.

    `measurable=False` means the corpus precondition was not met, so the bar was
    NOT evaluated. `passed` is then meaningless and the report must not present
    it as a rule result - see `AcceptanceReport.verdict == "BLOCKED"`.
    """

    name: str
    requirement: str
    measured: str
    passed: bool
    detail: str = ""
    measurable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "requirement": self.requirement,
            "measured": self.measured if self.measurable else "NOT MEASURED",
            "passed": self.passed,
            "measurable": self.measurable,
            "detail": self.detail,
        }


@dataclass
class RuleRow:
    """One row of the per-rule recall table (doc 14 §5.4)."""

    rule_id: str
    evaluator: str
    plantings: List[str] = field(default_factory=list)
    detected: List[str] = field(default_factory=list)
    missed: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    controls_fired: List[str] = field(default_factory=list)
    findings_raised: int = 0
    extras: int = 0
    wired: bool = True

    @property
    def recall_pct(self) -> Optional[float]:
        expected = len(self.plantings)
        if expected == 0:
            return None
        return round(len(self.detected) / expected * 100.0, 1)

    @property
    def zero_coverage(self) -> bool:
        """True when the rule cannot be measured or produced nothing at all.

        Doc 14 §5.3 has no numeric per-rule bar, so this is a
        completeness gate rather than an invented threshold: a rule that is
        unwired, or that has planted cases yet raised nothing, means the
        measurement is not trustworthy and the run must fail loudly.
        """
        return (not self.wired) or (bool(self.plantings) and not self.detected)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "evaluator": self.evaluator,
            "plantings": self.plantings,
            "detected": self.detected,
            "missed": self.missed,
            "controls": self.controls,
            "controls_fired": self.controls_fired,
            "findings_raised": self.findings_raised,
            "extras": self.extras,
            "wired": self.wired,
            "recall_pct": self.recall_pct,
            "zero_coverage": self.zero_coverage,
        }


@dataclass
class AcceptanceReport:
    """Outcome of one acceptance run.

    `verdict` is one of:

    - ``PASS``   - every §5.3 bar met on a measurable corpus.
    - ``FAIL``   - the corpus was measurable and a bar was not met, or a
      prerequisite other than corpus balance was violated.
    - ``BLOCKED``- the corpus precondition (doc 28 §5.0 criterion 4) is not met,
      so the §5.3 bars **cannot be measured**. This is deliberately distinct
      from both PASS and FAIL: reporting a low recall number for a corpus that
      never loaded would blame the rule engine for a data problem, and reporting
      PASS would be a green vacuum. ``BLOCKED`` is reported loudly, never
      silently, and the CLI exits 2 so it can never be mistaken for success.
    """

    verdict: str = "FAIL"
    bars: List[BarResult] = field(default_factory=list)
    rules: List[RuleRow] = field(default_factory=list)
    corpus: List[Dict[str, Any]] = field(default_factory=list)
    divergences: List[str] = field(default_factory=list)
    hard_failures: List[str] = field(default_factory=list)
    blocked_reasons: List[str] = field(default_factory=list)
    findings_total: int = 0
    extras_total: int = 0
    miss_list: List[Dict[str, str]] = field(default_factory=list)
    extras_by_rule: Dict[str, int] = field(default_factory=dict)
    controls_fired: List[Dict[str, str]] = field(default_factory=list)
    severity_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    corpus_checksum: Dict[str, str] = field(default_factory=dict)
    checksum_scope: Dict[str, Any] = field(default_factory=dict)
    as_of: str = DEFAULT_AS_OF
    period: str = PERIOD_CODE
    elapsed_seconds: float = 0.0

    @property
    def measurable(self) -> bool:
        """True when the §5.3 bars were actually measured."""
        return not self.blocked_reasons

    @property
    def passed(self) -> bool:
        """True only when every bar was measured AND met.

        Deliberately independent of `verdict`: `measure()` derives the verdict
        from this, so making `passed` read `verdict` would be circular and would
        make a perfect run impossible to pass. `verdict` is the outward-facing
        summary (PASS / FAIL / BLOCKED); `passed` is the strict bar check.
        """
        return (
            not self.blocked_reasons
            and not self.hard_failures
            and bool(self.bars)
            and all(b.passed for b in self.bars)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "passed": self.passed,
            "measurable": self.measurable,
            "blocked_reasons": self.blocked_reasons,
            "as_of": self.as_of,
            "period": self.period,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "corpus_checksum": self.corpus_checksum,
            "checksum_scope": self.checksum_scope,
            "corpus": self.corpus,
            "divergences": self.divergences,
            "hard_failures": self.hard_failures,
            "bars": [b.to_dict() for b in self.bars],
            "per_rule": [r.to_dict() for r in self.rules],
            "findings_total": self.findings_total,
            "extras_total": self.extras_total,
            "extras_by_rule": self.extras_by_rule,
            "miss_list": self.miss_list,
            "controls_fired": self.controls_fired,
            "severity_counts": self.severity_counts,
        }


# --------------------------------------------------------------------------
# Step 1 - the answer key and the corpus checksum
# --------------------------------------------------------------------------

def file_checksum(path: Path) -> str:
    """Return a SHA-256 fingerprint for a corpus data artefact.

    The digest is streamed in bounded chunks so the 250k-row GL fixture does not
    need to be held in memory. This records a reproducible per-run manifest; no
    committed golden checksum exists, so the report does not pretend to assert
    against a trusted constant.
    """
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


#: Every data artifact format emitted or used by the acceptance corpus.
#: Excel writers pin document and ZIP timestamps in xlsx_deterministic.py; the
#: JSON import-acceptance sidecar is part of the history fixture's provenance.
CHECKSUMMED_SUFFIXES = (".csv", ".json", ".xlsx")

#: Retained as an explicit, reportable list. The supported corpus formats above
#: are currently fingerprinted in full, so this must remain empty unless a
#: format is deliberately excluded with a documented and measured reason.
NON_REPRODUCIBLE: Tuple[Tuple[str, str], ...] = ()


def checksum_scope(sample_dir: Path = DEFAULT_SAMPLE_DIR) -> Dict[str, Any]:
    """Return an auditable SHA-256 manifest for recognized corpus data files.

    Paths are recorded RELATIVE to `sample_dir` and de-duplicated by path, not by
    bare filename: `sample-data/test_scale/` holds a second copy of the malformed
    and template fixtures, so keying on `p.name` would double-count every one of
    them and misreport the scope. The acceptance JSON sidecar is included because
    its recorded decision permits the history workbook to commit.
    """
    def _rel_paths(suffixes) -> list[str]:
        seen = set()
        for p in sample_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in suffixes:
                seen.add(p.relative_to(sample_dir).as_posix())
        return sorted(seen)

    fingerprinted = _rel_paths(CHECKSUMMED_SUFFIXES)
    checksums = {
        relative_path: file_checksum(sample_dir / relative_path)
        for relative_path in fingerprinted
    }
    excluded = _rel_paths({suffix for suffix, _ in NON_REPRODUCIBLE})
    return {
        "fingerprinted_count": len(fingerprinted),
        "fingerprinted_suffixes": sorted(CHECKSUMMED_SUFFIXES),
        "fingerprinted": fingerprinted,
        "sha256": checksums,
        "excluded_count": len(excluded),
        "excluded_suffixes": [suffix for suffix, _ in NON_REPRODUCIBLE],
        "exclusion_reason": {suffix: why for suffix, why in NON_REPRODUCIBLE},
        "excluded": excluded,
        "note": "paths are relative to the sample dir; test_scale/ holds second "
                "copies of templates and malformed fixtures, counted as separate "
                "paths; the history acceptance sidecar is included",
    }


def load_answer_key(sample_dir: Path = DEFAULT_SAMPLE_DIR) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    """Split the answer key into (expected raises, precision controls, other rows).

    Doc 14 §5.1: the file is the answer key
    (`planting_id, rule_id, expected_verdict, subject_key, severity, amount,
    period, notes`), 32 expected raises `P1`..`P24` and 8 controls `P25`..`P32`.

    The file opens with a `#` watermark comment line. `csv.DictReader` would
    consume it as the header row, so comment lines are stripped first.
    """
    path = sample_dir / ANSWER_KEY_NAME
    if not path.exists():
        raise AcceptanceHarnessError(f"Answer key not found: {path}")

    lines = [
        line for line in path.read_text(encoding="utf-8-sig").splitlines()
        if not line.lstrip().startswith("#")
    ]
    rows = list(csv.DictReader(lines))
    if not rows:
        raise AcceptanceHarnessError(f"Answer key {path} parsed to zero rows")

    def planting_number(row: Dict[str, str]) -> Optional[int]:
        pid = (row.get("planting_id") or "").strip()
        if not pid.startswith("P") or not pid[1:].isdigit():
            return None
        return int(pid[1:])

    raises, controls, other = [], [], []
    for row in rows:
        n = planting_number(row)
        if n is not None and n <= 24:
            raises.append(row)
        elif n is not None and n <= 32:
            controls.append(row)
        else:
            other.append(row)

    if len(raises) != 32:
        raise AcceptanceHarnessError(
            f"Doc 14 §5.1 states 32 expected raises (P1..P24); answer key has "
            f"{len(raises)}. The corpus and the spec disagree - refusing to score."
        )
    if len(controls) != 8:
        raise AcceptanceHarnessError(
            f"Doc 14 §5.1 states 8 precision controls (P25..P32); answer key has "
            f"{len(controls)}. Refusing to score."
        )
    return raises, controls, other


def validate_answer_key(
    raises: Sequence[Dict[str, str]],
    controls: Sequence[Dict[str, str]],
) -> List[str]:
    """Cross-check the answer key against doc 14 §5.4. Returns divergences.

    Divergences are REPORTED, never reconciled: doc 14 §5.1 makes the CSV the
    authority, so the fixture wins on content and §5.4 is used to prove the
    fixture still describes the same 24 rules and the same 7 controlled rules.
    """
    notes: List[str] = []

    rules_with_raises = {r["rule_id"] for r in raises}
    unplanted = [r for r in CATALOG_RULE_IDS if r not in rules_with_raises]
    if unplanted:
        notes.append(
            f"Catalog rules with NO raise planting in the answer key: {unplanted}. "
            f"Doc 14 §5.4 maps all 24 to a planting."
        )

    fixture_controls: Dict[str, set] = {}
    for row in controls:
        fixture_controls.setdefault(row["rule_id"], set()).add(row["planting_id"])
    # Compare like with like: both sides normalised to {rule_id: frozenset(ids)}.
    # Comparing a set-valued dict against a tuple-valued one would report a
    # divergence on every run.
    normalised_fixture = {k: frozenset(v) for k, v in fixture_controls.items()}
    normalised_doc14 = {k: frozenset(v)
                        for k, v in DOC14_SECTION_5_4_CONTROLS.items()}
    if normalised_fixture != normalised_doc14:
        notes.append(
            "Control assignment diverges from doc 14 §5.4. "
            f"fixture={ {k: sorted(v) for k, v in sorted(normalised_fixture.items())} } "
            f"doc14={ {k: sorted(v) for k, v in sorted(normalised_doc14.items())} }"
        )

    sev = {}
    for row in raises:
        sev[row["severity"]] = sev.get(row["severity"], 0) + 1
    if sev.get("High") != 18 or sev.get("Medium") != 12 or sev.get("Low") != 2:
        notes.append(
            f"Doc 14 §5.1 states 18 High / 12 Medium / 2 Low; answer key has {sev}."
        )

    periods = {r["period"] for r in list(raises) + list(controls)}
    unexpected = {p for p in periods if p != PERIOD_CODE}
    if unexpected:
        notes.append(
            f"Answer key rows assert periods other than {PERIOD_CODE}: "
            f"{sorted(unexpected)}. The harness evaluates a single period."
        )
    return notes


def _control_total_acceptance_for_fixture(
    sample_dir: Path, relative_name: str
) -> Optional[Dict[str, str]]:
    """Load a recorded synthetic acceptance decision for a named fixture only."""
    sidecar_name = CONTROL_TOTAL_ACCEPTANCE_FIXTURES.get(relative_name)
    if sidecar_name is None:
        return None

    sidecar_path = sample_dir / sidecar_name
    try:
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceHarnessError(
            f"Cannot load control-total acceptance fixture {sidecar_name}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise AcceptanceHarnessError(
            f"Control-total acceptance fixture {sidecar_name} must be a JSON object"
        )

    allowed_fields = {"accepted_by", "reason", "accepted_at"}
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        raise AcceptanceHarnessError(
            f"Control-total acceptance fixture {sidecar_name} has unknown field(s): "
            + ", ".join(sorted(unknown_fields))
        )
    accepted_by = str(payload.get("accepted_by", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    if not accepted_by or len(reason) < 10:
        raise AcceptanceHarnessError(
            f"Control-total acceptance fixture {sidecar_name} requires accepted_by "
            "and a reason of at least 10 characters"
        )

    acceptance = {"accepted_by": accepted_by, "reason": reason}
    accepted_at = payload.get("accepted_at")
    if accepted_at is not None:
        accepted_at_text = str(accepted_at).strip()
        if not accepted_at_text:
            raise AcceptanceHarnessError(
                f"Control-total acceptance fixture {sidecar_name} has an empty accepted_at"
            )
        acceptance["accepted_at"] = accepted_at_text
    return acceptance


def corpus_integrity(sample_dir: Path = DEFAULT_SAMPLE_DIR) -> List[Dict[str, Any]]:
    """Parse every acceptance import in order and report its commit precondition.

    CSV and XLSX fixtures use the production parsers, so the report carries the
    engine's own validation checks (`IMP-001`…`IMP-025`) and computed data-quality
    scores rather than a second opinion. Money stays `Decimal` end to end
    (`ImportBatchResult.total_debit` / `total_credit` / `net_imbalance` are
    already `Decimal`); nothing here re-derives an engine result. The committed
    status comes from `batch.can_commit`, not balance alone: a balanced workbook
    rejected by `IMP-025` is still rejected and must not look loadable.

    Per `04` §12 / DEC-056, journal sources use the exact debit=credit gate while
    amount-style sub-ledgers reconcile net within the documented tolerance.
    `ImportRepository.commit_batch` also blocks on structural and control-total
    failures (`IMP-005`/`006`/`008`/`025`), so the report must distinguish a
    balanced-but-rejected workbook from a committed batch. A rejected GL import
    that supplies a planting is a corpus precondition failure (BLOCKED); a
    rejected sub-ledger is a visible divergence, never resolved by the harness.

    `data_quality_score` is read, never assumed: since `DEF-009` it is computed
    by `calculate_quality_score()`, not the old literal 100.
    """
    from app.engine.calc.quality_score import calculate_quality_score
    from app.engine.imports.parser import parse_and_validate_csv, parse_excel_transactions

    rows: List[Dict[str, Any]] = []
    for name in ACCEPTANCE_IMPORT_FILES:
        path = sample_dir / name
        if not path.exists():
            rows.append(
                {
                    "file": name,
                    "status": "MISSING",
                    "balanced": False,
                    "committable": False,
                    "is_general_ledger": None,
                    "balance_gate": "unknown",
                }
            )
            continue
        try:
            control_total_acceptance = _control_total_acceptance_for_fixture(
                sample_dir, name
            )
            if path.suffix.lower() in {".xlsx", ".xlsm"}:
                batch, _ = parse_excel_transactions(
                    path, control_total_acceptance=control_total_acceptance
                )
            else:
                batch = parse_and_validate_csv(path)
        except Exception as exc:  # a file that cannot be parsed is a hard failure
            rows.append(
                {
                    "file": name,
                    "status": f"PARSE-ERROR: {type(exc).__name__}: {exc}",
                    "balanced": False,
                    "committable": False,
                    "rows": 0,
                    "is_general_ledger": None,
                    "balance_gate": "unknown",
                    "checks": [],
                    "checks_run": 0,
                }
            )
            continue

        is_gl = batch.source_type == "actuals_d365"
        dq = calculate_quality_score(batch)
        can_commit = bool(batch.can_commit)
        if batch.source_type in {"actuals_d365", "budget"}:
            balance_gate = "journal exact debit=credit (04 §12/IMP-023)"
        else:
            balance_gate = (
                "sub-ledger net reconciliation "
                f"(DEC-056/IMP-023; tolerance ₹{batch.balance_tolerance})"
            )
        rows.append(
            {
                "file": name,
                "source_type": batch.source_type,
                "is_general_ledger": is_gl,
                "recorded_status": "committed" if can_commit else "rejected",
                "status": "committed" if can_commit else "rejected",
                "balanced": bool(batch.is_balanced),
                "committable": can_commit,
                "balance_gate": balance_gate,
                "rows": batch.total_source_rows,
                "loaded_count": batch.loaded_count,
                "quarantined_count": batch.quarantined_count,
                "rejected_count": batch.rejected_count,
                "total_debit": str(batch.total_debit),
                "total_credit": str(batch.total_credit),
                "net_imbalance": str(batch.net_imbalance),
                "checks_run": len(batch.checks),
                "checks": [
                    {"code": c.check_code, "status": c.status, "severity": c.severity}
                    for c in batch.checks
                ],
                "failed_checks": [
                    c.check_code
                    for c in batch.checks
                    if str(c.status).lower() in {"fail", "failed"}
                ],
                # The engine's own score, not a re-derivation; CALC-050 owns rounding.
                "data_quality_score": dq.score,
                "data_quality_raw_score": str(dq.raw_score),
                "data_quality_failed": [c.check_code for c in dq.failed_checks],
                "data_quality_weight_set": dq.weight_set_version,
                "checksum": file_checksum(path),
            }
        )
    return rows


def measure_committed_rows(db) -> Dict[str, int]:
    """Count rows that actually landed in FactActual, per source file.

    Measured rather than assumed. `commit_batch` now derives both the audit row
    and the rows it writes from one `should_commit` decision (DEF-010), so the
    metadata and the analytic store agree by construction - but the harness
    still measures the landed count instead of trusting it, because a row count
    is exactly the sort of thing a broken corpus or a silently skipped insert
    changes without changing the report.
    """
    conn = db.get_duckdb_connection()
    try:
        rows = conn.execute(
            "SELECT source_file_name, COUNT(*) FROM FactActual "
            "GROUP BY source_file_name"
        ).fetchall()
    except Exception:
        return {}
    finally:
        conn.close()
    return {str(r[0]): int(r[1]) for r in rows}


# --------------------------------------------------------------------------
# Step 2 - build the context the production path would build
# --------------------------------------------------------------------------

def build_acceptance_context(
    project_dir: Path,
    sample_dir: Path = DEFAULT_SAMPLE_DIR,
    period_code: str = PERIOD_CODE,
    as_of_date: str = DEFAULT_AS_OF,
    load_actuals: bool = True,
):
    """Build a RuleContext from a throwaway project database.

    Uses `ExceptionsRepository.build_rule_context`, the same context the CLI
    (`fpa exceptions --run`) and API (`POST /api/v1/exceptions/run`) use, so the
    harness measures the production path rather than a hand-built approximation.

    `project_dir` is created fresh and is the only thing written.
    """
    if load_actuals:
        required_fixtures = [
            *ACCEPTANCE_IMPORT_FILES,
            *CONTROL_TOTAL_ACCEPTANCE_FIXTURES.values(),
        ]
        missing = [name for name in required_fixtures if not (sample_dir / name).is_file()]
        if missing:
            raise AcceptanceHarnessError(
                "Required acceptance fixture(s) missing: " + ", ".join(missing)
            )

    os.environ["FPA_PROJECT_DIR"] = str(project_dir)

    from app.engine.imports.parser import (
        parse_csv_transactions,
        parse_excel_transactions,
        prescan_file,
    )
    from app.engine.imports.profile_binding import (
        resolve_base_profile,
        resolve_profile_for_import,
    )
    from app.engine.store.db import DatabaseManager
    from app.engine.store.exceptions_repo import ExceptionsRepository
    from app.engine.store.import_repo import ImportRepository

    db = DatabaseManager()
    repo = ImportRepository(db)

    if load_actuals:
        for name in ACCEPTANCE_IMPORT_FILES:
            path = sample_dir / name
            prescan = prescan_file(path)
            base_profile = resolve_base_profile(db, prescan.sample_headers)
            binding = resolve_profile_for_import(db, base_profile=base_profile)
            control_total_acceptance = _control_total_acceptance_for_fixture(
                sample_dir, name
            )
            if path.suffix.lower() in {".xlsx", ".xlsm"}:
                batch, txs = parse_excel_transactions(
                    path,
                    profile=binding.profile,
                    control_total_acceptance=control_total_acceptance,
                )
            else:
                batch, txs = parse_csv_transactions(path, profile=binding.profile)
            identity = ACCEPTANCE_BATCH_IDENTITIES.get(name)
            if identity is not None:
                batch.external_batch_ref, batch.subject_namespace = identity
            repo.commit_batch(batch, txs)

    _load_budget(db, repo, sample_dir / BUDGET_NAME)
    return ExceptionsRepository(db).build_rule_context(period_code, as_of_date)


#: Dimension seeds from `db.py` lines 90-147. Needed to translate the budget
#: CSV's business codes into the integer ids `commit_budget_replace` expects.
_PERIOD_ID = {f"FY26-P{m:02d}": m for m in range(1, 13)}
_COMPANY_ID = {"IN01": 1, "IN02": 2}
_COST_CENTER_ID = {f"CC-{n}": n for n in
                   (100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 999)}
_COST_CENTER_ID["CC-950"] = 950


def _load_budget(db, repo, path: Path) -> int:
    """Load `budget_fy26.csv` into FactBudget.

    `ImportRepository.commit_budget_replace` takes pre-normalised rows keyed by
    INTEGER dimension ids, and no code path in the repository converts the CSV's
    business codes into those ids. This does that translation so the budget-
    variance rules (EXC-017..EXC-020) are actually measurable; without it
    `FactBudget` is empty and those rules score zero for a wiring reason rather
    than a logic reason.
    """
    if not path.exists():
        return 0
    lines = [
        line for line in path.read_text(encoding="utf-8-sig").splitlines()
        if not line.lstrip().startswith("#")
    ]
    rows = list(csv.DictReader(lines))
    normalised = []
    for i, r in enumerate(rows, start=1):
        period = (r.get("PeriodCode") or "").strip()
        account = (r.get("AccountCode") or "").strip()
        cost_center = (r.get("CostCenterCode") or "").strip()
        entity = (r.get("EntityCode") or "").strip()
        if period not in _PERIOD_ID or not account.isdigit():
            # Unmapped budget line: record it as unmapped rather than guessing
            # an id, so a budget the harness could not load is visible.
            continue
        normalised.append({
            "company_id": _COMPANY_ID.get(entity, 1),
            "account_id": int(account),
            "cost_center_id": _COST_CENTER_ID.get(cost_center),
            "period_id": _PERIOD_ID[period],
            "amount": r.get("BudgetAmount") or "0",
            "currency_code": "INR",
            "source_row_ref": f"budget_row_{i}",
        })
    if not normalised:
        return 0
    return repo.commit_budget_replace(
        budget_version="FY26-Approved", incoming_rows=normalised, batch_id=900001)


# --------------------------------------------------------------------------
# Steps 2-4 - run, join, classify
# --------------------------------------------------------------------------

def _catalog_id(finding: Any) -> str:
    """Catalog rule id for a finding.

    TRAP: `Finding.rule_id` is engine-space. For eight catalog rules the engine
    id differs (engine `evaluate_exc_005` is catalog `EXC-012`), so the catalog
    id must be preferred wherever one is set. See the module docstring.
    """
    return getattr(finding, "catalog_rule_id", None) or finding.rule_id


def run_rules(context) -> List[Any]:
    """Full engine run, default thresholds, every rule enabled (doc 14 §5.2 step 2)."""
    from app.engine.rules.batch import evaluate_all_rules
    return evaluate_all_rules(context)


def measure(
    context,
    raises: Sequence[Dict[str, str]],
    controls: Sequence[Dict[str, str]],
    *,
    as_of: str = DEFAULT_AS_OF,
    period: str = PERIOD_CODE,
    stability_runs: int = 2,
) -> AcceptanceReport:
    """Steps 2-4 plus the §5.3 bars and the §5.4 per-rule table."""
    import time
    from app.engine.rules.batch import catalog_rule_coverage

    report = AcceptanceReport(as_of=as_of, period=period)
    started = time.perf_counter()

    coverage = catalog_rule_coverage()

    first = run_rules(context)
    raised = [(_catalog_id(f), f.subject_key) for f in first]
    raised_set = set(raised)
    report.findings_total = len(first)

    # Step 5 requires the stability bar: two consecutive runs, identical sets.
    stable = True
    stability_detail = "identical"
    if stability_runs >= 2:
        second = run_rules(context)
        second_set = {(_catalog_id(f), f.subject_key) for f in second}
        if second_set != raised_set:
            stable = False
            only1 = sorted(raised_set - second_set)[:5]
            only2 = sorted(second_set - raised_set)[:5]
            stability_detail = f"diverged: only-run1={only1} only-run2={only2}"

    # ---- classify every raise (step 4) -----------------------------------
    raise_pairs = {(r["rule_id"], r["subject_key"]) for r in raises}
    control_pairs = {(r["rule_id"], r["subject_key"]) for r in controls}

    hits = raise_pairs & raised_set
    fired_controls = control_pairs & raised_set
    extras = raised_set - raise_pairs - control_pairs

    report.controls_fired = [
        {"rule_id": r, "subject_key": s,
         "planting_id": next(c["planting_id"] for c in controls
                             if (c["rule_id"], c["subject_key"]) == (r, s)),
         "notes": next(c["notes"] for c in controls
                       if (c["rule_id"], c["subject_key"]) == (r, s))}
        for r, s in sorted(fired_controls)
    ]

    from collections import Counter
    report.extras_by_rule = dict(sorted(Counter(r for r, _ in extras).items()))
    report.extras_total = len(extras)

    report.severity_counts = {
        "expected": _severity_counts(raises),
        "detected": _severity_counts([r for r in raises
                                      if (r["rule_id"], r["subject_key"]) in hits]),
        "missed": _severity_counts([r for r in raises
                                    if (r["rule_id"], r["subject_key"]) not in hits]),
    }

    # ---- per-rule table (doc 14 §5.4) -----------------------------------
    raised_by_rule = Counter(r for r, _ in raised)
    extras_by_rule = report.extras_by_rule
    for rule_id in CATALOG_RULE_IDS:
        row = RuleRow(rule_id=rule_id, evaluator=coverage.get(rule_id, "<NOT WIRED>"))
        row.wired = rule_id in coverage
        row.plantings = [r["planting_id"] for r in raises if r["rule_id"] == rule_id]
        row.detected = [r["planting_id"] for r in raises
                        if r["rule_id"] == rule_id
                        and (r["rule_id"], r["subject_key"]) in raised_set]
        row.missed = [r["planting_id"] for r in raises
                      if r["rule_id"] == rule_id
                      and (r["rule_id"], r["subject_key"]) not in raised_set]
        row.controls = [r["planting_id"] for r in controls if r["rule_id"] == rule_id]
        row.controls_fired = [r["planting_id"] for r in controls
                              if r["rule_id"] == rule_id
                              and (r["rule_id"], r["subject_key"]) in raised_set]
        row.findings_raised = raised_by_rule.get(rule_id, 0)
        row.extras = extras_by_rule.get(rule_id, 0)
        report.rules.append(row)

    report.miss_list = [
        {"planting_id": r["planting_id"], "rule_id": r["rule_id"],
         "severity": r["severity"], "subject_key": r["subject_key"],
         "notes": r["notes"]}
        for r in raises if (r["rule_id"], r["subject_key"]) not in raised_set
    ]

    # ---- the bars (doc 14 §5.3) -----------------------------------------
    high_rows = [r for r in raises if r["severity"] == "High"]
    high_found = sum(1 for r in high_rows
                     if (r["rule_id"], r["subject_key"]) in raised_set)
    over_extras = {r: n for r, n in extras_by_rule.items()
                   if n > BAR_UNEXPLAINED_EXTRAS_PER_RULE}
    zero_cov = [r.rule_id for r in report.rules if r.zero_coverage]
    unwired = [r.rule_id for r in report.rules if not r.wired]

    report.bars = [
        BarResult(
            "Planted-exception recall",
            f">= {BAR_RECALL_MIN_HITS} of {len(raises)} "
            f"(>= 90 % of the 32 raises)",
            f"{len(hits)}/{len(raises)} = {len(hits)/len(raises)*100:.1f} %",
            len(hits) >= BAR_RECALL_MIN_HITS,
            f"{len(report.miss_list)} planted case(s) not detected",
        ),
        BarResult(
            "Control precision",
            f"{BAR_CONTROL_RAISES_MAX} of {len(controls)} controls may raise",
            f"{len(fired_controls)} fired",
            len(fired_controls) <= BAR_CONTROL_RAISES_MAX,
            "; ".join(f"{c['planting_id']} {c['rule_id']}" for c in report.controls_fired),
        ),
        BarResult(
            "High-severity recall",
            f"{BAR_HIGH_SEVERITY_REQUIRED} of {len(high_rows)} High plantings found",
            f"{high_found}/{len(high_rows)}",
            high_found >= BAR_HIGH_SEVERITY_REQUIRED,
            "a missed High is a control failure, not a statistic",
        ),
        BarResult(
            "Extra findings",
            f"a rule with > {BAR_UNEXPLAINED_EXTRAS_PER_RULE} unexplained "
            f"findings is tuned or documented before the gate",
            f"{len(extras)} extra across "
            f"{len(extras_by_rule)} rule(s); over threshold: "
            f"{sorted(over_extras) or 'none'}",
            not over_extras,
            "no false-positive log reference is committed in this repository; "
            "extras are therefore UNEXPLAINED, not justified",
        ),
        BarResult(
            "Stability",
            "two consecutive runs produce identical raise sets",
            "identical" if stable else "DIVERGED",
            stable,
            stability_detail,
        ),
        BarResult(
            "Rule catalog coverage",
            "all 24 catalog rules are wired into the batch composer",
            f"{len(coverage)}/{len(CATALOG_RULE_IDS)} wired",
            not unwired,
            f"unwired: {unwired}" if unwired else "",
        ),
        BarResult(
            "Zero-coverage rules",
            "every rule with a planted case raises at least one finding",
            f"{len(zero_cov)} rule(s) with zero coverage",
            not zero_cov,
            f"zero coverage: {zero_cov}" if zero_cov else "",
        ),
    ]

    report.elapsed_seconds = time.perf_counter() - started
    report.verdict = "PASS" if report.passed else "FAIL"
    return report


def _severity_counts(rows: Sequence[Dict[str, str]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        out[r["severity"]] = out.get(r["severity"], 0) + 1
    return dict(sorted(out.items()))


def attach_corpus_gate(
    report: AcceptanceReport,
    corpus: List[Dict[str, Any]],
    committed_rows: Optional[Dict[str, int]] = None,
) -> None:
    """Fold doc 28 §5.0 entry criterion 4 into the verdict.

    A rejected general-ledger fixture makes the run **BLOCKED**, not FAIL: any
    planted case in that file never reaches `FactActual`, so attributing the miss
    to rule logic would be wrong. This includes a balanced workbook rejected by
    its control-total gate, not just an `IMP-023` imbalance. A rejected
    sub-ledger is a documented divergence: it is named with its failed check and
    any dependent plantings remain visibly unproven; the import policy itself is
    not papered over here.
    """
    report.corpus = corpus
    committed_rows = committed_rows or {}

    for row in corpus:
        if row.get("checksum"):
            report.corpus_checksum[row["file"]] = row["checksum"]

        if "loaded_count" in row:
            row["parsed_loaded_count"] = row["loaded_count"]
            row["loaded_count"] = committed_rows.get(Path(row["file"]).name, 0)

        committable = row.get("committable", row.get("balanced"))
        if committable:
            continue

        name = row["file"]
        # A file with no group in FactActual contributed zero rows: the query
        # groups BY source_file_name, so an absent name means nothing landed.
        landed = committed_rows.get(name, 0)
        landed_txt = f"{landed} of {row.get('rows')} parsed rows landed in FactActual"
        failed = ", ".join(row.get("failed_checks") or []) or "IMP-023"

        if row.get("is_general_ledger"):
            report.blocked_reasons.append(
                f"BLOCKED - doc 28 §5.0 entry criterion 4 ('Sample data corpus "
                f"(250k rows) loaded and validated') is not met for the general "
                f"ledger {name}: source_type={row.get('source_type')}, "
                f"total_debit={row.get('total_debit')}, "
                f"total_credit={row.get('total_credit')}, "
                f"net_imbalance={row.get('net_imbalance')}, "
                f"is_balanced={row.get('balanced')}, "
                f"recorded_status={row.get('recorded_status')}, "
                f"failing check(s)={failed} of {row.get('checks_run')} run, "
                f"data_quality_score={row.get('data_quality_score')}, and "
                f"{landed_txt}. This required general-ledger batch was rejected, "
                f"so its facts and any plantings that depend on it are absent from "
                f"the rule context. The doc 14 §5.3 bars are NOT MEASURED on the "
                f"complete planned corpus. This is a corpus precondition failure, "
                f"not a rule-logic result."
            )
        else:
            report.divergences.append(
                f"Required sub-ledger fixture {name} was rejected "
                f"(net={row.get('net_imbalance')}, failing check(s)={failed}) and "
                f"{landed_txt}. Any planting assigned to this source is unreachable "
                f"until the fixture satisfies DEC-056 / 04 §12; this is reported "
                f"as a corpus divergence, not hidden as rule behavior."
            )


def apply_blocked_state(report: AcceptanceReport) -> None:
    """Mark every bar unmeasured once the corpus precondition has failed.

    The numbers stay in the report for diagnosis, but `measurable=False` means
    no consumer can read them as a §5.3 result. `passed` is forced False as well,
    so no code path can observe a green bar on a run that measured nothing.
    """
    if not report.blocked_reasons:
        return
    for bar in report.bars:
        bar.measurable = False
        bar.passed = False
    report.verdict = "BLOCKED"


def run_acceptance(
    sample_dir: Path = DEFAULT_SAMPLE_DIR,
    *,
    project_dir: Optional[Path] = None,
    period: str = PERIOD_CODE,
    as_of: str = DEFAULT_AS_OF,
    load_actuals: bool = True,
    stability_runs: int = 2,
) -> AcceptanceReport:
    """Run doc 14 §5.2 steps 1-6 end to end and return the report.

    Never raises for a failing bar - the caller decides how to fail. Raises
    `AcceptanceHarnessError` only when the run cannot legitimately measure
    anything (missing answer key, wrong number of plantings).
    """
    owned = None
    if project_dir is None:
        owned = tempfile.mkdtemp(prefix="fpa_acceptance_")
        project_dir = Path(owned)

    raises, controls, other = load_answer_key(sample_dir)
    report = AcceptanceReport(as_of=as_of, period=period)
    report.divergences = validate_answer_key(raises, controls)
    for row in other:
        report.divergences.append(
            f"Answer key row outside P1..P32 and not counted as a planting: "
            f"{row['planting_id']} {row['rule_id']} {row['expected_verdict']} "
            f"(this is the prompt-injection fixture, not one of the 40)."
        )

    corpus = corpus_integrity(sample_dir)
    scope = checksum_scope(sample_dir)
    context = build_acceptance_context(
        project_dir, sample_dir=sample_dir, period_code=period,
        as_of_date=as_of, load_actuals=load_actuals)

    # Measured, not assumed: how many rows each file actually contributed.
    committed_rows: Dict[str, int] = {}
    if load_actuals:
        from app.engine.store.db import DatabaseManager
        committed_rows = measure_committed_rows(DatabaseManager(project_dir))

    measured = measure(context, raises, controls, as_of=as_of, period=period,
                       stability_runs=stability_runs)

    # Preserve ordering: corpus gate, then the measured bars.
    measured.checksum_scope = scope
    measured.divergences = report.divergences
    measured.other_rows = other  # type: ignore[attr-defined]
    attach_corpus_gate(measured, corpus, committed_rows)
    apply_blocked_state(measured)
    if measured.verdict != "BLOCKED":
        measured.verdict = "PASS" if measured.passed else "FAIL"
    if owned:
        measured.project_dir = owned  # type: ignore[attr-defined]
    return measured


# --------------------------------------------------------------------------
# Step 5 - reports
# --------------------------------------------------------------------------

def render_markdown(report: AcceptanceReport) -> str:
    """Human-readable report (doc 14 §5.2 step 5)."""
    L: List[str] = []
    A = L.append
    A("# Planted-exception acceptance report")
    A("")
    A(f"**Verdict: {report.verdict}**")
    A("")
    if report.verdict == "BLOCKED":
        A("> **The doc 14 §5.3 bars were NOT MEASURED.** The corpus precondition "
          "(doc 28 §5.0 entry criterion 4) is not met, so no facts exist for the "
          "rules to fire on. The figures in the per-rule table below are printed "
          "for diagnosis only and are **not** a §5.3 result. This run is neither a "
          "pass nor a rule-logic failure - it is BLOCKED.")
        A("")
    A(f"- Period: `{report.period}`  |  as_of (injected, no clock): `{report.as_of}`")
    A(f"- Findings raised: {report.findings_total}  |  elapsed: {report.elapsed_seconds:.1f}s")
    A(f"- Measurable: {'yes' if report.measurable else 'NO - see BLOCKED REASONS'}")
    A(f"- Harness: doc 14 §5.2, run by `scripts/acceptance`")
    A("")

    if report.blocked_reasons:
        A("## BLOCKED REASONS (corpus precondition)")
        A("")
        for b in report.blocked_reasons:
            A(f"- {b}")
        A("")

    if report.hard_failures:
        A("## HARD FAILURES (prerequisites)")
        A("")
        for f in report.hard_failures:
            A(f"- {f}")
        A("")

    A("## Bars (doc 14 §5.3)")
    A("")
    if not report.measurable:
        A("_Not measured - corpus precondition failed. See BLOCKED REASONS above._")
        A("")
    A("| Bar | Requirement | Measured | Result |")
    A("|---|---|---|---|")
    for b in report.bars:
        if not b.measurable:
            result = "_NOT MEASURED_"
        else:
            result = "PASS" if b.passed else "**FAIL**"
        A(f"| {b.name} | {b.requirement} | "
          f"{b.measured if b.measurable else 'NOT MEASURED'} | {result} |")
    A("")

    # One heading only: an earlier version emitted this section twice, once
    # unconditionally and once conditionally, which read as a duplicated table
    # in every report.
    if not report.measurable:
        A("## Per-rule recall (doc 14 §5.4) - DIAGNOSTIC ONLY, NOT A BAR RESULT")
        A("")
    else:
        A("## Per-rule recall (doc 14 §5.4)")
        A("")
    A("| Rule | Evaluator | Plantings | Detected | Recall | Controls | Controls fired | Findings | Extras |")
    A("|---|---|---|---|---|---|---|---|---|")
    for r in report.rules:
        recall = "n/a" if r.recall_pct is None else f"{r.recall_pct} %"
        flag = " **ZERO-COVERAGE**" if r.zero_coverage else ""
        A(f"| {r.rule_id}{flag} | `{r.evaluator}` | {len(r.plantings)} | "
          f"{len(r.detected)} | {recall} | {len(r.controls)} | "
          f"{len(r.controls_fired)} | {r.findings_raised} | {r.extras} |")
    A("")

    A("## Controls result (must be 0 of 8)")
    A("")
    if not report.controls_fired:
        A("No control raised.")
    else:
        A("| Planting | Rule | Subject key | Notes |")
        A("|---|---|---|---|")
        for c in report.controls_fired:
            A(f"| {c['planting_id']} | {c['rule_id']} | `{c['subject_key']}` | {c['notes']} |")
    A("")

    A("## Miss list")
    A("")
    if not report.miss_list:
        A("None.")
    else:
        A("| Planting | Rule | Severity | Subject key | Notes |")
        A("|---|---|---|---|---|")
        for m in report.miss_list:
            A(f"| {m['planting_id']} | {m['rule_id']} | {m['severity']} | "
              f"`{m['subject_key']}` | {m['notes']} |")
    A("")

    A("## Extra findings (false-positive log reference)")
    A("")
    if not report.extras_by_rule:
        A("None.")
    else:
        A(f"{report.extras_total} extra finding(s) by rule: "
          f"`{report.extras_by_rule}`")
        A("")
        A("No false-positive log is committed in this repository, so every extra "
          "is UNEXPLAINED, not justified.")
    A("")

    A("## Corpus integrity (doc 28 §5.0 criterion 4)")
    A("")
    A("| File | Source type | Gate | Recorded | Rows | Loaded | Debit | Credit | Net | Failed checks | DQ score |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in report.corpus:
        A(f"| {c['file']} | {c.get('source_type', '-')} | {c.get('balance_gate', '-')} | "
          f"{c.get('recorded_status', c.get('status', '-'))} | {c.get('rows', '-')} | "
          f"{c.get('loaded_count', '-')} | "
          f"{c.get('total_debit', '-')} | {c.get('total_credit', '-')} | "
          f"{c.get('net_imbalance', '-')} | "
          f"{', '.join(c.get('failed_checks') or []) or 'none'} | "
          f"{c.get('data_quality_score', '-')} |")
    A("")
    A("`DQ score` is computed by `calculate_quality_score()` (`DEF-021`); it is no "
      "longer the literal 100 that every batch used to report.")
    A("")

    if report.divergences:
        A("## Divergences and stated assumptions")
        A("")
        for d in report.divergences:
            A(f"- {d}")
        A("")

    A("## Checksum scope (doc 14 §5.2 step 1, amended 2026-10-06)")
    A("")
    if report.checksum_scope:
        formats = ", ".join(
            f"`{suffix}`" for suffix in report.checksum_scope.get("fingerprinted_suffixes", [])
        )
        A(f"- Fingerprinted: **{report.checksum_scope.get('fingerprinted_count', 0)} "
          f"data artefact(s)** across {formats}.")
        A("  SHA-256 values, keyed by relative path, are included in "
          "`acceptance_report.json` under `checksum_scope.sha256`.")
        A(f"- Excluded: **{report.checksum_scope.get('excluded_count', 0)} "
          "recognized data artefact(s)**.")
        A(f"  - {report.checksum_scope.get('note', '')}")
        for suffix, why in (report.checksum_scope.get("exclusion_reason") or {}).items():
            A(f"  - `{suffix}`: {why}.")
        if report.checksum_scope.get("excluded_count", 0):
            A("  Exclusions are listed and justified; they are not silently "
              "treated as checksummed.")
    A("")

    A("## Stated assumptions")
    A("")
    A(f"- **Run date.** Doc 14 §5.2 step 2 says only \"with default thresholds, "
      f"every rule enabled\" and names no run date. The answer key's P11 note "
      f"(\"Posting on 30-Nov-2026 is 18 days ahead of run date\") implies "
      f"`as_of={DEFAULT_AS_OF}`, which is used. No clock is read (doc 06 line 195).")
    A("- **Generator checksum.** The report records the actual SHA-256 of each "
      "recognized corpus data artifact and does not assert against a committed "
      "golden digest, because no canonical manifest is committed. The generator "
      "reproducibility test is separate; a recorded fingerprint is not a claim "
      "that this acceptance run regenerated the data.")
    A("- **Seed.** Doc 14 §5.2 step 1 was amended 2026-10-03 from `--seed "
      "20260101` to `--seed 42`. The committed corpus was generated at seed 42 "
      "and audit New-06 reproduced it byte-exactly; the previously documented "
      "seed was never used.")
    A("- **CLI name.** Doc 14 §5.2 says \"run by `scripts/acceptance`\". This "
      "repository names scripts with a `.py` suffix (`build.py`, `check.py`), so "
      "the entry point is `scripts/acceptance.py`.")
    A("")
    return "\n".join(L)


def write_reports(report: AcceptanceReport, out_dir: Path) -> Tuple[Path, Path]:
    """Write `acceptance_report.json` and `acceptance_report.md` (step 5)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "acceptance_report.json"
    md_path = out_dir / "acceptance_report.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path