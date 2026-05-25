from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.bolo_alert import BoloAlert
from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.legal_access_request import LegalAccessRequest
from models.user import User
from security.auth import require_role


router = APIRouter(prefix="/supervisor", tags=["Supervisor Review"])


@router.get("/queue")

# Supervisor Review Queue centralizes high-risk operational items that require
# admin or agency supervisor attention. This keeps legal, partner, case access,
# and active BOLO oversight in one auditable workflow.


def get_supervisor_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
):
    case_query = db.query(Cases)
    legal_query = db.query(LegalAccessRequest)
    partner_query = db.query(IntegrationSource)
    access_query = db.query(CaseAccessGrant)
    bolo_query = db.query(BoloAlert)

# Admin can see all agencies. Agency admins are restricted to their own agency
# to avoid cross-agency data exposure.

    if current_user.role != "admin":
        case_query = case_query.filter(Cases.agency_id == current_user.agency_id)
        legal_query = legal_query.filter(
            LegalAccessRequest.agency_id == current_user.agency_id
        )
        access_query = access_query.filter(
            CaseAccessGrant.agency_id == current_user.agency_id
        )
        bolo_query = bolo_query.filter(BoloAlert.agency_id == current_user.agency_id)

    pending_legal_requests = (
        legal_query
        .filter(LegalAccessRequest.status == "pending")
        .order_by(LegalAccessRequest.created_at.desc())
        .limit(10)
        .all()
    )

    pending_partner_sources = (
        partner_query
        .filter(IntegrationSource.status == "pending")
        .order_by(IntegrationSource.created_at.desc())
        .limit(10)
        .all()
    )

    high_priority_cases = (
        case_query
        .filter(func.lower(Cases.priority_level).in_(["high", "critical"]))
        .order_by(Cases.updated_at.desc())
        .limit(10)
        .all()
    )

 # Restricted case access is surfaced for supervisor review because each access
# should have a documented reason and may need follow-up.

    recent_case_access = (
        access_query
        .order_by(CaseAccessGrant.granted_at.desc())
        .limit(10)
        .all()
    )

# Active BOLO alerts are included so supervisors can monitor urgent public safety
# notices and make sure stale notices are closed or updated.

    active_bolos = (
        bolo_query
        .filter(BoloAlert.status == "active")
        .order_by(BoloAlert.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "pending_legal_requests": pending_legal_requests,
        "pending_partner_sources": pending_partner_sources,
        "high_priority_cases": high_priority_cases,
        "recent_case_access": recent_case_access,
        "active_bolos": active_bolos,
    }


