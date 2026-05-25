from __future__ import annotations

from datetime import date, datetime, time
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.database import raw_news, upsert_rows
from src.http_client import get_text
from src.ingestion.ocr import extract_image_text
from src.processing.clean_text import clean_text, normalize_key

logger = logging.getLogger(__name__)

BASE_URL = "https://hcdc.vn"
SEED_URLS = [
    "https://hcdc.vn/category/van-de-suc-khoe/tay-chan-mieng/pages-4",
    "https://hcdc.vn/category/van-de-suc-khoe/sot-xuat-huyet/pages-4",
]
KEYWORDS = ["tình hình dịch bệnh", "sốt xuất huyết", "tay chân miệng", "cúm"]


def _discover_links() -> list[str]:
    links: set[str] = set()
    for seed in SEED_URLS:
        try:
            soup = BeautifulSoup(get_text(seed), "lxml")
            for anchor in soup.find_all("a", href=True):
                url = urljoin(BASE_URL, anchor["href"])
                text = normalize_key(anchor.get_text(" ", strip=True) + " " + url)
                if "hcdc.vn" in url and url.endswith(".html") and any(normalize_key(k) in text for k in KEYWORDS):
                    links.add(url)
        except Exception as exc:
            logger.warning("Cannot discover HCDC links from %s: %s", seed, exc)
    return sorted(links)


def collect_hcdc(session, limit: int = 30) -> int:
    rows: list[dict] = []
    for link in _discover_links()[:limit]:
        try:
            soup = BeautifulSoup(get_text(link), "lxml")
            title = clean_text(soup.find(["h1", "h2"]).get_text(" ", strip=True) if soup.find(["h1", "h2"]) else link)
            content = clean_text(" ".join(p.get_text(" ", strip=True) for p in soup.find_all("p")))
            ocr_text = _extract_article_image_text(soup, link)
            if ocr_text:
                content = clean_text(f"{content} {ocr_text}")
            if not content:
                continue
            rows.append(
                {
                    "source_name": "HCDC",
                    "source_url": link,
                    "title": title,
                    "published_at": _parse_hcdc_date(soup, title, content),
                    "content": content,
                    "collected_at": datetime.utcnow(),
                }
            )
        except Exception as exc:
            logger.warning("Cannot collect HCDC article %s: %s", link, exc)
    count = upsert_rows(session, raw_news, rows, ["source_url"])
    logger.info("Collected %s HCDC rows", count)
    return count


def _extract_article_image_text(soup: BeautifulSoup, article_url: str) -> str:
    texts = []
    for image in soup.find_all("img", src=True)[:5]:
        image_url = urljoin(article_url, image["src"])
        text = extract_image_text(image_url)
        if text:
            texts.append(text)
    return "\n".join(texts)


def _parse_hcdc_date(soup: BeautifulSoup, title: str, content: str) -> datetime | None:
    for selector in [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "pubdate"}),
        ("meta", {"name": "publishdate"}),
    ]:
        tag = soup.find(*selector)
        value = tag.get("content") if tag else None
        parsed = _parse_datetime_value(value)
        if parsed:
            return parsed

    time_tag = soup.find("time")
    if time_tag:
        parsed = _parse_datetime_value(time_tag.get("datetime") or time_tag.get_text(" ", strip=True))
        if parsed:
            return parsed

    searchable = clean_text(f"{title}. {content[:800]}")
    date_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", searchable)
    if date_match:
        day, month, year = map(int, date_match.groups())
        try:
            return datetime.combine(date(year, month, day), time.min)
        except ValueError:
            pass

    week_match = re.search(r"tuan\s+(\d{1,2})\s*/\s*(20\d{2})|tuan\s+(\d{1,2}).{0,20}(20\d{2})", normalize_key(searchable))
    if week_match:
        week = int(week_match.group(1) or week_match.group(3))
        year = int(week_match.group(2) or week_match.group(4))
        try:
            return datetime.combine(date.fromisocalendar(year, week, 7), time.min)
        except ValueError:
            return None

    return None


def _parse_datetime_value(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", value)
    if match:
        day, month, year = map(int, match.groups())
        try:
            return datetime.combine(date(year, month, day), time.min)
        except ValueError:
            return None
    return None
