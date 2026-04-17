import unittest

from services.research import validate_selected_markets


class ResearchValidationTests(unittest.TestCase):
    def test_validate_selected_markets_deduplicates_and_filters(self):
        result = validate_selected_markets(["spy", "SPY", "BAD$$$", "QQQ"])
        self.assertEqual(result, ["SPY", "QQQ"])


if __name__ == "__main__":
    unittest.main()
