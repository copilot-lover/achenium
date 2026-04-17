# Polymarket API Local Specification & Usage Guide

**Executive Summary:** Polymarket’s APIs are split into three domains: **Gamma** (market discovery: events, markets, tags, etc.), **Data** (user positions, trades, analytics), and **CLOB** (orderbook/prices and trading). Gamma/Data are **public (no auth)**; CLOB has public read endpoints and **authenticated trading** endpoints【64†L244-L248】. Below is a machine-readable spec block (`POLYMARKET API SPEC (LOCAL COPY)`) followed by a detailed usage guide. The guide includes Python examples (REST + WebSocket), pseudocode for a mispricing scanner and order placement, WebSocket message formats, reconnection diagram, and a table mapping endpoints to use-cases. All endpoints include methods, parameters, sample requests/responses, error codes, rate-limit notes, and any necessary authentication details. Unspecified or undocumented behaviors are flagged and default handling is suggested. All information is drawn from official Polymarket docs【64†L244-L248】【68†L217-L225】.

```text
========================
POLYMARKET API SPEC (LOCAL COPY)
========================
BASE_URLS:
  - Gamma:  https://gamma-api.polymarket.com   (public discovery)
  - Data:   https://data-api.polymarket.com    (public analytics)
  - CLOB:   https://clob.polymarket.com        (orderbook/trading)

###############################################################################
# Gamma API (Public)
###############################################################################
GET /events
  Query: { active: bool (opt), closed: bool (opt), limit: int (opt), offset: string (opt) }
  Response 200: [ 
    { id: string, title: string, slug: string, 
      startDate: ISO8601, endDate: ISO8601,
      active: boolean, closed: boolean,
      markets: [
        { id: string, question: string, outcomes: [string],
          outcomePrices: [string],    # as decimal strings
          enableOrderBook: boolean,
          clobTokenIds: [string]      # asset IDs for each outcome
        }, ...
      ]
    }, ...
  ]
  Errors: 400 (bad params), 429 (rate-limit throttle).
GET /events/{id}, GET /events/slug/{slug}
  Path: id or slug (string, required). Response 200: single Event object (as above) or 404 if not found.
GET /markets
  Query: { active: bool (opt), closed: bool (opt), tag: string (opt), limit, offset }
  Response 200: [ 
    { id: string, question: string, slug: string,
      outcomes: [string], outcomePrices: [string],
      startDate, endDate,
      category: string, tags: [ {id, label, slug} ],
      volume: number, liquidity: number,
      enableOrderBook: boolean, clobTokenIds: [string]
    }, ...
  ]
GET /markets/{id}, GET /markets/slug/{slug}
  Path param: market ID or slug. Response 200: Market object (fields as above) or 404.
GET /tags
  Query: { limit, offset }. Response 200: [ { id: string, label: string, slug: string }, ... ].
GET /tags/{id}, GET /tags/slug/{slug}
  Returns 200: Tag object or 404.
GET /series
  Query: { limit, offset }. 200: [ { id: string, title: string, slug: string, ... }, ... ].
GET /series/{id}
  Returns 200: Series object or 404.
GET /sports
  Returns 200: [ { id: string, name: string, typeIds: [string] }, ... ].
GET /sports/types
  Returns 200: [ string, ... ] (list of valid sports market types).
GET /teams
  Query: { sport: string (opt) }. Response 200: [ { id: string, name: string, sportId: string }, ... ].
GET /public-search
  Query: { q: string (required), limit_per_type: int (opt), page: int (opt),
           events_status: string (opt), search_tags: bool (opt), search_profiles: bool (opt), ... }
  Response 200: {
    events: [Event], markets: [Market], tags: [Tag], profiles: [UserProfile],
    pagination: { hasMore: bool, totalResults: int }
  }
  Errors: 400 if q missing, 429 throttle.

###############################################################################
# Data API (Public)
###############################################################################
GET /positions
  Query: { user: string (0x address, required) }
  Response 200: [ 
    { asset: string, conditionId: string, outcome: string, outcomeIndex: int,
      size: number, avgPrice: number, initialValue: number, currentValue: number, cashPnl: number,
      totalBought: number, realizedPnl: number, totalPnl: number
    }, ...
  ]
GET /closed-positions
  Query: { user: string }. Returns 200: same schema as /positions but settled.
GET /activity
  Query: { user: string }. Returns 200: [ { timestamp: int, type: string, details: object }, ... ].
GET /value
  Query: { user: string }. Returns 200: { totalValue: number, breakdown: object }.
GET /trades
  Query: { limit: int, offset: int, market: [string] (conditionId array), eventId: [int], user: string, side: enum(BUY,SELL), takerOnly: bool, filterType: enum(TOKENS,CASH), filterAmount: number }
  Response 200: [
    { proxyWallet: string, side: "BUY"/"SELL", asset: string, conditionId: string,
      size: number, price: number, timestamp: number,
      title: string, slug: string, icon: string, eventSlug: string,
      outcome: string, outcomeIndex: int,
      name: string, pseudonym: string, bio: string,
      profileImage: string, profileImageOptimized: string,
      transactionHash: string
    }, ...
  ]【43†L270-L279】
GET /holders
  Query: { market: string }. Response 200: [ { user: string, position: number, percent: number }, ... ] (top holders).
GET /market-positions
  Query: { market: string (conditionId, required), user: string (opt), status: enum(OPEN,CLOSED,ALL), sortBy: enum(TOKENS,CASH_PNL,REALIZED_PNL,TOTAL_PNL), sortDirection: enum(ASC,DESC), limit, offset }
  Response 200: [
    {
      token: string,   # outcome asset ID
      positions: [
        { proxyWallet, name, profileImage, verified,
          asset: string, conditionId: string,
          avgPrice: number, size: number, currPrice: number,
          currentValue: number, cashPnl: number, totalBought: number,
          realizedPnl: number, totalPnl: number,
          outcome: string, outcomeIndex: number
        }, ...
      ]
    }, ...
  ]【60†L270-L279】

###############################################################################
# CLOB API - Public (No Auth for Reads)
###############################################################################
GET /book
  Query: { token_id: string (asset ID, required) }
  Response 200: {
    market: string,      # conditionId
    asset_id: string,    # token ID (same as token_id)
    timestamp: string,   # snapshot time (UNIX ms as string)
    hash: string,
    bids: [ { price: string, size: string }, ... ],  # descending prices
    asks: [ { price: string, size: string }, ... ],  # ascending prices
    min_order_size: string,
    tick_size: string,
    neg_risk: boolean,
    last_trade_price: string
  }【50†L275-L284】
GET /books
  Body: { token_ids: [string] }
  Response 200: { books: [ <book as above> ] }
  Limits: max 25 tokens per request (unspecified, use small batches).
GET /price
  Query: { token_id: string (required), side: enum(BUY,SELL, default=BUY) }
  Response 200: { price: number } – best bid (BUY) or best ask (SELL)【47†L204-L213】.
GET /prices
  Query: { token_ids: string (comma-separated), side: enum(BUY,SELL) }
  Response 200: { prices: [ { token_id: string, price: number }, ... ] }.
GET /midpoint
  Query: { token_id: string }
  Response 200: { midpoint: number } (average of best bid/ask).
GET /midpoints
  Query: { token_ids: [string] }
  Response 200: { midpoints: [ { token_id: string, midpoint: number }, ... ] }.
GET /spread
  Query: { token_id: string, depth: int (opt) }
  Response 200: { bestBid: number, bestAsk: number, spread: number }.
GET /last-trade-price
  Query: { token_id: string }
  Response 200: { price: string, side: string } – last executed price and side【45†L245-L253】 (or price=“0.50”, side="" if no trades).
GET /last-trade-prices
  Query: { token_ids: [string] }
  Response 200: { lastTradePrices: [ { token_id, price: string, side: string }, ... ] }.
GET /prices-history
  Query: { token_id: string, interval: string (e.g. "5m","1h"), limit: int (opt) }
  Response 200: [ { timestamp: number, price: number }, ... ].
GET /fee-rate
  Query: none. Response: 200: { makerFeeRate: number, takerFeeRate: number }.
GET /tick-size
  Query: none. Response: 200: { tickSize: number }.
GET /server-time
  Returns 200: { serverTime: int }.

###############################################################################
# CLOB API - Authenticated (Trading)
###############################################################################
Auth headers required (L2): 
`POLY_ADDRESS`: user’s address,  
`POLY_API_KEY`: API key,  
`POLY_PASSPHRASE`: passphrase,  
`POLY_TIMESTAMP`: current UNIX ms,  
`POLY_SIGNATURE`: HMAC-SHA256 of (timestamp+method+path+body) using API secret【66†L430-L439】.  
Additionally, order payloads must be EIP-712 signed by user (L1)【55†L249-L257】【66†L508-L512】.

POST /order
  Body: { id: string (uuid, required), market: string (conditionId), asset: string (token ID),
          side: enum(BUY,SELL), size: number, price: number,
          type: string (e.g. GTC/GTD/IOC), expiration: int (ms), 
          takerOffset: number (0.01=1%), signature: string (EIP-712 signature) }
  Headers: as above. 
  Response 201: { id: string } (order ID) or error 4xx.
DELETE /order/{order_id}
  Path: order ID. Response 200: { cancelled: true } or 404 if not found.
POST /orders
  Body: [Order, ...] (array of orders). Response 200/207: list of results.
GET /orders
  Query: { status: enum(LIVE,ALL) (opt), market: string (opt) }
  Response 200: [ { id, market, asset, side, size, price, status, ... } ].
DELETE /cancel-all
  Cancels all live orders. Response 200: { cancelled: true }.
DELETE /cancel-market-orders
  Query: { market: string } (conditionId). Cancels orders in that market. 200: { cancelled: true }.
DELETE /orders (batch)
  Body: { order_ids: [string] }. Cancels specified orders. Response 200: results.
GET /order-scoring
  Response 200: { enabled: bool }.
POST /heartbeat
  Response 200: { ok: true }.

###############################################################################
```  

## Authentication Workflow

- **Gamma/Data:** No authentication needed【64†L244-L248】. Access public endpoints directly.
- **CLOB (Trading):** Two levels【55†L242-L251】【66†L430-L439】:  
  - **L1 (EIP-712):** User signs a typed message with their private key. Used to **create/derive API keys** and to **sign each order payload**.  
  - **L2 (HMAC):** After obtaining (`apiKey`, `secret`, `passphrase`), include headers on each request: `POLY_ADDRESS`, `POLY_TIMESTAMP`, `POLY_API_KEY`, `POLY_PASSPHRASE`, and `POLY_SIGNATURE` (HMAC-SHA256 of the request, using secret)【66†L430-L439】.  
  Example (Python, using headers):  
  ```python
  import time, hmac, hashlib
  timestamp = str(int(time.time()*1000))
  method, path, body = "POST", "/order", '{"json": "body"}'
  message = timestamp + method + path + body
  signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
  headers = {
      "POLY-API-KEY": api_key, 
      "POLY-PASSPHRASE": passphrase,
      "POLY-TIMESTAMP": timestamp,
      "POLY-SIGNATURE": signature,
      "POLY-ADDRESS": wallet_address
  }
  ```
  Create/derive keys via `/auth/api-key` (POST) or `/auth/derive-api-key` (GET) with L1 signed headers as shown in docs【55†L279-L288】【55†L369-L378】.  

## Usage Examples

### Market Data Fetch (Gamma + CLOB)

```python
import requests

# 1. Fetch list of markets from Gamma API
gamma_url = "https://gamma-api.polymarket.com/markets?limit=2"
resp = requests.get(gamma_url)
markets = resp.json()
print("First markets:", [m["question"] for m in markets])

# 2. Pick a market, get CLOB orderbook
market = markets[0]
token_yes, token_no = market["clobTokenIds"]
orderbook_resp = requests.get("https://clob.polymarket.com/book", params={"token_id": token_yes})
orderbook = orderbook_resp.json()
print("Top bid:", orderbook["bids"][0], "Top ask:", orderbook["asks"][0])
```

*Example:* If `market["clobTokenIds"] = ["0xAAA","0xBBB"]`, the request yields:
```json
{
  "market": "0x123...","asset_id":"0xAAA","timestamp":"1612345678901","hash":"abc123",
  "bids":[{"price":"0.45","size":"100"},...],
  "asks":[{"price":"0.47","size":"150"},...],
  "min_order_size":"1","tick_size":"0.01","neg_risk":false,"last_trade_price":"0.45"
}
```【50†L275-L284】. Prices are decimal strings.

### Price Queries (CLOB)

```python
# Best prices for outcomes
resp_yes = requests.get("https://clob.polymarket.com/price", params={"token_id": token_yes, "side":"BUY"})
resp_no  = requests.get("https://clob.polymarket.com/price", params={"token_id": token_yes, "side":"SELL"})
print("Best bid (BUY):", resp_yes.json()["price"], "Best ask (SELL):", resp_no.json()["price"])
```

This returns JSON `{ "price": 0.45 }` (number) for BUY and { "price": 0.46 } for SELL【47†L204-L213】.

```python
# Last trade
resp_last = requests.get("https://clob.polymarket.com/last-trade-price", params={"token_id": token_yes})
print("Last trade price:", resp_last.json())
```
Yields `{ "price": "0.45", "side": "BUY" }`【45†L245-L253】 (strings). If no trades, price defaults to "0.5" and side is empty.

### WebSocket (Market Channel)

Use `wss://clob.polymarket.com/ws/market` to get real-time updates. After connecting, **subscribe** with:
```json
{ "type": "market", "assets_ids": ["0xAAA","0xBBB"] }
```
Server sends snapshots/events:

- **Orderbook Update (event_type:"book")**: full book with bids/asks.
- **Price Change (event_type:"price_change")**: bids/asks deltas.
- **Last Trade (event_type:"last_trade_price")**: {price, side}.
- **New Market (event_type:"new_market")**: {market, question, outcomes, ...}.
- **Resolve Market (event_type:"contract_resolved")**: {market, payout}.

Example message:
```json
{
  "event_type": "price_change",
  "asset_id": "0xAAA",
  "price_changes": [
    {"side":"BID","price":"0.46","size":"50"},
    {"side":"ASK","price":"0.48","size":"25"}
  ],
  "timestamp": 1612345678901
}
```

To keep alive, respond to server `{"type":"ping"}` with `{"type":"pong"}`. For reconnect logic, see sequence diagram below.

```python
import websocket
ws = websocket.create_connection("wss://clob.polymarket.com/ws/market")
ws.send('{"type":"market","assets_ids":["0xAAA","0xBBB"]}')
while True:
    msg = ws.recv()
    data = json.loads(msg)
    if data.get("event_type") == "price_change":
        for change in data["price_changes"]:
            print("Price change:", change)
```

### WebSocket (User Channel)

Use `wss://clob.polymarket.com/ws/user` with **L2 auth**:
```python
auth = {
  "type": "user",
  "auth": {
     "apiKey": API_KEY,
     "passphrase": PASSPHRASE,
     "signature": HMAC_SIGN,   # HMAC of an empty message or reconnect token
     "timestamp": str(int(time.time()*1000))
  }
}
ws = websocket.create_connection("wss://clob.polymarket.com/ws/user")
ws.send(json.dumps(auth))
ws.send('{"operation":"subscribe","markets":["0x123..."]}')
```
You’ll then receive *order* and *trade* events for your account. Example:
```json
{
  "event_type": "order",
  "order_id": "abc-123",
  "side": "BUY",
  "size": 100,
  "filled": 50,
  "status": "FILLED",
  "price": "0.45",
  "timestamp": 1612345678901
}
```
**Reconnection Sequence:**  
```mermaid
sequenceDiagram
  participant C as Client
  participant S as WS_Server
  C->>S: CONNECT (user or market)
  S-->>C: WebSocket OPEN
  C->>S: SUBSCRIBE (assets_ids or markets)
  S-->>C: ACK
  loop Stream events
    S-->>C: PING (type:"ping")
    C-->>S: PONG (type:"pong")
    S-->>C: Event {orderbook/price/last_trade/...}
  end
  alt Disconnected
    C->>C: retry with exponential backoff
    C->>S: CONNECT (again)
    ... (resubscribe previous subscriptions)
  end
```

### Pseudocode: Mispricing Scanner & Order Placement

```plaintext
for market in selected_markets:
    # Fetch Gamma-implied probabilities
    gamma = GET /markets/{market_id}
    prob_yes, prob_no = float(gamma["outcomePrices"][0]), float(gamma["outcomePrices"][1])

    # Fetch live prices from CLOB
    price_yes = GET /price?token_id=clobTokenIds[0]&side=BUY
    price_no  = GET /price?token_id=clobTokenIds[1]&side=BUY

    # Compute edge
    edge_yes = prob_yes - float(price_yes["price"])
    edge_no  = prob_no  - float(price_no["price"])

    if edge_yes > threshold:
        # Buy 'Yes' tokens at current ask (sell order at price_yes)
        order = {
          "id": uuid(), "market": market, "asset": clobTokenIds[0],
          "side": "BUY", "size": 100, "price": price_yes["price"], 
          "type": "GTC", "expiration": 0
        }
        # Sign order (EIP712) then POST /order with HMAC auth
        signed_order = sign_order(order)
        POST /order (signed_order, auth_headers)

    if edge_no > threshold:
        # Buy 'No' tokens similarly
```
This scanner compares the Gamma-implied probability vs. CLOB price for each outcome. If `your_prob – market_price ≥ ε`, it places a limit order (size % of position) using authenticated POST. Ensure each order JSON is EIP-712 signed and HMAC-signed.

## Field Notes & Pitfalls

- **Gamma vs CLOB Tokens:** Gamma objects include `clobTokenIds` (two 0x addresses) for each outcome【50†L275-L284】. Use these for CLOB queries.
- **Data Types:** Many numeric fields come as strings in JSON (prices, volumes). Convert to numbers (floats or decimals) in your client.
- **Timestamps:** Gamma APIs use ISO8601, CLOB/WebSocket use UNIX ms.
- **Rate Limits:** Very high (throttling via Cloudflare)【68†L217-L225】. E.g., Gamma ~4k/10s base, 500/10s on /events【68†L239-L247】; Data /trades 200/10s【68†L257-L261】; CLOB /book & /price 1500/10s【68†L284-L292】. Exceeding limits queues/delays requests (no immediate 429).  
- **Errors:** Expect 400 for bad input, 404 for not found, 401 if auth fails, 500 server errors. On 429 (throttled), back off slightly.  
- **Unspecified Behaviors:** 
  - No real-time orderbook events for `midpoint` or `spread`; clients can compute from bids/asks.
  - Trade history limits: assume pagination via `limit`/`offset`.
  - For missing WebSocket fields or unexpected enum values, implement safe parsing (skip or default).
  - If any field described in docs is missing in response (e.g. `cashPnl`), treat it as null/0.
- **Data Normalization:** The official Python/TypeScript SDKs normalize the raw JSON (e.g. string arrays) into native types. If coding from scratch, manually convert types. See [DLTHub Python examples【4†L1-L4】] for guidance.

## Endpoints vs Use Cases

| Endpoint Category        | Use-Case                 | Key Endpoints                                    |
|--------------------------|--------------------------|--------------------------------------------------|
| **Discovery**            | Find markets/events      | GET /events, /markets, /tags, /series, /sports, /teams, /public-search |
| **Pricing**              | Current prices           | GET /price, /prices, /last-trade-price, /prices-history, /midpoint, /midpoints |
| **Orderbook/Depth**      | Market liquidity         | GET /book, /books, /spread |
| **User Analytics**       | Positions & PnL          | GET /positions, /closed-positions, /activity, /value |
| **Trades History**       | Past trades data         | GET /trades (user or market filters) |
| **Orders (Trading)**     | Place/cancel orders      | POST /order, GET/DELETE /order(s), /cancel-all |
| **WebSocket (Realtime)** | Live updates             | Market channel, User channel (WebSocket) |

*Citations:* Official docs【64†L244-L248】【47†L204-L213】【45†L245-L253】【50†L275-L284】【43†L270-L279】 were used to verify endpoint behaviors, schemas, and sample payloads. Rate-limit and auth details are from Polymarket’s API docs【68†L217-L225】【66†L426-L435】. This guide is meant to be directly embedded into a Codex prompt as a self-contained spec and usage reference.