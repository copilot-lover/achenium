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

## Operations runbook

### Verify scheduler status
1. Start the app (`python app.py`) and verify the scheduler starts at boot.
2. Check runtime health:
   ```bash
   curl -s http://127.0.0.1:5000/health | python -m json.tool
   ```
3. Confirm these fields:
   - `"status": "ok"`
   - `"scheduler_running": true`
   - `"scheduler_type": "APScheduler BackgroundScheduler (in-process)"`
4. Verify startup logs include:
   - `APScheduler started (in-process). Jobs are not persisted across restarts.`

If `scheduler_running` is `false`, restart the process and re-check `/health`. Because jobs are in-process, scheduler state resets on each app restart.

### Inspect report storage
Reports are persisted in SQLite at `DB_PATH` (default `achenium.db`) in table `reports` (`created_at`, `report_type`, `payload` JSON text).

Quick inspection commands:

```bash
# Show newest 20 reports
sqlite3 "${DB_PATH:-achenium.db}" \
  "SELECT id, created_at, report_type, substr(payload,1,160) FROM reports ORDER BY id DESC LIMIT 20;"

# Count report volume by type
sqlite3 "${DB_PATH:-achenium.db}" \
  "SELECT report_type, COUNT(*) FROM reports GROUP BY report_type ORDER BY COUNT(*) DESC;"

# Review job failures only
sqlite3 "${DB_PATH:-achenium.db}" \
  "SELECT created_at, payload FROM reports WHERE report_type='job_error' ORDER BY created_at DESC LIMIT 20;"
```

### Recover from failed jobs
`safe_*` scheduler wrappers catch exceptions and write `report_type=job_error` entries instead of crashing the scheduler process.

Recovery workflow:
1. Identify failing job(s) from `job_error` rows in `reports`.
2. Fix root cause (common examples):
   - Missing API credentials in environment.
   - SMTP misconfiguration for digest delivery.
   - Temporary network/provider failures.
3. Restart the application so APScheduler re-registers all jobs.
4. Validate with `/health` (`scheduler_running: true`).
5. Confirm new `job_status`, `preclose_monitor`, or `daily_digest` rows appear and no new `job_error` rows are created.

Notes:
- `daily_research` runs at `DAILY_RESEARCH_HOUR_UTC`.
- `preclose_monitor` runs every `PRE_CLOSE_CHECK_INTERVAL_HOURS`.
- `daily_digest` runs one hour after `DAILY_RESEARCH_HOUR_UTC`.

### Rotate API credentials safely
Use a staged rotation to avoid downtime for OpenAI, Polymarket, and SMTP credentials:

1. **Create new credentials** in the provider console(s); keep old credentials active during overlap.
2. **Update runtime secret source** (for example: `.env`, systemd env file, container secret manager):
   - `OPENAI_API_KEY`
   - `POLY_API_KEY`, `POLY_API_SECRET`, `POLY_PASSPHRASE`, `POLY_ADDRESS`
   - `SMTP_USER`, `SMTP_PASSWORD`
3. **Restart app process** to load new environment variables.
4. **Smoke test immediately**:
   - `GET /health`
   - Trigger a manual research request in UI
   - Confirm no new `job_error` records in SQLite
5. **Revoke old credentials** only after successful validation.
6. **Audit and cleanup**:
   - Ensure rotated secrets are not committed to git.
   - Remove obsolete secrets from local shell history or temporary files.

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

## Suggested next steps
- Add unit/integration tests.
- Add Dockerfile + production WSGI setup.
- Consider persistent scheduler backend or task queue for multi-worker deployment.
- Add structured logging/tracing.
