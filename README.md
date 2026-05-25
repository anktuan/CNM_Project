# Hệ thống theo dõi bệnh truyền nhiễm thời gian thực

MVP production-ready cho giám sát gần thời gian thực các bệnh: sốt xuất huyết, tay chân miệng và cúm. Hệ thống thu thập dữ liệu từ báo chí, HCDC, Google Trends và Open-Meteo, trích xuất ca bệnh, tính điểm rủi ro theo khu vực, hiển thị dashboard Streamlit và gửi cảnh báo qua Telegram hoặc Email khi có cảnh báo mức Đỏ.

Dashboard hỗ trợ:

- Bảng rủi ro theo bệnh và khu vực.
- Biểu đồ top điểm rủi ro với màu cố định: Xanh, Vàng, Cam, Đỏ.
- Bản đồ chấm tròn biểu diễn vùng dịch theo bệnh đang chọn.
- Biểu đồ Google Trends như tín hiệu quan tâm tìm kiếm.
- Biểu đồ WHO theo năm từ dữ liệu lịch sử trong `data/raw/who_diseases_vietnam.csv`.
- Công thức phân vùng ổ dịch: `ca bệnh * 70% + Google Trends * 20% + thời tiết trễ 7-17 ngày * 10%`.
- Tra cứu AI qua Gemini/Tavily nếu cấu hình `GEMINI_API_KEY` và `TAVILY_API_KEY`.
- OCR ảnh thống kê HCDC nếu bật `OCR_ENABLED=true` và container/máy có Tesseract.
- Chỉ hiển thị khu vực cụ thể là tỉnh/thành/quận/huyện; không dùng dòng tổng quát `Việt Nam`.
- Nhận diện thêm tỉnh/thành khác trong Việt Nam nếu nguồn tin có nhắc đến.
- Ưu tiên số ca theo tuần/kỳ gần nhất cho risk score; số lũy kế vẫn hiển thị tham khảo nhưng không lấn át cảnh báo hiện tại khi có số tuần.
- Scheduler mặc định cập nhật dữ liệu mỗi 60 phút.
- Google Trends và thời tiết được dùng song song; nếu chưa có số ca mắc, hệ thống dùng trend + weather làm tín hiệu fallback.

## Chạy bằng Docker

```bash
cp .env.example .env
docker compose up --build
```

Dashboard: http://localhost:8501

Tài liệu pipeline trực quan: [`pipeline.md`](pipeline.md)

## Chạy local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py run-once
streamlit run dashboard/app.py
```

## Cấu trúc chính

- `src/config.py`: đọc cấu hình từ `.env`
- `src/database.py`: schema PostgreSQL và helper truy vấn
- `src/locations.py`: danh sách tỉnh/thành, quận/huyện và tọa độ hiển thị bản đồ
- `src/ingestion/`: crawl RSS/HCDC, Google Trends, Open-Meteo
- `src/processing/`: làm sạch text, trích xuất entity, tính điểm rủi ro
- `src/ai_research.py`: tra cứu AI bằng Gemini/Tavily
- `src/alerting/`: Telegram và Email cho cảnh báo mức Đỏ, có kiểm tra tránh gửi trùng cùng risk score
- `src/scheduler.py`: scheduler định kỳ
- `dashboard/app.py`: dashboard Streamlit
- `tests/`: unit tests cho extraction và risk scoring

## Lệnh vận hành

```bash
python main.py run-once --no-alerts
python main.py scheduler
pytest
```

Hệ thống không sinh dữ liệu giả. Khi nguồn ngoài lỗi hoặc giới hạn truy cập, pipeline ghi log vào `logs/app.log` và tiếp tục các nguồn còn lại.
