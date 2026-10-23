import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from config.settings import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from models.auth_session import AuthSession
from services.clock import utc_now


def refresh_token_hash(token: str) -> str:
    """Return the one-way digest persisted instead of a raw refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_auth_session(
    user_id: int,
    *,
    ip_address: str | None,
    user_agent: str | None,
    mfa_authenticated: bool = False,
    now: datetime | None = None,
) -> tuple[AuthSession, str]:
    """Create an unpersisted server session and its client-only refresh token."""
    issued_at = now or utc_now()
    refresh_token = secrets.token_urlsafe(48)
    session = AuthSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        expires_at=issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        last_seen_at=issued_at,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:512] or None,
        refresh_token_hash=refresh_token_hash(refresh_token),
        refresh_expires_at=issued_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        mfa_authenticated=mfa_authenticated,
    )
    return session, refresh_token


def rotate_refresh_token(
    session: AuthSession,
    *,
    now: datetime | None = None,
) -> str:
    """Replace a refresh credential so a captured old token cannot be replayed."""
    refresh_token = secrets.token_urlsafe(48)
    session.refresh_token_hash = refresh_token_hash(refresh_token)
    session.last_seen_at = now or utc_now()
    return refresh_token


def revoke_auth_session(
    session: AuthSession,
    *,
    now: datetime | None = None,
) -> None:
    session.revoked_at = now or utc_now()


def serialize_auth_session(session: AuthSession, current_session_id: str) -> dict:
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "last_seen_at": session.last_seen_at,
        "expires_at": session.refresh_expires_at,
        "ip_address": session.ip_address,
        "user_agent": session.user_agent,
        "is_current": session.session_id == current_session_id,
        "mfa_authenticated": bool(session.mfa_authenticated),
    }
