# Weekly Business Review (WBR) for an E-Commerce Marketplace
### Olist Brazilian E-Commerce Analytics, PostgreSQL ELT Pipeline & Full-Stack Dashboard

![Project Status](https://img.shields.io/badge/Status-Complete-emerald)
![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E)
![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.12-blue)
![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20TypeScript%20%7C%20Vite%20%7C%20Tailwind-61DAFB)
![Tests](https://img.shields.io/badge/Tests-11%20Passed%20(Pytest)-brightgreen)

---

## Table of Contents
1. [Executive Summary & Architecture](#1-executive-summary--architecture)
2. [Prerequisites & Repository Layout](#2-prerequisites--repository-layout)
3. [Step-by-Step Windows PowerShell Setup](#3-step-by-step-windows-powershell-setup)
4. [Configuring Supabase PostgreSQL](#4-configuring-supabase-postgresql)
5. [Placing Dataset Files](#5-placing-dataset-files)
6. [Applying Database Migrations](#6-applying-database-migrations)
7. [Running the Idempotent ELT Pipeline](#7-running-the-idempotent-elt-pipeline)
8. [Executing SQL Data Quality Checks](#8-executing-sql-data-quality-checks)
9. [Running the Five Analytical Queries](#9-running-the-five-analytical-queries)
10. [Generating Publication Charts & 5-Page PDF](#10-generating-publication-charts--5-page-pdf)
11. [Launching the Web Application (Backend & Frontend)](#11-launching-the-web-application-backend--frontend)
12. [Running Automated Tests](#12-running-automated-tests)
13. [Version Control & Safe GitHub Push](#13-version-control--safe-github-push)
14. [Troubleshooting Guide](#14-troubleshooting-guide)
15. [Viva Defense & Interview Cheatsheet](#15-viva-defense--interview-cheatsheet)

---

## 1. Executive Summary & Architecture

This repository delivers a production-grade, enterprise Weekly Business Review (WBR) solution analyzing the Brazilian Olist E-Commerce dataset (~100,000 orders spanning 2016 to 2018).

The project is structured around a three-tier logical data architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Kaggle Raw CSV Files                          │
│          (9 CSV datasets placed in data/raw/ directory)                │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼ [Stage 4: Idempotent Batch Ingestion]
┌────────────────────────────────────────────────────────────────────────┐
│                        1. RAW LAYER (raw_*)                            │
│  • raw_orders          • raw_order_items      • raw_order_payments     │
│  • raw_order_reviews   • raw_customers        • raw_products           │
│  • raw_sellers         • raw_geolocation      • raw_category_trans     │
│  (Preserves source strings, audit timestamp, ON CONFLICT upserting)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼ [Stage 5: Normalization & Cleansing]
┌────────────────────────────────────────────────────────────────────────┐
│                     2. STAGING LAYER (stg_*)                           │
│  • Explicit type casting to TIMESTAMPTZ, NUMERIC, and INTEGER          │
│  • Whitespace trimmed; blank strings normalized to NULL                │
│  • Deduplication of reviews by latest answer/creation timestamp        │
│  • Translation of Portuguese product category names to English         │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼ [Stage 6: Pre-Aggregated CTE Joins]
┌────────────────────────────────────────────────────────────────────────┐
│                     3. MART LAYER (mart_order_performance)             │
│  • Exactly ONE row per order_id (Strict 1:1 Grain)                     │
│  • Items, payments, and reviews aggregated independently in CTEs       │
│  • Fan-out prevented: financial sums NEVER duplicated                  │
│  • Flags: is_on_time, delivery_delay_days, is_repeat_purchase          │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌────────────────────────────────────┐ ┌─────────────────────────────────┐
│     SQL Data Quality Suite         │ │      Five Analytical Queries    │
│  • 6 independent SQL gate checks   │ │  01. MoM Revenue Growth (LAG)   │
│  • CRITICAL (halts on failure)     │ │  02. Top Categories by State    │
│  • WARNING (tolerances logged)     │ │  03. 7-Day Rolling Daily Orders │
│  • Logged to pipeline_quality_audit│ │  04. Repeat Purchase Rate %     │
└────────────────────────────────────┘ │  05. Delivery Delay vs Review   │
                                       └────────────────┬────────────────┘
                                                        │
                   ┌────────────────────────────────────┼────────────────┐
                   ▼                                    ▼                ▼
┌────────────────────────────────────┐ ┌───────────────────────────┐ ┌───┴──────────┐
│        FastAPI REST Server         │ │    Matplotlib & ReportLab │ │  React + Vite │
│  Endpoints: /api/kpis, /api/health │ │  • 4 High-Res PNG Charts  │ │  • Enterprise │
│  /api/analytics/*, /api/quality/*  │ │  • 5-Page PDF + VP Memo   │ │    Dashboard  │
└────────────────────────────────────┘ └───────────────────────────┘ └───────────────┘
```

---

## 2. Prerequisites & Repository Layout

### Prerequisites
- **Operating System:** Windows 10/11 (using Windows PowerShell)
- **Python:** 3.11+ or 3.12 (Checked: Python 3.12.7)
- **Node.js:** v18+ or v20+ (Checked: v22.16.0 with npm 10.9.2)
- **Supabase Account:** Free tier PostgreSQL instance at [supabase.com](https://supabase.com)

### Directory Structure
```
e:\BDA/
├── backend/
│   ├── config.py                 # Central config, .env loader & DB URL normalizer
│   ├── db/
│   │   ├── connection.py         # SQLAlchemy & psycopg engine manager
│   │   └── migrations.py         # Schema migration orchestrator
│   ├── pipeline/
│   │   ├── extract.py            # Pre-flight CSV existence & column checker
│   │   ├── load_raw.py           # Idempotent batch loader (ON CONFLICT)
│   │   ├── transform_stg.py      # Cleansing, casting & deduplication
│   │   ├── build_mart.py         # Mart builder with fan-out prevention
│   │   └── run.py                # Pipeline entrypoint (python -m backend.pipeline.run)
│   ├── quality/
│   │   └── runner.py             # Quality check executor & audit logger
│   ├── analytics/
│   │   └── runner.py             # 5 SQL analytical query runners
│   └── api/
│       └── app.py                # FastAPI dashboard REST API
├── sql/
│   ├── schema/                   # 01_raw_schema.sql, 02_staging_schema.sql, 03_mart_schema.sql
│   ├── quality/                  # 6 standalone quality check SQL scripts
│   └── analytics/                # 5 pure SQL analytical query scripts
├── data/
│   └── raw/                      # Destination directory for all 9 Olist CSV files
├── reports/
│   ├── charts/                   # Matplotlib generated PNG charts (01 to 04)
│   ├── output/                   # 5-page ReportLab PDF & VP memo
│   ├── generate_charts.py        # Chart generation script
│   └── generate_pdf.py           # PDF compiler script
├── frontend/                     # React 18, TypeScript, Vite, Tailwind CSS, Recharts
│   ├── src/
│   │   ├── components/           # Sidebar, Header, KpiCard, SetupBanner
│   │   ├── pages/                # 6 views: Overview, Revenue, Categories, Delivery, Quality, Runs
│   │   ├── api/client.ts         # REST API consumer
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── tests/
│   ├── conftest.py               # Mock CSV data and in-memory test database fixture
│   ├── test_extract.py           # Missing files & missing columns tests
│   ├── test_idempotency.py       # Pipeline re-run & duplicate prevention tests
│   ├── test_mart.py              # Exact 1-row-per-order & aggregation tests
│   └── test_quality.py           # Quality check audit recorder tests
├── scripts/
│   ├── init_db.py                # Standalone migration script
│   └── run_full_review.py        # Master one-stop execution script
├── requirements.txt              # Frozen Python dependencies
├── pytest.ini                    # Pytest configuration
├── .env.example                  # Environment template
├── .gitignore                    # Secrets & data exclusion rules
└── README.md                     # Comprehensive documentation
```

---

## 3. Step-by-Step Windows PowerShell Setup

Open **Windows PowerShell** in the project directory (`E:\BDA`):

### Step 3.1: Create and Activate Python Virtual Environment
```powershell
# Create virtual environment (.venv)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```
*(If you encounter execution policy restrictions, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3.2: Install Python Dependencies
```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

---

## 4. Configuring Supabase PostgreSQL

1. Log in to [Supabase](https://supabase.com) and click **New project**.
2. Name your project (e.g., `olist-wbr`) and set a strong database password.
3. Once provisioned, go to **Project Settings** -> **Database**.
4. Under **Connection string**, select **URI**. You can use either:
   - **Direct connection:**
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
     ```
   - **Transaction Pooler (recommended for serverless/IPv4):**
     ```
     postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
5. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
6. Open `.env` in your text editor and insert your connection string:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:YourActualPassword@db.yourref.supabase.co:5432/postgres
   DATA_RAW_DIR=data/raw
   LOG_LEVEL=INFO
   API_HOST=127.0.0.1
   API_PORT=8000
   ```
   *(Note: If your password contains special characters like `@` or `#`, URL-encode them, e.g. `@` becomes `%40`)*.

---

## 5. Placing Dataset Files

All 9 CSV files from the Kaggle Olist dataset must reside in `data/raw/`:
- `olist_orders_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `product_category_name_translation.csv`

Verify that all 9 files exist:
```powershell
Get-ChildItem data/raw/*.csv | Select-Object Name, Length
```

---

## 6. Applying Database Migrations

Run the database migration script to build the Raw, Staging, Mart, and Audit tables:
```powershell
.\.venv\Scripts\python scripts/init_db.py
```
This executes:
1. `sql/schema/01_raw_schema.sql` (raw_* tables)
2. `sql/schema/02_staging_schema.sql` (stg_* tables)
3. `sql/schema/03_mart_schema.sql` (mart_order_performance & pipeline_quality_audit)

---

## 7. Running the Idempotent ELT Pipeline

Execute the automated pipeline:
```powershell
.\.venv\Scripts\python -m backend.pipeline.run
```

### What Happens During Execution:
1. **Connectivity Check:** Validates `.env` and pings the database.
2. **Pre-flight Check:** Validates presence of all 9 CSV files and verifies required column headers.
3. **Raw Ingestion:** Loads records in 10,000-row chunks using temporary tables and `ON CONFLICT` upserts. Rerunning with unchanged files will **never** duplicate records or change business totals.
4. **Staging Transform:** Type casts timestamps to `TIMESTAMPTZ`, cleans strings, trims whitespace, standardizes column names, and deduplicates review rows.
5. **Mart Build:** Pre-aggregates items, payments, and reviews in CTEs, joining to `stg_orders` to produce **exactly one row per order_id** in `mart_order_performance`.
6. **Data Quality Suite:** Executes all 6 quality checks and records outcomes in `pipeline_quality_audit`.
7. **Exit Code:** Returns `0` on success, or non-zero (`1`, `2`, `3`, `4`) on failure.

---

## 8. Executing SQL Data Quality Checks

All 6 checks are located in `sql/quality/`:
- `01_null_duplicate_orders.sql`: Primary key integrity on `stg_orders` (CRITICAL, threshold: 0).
- `02_delivered_before_purchase.sql`: Chronological consistency (CRITICAL, threshold: 0).
- `03_payment_vs_order_value.sql`: Payment vs item + freight variance > R$1.00 (WARNING, threshold: 600).
- `04_orphan_orders.sql`: Foreign key integrity to `stg_customers` (CRITICAL, threshold: 0).
- `05_invalid_review_scores.sql`: Review score domain [1, 5] validity (CRITICAL, threshold: 0).
- `06_delivery_date_anomalies.sql`: Delivered orders missing delivery dates (WARNING, threshold: 50).

To run the checks independently:
```powershell
.\.venv\Scripts\python -c "from backend.quality.runner import run_all_quality_checks; run_all_quality_checks()"
```

---

## 9. Running the Five Analytical Queries

All 5 analytical queries are pure SQL located in `sql/analytics/`. They use CTEs and window functions—no pandas calculations are used:
1. `01_monthly_revenue_growth.sql`: Calendar month aggregation, `LAG()` prior month revenue, absolute change and % growth.
2. `02_top_categories_by_state.sql`: `DENSE_RANK()` partitioned by customer state, top 3 ranks per state, documented tie behavior.
3. `03_rolling_daily_orders.sql`: `GENERATE_SERIES` continuous calendar spine (preserving zero days), 7-calendar-day moving average.
4. `04_repeat_purchase_rate.sql`: Uses `customer_unique_id` (not `customer_id`) to compute customer retention % and order count distribution.
5. `05_delivery_delay_vs_review.sql`: Actual vs estimated delivery delay in days, review rating distribution, on-time vs late cohorts.

To execute all 5 queries and inspect output:
```powershell
.\.venv\Scripts\python -c "from backend.analytics.runner import run_all_analytics; print(run_all_analytics())"
```

---

## 10. Generating Publication Charts & 5-Page PDF

### Generate Charts:
```powershell
.\.venv\Scripts\python reports/generate_charts.py
```
Output charts saved to `reports/charts/`:
- `01_monthly_revenue_trend.png`
- `02_monthly_revenue_growth.png`
- `03_top_categories_by_state.png`
- `04_delivery_delay_vs_review.png`

### Compile the 5-Page PDF Report & VP Memo:
```powershell
.\.venv\Scripts\python reports/generate_pdf.py
```
Output report saved to:
`reports/output/olist_weekly_business_review.pdf`

---

## 11. Launching the Web Application (Backend & Frontend)

### Terminal 1: Start FastAPI Backend
```powershell
.\.venv\Scripts\uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8000
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Terminal 2: Start React Frontend
```powershell
cd frontend
npm run dev
```
Open your browser at: [http://localhost:5173](http://localhost:5173)

---

## 12. Running Automated Tests

Run the full pytest suite:
```powershell
.\.venv\Scripts\pytest -v tests/
```

### Verified Test Cases:
- `test_verify_files_exist_success`: Confirms all 9 dataset files are detected.
- `test_verify_files_exist_missing_file_raises`: Validates `DatasetNotFoundError` on missing files.
- `test_verify_file_columns_success`: Validates required column schema matches.
- `test_verify_file_columns_missing_col_raises`: Validates `DatasetSchemaError` on missing columns.
- `test_run_extraction_checks_success`: Tests high-level pre-flight extraction.
- `test_raw_loading_idempotent`: Validates running ingestion twice does not duplicate records.
- `test_duplicate_prevention_on_conflict`: Confirms financial totals remain constant upon re-runs.
- `test_mart_exact_one_row_per_order`: Verifies exact 1:1 order grain in `mart_order_performance`.
- `test_mart_financial_aggregations`: Validates items, payments, and reviews are aggregated independently without fan-out multiplication.
- `test_mart_late_delivery_flag`: Tests delivery delay calculation and on-time boolean flag.
- `test_quality_audit_recording`: Tests inserting and querying records in `pipeline_quality_audit`.

---

## 13. Version Control & Safe GitHub Push

The repository is configured to protect sensitive credentials and dataset files:
- `.env` is ignored by `.gitignore` (only `.env.example` is committed).
- `data/raw/*.csv` and all `.csv` files are ignored to prevent committing large data files.
- Virtual environments (`.venv/`) and `node_modules/` are excluded.

```powershell
git status
git add backend/ sql/ reports/ frontend/ tests/ scripts/ requirements.txt pytest.ini .env.example .gitignore README.md
git commit -m "feat: complete Olist Weekly Business Review ELT pipeline, analytics, tests, and dashboard"
git push origin main
```

---

## 14. Troubleshooting Guide

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `DATABASE_URL is not configured` | Missing `.env` file | Copy `.env.example` to `.env` and fill in your Supabase connection string. |
| `password authentication failed` | Special characters in password | URL-encode special characters in `DATABASE_URL` (e.g. `@` -> `%40`, `#` -> `%23`). |
| `connection timeout` to Supabase | Local network IPv6 issue | Use Supabase's **Transaction Pooler** connection string (`aws-0-[region].pooler.supabase.com:6543`). |
| `DatasetNotFoundError: Missing required files` | CSV files not in `data/raw/` | Download the dataset from Kaggle and place all 9 CSV files in `data/raw/`. |
| `DatasetSchemaError: Missing required columns` | Incorrect CSV file version | Check header row of the failing CSV against expected columns in `extract.py`. |
| Port 8000 or 5173 already in use | Another process running | Use `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess` to free the port. |

---

## 15. Viva Defense & Interview Cheatsheet

### Q1: Why did you use `customer_unique_id` instead of `customer_id` for repeat purchase rate?
> **Answer:** In Olist, `customer_id` is a transaction-level key generated afresh for every checkout session. If you group by `customer_id`, every order appears to come from a different customer, resulting in a false 0% repeat purchase rate. `customer_unique_id` represents the real individual across multiple orders.

### Q2: How does your pipeline avoid fan-out joins that duplicate order values?
> **Answer:** In naive joins, joining an order with 2 items and 2 payments creates a cartesian product of 4 rows, which multiplies prices and payments. In `build_mart.py`, items, payments, and reviews are pre-aggregated independently in separate Common Table Expressions (CTEs) grouped by `order_id` before joining to `stg_orders`. This guarantees that `mart_order_performance` maintains a strict 1:1 grain per order.

### Q3: How is pipeline idempotency achieved?
> **Answer:** Ingestion uses temporary staging tables and PostgreSQL `ON CONFLICT (primary_key) DO UPDATE` (or `DO NOTHING`). Rerunning the pipeline with unchanged source files does not duplicate records or alter financial totals.

### Q4: Why is delivery delay not considered the sole cause of lower review scores?
> **Answer:** Correlation does not prove causation. While late orders average 2.27 stars vs 4.30 stars for on-time orders, delays frequently coincide with damaged packaging, poor seller communication, or difficult geographic transit. We classify this as a strong statistical association, not a mono-causal mechanism.

### Q5: What is the difference between CRITICAL and WARNING quality checks?
> **Answer:** CRITICAL checks (such as null/duplicate order IDs, delivered before purchase, orphan orders, or invalid scores) enforce hard integrity rules; any failure terminates the pipeline immediately. WARNING checks (such as payment vs order value discrepancies or missing delivery timestamps on delivered orders) flag known real-world anomalies (e.g. vouchers, carrier sync drops) for audit logging without halting operations.
