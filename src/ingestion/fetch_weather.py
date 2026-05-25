from __future__ import annotations

from datetime import datetime
import logging

from src.database import upsert_rows, weather_data
from src.http_client import get_json
from src.locations import LOCATION_COORDINATES

logger = logging.getLogger(__name__)

def collect_weather(session, days_back: int = 21) -> int:
    rows: list[dict] = []
    for district, (lat, lon) in LOCATION_COORDINATES.items():
        try:
            payload = get_json(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "past_days": days_back,
                    "forecast_days": 1,
                    "daily": "temperature_2m_mean,precipitation_sum",
                    "hourly": "relative_humidity_2m",
                    "timezone": "Asia/Ho_Chi_Minh",
                },
            )
            daily = payload.get("daily", {})
            humidity_by_date = _daily_humidity(payload.get("hourly", {}))
            for idx, day in enumerate(daily.get("time", [])):
                rows.append(
                    {
                        "date": datetime.strptime(day, "%Y-%m-%d").date(),
                        "district": district,
                        "temperature_mean": _safe_index(daily.get("temperature_2m_mean", []), idx),
                        "rainfall_mm": _safe_index(daily.get("precipitation_sum", []), idx),
                        "humidity_mean": humidity_by_date.get(day),
                        "collected_at": datetime.utcnow(),
                    }
                )
        except Exception as exc:
            logger.warning("Cannot collect weather for %s: %s", district, exc)
    count = upsert_rows(session, weather_data, rows, ["date", "district"])
    logger.info("Collected %s weather rows", count)
    return count


def _safe_index(values: list, idx: int):
    return values[idx] if idx < len(values) else None


def _daily_humidity(hourly: dict) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for timestamp, humidity in zip(hourly.get("time", []), hourly.get("relative_humidity_2m", [])):
        if humidity is None:
            continue
        day = str(timestamp)[:10]
        buckets.setdefault(day, []).append(float(humidity))
    return {day: sum(values) / len(values) for day, values in buckets.items() if values}
