# Achenium

Flask + HTMX quant-research assistant that is beginner-usable.

## Features
- AI market suggestions (user picks manually; no auto-add).
- OpenAI deep research for selected markets.
- Suggested pick + confidence + risk output.
- Daily AI research job.
- Pre-close monitoring job every N hours (default 5h) inside close window (default 24h).
- Single daily digest email pipeline.
- Web UI accessible by host IP/port (`HOST=0.0.0.0`, `PORT=5000` by default).

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://<server-ip>:5000`

## Environment Variables
- `OPENAI_API_KEY` (optional; fallback mode works without it)
- `OPENAI_MODEL` (default: `gpt-4.1`)
- `PRE_CLOSE_WINDOW_HOURS` (default: `24`)
- `PRE_CLOSE_CHECK_INTERVAL_HOURS` (default: `5`)
- `DAILY_RESEARCH_HOUR_UTC` (default: `13`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_SENDER`, `REPORT_RECIPIENT`
- `HOST`, `PORT`, `DEBUG`

## Notes
- If SMTP credentials are not set, daily digest generation still runs but email sending is skipped.
- If OpenAI is not configured, a deterministic fallback research report is returned.
