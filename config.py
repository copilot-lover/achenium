import os
from dataclasses import dataclass


@dataclass
class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1")

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


settings = Settings()
