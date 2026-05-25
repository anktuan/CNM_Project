from __future__ import annotations

from io import BytesIO
import logging

import requests

from src.config import settings

logger = logging.getLogger(__name__)


def extract_image_text(url: str) -> str:
    if not settings.ocr_enabled:
        return ""
    try:
        import pytesseract
        from PIL import Image

        response = requests.get(url, timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return pytesseract.image_to_string(image, lang="vie+eng").strip()
    except Exception as exc:
        logger.warning("OCR failed for %s: %s", url, exc)
        return ""
