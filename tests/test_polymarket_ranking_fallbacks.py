import unittest
from unittest.mock import patch

from services.polymarket import PolymarketClient, fetch_suggested_markets


class PolymarketRankingFallbackTests(unittest.TestCase):
    def test_fetch_suggested_markets_returns_ranked_schema(self):
        fake_markets = [
            {
                "slug": "high-liquidity-market",
                "question": "Will X happen?",
                "liquidity": 800000,
                "volume": 2200000,
                "clobTokenIds": ["token_a"],
            },
            {
                "slug": "lower-liquidity-market",
                "question": "Will Y happen?",
                "liquidity": 200000,
                "volume": 300000,
                "clobTokenIds": ["token_b"],
            },
        ]

        with patch.object(PolymarketClient, "get_markets", return_value=fake_markets), patch.object(
            PolymarketClient,
            "get_price",
            side_effect=[0.58, None],
        ):
            rows = fetch_suggested_markets("balanced", limit=2)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["market"], "HIGH-LIQUIDITY-MARKET")

        for row in rows:
            self.assertEqual(set(row.keys()), {"market", "score", "rationale", "style"})
            self.assertIsInstance(row["market"], str)
            self.assertIsInstance(row["score"], float)
            self.assertGreaterEqual(row["score"], 0.0)
            self.assertLessEqual(row["score"], 0.99)
            self.assertIsInstance(row["rationale"], str)
            self.assertEqual(row["style"], "balanced")

        self.assertGreaterEqual(rows[0]["score"], rows[1]["score"])
        self.assertIn("YES 0.58", rows[0]["rationale"])
        self.assertNotIn("YES", rows[1]["rationale"])

    def test_fetch_suggested_markets_returns_empty_when_upstream_fails(self):
        with patch.object(PolymarketClient, "get_markets", side_effect=RuntimeError("upstream timeout")):
            rows = fetch_suggested_markets("balanced")

        self.assertEqual(rows, [])

    def test_fetch_suggested_markets_returns_empty_when_no_markets(self):
        with patch.object(PolymarketClient, "get_markets", return_value=[]):
            rows = fetch_suggested_markets("balanced")

        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
