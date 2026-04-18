"""In-memory job metrics helpers.

This module intentionally keeps a lightweight, process-local metrics registry that
can be imported by jobs/routes later without creating hard dependencies.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any


_lock = Lock()
_counters: dict[str, dict[str, int]] = defaultdict(lambda: {"started": 0, "succeeded": 0, "failed": 0})
_last_run_at: dict[str, str] = {}
_last_error_at: dict[str, str] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_job_started(job_name: str) -> None:
    """Increment the started counter and update the last-run timestamp."""
    with _lock:
        _counters[job_name]["started"] += 1
        _last_run_at[job_name] = _now_iso()


def record_job_succeeded(job_name: str) -> None:
    """Increment the succeeded counter and update the last-run timestamp."""
    with _lock:
        _counters[job_name]["succeeded"] += 1
        _last_run_at[job_name] = _now_iso()


def record_job_failed(job_name: str) -> None:
    """Increment the failed counter and update run/error timestamps."""
    now = _now_iso()
    with _lock:
        _counters[job_name]["failed"] += 1
        _last_run_at[job_name] = now
        _last_error_at[job_name] = now


def get_metrics_snapshot() -> dict[str, Any]:
    """Return a JSON-serializable snapshot of all tracked job metrics."""
    with _lock:
        jobs: dict[str, dict[str, Any]] = {}
        for job_name, counts in _counters.items():
            jobs[job_name] = {
                "counters": {
                    "started": counts["started"],
                    "succeeded": counts["succeeded"],
                    "failed": counts["failed"],
                },
                "last_run_at": _last_run_at.get(job_name),
                "last_error_at": _last_error_at.get(job_name),
            }

    return {"jobs": jobs, "tracked_jobs": len(jobs)}
