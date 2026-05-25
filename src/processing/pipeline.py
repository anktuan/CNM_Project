from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from sqlalchemy import and_, extract, func, select

from src.database import extracted_events, google_trends, raw_news, risk_scores, upsert_rows, weather_data
from src.config import settings
from src.processing.extract_entities import extract_events
from src.processing.risk_score import RiskInput, calculate_risk_score, classify_alert, weather_risk_score

logger = logging.getLogger(__name__)


def extract_raw_news_events(session) -> int:
    today = date.today()
    min_event_date = today - timedelta(days=settings.realtime_lookback_days)
    statement = select(raw_news).order_by(raw_news.c.collected_at.desc())
    rows_by_key: dict[tuple, dict] = {}
    for news in session.execute(statement).mappings():
        source_name = news["source_name"]
        confidence = 0.9 if source_name == "HCDC" else 0.6
        events = extract_events(
            f"{news['title']}. {news['content']}",
            default_date=(news["published_at"].date() if news["published_at"] else news["collected_at"].date()),
            source_confidence=confidence,
        )
        for event in events:
            if event.event_date and event.event_date > today:
                continue
            if event.event_date and event.event_date < min_event_date:
                continue
            if event.district == "Việt Nam":
                continue
            if _is_cumulative_text(event.raw_text):
                continue
            row = {
                "event_date": event.event_date,
                "disease": event.disease,
                "district": event.district,
                "cases": event.cases,
                "source_type": "hcdc" if source_name == "HCDC" else "news",
                "source_name": source_name,
                "source_url": news["source_url"],
                "raw_text": event.raw_text,
                "confidence": event.confidence,
                "collected_at": datetime.utcnow(),
            }
            key = (
                row["event_date"],
                row["disease"],
                row["district"],
                row["cases"],
                row["source_url"],
                row["raw_text"],
            )
            rows_by_key[key] = row
    rows = list(rows_by_key.values())
    session.execute(extracted_events.delete())
    if rows:
        session.execute(extracted_events.insert(), rows)
    logger.info("Extracted %s disease events", len(rows))
    return len(rows)


def build_risk_scores(session, score_date: date | None = None) -> int:
    score_date = score_date or date.today()
    since = score_date - timedelta(days=7)
    weather_lag_start = score_date - timedelta(days=17)
    weather_lag_end = score_date - timedelta(days=7)

    event_stmt = (
        select(
            extracted_events.c.disease,
            extracted_events.c.district,
            extracted_events.c.cases,
            extracted_events.c.raw_text,
        )
        .where(
            and_(
                extracted_events.c.event_date >= since,
                extracted_events.c.event_date <= score_date,
                extracted_events.c.district != "Việt Nam",
                extracted_events.c.cases.is_not(None),
            )
        )
    )
    event_rows = list(session.execute(event_stmt).mappings())
    cases_by_key = _cases_by_disease_location(event_rows)
    keys = set(cases_by_key)

    trend_stmt = (
        select(google_trends.c.disease, func.max(google_trends.c.trend_score).label("trend_score"))
        .where(and_(google_trends.c.date >= since, google_trends.c.date <= score_date))
        .group_by(google_trends.c.disease)
    )
    trend_by_disease = {row["disease"]: float(row["trend_score"] or 0) for row in session.execute(trend_stmt).mappings()}

    weather_stmt = (
        select(
            weather_data.c.district,
            func.avg(weather_data.c.temperature_mean).label("temperature_mean"),
            func.sum(weather_data.c.rainfall_mm).label("rainfall_mm"),
            func.avg(weather_data.c.humidity_mean).label("humidity_mean"),
        )
        .where(and_(weather_data.c.date >= weather_lag_start, weather_data.c.date <= weather_lag_end))
        .group_by(weather_data.c.district)
    )
    weather_by_district = {row["district"]: row for row in session.execute(weather_stmt).mappings()}
    baseline_by_key = _baseline_cases_by_disease_location(session, score_date)

    for disease in trend_by_disease:
        keys.add((disease, "TP. Hồ Chí Minh"))
    for key in baseline_by_key:
        if key[0] in trend_by_disease:
            keys.add(key)

    rows: list[dict] = []
    for disease, district in sorted(keys):
        weather = weather_by_district.get(district) or {}
        weather_score = weather_risk_score(
            disease,
            weather.get("rainfall_mm"),
            weather.get("humidity_mean"),
            weather.get("temperature_mean"),
        )
        current_cases = cases_by_key.get((disease, district), 0)
        trend = trend_by_disease.get(disease, 0)
        baseline_cases = baseline_by_key.get((disease, district), 0)
        cases = current_cases or int(round(baseline_cases * (1 + min(trend, 100) / 200))) if baseline_cases else current_cases
        score, components = calculate_risk_score(
            RiskInput(cases_7d=cases, trend_score=trend, weather_score=weather_score, disease=disease),
            baseline_cases=baseline_cases or None,
        )
        level = classify_alert(score)
        if current_cases > 0:
            basis = "case_data"
        elif baseline_cases > 0:
            basis = "baseline_google_trends_weather_fallback"
        else:
            basis = "google_trends_weather_fallback"
        rows.append(
            {
                "score_date": score_date,
                "disease": disease,
                "district": district,
                "cases_7d": cases,
                "trend_score": trend,
                "weather_score": weather_score,
                "risk_score": score,
                "alert_level": level,
                "explanation": (
                    f"basis={basis}; cases_7d={cases}; current_cases={current_cases}; baseline_cases={baseline_cases:.1f}; "
                    f"trend_score={trend:.1f}; weather_score={weather_score:.1f}; "
                    f"formula=cases*70%({components['case_component']:.1f}) + trends*20%({components['trend_component']:.1f}) "
                    f"+ weather_lag_7_17d*10%({components['weather_component']:.1f})"
                ),
                "created_at": datetime.utcnow(),
            }
        )

    count = upsert_rows(session, risk_scores, rows, ["score_date", "disease", "district"])
    active_keys = {(row["disease"], row["district"]) for row in rows}
    existing_rows = session.execute(
        select(risk_scores.c.id, risk_scores.c.disease, risk_scores.c.district).where(risk_scores.c.score_date == score_date)
    ).mappings()
    stale_ids = [
        row["id"]
        for row in existing_rows
        if (row["disease"], row["district"]) not in active_keys
    ]
    if stale_ids:
        session.execute(risk_scores.delete().where(risk_scores.c.id.in_(stale_ids)))
    logger.info("Built %s risk score rows", count)
    return count


def _cases_by_disease_location(event_rows) -> dict[tuple[str, str], int]:
    grouped: dict[tuple[str, str], dict[str, list[int]]] = {}
    for row in event_rows:
        key = (row["disease"], row["district"])
        bucket = grouped.setdefault(key, {"current": [], "cumulative": []})
        cases = int(row["cases"] or 0)
        if _is_cumulative_text(row.get("raw_text", "")):
            bucket["cumulative"].append(cases)
        else:
            bucket["current"].append(cases)
    return {
        key: max(values["current"] or [0])
        for key, values in grouped.items()
    }


def _is_cumulative_text(text: str) -> bool:
    from src.processing.clean_text import normalize_key

    key = normalize_key(text or "")
    return any(
        token in key
        for token in [
            "luy ke",
            "tich luy",
            "tu dau nam",
            "den nay",
            "nam 2024",
            "nam 2025",
            "nam 2026",
            "toan quoc",
        ]
    )


def _baseline_cases_by_disease_location(session, score_date: date) -> dict[tuple[str, str], float]:
    week = int(score_date.strftime("%V"))
    years = [score_date.year - offset for offset in range(1, 4)]
    rows = session.execute(
        select(
            extracted_events.c.disease,
            extracted_events.c.district,
            extracted_events.c.cases,
        ).where(
            and_(
                extracted_events.c.cases.is_not(None),
                extract("week", extracted_events.c.event_date) == week,
                extract("year", extracted_events.c.event_date).in_(years),
                extracted_events.c.district != "Việt Nam",
            )
        )
    ).mappings()
    grouped: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        grouped.setdefault((row["disease"], row["district"]), []).append(int(row["cases"] or 0))
    return {key: sum(values) / len(values) for key, values in grouped.items() if values}
