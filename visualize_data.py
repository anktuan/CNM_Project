import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Tùy chỉnh hiển thị cho đẹp
sns.set_theme(style="whitegrid")

def plot_who_trends():
    """Vẽ biểu đồ sự gia tăng số ca mắc qua các năm từ dữ liệu WHO"""
    file_path = "data/raw/who_diseases_vietnam.csv"
    
    if not os.path.exists(file_path):
        print(f"[-] Không tìm thấy file {file_path}")
        return

    df = pd.read_csv(file_path)
    
    # Tạo form hình chữ nhật rộng rãi
    plt.figure(figsize=(12, 6))
    
    # Vẽ biểu đồ line plot, chia màu theo từng loại bệnh
    sns.lineplot(data=df, x='year', y='cases', hue='disease', marker='o', linewidth=2.5)
    
    plt.title('Xu Hướng Gia Tăng Các Bệnh Truyền Nhiễm Tại Việt Nam (Nguồn: WHO)', fontsize=16, pad=15)
    plt.xlabel('Năm', fontsize=12)
    plt.ylabel('Số ca mắc được báo cáo', fontsize=12)
    plt.xticks(rotation=45)
    
    # Tạo thư mục xuất ảnh nếu chưa có
    os.makedirs("data/charts", exist_ok=True)
    out_path = "data/charts/who_trends_chart.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    print(f"[+] Đã tạo biểu đồ WHO tại: {out_path}")
    plt.close()

def plot_gtrends_stats():
    """Vẽ biểu đồ thống kê tổng lượt tìm kiếm của các bệnh trên Google Trends"""
    file_path = "data/raw/gtrends_diseases.csv"
    
    if not os.path.exists(file_path):
        print(f"[-] Không tìm thấy file {file_path}")
        return

    df = pd.read_csv(file_path)
    
    # Tính tổng lượt tìm kiếm hoặc tính trung bình cho mỗi loại bệnh
    df_stats = df.groupby('ten_benh')['luot_tim_kiem'].sum().reset_index()
    df_stats = df_stats.sort_values(by='luot_tim_kiem', ascending=False)
    
    plt.figure(figsize=(10, 6))
    
    # Vẽ biểu đồ cột (Bar plot)
    sns.barplot(data=df_stats, x='ten_benh', y='luot_tim_kiem', palette='viridis')
    
    plt.title('Tổng Lượt Tìm Kiếm Về Dịch Bệnh Tại Việt Nam (Google Trends 7 ngày qua)', fontsize=14, pad=15)
    plt.xlabel('Tên Bệnh', fontsize=12)
    plt.ylabel('Tổng Điểm Tìm Kiếm', fontsize=12)
    
    out_path = "data/charts/gtrends_stats_chart.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    print(f"[+] Đã tạo biểu đồ Google Trends tại: {out_path}")
    plt.close()

if __name__ == "__main__":
    print("Đang khởi tạo biểu đồ thống kê...")
    plot_who_trends()
    plot_gtrends_stats()
    print("Hoàn tất!")