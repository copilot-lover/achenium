import os
import sqlite3
import tempfile
import unittest

import config
from services import db_migrations, storage


class DbMigrationsTests(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db_path = path
        config.settings.db_path = self.db_path
        storage.init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_apply_migrations_is_idempotent(self):
        db_migrations.apply_migrations(self.db_path)
        db_migrations.apply_migrations(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ).fetchall()

        names = {row[0] for row in rows}
        self.assertEqual(
            names,
            {
                "idx_reports_created_at",
                "idx_reports_report_type",
                "idx_trades_status",
                "idx_trades_close_at",
            },
        )

    def test_recommended_setup_steps_apply_pragmas(self):
        with sqlite3.connect(self.db_path) as conn:
            db_migrations.apply_recommended_pragmas(conn, timeout_ms=1234)
            timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]

        self.assertEqual(timeout, 1234)


if __name__ == "__main__":
    unittest.main()
