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