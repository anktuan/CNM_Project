import os
import re
import pandas as pd
from datetime import datetime

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
ANALYTICS_DIR = "data/analytics"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(ANALYTICS_DIR, exist_ok=True)


DISEASE_MAP = {
    "sốt xuất huyết": "Sốt xuất huyết",
    "sxh": "Sốt xuất huyết",
    "dengue": "Sốt xuất huyết",

    "tay chân miệng": "Tay chân miệng",
    "tcm": "Tay chân miệng",

    "sởi": "Sởi",
    "bệnh sởi": "Sởi",
    "measles": "Sởi",

    "cúm": "Cúm",
    "influenza": "Cúm",

    "dại": "Dại",
    "bạch hầu": "Bạch hầu",

    "sốt rét": "Sốt rét",
    "malaria": "Sốt rét",

    "bệnh lao": "Bệnh Lao",
    "lao": "Bệnh Lao",
    "tuberculosis": "Bệnh Lao",
}


PROVINCE_MAP = {
    "tp.hcm": "TP. Hồ Chí Minh",
    "tp hcm": "TP. Hồ Chí Minh",
    "tphcm": "TP. Hồ Chí Minh",
    "tp. hồ chí minh": "TP. Hồ Chí Minh",
    "thành phố hồ chí minh": "TP. Hồ Chí Minh",
    "hồ chí minh": "TP. Hồ Chí Minh",

    "hà nội": "Hà Nội",
    "ha noi": "Hà Nội",

    "đồng nai": "Đồng Nai",
    "bình dương": "Bình Dương",
    "cần thơ": "Cần Thơ",
    "hà tĩnh": "Hà Tĩnh",
    "đắk lắk": "Đắk Lắk",
}


def read_csv_if_exists(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def normalize_text(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_disease(value):
    text = normalize_text(value).lower()
    return DISEASE_MAP.get(text, value.title() if text else "")


def normalize_province(value):
    text = normalize_text(value).lower()
    return PROVINCE_MAP.get(text, value if normalize_text(value) else "")


def clean_number(value):
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = value.replace(".", "").replace(",", "")

    try:
        return int(float(value))
    except ValueError:
        return None


def parse_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None

    value = str(value).strip()

    # Thử parse tự động nhiều dạng ngày.
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.date().isoformat()


def confidence_by_source(source_type):
    """
    Điểm tin cậy:
    - WHO, HCDC, VNCDC/Bộ Y tế: cao
    - News: trung bình
    - Google Trends: không phải số ca, chỉ là tín hiệu
    """
    source_type = str(source_type).lower()

    if source_type in ["who", "who api"]:
        return 0.95
    if source_type in ["hcdc"]:
        return 0.90
    if source_type in ["moh", "vncdc", "bo_y_te"]:
        return 0.85
    if source_type in ["news", "vnexpress"]:
        return 0.60
    if source_type in ["gtrends", "google_trends"]:
        return 0.50
    return 0.40


def normalize_hcdc():
    path = os.path.join(RAW_DIR, "hcdc_diseases.csv")
    df = read_csv_if_exists(path)

    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["event_date"] = df.get("event_date", "")
    out["event_date"] = out["event_date"].fillna("")
    if "collected_at" in df.columns:
        out.loc[out["event_date"] == "", "event_date"] = df.loc[out["event_date"] == "", "collected_at"]
    out["disease"] = df.get("disease", "")
    out["province"] = df.get("province", "TP. Hồ Chí Minh")
    out["country"] = "Vietnam"
    out["cases"] = df.get("cases", None)
    out["trend_score"] = None
    out["metric_type"] = df.get("metric_type", "unknown")
    out["source_type"] = "hcdc"
    out["source_name"] = "HCDC"
    out["source_url"] = df.get("source_url", "")
    out["raw_text"] = df.get("raw_text", "")
    out["collected_at"] = df.get("collected_at", "")

    return out


def normalize_news():
    path = os.path.join(RAW_DIR, "news_diseases.csv")
    df = read_csv_if_exists(path)

    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["event_date"] = df.get("timestamp", "")
    out["disease"] = df.get("disease", "")
    out["province"] = df.get("province", "")
    out["country"] = "Vietnam"
    out["cases"] = df.get("cases", None)
    out["trend_score"] = None
    out["metric_type"] = "reported_in_news"
    out["source_type"] = "news"
    out["source_name"] = "VnExpress RSS"
    out["source_url"] = df.get("source", "")
    out["raw_text"] = ""
    out["collected_at"] = df.get("timestamp", "")

    return out


def normalize_moh():
    path = os.path.join(RAW_DIR, "moh_diseases.csv")
    df = read_csv_if_exists(path)

    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["event_date"] = df.get("timestamp", "")
    out["disease"] = df.get("disease", "")
    out["province"] = ""
    out["country"] = "Vietnam"
    out["cases"] = df.get("cases", None)
    out["trend_score"] = None
    out["metric_type"] = "reported_by_moh"
    out["source_type"] = "moh"
    out["source_name"] = "VNCDC/Bộ Y tế"
    out["source_url"] = df.get("source", "")
    out["raw_text"] = ""
    out["collected_at"] = df.get("timestamp", "")

    return out


def normalize_who():
    path = os.path.join(RAW_DIR, "who_diseases_vietnam.csv")
    df = read_csv_if_exists(path)

    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["event_date"] = df.get("year", "").astype(str) + "-12-31"
    out["disease"] = df.get("disease", "")
    out["province"] = ""
    out["country"] = df.get("country", "Vietnam")
    out["cases"] = df.get("cases", None)
    out["trend_score"] = None
    out["metric_type"] = "annual"
    out["source_type"] = "who"
    out["source_name"] = "WHO GHO API"
    out["source_url"] = "https://www.who.int/data/gho/info/gho-odata-api"
    out["raw_text"] = ""
    out["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return out


def normalize_gtrends():
    path = os.path.join(RAW_DIR, "gtrends_diseases.csv")
    df = read_csv_if_exists(path)

    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["event_date"] = df.get("thoi_gian", "")
    out["disease"] = df.get("ten_benh", "")
    out["province"] = ""
    out["country"] = "Vietnam"
    out["cases"] = None
    out["trend_score"] = df.get("luot_tim_kiem", None)
    out["metric_type"] = "search_interest"
    out["source_type"] = "gtrends"
    out["source_name"] = "Google Trends"
    out["source_url"] = "https://trends.google.com/trends/"
    out["raw_text"] = ""
    out["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return out


def build_master_dataset():
    datasets = [
        normalize_hcdc(),
        normalize_news(),
        normalize_moh(),
        normalize_who(),
        normalize_gtrends(),
    ]

    datasets = [df for df in datasets if not df.empty]

    if not datasets:
        print("[-] Không có dữ liệu raw để xử lý.")
        return pd.DataFrame()

    master = pd.concat(datasets, ignore_index=True)

    master["event_date"] = master["event_date"].apply(parse_date)
    master["disease"] = master["disease"].apply(normalize_disease)
    master["province"] = master["province"].apply(normalize_province)
    master["cases"] = master["cases"].apply(clean_number)
    master["trend_score"] = pd.to_numeric(master["trend_score"], errors="coerce")
    master["source_type"] = master["source_type"].fillna("").astype(str)
    master["confidence"] = master["source_type"].apply(confidence_by_source)

    # Bỏ dòng không có tên bệnh.
    master = master[master["disease"].notna() & (master["disease"] != "")]

    # Loại trùng.
    master = master.drop_duplicates(
        subset=[
            "event_date",
            "disease",
            "province",
            "country",
            "cases",
            "trend_score",
            "metric_type",
            "source_url",
        ]
    )

    output_path = os.path.join(PROCESSED_DIR, "disease_events_clean.csv")
    master.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[+] Đã tạo bảng sạch: {output_path}")
    print(f"[+] Số dòng: {len(master)}")

    return master


def alert_level(row):
    cases = row.get("cases")
    trend_score = row.get("trend_score")

    if pd.notna(cases):
        if cases >= 1000:
            return "High"
        if cases >= 500:
            return "Medium"
        return "Low"

    if pd.notna(trend_score):
        if trend_score >= 80:
            return "High signal"
        if trend_score >= 60:
            return "Medium signal"
        return "Low signal"

    return "Unknown"


def build_daily_summary(master):
    if master.empty:
        return pd.DataFrame()

    df = master.copy()

    # Chỉ lấy ngày hợp lệ.
    df = df[df["event_date"].notna()]

    group_cols = ["event_date", "disease", "province", "country"]

    summary = df.groupby(group_cols, dropna=False).agg(
        max_cases=("cases", "max"),
        avg_trend_score=("trend_score", "mean"),
        news_count=("source_type", lambda x: (x == "news").sum()),
        source_count=("source_type", "count"),
        source_types=("source_type", lambda x: ",".join(sorted(set(x.astype(str))))),
        metric_types=("metric_type", lambda x: ",".join(sorted(set(x.astype(str))))),
        max_confidence=("confidence", "max"),
    ).reset_index()

    summary["cases"] = summary["max_cases"]
    summary["trend_score"] = summary["avg_trend_score"]
    summary["alert_level"] = summary.apply(alert_level, axis=1)

    output_path = os.path.join(ANALYTICS_DIR, "daily_disease_summary.csv")
    summary.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[+] Đã tạo bảng tổng hợp dashboard: {output_path}")
    print(f"[+] Số dòng: {len(summary)}")

    return summary


def build_alerts(summary):
    if summary.empty:
        return pd.DataFrame()

    current_year = datetime.now().year

    alerts = summary.copy()

    # Lấy năm từ event_date để chỉ cảnh báo dữ liệu gần hiện tại
    alerts["event_year"] = pd.to_datetime(alerts["event_date"], errors="coerce").dt.year

    # Lọc cảnh báo:
    # 1. Không lấy WHO vì WHO là dữ liệu lịch sử/nền, không phải cảnh báo realtime
    # 2. Chỉ lấy dữ liệu từ năm hiện tại hoặc năm trước
    # 3. Chỉ lấy các mức cảnh báo đáng chú ý
    alerts = alerts[
        (~alerts["source_types"].str.contains("who", na=False))
        & (alerts["event_year"] >= current_year - 1)
        & (alerts["alert_level"].isin(["High", "Medium", "High signal", "Medium signal"]))
    ].copy()

    def make_message(row):
        disease = row["disease"]
        province = row["province"] if pd.notna(row["province"]) and row["province"] else "Việt Nam"
        date = row["event_date"]
        metric_types = str(row.get("metric_types", "")).lower()

        if pd.notna(row.get("cases")):
            if "cumulative" in metric_types:
                 return f"{row['alert_level']}: {disease} tại {province} có số ca tích lũy đạt {int(row['cases'])} ca tính đến {date}."

            if "weekly" in metric_types:
                 return f"{row['alert_level']}: {disease} tại {province} ghi nhận {int(row['cases'])} ca trong tuần kết thúc ngày {date}."
            return f"{row['alert_level']}: {disease} tại {province} ghi nhận {int(row['cases'])} ca vào {date}."
        if pd.notna(row.get("trend_score")):
            return f"{row['alert_level']}: Mức quan tâm tìm kiếm về {disease} đạt {row['trend_score']:.1f} vào {date}."
        return f"{row['alert_level']}: Có tín hiệu cần theo dõi về {disease} tại {province}."

    alerts["alert_message"] = alerts.apply(make_message, axis=1)

    # Không cần lưu cột event_year phụ ra file cuối
    if "event_year" in alerts.columns:
        alerts = alerts.drop(columns=["event_year"])

    output_path = os.path.join(ANALYTICS_DIR, "alerts.csv")
    alerts.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[+] Đã tạo bảng cảnh báo: {output_path}")
    print(f"[+] Số cảnh báo: {len(alerts)}")

    return alerts


def run_processing_pipeline():
    print("\n" + "=" * 50)
    print("🧹 BẮT ĐẦU XỬ LÝ, CHUẨN HÓA VÀ TỔNG HỢP DỮ LIỆU")
    print("=" * 50)

    master = build_master_dataset()
    summary = build_daily_summary(master)
    alerts = build_alerts(summary)

    print("=" * 50)
    print("✅ HOÀN TẤT XỬ LÝ DỮ LIỆU")
    print("=" * 50 + "\n")

    return master, summary, alerts


if __name__ == "__main__":
    run_processing_pipeline()