"""Provider factory and resolver helpers."""

from __future__ import annotations

from config import settings
from services.providers.base import BaseProvider
from services.providers.openai_provider import OpenAIProvider


def resolve_provider(provider_key: str | None = None) -> BaseProvider:
    """Resolve a provider from explicit key or runtime configuration.

    Resolution precedence:
    1. explicit ``provider_key`` argument
    2. ``settings.research_provider`` (if present)
    3. default ``openai``
    """

    key = (provider_key or getattr(settings, "research_provider", "openai")).strip().lower()

    providers: dict[str, type[BaseProvider]] = {
        "openai": OpenAIProvider,
    }

    try:
        return providers[key]()
    except KeyError as exc:
        valid_keys = ", ".join(sorted(providers))
        raise ValueError(f"Unknown provider '{key}'. Available providers: {valid_keys}") from exc
