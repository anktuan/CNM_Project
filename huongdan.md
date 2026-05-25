# Hướng dẫn chạy Hệ thống theo dõi bệnh truyền nhiễm thời gian thực

Tài liệu này hướng dẫn chạy hệ thống giám sát bệnh truyền nhiễm tại Việt Nam trên máy local bằng Docker hoặc Python trực tiếp.

## 1. Yêu cầu môi trường

- Python 3.11
- Docker Desktop
- PostgreSQL nếu chạy không dùng Docker
- Kết nối Internet để crawl dữ liệu từ RSS, HCDC, Google Trends và Open-Meteo

## 2. Chạy nhanh bằng Docker

Đây là cách khuyến nghị vì PostgreSQL, scheduler và dashboard được cấu hình sẵn.

```powershell
cd E:\Hoc_ky_2_2025_2026\CNM\CNM_Project
docker compose up --build
```

Sau khi chạy thành công:

- Dashboard: http://localhost:8501
- PostgreSQL: `localhost:5432`
- Scheduler tự chạy định kỳ theo biến `SCHEDULER_INTERVAL_MINUTES` trong `.env`, mặc định là 60 phút.
- Dashboard có bảng rủi ro, biểu đồ, bản đồ chấm tròn vùng dịch và bộ lọc theo bệnh/mức cảnh báo.
- Dashboard có thêm biểu đồ Google Trends và biểu đồ WHO theo năm.
- Hệ thống chỉ hiển thị các khu vực cụ thể trong Việt Nam, không hiển thị dòng tổng quát `Việt Nam`.

Nếu dữ liệu chưa tự cập nhật, kiểm tra service scheduler:

```powershell
docker compose ps
docker compose logs -f scheduler
```

Scheduler chỉ tự crawl khi container `cnm_scheduler` đang chạy. Mặc định service này chạy ngay một lượt khi khởi động và lặp lại mỗi 60 phút.

Chạy ở chế độ nền:

```powershell
docker compose up -d --build
```

Xem trạng thái container:

```powershell
docker compose ps
```

Xem log:

```powershell
docker compose logs -f scheduler
docker compose logs -f dashboard
```

Dừng hệ thống:

```powershell
docker compose down
```

## 3. Chạy một lần pipeline bằng Docker

Lệnh này dùng để thu thập dữ liệu, xử lý, tính điểm rủi ro một lần rồi thoát.

```powershell
docker compose run --rm scheduler python main.py run-once --no-alerts
```

Bỏ `--no-alerts` nếu đã cấu hình Telegram hoặc Email và muốn gửi cảnh báo:

```powershell
docker compose run --rm scheduler python main.py run-once
```

## 4. Chạy local bằng Python

Tạo môi trường ảo:

```powershell
cd E:\Hoc_ky_2_2025_2026\CNM\CNM_Project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Cài thư viện:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Tạo file `.env` từ mẫu nếu chưa có:

```powershell
Copy-Item .env.example .env
```

Chạy PostgreSQL bằng Docker riêng:

```powershell
docker compose up -d db
```

Chạy pipeline một lần:

```powershell
python main.py run-once --no-alerts
```

Chạy scheduler:

```powershell
python main.py scheduler
```

Chạy dashboard:

```powershell
streamlit run dashboard/app.py
```

Mở dashboard tại:

```text
http://localhost:8501
```

## 5. Cấu hình `.env`

Các biến quan trọng:

```env
APP_ENV=development
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://atuans_admin:atuans2026@localhost:5432/cnm_disease_db
REQUEST_TIMEOUT_SECONDS=20
REQUEST_RETRIES=3
SCHEDULER_INTERVAL_MINUTES=60
DASHBOARD_REFRESH_SECONDS=300
REALTIME_LOOKBACK_DAYS=14
OCR_ENABLED=false
```

Cấu hình Telegram nếu muốn gửi cảnh báo mức Đỏ:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Cấu hình Email nếu muốn gửi cảnh báo mức Đỏ:

```env
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
```

Hoặc dùng dạng Gmail alias:

```env
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_TO=
```

Nếu dùng Gmail, hệ thống tự dùng `smtp.gmail.com:587` khi có `EMAIL_USER`.

Cấu hình AI tra cứu bệnh:

```env
GEMINI_API_KEY=
TAVILY_API_KEY=
```

Nếu bạn đang dùng tên biến bị gõ nhầm `TAVITY_API_KEY`, hệ thống vẫn hỗ trợ alias này.

Email có thể gửi đến nhiều Gmail cùng lúc bằng cách phân tách người nhận bằng dấu phẩy hoặc dấu chấm phẩy:

```env
EMAIL_TO=nguoinhan1@gmail.com,nguoinhan2@gmail.com
```

Nếu dùng Docker Compose, service `scheduler` và `dashboard` tự dùng database URL nội bộ trỏ đến host `db`.

Hệ thống chỉ gửi thông báo khi risk score được phân loại mức `Đỏ`. Các mức `Xanh`, `Vàng`, `Cam` vẫn hiển thị trên dashboard nhưng không kích hoạt gửi Telegram/Email. Hệ thống cũng kiểm tra lịch sử bảng `alerts` để không gửi trùng cùng một risk score qua cùng một kênh.

## 6. Kiểm tra hệ thống

Chạy test:

```powershell
python -m pytest -q
```

Kiểm tra cú pháp Python:

```powershell
python -m compileall src dashboard main.py
```

Kiểm tra Docker Compose config:

```powershell
docker compose config
```

## 7. Luồng chạy chính

1. `main.py` nhận lệnh `run-once` hoặc `scheduler`.
2. `src/scheduler.py` khởi tạo database, gọi các collector dữ liệu.
3. Các file trong `src/ingestion/` lấy dữ liệu từ nguồn ngoài.
4. `src/processing/pipeline.py` trích xuất ca bệnh, bỏ câu không có khu vực cụ thể và tính điểm rủi ro.
5. `src/locations.py` gắn khu vực với tọa độ để hiển thị bản đồ chấm tròn.
6. `src/alerting/manager.py` gửi cảnh báo nếu điểm rủi ro đạt mức Đỏ.
7. `dashboard/app.py` đọc dữ liệu PostgreSQL và hiển thị dashboard.

## 8. Màu cảnh báo và bản đồ

Màu cảnh báo trên dashboard được cố định như sau:

| Mức | Ý nghĩa | Màu |
|---|---|---|
| `Xanh` | Rủi ro thấp | Xanh lá |
| `Vàng` | Cần theo dõi | Vàng |
| `Cam` | Rủi ro cao | Cam |
| `Đỏ` | Cảnh báo nghiêm trọng, có gửi thông báo nếu đã cấu hình | Đỏ |

Khi chọn một hoặc nhiều bệnh trong sidebar, mục `Bản đồ vùng dịch` sẽ hiển thị các khu vực có dữ liệu bằng chấm tròn. Kích thước chấm tăng theo điểm rủi ro, màu chấm theo mức cảnh báo.

Hệ thống có thể hiển thị thêm tỉnh/thành khác ngoài TP.HCM nếu nguồn tin crawl được có nhắc địa phương đó và trích xuất được bệnh/số ca.

## 9. Cách xử lý dữ liệu ca bệnh và thời tiết

Hệ thống không tạo dòng tổng hợp `Việt Nam` vì yêu cầu chỉ theo dõi các tỉnh/thành hoặc quận/huyện cụ thể. Nếu một câu chỉ nói chung chung như `ghi nhận 916 ca tay chân miệng` mà không có địa phương, câu đó sẽ bị bỏ qua trong bước trích xuất.

Với risk score, hệ thống ưu tiên số ca theo tuần/kỳ gần nhất. Nếu cùng một bài có cả số ca lũy kế từ đầu năm và số ca trong tuần, số ca trong tuần được dùng để tính cảnh báo hiện tại. Số lũy kế vẫn xuất hiện trong bảng diễn biến để tham khảo nguồn.

Dữ liệu thời tiết hiện được lấy theo danh sách khu vực trong `src/locations.py`, gồm tỉnh/thành Việt Nam và một số quận/huyện TP.HCM. Tỉnh khác không còn dùng nhầm thời tiết TP.HCM; nếu khu vực chưa có weather row riêng thì `weather_score` sẽ là 0.

Google Trends được lưu trong bảng `google_trends` và đưa vào `trend_score`. Nếu một bệnh chưa có số ca mắc cụ thể trong kỳ gần đây, pipeline vẫn tạo dòng risk score từ Google Trends và thời tiết với `basis=google_trends_weather_fallback` trong cột `explanation`. Nếu đã có số ca mắc, Google Trends vẫn được cộng như một tín hiệu phụ bên cạnh ca bệnh và thời tiết.

Google Trends hiện lấy nhiều từ khóa/chủ đề hơn như `cúm A`, `cúm B`, `sốt rét`, `sởi`, `thủy đậu`, `đau mắt đỏ`, `thuốc bôi tay chân miệng`. Dữ liệu được làm mượt bằng trung bình trượt 7 ngày trước khi lưu vào PostgreSQL.

## 10. Công thức phân vùng ổ dịch

Risk score được tính trên thang 100:

```text
Risk score = ca bệnh * 70% + Google Trends * 20% + thời tiết trễ 7-17 ngày * 10%
```

Trong đó:

- `ca bệnh`: số ca theo tuần/kỳ gần nhất, chuẩn hóa theo ngưỡng từng bệnh. Nếu đã có báo cáo ca bệnh, tín hiệu này được ưu tiên cao nhất vì xác suất đang có ổ dịch là lớn hơn.
- `Google Trends`: điểm tìm kiếm đã làm mượt bằng trung bình trượt 7 ngày, dùng như tín hiệu sớm hoặc tín hiệu phụ.
- `thời tiết`: điểm nguy cơ từ mưa, độ ẩm, nhiệt độ trong khoảng 7-17 ngày trước ngày đánh giá để phản ánh độ trễ thời gian của dịch, nhất là sốt xuất huyết.

Mức cảnh báo:

| Điểm | Mức |
|---|---|
| `< 25` | Xanh |
| `25 - 49.9` | Vàng |
| `50 - 74.9` | Cam |
| `>= 75` | Đỏ |

## 11. OCR ảnh/PDF số liệu

Nếu HCDC đăng ảnh thống kê thay vì bảng HTML, có thể bật OCR:

```env
OCR_ENABLED=true
```

Code dùng `pytesseract` theo kiểu optional. Nếu bật OCR nhưng máy/container chưa có Tesseract binary, pipeline sẽ ghi log cảnh báo và tiếp tục chạy nguồn text/RSS bình thường.

## 12. Kiểm tra email cảnh báo

Sau khi cấu hình email, chạy:

```powershell
docker compose run --rm scheduler python main.py run-once
```

Kiểm tra lịch sử gửi:

```powershell
docker compose exec db psql -U atuans_admin -d cnm_disease_db -c "select channel, status, created_at from alerts order by created_at desc limit 10;"
```

Nếu `status` là `sent`, email đã được SMTP chấp nhận gửi. Nếu `email_not_configured`, cần kiểm tra lại biến `EMAIL_USER`, `EMAIL_PASSWORD`, `ALERT_EMAIL_TO` hoặc nhóm `SMTP_*`.

Nội dung email cảnh báo được trình bày theo dạng:

```text
CẢNH BÁO Đỏ: Sốt xuất huyết tại TP. Hồ Chí Minh
Điểm rủi ro tổng hợp: 98.1/100.
Số ca dùng để tính cảnh báo trong kỳ gần đây: 414 ca.
Tín hiệu Google Trends: 12.5/100.
Điểm nguy cơ thời tiết: 40.0/40.
```

## 13. Xem dữ liệu trong PGAdmin

Database chạy trong Docker container `cnm_disease_db`. Khi kết nối từ PGAdmin trên máy Windows, dùng thông tin:

```text
Host name/address: localhost
Port: 5433
Maintenance database: cnm_disease_db
Username: atuans_admin
Password: atuans2026
```

Lưu ý: bên trong Docker network, app dùng host `db` và port `5432`; nhưng từ PGAdmin trên máy host phải dùng `localhost:5433` vì `docker-compose.yml` đang map `5433:5432`.

Các bảng chính nằm trong schema `public`:

- `raw_news`
- `extracted_events`
- `google_trends`
- `weather_data`
- `risk_scores`
- `alerts`

Nếu không thấy bảng, hãy refresh tree trong PGAdmin: `Servers > Databases > cnm_disease_db > Schemas > public > Tables`.

## 14. Lỗi thường gặp

### Không kết nối được database

Kiểm tra container PostgreSQL:

```powershell
docker compose ps
docker compose logs db
```

Nếu volume PostgreSQL cũ dùng user/password khác, có thể cần xóa volume để khởi tạo lại database. Chỉ chạy lệnh này khi chấp nhận mất dữ liệu PostgreSQL trong Docker volume:

```powershell
docker compose down -v
docker compose up -d db
```

### Dashboard báo chưa có dữ liệu

Chạy pipeline trước:

```powershell
docker compose run --rm scheduler python main.py run-once --no-alerts
```

Sau đó refresh dashboard.

### Google Trends lỗi hoặc bị giới hạn

Google Trends có thể giới hạn request. Hệ thống sẽ ghi log và tiếp tục các nguồn còn lại.

### Website nguồn thay đổi cấu trúc

Các crawler dùng HTML/RSS thật, nên nếu trang nguồn thay đổi layout, có thể cần cập nhật file trong `src/ingestion/`.
