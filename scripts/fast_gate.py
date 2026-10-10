#!/usr/bin/env python3
"""Unified Fast Quality Gate (ENG-06).

One single command that runs on every change:
1. Unit test suite (fast unit tests, excluding slow perf/acceptance)
2. The R12 engine duplication guard (tests/unit/test_engine_common.py)
3. License & provenance gate (scripts/license_gate.py)
4. Documentation integrity check (scripts/check_doc_integrity.py)
5. Continuity layer verification (scripts/memory.py verify)

Fails loudly with non-zero exit code if any gate step fails.
No new runtime dependencies, no suppressed rules.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent


class GateStep(NamedTuple):
    name: str
    command: list[str]


GATE_STEPS: list[GateStep] = [
    GateStep(
        "Unit Tests & R12 Guard",
        [sys.executable, "-m", "pytest", "tests/unit", "-m", "not perf", "-q", "-o", "addopts="],
    ),
    GateStep(
        "License & Provenance Gate", [sys.executable, str(ROOT / "scripts" / "license_gate.py")]
    ),
    GateStep(
        "Documentation Integrity Check",
        [sys.executable, str(ROOT / "scripts" / "check_doc_integrity.py")],
    ),
    GateStep(
        "Continuity Memory Verification",
        [sys.executable, str(ROOT / "scripts" / "memory.py"), "verify"],
    ),
]


def run_fast_gate() -> int:
    print("=== FP&A Copilot Fast Gate (ENG-06) ===")
    total_start = time.perf_counter()

    for idx, step in enumerate(GATE_STEPS, start=1):
        print(f"\n--> [{idx}/{len(GATE_STEPS)}] Running: {step.name}...")
        step_start = time.perf_counter()
        res = subprocess.run(step.command, cwd=str(ROOT))
        elapsed = time.perf_counter() - step_start

        if res.returncode != 0:
            print(
                f"\n❌ FAILED: {step.name} exited with status {res.returncode} ({elapsed:.2f}s)",
                file=sys.stderr,
            )
            return res.returncode
        print(f"    ✓ {step.name} passed in {elapsed:.2f}s")

    total_elapsed = time.perf_counter() - total_start
    print(f"\n=== All {len(GATE_STEPS)} Fast Gate Steps PASSED ({total_elapsed:.2f}s) ===")
    return 0


if __name__ == "__main__":
    sys.exit(run_fast_gate())
