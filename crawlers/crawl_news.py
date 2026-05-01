import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils import save_to_csv

HEADERS = {"User-Agent": "Mozilla/5.0"}
ALERT_THRESHOLD = 500 
PROVINCES = ["TP.HCM", "Hà Nội", "Đồng Nai", "Bình Dương", "Cần Thơ", "Hà Tĩnh", "Đắk Lắk"]
# Thêm danh sách các bệnh cần theo dõi trên báo
TARGET_DISEASES = ["sốt xuất huyết", "tay chân miệng", "sởi", "đậu mùa khỉ", "cúm", "dại", "bạch hầu"]

def run_news():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang quét tin tức ĐA BỆNH từ RSS VnExpress...")
    rss_url = "https://vnexpress.net/rss/suc-khoe.rss"
    
    try:
        res = requests.get(rss_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.content, "xml") 
        items = soup.find_all("item")
        
        all_data = []
        
        for item in items:
            title = item.title.text if item.title else ""
            description = item.description.text if item.description else ""
            link = item.link.text if item.link else ""
            
            full_text = f"{title} {description}".lower()
            
            # Kiểm tra xem bài báo có nhắc đến bệnh nào trong danh sách không
            found_diseases = [d for d in TARGET_DISEASES if d in full_text]
            
            if found_diseases:
                article_res = requests.get(link, headers=HEADERS, timeout=10)
                article_soup = BeautifulSoup(article_res.text, "lxml")
                article_text = " ".join([p.text for p in article_soup.find_all("p")])
                
                for p in PROVINCES:
                    if p in article_text:
                        cases_matches = re.findall(r"(\d+[.,]?\d*)\s*ca", article_text)
                        if cases_matches:
                            clean_case = cases_matches[0].replace(".", "").replace(",", "")
                            try:
                                case_count = int(clean_case)
                                for disease in found_diseases:
                                    all_data.append({
                                        "disease": disease.capitalize(),
                                        "province": p,
                                        "cases": case_count,
                                        "source": link,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    })
                            except ValueError:
                                continue

        if all_data:
            save_to_csv(all_data, "news_diseases.csv")
        else:
            print("[-] Chưa có số liệu ca mắc cụ thể trong các tin tức sức khỏe hôm nay.")
            
    except Exception as e:
        print(f"[Lỗi Crawl Báo] {e}")