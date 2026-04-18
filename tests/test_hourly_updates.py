import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

import config
from services.hourly_updates import (
    hourly_update_job,
    normalize_update_interval_hours,
)
from services.storage import add_trade, get_reports_since, init_db


class HourlyUpdatesTests(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db_path = path
        config.settings.db_path = self.db_path
        init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_normalize_update_interval_hours_clamps_to_bounds(self):
        self.assertEqual(normalize_update_interval_hours(0), 1)
        self.assertEqual(normalize_update_interval_hours(8), 8)
        self.assertEqual(normalize_update_interval_hours(99), 24)

    def test_hourly_update_job_saves_report_with_expected_shape(self):
        close_at = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
        add_trade("SPY", "YES", 0.62, close_at)

        result = hourly_update_job(cadence_hours=5)

        self.assertEqual(result["report_type"], "hourly_update")
        self.assertIn("payload", result)
        self.assertEqual(result["payload"]["cadence_hours"], 5)
        self.assertEqual(result["payload"]["open_trade_count"], 1)

        reports = get_reports_since("1970-01-01T00:00:00+00:00")
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["report_type"], "hourly_update")
        self.assertEqual(reports[0]["payload"]["cadence_hours"], 5)


if __name__ == "__main__":
    unittest.main()
