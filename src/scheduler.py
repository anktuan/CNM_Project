from __future__ import annotations

import logging
import time

import schedule

from src.alerting.manager import dispatch_alerts
from src.config import settings
from src.database import get_session, init_db
from src.ingestion.crawl_hcdc import collect_hcdc
from src.ingestion.crawl_news import collect_news
from src.ingestion.fetch_google_trends import collect_google_trends
from src.ingestion.fetch_weather import collect_weather
from src.logging_config import setup_logging
from src.processing.pipeline import build_risk_scores, extract_raw_news_events

logger = logging.getLogger(__name__)


def run_pipeline_once(send_alerts: bool = True) -> None:
    init_db()
    with get_session() as session:
        collect_news(session)
        collect_hcdc(session)
        collect_google_trends(session)
        collect_weather(session)
        extract_raw_news_events(session)
        build_risk_scores(session)
        if send_alerts:
            dispatch_alerts(session)


def run_scheduler() -> None:
    setup_logging(settings.log_level)
    logger.info("Starting scheduler with %s minute interval", settings.scheduler_interval_minutes)
    run_pipeline_once(send_alerts=True)
    schedule.every(settings.scheduler_interval_minutes).minutes.do(run_pipeline_once)
    while True:
        schedule.run_pending()
        time.sleep(30)
