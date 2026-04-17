from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.openai_service import ResearchOutput, deep_research_for_market
from services.storage import add_trade, save_report

DEFAULT_MARKETS = [
    "SPY",
    "QQQ",
    "TLT",
    "GLD",
    "BTC-USD",
    "ETH-USD",
    "EURUSD",
    "CL=F",
]


def suggest_markets(style: str) -> list[dict]:
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


def run_deep_research(selected_markets: list[str], risk_profile: str, horizon: str) -> list[ResearchOutput]:
    outputs: list[ResearchOutput] = []
    for market in selected_markets:
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
