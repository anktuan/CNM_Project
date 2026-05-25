from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from src.ai_research import research_disease
from src.config import settings
from src.database import fetch_dataframe, init_db
from src.locations import get_location_coordinates

BASE_DIR = Path(__file__).resolve().parents[1]

st.set_page_config(page_title="Hệ thống theo dõi bệnh truyền nhiễm thời gian thực", layout="wide")

ALERT_COLORS = {
    "Đỏ": "#d7191c",
    "Cam": "#fdae61",
    "Vàng": "#ffd92f",
    "Xanh": "#1a9850",
}
LOGO_PATH = BASE_DIR / "Lo_go" / "Logo chính thức.png"
AI_LOGO_PATH = BASE_DIR / "Lo_go" / "Logo_AI.png"
AI_LOGO_DATA_URI = ""
if AI_LOGO_PATH.exists():
    AI_LOGO_DATA_URI = "data:image/png;base64," + base64.b64encode(AI_LOGO_PATH.read_bytes()).decode("ascii")

st.markdown(
    """
    <style>
    :root {
        --brand-blue: #244699;
        --brand-gold: #ffc328;
        --surface: #f7f9fd;
    }
    .stApp { background: var(--surface); }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #172033;
    }
    h1, h2, h3 { color: var(--brand-blue) !important; }
    [data-testid="stSidebar"] * { color: #172033 !important; }
    [data-testid="stMetric"] {
        background: white;
        border-left: 5px solid var(--brand-gold);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 6px rgba(36, 70, 153, 0.08);
    }
    [data-testid="stPopover"] button {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        z-index: 2147483647;
        border-radius: 999px;
        width: 3.25rem;
        height: 3.25rem;
        background-color: white;
        background-image: url("__AI_LOGO_DATA_URI__");
        background-size: 72%;
        background-repeat: no-repeat;
        background-position: center;
        color: white !important;
        border: 2px solid var(--brand-gold);
        box-shadow: 0 8px 24px rgba(36, 70, 153, 0.25);
    }
    [data-testid="stPopover"] button[aria-expanded="true"] {
        opacity: 0;
        pointer-events: none;
    }
    [data-testid="stPopover"] button p {
        opacity: 0;
        font-weight: 700;
    }
    </style>
    """.replace("__AI_LOGO_DATA_URI__", AI_LOGO_DATA_URI),
    unsafe_allow_html=True,
)


@st.cache_data(ttl=settings.dashboard_refresh_seconds)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    init_db()
    risk = fetch_dataframe(
        text(
            """
            SELECT *
            FROM risk_scores
            WHERE score_date = (SELECT MAX(score_date) FROM risk_scores)
            ORDER BY risk_score DESC
            """
        )
    )
    risk_history = fetch_dataframe(text("SELECT * FROM risk_scores ORDER BY score_date ASC, risk_score DESC"))
    events = fetch_dataframe(text("SELECT * FROM extracted_events ORDER BY collected_at DESC LIMIT 500"))
    weather = fetch_dataframe(text("SELECT * FROM weather_data ORDER BY date DESC LIMIT 500"))
    trends = fetch_dataframe(text("SELECT * FROM google_trends ORDER BY date DESC LIMIT 500"))
    who = load_who_data()
    return risk, risk_history, events, weather, trends, who


@st.cache_data(ttl=3600)
def load_who_data() -> pd.DataFrame:
    path = BASE_DIR / "data" / "raw" / "who_diseases_vietnam.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["cases"] = pd.to_numeric(df["cases"], errors="coerce")
    return df.dropna(subset=["year", "cases"])


risk_df, risk_history_df, events_df, weather_df, trends_df, who_df = load_data()

header_left, header_right = st.columns([1, 5])
with header_left:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_column_width=True)
with header_right:
    st.title("Hệ thống theo dõi bệnh truyền nhiễm thời gian thực")
    st.caption("Giám sát ca bệnh, Google Trends, thời tiết và cảnh báo theo khu vực tại Việt Nam")

if risk_df.empty:
    st.info("Chưa có dữ liệu rủi ro. Chạy `python main.py run-once` hoặc đợi scheduler thu thập dữ liệu.")
    st.stop()

level_order = ["Đỏ", "Cam", "Vàng", "Xanh"]
selected_disease = st.sidebar.multiselect(
    "Bệnh",
    options=sorted(risk_df["disease"].dropna().unique()),
    default=sorted(risk_df["disease"].dropna().unique()),
)
selected_level = st.sidebar.multiselect("Mức cảnh báo", options=level_order, default=level_order)
filtered = risk_df[risk_df["disease"].isin(selected_disease) & risk_df["alert_level"].isin(selected_level)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Khu vực theo dõi", int(filtered["district"].nunique()))
col2.metric("Bệnh theo dõi", int(filtered["disease"].nunique()))
col3.metric("Điểm cao nhất", f"{filtered['risk_score'].max():.1f}" if not filtered.empty else "0")
col4.metric("Cảnh báo Cam/Đỏ", int(filtered["alert_level"].isin(["Cam", "Đỏ"]).sum()))

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Bảng rủi ro hiện tại")
    risk_table = filtered[
            [
                "score_date",
                "disease",
                "district",
                "cases_7d",
                "trend_score",
                "weather_score",
                "risk_score",
                "alert_level",
            ]
        ].rename(columns={"cases_7d": "cases_used_for_score"})
    st.dataframe(
        risk_table,
        use_container_width=True,
        hide_index=True,
    )

with right:
    st.subheader("Top điểm rủi ro")
    chart_df = filtered.head(20).copy()
    if not chart_df.empty:
        chart_df["label"] = chart_df["district"] + " - " + chart_df["disease"]
        fig = px.bar(
            chart_df,
            x="risk_score",
            y="label",
            color="alert_level",
            color_discrete_map=ALERT_COLORS,
            orientation="h",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Lịch sử rủi ro từng ngày")
if risk_history_df.empty:
    st.caption("Chưa có dữ liệu lịch sử trong bảng risk_scores.")
else:
    history_filtered = risk_history_df[
        risk_history_df["disease"].isin(selected_disease)
        & risk_history_df["alert_level"].isin(selected_level)
    ].copy()
    history_filtered["score_date"] = pd.to_datetime(history_filtered["score_date"], errors="coerce")
    history_filtered["label"] = history_filtered["district"] + " - " + history_filtered["disease"]
    history_filtered = history_filtered.dropna(subset=["score_date"])
    if history_filtered.empty:
        st.caption("Không có dữ liệu lịch sử phù hợp với bộ lọc hiện tại.")
    else:
        fig = px.line(
            history_filtered,
            x="score_date",
            y="risk_score",
            color="label",
            markers=True,
            labels={"score_date": "Ngày", "risk_score": "Điểm rủi ro", "label": "Khu vực - bệnh"},
        )
        st.plotly_chart(fig, use_container_width=True)

        cases_history = (
            history_filtered.groupby(["score_date", "disease"], as_index=False)["cases_7d"]
            .sum()
            .sort_values("score_date")
        )
        fig = px.area(
            cases_history,
            x="score_date",
            y="cases_7d",
            color="disease",
            markers=True,
            labels={"score_date": "Ngày", "cases_7d": "Số ca dùng để tính điểm", "disease": "Bệnh"},
        )
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Bản đồ vùng dịch")
map_df = filtered.copy()
if map_df.empty:
    st.caption("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
else:
    coordinates = map_df["district"].apply(lambda value: pd.Series(get_location_coordinates(str(value)), index=["lat", "lon"]))
    map_df = pd.concat([map_df, coordinates], axis=1)
    map_df = map_df.dropna(subset=["lat", "lon"])
    if map_df.empty:
        st.caption("Các khu vực hiện có chưa có tọa độ để hiển thị trên bản đồ.")
    else:
        map_df["marker_size"] = map_df["risk_score"].clip(lower=8, upper=80)
        fig = px.scatter_mapbox(
            map_df,
            lat="lat",
            lon="lon",
            color="alert_level",
            size="marker_size",
            color_discrete_map=ALERT_COLORS,
            hover_name="district",
            hover_data={
                "disease": True,
                "cases_7d": True,
                "trend_score": ":.1f",
                "weather_score": ":.1f",
                "risk_score": ":.1f",
                "alert_level": True,
                "lat": False,
                "lon": False,
                "marker_size": False,
            },
            zoom=5,
            height=560,
        )
        fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Diễn biến ca ghi nhận")
if events_df.empty:
    st.caption("Chưa trích xuất được ca bệnh từ nguồn tin.")
else:
    events_df["event_date"] = pd.to_datetime(events_df["event_date"], errors="coerce")
    event_diseases = selected_disease or sorted(events_df["disease"].dropna().unique())
    event_area_options = sorted(events_df["district"].dropna().unique())
    selected_event_areas = st.multiselect(
        "Khu vực hiển thị trong diễn biến ca",
        options=event_area_options,
        default=event_area_options[:8],
    )
    event_filtered = events_df[
        events_df["disease"].isin(event_diseases)
        & events_df["district"].isin(selected_event_areas)
        & events_df["cases"].notna()
    ].copy()
    event_filtered["metric_note"] = event_filtered["raw_text"].fillna("").str.lower().apply(
        lambda text: "Lũy kế" if any(token in text for token in ["lũy kế", "luỹ kế", "tích lũy", "từ đầu năm", "đến nay"]) else "Theo kỳ/tuần"
    )
    trend = (
        event_filtered.dropna(subset=["event_date"])
        .groupby(["event_date", "disease", "district"], as_index=False)["cases"]
        .max()
    )
    if trend.empty:
        st.caption("Không có dòng có số ca cho bệnh/khu vực đang chọn.")
    else:
        trend["label"] = trend["district"] + " - " + trend["disease"]
        fig = px.line(
            trend,
            x="event_date",
            y="cases",
            color="label",
            markers=True,
            hover_data={"district": True, "disease": True, "cases": True},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            event_filtered[
                [
                    "event_date",
                    "disease",
                    "district",
                    "cases",
                    "metric_note",
                    "source_name",
                    "source_url",
                    "raw_text",
                ]
            ].sort_values(["event_date", "disease", "district"], ascending=[False, True, True]),
            use_container_width=True,
            hide_index=True,
        )

st.subheader("Tín hiệu Google Trends")
if trends_df.empty:
    st.caption("Chưa có dữ liệu Google Trends.")
else:
    trends_df["date"] = pd.to_datetime(trends_df["date"], errors="coerce")
    trend_filtered = trends_df[trends_df["disease"].isin(selected_disease)].copy()
    fig = px.line(
        trend_filtered,
        x="date",
        y="trend_score",
        color="disease",
        markers=True,
        labels={"trend_score": "Điểm quan tâm tìm kiếm", "date": "Ngày", "disease": "Bệnh"},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Google Trends không phải số ca mắc. Hệ thống dùng dữ liệu này như tín hiệu sớm: "
        "khi có số ca, trend_score là tín hiệu phụ; khi chưa có số ca, trend_score kết hợp với thời tiết để tạo cảnh báo thay thế."
    )

st.subheader("Dữ liệu WHO theo năm")
if who_df.empty:
    st.caption("Chưa tìm thấy file dữ liệu WHO.")
else:
    who_diseases = st.multiselect(
        "Bệnh trong dữ liệu WHO",
        options=sorted(who_df["disease"].dropna().unique()),
        default=sorted(who_df["disease"].dropna().unique())[:5],
    )
    who_filtered = who_df[who_df["disease"].isin(who_diseases)].sort_values("year")
    if who_filtered.empty:
        st.caption("Chưa chọn bệnh để hiển thị.")
    else:
        fig = px.line(
            who_filtered,
            x="year",
            y="cases",
            color="disease",
            markers=True,
            labels={"year": "Năm", "cases": "Số ca", "disease": "Bệnh"},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(who_filtered, use_container_width=True, hide_index=True)

with st.popover("AI"):
    st.markdown("**Tra cứu bệnh truyền nhiễm**")
    if not settings.gemini_api_key and not settings.tavily_api_key:
        st.warning("Chưa cấu hình GEMINI_API_KEY hoặc TAVILY_API_KEY/TAVITY_API_KEY trong .env.")
    elif not settings.gemini_api_key:
        st.info("Đã có Tavily, chưa có Gemini. Hệ thống sẽ trả lời từ kết quả tìm kiếm.")
    elif not settings.tavily_api_key:
        st.info("Đã có Gemini, chưa có Tavily. Hệ thống sẽ trả lời không kèm dữ liệu tìm kiếm mới.")
    question = st.text_input("Nhập câu hỏi", placeholder="Ví dụ: dấu hiệu sốt xuất huyết nặng là gì?", key="ai_chat_question")
    if st.button("Tra cứu", key="ai_chat_submit"):
        with st.spinner("Đang tra cứu..."):
            st.markdown(research_disease(question))

st.subheader("Dữ liệu thời tiết")
if not weather_df.empty:
    st.dataframe(weather_df, use_container_width=True, hide_index=True)
