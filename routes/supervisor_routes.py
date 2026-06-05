from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.bolo_alert import BoloAlert
from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.case_team_member import CaseTeamMember
from models.legal_access_request import LegalAccessRequest
from models.user import User
from security.auth import require_role
from services.activity_service import create_activity_log


router = APIRouter(prefix="/supervisor", tags=["Supervisor Review"])


class CaseAccessReview(BaseModel):
    review_notes: str | None = None


class CaseTeamAssignment(BaseModel):
    user_id: int
    role: str = "support_investigator"
    reason: str | None = None


TEAM_MEMBER_ROLES = {
    "support_investigator",
    "analyst_support",
    "supervisor_observer",
}


@router.get("/queue")

# Supervisor Review Queue centralizes high-risk operational items that require
# admin or agency supervisor attention. This keeps legal, partner, case access,
# and active BOLO oversight in one auditable workflow.


def get_supervisor_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
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
        .order_by(LegalAccessRequest.requested_at.desc())
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

    investigator_ids = {
        case.investigator_id for case in high_priority_cases if case.investigator_id
    }
    investigators = (
        {
            user.user_id: user.username
            for user in db.query(User).filter(User.user_id.in_(investigator_ids)).all()
        }
        if investigator_ids
        else {}
    )
    high_priority_case_summaries = [
        {
            "case_id": case.case_id,
            "case_number": case.case_number,
            "title": case.title,
            "priority_level": case.priority_level,
            "case_status": case.case_status,
            "investigator_id": case.investigator_id,
            "investigator_name": investigators.get(case.investigator_id),
        }
        for case in high_priority_cases
    ]

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
        "high_priority_cases": high_priority_case_summaries,
        "pending_case_access": (
            access_query
            .filter(CaseAccessGrant.status == "pending")
            .order_by(CaseAccessGrant.granted_at.desc())
            .limit(10)
            .all()
        ),
        "recent_case_access": recent_case_access,
        "active_bolos": active_bolos,
    }


def get_supervisor_case(
    db: Session,
    case_id: int,
    current_user: User,
):
    query = db.query(Cases).filter(Cases.case_id == case_id)

    if current_user.role != "admin":
        query = query.filter(Cases.agency_id == current_user.agency_id)

    case = query.first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    return case


@router.get("/cases/{case_id}/team")
def get_case_team(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    case = get_supervisor_case(db, case_id, current_user)
    lead = db.query(User).filter(User.user_id == case.investigator_id).first()
    team_members = (
        db.query(CaseTeamMember, User)
        .join(User, CaseTeamMember.user_id == User.user_id)
        .filter(
            CaseTeamMember.case_id == case_id,
            CaseTeamMember.status == "active",
        )
        .order_by(CaseTeamMember.assigned_at.desc())
        .all()
    )

    return {
        "case_id": case.case_id,
        "case_number": case.case_number,
        "lead_investigator": {
            "user_id": lead.user_id,
            "username": lead.username,
            "role": "lead_investigator",
        } if lead else None,
        "team_members": [
            {
                "team_member_id": member.team_member_id,
                "user_id": user.user_id,
                "username": user.username,
                "role": member.role,
                "reason": member.reason,
                "assigned_by": member.assigned_by,
                "assigned_at": member.assigned_at,
            }
            for member, user in team_members
        ],
    }


@router.post("/cases/{case_id}/team")
def assign_case_team_member(
    case_id: int,
    data: CaseTeamAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    case = get_supervisor_case(db, case_id, current_user)
    role = data.role.strip().lower()

    if role not in TEAM_MEMBER_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported case team role")

    user = db.query(User).filter(User.user_id == data.user_id).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="Active user not found")

    if current_user.role != "admin" and user.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Cannot assign a user from another agency")

    if user.user_id == case.investigator_id:
        raise HTTPException(status_code=400, detail="Lead investigator is already assigned to this case")

    existing_member = (
        db.query(CaseTeamMember)
        .filter(
            CaseTeamMember.case_id == case_id,
            CaseTeamMember.user_id == data.user_id,
        )
        .first()
    )

    if existing_member:
        existing_member.role = role
        existing_member.status = "active"
        existing_member.reason = data.reason
        existing_member.assigned_by = current_user.user_id
        existing_member.assigned_at = datetime.utcnow()
        existing_member.removed_at = None
        member = existing_member
    else:
        member = CaseTeamMember(
            case_id=case_id,
            user_id=data.user_id,
            agency_id=case.agency_id,
            role=role,
            reason=data.reason,
            assigned_by=current_user.user_id,
        )
        db.add(member)

    db.commit()
    db.refresh(member)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CASE_TEAM_MEMBER_ASSIGNED",
        entity="case",
        entity_id=case_id,
        details=(
            f"Assigned user {data.user_id} to case {case.case_number} as {role}. "
            f"Reason: {data.reason or 'None'}"
        ),
    )

    return {
        "message": "Case team member assigned and logged",
        "team_member_id": member.team_member_id,
    }


@router.delete("/cases/{case_id}/team/{user_id}")
def remove_case_team_member(
    case_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    case = get_supervisor_case(db, case_id, current_user)
    member = (
        db.query(CaseTeamMember)
        .filter(
            CaseTeamMember.case_id == case_id,
            CaseTeamMember.user_id == user_id,
            CaseTeamMember.status == "active",
        )
        .first()
    )

    if not member:
        raise HTTPException(status_code=404, detail="Active case team member not found")

    member.status = "removed"
    member.removed_at = datetime.utcnow()
    db.commit()

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CASE_TEAM_MEMBER_REMOVED",
        entity="case",
        entity_id=case_id,
        details=f"Removed user {user_id} from case {case.case_number}",
    )

    return {"message": "Case team member removed and logged"}


def get_reviewable_case_access_grant(
    db: Session,
    grant_id: int,
    current_user: User,
):
    query = db.query(CaseAccessGrant).filter(CaseAccessGrant.grant_id == grant_id)

    if current_user.role != "admin":
        query = query.filter(CaseAccessGrant.agency_id == current_user.agency_id)

    grant = query.first()

    if not grant:
        raise HTTPException(status_code=404, detail="Case access request not found")

    return grant


@router.put("/case-access/{grant_id}/approve")
def approve_case_access_request(
    grant_id: int,
    data: CaseAccessReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    grant = get_reviewable_case_access_grant(db, grant_id, current_user)

    grant.status = "active"
    grant.approval_type = "manual"
    grant.reviewed_by = current_user.user_id
    grant.review_notes = data.review_notes
    grant.expires_at = datetime.utcnow() + timedelta(hours=24)
    grant.revoked_at = None

    db.commit()
    db.refresh(grant)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CASE_ACCESS_APPROVED_BY_SUPERVISOR",
        entity="case",
        entity_id=grant.case_id,
        details=f"Approved case access request {grant.grant_id}. Notes: {data.review_notes or 'None'}",
    )

    return {"message": "Case access approved for 24 hours"}


@router.put("/case-access/{grant_id}/deny")
def deny_case_access_request(
    grant_id: int,
    data: CaseAccessReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    grant = get_reviewable_case_access_grant(db, grant_id, current_user)

    grant.status = "denied"
    grant.approval_type = "manual"
    grant.reviewed_by = current_user.user_id
    grant.review_notes = data.review_notes
    grant.revoked_at = datetime.utcnow()

    db.commit()
    db.refresh(grant)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CASE_ACCESS_DENIED",
        entity="case",
        entity_id=grant.case_id,
        details=f"Denied case access request {grant.grant_id}. Notes: {data.review_notes or 'None'}",
    )

    return {"message": "Case access denied"}


