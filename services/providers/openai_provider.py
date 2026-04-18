"""OpenAI-backed provider adapter.

This adapter intentionally wraps the current OpenAI behavior in
``services.openai_service`` so existing behavior stays unchanged while
callers migrate to the provider interface.
"""

from __future__ import annotations

from services.openai_service import SYSTEM_PROMPT, deep_research_for_market

from config import settings
from services.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Provider adapter that preserves today's OpenAI integration behavior."""

    @property
    def key(self) -> str:
        return "openai"

    def generate_text(self, prompt: str, *, system_prompt: str | None = None) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return getattr(response, "output_text", "").strip()

    def generate_research(self, market: str, risk_profile: str, horizon: str):
        return deep_research_for_market(market, risk_profile, horizon)
