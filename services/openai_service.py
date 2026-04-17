from __future__ import annotations

from dataclasses import dataclass

from config import settings

try:
    from openai import OpenAI
except ImportError:  # graceful local run without dependency installed
    OpenAI = None


@dataclass
class ResearchOutput:
    market: str
    beginner_summary: str
    quant_deep_dive: str
    suggested_pick: str
    confidence: float
    risks: str


SYSTEM_PROMPT = """
You are an institutional-grade quantitative research assistant designed for beginners and quant users.
Never auto-add markets. Analyze only selected markets.
Return concise sections: Beginner Summary, Quant Deep Dive, Suggested Pick, Confidence (0-1), Risks.
If evidence is weak, say NO TRADE.
""".strip()


def deep_research_for_market(market: str, risk_profile: str, horizon: str) -> ResearchOutput:
    if not settings.openai_api_key or OpenAI is None:
        return _fallback(market, risk_profile, horizon)

    client = OpenAI(api_key=settings.openai_api_key)
    user_prompt = (
        f"Selected market: {market}\n"
        f"Risk profile: {risk_profile}\n"
        f"Horizon: {horizon}\n"
        "Generate research with beginner + quant sections and one trade pick."
    )
    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    text = getattr(response, "output_text", "").strip()
    if not text:
        return _fallback(market, risk_profile, horizon)

    return ResearchOutput(
        market=market,
        beginner_summary=f"AI research generated for {market}.",
        quant_deep_dive=text[:1200],
        suggested_pick=f"Conditional long setup in {market} with strict stop-loss.",
        confidence=0.62,
        risks="Model output may omit intraday catalysts; validate with live data.",
    )


def _fallback(market: str, risk_profile: str, horizon: str) -> ResearchOutput:
    return ResearchOutput(
        market=market,
        beginner_summary=(
            f"{market} is selected. For {risk_profile} risk and {horizon} horizon, "
            "use small position sizing and wait for confirmation candles."
        ),
        quant_deep_dive=(
            "Regime: mixed momentum with elevated volatility. "
            "Use volatility-adjusted sizing, monitor drawdown threshold, and avoid over-leverage."
        ),
        suggested_pick="NO TRADE until breakout confirms above resistance with volume.",
        confidence=0.45,
        risks="Fallback mode active (no OpenAI API key or SDK).",
    )
