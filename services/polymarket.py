"""Polymarket integration (Gamma/Data/CLOB) guided by API-KEY-DOCS.md."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class PolymarketAPIError(RuntimeError):
    """Raised when Polymarket API returns an error response."""

    status_code: int
    message: str

    def __str__(self) -> str:
        return f"Polymarket API error {self.status_code}: {self.message}"


class PolymarketClient:
    """Typed helper for Gamma/Data/CLOB API calls.

    API surface follows API-KEY-DOCS.md:
    - Gamma: market/event discovery (public)
    - Data: positions/activity analytics (public)
    - CLOB: orderbook/prices (public) + order endpoints (authenticated)
    """

    gamma_base = "https://gamma-api.polymarket.com"
    data_base = "https://data-api.polymarket.com"
    clob_base = "https://clob.polymarket.com"

    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    # ---- Internal transport helpers ----
    def _request(
        self,
        method: str,
        base_url: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | list[Any] | None = None,
        auth_required: bool = False,
    ) -> Any:
        url = f"{base_url}{path}"
        headers: dict[str, str] = {"Accept": "application/json"}
        data = None

        if body is not None:
            data = json.dumps(body, separators=(",", ":"))
            headers["Content-Type"] = "application/json"

        if auth_required:
            headers.update(self._build_l2_headers(method, path, data or ""))

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise PolymarketAPIError(response.status_code, response.text[:300])

        if not response.text:
            return {}
        return response.json()

    def _build_l2_headers(self, method: str, path: str, body: str) -> dict[str, str]:
        if not all(
            [
                settings.poly_address,
                settings.poly_api_key,
                settings.poly_api_secret,
                settings.poly_passphrase,
            ]
        ):
            raise RuntimeError(
                "Missing Polymarket auth env vars. Set POLY_ADDRESS, POLY_API_KEY, "
                "POLY_API_SECRET, and POLY_PASSPHRASE."
            )

        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method.upper()}{path}{body}"
        signature = hmac.new(
            settings.poly_api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "POLY_ADDRESS": settings.poly_address,
            "POLY_API_KEY": settings.poly_api_key,
            "POLY_PASSPHRASE": settings.poly_passphrase,
            "POLY_TIMESTAMP": timestamp,
            "POLY_SIGNATURE": signature,
        }

    # ---- Gamma endpoints ----
    def get_markets(self, *, active: bool = True, closed: bool = False, limit: int = 50) -> list[dict[str, Any]]:
        return self._request("GET", self.gamma_base, "/markets", params={"active": active, "closed": closed, "limit": limit})

    def search(self, query: str, limit_per_type: int = 10) -> dict[str, Any]:
        return self._request(
            "GET",
            self.gamma_base,
            "/public-search",
            params={"q": query, "limit_per_type": limit_per_type},
        )

    # ---- Data endpoints ----
    def get_positions(self, user: str) -> list[dict[str, Any]]:
        return self._request("GET", self.data_base, "/positions", params={"user": user})

    def get_activity(self, user: str) -> list[dict[str, Any]]:
        return self._request("GET", self.data_base, "/activity", params={"user": user})

    def get_trades(self, *, limit: int = 50, user: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if user:
            params["user"] = user
        return self._request("GET", self.data_base, "/trades", params=params)

    # ---- CLOB public endpoints ----
    def get_book(self, token_id: str) -> dict[str, Any]:
        return self._request("GET", self.clob_base, "/book", params={"token_id": token_id})

    def get_price(self, token_id: str, side: str = "BUY") -> float | None:
        payload = self._request("GET", self.clob_base, "/price", params={"token_id": token_id, "side": side})
        price = payload.get("price")
        return float(price) if price is not None else None

    def get_spread(self, token_id: str) -> dict[str, Any]:
        return self._request("GET", self.clob_base, "/spread", params={"token_id": token_id})

    # ---- CLOB authenticated endpoints ----
    def create_order(self, order_payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", self.clob_base, "/order", body=order_payload, auth_required=True)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return self._request("DELETE", self.clob_base, f"/order/{order_id}", auth_required=True)

    def get_orders(self, *, status: str = "LIVE", market: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"status": status}
        if market:
            params["market"] = market
        return self._request("GET", self.clob_base, "/orders", params=params, auth_required=True)


def _float_or_default(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fetch_suggested_markets(style: str, limit: int = 8) -> list[dict[str, Any]]:
    """Return Polymarket-backed suggestions for UI selection.

    This references endpoint fields documented in API-KEY-DOCS.md and gracefully
    falls back to empty results if the upstream API is unavailable.
    """
    client = PolymarketClient(timeout_seconds=settings.polymarket_timeout_seconds)
    try:
        markets = client.get_markets(active=True, closed=False, limit=80)
    except Exception as exc:
        logger.warning("Polymarket lookup failed: %s", exc)
        return []

    ranked: list[dict[str, Any]] = []
    for market in markets:
        clob_token_ids = market.get("clobTokenIds") or []
        yes_token = clob_token_ids[0] if clob_token_ids else None
        yes_price = None
        if yes_token:
            try:
                yes_price = client.get_price(yes_token, side="BUY")
            except Exception:
                yes_price = None

        liquidity = _float_or_default(market.get("liquidity"))
        volume = _float_or_default(market.get("volume"))
        score = min(0.99, 0.35 + (liquidity / 1_000_000) + (volume / 5_000_000))

        rationale_parts = [
            f"Liquidity ${liquidity:,.0f}",
            f"volume ${volume:,.0f}",
        ]
        if yes_price is not None:
            rationale_parts.append(f"YES {yes_price:.2f}")

        ranked.append(
            {
                "market": str((market.get("slug") or market.get("id") or "")).upper(),
                "score": round(score, 2),
                "rationale": f"{market.get('question', 'Polymarket event')} | {'; '.join(rationale_parts)}",
                "style": style,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    unique: list[dict[str, Any]] = []
    seen = set()
    for item in ranked:
        if not item["market"] or item["market"] in seen:
            continue
        seen.add(item["market"])
        unique.append(item)
        if len(unique) >= limit:
            break

    return unique
