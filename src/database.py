from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Iterable

from sqlalchemy import (
    Column,
    JSON,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

metadata = MetaData()

raw_news = Table(
    "raw_news",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_name", String(100), nullable=False),
    Column("source_url", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("published_at", DateTime, nullable=True),
    Column("content", Text, nullable=False),
    Column("collected_at", DateTime, nullable=False, default=datetime.utcnow),
    UniqueConstraint("source_url", name="uq_raw_news_source_url"),
)

extracted_events = Table(
    "extracted_events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_date", Date, nullable=True),
    Column("disease", String(100), nullable=False),
    Column("district", String(120), nullable=False),
    Column("cases", Integer, nullable=True),
    Column("source_type", String(50), nullable=False),
    Column("source_name", String(100), nullable=False),
    Column("source_url", Text, nullable=False),
    Column("raw_text", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("collected_at", DateTime, nullable=False, default=datetime.utcnow),
)

google_trends = Table(
    "google_trends",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("date", Date, nullable=False),
    Column("disease", String(100), nullable=False),
    Column("keyword", String(160), nullable=False, default=""),
    Column("geo", String(30), nullable=False),
    Column("trend_score", Float, nullable=False),
    Column("trend_score_raw", Float, nullable=True),
    Column("collected_at", DateTime, nullable=False, default=datetime.utcnow),
    UniqueConstraint("date", "disease", "keyword", "geo", name="uq_google_trends_date_disease_keyword_geo"),
)

weather_data = Table(
    "weather_data",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("date", Date, nullable=False),
    Column("district", String(120), nullable=False),
    Column("temperature_mean", Float, nullable=True),
    Column("rainfall_mm", Float, nullable=True),
    Column("humidity_mean", Float, nullable=True),
    Column("collected_at", DateTime, nullable=False, default=datetime.utcnow),
    UniqueConstraint("date", "district", name="uq_weather_date_district"),
)

risk_scores = Table(
    "risk_scores",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("score_date", Date, nullable=False),
    Column("disease", String(100), nullable=False),
    Column("district", String(120), nullable=False),
    Column("cases_7d", Integer, nullable=False, default=0),
    Column("trend_score", Float, nullable=False, default=0),
    Column("weather_score", Float, nullable=False, default=0),
    Column("risk_score", Float, nullable=False),
    Column("alert_level", String(20), nullable=False),
    Column("explanation", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
    UniqueConstraint("score_date", "disease", "district", name="uq_risk_score_date_disease_district"),
)

alerts = Table(
    "alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("risk_score_id", Integer, nullable=False),
    Column("channel", String(30), nullable=False),
    Column("message", Text, nullable=False),
    Column("status", String(30), nullable=False),
    Column("provider_response", Text, nullable=True),
    Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
)


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    metadata.create_all(engine)
    _migrate_schema(engine)


def _migrate_schema(db_engine: Engine) -> None:
    if db_engine.dialect.name != "postgresql":
        return
    statements = [
        "ALTER TABLE google_trends ADD COLUMN IF NOT EXISTS keyword VARCHAR(160)",
        "UPDATE google_trends SET keyword = disease WHERE keyword IS NULL OR keyword = ''",
        "ALTER TABLE google_trends ALTER COLUMN keyword SET NOT NULL",
        "ALTER TABLE google_trends ADD COLUMN IF NOT EXISTS trend_score_raw DOUBLE PRECISION",
        "UPDATE google_trends SET trend_score_raw = trend_score WHERE trend_score_raw IS NULL",
        "ALTER TABLE google_trends DROP CONSTRAINT IF EXISTS uq_google_trends_date_disease_geo",
        (
            "DO $$ BEGIN "
            "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_google_trends_date_disease_keyword_geo') THEN "
            "ALTER TABLE google_trends ADD CONSTRAINT uq_google_trends_date_disease_keyword_geo UNIQUE (date, disease, keyword, geo); "
            "END IF; END $$;"
        ),
    ]
    with db_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@contextmanager
def get_session() -> Iterable[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def upsert_rows(session: Session, table: Table, rows: list[dict], conflict_columns: list[str]) -> int:
    if not rows:
        return 0
    rows = _dedupe_rows(rows, conflict_columns)
    if engine.dialect.name == "postgresql":
        statement = pg_insert(table).values(rows)
        update_columns = {
            column.name: getattr(statement.excluded, column.name)
            for column in table.columns
            if column.name not in conflict_columns and not column.primary_key
        }
        statement = statement.on_conflict_do_update(index_elements=conflict_columns, set_=update_columns)
        session.execute(statement)
    else:
        session.execute(table.insert(), rows)
    return len(rows)


def _dedupe_rows(rows: list[dict], conflict_columns: list[str]) -> list[dict]:
    deduped: dict[tuple, dict] = {}
    for row in rows:
        key = tuple(row.get(column) for column in conflict_columns)
        deduped[key] = row
    return list(deduped.values())


def fetch_dataframe(query):
    import pandas as pd

    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def latest_risk_query():
    return select(risk_scores).order_by(risk_scores.c.score_date.desc(), risk_scores.c.risk_score.desc())
