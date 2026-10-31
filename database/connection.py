import json
import logging
import os
import time
from urllib.parse import quote_plus, urlencode

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import (
    DATABASE_MAX_OVERFLOW,
    DATABASE_POOL_RECYCLE_SECONDS,
    DATABASE_POOL_SIZE,
    DATABASE_SLOW_QUERY_MS,
)
from services.database_metrics import database_metrics

load_dotenv()


def build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT", "5432")
    db_sslmode = os.getenv("DB_SSLMODE", "").strip()
    db_sslrootcert = os.getenv("DB_SSLROOTCERT", "").strip()

    if db_user and db_password and db_host and db_name:
        database_url = (
            f"postgresql+psycopg2://{db_user}:{quote_plus(db_password)}"
            f"@{db_host}:{db_port}/{db_name}"
        )
        tls_options = {
            key: value
            for key, value in {
                "sslmode": db_sslmode,
                "sslrootcert": db_sslrootcert,
            }.items()
            if value
        }
        if tls_options:
            database_url = f"{database_url}?{urlencode(tls_options)}"
        return database_url

    raise RuntimeError(
        "Set DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_NAME before starting Beacon."
    )


DATABASE_URL = build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=DATABASE_POOL_RECYCLE_SECONDS,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
)

query_logger = logging.getLogger("beacon.database")
query_logger.setLevel(logging.INFO)


@event.listens_for(engine, "before_cursor_execute")
def record_query_start(connection, cursor, statement, parameters, context, executemany):
    connection.info.setdefault("query_started_at", []).append(time.perf_counter())


@event.listens_for(engine, "after_cursor_execute")
def record_query_duration(connection, cursor, statement, parameters, context, executemany):
    started = connection.info.get("query_started_at", []).pop()
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    operation = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else "UNKNOWN"
    database_metrics.record(
        operation=operation,
        duration_seconds=duration_ms / 1000,
        slow=duration_ms >= DATABASE_SLOW_QUERY_MS,
    )
    if duration_ms >= DATABASE_SLOW_QUERY_MS:
        query_logger.warning(json.dumps({
            "event": "slow_database_query",
            "duration_ms": duration_ms,
            "operation": database_metrics.normalize_operation(operation),
        }))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Register transaction hooks that restore tenant settings after a commit.
from database import tenant_context  # noqa: E402, F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
