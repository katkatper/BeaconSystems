from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.activity_log import ActivityLog
from models.alerts import Alerts
from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.evidence import Evidence
from models.legal_access_request import LegalAccessRequest
from models.sighting import Sighting
from models.user import User
from security.auth import get_current_user
from models.bolo_alert import BoloAlert

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def apply_dashboard_case_filter(query, current_user: User):
    if current_user.role == "admin":
        return query

    if current_user.role == "agency_admin":
        return query.filter(Cases.agency_id == current_user.agency_id)

    if current_user.role == "investigator":
        return query.filter(
            Cases.agency_id == current_user.agency_id,
            Cases.investigator_id == current_user.user_id,
        )

    return query.filter(Cases.case_id == -1)


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = datetime.utcnow() - timedelta(days=1)

    case_query = apply_dashboard_case_filter(db.query(Cases), current_user)

    total_cases = case_query.count()
    open_cases = case_query.filter(func.lower(Cases.case_status) == "open").count()
    high_priority_cases = case_query.filter(
        func.lower(Cases.priority_level).in_(["high", "critical"])
    ).count()

    accessible_case_ids = [case.case_id for case in case_query.all()]

    alert_query = db.query(Alerts)
    legal_query = db.query(LegalAccessRequest)
    partner_query = db.query(IntegrationSource)
    evidence_query = db.query(Evidence)
    access_query = db.query(CaseAccessGrant)

    if current_user.role != "admin":
        alert_query = alert_query.filter(
            Alerts.recipient_agency_id == current_user.agency_id
        )
        legal_query = legal_query.filter(
            LegalAccessRequest.agency_id == current_user.agency_id
        )
        access_query = access_query.filter(
            CaseAccessGrant.agency_id == current_user.agency_id
        )

    if accessible_case_ids:
        evidence_query = evidence_query.filter(Evidence.case_id.in_(accessible_case_ids))
    else:
        evidence_query = evidence_query.filter(Evidence.case_id == -1)

    new_alerts = alert_query.filter(
        func.lower(Alerts.alert_status) == "active"
    ).count()

    pending_legal_requests = legal_query.filter(
        LegalAccessRequest.status == "pending"
    ).count()

    pending_partner_sources = partner_query.filter(
        IntegrationSource.status == "pending"
    ).count()

    evidence_uploaded_today = evidence_query.filter(
        Evidence.created_at >= today
    ).count()

    restricted_access_events = access_query.filter(
        CaseAccessGrant.granted_at >= today
    ).count()

    active_partner_sources = partner_query.filter(
        IntegrationSource.is_active == True
    ).count()

    urgent_cases = (
        case_query.filter(func.lower(Cases.priority_level).in_(["high", "critical"]))
        .order_by(Cases.updated_at.desc())
        .limit(5)
        .all()
    )

    recent_alerts = alert_query.order_by(Alerts.created_at.desc()).limit(5).all()
    recent_evidence = evidence_query.order_by(Evidence.created_at.desc()).limit(5).all()
    recent_access = access_query.order_by(CaseAccessGrant.granted_at.desc()).limit(5).all()
    bolo_query = db.query(BoloAlert)

    if current_user.role != "admin":
     bolo_query = bolo_query.filter(BoloAlert.agency_id == current_user.agency_id)

    active_bolos = (
    bolo_query
    .filter(BoloAlert.status == "active")
    .order_by(BoloAlert.created_at.desc())
    .limit(5)
    .all()
)


    recent_sightings_query = db.query(Sighting)
    if accessible_case_ids:
        recent_sightings_query = recent_sightings_query.filter(
            Sighting.case_id.in_(accessible_case_ids)
        )
    else:
        recent_sightings_query = recent_sightings_query.filter(Sighting.case_id == -1)

    recent_sightings = (
        recent_sightings_query.order_by(Sighting.created_at.desc()).limit(5).all()
    )

    recent_activity = (
        db.query(ActivityLog)
        .order_by(ActivityLog.timestamp.desc())
        .limit(5)
        .all()
    )

    urgent_case = urgent_cases[0] if urgent_cases else None
    latest_alert = recent_alerts[0] if recent_alerts else None
    latest_evidence = recent_evidence[0] if recent_evidence else None

    command_briefing = {
        "urgent_case": {
            "case_id": urgent_case.case_id,
            "case_number": urgent_case.case_number,
            "title": urgent_case.title,
            "priority_level": urgent_case.priority_level,
        } if urgent_case else None,
        "latest_alert": {
            "alert_id": latest_alert.alert_id,
            "title": latest_alert.title,
            "severity": latest_alert.severity,
        } if latest_alert else None,
        "latest_evidence": {
            "evidence_id": latest_evidence.evidence_id,
            "file_name": latest_evidence.file_name,
            "case_id": latest_evidence.case_id,
        } if latest_evidence else None,
        "compliance": {
            "pending_legal_requests": pending_legal_requests,
            "pending_partner_sources": pending_partner_sources,
            "restricted_access_events": restricted_access_events,
        },
    }

    return {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "high_priority_cases": high_priority_cases,
        "command_briefing": command_briefing,
        "new_alerts": new_alerts,
        "pending_legal_requests": pending_legal_requests,
        "pending_partner_sources": pending_partner_sources,
        "evidence_uploaded_today": evidence_uploaded_today,
        "restricted_access_events": restricted_access_events,
        "active_partner_sources": active_partner_sources,
        "urgent_cases": urgent_cases,
        "recent_alerts": recent_alerts,
        "recent_evidence": recent_evidence,
        "active_bolos": active_bolos,
        "recent_access": recent_access,
        "recent_sightings": recent_sightings,
        "recent_activity": recent_activity,
    }
