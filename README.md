# E-Commerce Customer Behavior Analytics & Sales Decision Support System

## DBMS Course Project — SY Engineering / 3rd Semester

A PostgreSQL-backed desktop application that analyzes e-commerce customer behavior, detects business problems, predicts outcomes, and recommends evidence-based actions.

## Architecture

```
Event Data → PostgreSQL → Analytics → ML → Problem Detection → Recommendation → Decision
```

## Project Structure

```
├── database/                     # SQL scripts
│   ├── 01_create_tables.sql      # 14 tables with constraints, indexes
│   ├── 02_views.sql              # Materialized views & regular views
│   ├── 03_procedures_triggers.sql # Stored procedures, functions, triggers
│   ├── 04_transactions.sql       # ACID transaction demonstrations
│   └── 05_security.sql           # Role-based access control
│
├── dataset/                      # Real-world e-commerce datasets
│   └── Amazon_Reviews.csv        # 21,000+ real customer reviews & feedback
│
├── src/                          # Python application
│   ├── config.py                 # Configuration
│   ├── database/                 # DB connection manager & seed generator
│   ├── analytics/                # SQL analytics module & telemetry queries
│   ├── ml/                       # ML models, NLP review loader & feature engineering
│   ├── engine/                   # Problem detection & recommendation engine
│   ├── simulator/                # Multi-threaded event simulator
│   └── gui/                      # PySide6 desktop application
│       ├── main_window.py        # Main window with sidebar navigation
│       └── pages/                # Application pages
│           ├── dashboard_page.py # Live KPI cards & Real-Time Event Ticker
│           ├── customer_page.py  # RFM segmentation & Customer Explorer
│           ├── product_page.py   # Catalog performance & Problem product detector
│           ├── funnel_page.py    # Conversion funnel & Device analytics
│           ├── reviews_page.py   # Voice of Customer & Live NLP Testing Studio
│           ├── problems_page.py  # Prioritized bottlenecks & Root cause evidence
│           ├── predictions_page.py # 3 ML models & Live What-If Simulator
│           └── simulator_page.py # Event generator & Scenario presets
│
├── main.py                       # Application entry point
├── setup_database.py             # One-click database setup & seeding
└── requirements.txt              # Python dependencies
```

## Quick Start

### 1. Install PostgreSQL 15+

Download from [postgresql.org](https://www.postgresql.org/download/)

### 2. Create the database

```bash
psql -U postgres -c "CREATE DATABASE ecom_analytics;"
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database connection

Edit `src/config.py` with your PostgreSQL credentials.

### 5. Setup database (creates tables + seeds data with Amazon Reviews)

```bash
python setup_database.py
```

### 6. Run the application

```bash
python main.py
```

## Core Features & Intelligence Layers

- **Executive Dashboard**: Real-time KPI cards, Customer Sentiment Index, and Live Event & Transaction Pulse Stream.
- **Reviews & Sentiment Intelligence Studio**:
  - Browse verified real-world Amazon customer reviews.
  - Interactive **Live AI NLP Playground**: Type any custom customer feedback and get instant sentiment classification, star prediction (1–5★), confidence meters, and positive/negative keyword triggers.
  - Multi-aspect topic classification (Delivery, Product Quality, Customer Service, Pricing, Account/App).
- **Machine Learning Hub & Interactive What-If Simulator**:
  - **Purchase Prediction Model**: Random Forest + Logistic Regression (98%+ accuracy).
  - **Cart Abandonment Model**: Random Forest classifier with behavioral feature importance.
  - **Review Sentiment & Rating NLP Model**: TF-IDF + Multinomial Logistic Regression (85.5% accuracy, 0.873 F1) trained on 21,000+ real reviews.
  - **Live What-If Sandbox**: Interactive sliders (Cart Value, Duration, Views, Items Removed, Device, Segment) with instant real-time probability dials and proactive action recommendations.
- **Problem Detection & Decision Support**: Auto-detects conversion drops, logistics/delivery complaint spikes, refund bottlenecks, and customer churn risk with evidence chains.
- **Real-Time Multi-Threaded Simulator**: Simulates high-intent, mobile friction, and normal customer traffic in real time.

## Technology Stack

| Layer | Technology |
| ------- | ----------- |
| Database | PostgreSQL 15+ |
| Language | Python 3.11+ / 3.14 |
| GUI | PySide6 (Qt for Python) |
| Analytics & Data | Pandas, NumPy |
| Machine Learning | Scikit-learn (RandomForest, TF-IDF, LogisticRegression, NaiveBayes) |
| DB Connectivity | psycopg2-binary |

## License

This project is developed for academic purposes at VIT as a 3rd-semester Computer Engineering project.
