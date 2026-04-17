import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config import settings


def init_db() -> None:
    Path(settings.db_path).touch(exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market TEXT NOT NULL,
                pick TEXT NOT NULL,
                confidence REAL NOT NULL,
                close_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                report_type TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )


@contextmanager
def _connect():
    conn = sqlite3.connect(settings.db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_report(report_type: str, payload: dict) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO reports(created_at, report_type, payload) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), report_type, json.dumps(payload)),
        )


def get_reports_since(start_iso: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT created_at, report_type, payload FROM reports WHERE created_at >= ? ORDER BY created_at",
            (start_iso,),
        ).fetchall()
    reports = []
    for created_at, report_type, payload in rows:
        reports.append(
            {
                "created_at": created_at,
                "report_type": report_type,
                "payload": json.loads(payload),
            }
        )
    return reports


def add_trade(market: str, pick: str, confidence: float, close_at_iso: str, metadata: dict | None = None) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO trades(market, pick, confidence, close_at, metadata) VALUES (?, ?, ?, ?, ?)",
            (market, pick, confidence, close_at_iso, json.dumps(metadata or {})),
        )
        return int(cursor.lastrowid)


def get_open_trades() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, market, pick, confidence, close_at, metadata FROM trades WHERE status='open'"
        ).fetchall()
    result = []
    for row in rows:
        result.append(
            {
                "id": row[0],
                "market": row[1],
                "pick": row[2],
                "confidence": row[3],
                "close_at": row[4],
                "metadata": json.loads(row[5]),
            }
        )
    return result
