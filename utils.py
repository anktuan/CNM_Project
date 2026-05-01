import os
import pandas as pd

def save_to_csv(data, filename):
    if not data:
        return
    
    os.makedirs("data/raw", exist_ok=True)
    file_path = os.path.join("data/raw", filename)
    df_new = pd.DataFrame(data)
    
    if os.path.exists(file_path):
        df_old = pd.read_csv(file_path)
        df_final = pd.concat([df_old, df_new]).drop_duplicates()
        df_final.to_csv(file_path, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    print(f"[+] Đã lưu/cập nhật dữ liệu vào {file_path}")