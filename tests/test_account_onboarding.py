import pytest
from fastapi import HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.requests import Request

from models.agencies import Agencies
from models.onboarding import AccountAccessRequest, AccountInvitation
from models.user import User
from routes import onboarding_routes as routes


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite://")
    for model in (Agencies, User, AccountInvitation, AccountAccessRequest):
        model.__table__.create(engine)
    monkeypatch.setattr(routes, "enforce_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(routes, "hash_password", lambda _: "test-hash")
    monkeypatch.setattr(routes, "send_invitation_email", lambda *_: "not_configured")
    with Session(engine) as session:
        session.add_all([Agencies(agency_id=1), Agencies(agency_id=2)])
        session.add(User(
            user_id=1, email="admin@example.com", username="agency-admin",
            password_hash="test-hash", agency_id=1, role="agency_admin",
        ))
        session.commit()
        yield session
    engine.dispose()


def test_invite_is_single_use_and_bound_to_issuer_agency(db):
    code = routes.create_invitation(
        routes.InviteSubmission(email="staff@example.com", role="viewer", agency_id=2),
        Response(), db, db.get(User, 1),
    )["invitation_code"]
    assert db.get(AccountInvitation, code) is None
    registration = routes.AccountRegistration(
        invitation_code=code, username="new-staff", password="sample-password",
    )
    request = Request({"type": "http"})
    routes.redeem_invitation(registration, request, db)
    user = db.query(User).filter_by(username="new-staff").one()
    assert (user.agency_id, user.role, user.email) == (1, "viewer", "staff@example.com")
    with pytest.raises(HTTPException, match="already used"):
        routes.redeem_invitation(registration, request, db)


def test_access_request_only_creates_account_after_invite_redemption(db, monkeypatch):
    delivered = []

    def deliver(recipient, code):
        delivered.append((recipient, code))
        return "sent"

    monkeypatch.setattr(routes, "send_invitation_email", deliver)
    request = Request({"type": "http"})
    submission = routes.AccessSubmission(email="applicant@example.com", agency_name="Agency Two")
    routes.request_access(submission, request, db)
    routes.request_access(submission, request, db)
    entry = db.query(AccountAccessRequest).one()
    assert db.query(User).count() == 1
    assert delivered == []
    reviewer = db.get(User, 1)
    reviewer.role = "platform_admin"
    db.commit()
    result = routes.review_access(
        entry.request_id, routes.AccessDecision(decision="approve", agency_id=2),
        Response(), db, reviewer,
    )
    assert result["invitation_code"]
    assert result["email_status"] == "sent"
    assert delivered == [("applicant@example.com", result["invitation_code"])]
    assert db.query(User).count() == 1
    assert db.query(AccountAccessRequest).one().decision == "approve"
    assert not routes.pending_requests(db=db, reviewer=reviewer)
