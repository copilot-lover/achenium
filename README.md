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
- A lightweight migration directory exists at `migrations/` with `0001_initial_schema.sql` for preparatory/manual use.
- Migration execution is not wired into app startup yet.
- To reset the DB, stop app and remove the database file configured by `DB_PATH`.

## Error handling UX
- UI routes return user-visible error messages on failures.
- OpenAI failures/timeouts/rate-limit fallback to deterministic research output.
- Scheduler job errors are logged and recorded in `reports` with `report_type=job_error`.

## Suggested next steps
- Add unit/integration tests.
- Add Dockerfile + production WSGI setup.
- Consider persistent scheduler backend or task queue for multi-worker deployment.
- Add structured logging/tracing.
