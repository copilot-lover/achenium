import unittest
from dataclasses import asdict, fields
from unittest.mock import patch

import config
from services.openai_service import ResearchOutput, deep_research_for_market


class ResearchOutputSchemaTests(unittest.TestCase):
    def test_research_output_uses_canonical_schema_on_fallback(self):
        original_key = config.settings.openai_api_key
        config.settings.openai_api_key = None

        try:
            output = deep_research_for_market("SPY", "balanced", "swing")
        finally:
            config.settings.openai_api_key = original_key

        self.assertIsInstance(output, ResearchOutput)

        payload = asdict(output)
        self.assertEqual(
            list(payload.keys()),
            [
                "market",
                "beginner_summary",
                "quant_deep_dive",
                "suggested_pick",
                "confidence",
                "risks",
            ],
        )

        self.assertEqual(output.market, "SPY")
        self.assertIsInstance(output.beginner_summary, str)
        self.assertIsInstance(output.quant_deep_dive, str)
        self.assertIsInstance(output.suggested_pick, str)
        self.assertIsInstance(output.confidence, float)
        self.assertIsInstance(output.risks, str)

    def test_research_output_dataclass_fields_are_stable(self):
        self.assertEqual(
            [field.name for field in fields(ResearchOutput)],
            [
                "market",
                "beginner_summary",
                "quant_deep_dive",
                "suggested_pick",
                "confidence",
                "risks",
            ],
        )


if __name__ == "__main__":
    unittest.main()
