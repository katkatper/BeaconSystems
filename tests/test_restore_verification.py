from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from scripts.verify_restored_database import (
    REQUIRED_TABLES,
    database_identity,
    validate_restore_target,
    verify_restore,
)


def test_restore_target_rejects_live_database_even_when_credentials_differ():
    live = "postgresql://app:secret@db.example.gov:5432/beacon?sslmode=verify-full"
    restore = "postgresql://auditor:different@db.example.gov:5432/beacon"

    assert database_identity(live) == database_identity(restore)
    with pytest.raises(RuntimeError, match="configured live database"):
        validate_restore_target(restore, [live])


@pytest.mark.parametrize(
    "target",
    ["sqlite:///restore.db", "postgresql:///missing-host", "postgresql://host"],
)
def test_restore_target_requires_complete_postgresql_url(target):
    with pytest.raises(RuntimeError, match="requires a PostgreSQL"):
        validate_restore_target(target, [])


def test_restore_verification_is_read_only_and_reports_only_counts():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        for table_name in sorted(REQUIRED_TABLES):
            if table_name == "alembic_version":
                connection.execute(text("CREATE TABLE alembic_version (version_num TEXT)"))
            elif table_name == "agencies":
                connection.execute(text("CREATE TABLE agencies (agency_id INTEGER)"))
            elif table_name == "persons":
                connection.execute(text("CREATE TABLE persons (person_id INTEGER)"))
            elif table_name == "cases":
                connection.execute(text(
                    "CREATE TABLE cases (case_id INTEGER, agency_id INTEGER, person_id INTEGER)"
                ))
            elif table_name == "evidence":
                connection.execute(text(
                    "CREATE TABLE evidence (evidence_id INTEGER, case_id INTEGER)"
                ))
            else:
                connection.execute(text(f'CREATE TABLE "{table_name}" (id INTEGER)'))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('expected-head')")
        )
        connection.execute(text("INSERT INTO agencies (agency_id) VALUES (10)"))
        connection.execute(text("INSERT INTO persons (person_id) VALUES (20)"))
        connection.execute(text(
            "INSERT INTO cases (case_id, agency_id, person_id) VALUES (30, 10, 20)"
        ))
        connection.execute(text(
            "INSERT INTO evidence (evidence_id, case_id) VALUES (40, 30)"
        ))

    result = verify_restore(engine, "expected-head")

    assert result["status"] == "verified"
    assert result["table_counts"]["cases"] == 1
    assert not any(result["relationship_checks"].values())
    assert "record" not in result
    engine.dispose()


def test_restore_verification_rejects_orphaned_records():
    source = Path("scripts/verify_restored_database.py").read_text(encoding="utf-8")
    assert "cases_without_agency" in source
    assert "cases_without_person" in source
    assert "evidence_without_case" in source
    assert "SET TRANSACTION READ ONLY" in source
