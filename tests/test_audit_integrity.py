from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.activity_log import ActivityLog
from scripts.verify_audit_integrity import load_verification_keys, validate_database_url
from services.audit_integrity import sign_activity_log, verify_activity_log_chain

KEY = "audit-integrity-test-key-with-32-bytes-minimum"
KEY_ID = "test-key-v1"


def build_event(action: str, *, agency_id: int = 10) -> ActivityLog:
    return ActivityLog(
        agency_id=agency_id,
        user_id=7,
        action=action,
        entity="case",
        entity_id=4,
        details="test detail",
        ip_address="192.0.2.10",
        timestamp=datetime(2026, 10, 24, 12, 0, 0),
    )


def test_audit_events_form_independent_tenant_chains():
    engine = create_engine("sqlite://")
    ActivityLog.__table__.create(engine)
    with Session(engine) as db:
        first = build_event("CREATE_CASE")
        sign_activity_log(db, first, key=KEY, key_id=KEY_ID)
        db.add(first)
        db.commit()

        second = build_event("VIEW_CASE")
        sign_activity_log(db, second, key=KEY, key_id=KEY_ID)
        db.add(second)
        other_agency = build_event("CREATE_CASE", agency_id=20)
        sign_activity_log(db, other_agency, key=KEY, key_id=KEY_ID)
        db.add(other_agency)
        db.commit()

        assert second.previous_hash == first.event_hash
        assert other_agency.previous_hash != first.event_hash
        events = db.query(ActivityLog).order_by(ActivityLog.id.asc()).all()
        result = verify_activity_log_chain(events, keys={KEY_ID: KEY})

    assert result == {"valid": True, "verified": 3, "unsigned": 0}
    engine.dispose()


def test_audit_chain_detects_modified_content_and_missing_keys():
    event = build_event("CREATE_CASE")
    engine = create_engine("sqlite://")
    ActivityLog.__table__.create(engine)
    with Session(engine) as db:
        sign_activity_log(db, event, key=KEY, key_id=KEY_ID)
        db.add(event)
        db.commit()
        event.action = "ALTERED_ACTION"
        assert not verify_activity_log_chain([event], keys={KEY_ID: KEY})["valid"]
        event.action = "CREATE_CASE"
        assert not verify_activity_log_chain([event], keys={})["valid"]
    engine.dispose()


def test_pre_migration_unsigned_events_are_counted_not_misrepresented():
    event = build_event("LEGACY_EVENT")
    assert verify_activity_log_chain([event], keys={}) == {
        "valid": True,
        "verified": 0,
        "unsigned": 1,
    }


def test_offline_verifier_accepts_versioned_keys_without_exposing_values():
    keys = load_verification_keys(
        '{"audit-v1":"first-audit-key-with-at-least-32-characters",'
        '"audit-v2":"second-audit-key-with-at-least-32-characters"}'
    )
    assert set(keys) == {"audit-v1", "audit-v2"}
    validate_database_url("postgresql://auditor@audit-db.example.gov/beacon")


def test_offline_verifier_rejects_invalid_key_map_and_database_url():
    import pytest

    with pytest.raises(RuntimeError, match="map key IDs"):
        load_verification_keys("{}")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        validate_database_url("sqlite:///beacon.db")
