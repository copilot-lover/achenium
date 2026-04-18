-- Initial SQLite schema for Achenium.
-- This migration is intentionally not wired into application startup yet.

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,
    pick TEXT NOT NULL,
    confidence REAL NOT NULL,
    close_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    report_type TEXT NOT NULL,
    payload TEXT NOT NULL
);
