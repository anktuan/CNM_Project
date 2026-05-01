import requests
from utils import save_to_csv
from datetime import datetime

# Từ điển ánh xạ: Tên Bệnh -> Mã dữ liệu chuẩn của WHO
WHO_DISEASES = {
    "Sốt xuất huyết": "WHS3_48",
    "Sốt rét": "WHS3_41",       # Malaria
    "Bệnh Lao": "TB_e_inc_num", # Tuberculosis
    "Bệnh Sởi": "WHS3_47"       # Measles
}

def run_who():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Lấy số liệu ĐA BỆNH từ WHO GHO API...")
    
    all_data = []
    
    for disease_name, indicator in WHO_DISEASES.items():
        # Lấy dữ liệu riêng cho Việt Nam (SpatialDim eq 'VNM')
        url = f"https://ghoapi.azureedge.net/api/{indicator}?$filter=SpatialDim eq 'VNM'"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                records = response.json().get('value', [])
                
                for item in records:
                    # Lọc bỏ các dòng bị rỗng số liệu
                    cases = item.get("NumericValue")
                    if cases is not None:
                        all_data.append({
                            "disease": disease_name,
                            "country": "Vietnam",
                            "year": item.get("TimeDim"), # WHO báo cáo theo năm
                            "cases": int(cases),
                            "source": "WHO API"
                        })
        except Exception as e:
            print(f"[-] Lỗi khi tải dữ liệu {disease_name}: {e}")
            continue

    if all_data:
        # Sắp xếp để dữ liệu mới nhất (năm gần nhất) hiển thị lên trên
        all_data = sorted(all_data, key=lambda x: (x['disease'], -x['year']))
        save_to_csv(all_data, "who_diseases_vietnam.csv")
    else:
        print("[-] Không lấy được dữ liệu bệnh truyền nhiễm nào từ WHO.")