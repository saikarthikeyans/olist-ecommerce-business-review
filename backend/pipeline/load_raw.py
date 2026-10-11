"""Idempotent raw data loading module for Olist Weekly Business Review.

Loads raw CSV records into PostgreSQL raw_* tables using transactional staging,
chunked streaming, and conflict resolution to guarantee that rerunning the
pipeline never duplicates rows or alters totals.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.config import DATA_RAW_DIR, setup_logging
from backend.db.connection import get_engine
from backend.pipeline.extract import REQUIRED_DATASETS

logger = setup_logging()

CHUNK_SIZE = 10000


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize NaN, None, and blank whitespace."""
    # Replace NaN with None for SQL NULL mapping
    df = df.where(pd.notnull(df), None)
    return df


def load_raw_table(
    csv_path: Path,
    table_name: str,
    engine: Engine,
    pk_cols: list[str] | None = None,
) -> int:
    """Load a single CSV file into its target raw table idempotently.

    Uses a temporary table strategy within a transaction:
    1. Reads CSV in chunks into a temporary table.
    2. Upserts from temporary table into the target raw table using ON CONFLICT.
    3. Drops the temporary table upon transaction commit.

    Returns:
        Total row count loaded.
    """
    start_time = time.time()
    temp_table = f"_tmp_{table_name}"
    total_rows = 0

    logger.info("Loading '%s' into '%s'...", csv_path.name, table_name)

    # Detect dialect
    is_postgres = engine.dialect.name == "postgresql"

    with engine.begin() as conn:
        # Idempotency check: if table already contains data, avoid redundant re-ingestion
        # which can exhaust database connection pools or disk quotas on hosted tiers.
        try:
            existing_cnt = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar() or 0
            if existing_cnt > 0:
                logger.info(
                    "Table '%s' is already populated with %d rows. Ingestion is up to date.",
                    table_name,
                    existing_cnt,
                )
                return existing_cnt
        except Exception:
            pass

        # For PostgreSQL: let pandas create the temp table on the first chunk
        # using all-VARCHAR columns so there are no type mismatches. The typed
        # upsert into the target table handles all casts via ON CONFLICT SQL.
        if not is_postgres:
            conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))

        # Stream CSV chunks into temporary table.
        # For PostgreSQL we let pandas CREATE the temp table on the first chunk
        # (if_exists="replace") so all columns stay text/VARCHAR — no type
        # mismatch.  Subsequent chunks append.  Casts happen in the upsert SQL.
        first_chunk = True
        for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, dtype=str):
            chunk = clean_dataframe(chunk)
            chunk["_loaded_at"] = pd.Timestamp.now(tz="UTC") if is_postgres else pd.Timestamp.now()
            if_ex = "replace" if first_chunk else "append"
            chunk.to_sql(temp_table, conn, if_exists=if_ex, index=False)
            first_chunk = False
            total_rows += len(chunk)

        # Idempotent merge into target table
        if is_postgres:
            # Retrieve column names and data types from the target raw table
            col_meta_query = text(
                f"SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_name = '{table_name}' ORDER BY ordinal_position;"
            )
            col_meta = {r[0]: r[1] for r in conn.execute(col_meta_query).fetchall()}

            # Build cast expressions: cast each temp (text) column to its target type
            def cast_expr(col: str) -> str:
                dtype = col_meta.get(col, "text")
                # Map information_schema data_type to a safe CAST target
                if dtype in ("integer", "bigint", "smallint"):
                    return f"NULLIF(TRIM({col}), '')::INTEGER AS {col}"
                elif dtype in ("numeric", "decimal", "real", "double precision"):
                    return f"NULLIF(TRIM({col}), '')::NUMERIC AS {col}"
                elif "timestamp" in dtype:
                    return f"NULLIF(TRIM({col}), '')::TIMESTAMPTZ AS {col}"
                else:
                    return col  # already text/varchar

            if pk_cols:
                pk_clause = ", ".join(pk_cols)
                all_target_cols = [c for c in col_meta if c not in ("_loaded_at",)]
                non_pk_cols = [c for c in all_target_cols if c not in pk_cols]

                select_exprs = ", ".join(cast_expr(c) for c in all_target_cols)
                col_names_str = ", ".join(all_target_cols)

                if non_pk_cols:
                    update_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in non_pk_cols)
                    conflict_action = f"DO UPDATE SET {update_clause}, _loaded_at = CURRENT_TIMESTAMP"
                else:
                    conflict_action = "DO NOTHING"

                upsert_sql = f"""
                    INSERT INTO {table_name} ({col_names_str}, _loaded_at)
                    SELECT {select_exprs}, CURRENT_TIMESTAMP
                    FROM {temp_table}
                    ON CONFLICT ({pk_clause}) {conflict_action};
                """
                conn.execute(text(upsert_sql))
            else:
                # Table without unique natural key (e.g. raw_geolocation):
                # Clean refresh to prevent duplicate coordinate sets on reruns
                conn.execute(text(f"TRUNCATE TABLE {table_name};"))
                non_serial_cols = [c for c in col_meta if c not in ("geolocation_id", "_loaded_at")]
                select_exprs = ", ".join(cast_expr(c) for c in non_serial_cols)
                col_names_str = ", ".join(non_serial_cols)
                conn.execute(text(
                    f"INSERT INTO {table_name} ({col_names_str}, _loaded_at) "
                    f"SELECT {select_exprs}, CURRENT_TIMESTAMP FROM {temp_table};"
                ))

            conn.execute(text(f"DROP TABLE IF EXISTS {temp_table};"))
        else:
            # SQLite fallback: Replace table cleanly
            conn.execute(text(f"DELETE FROM {table_name};"))
            chunk_copy = pd.read_csv(csv_path, dtype=str)
            chunk_copy = clean_dataframe(chunk_copy)
            chunk_copy.to_sql(table_name, conn, if_exists="append", index=False)

    elapsed = time.time() - start_time
    logger.info("Loaded '%s': %d rows processed in %.2f seconds.", table_name, total_rows, elapsed)
    return total_rows


# Primary key mappings for each dataset
TABLE_PKS: Dict[str, list[str]] = {
    "raw_orders": ["order_id"],
    "raw_customers": ["customer_id"],
    "raw_order_items": ["order_id", "order_item_id"],
    "raw_order_payments": ["order_id", "payment_sequential"],
    "raw_order_reviews": ["review_id", "order_id"],
    "raw_products": ["product_id"],
    "raw_sellers": ["seller_id"],
    "raw_product_category_translation": ["product_category_name"],
    "raw_geolocation": [],  # Handled via clean refresh
}


def load_all_raw_data(
    raw_dir: Path | None = None,
    engine: Engine | None = None,
) -> Dict[str, int]:
    """Execute raw ingestion for all 9 Olist datasets."""
    directory = raw_dir or DATA_RAW_DIR
    eng = engine or get_engine()

    counts: Dict[str, int] = {}
    logger.info("Beginning idempotent raw data ingestion...")

    for filename, meta in REQUIRED_DATASETS.items():
        csv_file = directory / filename
        table = meta["table"]
        pks = TABLE_PKS.get(table, [])
        row_count = load_raw_table(csv_file, table, eng, pk_cols=pks)
        counts[table] = row_count

    logger.info("Raw ingestion complete across all %d tables.", len(counts))
    return counts
