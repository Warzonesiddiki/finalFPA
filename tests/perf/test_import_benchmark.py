"""Performance and scale benchmark tests for data import.

Governed by 14_TESTING_QA_PLAN.md:
- NFR-002 (TST-PRF-02): 250k-row import <= 60s
- NFR-005 (TST-PRF-05): Peak memory <= 1.5 GB during 250k-row import
"""

import sys
import time
from pathlib import Path

import pytest

from app.engine.imports import parse_csv_transactions, prescan_file


def get_peak_working_set_bytes() -> int:
    """Return peak working set memory in bytes for current process."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
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

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        h_proc = kernel32.GetCurrentProcess()
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if psapi.GetProcessMemoryInfo(h_proc, ctypes.byref(pmc), pmc.cb):
            return int(pmc.PeakWorkingSetSize)

    return 0


@pytest.mark.perf
def test_import_250k_benchmark():
    """Benchmark prescan and parse on 250,000-row D365 GL actuals dataset.

    Asserts:
    - NFR-002: Total import time (prescan + parse) <= 60.0 seconds
    - NFR-005: Peak working set memory <= 1.5 GB (1536 MB)
    - Data integrity: row count reconciliation (loaded + quarantined + rejected == total)
    """
    sample_path = Path("sample-data/d365_gl_actuals.csv")
    if not sample_path.exists():
        pytest.skip(f"Scale benchmark fixture missing: {sample_path}")

    # 1. Prescan benchmark
    t_start = time.perf_counter()
    prescan_result = prescan_file(sample_path)
    t_prescan = time.perf_counter()
    prescan_elapsed = t_prescan - t_start

    assert prescan_result.file_name == "d365_gl_actuals.csv"
    assert prescan_result.estimated_rows >= 200_000
    assert prescan_elapsed < 5.0, f"Prescan took too long: {prescan_elapsed:.2f}s"

    # 2. Parse benchmark
    batch, transactions = parse_csv_transactions(sample_path)
    t_end = time.perf_counter()
    parse_elapsed = t_end - t_prescan
    total_elapsed = t_end - t_start

    # 3. Peak memory measurement
    peak_bytes = get_peak_working_set_bytes()
    peak_mb = peak_bytes / (1024 * 1024) if peak_bytes > 0 else 0.0

    print(
        f"\n[BENCHMARK RESULT] Rows: {batch.total_source_rows:,} | "
        f"Prescan: {prescan_elapsed:.2f}s | "
        f"Parse: {parse_elapsed:.2f}s | "
        f"Total: {total_elapsed:.2f}s | "
        f"Peak Memory: {peak_mb:.1f} MB"
    )

    # 4. NFR-002: Import 250k rows <= 60.0s
    assert total_elapsed <= 60.0, (
        f"NFR-002 violation: 250k import took {total_elapsed:.2f}s (budget: <= 60.0s)"
    )

    # 5. NFR-005: Peak memory <= 1.5 GB (1536 MB)
    if peak_mb > 0:
        assert peak_mb <= 1536.0, (
            f"NFR-005 violation: Peak memory {peak_mb:.1f} MB exceeded 1.5 GB limit"
        )

    # 6. Integrity and validation assertions
    assert batch.loaded_count >= 200_000
    assert (
        batch.total_source_rows
        == batch.loaded_count + batch.quarantined_count + batch.rejected_count
    )
    assert len(transactions) == batch.loaded_count
