from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.activity_log import ActivityLog
from models.case_access_grant import CaseAccessGrant
from models.evidence_chain import EvidenceChain
from models.legal_access_request import LegalAccessRequest
from models.user import User
from security.auth import require_role


router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


# Audit Center is restricted to supervisors/admins because it exposes sensitive
# access history across cases, evidence, legal requests, and partner workflows.
@router.get("/summary")
def get_audit_summary(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
):
    activity_query = db.query(ActivityLog)
    access_query = db.query(CaseAccessGrant)
    evidence_query = db.query(EvidenceChain)
    legal_query = db.query(LegalAccessRequest)
    partner_query = db.query(IntegrationSource)

    # Admin can review the whole system. Agency admins only see audit records
    # scoped to their agency where the table supports agency scoping.
    if current_user.role != "admin":
        activity_query = activity_query.filter(
            ActivityLog.agency_id == current_user.agency_id
        )
        access_query = access_query.filter(
            CaseAccessGrant.agency_id == current_user.agency_id
        )
        legal_query = legal_query.filter(
            LegalAccessRequest.agency_id == current_user.agency_id
        )

    return {
        "compliance_readiness": {
            "audit_logging_active": True,
            "evidence_chain_active": True,
            "missing_info_legal_requests": legal_query.filter(
                LegalAccessRequest.status == "missing_info"
            ).count(),
            "denied_legal_requests": legal_query.filter(
                LegalAccessRequest.status == "denied"
            ).count(),
            "pending_legal_requests": legal_query.filter(
                LegalAccessRequest.status == "pending"
            ).count(),
            "approved_legal_requests": legal_query.filter(
                LegalAccessRequest.status == "approved"
            ).count(),
            "pending_partner_sources": partner_query.filter(
                IntegrationSource.status == "pending"
            ).count(),
        },
        "recent_activity": (
            activity_query
            .order_by(ActivityLog.timestamp.desc())
            .limit(limit)
            .all()
        ),
        "restricted_case_access": (
            access_query
            .order_by(CaseAccessGrant.granted_at.desc())
            .limit(limit)
            .all()
        ),
        "evidence_chain_events": (
            evidence_query
            .order_by(EvidenceChain.created_at.desc())
            .limit(limit)
            .all()
        ),
    }


# Supervisors can search users before drilling into a specific user's audit trail.
# This avoids exposing a giant system-wide log as the default audit view.
@router.get("/users")
def search_audit_users(
    q: str = Query("", min_length=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
):
    query = db.query(User)

    if current_user.role != "admin":
        query = query.filter(User.agency_id == current_user.agency_id)

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                User.username.ilike(search),
                User.email.ilike(search),
            )
        )

    return query.order_by(User.username.asc()).limit(limit).all()


# User-specific audit trail shows what one person accessed or changed. This is
# easier for supervisors to review than scanning all system events at once.
@router.get("/users/{user_id}/activity")
def get_user_audit_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role != "admin" and user.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="User belongs to another agency")

    return {
        "user": user,
        "recent_activity": (
            db.query(ActivityLog)
            .filter(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.timestamp.desc())
            .limit(limit)
            .all()
        ),
        "restricted_case_access": (
            db.query(CaseAccessGrant)
            .filter(CaseAccessGrant.user_id == user_id)
            .order_by(CaseAccessGrant.granted_at.desc())
            .limit(limit)
            .all()
        ),
        "evidence_chain_events": (
            db.query(EvidenceChain)
            .filter(EvidenceChain.user_id == user_id)
            .order_by(EvidenceChain.created_at.desc())
            .limit(limit)
            .all()
        ),
    }
