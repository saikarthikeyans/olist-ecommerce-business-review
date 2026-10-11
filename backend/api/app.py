"""FastAPI backend application for Olist Weekly Business Review dashboard.

Provides REST endpoints for executive KPIs, analytical queries, data quality audit
history, and system health status.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.analytics.runner import (
    run_all_analytics,
    run_delivery_delay_vs_review,
    run_monthly_revenue_growth,
    run_repeat_purchase_rate,
    run_rolling_daily_orders,
    run_top_categories_by_state,
)
from backend.config import CORS_ORIGINS, DATA_RAW_DIR, DATABASE_URL, setup_logging
from backend.db.connection import check_db_connectivity, get_engine
from backend.pipeline.extract import REQUIRED_DATASETS
from backend.quality.runner import get_latest_quality_audit

logger = setup_logging()

app = FastAPI(
    title="Olist Weekly Business Review API",
    description="Backend API powering the Olist E-commerce Marketplace analytics dashboard.",
    version="1.0.0",
)

# Enable CORS for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """System health check and database connectivity verification."""
    is_connected = False
    db_message = "Database URL not configured."
    if DATABASE_URL:
        try:
            is_connected, db_message = check_db_connectivity()
        except Exception as e:
            db_message = str(e)

    # Check raw CSV files availability
    files_available = 0
    if DATA_RAW_DIR.exists():
        files_available = sum(1 for f in REQUIRED_DATASETS if (DATA_RAW_DIR / f).exists())

    return {
        "status": "healthy",
        "database_connected": is_connected,
        "database_message": db_message,
        "dataset_files_present": f"{files_available}/{len(REQUIRED_DATASETS)}",
        "is_ready_for_analytics": is_connected,
    }


@app.get("/api/kpis")
def get_executive_kpis() -> Dict[str, Any]:
    """Retrieve executive overview North Star and supporting KPIs."""
    if not DATABASE_URL:
        return {
            "is_configured": False,
            "message": "Database not configured. Provide DATABASE_URL in .env to load metrics.",
        }

    try:
        engine = get_engine()
        is_connected, _ = check_db_connectivity(engine)
        if not is_connected:
            return {
                "is_configured": False,
                "message": "Database unreachable. Verify Supabase connection string.",
            }

        kpi_sql = """
            SELECT 
                COUNT(*) AS total_mart_orders,
                COUNT(DISTINCT customer_unique_id) AS total_customers,
                ROUND(SUM(total_order_value), 2) AS total_gross_gmv,
                ROUND(AVG(total_order_value), 2) AS avg_order_value,
                
                -- North Star: On-time delivery rate for delivered orders
                COUNT(CASE WHEN order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL THEN 1 END) AS delivered_orders_count,
                COUNT(CASE WHEN order_status = 'delivered' AND is_on_time = TRUE THEN 1 END) AS on_time_orders_count,
                ROUND(
                    (COUNT(CASE WHEN order_status = 'delivered' AND is_on_time = TRUE THEN 1 END) * 100.0) / 
                    NULLIF(COUNT(CASE WHEN order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL THEN 1 END), 0),
                    2
                ) AS on_time_delivery_rate_pct,
                
                -- Customer Satisfaction
                ROUND(AVG(review_score), 2) AS avg_review_score,
                
                -- Repeat Customer Rate
                ROUND(
                    (COUNT(DISTINCT CASE WHEN is_repeat_customer = TRUE THEN customer_unique_id END) * 100.0) / 
                    NULLIF(COUNT(DISTINCT customer_unique_id), 0),
                    2
                ) AS repeat_customer_rate_pct
            FROM mart_order_performance;
        """
        with engine.connect() as conn:
            result = conn.execute(text(kpi_sql)).fetchone()
            columns = [
                "total_mart_orders", "total_customers", "total_gross_gmv", "avg_order_value",
                "delivered_orders_count", "on_time_orders_count", "on_time_delivery_rate_pct",
                "avg_review_score", "repeat_customer_rate_pct"
            ]
            row_dict = dict(zip(columns, result)) if result else {}

        return {
            "is_configured": True,
            "data": row_dict,
        }
    except Exception as e:
        logger.warning("Error fetching KPIs: %s", str(e))
        return {
            "is_configured": False,
            "error": str(e),
            "message": "Mart tables not populated yet. Run pipeline with `python -m backend.pipeline.run`.",
        }


@app.get("/api/analytics/monthly-revenue")
def get_monthly_revenue() -> Dict[str, Any]:
    """API endpoint for Query 1: Month-over-month revenue and growth."""
    try:
        data = run_monthly_revenue_growth()
        return {"is_configured": True, "data": data}
    except Exception as e:
        return {"is_configured": False, "error": str(e), "data": []}


@app.get("/api/analytics/top-categories")
def get_top_categories() -> Dict[str, Any]:
    """API endpoint for Query 2: Top 3 product categories by state."""
    try:
        data = run_top_categories_by_state()
        return {"is_configured": True, "data": data}
    except Exception as e:
        return {"is_configured": False, "error": str(e), "data": []}


@app.get("/api/analytics/rolling-orders")
def get_rolling_orders() -> Dict[str, Any]:
    """API endpoint for Query 3: 7-day rolling average daily orders."""
    try:
        data = run_rolling_daily_orders()
        return {"is_configured": True, "data": data}
    except Exception as e:
        return {"is_configured": False, "error": str(e), "data": []}


@app.get("/api/analytics/repeat-purchases")
def get_repeat_purchases() -> Dict[str, Any]:
    """API endpoint for Query 4: Repeat-purchase rate."""
    try:
        data = run_repeat_purchase_rate()
        return {"is_configured": True, "data": data}
    except Exception as e:
        return {"is_configured": False, "error": str(e), "data": {}}


@app.get("/api/analytics/delivery-satisfaction")
def get_delivery_satisfaction() -> Dict[str, Any]:
    """API endpoint for Query 5: Delivery delay versus review scores."""
    try:
        data = run_delivery_delay_vs_review()
        return {"is_configured": True, "data": data}
    except Exception as e:
        return {"is_configured": False, "error": str(e), "data": []}


@app.get("/api/quality/results")
def get_quality_audit_results() -> Dict[str, Any]:
    """API endpoint for latest data quality check audits."""
    try:
        data = get_latest_quality_audit()
        return {"is_configured": True, "data": data}
    except Exception as e:
        return {"is_configured": False, "error": str(e), "data": []}


# --------------------------------------------------------------------------
# Staging & Mart Data Exploration & Charting Endpoints
# --------------------------------------------------------------------------

ALLOWED_TABLES = [
    "stg_customers",
    "stg_orders",
    "stg_order_items",
    "stg_order_payments",
    "stg_order_reviews",
    "stg_products",
    "stg_sellers",
    "mart_order_performance",
]


@app.get("/api/tables")
def get_tables() -> Dict[str, Any]:
    """List available staging and mart tables."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                res = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND (table_name LIKE 'stg_%' OR table_name LIKE 'mart_%') "
                    "ORDER BY table_name;"
                )).fetchall()
                tables = [r[0] for r in res]
            else:
                res = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'stg_%' OR name LIKE 'mart_%') "
                    "ORDER BY name;"
                )).fetchall()
                tables = [r[0] for r in res]
        if not tables:
            tables = ALLOWED_TABLES
        return {"tables": tables}
    except Exception as e:
        logger.warning("Error fetching tables: %s", str(e))
        return {"tables": ALLOWED_TABLES}


@app.get("/api/preview/{table_name}")
def get_table_preview(table_name: str, limit: int = 20) -> Dict[str, Any]:
    """Return the first 20 rows and column names for the selected table."""
    clean_name = table_name.strip()
    if clean_name not in ALLOWED_TABLES and not (clean_name.startswith("stg_") or clean_name.startswith("raw_") or clean_name.startswith("mart_")):
        raise HTTPException(status_code=400, detail="Invalid table name requested.")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {clean_name} LIMIT :limit"), {"limit": limit})
            columns = list(result.keys())
            rows = [dict(zip(columns, [str(v) if v is not None else "" for v in row])) for row in result.fetchall()]
        return {"table": clean_name, "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        logger.error("Error previewing table %s: %s", clean_name, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/numeric-columns/{table_name}")
def get_numeric_columns(table_name: str) -> Dict[str, Any]:
    """Return list of numeric columns for the specified table."""
    clean_name = table_name.strip()
    if clean_name not in ALLOWED_TABLES and not (clean_name.startswith("stg_") or clean_name.startswith("raw_") or clean_name.startswith("mart_")):
        raise HTTPException(status_code=400, detail="Invalid table name.")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :t 
                      AND data_type IN ('integer', 'smallint', 'bigint', 'numeric', 'real', 'double precision', 'decimal')
                    ORDER BY ordinal_position;
                """)
                res = conn.execute(query, {"t": clean_name}).fetchall()
                numeric_cols = [r[0] for r in res]
            else:
                res = conn.execute(text(f"PRAGMA table_info({clean_name})")).fetchall()
                numeric_cols = [r[1] for r in res if any(t in str(r[2]).upper() for t in ('INT', 'NUM', 'REAL', 'FLOA', 'DOUB'))]
        return {"table": clean_name, "numeric_columns": numeric_cols}
    except Exception as e:
        logger.error("Error fetching numeric columns: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chart/{table_name}/{column_name}")
def get_chart_data(table_name: str, column_name: str) -> Dict[str, Any]:
    """Return aggregated distribution and stats for a numeric column."""
    clean_table = table_name.strip()
    clean_col = column_name.strip()
    if clean_table not in ALLOWED_TABLES and not (clean_table.startswith("stg_") or clean_table.startswith("raw_") or clean_table.startswith("mart_")):
        raise HTTPException(status_code=400, detail="Invalid table name.")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            stats_sql = f"""
                SELECT 
                    COUNT({clean_col}) AS total_count,
                    MIN({clean_col}) AS min_val,
                    MAX({clean_col}) AS max_val,
                    AVG({clean_col}) AS avg_val
                FROM {clean_table}
                WHERE {clean_col} IS NOT NULL;
            """
            stats = conn.execute(text(stats_sql)).fetchone()
            if not stats or stats[0] == 0:
                return {"table": clean_table, "column": clean_col, "stats": {}, "histogram": [], "top_values": []}

            total_count = stats[0]
            min_val = float(stats[1] or 0)
            max_val = float(stats[2] or 0)
            avg_val = float(stats[3] or 0)

            # Top 10 frequent values
            top_sql = f"""
                SELECT CAST({clean_col} AS TEXT) AS val, COUNT(*) AS count
                FROM {clean_table}
                WHERE {clean_col} IS NOT NULL
                GROUP BY {clean_col}
                ORDER BY count DESC
                LIMIT 10;
            """
            top_res = conn.execute(text(top_sql)).fetchall()
            top_values = [{"label": str(r[0]), "count": int(r[1])} for r in top_res]

            # 10-bin histogram distribution
            histogram = []
            if max_val > min_val:
                step = (max_val - min_val) / 10.0
                bin_sql = f"""
                    SELECT 
                        FLOOR(({clean_col} - :min_val) / :step) AS bin_idx,
                        COUNT(*) AS bin_count
                    FROM {clean_table}
                    WHERE {clean_col} IS NOT NULL AND {clean_col} <= :max_val
                    GROUP BY 1
                    ORDER BY 1;
                """
                bin_res = conn.execute(text(bin_sql), {"min_val": min_val, "step": step, "max_val": max_val}).fetchall()
                bin_map = {int(r[0]): int(r[1]) for r in bin_res if r[0] is not None}

                for i in range(10):
                    b_start = round(min_val + i * step, 2)
                    b_end = round(min_val + (i + 1) * step, 2)
                    histogram.append({
                        "bin": f"{b_start} - {b_end}",
                        "count": bin_map.get(i, 0),
                        "range_start": b_start,
                        "range_end": b_end
                    })

            return {
                "table": clean_table,
                "column": clean_col,
                "stats": {
                    "count": total_count,
                    "min": min_val,
                    "max": max_val,
                    "avg": round(avg_val, 2),
                },
                "histogram": histogram,
                "top_values": top_values,
            }
    except Exception as e:
        logger.error("Error generating chart for %s.%s: %s", clean_table, clean_col, str(e))
        raise HTTPException(status_code=500, detail=str(e))

