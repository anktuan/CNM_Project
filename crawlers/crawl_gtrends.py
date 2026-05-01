from pytrends.request import TrendReq
from utils import save_to_csv
from datetime import datetime
import time

def run_gtrends():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Lấy dữ liệu Google Trends...")
    try:
        pytrend = TrendReq(hl='vi-VN', tz=-420, timeout=(10,25))
        
        # Danh sách các bệnh muốn theo dõi trên Google Trends
        diseases = ["sốt xuất huyết", "tay chân miệng", "bệnh sởi"]
        all_data = []
        
        for disease in diseases:
            pytrend.build_payload(kw_list=[disease], geo='VN', timeframe='now 7-d')
            time.sleep(2) # Nghỉ 2s giữa các lần lấy để không bị Google block
            
            df = pytrend.interest_over_time()
            if not df.empty:
                df = df.reset_index()
                if 'isPartial' in df.columns:
                    df = df.drop(columns=['isPartial'])
                
                # Format lại dữ liệu theo yêu cầu của bạn
                df = df.rename(columns={'date': 'thoi_gian', disease: 'luot_tim_kiem'})
                df['ten_benh'] = disease # Thêm cột tên bệnh
                
                # Sắp xếp thứ tự cột cho chuẩn
                df = df[['thoi_gian', 'ten_benh', 'luot_tim_kiem']]
                df['thoi_gian'] = df['thoi_gian'].astype(str)
                
                # Chuyển thành dạng dict để lưu chung
                all_data.extend(df.to_dict('records'))
        
        if all_data:
            save_to_csv(all_data, "gtrends_diseases.csv")
        else:
            print("[-] Không có dữ liệu xu hướng mới từ Google Trends.")
            
    except Exception as e:
        print(f"[Lỗi Google Trends] - Có thể do giới hạn API (429): {e}")