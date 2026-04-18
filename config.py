"""Application configuration loaded from environment variables."""

import logging
import os
from dataclasses import dataclass


logger = logging.getLogger(__name__)


def _parse_int_env(
    name: str,
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Parse integer env var with fallback default and optional bounds."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid integer for %s=%r; using default %s",
            name,
            raw_value,
            default,
        )
        return default

    if min_value is not None and value < min_value:
        logger.warning(
            "Integer for %s=%s is below minimum %s; using default %s",
            name,
            value,
            min_value,
            default,
        )
        return default
    if max_value is not None and value > max_value:
        logger.warning(
            "Integer for %s=%s exceeds maximum %s; using default %s",
            name,
            value,
            max_value,
            default,
        )
        return default
    return value


def _parse_bool_env(name: str, default: bool) -> bool:
    """Parse boolean env var with fallback default."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    value = raw_value.strip().lower()
    true_values = {"1", "true", "t", "yes", "y", "on"}
    false_values = {"0", "false", "f", "no", "n", "off"}
    if value in true_values:
        return True
    if value in false_values:
        return False

    logger.warning(
        "Invalid boolean for %s=%r; using default %s",
        name,
        raw_value,
        default,
    )
    return default


@dataclass
class Settings:
    """Runtime settings for Flask app, jobs, storage, and integrations."""

    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
    openai_timeout_seconds: int = _parse_int_env("OPENAI_TIMEOUT_SECONDS", 25, min_value=1)
    openai_requests_per_minute: int = _parse_int_env("OPENAI_REQUESTS_PER_MINUTE", 20, min_value=1)

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = _parse_int_env("PORT", 5000, min_value=1, max_value=65535)
    debug: bool = _parse_bool_env("DEBUG", False)

    pre_close_window_hours: int = _parse_int_env("PRE_CLOSE_WINDOW_HOURS", 24, min_value=1)
    pre_close_check_interval_hours: int = _parse_int_env("PRE_CLOSE_CHECK_INTERVAL_HOURS", 5, min_value=1)
    daily_research_hour_utc: int = _parse_int_env("DAILY_RESEARCH_HOUR_UTC", 13, min_value=0, max_value=23)

    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = _parse_int_env("SMTP_PORT", 587, min_value=1, max_value=65535)
    smtp_user: str | None = os.getenv("SMTP_USER")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_sender: str = os.getenv("SMTP_SENDER", "noreply@local")
    report_recipient: str | None = os.getenv("REPORT_RECIPIENT")

    db_path: str = os.getenv("DB_PATH", "achenium.db")

    max_selected_markets: int = _parse_int_env("MAX_SELECTED_MARKETS", 8, min_value=1)


    polymarket_timeout_seconds: int = _parse_int_env("POLYMARKET_TIMEOUT_SECONDS", 10, min_value=1)
    poly_address: str | None = os.getenv("POLY_ADDRESS")
    poly_api_key: str | None = os.getenv("POLY_API_KEY")
    poly_api_secret: str | None = os.getenv("POLY_API_SECRET")
    poly_passphrase: str | None = os.getenv("POLY_PASSPHRASE")


settings = Settings()
