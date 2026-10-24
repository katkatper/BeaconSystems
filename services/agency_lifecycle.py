from fastapi import HTTPException

from models.agencies import Agencies
from models.auth_session import AuthSession
from models.user import User
from services.clock import utc_now

AGENCY_STATUSES = {"active", "suspended", "offboarded"}


def agency_is_active(db, agency_id: int | None) -> bool:
    if agency_id is None:
        return False
    agency = db.query(Agencies).filter(Agencies.agency_id == agency_id).first()
    return agency is not None and agency.lifecycle_status == "active"


def set_agency_status(db, actor: User, agency: Agencies, status: str, reason: str) -> int:
    normalized_status = status.strip().lower()
    normalized_reason = reason.strip()
    if normalized_status not in AGENCY_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid agency status")
    if len(normalized_reason) < 10:
        raise HTTPException(status_code=400, detail="Agency status reason is required")
    if actor.agency_id == agency.agency_id and normalized_status != "active":
        raise HTTPException(status_code=400, detail="Cannot suspend your own agency")
    if agency.lifecycle_status == "offboarded" and normalized_status != "offboarded":
        raise HTTPException(status_code=409, detail="Offboarded agencies cannot be reactivated")

    agency.lifecycle_status = normalized_status
    agency.status_changed_at = utc_now()
    agency.status_reason = normalized_reason
    if normalized_status == "active":
        return 0

    user_ids = db.query(User.user_id).filter(User.agency_id == agency.agency_id)
    affected = db.query(User).filter(User.agency_id == agency.agency_id).update(
        {
            User.is_active: False,
            User.auth_version: User.auth_version + 1,
        },
        synchronize_session=False,
    )
    db.query(AuthSession).filter(
        AuthSession.user_id.in_(user_ids),
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: utc_now()}, synchronize_session=False)
    return affected
