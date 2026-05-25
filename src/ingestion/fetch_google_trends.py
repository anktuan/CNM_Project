from __future__ import annotations

from datetime import datetime
import logging
import time

import pandas as pd

from src.database import google_trends, upsert_rows

logger = logging.getLogger(__name__)

TREND_QUERIES = [
    {"disease": "Sốt xuất huyết", "keyword": "Sốt xuất huyết (bệnh)", "query": "/m/02cl6", "fallback_query": "sốt xuất huyết"},
    {"disease": "Sốt xuất huyết", "keyword": "sốt xuất huyết", "query": "sốt xuất huyết"},
    {"disease": "Tay chân miệng", "keyword": "Tay chân miệng (bệnh)", "query": "/m/03b_07", "fallback_query": "tay chân miệng"},
    {"disease": "Tay chân miệng", "keyword": "tay chân miệng", "query": "tay chân miệng"},
    {"disease": "Tay chân miệng", "keyword": "thuốc bôi tay chân miệng", "query": "thuốc bôi tay chân miệng"},
    {"disease": "Cúm", "keyword": "cúm A", "query": "cúm A"},
    {"disease": "Cúm", "keyword": "cúm B", "query": "cúm B"},
    {"disease": "Cúm", "keyword": "influenza", "query": "influenza"},
    {"disease": "Sốt rét", "keyword": "sốt rét", "query": "sốt rét"},
    {"disease": "Sởi", "keyword": "sởi", "query": "sởi"},
    {"disease": "Thủy đậu", "keyword": "thủy đậu", "query": "thủy đậu"},
    {"disease": "Đau mắt đỏ", "keyword": "đau mắt đỏ", "query": "đau mắt đỏ"},
]


def collect_google_trends(session) -> int:
    try:
        from pytrends.request import TrendReq
    except Exception as exc:
        logger.warning("pytrends is unavailable: %s", exc)
        return 0

    rows: list[dict] = []
    pytrend = TrendReq(hl="vi-VN", tz=-420, timeout=(10, 25))
    query_map: dict[str, list[dict]] = {}
    for item in TREND_QUERIES:
        active_query = item.get("fallback_query") if str(item["query"]).startswith("/") else item["query"]
        query_map.setdefault(str(active_query), []).append(item)

    for query_batch in _chunks(list(query_map), 5):
        try:
            rows.extend(_fetch_batch(pytrend, query_batch, query_map))
            time.sleep(6)
        except Exception as exc:
            logger.warning("Cannot collect Google Trends batch %s: %s", query_batch, exc)
            for query in query_batch:
                try:
                    rows.extend(_fetch_batch(pytrend, [query], query_map))
                    time.sleep(6)
                except Exception as item_exc:
                    for item in query_map[query]:
                        logger.warning(
                            "Cannot collect Google Trends for %s/%s: %s",
                            item["disease"],
                            item["keyword"],
                            item_exc,
                        )
    count = upsert_rows(session, google_trends, rows, ["date", "disease", "keyword", "geo"])
    logger.info("Collected %s Google Trends rows", count)
    return count


def _fetch_batch(pytrend, queries: list[str], query_map: dict[str, list[dict]]) -> list[dict]:
    pytrend.build_payload(kw_list=queries, geo="VN", timeframe="today 1-m")
    df = pytrend.interest_over_time()
    if df.empty:
        return []
    df = df.reset_index()
    rows: list[dict] = []
    collected_at = datetime.utcnow()
    for query in queries:
        if query not in df:
            continue
        signal = pd.to_numeric(df[query], errors="coerce").fillna(0)
        smoothed = signal.rolling(window=7, min_periods=1).mean()
        for item in query_map[query]:
            for date_value, raw_score, trend_score in zip(df["date"], signal, smoothed):
                rows.append(
                    {
                        "date": date_value.date(),
                        "disease": item["disease"],
                        "keyword": item["keyword"],
                        "geo": "VN",
                        "trend_score": float(trend_score),
                        "trend_score_raw": float(raw_score),
                        "collected_at": collected_at,
                    }
                )
    return rows


def _chunks(values: list[str], size: int):
    for idx in range(0, len(values), size):
        yield values[idx : idx + size]
