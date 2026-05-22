import schedule
import time
from processing.build_datasets import run_processing_pipeline
from crawlers.crawl_news import run_news
from crawlers.crawl_gtrends import run_gtrends
from crawlers.crawl_who import run_who
from crawlers.crawl_moh import run_moh
from crawlers.crawl_hcdc import run_hcdc
def run_all_jobs():
    print("\n" + "="*50)
    print("🚀 KHỞI ĐỘNG LUỒNG DỮ LIỆU ĐA NGUỒN")
    print("="*50)
    
    run_news()
    run_hcdc()
#    run_gtrends()
    run_who()
    run_moh()
    run_processing_pipeline()
    print("="*50 + "\n")

if __name__ == "__main__":
    # Chạy toàn bộ 1 lần khi vừa bật
    run_all_jobs()
    
    # Setup lịch trình linh hoạt
    schedule.every(3).hours.do(run_news)      # Báo chí cào 3 tiếng/lần (cập nhật nhanh)
    schedule.every().day.at("19:00").do(run_hcdc)
#    schedule.every(12).hours.do(run_gtrends)  # Google Trends 12 tiếng/lần
    schedule.every(24).hours.do(run_who)      # WHO cào 1 ngày/lần (dữ liệu WHO ít thay đổi)
    schedule.every().day.at("18:00").do(run_moh) # Quét vào 6h tối mỗi ngày
    print("⏳ Hệ thống đang chạy ngầm đa tiến trình. Nhấn Ctrl+C để dừng.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Đã dừng hệ thống an toàn bằng phím tắt!")