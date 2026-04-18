# Setup and Environment Configuration

This document explains how to configure environment variables, run Achenium locally, and troubleshoot scheduler/API setup.

## 1) Environment variables

Achenium reads all runtime configuration from environment variables in `config.py`.

### Required for app startup

These have safe defaults, so the app can start without extra configuration:

- `SECRET_KEY` (default: `dev-secret` in code; set a real secret outside local dev)
- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `5000`)
- `DEBUG` (default: `false`)
- `DB_PATH` (default: `achenium.db`)

### Optional: OpenAI deep research

If `OPENAI_API_KEY` is unset, the app falls back to deterministic research output.

- `OPENAI_API_KEY` (optional)
- `OPENAI_MODEL` (default: `gpt-4.1`)
- `OPENAI_TIMEOUT_SECONDS` (default: `25`)
- `OPENAI_REQUESTS_PER_MINUTE` (default: `20`)

### Optional: Scheduler tuning

These control internal APScheduler jobs:

- `DAILY_RESEARCH_HOUR_UTC` (default: `13`, expected range `0-23`)
- `PRE_CLOSE_WINDOW_HOURS` (default: `24`)
- `PRE_CLOSE_CHECK_INTERVAL_HOURS` (default: `5`)
- `MAX_SELECTED_MARKETS` (default: `8`)

### Optional: Email digest delivery

Email sending is skipped unless **all required SMTP fields** are set.

- `SMTP_HOST` (**required if enabling email**)
- `SMTP_PORT` (default: `587`)
- `SMTP_USER` (**required if enabling email**)
- `SMTP_PASSWORD` (**required if enabling email**)
- `SMTP_SENDER` (default: `noreply@local`)
- `REPORT_RECIPIENT` (**required if enabling email**)

### Optional: Polymarket configuration

- `POLYMARKET_TIMEOUT_SECONDS` (default: `10`)
- `POLY_ADDRESS` (required only for authenticated CLOB usage)
- `POLY_API_KEY` (required only for authenticated CLOB usage)
- `POLY_API_SECRET` (required only for authenticated CLOB usage)
- `POLY_PASSPHRASE` (required only for authenticated CLOB usage)

> Note: Public/suggestion data paths can still work without authenticated Polymarket credentials depending on endpoint usage.

---

## 2) Local run steps

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create local env file:

   ```bash
   cp .env.example .env
   ```

4. Update `.env` with any keys you want enabled (OpenAI, SMTP, Polymarket auth).

5. Run the app:

   ```bash
   python app.py
   ```

6. Open:

   - `http://127.0.0.1:5000` (same machine)
   - `http://<your-host-ip>:5000` (LAN, if allowed by firewall/network)

---

## 3) Scheduler and API troubleshooting

### Scheduler appears not to run

- Confirm the app process is running continuously (scheduler is in-process; jobs stop when app stops).
- Check `/health` and verify `scheduler_running` is `true`.
- Ensure `DAILY_RESEARCH_HOUR_UTC` is an integer `0-23`.
- Verify `PRE_CLOSE_CHECK_INTERVAL_HOURS` is a positive integer.

### No OpenAI-generated research

- Confirm `OPENAI_API_KEY` is set correctly in `.env`.
- Check `OPENAI_TIMEOUT_SECONDS` isn’t too low for your network.
- If rate-limited, reduce request frequency or increase `OPENAI_REQUESTS_PER_MINUTE` carefully.
- If key is missing/invalid, fallback mode is expected behavior.

### Digest emails not being sent

- Ensure all required SMTP variables are set: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `REPORT_RECIPIENT`.
- Confirm `SMTP_PORT` matches your provider (`587` for STARTTLS is common).
- Verify credentials and sender policy for `SMTP_SENDER`.
- Check app logs for SMTP authentication or connection errors.

### Polymarket auth issues

- Authenticated CLOB calls require all four values:
  `POLY_ADDRESS`, `POLY_API_KEY`, `POLY_API_SECRET`, `POLY_PASSPHRASE`.
- Validate there are no extra spaces/newlines in credential values.
- Confirm system clock is accurate; timestamp drift can break signed requests.
- Increase `POLYMARKET_TIMEOUT_SECONDS` if requests are timing out.

### Database/path issues

- Ensure the app can write to the directory containing `DB_PATH`.
- If resetting local state is needed, stop the app and remove the DB file, then restart.

