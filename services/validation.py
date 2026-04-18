"""Framework-agnostic input normalization and validation helpers."""

from __future__ import annotations

import re
from typing import Iterable, Literal, TypeAlias

Style: TypeAlias = Literal["balanced", "trend", "mean_reversion"]
RiskProfile: TypeAlias = Literal["conservative", "moderate", "aggressive"]
Horizon: TypeAlias = Literal["intraday", "swing", "position"]

STYLES: tuple[Style, ...] = ("balanced", "trend", "mean_reversion")
RISK_PROFILES: tuple[RiskProfile, ...] = ("conservative", "moderate", "aggressive")
HORIZONS: tuple[Horizon, ...] = ("intraday", "swing", "position")

MARKET_PATTERN = re.compile(r"^[A-Z0-9=\-.]{1,20}$")


def normalize_trim(value: str | None) -> str:
    """Return a safely trimmed string representation for an incoming value."""
    return str(value or "").strip()


def normalize_lower(value: str | None) -> str:
    """Trim and lowercase a value."""
    return normalize_trim(value).lower()


def normalize_upper(value: str | None) -> str:
    """Trim and uppercase a value."""
    return normalize_trim(value).upper()


def validate_style(value: str | None, default: Style = "balanced") -> Style:
    """Normalize and validate a trading style, returning a typed canonical value."""
    normalized = normalize_lower(value)
    if normalized in STYLES:
        return normalized  # type: ignore[return-value]
    return default


def validate_risk_profile(value: str | None, default: RiskProfile = "moderate") -> RiskProfile:
    """Normalize and validate a risk profile, returning a typed canonical value."""
    normalized = normalize_lower(value)
    if normalized in RISK_PROFILES:
        return normalized  # type: ignore[return-value]
    return default


def validate_horizon(value: str | None, default: Horizon = "swing") -> Horizon:
    """Normalize and validate a horizon, returning a typed canonical value."""
    normalized = normalize_lower(value)
    if normalized in HORIZONS:
        return normalized  # type: ignore[return-value]
    return default


def validate_selected_markets(
    selected_markets: Iterable[str | None],
    *,
    max_items: int = 8,
) -> list[str]:
    """Normalize, deduplicate, and validate selected market symbols."""
    markets: list[str] = []
    seen: set[str] = set()

    for raw in selected_markets:
        market = normalize_upper(raw)
        if not market or market in seen:
            continue
        if not MARKET_PATTERN.fullmatch(market):
            continue
        seen.add(market)
        markets.append(market)
        if len(markets) >= max_items:
            break

    return markets


def parse_int(
    value: str | int | float | None,
    *,
    default: int | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int | None:
    """Safely parse an integer and enforce optional min/max bounds."""
    try:
        parsed = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default

    if min_value is not None and parsed < min_value:
        return min_value
    if max_value is not None and parsed > max_value:
        return max_value
    return parsed


def parse_float(
    value: str | int | float | None,
    *,
    default: float | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    """Safely parse a float and enforce optional min/max bounds."""
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return default

    if min_value is not None and parsed < min_value:
        return min_value
    if max_value is not None and parsed > max_value:
        return max_value
    return parsed


__all__ = [
    "HORIZONS",
    "Horizon",
    "MARKET_PATTERN",
    "RISK_PROFILES",
    "RiskProfile",
    "STYLES",
    "Style",
    "normalize_lower",
    "normalize_trim",
    "normalize_upper",
    "parse_float",
    "parse_int",
    "validate_horizon",
    "validate_risk_profile",
    "validate_selected_markets",
    "validate_style",
]
