"""Helpers for generating and persisting periodic status/research updates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.storage import get_open_trades, get_reports_since, save_report

MIN_CADENCE_HOURS = 1
MAX_CADENCE_HOURS = 24


def normalize_update_interval_hours(
    cadence_hours: int,
    minimum_hours: int = MIN_CADENCE_HOURS,
    maximum_hours: int = MAX_CADENCE_HOURS,
) -> int:
    """Clamp cadence to a safe inclusive hourly range for periodic updates."""
    if minimum_hours > maximum_hours:
        raise ValueError("minimum_hours cannot be greater than maximum_hours")
    return max(minimum_hours, min(maximum_hours, int(cadence_hours)))


def build_hourly_update_payload(cadence_hours: int, now: datetime | None = None) -> dict:
    """Build a lightweight periodic snapshot payload suitable for save_report."""
    checked_at = now or datetime.now(timezone.utc)
    normalized_cadence = normalize_update_interval_hours(cadence_hours)
    since = (checked_at - timedelta(hours=normalized_cadence)).isoformat()

    open_trades = get_open_trades()
    recent_reports = get_reports_since(since)

    return {
        "checked_at": checked_at.isoformat(),
        "cadence_hours": normalized_cadence,
        "open_trade_count": len(open_trades),
        "recent_report_count": len(recent_reports),
        "signal": "monitor" if open_trades else "idle",
    }


def hourly_update_job(cadence_hours: int = MIN_CADENCE_HOURS) -> dict:
    """Generate and persist a lightweight periodic status/research update."""
    payload = build_hourly_update_payload(cadence_hours)
    save_report("hourly_update", payload)
    return {"report_type": "hourly_update", "payload": payload}
