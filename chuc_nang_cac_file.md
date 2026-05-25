# Chức năng các file trong project

Tài liệu này mô tả vai trò của các file/thư mục trong dự án và cách các phần kết nối với nhau.

## 1. Luồng chính của hệ thống mới

Luồng chính đang dùng cho MVP production-ready:

```text
main.py
  -> src/scheduler.py
    -> src/ingestion/*
    -> src/processing/pipeline.py
    -> src/alerting/manager.py
  -> PostgreSQL
  -> dashboard/app.py
```

Hệ thống không sinh dữ liệu giả. Nếu nguồn bên ngoài lỗi, hệ thống ghi log và tiếp tục xử lý các nguồn còn lại. Dashboard dùng màu cảnh báo cố định và bản đồ chấm tròn để xem vùng dịch theo bệnh. Hệ thống chỉ giữ các khu vực cụ thể trong Việt Nam, không dùng dòng tổng quát `Việt Nam`.

## 2. File cấu hình và vận hành

| File | Chức năng |
|---|---|
| `README.md` | Giới thiệu nhanh dự án, lệnh chạy chính và cấu trúc tổng quan. |
| `huongdan.md` | Hướng dẫn chi tiết cách chạy local, Docker, test và xử lý lỗi thường gặp. |
| `chuc_nang_cac_file.md` | File hiện tại, giải thích chức năng các file trong project. |
| `requirements.txt` | Danh sách thư viện Python cần cài: Streamlit, SQLAlchemy, psycopg, pandas, requests, pytrends, pytest... |
| `.env` | Cấu hình thật khi chạy local/Docker. File này không nên commit lên Git. |
| `.env.example` | File mẫu để tạo `.env`. |
| `.gitignore` | Bỏ qua file môi trường, cache Python, virtualenv, log. |
| `.dockerignore` | Bỏ qua file/thư mục không cần gửi vào Docker build context. |
| `Dockerfile` | Định nghĩa image Python 3.11, cài dependency và chạy app trong container. |
| `docker-compose.yml` | Khai báo 3 service: PostgreSQL `db`, scheduler `scheduler`, dashboard `dashboard`. |
| `main.py` | Entry point chính. Nhận lệnh `run-once` hoặc `scheduler`. |

## 3. Tài liệu yêu cầu ban đầu

| File | Chức năng |
|---|---|
| `plan.md` | Kế hoạch/đặc tả mục tiêu hệ thống: nguồn dữ liệu, xử lý, risk score, dashboard, alert. |
| `Cau_truc.md` | Cấu trúc thư mục mong muốn của dự án. |
| `rm.md` | File nội dung/yêu cầu bổ sung. Hiện file này gần như trống trong workspace. |
| `Hệ thống theo dõi bệnh truyền nhiễm.txt` | Tài liệu mô tả hệ thống ban đầu, giữ lại làm tài liệu tham khảo. |

## 4. Thư mục `src/`

Đây là phần code chính mới của hệ thống.

| File | Chức năng |
|---|---|
| `src/__init__.py` | Đánh dấu `src` là Python package. |
| `src/config.py` | Đọc cấu hình từ `.env`, tạo object `settings` dùng toàn hệ thống; hỗ trợ `SMTP_*`, `EMAIL_*`, Gemini, Tavily và OCR. |
| `src/database.py` | Định nghĩa schema PostgreSQL, tạo bảng, session, upsert dữ liệu, query helper. |
| `src/http_client.py` | Tạo HTTP client có retry, timeout và User-Agent. |
| `src/locations.py` | Danh sách tỉnh/thành, quận/huyện và tọa độ; dùng để trích xuất địa điểm và vẽ bản đồ chấm tròn. |
| `src/logging_config.py` | Cấu hình logging ra console và file `logs/app.log`. |
| `src/scheduler.py` | Điều phối pipeline: crawl dữ liệu, xử lý, tính rủi ro, gửi cảnh báo, chạy định kỳ. |
| `src/ai_research.py` | Tra cứu thông tin bệnh bằng Tavily và Gemini nếu đã cấu hình API key. |

## 5. Thư mục `src/ingestion/`

Các module thu thập dữ liệu từ nguồn ngoài.

| File | Chức năng |
|---|---|
| `src/ingestion/__init__.py` | Đánh dấu thư mục ingestion là package. |
| `src/ingestion/crawl_news.py` | Lấy RSS/bài viết từ VnExpress, Tuổi Trẻ, Thanh Niên, Sức khỏe Đời sống; nếu có Tavily API thì tìm thêm bài y tế từ nguồn tin cậy để không phụ thuộc riêng RSS. |
| `src/ingestion/crawl_hcdc.py` | Tìm và crawl bài viết HCDC liên quan tình hình dịch bệnh. |
| `src/ingestion/fetch_google_trends.py` | Lấy tín hiệu Google Trends cho nhiều từ khóa/chủ đề bệnh, làm mượt 7 ngày rồi lưu PostgreSQL. |
| `src/ingestion/fetch_weather.py` | Lấy dữ liệu thời tiết từ Open-Meteo theo danh sách khu vực trong `src/locations.py`, gồm tỉnh/thành và một số quận/huyện. |
| `src/ingestion/ocr.py` | OCR optional cho ảnh thống kê bằng `pytesseract` nếu bật `OCR_ENABLED=true`. |

Kết quả ingestion được lưu vào các bảng như `raw_news`, `google_trends`, `weather_data`.

## 6. Thư mục `src/processing/`

Các module làm sạch, trích xuất và tính điểm rủi ro.

| File | Chức năng |
|---|---|
| `src/processing/__init__.py` | Đánh dấu thư mục processing là package. |
| `src/processing/clean_text.py` | Chuẩn hóa unicode, bỏ HTML đơn giản, gộp khoảng trắng, tạo key không dấu để so khớp tiếng Việt. |
| `src/processing/extract_entities.py` | Trích xuất tên bệnh, địa điểm/quận huyện/tỉnh thành, số ca từ text bằng rule/regex. |
| `src/processing/risk_score.py` | Tính điểm thời tiết, công thức risk score 70/20/10 và phân loại Xanh/Vàng/Cam/Đỏ. |
| `src/processing/pipeline.py` | Đọc raw news, tạo `extracted_events`, bỏ dòng không có khu vực cụ thể, ưu tiên số ca theo tuần/kỳ gần nhất, dùng Google Trends + weather làm fallback khi chưa có số ca, và ghi `risk_scores`. |

## 7. Thư mục `src/alerting/`

Các module gửi cảnh báo.

| File | Chức năng |
|---|---|
| `src/alerting/__init__.py` | Đánh dấu thư mục alerting là package. |
| `src/alerting/telegram_alert.py` | Gửi tin nhắn Telegram nếu có `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID`. |
| `src/alerting/email_alert.py` | Gửi email qua SMTP nếu có cấu hình SMTP trong `.env`. |
| `src/alerting/manager.py` | Lấy risk score mức Đỏ, kiểm tra tránh gửi trùng, rồi gọi Telegram/Email. |

## 8. Thư mục `dashboard/`

| File | Chức năng |
|---|---|
| `dashboard/app.py` | Ứng dụng Streamlit. Đọc PostgreSQL, hiển thị KPI, bảng risk score, biểu đồ top rủi ro, bản đồ chấm tròn vùng dịch, diễn biến ca bệnh, Google Trends, WHO theo năm và dữ liệu thời tiết. |

Dashboard chạy tại:

```text
http://localhost:8501
```

## 9. Thư mục `tests/`

| File | Chức năng |
|---|---|
| `tests/test_extract_entities.py` | Kiểm thử trích xuất bệnh, địa điểm, số ca từ câu tiếng Việt. |
| `tests/test_risk_score.py` | Kiểm thử công thức risk score và phân loại cảnh báo. |

Chạy test:

```powershell
python -m pytest -q
```

## 10. Thư mục `data/`

Thư mục dữ liệu giữ lại từ bản trước và dùng làm dữ liệu tham khảo/đối chiếu.

| File/Thư mục | Chức năng |
|---|---|
| `data/reference/hcm_districts.csv` | Danh sách quận/huyện TP.HCM tham khảo. |
| `data/reference/disease_keywords.json` | Bộ từ khóa bệnh truyền nhiễm tham khảo. |
| `data/raw/hcdc_diseases.csv` | Dữ liệu HCDC dạng CSV từ pipeline cũ. |
| `data/raw/gtrends_diseases.csv` | Dữ liệu Google Trends dạng CSV từ pipeline cũ. |
| `data/raw/news_diseases.csv` | Dữ liệu tin tức dạng CSV từ pipeline cũ. |
| `data/raw/who_diseases_vietnam.csv` | Dữ liệu WHO dạng CSV từ pipeline cũ. |
| `data/processed/disease_events_clean.csv` | Dữ liệu đã xử lý từ pipeline cũ. |
| `data/analytics/daily_disease_summary.csv` | Bảng tổng hợp ngày từ pipeline cũ. |
| `data/analytics/alerts.csv` | Bảng cảnh báo từ pipeline cũ. |
| `data/geojson/vietnam.geojson` | GeoJSON Việt Nam, có thể dùng cho bản đồ sau này. |
| `data/charts/who_trends_chart.png` | Biểu đồ ảnh tạo từ dữ liệu WHO cũ. |
| `data/charts/gtrends_stats_chart.png` | Biểu đồ ảnh tạo từ dữ liệu Google Trends cũ. |

Trong MVP mới, dữ liệu runtime chính được lưu trong PostgreSQL, không phụ thuộc vào các CSV này.

## 11. Màu cảnh báo và hiển thị bản đồ

Dashboard dùng bảng màu cố định để tránh nhầm lẫn:

| Mức cảnh báo | Màu |
|---|---|
| `Xanh` | Xanh lá |
| `Vàng` | Vàng |
| `Cam` | Cam |
| `Đỏ` | Đỏ |

Mục `Bản đồ vùng dịch` trong dashboard lấy dữ liệu từ bảng `risk_scores`, ghép tọa độ trong `src/locations.py`, rồi hiển thị chấm tròn bằng Plotly. Người dùng lọc bệnh ở sidebar như `Cúm`, `Sốt xuất huyết`, `Tay chân miệng`; bản đồ chỉ giữ các khu vực tương ứng với bộ lọc hiện tại.

Nếu nguồn tin có nhắc tỉnh/thành khác ngoài TP.HCM, `src/processing/extract_entities.py` sẽ nhận diện địa phương đó và pipeline sẽ tính risk score theo khu vực đó. Những khu vực có tọa độ trong `src/locations.py` sẽ xuất hiện trên bản đồ.

## 12. Kiểm soát chất lượng dữ liệu

Một số bài báo/HCDC có cả số ca tuần hiện tại và số lũy kế từ đầu năm. Để tránh cảnh báo bị phóng đại, pipeline ưu tiên số ca theo tuần/kỳ gần nhất khi tính `risk_scores.cases_7d`. Nếu không có số theo kỳ, hệ thống mới dùng số lũy kế như tín hiệu dự phòng.

Các câu không có địa phương cụ thể sẽ không được gán mặc định thành `Việt Nam`. Điều này tránh trường hợp so sánh sai giữa `Việt Nam` và một tỉnh/thành cụ thể.

Dữ liệu thời tiết không còn lấy TP.HCM làm fallback cho tỉnh khác. Mỗi khu vực dùng weather row riêng nếu có; nếu chưa có dữ liệu thời tiết riêng thì điểm thời tiết bằng 0.

Google Trends được dùng trong hai trường hợp:

- Khi đã có số ca mắc: `trend_score` là tín hiệu phụ, cộng vào risk score cùng số ca và thời tiết.
- Khi chưa có số ca mắc: pipeline vẫn tạo dòng theo bệnh từ Google Trends, dùng `basis=google_trends_weather_fallback` trong `risk_scores.explanation`.

Scheduler mặc định chạy lại pipeline mỗi 60 phút qua `SCHEDULER_INTERVAL_MINUTES=60`.

Công thức phân vùng ổ dịch:

```text
Risk score = ca bệnh * 70% + Google Trends * 20% + thời tiết trễ 7-17 ngày * 10%
```

Thời tiết dùng khoảng trễ 7-17 ngày để phản ánh việc mưa/độ ẩm hôm nay thường không tạo ca bệnh ngay ngày mai.

Dữ liệu WHO hiện được đọc từ `data/raw/who_diseases_vietnam.csv` để vẽ biểu đồ lịch sử theo năm trên dashboard. Đây là dữ liệu nền/lịch sử, không dùng để phát cảnh báo realtime.

## 13. Script cũ còn giữ lại

Các file này thuộc bản triển khai trước, hiện không phải luồng chính của MVP mới. Chúng được giữ lại để tham khảo hoặc tái sử dụng ý tưởng.

| File | Chức năng |
|---|---|
| `crawl_data.py` | Script crawl báo VnExpress cũ, lưu CSV. |
| `visualize_data.py` | Script vẽ biểu đồ PNG từ CSV cũ. |
| `utils.py` | Helper cũ, chủ yếu phục vụ lưu CSV cho crawler cũ. |
| `processing/__init__.py` | Package marker cho thư mục processing cũ. |
| `processing/build_datasets.py` | Pipeline cũ đọc CSV raw, chuẩn hóa, tạo CSV processed/analytics. |
| `crawlers/__init__.py` | Package marker cho crawler cũ. |
| `crawlers/crawl_news.py` | Crawler news cũ lưu CSV. |
| `crawlers/crawl_hcdc.py` | Crawler HCDC cũ lưu CSV. |
| `crawlers/crawl_gtrends.py` | Collector Google Trends cũ lưu CSV. |
| `crawlers/crawl_moh.py` | Crawler Bộ Y tế/VNCDC cũ. |
| `crawlers/crawl_who.py` | Collector WHO cũ. |

## 14. Các bảng PostgreSQL chính

| Bảng | Chức năng |
|---|---|
| `raw_news` | Lưu bài viết/raw text từ news, Tavily search và HCDC. |
| `extracted_events` | Lưu entity đã trích xuất: bệnh, khu vực, số ca, source. |
| `google_trends` | Lưu điểm quan tâm tìm kiếm theo ngày/bệnh. |
| `weather_data` | Lưu thời tiết theo ngày/khu vực. |
| `risk_scores` | Lưu điểm rủi ro và mức cảnh báo. |
| `alerts` | Lưu lịch sử gửi hoặc bỏ qua cảnh báo. |

## 15. Cách đọc code theo thứ tự dễ hiểu

1. Đọc `main.py` để biết chương trình bắt đầu như thế nào.
2. Đọc `src/scheduler.py` để hiểu thứ tự các bước pipeline.
3. Đọc `src/ingestion/crawl_news.py`, `crawl_hcdc.py`, `fetch_google_trends.py`, `fetch_weather.py` để hiểu nguồn dữ liệu.
4. Đọc `src/locations.py` để hiểu danh sách khu vực và tọa độ bản đồ.
5. Đọc `src/processing/extract_entities.py` để hiểu cách trích xuất bệnh, địa điểm, số ca.
6. Đọc `src/processing/risk_score.py` để hiểu cách tính điểm rủi ro.
7. Đọc `src/database.py` để hiểu các bảng PostgreSQL.
8. Đọc `dashboard/app.py` để hiểu dashboard hiển thị dữ liệu ra sao.
