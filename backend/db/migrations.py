"""Database migrations manager for Olist Weekly Business Review."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.engine import Engine

from backend.config import SCHEMA_SQL_DIR, setup_logging
from backend.db.connection import execute_sql_file, get_engine

logger = setup_logging()

MIGRATION_FILES = [
    "01_raw_schema.sql",
    "02_staging_schema.sql",
    "03_mart_schema.sql",
]


def run_migrations(engine: Optional[Engine] = None, schema_dir: Optional[Path] = None) -> None:
    """Execute raw, staging, and mart schema migrations in sequential order."""
    target_engine = engine or get_engine()
    target_dir = schema_dir or SCHEMA_SQL_DIR

    logger.info("Starting schema migrations from: %s", target_dir)

    for file_name in MIGRATION_FILES:
        file_path = target_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Migration file not found: {file_path}")

        logger.info("Applying migration: %s", file_name)
        execute_sql_file(str(file_path), engine=target_engine)

    logger.info("All schema migrations completed successfully.")


if __name__ == "__main__":
    run_migrations()
