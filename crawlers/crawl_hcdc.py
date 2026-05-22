import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from utils import save_to_csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

BASE_URL = "https://hcdc.vn"

SEED_URLS = [
    "https://hcdc.vn/category/van-de-suc-khoe/tay-chan-mieng/pages-4",
    "https://hcdc.vn/tinh-hinh-dich-benh-sot-xuat-huyet-tay-chan-mieng-tren-dia-ban-tp-ho-chi-minh-tinh-den-tuan-192026-df84pO.html",
    "https://www.hcdc.vn/tinh-hinh-dich-benh-sot-xuat-huyet-tay-chan-mieng-tren-dia-ban-tp-ho-chi-minh-tinh-den-tuan-122026-tsOeSg.html",
]

TARGET_DISEASES = {
    "sốt xuất huyết": "Sốt xuất huyết",
    "tay chân miệng": "Tay chân miệng",
    "sởi": "Sởi",
}

def clean_number(value: str):
    """
    Chuyển '1.481' hoặc '1,481' thành 1481.
    """
    if value is None:
        return None

    value = value.strip()
    value = value.replace(".", "").replace(",", "")

    try:
        return int(value)
    except ValueError:
        return None


def get_html(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[Lỗi HCDC] Không tải được {url}: {e}")
        return ""


def discover_article_links():
    """
    Lấy các link bài viết HCDC có cụm 'tình hình dịch bệnh'.
    """
    links = set()

    for seed_url in SEED_URLS:
        html = get_html(seed_url)
        if not html:
            continue

        soup = BeautifulSoup(html, "lxml")

        # Nếu seed_url đã là bài viết thì thêm luôn.
        if seed_url.endswith(".html"):
            links.add(seed_url)

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            text = a.get_text(" ", strip=True).lower()
            full_url = urljoin(BASE_URL, href)

            if (
                "hcdc.vn" in full_url
                and full_url.endswith(".html")
                and (
                    "tình hình dịch bệnh" in text
                    or "tinh-hinh-dich-benh" in full_url
                    or "sốt xuất huyết" in text
                    or "tay chân miệng" in text
                    or "sởi" in text
                )
            ):
                links.add(full_url)

    return sorted(links)


def split_sentences(text: str):
    text = re.sub(r"\s+", " ", text)
    return re.split(r"(?<=[.!?])\s+", text)


def extract_week_info(text: str):
    """
    Tìm thông tin tuần, ví dụ: tuần 19/2026.
    """
    match = re.search(r"tuần\s+(\d{1,2})\s*/\s*(\d{4})", text.lower())
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def extract_date_range(text: str):
    """
    Tìm khoảng ngày dạng: từ ngày 04/5/2026 đến ngày 10/5/2026.
    """
    pattern = r"từ ngày\s+(\d{1,2}/\d{1,2}/\d{4})\s+đến ngày\s+(\d{1,2}/\d{1,2}/\d{4})"
    match = re.search(pattern, text.lower())
    if match:
        return match.group(1), match.group(2)
    return None, None


def classify_metric_type(sentence: str):
    """
    Phân loại số ca trong câu là ca theo tuần hay ca tích lũy.
    """
    s = sentence.lower()
    if "tích lũy" in s or "từ đầu năm" in s:
        return "cumulative"
    if "trong tuần" in s or "tuần" in s:
        return "weekly"
    return "unknown"


def extract_cases_from_article(article_text: str, source_url: str):
    """
    Trích xuất số ca bệnh từ bài HCDC.
    """
    records = []

    lower_text = article_text.lower()
    week, year = extract_week_info(lower_text)
    start_date, end_date = extract_date_range(lower_text)
    sentences = split_sentences(article_text)

    for sentence in sentences:
        s_lower = sentence.lower()

        for disease_key, disease_name in TARGET_DISEASES.items():
            if disease_key not in s_lower:
                continue

            # Các mẫu thường gặp:
            # "ghi nhận 1.481 trường hợp mắc bệnh tay chân miệng"
            # "có 500 ca sốt xuất huyết"
            # "tổng số ca ... là 29.395 ca"
            patterns = [
                r"ghi nhận\s+([\d\.,]+)\s+(?:ca|trường hợp)",
                r"có\s+([\d\.,]+)\s+(?:ca|trường hợp)",
                r"là\s+([\d\.,]+)\s+(?:ca|trường hợp)",
                r"([\d\.,]+)\s+(?:ca|trường hợp)\s+mắc",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, s_lower)
                for raw_number in matches:
                    cases = clean_number(raw_number)
                    if cases is None:
                        continue

                    records.append({
                        "event_date": end_date,
                        "week": week,
                        "year": year,
                        "disease": disease_name,
                        "province": "TP. Hồ Chí Minh",
                        "cases": cases,
                        "metric_type": classify_metric_type(sentence),
                        "source_type": "hcdc",
                        "source_name": "HCDC",
                        "source_url": source_url,
                        "raw_text": sentence.strip(),
                        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })

    return records


def parse_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None

    value = str(value).strip()

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.date().isoformat()


def run_hcdc():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang quét dữ liệu HCDC...")

    links = discover_article_links()
    print(f"[*] Tìm thấy {len(links)} link HCDC có khả năng chứa dữ liệu dịch bệnh.")

    all_records = []

    for link in links[:20]:
        records = parse_article(link)
        all_records.extend(records)

    if all_records:
        df = pd.DataFrame(all_records)
        df = df.drop_duplicates(
            subset=["event_date", "week", "year", "disease", "province", "cases", "metric_type", "source_url"]
        )
        save_to_csv(df.to_dict("records"), "hcdc_diseases.csv")
        print(f"[+] Đã lưu {len(df)} dòng dữ liệu HCDC.")
    else:
        print("[-] Chưa trích xuất được số ca từ HCDC.")