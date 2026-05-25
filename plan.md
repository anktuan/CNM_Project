# PLAN.md — Hệ thống giám sát và cảnh báo bệnh truyền nhiễm thời gian thực tại TP.HCM

## 1. Mục tiêu hệ thống

Xây dựng hệ thống theo dõi bệnh truyền nhiễm gần thời gian thực tại TP.HCM, tập trung ban đầu vào các bệnh:

- Sốt xuất huyết
- Tay chân miệng
- Cúm

Hệ thống cần có khả năng:

- Thu thập dữ liệu tự động từ báo chí, HCDC, Bộ Y tế, Google Trends và dữ liệu thời tiết.
- Trích xuất tên bệnh, địa điểm, số ca mắc và thời gian từ dữ liệu thô.
- Tính điểm nguy cơ dịch bệnh theo quận/huyện.
- Phân loại cảnh báo thành 4 mức: Xanh, Vàng, Cam, Đỏ.
- Hiển thị dữ liệu trên dashboard.
- Gửi cảnh báo qua Telegram hoặc Email khi nguy cơ vượt ngưỡng.

---

## 2. Kiến trúc tổng quát

Hệ thống gồm các module chính:

```text
Data Sources
│
├── HCDC / Bộ Y tế
├── Báo chí: VnExpress, Tuổi Trẻ, Thanh Niên
├── Google Trends
└── Open-Meteo Weather API

        ↓

Data Ingestion Pipeline
│
├── Web Scraper
├── API Collector
└── Scheduler / Cron Job

        ↓

Data Processing
│
├── Text Cleaning
├── NLP / Regex Extraction
├── Entity Recognition
└── Risk Scoring Engine

        ↓

Database
│
├── raw_news
├── google_trends
├── weather_data
└── risk_scores

        ↓

Dashboard & Alerting
│
├── Streamlit Dashboard
├── Map / Chart Visualization
└── Telegram / Email Alert


