import os
import tempfile
import unittest
from datetime import datetime, timezone

import config
from services import storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db_path = path
        config.settings.db_path = self.db_path
        storage.init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_read_open_trades(self):
        close_at = datetime.now(timezone.utc).isoformat()
        storage.add_trade("SPY", "NO TRADE", 0.4, close_at)
        trades = storage.get_open_trades()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["market"], "SPY")


if __name__ == "__main__":
    unittest.main()
