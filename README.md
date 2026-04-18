# Achenium

Flask + HTMX quant-research assistant that is beginner-usable and configurable for deeper quant workflows.

## What this includes
- Suggest markets first, then require explicit user selection (no auto-add).
- OpenAI deep research for selected markets with graceful fallback mode.
- Polymarket integration using the local API contract in `API-KEY-DOCS.md` (Gamma/Data/CLOB + auth header support).
- Suggested pick + confidence + risk output for each selected market.
- Daily AI research job.
- Pre-close monitoring job every N hours (default 5h) inside a close window (default 24h).
- One consolidated daily digest email pipeline.
- Web UI accessible by host IP/port (`HOST=0.0.0.0`, `PORT=5000` by default).

## Project layout
```text
achenium/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── services/
│   ├── jobs.py
│   ├── openai_service.py
│   ├── research.py
│   └── storage.py
├── templates/
└── static/
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open: `http://<server-ip>:5000`

## Security and secrets
- Never commit secrets.
- Place API keys and SMTP credentials in `.env` or process environment.
- `.env` is git-ignored.

## Environment variables
- `OPENAI_API_KEY` (optional; fallback mode works without it)
- `OPENAI_MODEL` (default `gpt-4.1`)
- `OPENAI_TIMEOUT_SECONDS` (default `25`)
- `OPENAI_REQUESTS_PER_MINUTE` (default `20`, in-process limiter)
- `PRE_CLOSE_WINDOW_HOURS` (default `24`)
- `PRE_CLOSE_CHECK_INTERVAL_HOURS` (default `5`)
- `DAILY_RESEARCH_HOUR_UTC` (default `13`)
- `MAX_SELECTED_MARKETS` (default `8`)
- `DB_PATH` (default `achenium.db`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_SENDER`, `REPORT_RECIPIENT`
- `HOST`, `PORT`, `DEBUG`
- `POLYMARKET_TIMEOUT_SECONDS` (default `10`)
- `POLY_ADDRESS`, `POLY_API_KEY`, `POLY_API_SECRET`, `POLY_PASSPHRASE` (required for authenticated CLOB trading endpoints)

## Scheduler notes
- Scheduler: `APScheduler` (`BackgroundScheduler`), started in-process with Flask startup.
- This scheduler is suitable for local/dev and simple single-process deployment.
- Scheduled job definitions are re-created on startup and are **not persisted** across app restarts.

## SQLite notes
- Persistence uses raw SQL via `sqlite3` (no ORM yet).
- Schema is auto-initialized at startup by `init_db()` for tables:
  - `trades`
  - `reports`
- To reset the DB, stop app and remove the database file configured by `DB_PATH`.

## Error handling UX
- UI routes return user-visible error messages on failures.
- OpenAI failures/timeouts/rate-limit fallback to deterministic research output.
- Scheduler job errors are logged and recorded in `reports` with `report_type=job_error`.

## HTTP route contract (UI + health endpoints)

The app currently serves HTMX-driven HTML partials for user workflows, plus one JSON health endpoint.

### `POST /suggestions`

**Purpose**
- Generate a curated list of market suggestions based on style preference.

**Payload expectations**
- Content type: `application/x-www-form-urlencoded` (typical HTMX form post).
- Supported field:
  - `style` (optional, string): e.g., `balanced`, `momentum`, etc.
- Defaulting/normalization:
  - Missing `style` defaults to `balanced`.
  - Value is trimmed and lowercased before processing.

**Successful response**
- HTTP `200 OK`
- Returns HTML partial: `templates/partials/suggestions.html`
- Template context:
  - `markets`: list of suggested market objects returned by `suggest_markets(style)`.

**Error behavior**
- HTTP `500 Internal Server Error` for any unhandled backend failure.
- Returns HTML partial: `templates/partials/error.html`
- Error message shown to user:
  - `Could not generate market suggestions right now. Please retry.`

---

### `POST /research`

**Purpose**
- Run deep research across explicitly selected markets and render report cards.

**Payload expectations**
- Content type: `application/x-www-form-urlencoded`.
- Supported fields:
  - `selected_markets` (required list semantics): multi-value form key (e.g., repeated checkboxes).
  - `risk_profile` (optional, string): defaults to `moderate`.
  - `horizon` (optional, string): defaults to `swing`.
- Validation/defaulting:
  - `selected_markets` values are normalized/filtered by `validate_selected_markets(...)`.
  - `risk_profile` and `horizon` are trimmed and lowercased.

**Successful response**
- HTTP `200 OK`
- Returns HTML partial: `templates/partials/reports.html`
- Template context:
  - `outputs`: research result list from `run_deep_research(...)`.

**Error behavior**
- HTTP `400 Bad Request` when no valid market selections remain after validation.
  - Condition A: user submitted no valid selections.
  - Condition B: research pipeline returns no processed outputs.
- For both 400 cases, returns HTML partial: `templates/partials/error.html`
- 400 user-facing messages:
  - `Select at least one valid market.`
  - `No valid markets were processed. Please adjust your selections.`

- HTTP `500 Internal Server Error` for any unhandled runtime failure.
- Returns HTML partial: `templates/partials/error.html`
- 500 user-facing message:
  - `Deep research is temporarily unavailable. The app switched to a safe fallback; try again shortly.`

---

### `GET /health`

**Purpose**
- Lightweight process health probe for app/scheduler status.

**Payload expectations**
- No request body required.

**Successful response**
- HTTP `200 OK`
- Returns JSON object with fields:
  - `status`: `"ok"`
  - `scheduler_running`: boolean (`true` when scheduler exists and is running)
  - `scheduler_type`: `"APScheduler BackgroundScheduler (in-process)"`

**Error behavior**
- No explicit custom error path is implemented in this route.
- Any framework-level or unexpected exception would surface as default Flask 5xx handling.

## Suggested next steps
- Add unit/integration tests.
- Add Dockerfile + production WSGI setup.
- Consider persistent scheduler backend or task queue for multi-worker deployment.
- Add structured logging/tracing.
