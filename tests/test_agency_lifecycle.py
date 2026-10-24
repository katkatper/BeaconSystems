from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.agencies import Agencies
from models.auth_session import AuthSession
from models.user import User
from services.agency_lifecycle import agency_is_active, set_agency_status


def test_suspending_agency_disables_users_and_revokes_sessions():
    engine = create_engine("sqlite://")
    for model in (Agencies, User, AuthSession):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add_all([
            Agencies(agency_id=10, agency_name="Actor", lifecycle_status="active"),
            Agencies(agency_id=20, agency_name="Target", lifecycle_status="active"),
            User(user_id=2, username="target", email="target@example.gov",
                 password_hash="hash", agency_id=20, is_active=True, auth_version=0),
        ])
        db.commit()
        db.add(AuthSession(
            session_id="00000000-0000-0000-0000-000000000002",
            user_id=2,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            last_seen_at=datetime.utcnow(),
        ))
        db.commit()
        agency = db.get(Agencies, 20)
        actor = SimpleNamespace(agency_id=10)
        affected = set_agency_status(db, actor, agency, "suspended", "Approved security hold")
        db.commit()

        assert affected == 1
        assert agency.lifecycle_status == "suspended"
        assert not db.get(User, 2).is_active
        assert db.get(User, 2).auth_version == 1
        assert db.get(AuthSession, "00000000-0000-0000-0000-000000000002").revoked_at
        assert not agency_is_active(db, 20)
    engine.dispose()


def test_offboarding_is_terminal_and_actor_cannot_suspend_own_agency():
    agency = SimpleNamespace(agency_id=10, lifecycle_status="active")
    actor = SimpleNamespace(agency_id=10)
    with pytest.raises(HTTPException, match="Cannot suspend"):
        set_agency_status(SimpleNamespace(), actor, agency, "suspended", "Valid reason here")

    agency.agency_id = 20
    agency.lifecycle_status = "offboarded"
    with pytest.raises(HTTPException, match="cannot be reactivated"):
        set_agency_status(SimpleNamespace(), actor, agency, "active", "Approved reactivation")
