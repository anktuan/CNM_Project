3. Công nghệ sử dụng
Backend / Data Pipeline
Python 3.11+
requests
BeautifulSoup4
Scrapy
pandas
numpy
schedule hoặc cron
pytrends
openmeteo API
NLP / Xử lý văn bản
regex
underthesea
VnCoreNLP hoặc PhoBERT nếu cần nâng cấp
Database

Ưu tiên dùng:

PostgreSQL

Có thể thay thế bằng:

SQLite cho bản demo đơn giản
MongoDB nếu dữ liệu phi cấu trúc nhiều
Dashboard
Streamlit
Plotly
Folium hoặc geopandas
GeoJSON TP.HCM
Alert
Telegram Bot API
smtplib gửi Email
Deployment
Docker
docker-compose
VPS Ubuntu
4. Cấu trúc thư mục đề xuất
infectious-disease-monitoring/
│
├── README.md
├── PLAN.md
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── geojson/
│
├── src/
│   ├── config.py
│   ├── database.py
│   │
│   ├── ingestion/
│   │   ├── crawl_hcdc.py
│   │   ├── crawl_news.py
│   │   ├── fetch_google_trends.py
│   │   └── fetch_weather.py
│   │
│   ├── processing/
│   │   ├── clean_text.py
│   │   ├── extract_entities.py
│   │   └── risk_score.py
│   │
│   ├── alerting/
│   │   ├── telegram_alert.py
│   │   └── email_alert.py
│   │
│   └── scheduler.py
│
├── dashboard/
│   └── app.py
│
└── tests/
    ├── test_extract_entities.py
    ├── test_risk_score.py
    └── test_pipeline.py
5. Các bước Codex cần thực hiện
Bước 1: Khởi tạo project

Tạo project Python với các file:

README.md
PLAN.md
requirements.txt
.env.example
src/config.py
src/database.py

Thiết lập biến môi trường trong .env.example:

DATABASE_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EMAIL_USER=
EMAIL_PASSWORD=
Bước 2: Tạo database schema

Tạo các bảng:

raw_news (
    id,
    source,
    url,
    title,
    content,
    published_at,
    crawled_at
)

google_trends (
    id,
    disease,
    keyword,
    location,
    trend_score,
    collected_at
)

weather_data (
    id,
    location,
    temperature,
    humidity,
    rainfall,
    collected_at
)

risk_scores (
    id,
    disease,
    district,
    risk_score,
    risk_level,
    created_at
)
Bước 3: Viết module crawl báo chí

Tạo file:

src/ingestion/crawl_news.py

Chức năng:

Crawl bài viết từ VnExpress, Tuổi Trẻ, Thanh Niên.
Lọc bài viết liên quan đến:
sốt xuất huyết
tay chân miệng
cúm
Lưu các trường:
nguồn
URL
tiêu đề
nội dung
thời gian crawl
Bước 4: Viết module crawl nguồn chính thống

Tạo file:

src/ingestion/crawl_hcdc.py

Chức năng:

Crawl tin tức từ HCDC.
Crawl tin tức từ Cục Y tế Dự phòng nếu có thể.
Parse tiêu đề, nội dung, ngày đăng.
Lưu vào bảng raw_news.
Bước 5: Viết module Google Trends

Tạo file:

src/ingestion/fetch_google_trends.py

Chức năng:

Dùng pytrends.
Lấy chỉ số tìm kiếm theo từ khóa bệnh.
Khu vực ưu tiên: TP.HCM hoặc Việt Nam.
Lưu vào bảng google_trends.
Bước 6: Viết module thời tiết

Tạo file:

src/ingestion/fetch_weather.py

Chức năng:

Gọi Open-Meteo API.
Lấy dữ liệu:
nhiệt độ
độ ẩm
lượng mưa
Khu vực: TP.HCM.
Lưu vào bảng weather_data.
Bước 7: Viết module xử lý văn bản

Tạo file:

src/processing/clean_text.py
src/processing/extract_entities.py

Chức năng:

Làm sạch HTML, ký tự thừa.
Chuẩn hóa tiếng Việt.
Trích xuất:
tên bệnh
quận/huyện
số ca mắc
thời gian
Dùng regex trước, có thể nâng cấp bằng Underthesea.
Bước 8: Viết Risk Scoring Engine

Tạo file:

src/processing/risk_score.py

Công thức gợi ý:

Risk Score =
0.4 * disease_severity
+ 0.25 * news_frequency
+ 0.2 * google_trend_score
+ 0.15 * weather_risk

Phân loại mức cảnh báo:

0 - 25    : Xanh
26 - 50   : Vàng
51 - 75   : Cam
76 - 100  : Đỏ

Lưu kết quả vào bảng risk_scores.

Bước 9: Viết module cảnh báo

Tạo file:

src/alerting/telegram_alert.py
src/alerting/email_alert.py

Logic:

Kiểm tra bản ghi mới trong risk_scores.
Nếu risk_level là Cam hoặc Đỏ, gửi cảnh báo.
Nội dung cảnh báo gồm:
tên bệnh
quận/huyện
điểm nguy cơ
mức cảnh báo
thời gian phát hiện
Bước 10: Viết scheduler

Tạo file:

src/scheduler.py

Lịch chạy:

Crawl báo chí       : mỗi 3 giờ
Crawl HCDC          : mỗi 6 giờ
Google Trends       : mỗi 24 giờ
Weather API         : mỗi 6 giờ
Risk Scoring        : sau mỗi lần cập nhật dữ liệu
Alert Checking      : sau khi tính Risk Score
Bước 11: Xây dựng dashboard

Tạo file:

dashboard/app.py

Dashboard cần có:

Bộ lọc theo bệnh.
Bộ lọc theo quận/huyện.
Thẻ tổng quan:
số bài viết mới
bệnh có nguy cơ cao nhất
quận/huyện nguy cơ cao nhất
Bản đồ nhiệt TP.HCM.
Biểu đồ đường theo thời gian.
Bảng cảnh báo mới nhất.
Bước 12: Docker hóa project

Tạo:

Dockerfile
docker-compose.yml

docker-compose.yml cần chạy được:

app dashboard
database PostgreSQL
scheduler worker
6. Yêu cầu chất lượng code

Codex cần đảm bảo:

Code chia module rõ ràng.
Có logging.
Có try/except khi crawl.
Có timeout khi gọi request.
Có User-Agent header.
Không hard-code token.
Dùng .env.
Có test cơ bản cho:
extract entity
risk scoring
database connection
7. Kết quả cuối cùng mong muốn

Sau khi hoàn thành, project phải chạy được bằng lệnh:

docker-compose up --build

Hoặc chạy local:

pip install -r requirements.txt
python src/scheduler.py
streamlit run dashboard/app.py

Hệ thống cần hiển thị dashboard và tự động cảnh báo khi phát hiện nguy cơ dịch bệnh mức Cam hoặc Đỏ.