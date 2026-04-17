import unittest

from unittest.mock import patch

from services.research import suggest_markets, validate_selected_markets


class ResearchValidationTests(unittest.TestCase):
    def test_validate_selected_markets_deduplicates_and_filters(self):
        result = validate_selected_markets(["spy", "SPY", "BAD$$$", "QQQ"])
        self.assertEqual(result, ["SPY", "QQQ"])

    def test_suggest_markets_uses_fallback_when_polymarket_unavailable(self):
        with patch("services.research.fetch_suggested_markets", return_value=[]):
            markets = suggest_markets("balanced")
        self.assertGreaterEqual(len(markets), 1)
        self.assertIn("market", markets[0])



if __name__ == "__main__":
    unittest.main()
