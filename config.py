"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Runtime settings for Flask app, jobs, storage, and integrations."""

    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "25"))
    openai_requests_per_minute: int = int(os.getenv("OPENAI_REQUESTS_PER_MINUTE", "20"))

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    pre_close_window_hours: int = int(os.getenv("PRE_CLOSE_WINDOW_HOURS", "24"))
    pre_close_check_interval_hours: int = int(os.getenv("PRE_CLOSE_CHECK_INTERVAL_HOURS", "5"))
    daily_research_hour_utc: int = int(os.getenv("DAILY_RESEARCH_HOUR_UTC", "13"))

    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str | None = os.getenv("SMTP_USER")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_sender: str = os.getenv("SMTP_SENDER", "noreply@local")
    report_recipient: str | None = os.getenv("REPORT_RECIPIENT")

    db_path: str = os.getenv("DB_PATH", "achenium.db")

    max_selected_markets: int = int(os.getenv("MAX_SELECTED_MARKETS", "8"))


    polymarket_timeout_seconds: int = int(os.getenv("POLYMARKET_TIMEOUT_SECONDS", "10"))
    poly_address: str | None = os.getenv("POLY_ADDRESS")
    poly_api_key: str | None = os.getenv("POLY_API_KEY")
    poly_api_secret: str | None = os.getenv("POLY_API_SECRET")
    poly_passphrase: str | None = os.getenv("POLY_PASSPHRASE")


settings = Settings()
