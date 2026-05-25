from __future__ import annotations

import logging

import requests

from src.config import settings

logger = logging.getLogger(__name__)


def send_telegram(message: str) -> tuple[bool, str]:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False, "telegram_not_configured"
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
            json={"chat_id": settings.telegram_chat_id, "text": message},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        return True, response.text[:500]
    except Exception as exc:
        logger.warning("Telegram alert failed: %s", exc)
        return False, str(exc)
