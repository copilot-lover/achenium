import sqlite3
from collections.abc import Callable
from pathlib import Path

from config import settings

ConnectionSetupStep = Callable[[sqlite3.Connection], None]


INDEX_STATEMENTS: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_reports_report_type ON reports(report_type)",
    "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)",
    "CREATE INDEX IF NOT EXISTS idx_trades_close_at ON trades(close_at)",
)


def apply_migrations(db_path: str | None = None) -> None:
    """Apply database schema/index migrations.

    This entrypoint is idempotent and can be called repeatedly.
    """
    path = db_path or settings.db_path
    Path(path).touch(exist_ok=True)
    with sqlite3.connect(path) as conn:
        for statement in INDEX_STATEMENTS:
            conn.execute(statement)
        conn.commit()


def enable_wal_mode(conn: sqlite3.Connection) -> None:
    """Recommended SQLite setup: use Write-Ahead Logging mode."""
    conn.execute("PRAGMA journal_mode=WAL")


def set_busy_timeout(conn: sqlite3.Connection, timeout_ms: int = 5000) -> None:
    """Recommended SQLite setup: set busy timeout in milliseconds."""
    conn.execute(f"PRAGMA busy_timeout={int(timeout_ms)}")


def recommended_setup_steps(timeout_ms: int = 5000) -> tuple[ConnectionSetupStep, ...]:
    """Return optional connection setup steps as callables."""

    def _busy_timeout_step(conn: sqlite3.Connection) -> None:
        set_busy_timeout(conn, timeout_ms=timeout_ms)

    return (
        enable_wal_mode,
        _busy_timeout_step,
    )


def apply_recommended_pragmas(
    conn: sqlite3.Connection, timeout_ms: int = 5000
) -> None:
    """Convenience helper to apply recommended PRAGMA settings to a connection."""
    for step in recommended_setup_steps(timeout_ms=timeout_ms):
        step(conn)
