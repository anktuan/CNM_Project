import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import schedule
import time
from datetime import datetime
import os

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
ALERT_THRESHOLD = 1000 
PROVINCES = ["TP.HCM", "Hà Nội", "Đồng Nai", "Bình Dương", "Cần Thơ", "Hà Tĩnh", "Đắk Lắk"]
DATA_DIR = "data/raw"
FILE_PATH = os.path.join(DATA_DIR, "news_dengue.csv")

# ==========================================
# CÁC HÀM XỬ LÝ (PIPELINE)
# ==========================================
def get_article_links():
    """Bước 1: Quét các bài báo về sức khỏe để tìm link liên quan sốt xuất huyết"""
    url = "https://vnexpress.net/suc-khoe"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")
        
        links = [a["href"] for a in soup.find_all("a", href=True) 
                 if "sot-xuat-huyet" in a["href"] and "vnexpress.net" in a["href"]]
        return list(set(links))
    except Exception as e:
        print(f"[Lỗi] Không thể lấy danh sách bài viết: {e}")
        return []

def get_article_content(url):
    """Bước 2: Lấy toàn bộ nội dung text của một bài báo"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")
        return " ".join([p.text for p in soup.find_all("p")])
    except Exception as e:
        print(f"[Lỗi] Không thể đọc nội dung {url}: {e}")
        return ""

def extract_info(text, source_url):
    """Bước 3 & 4: Trích xuất tên tỉnh và số ca mắc bằng Regex"""
    data = []
    for p in PROVINCES:
        if p in text:
            # Tìm pattern số + chữ 'ca' (VD: 1.200 ca, 500 ca)
            cases_matches = re.findall(r"(\d+[.,]?\d*)\s*ca", text)
            if cases_matches:
                clean_case = cases_matches[0].replace(".", "").replace(",", "")
                try:
                    case_count = int(clean_case)
                    
                    if case_count > ALERT_THRESHOLD:
                        print(f"⚠️ [CẢNH BÁO MỨC ĐỘ CAO] Phát hiện {case_count} ca tại {p}!")

                    data.append({
                        "province": p,
                        "cases": case_count,
                        "source": source_url,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                except ValueError:
                    continue
    return data

def save_data(data):
    """Bước 5: Lưu dữ liệu thô vào CSV"""
    if not data:
        print("[-] Không có dữ liệu số ca mắc mới trong lần quét này.")
        return
        
    os.makedirs(DATA_DIR, exist_ok=True)
    df_new = pd.DataFrame(data)
    
    if os.path.exists(FILE_PATH):
        df_old = pd.read_csv(FILE_PATH)
        # Nối data mới, loại bỏ các dòng trùng lặp cùng tỉnh, cùng số ca từ cùng 1 nguồn
        df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['province', 'cases', 'source'])
        df_final.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')
        
    print(f"[+] Đã cập nhật {len(df_new)} bản ghi vào {FILE_PATH}")

def run_pipeline():
    """Hàm chạy tổng hợp toàn bộ quy trình"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ĐANG CHẠY BỘ THU THẬP DỮ LIỆU...")
    links = get_article_links()
    print(f"[*] Tìm thấy {len(links)} bài báo liên quan.")
    
    all_data = []
    for link in links:
        text = get_article_content(link)
        if text:
            all_data.extend(extract_info(text, link))
            
    save_data(all_data)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HOÀN THÀNH QUÉT.\n" + "-"*40)

# ==========================================
# KHỞI CHẠY TỰ ĐỘNG
# ==========================================
if __name__ == "__main__":
    run_pipeline() # Chạy lần đầu ngay lập tức
    
    # Cài đặt lịch quét tự động mỗi 3 giờ
    schedule.every(3).hours.do(run_pipeline)
    print("⏳ Hệ thống đang chạy ngầm (Mỗi 3 tiếng quét 1 lần). Nhấn Ctrl+C để dừng.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)