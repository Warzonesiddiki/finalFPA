"""Fault injection for the planted-exception corpus (CORPUS-03).

A rule that fires on a fixture is not the same as a rule that fires because it is
right. This command corrupts the corpus in NAMED, DOCUMENTED ways and asserts
that each corruption costs exactly the detection it was predicted to cost. If a
fault leaves the acceptance result unchanged, the rule it targets was never
load-bearing on this fixture - which is a finding about the corpus, not a pass.

Acceptance (doc 14 §5.2 / task CORPUS-03): for every fault, print

    the injected defect name, the expected detection, and the exit code

and exit non-zero if any fault did NOT behave as predicted.

The real ``sample-data/`` is never written to. Every fault runs against a
throwaway copy in a temporary directory.
"""

from __future__ import annotations

import argparse
import csv
import io
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.engine.rules import acceptance as acc  # noqa: E402

ZERO = Decimal("0.00")


# ---------------------------------------------------------------------------
# Corpus editing helpers
# ---------------------------------------------------------------------------


def _split(path: Path) -> tuple[list[str], list[str], str]:
    """Split a corpus CSV into (preamble lines, body lines, line terminator).

    The preamble keeps the watermark comment EXACTLY as written - rewriting it
    with a different dash would be a corruption of its own, and the fault under
    test has to be the only thing that changed.
    """
    raw = path.read_text(encoding="utf-8")
    terminator = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()
    body_start = next((i for i, line in enumerate(lines) if not line.startswith("#")), 0)
    return lines[:body_start], lines[body_start:], terminator


def _header_index(body: list[str]) -> int:
    return next(
        i
        for i, line in enumerate(body)
        if line.startswith("Voucher,") or line.startswith("PeriodCode,")
    )


def _edit_rows(path: Path, mutate: Callable[[list[str], list[list[str]]], None]) -> int:
    """Apply `mutate` to the parsed body, writing back with the original shape.

    Returns the number of body rows. Only rows the caller actually changes are
    re-serialised; everything else - preamble, ordering, line terminator - is
    preserved, so the injected fault is the sole difference from the clean corpus.
    """
    preamble, body, terminator = _split(path)
    head = _header_index(body)
    parsed = [next(csv.reader([line])) for line in body]
    mutate(parsed[head], parsed[head + 1 :])
    out = list(preamble)
    for row in parsed:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="").writerow(row)
        out.append(buffer.getvalue())
    path.write_text(terminator.join(out) + terminator, encoding="utf-8")
    return len(parsed) - head - 1


def _set(header: list[str], rows: list[list[str]], name: str, index: int, value: str) -> None:
    rows[index][header.index(name)] = value


# ---------------------------------------------------------------------------
# The fault registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Fault:
    """One named corruption and the detection it is predicted to destroy.

    ``lost_plantings`` are the answer-key rows that must stop being recalled
    once the fault is applied. ``why`` states the mechanism, so a failure is
    interpretable rather than merely red.
    """

    name: str
    summary: str
    why: str
    lost_plantings: tuple[str, ...]
    lost_controls: tuple[str, ...]
    apply: Callable[[Path], None]


def _budget_amount(
    sample: Path, period: str, entity: str, cost_centre: str, account: str, amount: str
) -> None:
    """Rewrite one budget line, asserting exactly one row matched."""
    path = sample / "budget_fy26.csv"

    def mutate(header: list[str], rows: list[list[str]]) -> None:
        matches = [
            i
            for i, row in enumerate(rows)
            if row[header.index("PeriodCode")] == period
            and row[header.index("EntityCode")] == entity
            and row[header.index("CostCenterCode")] == cost_centre
            and row[header.index("AccountCode")] == account
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"budget_fy26.csv: expected exactly 1 row for "
                f"{period}/{entity}/{cost_centre}/{account}, found {len(matches)}"
            )
        _set(header, rows, "BudgetAmount", matches[0], amount)

    _edit_rows(path, mutate)


def _gl_edit(
    sample: Path,
    vouchers: tuple[str, ...],
    field: str,
    new_value: str,
    expected_count: int | None = None,
) -> None:
    """Set `field` on every row of the named vouchers, asserting the row count."""
    path = sample / "d365_gl_actuals.csv"
    wanted = set(vouchers)

    def mutate(header: list[str], rows: list[list[str]]) -> None:
        hits = 0
        for i, row in enumerate(rows):
            if row[header.index("Voucher")] in wanted:
                _set(header, rows, field, i, new_value)
                hits += 1
        if expected_count is not None and hits != expected_count:
            raise RuntimeError(
                f"d365_gl_actuals.csv: expected {expected_count} row(s) for "
                f"{sorted(wanted)}, found {hits}"
            )

    _edit_rows(path, mutate)


def _gl_drop_vouchers(sample: Path, voucher: str) -> None:
    path = sample / "d365_gl_actuals.csv"

    def mutate(header: list[str], rows: list[list[str]]) -> None:
        keep = [i for i, row in enumerate(rows) if row[header.index("Voucher")] != voucher]
        if len(keep) == len(rows):
            raise RuntimeError(f"VCH {voucher} not found in the corpus")
        rows[:] = [rows[i] for i in keep]

    _edit_rows(path, mutate)


def fault_p18_below_absolute_floor() -> Fault:
    """Move P18's variance under the ₹500,000 materiality floor."""
    return Fault(
        name="p18-below-absolute-floor",
        summary="budget_fy26.csv FY26-P09/IN01/CC-100/5200 -> 10700000.00 "
        "(actual 10540000.00, so var +160000.00)",
        why="EXC-018 is a mandatory AND-test: |var| >= max(500000, 2% x budget) "
        "AND |var%| >= 5%. 160000.00 clears the 5% leg at 1.50% but fails the "
        "500000 absolute floor, so EXC-018 must stop raising "
        "IN01|5200|CC-100. If it keeps raising, the floor is not load-bearing.",
        lost_plantings=("P18",),
        lost_controls=(),
        apply=lambda sample: _budget_amount(
            sample, "FY26-P09", "IN01", "CC-100", "5200", "10700000.00"
        ),
    )


def fault_p30_over_percentage_leg() -> Fault:
    """Widen P30's budget so its control variance clears the 5% leg."""
    return Fault(
        name="p30-control-over-percentage-leg",
        summary="budget_fy26.csv FY26-P09/IN01/CC-110/5200 -> 38000000.00 "
        "(actual 40900000.00, so var +2900000.00 = +7.63%)",
        why="P30 is the F13c precision control: a 900000.00 variance on a "
        "40000000.00 budget is +2.25%, below the 5% leg of the AND-test, so "
        "EXC-018 must stay silent. Re-budgeting to 38000000.00 makes the "
        "variance 2900000.00 (+7.63%) and the amount clears the "
        "max(500000, 2% x 38000000) floor of 760000.00, so the control MUST "
        "start firing. A control that cannot be made to fail is not a control.",
        lost_plantings=(),
        lost_controls=("P30",),
        apply=lambda sample: _budget_amount(
            sample, "FY26-P09", "IN01", "CC-110", "5200", "38000000.00"
        ),
    )


def fault_p29_control_over_floor() -> Fault:
    """Deepen P29's variance so its control clears the absolute floor."""
    return Fault(
        name="p29-control-over-absolute-floor",
        summary="budget_fy26.csv FY26-P09/IN01/CC-105/5200 -> 6600000.00 "
        "(actual 7420000.00, so var +820000.00 = +12.42%)",
        why="P29 is the F13b precision control: a 420000.00 variance is +6.00%, "
        "past the 5% leg but UNDER the 500000 absolute floor, so EXC-018 "
        "must stay silent. Re-budgeting to 6600000.00 makes the variance "
        "820000.00 (+12.42%), clearing both legs, so the control MUST start "
        "firing. This is the mirror of the P18 fault and proves the floor "
        "and the percentage are separate gates, not one.",
        lost_plantings=(),
        lost_controls=("P29",),
        apply=lambda sample: _budget_amount(
            sample, "FY26-P09", "IN01", "CC-105", "5200", "6600000.00"
        ),
    )


def fault_p8_duplicate_line_floor() -> Fault:
    """Raise the duplicate-line floor above P8's amount with a budget change.

    Deliberately a BUDGET edit, not a GL edit. P8's two vouchers are single-sided
    (they are part of the planted residual the FIX legs balance at month level),
    so editing their amount unbalances the whole file, the batch is rejected, and
    the run goes BLOCKED - which loses every detection at once and would make any
    assertion pass. Faults that touch transaction amounts must be
    balance-neutral; this one is.
    """
    return Fault(
        name="p8-duplicate-line-floor-above-amount",
        summary="budget_fy26.csv FY26-P09/IN01/CC-110/5300 -> 30000000.00 "
        "(account budget 12 x 30000000, so EXC-008's min_amount "
        "becomes 7200000.00 against P8's 500000.00 line)",
        why="DEC-057 plants P8 at exactly 500000.00 because that is EXC-008's "
        "absolute floor, and EXC-008's threshold is max(500000, 2% x the "
        "account's annual budget). On the clean corpus account 5300's budget "
        "keeps that threshold at 500000.00 and P8 fires. Raising the budget "
        "must lift the threshold above 500000.00 so EXC-008 stops raising "
        "IN01|5300|500000.00|2026-09-22|CC-110 - proving the plant passes on "
        "the documented floor and not on some other mechanism.",
        lost_plantings=("P8",),
        lost_controls=(),
        apply=lambda sample: _budget_amount(
            sample, "FY26-P09", "IN01", "CC-110", "5300", "30000000.00"
        ),
    )


def fault_p21_drop_dual_voucher() -> Fault:
    """Delete P21's dual-approval voucher entirely."""
    return Fault(
        name="p21-drop-dual-approval-voucher",
        summary="d365_gl_actuals.csv: delete voucher VCH-2026-0925-003 (both legs)",
        why="P21's second row is a 2751913.00 voucher crossing the 2500000 dual "
        "approval threshold. With the voucher gone there is nothing above "
        "the dual threshold on that key, so EXC-021 must stop raising "
        "IN01|VCH-2026-0925-003|dual and that answer-key row must be missed.",
        lost_plantings=("P21",),
        lost_controls=(),
        apply=lambda sample: _gl_drop_vouchers(sample, "VCH-2026-0925-003"),
    )


def fault_p6_budget_the_entity() -> Fault:
    """Give IN02 a budget line, removing the reason P6 exists."""
    return Fault(
        name="p6-budget-the-unbudgeted-entity",
        summary="budget_fy26.csv: add FY26-P09/IN02/CC-140/5000 = 840000.00",
        why="P6 is 'actuals without a budget'. IN02 has 840000.00 of year-to-date "
        "actuals on account 5000 and no FY26 budget line at all. Budgeting "
        "exactly what it spent must make EXC-006 stop raising "
        "entity_account|IN02|5000 - proving the rule reads the budget and not "
        "merely the spend. If it still raises, EXC-006 is measuring traffic "
        "volume rather than a missing budget.",
        lost_plantings=("P6",),
        lost_controls=(),
        apply=lambda sample: _budget_amount(
            sample, "FY26-P09", "IN02", "CC-140", "5000", "840000.00"
        ),
    )


FAULTS: tuple[Fault, ...] = (
    fault_p18_below_absolute_floor(),
    fault_p8_duplicate_line_floor(),
    fault_p21_drop_dual_voucher(),
    fault_p6_budget_the_entity(),
    fault_p29_control_over_floor(),
    fault_p30_over_percentage_leg(),
)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _safe(text: str) -> str:
    """Keep the rupee sign out of a cp1252 console."""
    return text.encode("ascii", "replace").decode("ascii")


def run_corpus(sample_dir: Path, project_dir: Path):
    return acc.run_acceptance(sample_dir=sample_dir, project_dir=project_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inject named corpus faults and assert the tool catches each."
    )
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=REPO_ROOT / "sample-data",
        help="Clean corpus to copy faults from (never written to)",
    )
    parser.add_argument(
        "--fault",
        action="append",
        default=None,
        help="Run only this fault (repeatable); default is all",
    )
    parser.add_argument("--period", default=acc.PERIOD_CODE)
    parser.add_argument("--as-of", default=acc.DEFAULT_AS_OF)
    parser.add_argument(
        "--json", type=Path, default=None, help="Also write the result table as JSON"
    )
    args = parser.parse_args(argv)

    selected = tuple(FAULTS)
    if args.fault:
        wanted = set(args.fault)
        unknown = wanted - {f.name for f in FAULTS}
        if unknown:
            parser.error(f"unknown fault(s): {sorted(unknown)}")
        selected = tuple(f for f in FAULTS if f.name in wanted)

    print("Fault injection (CORPUS-03)")
    print(f"  clean corpus : {args.sample_dir}")
    print(f"  period {args.period}  as_of {args.as_of}  ({len(selected)} fault(s))")
    print("  the real corpus is copied per fault and never written to\n")

    rows = []
    failures = 0

    _clean_holder: list = []

    def flush_json() -> None:
        """Persist after EVERY fault, not once at the end.

        A full six-fault run takes several minutes. Writing the evidence only on
        success means an interrupted run produces nothing at all, which is the
        opposite of what a gate is for.
        """
        if args.json is None:
            return
        import json

        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "baseline_verdict": clean.verdict,
                    "baseline_findings": clean.findings_total,
                    "complete": False,
                    "faults": rows,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    with tempfile.TemporaryDirectory(prefix="fpa_fault_") as workspace:
        base = Path(workspace)
        clean_project = base / "clean_project"
        clean = run_corpus(args.sample_dir, clean_project)
        clean_recall = {(r["planting_id"], r["rule_id"]) for r in clean.miss_list}
        print(
            f"  BASELINE on the clean corpus: {clean.findings_total} findings, "
            f"{len(clean.miss_list)} misses, verdict {clean.verdict}",
            flush=True,
        )

        for fault in selected:
            sample = base / f"corpus_{fault.name}"
            project = base / f"project_{fault.name}"
            shutil.copytree(args.sample_dir, sample)
            fault.apply(sample)
            report = run_corpus(sample, project)
            misses = {(r["planting_id"], r["rule_id"]) for r in report.miss_list}

            # A fault "caught" the rule if the detections it targeted are gone
            # from the recalled set (a planting moved into the miss list).
            newly_missed = sorted({(p, r) for p, r in misses if (p, r) not in clean_recall})

            # A BLOCKED run loses EVERY detection at once, so it would satisfy
            # any "this detection must disappear" assertion while proving
            # nothing. An unusable run is a hard failure, never a pass - and it
            # almost always means the fault unbalanced the file rather than
            # testing the rule it claimed to test.
            if report.verdict == "BLOCKED" or not report.measurable:
                verdict = "INVALID"
                failures += 1
                print(f"\n  [INVALID] {fault.name}")
                print(f"      injected   : {fault.summary}")
                print(
                    "      why        : the run went BLOCKED, so it lost every "
                    "detection for the wrong reason. This fault is not "
                    "measuring the rule it claims to measure."
                )
                for reason in report.blocked_reasons:
                    print(f"      blocked    : {_safe(reason)[:200]}")
                rows.append(
                    {
                        "fault": fault.name,
                        "injected": fault.summary,
                        "expected": "a measurable run",
                        "verdict": verdict,
                        "exit_code": 1,
                        "findings_before": clean.findings_total,
                        "findings_after": report.findings_total,
                        "misses_before": len(clean.miss_list),
                        "misses_after": len(report.miss_list),
                        "newly_missed": [],
                        "blocked_reasons": report.blocked_reasons,
                    }
                )
                flush_json()
                continue

            if fault.lost_plantings:
                expected = set(fault.lost_plantings)
                actual = {p for p, _ in newly_missed}
                caught = expected <= actual
                expectation = f"{', '.join(sorted(expected))} stops being recalled"
            else:
                # A control fault: the named precision control must start
                # FIRING. A control that cannot be made to fail is not a control.
                fired = {c["planting_id"] for c in report.controls_fired}
                expected = set(fault.lost_controls)
                caught = bool(expected & fired)
                expectation = f"control {', '.join(sorted(expected))} starts firing"

            if caught:
                verdict = "CAUGHT"
            else:
                verdict = "MISSED"
                failures += 1

            print(f"\n  [{verdict}] {fault.name}")
            print(f"      injected   : {fault.summary}")
            print(f"      mechanism  : {_safe(fault.why)}")
            print(f"      expected   : {expectation}")
            print(
                f"      observed   : findings {clean.findings_total} -> "
                f"{report.findings_total}; misses {len(clean.miss_list)} -> "
                f"{len(report.miss_list)}; verdict {clean.verdict} -> "
                f"{report.verdict}"
            )
            if newly_missed:
                print(f"      newly missed: {', '.join(f'{p}/{r}' for p, r in newly_missed)}")
            if report.controls_fired:
                print(
                    f"      controls fired: "
                    f"{', '.join(c['planting_id'] + '/' + c['rule_id'] for c in report.controls_fired)}"
                )

            rows.append(
                {
                    "fault": fault.name,
                    "injected": fault.summary,
                    "expected": expectation,
                    "verdict": verdict,
                    "exit_code": 0 if caught else 1,
                    "findings_before": clean.findings_total,
                    "findings_after": report.findings_total,
                    "misses_before": len(clean.miss_list),
                    "misses_after": len(report.miss_list),
                    "newly_missed": [f"{p}/{r}" for p, r in newly_missed],
                    "blocked_reasons": [],
                }
            )
            flush_json()

    print("\n" + "=" * 88)
    print(f"{'FAULT':38} {'EXPECTED DETECTION':36} {'EXIT':>5}")
    print("-" * 88)
    for row in rows:
        print(f"{row['fault']:38} {row['expected']:36} {row['exit_code']:>5}")
    print("=" * 88)
    caught = sum(1 for r in rows if r["verdict"] == "CAUGHT")
    invalid = sum(1 for r in rows if r["verdict"] == "INVALID")
    print(
        f"{caught}/{len(rows)} faults behaved as predicted"
        + (f" ({invalid} unusable run(s))" if invalid else "")
    )

    if args.json is not None:
        import json

        args.json.write_text(
            json.dumps(
                {
                    "baseline_verdict": clean.verdict,
                    "baseline_findings": clean.findings_total,
                    "complete": True,
                    "faults": rows,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"wrote {args.json}")

    if failures:
        if invalid:
            print(
                f"\nFAIL: {invalid} fault run(s) were unusable (BLOCKED). A fault "
                f"that unbalances the corpus is not testing a rule - it is "
                f"testing the loader."
            )
        print(
            f"{failures} fault(s) did not produce the predicted detection. "
            f"Where a raise was expected to disappear and did not, the rule it "
            f"targets is not load-bearing on this corpus."
        )
        return 1
    print("\nPASS: every injected fault cost exactly the detection it was predicted to cost.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
