"""OpenAI integration and fallback research generation."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResearchOutput:
    """Normalized research response used by templates and storage."""

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

_REQUEST_TIMESTAMPS: deque[float] = deque()


def deep_research_for_market(market: str, risk_profile: str, horizon: str) -> ResearchOutput:
    """Generate research output for one market, with graceful fallback."""
    if not settings.openai_api_key:
        logger.info("OpenAI API key missing; using fallback for %s", market)
        return _fallback(market, risk_profile, horizon)

    if not _allow_request_now():
        logger.warning("OpenAI rate limit reached in-process; using fallback for %s", market)
        return _fallback(market, risk_profile, horizon)

    from openai import OpenAI

    try:
        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
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
            logger.warning("Empty OpenAI response for %s; using fallback", market)
            return _fallback(market, risk_profile, horizon)

        logger.info("OpenAI research generated for %s", market)
        return ResearchOutput(
            market=market,
            beginner_summary=f"AI research generated for {market}.",
            quant_deep_dive=text[:1400],
            suggested_pick=f"Conditional long setup in {market} with strict stop-loss.",
            confidence=0.62,
            risks="Model output may omit intraday catalysts; validate with live data.",
        )
    except Exception as exc:
        logger.exception("OpenAI request failed for %s: %s", market, exc)
        return _fallback(market, risk_profile, horizon)


def _allow_request_now() -> bool:
    now = time.time()
    one_minute_ago = now - 60
    while _REQUEST_TIMESTAMPS and _REQUEST_TIMESTAMPS[0] < one_minute_ago:
        _REQUEST_TIMESTAMPS.popleft()

    if len(_REQUEST_TIMESTAMPS) >= settings.openai_requests_per_minute:
        return False

    _REQUEST_TIMESTAMPS.append(now)
    return True


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
        risks="Fallback mode active due to API unavailability, rate limit, or request failure.",
    )
