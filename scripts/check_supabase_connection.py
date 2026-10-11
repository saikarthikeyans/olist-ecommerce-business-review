"""Safe inspection script for testing Supabase connection and existing tables.

Adheres strictly to:
  - No secret printing (passwords and sensitive keys are masked)
  - Read-only operations only (no DROP, TRUNCATE, or INSERT)
  - Full schema inspection of all tables and columns in user schemas
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from sqlalchemy import text
from backend.config import get_normalized_db_url
from backend.db.connection import get_engine
from backend.pipeline.extract import REQUIRED_DATASETS

load_dotenv(PROJECT_ROOT / ".env")


def mask_url(url: str | None) -> str:
    if not url:
        return "[NOT SET]"
    try:
        parsed = urlparse(url)
        netloc = ""
        if parsed.username:
            netloc += parsed.username
        if parsed.password:
            netloc += ":****"
        if parsed.hostname:
            if netloc:
                netloc += "@"
            netloc += parsed.hostname
        if parsed.port:
            netloc += f":{parsed.port}"
        return f"{parsed.scheme}://{netloc}{parsed.path}"
    except Exception:
        return "[UNPARSEABLE URL (MASKED)]"


def mask_key(val: str | None) -> str:
    if not val:
        return "[NOT SET]"
    if len(val) <= 8:
        return "****"
    return f"{val[:4]}...{val[-4:]} (Length: {len(val)})"


def main():
    print("=" * 80)
    print("SUPABASE CONNECTION & OLIST TABLES INSPECTION (READ-ONLY)")
    print("=" * 80)

    # 1. Inspect environment variables safely
    raw_db_url = os.getenv("DATABASE_URL")
    supabase_url = os.getenv("SUPABASE_URL")
    pub_key = os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")

    print("\n--- 1. Environment Variables Check ---")
    print(f"DATABASE_URL:             {mask_url(raw_db_url)}")
    print(f"SUPABASE_URL:             {mask_url(supabase_url)}")
    print(f"SUPABASE_PUBLISHABLE_KEY: {mask_key(pub_key)}")

    if not raw_db_url:
        print("\n[ERROR] DATABASE_URL is not set in .env!")
        sys.exit(1)

    normalized_url = get_normalized_db_url(raw_db_url)
    print(f"Normalized Engine Dialect: {urlparse(normalized_url).scheme}")

    # 2. Test PostgreSQL connection
    print("\n--- 2. Testing PostgreSQL Connection ---")
    try:
        engine = get_engine(normalized_url)
        with engine.connect() as conn:
            ping_res = conn.execute(text("SELECT 1;")).scalar()
            ver_res = conn.execute(text("SELECT version();")).scalar()
            current_db = conn.execute(text("SELECT current_database();")).scalar()
            current_user = conn.execute(text("SELECT current_user;")).scalar()

        print("[SUCCESS] Connected to Supabase PostgreSQL!")
        print(f"Current Database: {current_db}")
        print(f"Connected User:   {current_user}")
        print(f"PostgreSQL Ver:   {ver_res.split(',')[0] if ver_res else 'Unknown'}")
    except Exception as e:
        print(f"\n[CONNECTION FAILED] Exact Error:")
        print(f"{type(e).__name__}: {str(e)}")
        print("\nTroubleshooting Tips:")
        print("  - If 'password authentication failed': verify your Supabase database password in .env.")
        print("  - If your password contains special characters (e.g. '@', ':', '#'), ensure they are URL-encoded.")
        print("  - If 'timeout' or 'cannot assign requested address': check whether you are using the direct port 5432 or pooler port 6543.")
        print("    Supabase transaction pooler URI format:")
        print("    postgresql+psycopg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        sys.exit(1)

    # 3. Discover all tables in database
    print("\n--- 3. Discovering Database Tables ---")
    with engine.connect() as conn:
        tables_query = text("""
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'vault', 'graphql', 'realtime', 'auth', 'storage')
            ORDER BY table_schema, table_name;
        """)
        db_tables = conn.execute(tables_query).fetchall()

    if not db_tables:
        print("[WARNING] No user tables found outside system schemas.")
    else:
        print(f"Found {len(db_tables)} table(s) in database:")
        for schema, name, ttype in db_tables:
            print(f"  • {schema}.{name} ({ttype})")

    # 4. Inspect columns and row counts for all detected user tables
    print("\n--- 4. Detailed Table & Row Count Inspection ---")
    found_table_names = set()
    table_details = {}

    with engine.connect() as conn:
        for schema, name, ttype in db_tables:
            if ttype != "BASE TABLE":
                continue
            found_table_names.add(name)
            qualified_name = f'"{schema}"."{name}"'

            # Row count
            try:
                cnt = conn.execute(text(f"SELECT COUNT(*) FROM {qualified_name};")).scalar()
            except Exception as e:
                cnt = f"[Count Error: {e}]"

            # Columns
            cols_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :tname
                ORDER BY ordinal_position;
            """)
            col_rows = conn.execute(cols_query, {"schema": schema, "tname": name}).fetchall()
            col_names = [r[0] for r in col_rows]

            table_details[name] = {
                "schema": schema,
                "count": cnt,
                "columns": col_names,
                "column_details": col_rows,
            }

            print(f"\nTable: {schema}.{name}")
            print(f"  Row Count: {cnt:,}" if isinstance(cnt, int) else f"  Row Count: {cnt}")
            print(f"  Columns ({len(col_names)}): {', '.join(col_names)}")

    # 5. Compare with Expected Olist Datasets / Pipeline expectations
    print("\n" + "=" * 80)
    print("--- 5. Comparison with Pipeline Expectations ---")
    print("=" * 80)

    # Expected mappings
    expected_datasets = REQUIRED_DATASETS

    # Match each expected dataset to existing tables
    for csv_name, meta in expected_datasets.items():
        table_target = meta["table"]  # e.g. raw_orders
        base_name = csv_name.replace(".csv", "")  # e.g. olist_orders_dataset
        short_name = base_name.replace("_dataset", "")  # e.g. olist_orders

        # Check possible matches
        matched_name = None
        for candidate in [table_target, base_name, short_name, base_name.replace("olist_", ""), short_name.replace("olist_", "")]:
            if candidate in found_table_names:
                matched_name = candidate
                break

        print(f"\nExpected Dataset: {csv_name}")
        print(f"  Target Pipeline Table: {table_target}")
        if matched_name:
            details = table_details[matched_name]
            actual_cols = set(details["columns"])
            required_cols = set(meta["required_columns"])
            missing = required_cols - actual_cols
            extra = actual_cols - required_cols

            print(f"  [MATCHED] Found Table in DB: '{details['schema']}.{matched_name}'")
            print(f"  Row Count: {details['count']:,}" if isinstance(details['count'], int) else f"  Row Count: {details['count']}")

            if not missing:
                print(f"  Columns Status: ALL {len(required_cols)} REQUIRED COLUMNS PRESENT [OK]")
            else:
                print(f"  Columns Status: MISSING {len(missing)} COLUMNS: {missing}")

            if extra:
                print(f"  Additional Columns in Table: {extra}")
        else:
            print(f"  [MISSING] No matching table found in DB for {csv_name}")

    print("\n" + "=" * 80)
    print("Inspection complete. No data was modified.")
    print("=" * 80)


if __name__ == "__main__":
    main()
