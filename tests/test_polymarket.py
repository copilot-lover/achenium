import unittest
from unittest.mock import patch

import config
from services.polymarket import PolymarketClient, fetch_suggested_markets


class PolymarketTests(unittest.TestCase):
    def test_fetch_suggested_markets_ranks_and_limits(self):
        fake_markets = [
            {
                "slug": "election-2028",
                "question": "Will candidate X win?",
                "liquidity": 800000,
                "volume": 2500000,
                "clobTokenIds": ["token_yes"],
            },
            {
                "slug": "fed-rate-cut-june",
                "question": "Will the Fed cut rates by June?",
                "liquidity": 100000,
                "volume": 400000,
                "clobTokenIds": ["token_yes_2"],
            },
        ]

        with patch.object(PolymarketClient, "get_markets", return_value=fake_markets), patch.object(
            PolymarketClient, "get_price", side_effect=[0.61, 0.44]
        ):
            rows = fetch_suggested_markets("balanced", limit=1)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["market"], "ELECTION-2028")
        self.assertIn("YES 0.61", rows[0]["rationale"])

    def test_build_l2_headers_requires_credentials(self):
        client = PolymarketClient()

        original = (
            config.settings.poly_address,
            config.settings.poly_api_key,
            config.settings.poly_api_secret,
            config.settings.poly_passphrase,
        )
        config.settings.poly_address = None
        config.settings.poly_api_key = None
        config.settings.poly_api_secret = None
        config.settings.poly_passphrase = None

        try:
            with self.assertRaises(RuntimeError):
                client._build_l2_headers("GET", "/orders", "")
        finally:
            (
                config.settings.poly_address,
                config.settings.poly_api_key,
                config.settings.poly_api_secret,
                config.settings.poly_passphrase,
            ) = original


if __name__ == "__main__":
    unittest.main()
