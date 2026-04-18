import unittest
from unittest.mock import Mock, patch

from services.openai_service import ResearchOutput
from services.providers.factory import resolve_provider
from services.providers.openai_provider import OpenAIProvider


class ProviderFactoryTests(unittest.TestCase):
    def test_resolve_provider_defaults_to_openai(self):
        provider = resolve_provider()
        self.assertIsInstance(provider, OpenAIProvider)

    def test_resolve_provider_uses_explicit_key(self):
        provider = resolve_provider("OPENAI")
        self.assertIsInstance(provider, OpenAIProvider)

    def test_resolve_provider_raises_for_unknown_provider(self):
        with self.assertRaisesRegex(ValueError, "Unknown provider"):
            resolve_provider("unknown")


class OpenAIProviderTests(unittest.TestCase):
    def test_generate_research_delegates_to_existing_openai_service(self):
        expected = ResearchOutput(
            market="BTC",
            beginner_summary="summary",
            quant_deep_dive="deep-dive",
            suggested_pick="NO TRADE",
            confidence=0.5,
            risks="risk",
        )
        provider = OpenAIProvider()

        with patch("services.providers.openai_provider.deep_research_for_market", return_value=expected) as mock_call:
            result = provider.generate_research("BTC", "balanced", "swing")

        mock_call.assert_called_once_with("BTC", "balanced", "swing")
        self.assertEqual(result, expected)

    def test_generate_text_uses_openai_client(self):
        provider = OpenAIProvider()
        mock_response = Mock(output_text="hello world")
        mock_client = Mock()
        mock_client.responses.create.return_value = mock_response

        with patch("openai.OpenAI", return_value=mock_client) as mock_openai:
            text = provider.generate_text("say hi", system_prompt="system")

        self.assertEqual(text, "hello world")
        self.assertTrue(mock_openai.called)
        self.assertTrue(mock_client.responses.create.called)


if __name__ == "__main__":
    unittest.main()
