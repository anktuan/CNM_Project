import requests
import urllib3
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils import save_to_csv

# Tắt cảnh báo bảo mật InsecureRequestWarning của urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
TARGET_DISEASES = ["sốt xuất huyết", "tay chân miệng", "sởi", "đậu mùa khỉ", "cúm", "dại"]

def run_moh():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang quét bản tin dịch bệnh từ VNCDC (Bộ Y tế)...")
    url = "https://vncdc.gov.vn/thong-tin-dich-benh-c4.html"
    
    try:
        # Thêm verify=False để bỏ qua lỗi SSL Certificate
        res = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(res.content, "lxml")
        
        links = []
        for a in soup.find_all("a", href=True):
            if ".html" in a['href'] and "thong-tin" not in a['href']:
                full_link = a['href'] if a['href'].startswith("http") else "https://vncdc.gov.vn" + a['href']
                links.append(full_link)
        
        links = list(set(links))
        all_data = []

        for link in links[:10]:
            try:
                # Thêm verify=False ở đây nữa
                article_res = requests.get(link, headers=HEADERS, timeout=10, verify=False)
                article_soup = BeautifulSoup(article_res.text, "lxml")
                text = " ".join([p.text.lower() for p in article_soup.find_all("p")])
                
                for disease in TARGET_DISEASES:
                    if disease in text:
                        cases_matches = re.findall(r"(\d+[.,]?\d*)\s*ca", text)
                        if cases_matches:
                            clean_case = cases_matches[0].replace(".", "").replace(",", "")
                            try:
                                case_count = int(clean_case)
                                all_data.append({
                                    "disease": disease.capitalize(),
                                    "cases": case_count,
                                    "source": link,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                            except ValueError:
                                continue
            except:
                continue

        if all_data:
            save_to_csv(all_data, "moh_diseases.csv")
        else:
            print("[-] Chưa có báo cáo số liệu dịch bệnh mới trên VNCDC hôm nay.")

    except Exception as e:
        print(f"[Lỗi Crawl Bộ Y tế] {e}")