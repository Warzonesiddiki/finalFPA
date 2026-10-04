"""TST-PRF-07 - full rule-run performance baseline (NFR-007).

Governed by 14_TESTING_QA_PLAN.md:

| `NFR-007` | Full rule run over 250k rows <= **60 s** | Timed `fpa exceptions --run` | 250k-row project | `TST-PRF-07` |

Reference machine per doc 14 line 100: 4-core laptop-class CPU, 16 GB RAM, SSD,
Windows 11. Doc 14 line 424 notes baselines live in tests/perf/baselines/<nfr>.json
and are committed, and that re-baselining without cause is a defect - so this test
asserts the NFR budget, not a machine-specific number that would flake on other
hardware.

SCOPE: EXC-001..EXC-024 via the BATCH evaluators, DEDUPLICATED.

`BATCH_01_08_EVALUATORS` internally carries catalog EXC-009, EXC-012 and EXC-015 as
`evaluate_exc_004` / `evaluate_exc_005` / `evaluate_exc_006`. `BATCH_09_16_EVALUATORS`
re-exposes those same three rules under catalog ids. Naively concatenating both
batches therefore evaluates three rules twice. `rules_17_24` deliberately excludes
catalog EXC-017 / EXC-018 for exactly this reason (see the comment above
`BATCH_17_24_EVALUATORS`: including them "would double-raise findings for plantings
P17 / P18"). This module composes the de-duplicated set explicitly and
`test_rule_batch_has_no_double_invocation` locks that in.

Marked `perf` so it stays out of the default fast suite; run with:

    pytest -m perf tests/perf/test_rules_perf.py

Read-only: this module never mutates rule logic or sample data.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from app.engine.imports import parse_csv_transactions
from app.engine.rules.batch import (
    build_full_rule_batch,
    catalog_rule_coverage,
)
from app.engine.rules.rules_01_08 import RuleContext

# NFR-007 budget, quoted from 14_TESTING_QA_PLAN.md line 85.
NFR_007_BUDGET_SECONDS = 60.0

# Doc 14 line 100: the scale fixture is the 250k-row project.
SCALE_CSV = Path("sample-data/d365_gl_actuals.csv")
MIN_EXPECTED_ROWS = 200_000

# The batch composer lives in the engine (app/engine/rules/batch.py) so the CLI,
# the API and this perf harness all measure the same composition. Re-exported here
# under the historical name so existing references keep working.
build_deduplicated_batch = build_full_rule_batch


def peak_working_set_mb() -> float:
    """Peak working set of this process in MB (Windows PROCESS_MEMORY_COUNTERS)."""
    import ctypes
    from ctypes import wintypes

    class PMC(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    psapi = ctypes.windll.psapi
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(PMC),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    ok = psapi.GetProcessMemoryInfo(
        ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb
    )
    return pmc.PeakWorkingSetSize / (1024 * 1024) if ok else 0.0


def _load_context() -> Tuple[RuleContext, int, float]:
    """Parse the scale fixture and build the rule context. Returns (ctx, rows, parse_s)."""
    t0 = time.perf_counter()
    _batch, transactions = parse_csv_transactions(SCALE_CSV)
    parse_s = time.perf_counter() - t0
    # period_id FY26-P09; as_of intentionally left unset so it resolves from the
    # period under review (doc 05 CALC-002) rather than any system clock.
    ctx = RuleContext(transactions=transactions, period_id="FY26-P09")
    return ctx, len(transactions), parse_s


@pytest.mark.perf
def test_rule_batch_has_no_double_invocation():
    """Guard the composition itself: every evaluator appears exactly once."""
    batch = build_deduplicated_batch()
    names = [ev.__name__ for ev in batch]
    assert len(names) == len(set(names)), f"duplicate evaluator in batch: {names}"

    # EXC-009 / EXC-012 / EXC-015 must be covered by the 01-08 batch only.
    for excluded in ("evaluate_exc_009", "evaluate_exc_012", "evaluate_exc_015"):
        assert excluded not in names

    # Five catalog-native evaluators + 8 legacy + 5 unique (09-16) + 6 (17-24).
    assert len(batch) == 24

    # Every catalog ID must map to a real, uniquely wired evaluator.
    coverage = catalog_rule_coverage()
    missing = [f"EXC-{i:03d}" for i in range(1, 25) if f"EXC-{i:03d}" not in coverage]
    assert len(coverage) == 24
    assert not missing


@pytest.mark.perf
def test_full_rule_run_250k_within_nfr007():
    """NFR-007: full rule run over the 250k-row project completes within 60 s.

    Timed around the rule evaluation only. Parsing the fixture is NFR-002
    territory (covered by tests/perf/test_import_benchmark.py) and is excluded here
    so this test measures exactly what doc 14 line 85 describes: "Full rule run".
    """
    if not SCALE_CSV.exists():
        pytest.skip(f"Scale benchmark fixture missing: {SCALE_CSV}")

    ctx, rows, parse_s = _load_context()
    assert rows >= MIN_EXPECTED_ROWS, (
        f"TST-PRF-07 expects a >= {MIN_EXPECTED_ROWS:,}-row fixture, got {rows:,}. "
        "Regenerate with: python sample-data/generate_sample_data.py --scale 250000"
    )

    batch = build_deduplicated_batch()
    findings: List[Any] = []
    per_rule: Dict[str, float] = {}

    t0 = time.perf_counter()
    for evaluator in batch:
        t_rule = time.perf_counter()
        findings.extend(evaluator(ctx))
        per_rule[evaluator.__name__] = time.perf_counter() - t_rule
    elapsed = time.perf_counter() - t0

    peak_mb = peak_working_set_mb()
    breakdown = ", ".join(f"{k}={v:.2f}s" for k, v in per_rule.items())

    print(
        f"\n[TST-PRF-07] rows={rows:,} | parse={parse_s:.2f}s (excluded) | "
        f"rule_run={elapsed:.2f}s | budget={NFR_007_BUDGET_SECONDS:.1f}s | "
        f"rows/s={rows / elapsed:,.0f} | peak={peak_mb:.1f} MB | "
        f"findings={len(findings)} | evaluators={len(batch)}\n"
        f"           breakdown: {breakdown}"
    )

    assert elapsed <= NFR_007_BUDGET_SECONDS, (
        f"NFR-007 violation: full rule run over {rows:,} rows took {elapsed:.2f}s "
        f"(budget <= {NFR_007_BUDGET_SECONDS:.1f}s). Breakdown: {breakdown}"
    )


@pytest.mark.perf
def test_rule_run_peak_memory_within_nfr005_limit():
    """NFR-005 peak-memory sanity check during the 250k-row rule run.

    Doc 14 caps peak working set at 1.5 GB for the 250k-row import. The parsed
    transaction objects dominate, and they are retained for the duration of the run,
    so this bound applies here too.
    """
    if not SCALE_CSV.exists():
        pytest.skip(f"Scale benchmark fixture missing: {SCALE_CSV}")

    ctx, rows, _parse_s = _load_context()
    for evaluator in build_deduplicated_batch():
        evaluator(ctx)

    peak_mb = peak_working_set_mb()
    print(f"\n[TST-PRF-07 memory] rows={rows:,} | peak={peak_mb:.1f} MB")

    if peak_mb > 0:
        assert peak_mb <= 1536.0, (
            f"NFR-005 violation: peak memory {peak_mb:.1f} MB exceeded the 1.5 GB limit"
        )