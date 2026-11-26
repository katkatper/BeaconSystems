import hashlib
import secrets
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.connection import get_db
from models.agencies import Agencies
from models.onboarding import AccountAccessRequest, AccountInvitation
from models.user import User
from security.auth import hash_password, require_role
from security.rate_limit import client_address, enforce_rate_limit
from security.user_management import USER_MANAGER_ROLES
from services.clock import utc_now
from services.invitation_email import send_invitation_email


class OnboardingRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request):
            try:
                return await handler(request)
            except RequestValidationError as exc:
                raise HTTPException(422, "Check the fields and try again.") from exc

        return handle


router = APIRouter(prefix="/onboarding", tags=["Account onboarding"], route_class=OnboardingRoute)
InviteRole = Literal["investigator", "supervisor", "analyst", "viewer"]


class AccessSubmission(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr = Field(max_length=254)
    agency_name: str = Field(min_length=2, max_length=200)


class InviteSubmission(BaseModel):
    email: EmailStr = Field(max_length=254)
    role: InviteRole
    agency_id: int | None = None


class AccessDecision(BaseModel):
    decision: Literal["approve", "decline"]
    agency_id: int | None = None
    role: InviteRole = "viewer"


class AccountRegistration(BaseModel):
    invitation_code: str = Field(min_length=43, max_length=43)
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=128, repr=False)


def digest(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def active_agency(db: Session, agency_id: int | None) -> bool:
    return agency_id is not None and db.query(Agencies.agency_id).filter(
        Agencies.agency_id == agency_id, Agencies.lifecycle_status == "active",
    ).first() is not None


def issue_invite(db: Session, issuer: User, data: InviteSubmission):
    agency_id = issuer.agency_id if issuer.role == "agency_admin" else data.agency_id
    if not active_agency(db, agency_id):
        raise HTTPException(400, "Select an active agency.")
    email = data.email.lower()
    if db.query(User.user_id).filter(func.lower(User.email) == email).first():
        raise HTTPException(409, "That email already belongs to an account.")
    code = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(hours=24)
    db.add(AccountInvitation(
        token_hash=digest(code), email=email, role=data.role, agency_id=agency_id,
        issuer_id=issuer.user_id, expires_at=expires_at,
    ))
    return {"invitation_code": code, "expires_at": expires_at}


@router.post("/invitations", status_code=201)
def create_invitation(
    data: InviteSubmission, response: Response, db: Session = Depends(get_db),
    issuer: User = Depends(require_role(*USER_MANAGER_ROLES)),
):
    result = issue_invite(db, issuer, data)
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    result["email_status"] = send_invitation_email(data.email.lower(), result["invitation_code"])
    return result


@router.post("/access-requests", status_code=202)
def request_access(data: AccessSubmission, request: Request, db: Session = Depends(get_db)):
    enforce_rate_limit(
        request, namespace="account-access-request", identifier=client_address(request),
        limit=5, window_seconds=3600,
    )
    email = data.email.lower()
    if not db.query(AccountAccessRequest.request_id).filter(
        AccountAccessRequest.email == email, AccountAccessRequest.reviewed_at.is_(None),
    ).first():
        db.add(AccountAccessRequest(email=email, agency_name=data.agency_name, created_at=utc_now()))
        db.commit()
    return {"message": "Your request has been received for review."}


@router.get("/access-requests")
def pending_requests(
    after_id: int = 0,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_role("platform_admin")),
):
    return [
        {"request_id": row.request_id, "email": row.email, "agency_name": row.agency_name}
        for row in db.query(AccountAccessRequest).filter(
            AccountAccessRequest.reviewed_at.is_(None), AccountAccessRequest.request_id > after_id,
        ).order_by(AccountAccessRequest.request_id).limit(50).all()
    ]


@router.post("/access-requests/{request_id}/decision")
def review_access(
    request_id: int, data: AccessDecision, response: Response, db: Session = Depends(get_db),
    reviewer: User = Depends(require_role("platform_admin")),
):
    claim = db.execute(update(AccountAccessRequest).where(
        AccountAccessRequest.request_id == request_id, AccountAccessRequest.reviewed_at.is_(None),
    ).values(reviewed_at=utc_now(), decision=data.decision))
    if claim.rowcount != 1:
        raise HTTPException(404, "Pending request not found.")
    result = {"message": "Request declined."}
    recipient = None
    if data.decision == "approve":
        row = db.get(AccountAccessRequest, request_id)
        recipient = row.email
        result = issue_invite(db, reviewer, InviteSubmission(
            email=recipient, role=data.role, agency_id=data.agency_id,
        ))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    if recipient:
        result["email_status"] = send_invitation_email(recipient, result["invitation_code"])
    return result


@router.post("/register", status_code=201)
def redeem_invitation(data: AccountRegistration, request: Request, db: Session = Depends(get_db)):
    enforce_rate_limit(
        request, namespace="account-invite-redemption", identifier=client_address(request),
        limit=15, window_seconds=900,
    )
    now = utc_now()
    key = digest(data.invitation_code)
    invite = db.get(AccountInvitation, key)
    issuer = db.get(User, invite.issuer_id) if invite else None
    if (
        not invite or invite.used_at is not None or invite.expires_at <= now
        or not issuer or not issuer.is_active or issuer.role not in USER_MANAGER_ROLES
        or (issuer.role == "agency_admin" and issuer.agency_id != invite.agency_id)
        or not active_agency(db, invite.agency_id)
    ):
        raise HTTPException(400, "Invitation is invalid, expired, or already used.")
    if db.query(User.user_id).filter(
        (func.lower(User.email) == invite.email) | (func.lower(User.username) == data.username.lower())
    ).first():
        raise HTTPException(409, "Could not create account with these details.")
    claimed = db.execute(update(AccountInvitation).where(
        AccountInvitation.token_hash == key, AccountInvitation.used_at.is_(None),
        AccountInvitation.expires_at > utc_now(),
    ).values(used_at=now))
    if claimed.rowcount != 1:
        raise HTTPException(400, "Invitation is invalid, expired, or already used.")
    db.add(User(
        email=invite.email, username=data.username, password_hash=hash_password(data.password),
        role=invite.role, agency_id=invite.agency_id, is_active=True, password_changed_at=now,
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Could not create account with these details.") from exc
    return {"message": "Account created. You can now sign in."}
