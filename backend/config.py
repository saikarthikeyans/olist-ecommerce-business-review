"""Configuration module for Olist Weekly Business Review.

Reads environment variables from .env and establishes core system settings.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env if present
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


def get_normalized_db_url(raw_url: str | None) -> str:
    """Normalize PostgreSQL connection string for SQLAlchemy 2.0.

    Ensures postgres:// is rewritten to postgresql+psycopg:// or postgresql://
    so that modern psycopg drivers bind properly.
    """
    if not raw_url:
        # Default placeholder / local fallback
        return ""

    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not (
        url.startswith("postgresql+psycopg://") or url.startswith("postgresql+psycopg2://")
    ):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


# Database Configuration
DATABASE_URL: str = get_normalized_db_url(os.getenv("DATABASE_URL"))
USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "false").lower() in ("true", "1", "yes")

# If no DATABASE_URL is set and SQLITE_FALLBACK is requested, use local SQLite file
if not DATABASE_URL and USE_SQLITE_FALLBACK:
    SQLITE_PATH = PROJECT_ROOT / "olist_local.db"
    DATABASE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"

# Directory Paths
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", str(PROJECT_ROOT / "data" / "raw")))
REPORTS_DIR = PROJECT_ROOT / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"
OUTPUT_DIR = REPORTS_DIR / "output"
SQL_DIR = PROJECT_ROOT / "sql"
SCHEMA_SQL_DIR = SQL_DIR / "schema"
QUALITY_SQL_DIR = SQL_DIR / "quality"
ANALYTICS_SQL_DIR = SQL_DIR / "analytics"

# API & Server Configuration
API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS: List[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# Logging Configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure standardized logging with timestamps and severity levels."""
    log_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger = logging.getLogger("olist_pipeline")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
