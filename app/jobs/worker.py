"""Single background worker thread owning long-job execution (ADR-006).

One worker runs one job at a time; a second admitted job waits in ``queued``
(queue depth 1 — a third submit is rejected by the registry). The worker owns
its thread and all lifecycle transitions; job functions stay pure and receive
only a :class:`JobContext`. Rollback on cancellation is the job function's
responsibility (run it in ``except JobCancelled`` or via ``on_cancel``).
"""

from __future__ import annotations

import threading
import traceback
from typing import Any

from app.jobs.registry import (
    JobCancelled,
    JobContext,
    JobRegistry,
    JobState,
)


class JobWorker:
    """Owns the single background thread that drains the registry queue."""

    def __init__(self, registry: JobRegistry | None = None) -> None:
        self.registry = registry or JobRegistry()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the background thread (idempotent)."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._serve,
                name="fpa-job-worker",
                daemon=True,
            )
            self._thread.start()

    def stop(self, *, timeout: float | None = 10.0) -> None:
        """Ask the thread to exit after the current job and join it."""
        with self._lock:
            thread = self._thread
        self._stop.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)

    @property
    def alive(self) -> bool:
        """True while the background thread runs."""
        thread = self._thread
        return thread is not None and thread.is_alive()

    def _serve(self) -> None:
        while not self._stop.is_set():
            taken = self.registry.take_next()
            if taken is None:
                # Idle: short sleep keeps CPU at zero without slowing pickup.
                self._stop.wait(0.05)
                continue
            record, func, on_cancel = taken
            # Cancelled between take and run (request_cancel on queued flips
            # state, but take_next already moved it to running): honour it now.
            ctx = JobContext(job_id=record.job_id, _registry=self.registry)
            try:
                if self.registry.get(record.job_id).state == JobState.CANCELLING:
                    raise JobCancelled(f"{record.job_id} cancelled before start")
                result = func(ctx)
            except JobCancelled as exc:
                self._run_hook(on_cancel)
                self.registry.finish(record.job_id, cancelled=True, error=str(exc))
            except Exception as exc:
                # Every failure lands in the registry with its reason (§8.1);
                # nothing a job raises may kill the worker thread.
                self.registry.finish(
                    record.job_id,
                    error=f"{type(exc).__name__}: {exc}",
                    result={"traceback": traceback.format_exc(limit=5)},
                )
            else:
                # A late cancel (requested after the last check) still wins:
                # the job did the work, but the user asked out.
                state = self.registry.get(record.job_id).state
                if state == JobState.CANCELLING:
                    self._run_hook(on_cancel)
                    self.registry.finish(
                        record.job_id, cancelled=True, error="cancelled after final check"
                    )
                else:
                    self.registry.finish(record.job_id, result=result)

    @staticmethod
    def _run_hook(hook: Any) -> None:
        if hook is None:
            return
        try:
            hook()
        except Exception:
            pass  # Rollback hooks must never break the worker loop.
