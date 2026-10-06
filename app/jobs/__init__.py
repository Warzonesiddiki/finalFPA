"""Job execution package: worker thread + registry (ADR-006, docs/09 §3.7, §8).

Long jobs run on a single background thread with states, progress, ETA and
cooperative cancellation; the queue holds one job (a third submit is
rejected). Import from here, never from the submodules.
"""

from app.jobs.registry import (
    TERMINAL_STATES,
    JobCancelled,
    JobContext,
    JobQueueFull,
    JobRecord,
    JobRegistry,
    JobState,
    JobType,
)
from app.jobs.worker import JobWorker

__all__ = [
    "TERMINAL_STATES",
    "JobCancelled",
    "JobContext",
    "JobQueueFull",
    "JobRecord",
    "JobRegistry",
    "JobState",
    "JobType",
    "JobWorker",
]
