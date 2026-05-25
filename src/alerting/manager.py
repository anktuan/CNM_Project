from __future__ import annotations

from datetime import datetime
import logging

from sqlalchemy import and_, select

from src.alerting.email_alert import send_email
from src.alerting.telegram_alert import send_telegram
from src.database import alerts, risk_scores

logger = logging.getLogger(__name__)

ACTIONABLE_LEVELS = {"Đỏ"}


def dispatch_alerts(session) -> int:
    statement = select(risk_scores).where(risk_scores.c.alert_level.in_(ACTIONABLE_LEVELS))
    sent = 0
    for row in session.execute(statement).mappings():
        message = _format_alert_message(row)
        for channel, sender in [("telegram", lambda msg: send_telegram(msg)), ("email", lambda msg: send_email("Cảnh báo dịch bệnh truyền nhiễm", msg))]:
            already_sent = session.execute(
                select(alerts.c.id).where(
                    and_(
                        alerts.c.risk_score_id == row["id"],
                        alerts.c.channel == channel,
                        alerts.c.status == "sent",
                    )
                )
            ).first()
            if already_sent:
                continue
            ok, response = sender(message)
            session.execute(
                alerts.insert().values(
                    risk_score_id=row["id"],
                    channel=channel,
                    message=message,
                    status="sent" if ok else "skipped_or_failed",
                    provider_response=response,
                    created_at=datetime.utcnow(),
                )
            )
            sent += 1 if ok else 0
    logger.info("Dispatched %s configured alerts", sent)
    return sent


def _format_alert_message(row) -> str:
    cases = int(row["cases_7d"] or 0)
    trend_score = float(row["trend_score"] or 0)
    weather_score = float(row["weather_score"] or 0)
    risk_score = float(row["risk_score"] or 0)
    basis = "có ghi nhận số ca mắc mới trong kỳ gần đây" if cases > 0 else "chưa có số ca mới, dùng Google Trends và thời tiết làm tín hiệu thay thế"

    lines = [
        f"CẢNH BÁO {row['alert_level']}: {row['disease']} tại {row['district']}",
        f"Điểm rủi ro tổng hợp: {risk_score:.1f}/100.",
        f"Số ca dùng để tính cảnh báo trong kỳ gần đây: {cases:,} ca.",
        f"Tín hiệu Google Trends: {trend_score:.1f}/100.",
        f"Điểm nguy cơ thời tiết: {weather_score:.1f}/40.",
        f"Cơ sở đánh giá: {basis}.",
        "Vui lòng kiểm tra dashboard để xem nguồn tin, diễn biến ca bệnh và bản đồ khu vực.",
    ]
    return "\n".join(lines)
