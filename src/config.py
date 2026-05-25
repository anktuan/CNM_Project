from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def first_non_empty(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://atuans_admin:atuans2026@localhost:5432/cnm_disease_db",
    )
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    request_retries: int = int(os.getenv("REQUEST_RETRIES", "3"))
    scheduler_interval_minutes: int = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))
    dashboard_refresh_seconds: int = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "300"))
    realtime_lookback_days: int = int(os.getenv("REALTIME_LOOKBACK_DAYS", "14"))
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    email_user: str = first_non_empty("EMAIL_USER", "SMTP_USER")
    email_password: str = first_non_empty("EMAIL_PASSWORD", "SMTP_PASSWORD")
    smtp_host: str = first_non_empty("SMTP_HOST", "EMAIL_HOST", default="smtp.gmail.com" if first_non_empty("EMAIL_USER", "SMTP_USER") else "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = first_non_empty("SMTP_USER", "EMAIL_USER")
    smtp_password: str = first_non_empty("SMTP_PASSWORD", "EMAIL_PASSWORD")
    alert_email_to: str = first_non_empty("ALERT_EMAIL_TO", "EMAIL_TO", "EMAIL_USER", "SMTP_USER")
    alert_email_from: str = first_non_empty("ALERT_EMAIL_FROM", "EMAIL_USER", "SMTP_USER")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    tavily_api_key: str = first_non_empty("TAVILY_API_KEY", "TAVITY_API_KEY")
    ocr_enabled: bool = os.getenv("OCR_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


settings = Settings()
