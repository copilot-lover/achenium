import unittest
from unittest.mock import patch

import config
from services.openai_service import _REQUEST_TIMESTAMPS, deep_research_for_market


class OpenAIDeterministicFallbackTests(unittest.TestCase):
    def test_provider_unavailable_fallback_is_deterministic(self):
        original_key = config.settings.openai_api_key
        config.settings.openai_api_key = None

        try:
            first = deep_research_for_market("BTC-USD", "aggressive", "intraday")
            second = deep_research_for_market("BTC-USD", "aggressive", "intraday")
        finally:
            config.settings.openai_api_key = original_key

        self.assertEqual(first, second)
        self.assertIn("Fallback mode active", first.risks)

    def test_rate_limited_fallback_is_deterministic(self):
        original_key = config.settings.openai_api_key
        config.settings.openai_api_key = "test-key"

        try:
            _REQUEST_TIMESTAMPS.clear()
            with patch("services.openai_service._allow_request_now", return_value=False):
                first = deep_research_for_market("ETH-USD", "balanced", "swing")
                second = deep_research_for_market("ETH-USD", "balanced", "swing")
        finally:
            config.settings.openai_api_key = original_key
            _REQUEST_TIMESTAMPS.clear()

        self.assertEqual(first, second)
        self.assertEqual(first.confidence, 0.45)
        self.assertEqual(
            first.suggested_pick,
            "NO TRADE until breakout confirms above resistance with volume.",
        )


if __name__ == "__main__":
    unittest.main()
