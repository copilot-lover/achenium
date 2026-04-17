"""Market suggestion and deep-research orchestration."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from config import settings
from services.openai_service import ResearchOutput, deep_research_for_market
from services.polymarket import fetch_suggested_markets
from services.storage import add_trade, save_report

DEFAULT_MARKETS = ["SPY", "QQQ", "TLT", "GLD", "BTC-USD", "ETH-USD", "EURUSD", "CL=F"]
_MARKET_PATTERN = re.compile(r"^[A-Z0-9=\-\.]{2,15}$")


def suggest_markets(style: str) -> list[dict]:
    """Return ranked suggestions with Polymarket-first behavior and safe fallback."""
    live_markets = fetch_suggested_markets(style=style, limit=settings.max_selected_markets)
    if live_markets:
        return live_markets

    ranked = []
    for idx, market in enumerate(DEFAULT_MARKETS, start=1):
        ranked.append(
            {
                "market": market,
                "score": round(max(0.35, 0.92 - (idx * 0.07)), 2),
                "rationale": f"{market} has strong liquidity and clean structure for {style} strategies.",
            }
        )
    return ranked


def validate_selected_markets(selected_markets: list[str]) -> list[str]:
    """Validate selected markets and normalize duplicates."""
    cleaned = []
    seen = set()
    for market in selected_markets:
        token = market.strip().upper()
        if token in seen:
            continue
        if token not in DEFAULT_MARKETS and not _MARKET_PATTERN.match(token):
            continue
        seen.add(token)
        cleaned.append(token)

    return cleaned[: settings.max_selected_markets]


def run_deep_research(selected_markets: list[str], risk_profile: str, horizon: str) -> list[ResearchOutput]:
    """Run deep research for validated selected markets and persist outcomes."""
    outputs: list[ResearchOutput] = []
    for market in validate_selected_markets(selected_markets):
        result = deep_research_for_market(market, risk_profile, horizon)
        outputs.append(result)

        close_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        add_trade(
            market=result.market,
            pick=result.suggested_pick,
            confidence=result.confidence,
            close_at_iso=close_at,
            metadata={"risk_profile": risk_profile, "horizon": horizon},
        )

    save_report(
        "deep_research",
        {
            "selected_markets": selected_markets,
            "risk_profile": risk_profile,
            "horizon": horizon,
            "count": len(outputs),
        },
    )
    return outputs
