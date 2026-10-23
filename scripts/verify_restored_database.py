"""Verify an isolated Beacon database restore without reading record contents."""

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool

REQUIRED_TABLES = {
    "activity_log",
    "agencies",
    "alerts",
    "alembic_version",
    "cases",
    "evidence",
    "evidence_chain",
    "persons",
    "users",
}

ORPHAN_CHECKS = {
    "cases_without_agency": """
        SELECT COUNT(*) FROM cases AS child
        LEFT JOIN agencies AS parent ON parent.agency_id = child.agency_id
        WHERE child.agency_id IS NOT NULL AND parent.agency_id IS NULL
    """,
    "cases_without_person": """
        SELECT COUNT(*) FROM cases AS child
        LEFT JOIN persons AS parent ON parent.person_id = child.person_id
        WHERE child.person_id IS NOT NULL AND parent.person_id IS NULL
    """,
    "evidence_without_case": """
        SELECT COUNT(*) FROM evidence AS child
        LEFT JOIN cases AS parent ON parent.case_id = child.case_id
        WHERE child.case_id IS NOT NULL AND parent.case_id IS NULL
    """,
}


def database_identity(database_url: str) -> tuple[str, str, str, str]:
    parsed = urlsplit(database_url)
    scheme = parsed.scheme.split("+", 1)[0].lower()
    return (
        scheme,
        (parsed.hostname or "").lower(),
        str(parsed.port or 5432),
        parsed.path.lstrip("/"),
    )


def validate_restore_target(database_url: str, protected_urls: list[str]) -> None:
    target = database_identity(database_url)
    if target[0] != "postgresql" or not target[1] or not target[3]:
        raise RuntimeError("Restore verification requires a PostgreSQL database URL")
    if any(database_identity(url) == target for url in protected_urls if url):
        raise RuntimeError(
            "Restore verification refuses to connect to the configured live database"
        )


def expected_alembic_head(repository_root: Path) -> str:
    config = Config(str(repository_root / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    if not head:
        raise RuntimeError("Beacon migration head could not be determined")
    return head


def verify_restore(engine, expected_revision: str) -> dict:
    tables = set(inspect(engine).get_table_names())
    missing_tables = sorted(REQUIRED_TABLES - tables)
    if missing_tables:
        raise RuntimeError("Restored database is missing required Beacon tables")

    with engine.connect() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout = '30s'"))

        revisions = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalars().all()
        if revisions != [expected_revision]:
            raise RuntimeError("Restored database migration revision is not current")

        orphan_counts = {
            name: int(connection.execute(text(statement)).scalar_one())
            for name, statement in ORPHAN_CHECKS.items()
        }
        if any(orphan_counts.values()):
            raise RuntimeError("Restored database failed relationship integrity checks")

        table_counts = {
            table_name: int(
                connection.execute(
                    text(f'SELECT COUNT(*) FROM "{table_name}"')
                ).scalar_one()
            )
            for table_name in sorted(REQUIRED_TABLES - {"alembic_version"})
        }

    return {
        "status": "verified",
        "migration_revision": expected_revision,
        "table_counts": table_counts,
        "relationship_checks": orphan_counts,
    }


def main() -> int:
    database_url = os.getenv("BEACON_RESTORE_DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("BEACON_RESTORE_DATABASE_URL is required")

    validate_restore_target(
        database_url,
        [os.getenv("DATABASE_URL", ""), os.getenv("MIGRATION_DATABASE_URL", "")],
    )
    repository_root = Path(__file__).resolve().parents[1]
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        result = verify_restore(engine, expected_alembic_head(repository_root))
    finally:
        engine.dispose()
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        reason = str(exc) if isinstance(exc, RuntimeError) else "verification failed"
        print(json.dumps({"status": "failed", "reason": reason}), file=sys.stderr)
        sys.exit(1)
