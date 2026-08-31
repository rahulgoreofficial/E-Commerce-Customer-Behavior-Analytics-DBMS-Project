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
├── src/                          # Python application
│   ├── config.py                 # Configuration
│   ├── database/                 # DB connection manager
│   ├── analytics/                # SQL analytics module
│   ├── ml/                       # ML models & feature engineering
│   ├── engine/                   # Problem detection & recommendation
│   ├── simulator/                # Event simulator
│   └── gui/                      # PySide6 desktop application
│       ├── main_window.py        # Main window with sidebar
│       └── pages/                # Application pages
│           ├── dashboard_page.py
│           ├── customer_page.py
│           ├── product_page.py
│           ├── funnel_page.py
│           ├── problems_page.py
│           ├── predictions_page.py
│           └── simulator_page.py
│
├── main.py                       # Application entry point
├── setup_database.py             # One-click database setup
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

### 5. Setup database (creates tables + seeds data)
```bash
python setup_database.py
```

### 6. Run the application
```bash
python main.py
```

## Features

- **Dashboard**: KPI cards, revenue trends, funnel overview, segment distribution
- **Customer Analytics**: RFM segmentation, customer lifecycle, behavior timeline
- **Product Analytics**: Performance metrics, problem products detection
- **Funnel Analytics**: View→Cart→Checkout→Purchase with device/channel breakdown
- **Problem Detection**: Auto-detect conversion drops, cart abandonment spikes, churn risk
- **ML Predictions**: Purchase prediction, cart abandonment prediction (Random Forest)
- **Event Simulator**: Generate realistic e-commerce events with configurable scenarios
- **What-If Analysis**: Impact estimation with stated assumptions

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Database | PostgreSQL 15+ |
| Language | Python 3.11+ |
| GUI | PySide6 |
| Analytics | Pandas, NumPy |
| ML | Scikit-learn |
| DB Connectivity | psycopg2 |
