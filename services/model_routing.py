"""Provider-agnostic model routing by task type.

This module intentionally has a single responsibility: resolve a model/provider
configuration from a task type so scheduler and service callers can stay
decoupled from provider-specific integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Supported task type constants.
TASK_DEEP_RESEARCH: Final[str] = "deep_research"
TASK_DAILY_DIGEST: Final[str] = "daily_digest"
TASK_HOURLY_UPDATE: Final[str] = "hourly_update"


@dataclass(frozen=True)
class ModelConfig:
    """Resolved model settings for a given task type.

    Attributes:
        provider: Provider/integration identifier (for example: "openai").
        model_id: Provider model identifier.
        temperature: Optional default temperature.
        timeout_seconds: Optional default request timeout for this task.
    """

    provider: str
    model_id: str
    temperature: float | None = None
    timeout_seconds: int | None = None


_MODEL_CONFIG_BY_TASK: Final[dict[str, ModelConfig]] = {
    TASK_DEEP_RESEARCH: ModelConfig(
        provider="openai",
        model_id="gpt-4.1",
        temperature=0.2,
        timeout_seconds=25,
    ),
    TASK_DAILY_DIGEST: ModelConfig(
        provider="openai",
        model_id="gpt-4.1-mini",
        temperature=0.1,
        timeout_seconds=20,
    ),
    TASK_HOURLY_UPDATE: ModelConfig(
        provider="openai",
        model_id="gpt-4.1-mini",
        temperature=0.0,
        timeout_seconds=15,
    ),
}


def resolve_model_for_task(task_type: str) -> ModelConfig:
    """Resolve provider/model config for a task type.

    Args:
        task_type: Task identifier such as ``deep_research``, ``daily_digest``,
            or ``hourly_update``.

    Returns:
        ModelConfig for the provided task type.

    Raises:
        ValueError: If the task type is unsupported.
    """

    normalized = task_type.strip().lower()
    try:
        return _MODEL_CONFIG_BY_TASK[normalized]
    except KeyError as exc:
        supported = ", ".join(sorted(_MODEL_CONFIG_BY_TASK))
        raise ValueError(f"Unsupported task_type '{task_type}'. Supported: {supported}") from exc
