from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib

from src.config import settings

logger = logging.getLogger(__name__)


def send_email(subject: str, message: str) -> tuple[bool, str]:
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.alert_email_to]):
        return False, "email_not_configured"
    recipients = _split_recipients(settings.alert_email_to)
    if not recipients:
        return False, "email_recipient_not_configured"

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = settings.alert_email_from or settings.smtp_user
    email["To"] = ", ".join(recipients)
    email.set_content(message)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.request_timeout_seconds) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(email, to_addrs=recipients)
        return True, "sent"
    except Exception as exc:
        logger.warning("Email alert failed: %s", exc)
        return False, str(exc)


def _split_recipients(value: str) -> list[str]:
    return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
