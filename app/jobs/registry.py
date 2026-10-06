"""Job execution for long operations per ADR-006 (docs/09 §3.7, §8).

Single process, one background worker thread, one long job at a time (queue
depth 1). The API thread never blocks on analysis work; the UI polls the
registry (see §8.2). No module-level mutable state (ADR-006 thread safety):
callers construct and own :class:`JobRegistry` (and :class:`JobWorker`)
instances explicitly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from typing import Any


class JobType(StrEnum):
    """Closed job-type set, quoted from 09 §8.1."""

    IMPORT_VALIDATE = "import_validate"
    IMPORT_COMMIT = "import_commit"
    RULE_RUN = "rule_run"
    FORECAST_GENERATE = "forecast_generate"
    EXPORT_XLSX = "export_xlsx"
    EXPORT_PPT = "export_ppt"
    BACKUP = "backup"
    RESTORE = "restore"
    MIGRATE = "migrate"
    AI_BATCH = "ai_batch"


class JobState(StrEnum):
    """Lifecycle states, quoted from 09 §8.1."""

    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset({JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED})


class JobQueueFull(Exception):
    """Raised when a submit arrives while running + queued slots are taken."""


class JobCancelled(Exception):
    """Raised inside a job function when it observes a cancellation request."""


@dataclass
class JobContext:
    """Handle a running job function uses to report progress and observe cancel.

    Constructed by the worker, never by job code. Cooperative cancellation
    (§8.1): check :meth:`is_cancelling` at every stage boundary and every N
    rows (N documented per job type); call :meth:`check` to raise
    :class:`JobCancelled` when cancellation was requested.
    """

    job_id: str
    _registry: JobRegistry
    _cancelled: bool = False

    def report(self, progress_pct: float, stage: str) -> None:
        """Report monotonic progress (0–100) and the current stage."""
        self._registry.report_progress(self.job_id, progress_pct, stage)

    def is_cancelling(self) -> bool:
        """True once cancellation was requested for this job."""
        record = self._registry.get(self.job_id)
        return record.state == JobState.CANCELLING or self._cancelled

    def check(self) -> None:
        """Raise :class:`JobCancelled` if cancellation was requested."""
        if self.is_cancelling():
            raise JobCancelled(f"{self.job_id} cancelled by user")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class JobRecord:
    """One job and its observable status (09 §8.1 registry row)."""

    job_id: str
    job_type: JobType
    state: JobState = JobState.QUEUED
    progress_pct: float = 0.0
    stage: str = "queued"
    eta_seconds: float | None = None
    enqueued_at: str = field(default_factory=_utcnow)
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    # Throughput samples for ETA: (monotonic_seconds, progress_pct).
    _samples: list[tuple[float, float]] = field(default_factory=list, repr=False)


class JobRegistry:
    """Thread-safe registry of jobs with queue-depth-1 admission.

    All mutations hold an internal lock; readers get snapshots, never live
    references to mutable internals beyond the record itself.
    """

    #: ETA needs this many seconds of observed progress before it is trusted;
    #: until then ``eta_seconds`` stays None and the UI shows elapsed + stage.
    ETA_WARMUP_SECONDS = 2.0

    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, JobRecord] = {}
        self._funcs: dict[str, Callable[[JobContext], dict[str, Any] | None]] = {}
        self._on_cancel: dict[str, Callable[[], None] | None] = {}
        self._seq = 0

    def submit(
        self,
        job_type: JobType | str,
        func: Callable[[JobContext], dict[str, Any] | None],
        *,
        on_cancel: Callable[[], None] | None = None,
    ) -> JobRecord:
        """Admit a job. Second concurrent job queues; a third is rejected."""
        if isinstance(job_type, str):
            job_type = JobType(job_type)  # ValueError on unknown types
        with self._lock:
            active = [j for j in self._jobs.values() if j.state not in TERMINAL_STATES]
            if len(active) >= 2:
                raise JobQueueFull(f"queue depth 1 exceeded: {[j.job_id for j in active]} active")
            self._seq += 1
            record = JobRecord(job_id=f"job-{self._seq:06d}", job_type=job_type)
            record.stage = "queued"
            self._jobs[record.job_id] = record
            self._funcs[record.job_id] = func
            self._on_cancel[record.job_id] = on_cancel
            if len(active) == 0:
                record.state = JobState.QUEUED
            return record

    def request_cancel(self, job_id: str) -> JobRecord:
        """Ask for cancellation: queued jobs die now, running jobs flip to cancelling."""
        with self._lock:
            record = self._jobs[job_id]
            if record.state == JobState.QUEUED:
                record.state = JobState.CANCELLED
                record.finished_at = _utcnow()
                record.error = "cancelled before start"
            elif record.state == JobState.RUNNING:
                record.state = JobState.CANCELLING
            return record

    def report_progress(self, job_id: str, progress_pct: float, stage: str) -> JobRecord:
        """Record monotonic progress plus a throughput sample for ETA."""
        import time

        with self._lock:
            record = self._jobs[job_id]
            progress_pct = max(0.0, min(100.0, progress_pct))
            # Aggregate percentage is monotonic and honest (§8.1): never step back.
            if progress_pct < record.progress_pct:
                progress_pct = record.progress_pct
            record.progress_pct = progress_pct
            record.stage = stage
            record._samples.append((time.monotonic(), progress_pct))
            record.eta_seconds = self._eta_locked(record)
            return record

    def _eta_locked(self, record: JobRecord) -> float | None:
        """Throughput-based ETA with a warm-up window; None when unstable."""

        samples = record._samples
        if len(samples) < 2:
            return None
        first_t, first_p = samples[0]
        last_t, last_p = samples[-1]
        elapsed = last_t - first_t
        gained = last_p - first_p
        if elapsed < self.ETA_WARMUP_SECONDS or gained <= 0:
            return None
        rate = gained / elapsed  # pct per second
        remaining = 100.0 - last_p
        if remaining <= 0:
            return 0.0
        return remaining / rate

    def finish(
        self,
        job_id: str,
        *,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        cancelled: bool = False,
    ) -> JobRecord:
        """Close a job as succeeded / failed / cancelled with its summary."""
        with self._lock:
            record = self._jobs[job_id]
            record.finished_at = _utcnow()
            if cancelled:
                record.state = JobState.CANCELLED
                record.error = error or "cancelled by user"
            elif error is not None:
                record.state = JobState.FAILED
                record.error = error
            else:
                record.state = JobState.SUCCEEDED
                record.progress_pct = 100.0
                record.result = result
            record.eta_seconds = None
            return record

    def get(self, job_id: str) -> JobRecord:
        """Return one job's record (KeyError on unknown id)."""
        with self._lock:
            return self._jobs[job_id]

    def list(self, *, include_terminal: bool = True) -> list[JobRecord]:
        """Return records oldest-first; terminal ones included on request."""
        with self._lock:
            records = sorted(self._jobs.values(), key=lambda r: r.enqueued_at)
            if not include_terminal:
                records = [r for r in records if r.state not in TERMINAL_STATES]
            return list(records)

    def take_next(
        self,
    ) -> (
        tuple[JobRecord, Callable[[JobContext], dict[str, Any] | None], Callable[[], None] | None]
        | None
    ):
        """Atomically pop the oldest queued job with its function and hooks.

        Returns ``(record, func, on_cancel)`` or None when the queue is empty.
        Worker-owned; the record is already flipped to running.
        """
        with self._lock:
            queued = [r for r in self._jobs.values() if r.state == JobState.QUEUED]
            if not queued:
                return None
            record = min(queued, key=lambda r: r.enqueued_at)
            record.state = JobState.RUNNING
            record.started_at = _utcnow()
            record.stage = "running"
            return record, self._funcs[record.job_id], self._on_cancel[record.job_id]
