"""Database connectivity and execution manager for Supabase PostgreSQL.

Provides resilient SQLAlchemy engine management, SSL handling, connection checks,
and SQL statement execution helpers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection

from backend.config import DATABASE_URL, setup_logging

logger = setup_logging()

_ENGINE_CACHE: Optional[Engine] = None


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Create or retrieve a cached SQLAlchemy Engine.

    Configures connection pooling and timeouts suitable for Supabase PostgreSQL.
    """
    global _ENGINE_CACHE
    target_url = db_url or DATABASE_URL

    if not target_url:
        raise ValueError(
            "DATABASE_URL is not configured. Please define DATABASE_URL in your .env file "
            "(e.g. postgresql+psycopg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres)"
        )

    if _ENGINE_CACHE is not None and db_url is None:
        return _ENGINE_CACHE

    engine_kwargs: Dict[str, Any] = {
        "future": True,
        "pool_pre_ping": True,
    }

    # If targeting PostgreSQL / Supabase, configure pooling and connect_args
    if target_url.startswith("postgresql"):
        engine_kwargs.update(
            {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 1800,  # Recycle connections after 30 min
                "connect_args": {
                    "connect_timeout": 3,
                },
            }
        )
    elif target_url.startswith("sqlite"):
        engine_kwargs.update(
            {
                "connect_args": {"check_same_thread": False},
            }
        )

    engine = create_engine(target_url, **engine_kwargs)

    if db_url is None:
        _ENGINE_CACHE = engine

    return engine


def check_db_connectivity(engine: Optional[Engine] = None) -> Tuple[bool, str]:
    """Verify active database connectivity.

    Returns:
        (is_connected, message_or_version)
    """
    try:
        eng = engine or get_engine()
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1;"))
            val = result.scalar()
            if val == 1:
                # Retrieve database version if accessible
                try:
                    ver = conn.execute(text("SELECT version();")).scalar()
                    return True, f"Connected: {ver}"
                except Exception:
                    return True, "Connected successfully (SELECT 1 passed)."
            return False, "Unexpected response from database ping."
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", str(exc))
        return False, str(exc)


def execute_sql_file(file_path: str, engine: Optional[Engine] = None) -> None:
    """Execute all statements in an external SQL file inside a transaction."""
    eng = engine or get_engine()
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Filter out empty statements
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with eng.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    logger.info("Executed SQL file: %s (%d statements)", file_path, len(statements))


def execute_query_df(query: str, params: Optional[Dict[str, Any]] = None, engine: Optional[Engine] = None) -> pd.DataFrame:
    """Execute a SQL query and return results as a Pandas DataFrame."""
    eng = engine or get_engine()
    with eng.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params=params or {})
    return df


def execute_query_dicts(query: str, params: Optional[Dict[str, Any]] = None, engine: Optional[Engine] = None) -> List[Dict[str, Any]]:
    """Execute a SQL query and return rows as a list of dictionaries."""
    eng = engine or get_engine()
    with eng.connect() as conn:
        result = conn.execute(text(query), params=params or {})
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return rows
