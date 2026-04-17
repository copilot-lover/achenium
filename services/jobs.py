from __future__ import annotations

import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from services.research import run_deep_research
from services.storage import get_open_trades, get_reports_since, save_report

scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global scheduler
    if scheduler:
        return

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        daily_research_job,
        CronTrigger(hour=settings.daily_research_hour_utc, minute=0),
        id="daily_research",
        replace_existing=True,
    )
    scheduler.add_job(
        preclose_monitor_job,
        IntervalTrigger(hours=settings.pre_close_check_interval_hours),
        id="preclose_monitor",
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_digest_job,
        CronTrigger(hour=(settings.daily_research_hour_utc + 1) % 24, minute=0),
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()


def daily_research_job() -> None:
    run_deep_research(["SPY", "QQQ"], "moderate", "swing")
    save_report("job_status", {"job": "daily_research", "status": "completed"})


def preclose_monitor_job() -> None:
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=settings.pre_close_window_hours)
    watched = []

    for trade in get_open_trades():
        close_at = datetime.fromisoformat(trade["close_at"])
        if now <= close_at <= window_end:
            watched.append(
                {
                    "trade_id": trade["id"],
                    "market": trade["market"],
                    "suggestion": "Re-evaluate stop/target; consider partial close if volatility expands.",
                }
            )

    save_report(
        "preclose_monitor",
        {
            "checked_at": now.isoformat(),
            "window_hours": settings.pre_close_window_hours,
            "flagged": watched,
        },
    )


def send_daily_digest_job() -> None:
    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    reports = get_reports_since(since)
    body = _render_digest(reports)

    save_report("daily_digest", {"sent": bool(_send_email(body)), "report_count": len(reports)})


def _render_digest(reports: list[dict]) -> str:
    lines = ["Achenium Daily AI Digest", "", f"Total updates: {len(reports)}", ""]
    for report in reports[-25:]:
        lines.append(f"[{report['created_at']}] {report['report_type']}: {report['payload']}")
    return "\n".join(lines)


def _send_email(body: str) -> bool:
    if not (settings.smtp_host and settings.report_recipient and settings.smtp_user and settings.smtp_password):
        return False

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_sender
    msg["To"] = settings.report_recipient
    msg["Subject"] = "Achenium Daily AI Digest"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    return True
