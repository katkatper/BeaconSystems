"""Verify visible Beacon audit hash chains without emitting sensitive records."""

import json
import os
import sys
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from models.activity_log import ActivityLog
from services.audit_integrity import verify_activity_log_chain


def load_verification_keys(raw_keys: str) -> dict[str, str]:
    try:
        keys = json.loads(raw_keys)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AUDIT_INTEGRITY_KEYS_JSON must be valid JSON") from exc
    if not isinstance(keys, dict) or not keys:
        raise RuntimeError("AUDIT_INTEGRITY_KEYS_JSON must map key IDs to keys")
    if not all(
        isinstance(key_id, str)
        and key_id
        and isinstance(key, str)
        and len(key) >= 32
        for key_id, key in keys.items()
    ):
        raise RuntimeError("Audit verification keys are invalid")
    return keys


def validate_database_url(database_url: str) -> None:
    parsed = urlsplit(database_url)
    if (
        parsed.scheme.split("+", 1)[0].lower() != "postgresql"
        or not parsed.hostname
        or not parsed.path.lstrip("/")
    ):
        raise RuntimeError("Audit verification requires a PostgreSQL database URL")


def verify_database(engine, keys: dict[str, str]) -> dict:
    with engine.connect() as connection:
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        connection.exec_driver_sql("SET LOCAL statement_timeout = '60s'")
        events = (
            connection.execution_options(stream_results=True)
            .execute(
                ActivityLog.__table__.select().order_by(
                    ActivityLog.agency_id.asc().nullsfirst(),
                    ActivityLog.id.asc(),
                )
            )
            .mappings()
        )
        modeled_events = (ActivityLog(**dict(row)) for row in events)
        result = verify_activity_log_chain(modeled_events, keys=keys)
    return {"status": "verified" if result["valid"] else "failed", **result}


def main() -> int:
    database_url = os.getenv("BEACON_AUDIT_DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("BEACON_AUDIT_DATABASE_URL is required")
    validate_database_url(database_url)
    keys = load_verification_keys(os.getenv("AUDIT_INTEGRITY_KEYS_JSON", ""))
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        result = verify_database(engine, keys)
    finally:
        engine.dispose()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        reason = str(exc) if isinstance(exc, RuntimeError) else "verification failed"
        print(json.dumps({"status": "failed", "reason": reason}), file=sys.stderr)
        sys.exit(1)
