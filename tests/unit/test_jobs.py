"""TB-025 regression: worker thread + registry per ADR-006 (docs/09 §3.7, §8.1).

Covers the registry contract (states, queue depth 1, monotonic progress,
ETA warm-up, cooperative cancellation, failure capture) and the worker
lifecycle — plus the shell decoupling proof (no ``_server_thread`` global).
"""

import socket
import threading
import time

import pytest

from app.jobs import (
    JobContext,
    JobQueueFull,
    JobRegistry,
    JobState,
    JobType,
    JobWorker,
)


def _ok_fn(ctx: JobContext) -> dict[str, object]:
    ctx.report(50.0, "half")
    ctx.report(30.0, "rewind-attempt")  # must not step back (§8.1 monotonic)
    ctx.report(100.0, "done")
    return {"rows": 3}


def _staged_fn(ctx: JobContext) -> dict[str, object] | None:
    for pct, stage in ((10.0, "pre-scan"), (50.0, "parse"), (100.0, "commit")):
        ctx.check()
        ctx.report(pct, stage)
        time.sleep(0.05)
    return {"ok": True}


def _boom_fn(_ctx: JobContext) -> dict[str, object] | None:
    raise RuntimeError("synthetic failure")


def _run_one(worker: JobWorker, record_id: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    terminal = {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}
    while time.monotonic() < deadline:
        if worker.registry.get(record_id).state in terminal:
            return
        time.sleep(0.02)
    raise TimeoutError(f"{record_id} never reached a terminal state")


def test_submit_second_queues_third_rejected():
    """Queue depth 1: one running slot + one queued; a third is rejected."""
    reg = JobRegistry()
    first = reg.submit(JobType.RULE_RUN, _staged_fn)
    second = reg.submit(JobType.RULE_RUN, _staged_fn)
    assert first.state == JobState.QUEUED
    assert second.state == JobState.QUEUED
    with pytest.raises(JobQueueFull):
        reg.submit(JobType.RULE_RUN, _staged_fn)


def test_unknown_job_type_rejected():
    """The §8.1 type set is closed: unknown types fail at submit."""
    reg = JobRegistry()
    with pytest.raises(ValueError):
        reg.submit("defrag_hard_drive", _ok_fn)  # type: ignore[arg-type]


def test_worker_runs_fifo_to_success_with_summary():
    """Worker drains queued jobs in order; success stores the summary."""
    reg = JobRegistry()
    worker = JobWorker(reg)
    worker.start()
    try:
        first = reg.submit(JobType.IMPORT_COMMIT, _ok_fn)
        second = reg.submit(JobType.EXPORT_XLSX, _ok_fn)
        _run_one(worker, first.job_id)
        _run_one(worker, second.job_id)
        assert reg.get(first.job_id).state == JobState.SUCCEEDED
        assert reg.get(first.job_id).result == {"rows": 3}
        assert reg.get(second.job_id).state == JobState.SUCCEEDED
        # FIFO: the first-submitted job started first.
        assert reg.get(first.job_id).started_at <= reg.get(second.job_id).started_at
    finally:
        worker.stop()


def test_progress_is_monotonic():
    """A 50 → 30 report sequence never steps the aggregate back (§8.1)."""
    reg = JobRegistry()
    record = reg.submit(JobType.RULE_RUN, _ok_fn)
    reg.report_progress(record.job_id, 50.0, "parse")
    reg.report_progress(record.job_id, 30.0, "rewind-attempt")
    assert reg.get(record.job_id).progress_pct == 50.0

    worker = JobWorker(reg)
    worker.start()
    try:
        _run_one(worker, record.job_id)
        assert reg.get(record.job_id).progress_pct == 100.0
    finally:
        worker.stop()


def test_cancel_queued_job_never_runs():
    """Cancelling a queued job marks it cancelled; the worker skips it."""
    reg = JobRegistry()
    ran = []
    worker = JobWorker(reg)
    worker.start()
    try:
        blocker = reg.submit(JobType.RULE_RUN, _staged_fn)
        queued = reg.submit(JobType.RULE_RUN, lambda ctx: ran.append(True) or {"x": 1})
        reg.request_cancel(queued.job_id)
        assert reg.get(queued.job_id).state == JobState.CANCELLED
        _run_one(worker, blocker.job_id)
        time.sleep(0.2)  # let the worker pass over the cancelled job
        assert ran == []
        assert reg.get(queued.job_id).state == JobState.CANCELLED
    finally:
        worker.stop()


def test_cancel_running_job_is_cooperative_with_hook():
    """A staged job observing ctx.check() cancels; the on_cancel hook runs."""
    reg = JobRegistry()
    worker = JobWorker(reg)
    worker.start()
    hooked = []
    try:
        record = reg.submit(
            JobType.IMPORT_COMMIT, _staged_fn, on_cancel=lambda: hooked.append(True)
        )
        while reg.get(record.job_id).state != JobState.RUNNING:
            time.sleep(0.01)
        reg.request_cancel(record.job_id)
        assert reg.get(record.job_id).state == JobState.CANCELLING
        _run_one(worker, record.job_id)
        final = reg.get(record.job_id)
        assert final.state == JobState.CANCELLED
        assert hooked == [True]
    finally:
        worker.stop()


def test_failure_captured_and_worker_survives():
    """A raising job is marked failed with its reason; the next job still runs."""
    reg = JobRegistry()
    worker = JobWorker(reg)
    worker.start()
    try:
        bad = reg.submit(JobType.MIGRATE, _boom_fn)
        good = reg.submit(JobType.BACKUP, _ok_fn)
        _run_one(worker, bad.job_id)
        _run_one(worker, good.job_id)
        failed = reg.get(bad.job_id)
        assert failed.state == JobState.FAILED
        assert "synthetic failure" in (failed.error or "")
        assert reg.get(good.job_id).state == JobState.SUCCEEDED
        assert worker.alive
    finally:
        worker.stop()


def test_eta_none_before_warmup_then_computed():
    """ETA is None until the warm-up window passes; then throughput-based."""
    reg = JobRegistry()
    record = reg.submit(JobType.RULE_RUN, _ok_fn)
    got = reg.get(record.job_id)
    assert got.eta_seconds is None
    reg.report_progress(record.job_id, 50.0, "parse")
    reg.report_progress(record.job_id, 60.0, "parse")
    assert reg.get(record.job_id).eta_seconds is None  # warm-up: show elapsed+stage

    reg2 = JobRegistry()
    reg2.ETA_WARMUP_SECONDS = 0.0  # instance-level: short-circuit warm-up
    record2 = reg2.submit(JobType.RULE_RUN, _ok_fn)
    reg2.report_progress(record2.job_id, 50.0, "parse")
    reg2.report_progress(record2.job_id, 75.0, "validate")
    eta = reg2.get(record2.job_id).eta_seconds
    assert eta is not None and eta >= 0.0


def test_get_list_and_unknown_id():
    """Registry reads: get by id, oldest-first list, KeyError on unknown."""
    reg = JobRegistry()
    first = reg.submit(JobType.BACKUP, _ok_fn)
    second = reg.submit(JobType.RESTORE, _ok_fn)
    ids = [r.job_id for r in reg.list()]
    assert ids == [first.job_id, second.job_id]
    assert reg.list(include_terminal=False) != []
    with pytest.raises(KeyError):
        reg.get("job-999999")


def test_worker_lifecycle_start_stop():
    """Worker starts idempotently and stops its thread on request."""
    worker = JobWorker()
    worker.start()
    worker.start()
    assert worker.alive
    worker.stop(timeout=5.0)
    assert not worker.alive


def test_shell_has_no_adhoc_server_thread_global():
    """TB-025 decoupling proof: shell.py owns no _server_thread global."""
    import app.desktop.shell as shell

    assert not hasattr(shell, "_server_thread")
    assert hasattr(shell, "ServerHandle")


def test_server_handle_wait_for_exit_joins_quick_thread():
    """ServerHandle exit-waiting joins a short-lived thread."""
    import app.desktop.shell as shell

    done = threading.Event()
    thread = threading.Thread(target=done.wait, args=(0.2,), daemon=True)
    handle = shell.ServerHandle(thread=thread, port=1)
    thread.start()
    handle.wait_for_exit()
    assert not thread.is_alive()


def test_server_handle_proves_readiness_by_connect():
    """wait_until_serving returns True against a real listening socket."""
    import app.desktop.shell as shell

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    stop = threading.Event()
    thread = threading.Thread(target=stop.wait, args=(5.0,), daemon=True)
    handle = shell.ServerHandle(thread=thread, port=port)
    thread.start()
    try:
        assert handle.wait_until_serving(timeout=5.0) is True
    finally:
        stop.set()
        listener.close()
