"""Provider interfaces for model-backed text and research generation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.openai_service import ResearchOutput


class BaseProvider(ABC):
    """Abstract provider contract for text and structured research generation."""

    @property
    @abstractmethod
    def key(self) -> str:
        """Stable provider identifier used by resolver logic."""

    @abstractmethod
    def generate_text(self, prompt: str, *, system_prompt: str | None = None) -> str:
        """Generate plain text from a prompt."""

    @abstractmethod
    def generate_research(self, market: str, risk_profile: str, horizon: str) -> ResearchOutput:
        """Generate normalized research output for a market."""
