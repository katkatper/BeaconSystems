from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.activity_log import ActivityLog
from models.agency_exchange import AgencyExchange
from models.alerts import Alerts
from models.bolo_alert import BoloAlert
from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.case_team_member import CaseTeamMember
from models.evidence import Evidence
from models.leads import Leads
from models.legal_access_request import LegalAccessRequest
from models.sighting import Sighting
from models.timeline_events import Timeline_Event
from models.user import User
from security.auth import require_role
from services.activity_service import create_activity_log


router = APIRouter(prefix="/supervisor", tags=["Supervisor Review"])


class CaseAccessReview(BaseModel):
    review_notes: str | None = None


class CaseTeamAssignment(BaseModel):
    user_id: int
    role: str = "lead_investigator"
    reason: str | None = None


TEAM_MEMBER_ROLES = {
    "supervisor",
    "lead_investigator",
    "investigator",
    "intelligence_analyst",
    "evidence_technician",
    "tip_coordinator",
    "external_agency_user",
    "administrator",
    "command_staff",
}


@router.get("/queue")

# Supervisor Review Queue centralizes high-risk operational items that require
# admin or agency supervisor attention. This keeps legal, partner, case access,
# and active BOLO oversight in one auditable workflow.


def get_supervisor_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)
    inactive_statuses = ["closed", "resolved", "archived"]
    case_query = db.query(Cases)
    legal_query = db.query(LegalAccessRequest)
    partner_query = db.query(IntegrationSource)
    access_query = db.query(CaseAccessGrant)
    bolo_query = db.query(BoloAlert)
    alert_query = db.query(Alerts)
    evidence_query = db.query(Evidence)
    exchange_query = db.query(AgencyExchange)
    investigator_query = db.query(User).filter(
        User.role == "investigator",
        User.is_active == True,  # noqa: E712
    )

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
        alert_query = alert_query.filter(
            Alerts.recipient_agency_id == current_user.agency_id
        )
        investigator_query = investigator_query.filter(
            User.agency_id == current_user.agency_id
        )

    open_case_query = case_query.filter(
        or_(
            Cases.case_status == None,  # noqa: E711
            ~func.lower(Cases.case_status).in_(inactive_statuses),
        )
    )
    open_cases = open_case_query.all()
    open_case_ids = [case.case_id for case in open_cases]
    open_case_filter = open_case_ids or [-1]

    evidence_query = evidence_query.filter(Evidence.case_id.in_(open_case_filter))
    exchange_query = exchange_query.filter(AgencyExchange.case_id.in_(open_case_filter))
    leads_query = db.query(Leads).filter(Leads.case_id.in_(open_case_filter))
    sighting_query = db.query(Sighting).filter(Sighting.case_id.in_(open_case_filter))
    timeline_query = db.query(Timeline_Event).filter(
        Timeline_Event.case_id.in_(open_case_filter)
    )

    active_case_counts = {
        investigator_id: count
        for investigator_id, count in (
            open_case_query
            .filter(Cases.investigator_id != None)  # noqa: E711
            .with_entities(Cases.investigator_id, func.count(Cases.case_id))
            .group_by(Cases.investigator_id)
            .all()
        )
    }
    recent_activity_counts = {
        user_id: count
        for user_id, count in (
            db.query(ActivityLog.user_id, func.count(ActivityLog.id))
            .filter(ActivityLog.timestamp >= fourteen_days_ago)
            .group_by(ActivityLog.user_id)
            .all()
        )
    }
    investigator_workload = []

    for investigator in investigator_query.order_by(User.username.asc()).all():
        active_cases = active_case_counts.get(investigator.user_id, 0)
        recent_results = recent_activity_counts.get(investigator.user_id, 0)
        workload_status = "balanced"

        if active_cases >= 5:
            workload_status = "overloaded"
        elif active_cases <= 2:
            workload_status = "capacity"

        investigator_workload.append({
            "user_id": investigator.user_id,
            "username": investigator.username,
            "email": investigator.email,
            "active_cases": active_cases,
            "recent_results": recent_results,
            "workload_status": workload_status,
        })

    inactive_cases = (
        open_case_query
        .filter(Cases.updated_at <= seven_days_ago)
        .order_by(Cases.updated_at.asc())
        .limit(12)
        .all()
    )
    inactive_case_summaries = []

    for case in inactive_cases:
        last_update = case.updated_at or case.created_at or now
        days_inactive = (now - last_update).days
        inactive_case_summaries.append({
            "case_id": case.case_id,
            "case_number": case.case_number,
            "title": case.title,
            "case_status": case.case_status,
            "priority_level": case.priority_level,
            "investigator_id": case.investigator_id,
            "days_inactive": days_inactive,
            "bucket": "30+ days" if days_inactive >= 30 else "14+ days" if days_inactive >= 14 else "7+ days",
            "updated_at": case.updated_at,
        })

    lead_status_counts = {
        "total": 0,
        "new": 0,
        "assigned": 0,
        "pending": 0,
        "closed": 0,
        "unassigned": 0,
        "overdue_followups": 0,
    }

    for lead in leads_query.all():
        lead_status_counts["total"] += 1
        status = (lead.status or "new").strip().lower()

        if status in lead_status_counts:
            lead_status_counts[status] += 1
        elif status in {"open", "active"}:
            lead_status_counts["assigned"] += 1
        else:
            lead_status_counts["new"] += 1

        if status in {"new", "unassigned"}:
            lead_status_counts["unassigned"] += 1

        if status in {"pending", "assigned", "open", "active"} and lead.created_at <= seven_days_ago:
            lead_status_counts["overdue_followups"] += 1

    unassigned_case_count = open_case_query.filter(
        Cases.investigator_id == None  # noqa: E711
    ).count()
    pending_warrants = (
        legal_query
        .filter(
            LegalAccessRequest.status == "pending",
            func.lower(LegalAccessRequest.authority_type).like("%warrant%"),
        )
        .count()
    )
    missing_reports = len([
        case for case in open_cases
        if (case.updated_at or case.created_at or now) <= fourteen_days_ago
    ])
    high_risk_case_count = (
        open_case_query
        .filter(func.lower(Cases.priority_level).in_(["high", "critical"]))
        .count()
    )
    active_alert_count = (
        alert_query
        .filter(func.lower(Alerts.alert_status) == "active")
        .count()
    )
    critical_alert_count = (
        alert_query
        .filter(
            func.lower(Alerts.alert_status) == "active",
            func.lower(Alerts.severity).in_(["high", "critical"]),
        )
        .count()
    )
    cases_needing_attention_today = (
        len(inactive_case_summaries) +
        unassigned_case_count +
        lead_status_counts["overdue_followups"] +
        pending_warrants
    )

    command_dashboard = {
        "active_cases": len(open_cases),
        "high_risk_missing_persons": high_risk_case_count,
        "critical_alerts": critical_alert_count,
        "active_alerts": active_alert_count,
        "cases_needing_attention_today": cases_needing_attention_today,
        "unassigned_cases": unassigned_case_count,
    }

    stall_risk_summary = {
        "inactive_7_days": len([item for item in inactive_case_summaries if item["days_inactive"] >= 7]),
        "inactive_14_days": len([item for item in inactive_case_summaries if item["days_inactive"] >= 14]),
        "inactive_30_days": len([item for item in inactive_case_summaries if item["days_inactive"] >= 30]),
        "unassigned_leads": lead_status_counts["unassigned"],
        "missing_followups": lead_status_counts["overdue_followups"],
        "pending_warrants": pending_warrants,
        "missing_reports": missing_reports,
    }

    recent_timeline_events = (
        timeline_query
        .order_by(Timeline_Event.timestamp.desc())
        .limit(8)
        .all()
    )
    recent_sightings = (
        sighting_query
        .order_by(Sighting.created_at.desc())
        .limit(5)
        .all()
    )
    recent_evidence = (
        evidence_query
        .order_by(Evidence.created_at.desc())
        .limit(5)
        .all()
    )
    recent_exchanges = (
        exchange_query
        .order_by(AgencyExchange.created_at.desc())
        .limit(8)
        .all()
    )

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

    pending_case_access = (
        access_query
        .filter(CaseAccessGrant.status == "pending")
        .order_by(CaseAccessGrant.granted_at.desc())
        .limit(10)
        .all()
    )

    access_items = pending_case_access + recent_case_access
    access_case_ids = {item.case_id for item in access_items}
    access_user_ids = {item.user_id for item in access_items}
    access_cases = (
        {
            case.case_id: case
            for case in db.query(Cases).filter(Cases.case_id.in_(access_case_ids)).all()
        }
        if access_case_ids
        else {}
    )
    access_users = (
        {
            user.user_id: user.username
            for user in db.query(User).filter(User.user_id.in_(access_user_ids)).all()
        }
        if access_user_ids
        else {}
    )

    def serialize_case_access(item: CaseAccessGrant):
        case = access_cases.get(item.case_id)

        return {
            "grant_id": item.grant_id,
            "case_id": item.case_id,
            "case_number": case.case_number if case else None,
            "case_title": case.title if case else None,
            "user_id": item.user_id,
            "username": access_users.get(item.user_id),
            "agency_id": item.agency_id,
            "reason": item.reason,
            "reason_category": item.reason_category,
            "approval_type": item.approval_type,
            "status": item.status,
            "reviewed_by": item.reviewed_by,
            "review_notes": item.review_notes,
            "granted_at": item.granted_at,
            "expires_at": item.expires_at,
            "revoked_at": item.revoked_at,
        }

# Active BOLO alerts are included so supervisors can monitor urgent public safety
# notices and make sure stale notices are closed or updated.

    active_bolos = (
        bolo_query
        .filter(BoloAlert.status == "active")
        .order_by(BoloAlert.created_at.desc())
        .limit(10)
        .all()
    )
    case_lookup = {case.case_id: case for case in open_cases}

    def case_label(case_id: int):
        case = case_lookup.get(case_id)
        return case.case_number if case else f"Case {case_id}"

    return {
        "command_dashboard": command_dashboard,
        "investigator_workload": investigator_workload,
        "inactive_cases": inactive_case_summaries,
        "stall_risk_summary": stall_risk_summary,
        "lead_summary": lead_status_counts,
        "timeline_summary": {
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "case_id": event.case_id,
                    "case_number": case_label(event.case_id),
                    "event_type": event.event_type,
                    "source_type": event.source_type,
                    "location": event.location,
                    "description": event.description,
                    "timestamp": event.timestamp,
                }
                for event in recent_timeline_events
            ],
            "recent_sightings": [
                {
                    "sighting_id": sighting.sighting_id,
                    "case_id": sighting.case_id,
                    "case_number": case_label(sighting.case_id),
                    "location": sighting.location,
                    "confidence_score": sighting.confidence_score,
                    "created_at": sighting.created_at,
                }
                for sighting in recent_sightings
            ],
            "recent_evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "case_id": item.case_id,
                    "case_number": case_label(item.case_id),
                    "evidence_type": item.evidence_type,
                    "custody_status": item.custody_status,
                    "created_at": item.created_at,
                }
                for item in recent_evidence
            ],
        },
        "agency_coordination": {
            "involved_agencies": sorted({
                agency
                for exchange in recent_exchanges
                for agency in [exchange.from_agency, exchange.to_agency]
                if agency
            }),
            "shared_intelligence": len(recent_exchanges),
            "joint_investigations": len({exchange.case_id for exchange in recent_exchanges}),
            "outstanding_requests": len([
                item for item in pending_legal_requests if item.case_id in case_lookup
            ]),
            "recent_exchanges": [
                {
                    "exchange_id": exchange.exchange_id,
                    "case_id": exchange.case_id,
                    "case_number": case_label(exchange.case_id),
                    "from_agency": exchange.from_agency,
                    "to_agency": exchange.to_agency,
                    "information_type": exchange.information_type,
                    "summary": exchange.summary,
                    "status": exchange.status,
                    "created_at": exchange.created_at,
                }
                for exchange in recent_exchanges
            ],
        },
        "pending_legal_requests": pending_legal_requests,
        "pending_partner_sources": pending_partner_sources,
        "high_priority_cases": high_priority_case_summaries,
        "pending_case_access": [serialize_case_access(item) for item in pending_case_access],
        "recent_case_access": [serialize_case_access(item) for item in recent_case_access],
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


