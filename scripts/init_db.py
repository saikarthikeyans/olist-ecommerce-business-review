"""Initialize database schemas and apply migrations."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db.connection import check_db_connectivity, get_engine
from backend.db.migrations import run_migrations


def main():
    print("=" * 70)
    print("INITIALIZING OLIST DATABASE SCHEMAS (SUPABASE POSTGRESQL)")
    print("=" * 70)

    try:
        engine = get_engine()
        ok, msg = check_db_connectivity(engine)
        if not ok:
            print(f"[ERROR] Database connection failed: {msg}")
            print("Please verify DATABASE_URL in your .env file.")
            sys.exit(1)

        print(f"[OK] Database connection verified: {msg}")
        run_migrations(engine)
        print("[SUCCESS] All migrations (raw, staging, mart, audit) applied successfully.")
    except Exception as e:
        print(f"[FATAL] Migration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
