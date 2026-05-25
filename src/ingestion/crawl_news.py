from __future__ import annotations

from datetime import datetime, timezone
import logging
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.database import raw_news, upsert_rows
from src.http_client import get_text
from src.processing.clean_text import clean_text, normalize_key

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "VnExpress Sức khỏe": "https://vnexpress.net/rss/suc-khoe.rss",
    "Tuổi Trẻ Sức khỏe": "https://tuoitre.vn/rss/suc-khoe.rss",
    "Thanh Niên Sức khỏe": "https://thanhnien.vn/rss/suc-khoe.rss",
    "Sức khỏe Đời sống": "https://suckhoedoisong.vn/rss/thoi-su-y-te-175.rss",
}
KEYWORDS = ["sốt xuất huyết", "tay chân miệng", "cúm", "sốt rét", "sởi", "thủy đậu", "đau mắt đỏ", "dengue", "hfmd", "influenza"]
MAX_ITEMS_PER_FEED = 25


def _parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def _article_text(url: str) -> str:
    html = get_text(url)
    soup = BeautifulSoup(html, "lxml")
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    return clean_text(" ".join(paragraphs))


def collect_news(session) -> int:
    rows: list[dict] = []
    for source_name, feed_url in RSS_FEEDS.items():
        try:
            soup = BeautifulSoup(get_text(feed_url), "xml")
            for item in soup.find_all("item")[:MAX_ITEMS_PER_FEED]:
                title = clean_text(item.title.get_text(" ", strip=True) if item.title else "")
                description = clean_text(item.description.get_text(" ", strip=True) if item.description else "")
                link = item.link.get_text(strip=True) if item.link else ""
                link = urljoin(feed_url, link)
                searchable = normalize_key(f"{title} {description}")
                if not link:
                    continue
                try:
                    content = _article_text(link)
                except Exception as exc:
                    logger.warning("Cannot fetch article %s: %s", link, exc)
                    content = description
                searchable = normalize_key(f"{title} {description} {content}")
                if not any(normalize_key(keyword) in searchable for keyword in KEYWORDS):
                    continue
                rows.append(
                    {
                        "source_name": source_name,
                        "source_url": link,
                        "title": title,
                        "published_at": _parse_published(item.pubDate.get_text(strip=True) if item.pubDate else None),
                        "content": content or description or title,
                        "collected_at": datetime.utcnow(),
                    }
                )
        except Exception as exc:
            logger.warning("Cannot collect RSS feed %s: %s", feed_url, exc)
    count = upsert_rows(session, raw_news, rows, ["source_url"])
    logger.info("Collected %s news rows", count)
    return count
