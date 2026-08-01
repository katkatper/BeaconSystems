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
from security.case_access import apply_case_access_filter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = datetime.utcnow() - timedelta(days=1)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    inactive_statuses = ["closed", "resolved", "archived"]

    case_query = apply_case_access_filter(db.query(Cases), current_user)

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
        alert_query = alert_query.filter(Alerts.case_id.in_(accessible_case_ids))
    else:
        evidence_query = evidence_query.filter(Evidence.case_id == -1)
        alert_query = alert_query.filter(Alerts.case_id == -1)

    dashboard_alert_query = alert_query.filter(
        (Alerts.alert_type.is_(None))
        | (~func.lower(Alerts.alert_type).like("%deleted%")),
        (Alerts.title.is_(None)) | (~func.lower(Alerts.title).like("%deleted%")),
    )

    new_alerts = dashboard_alert_query.filter(
        func.lower(Alerts.alert_status) == "active"
    ).count()

    pending_legal_requests = legal_query.filter(
        LegalAccessRequest.status == "pending"
    ).count()
    missing_info_legal_requests = legal_query.filter(
        LegalAccessRequest.status == "missing_info"
    ).count()
    denied_legal_requests = legal_query.filter(
        LegalAccessRequest.status == "denied"
    ).count()
    approved_legal_requests = legal_query.filter(
        LegalAccessRequest.status == "approved"
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

    inactive_case_query = case_query.filter(
        Cases.updated_at <= seven_days_ago,
        func.lower(Cases.case_status).notin_(inactive_statuses),
    )
    stalled_cases = inactive_case_query.count()
    inactive_7_days = stalled_cases
    inactive_14_days = case_query.filter(
        Cases.updated_at <= fourteen_days_ago,
        func.lower(Cases.case_status).notin_(inactive_statuses),
    ).count()
    unassigned_cases = case_query.filter(
        Cases.investigator_id == None,  # noqa: E711
        func.lower(Cases.case_status).notin_(inactive_statuses),
    ).count()

    urgent_cases = (
        case_query.filter(func.lower(Cases.priority_level).in_(["high", "critical"]))
        .order_by(Cases.updated_at.desc())
        .limit(5)
        .all()
    )

    recent_alerts = (
        dashboard_alert_query
        .filter(
            func.lower(Alerts.alert_status) == "active",
            func.lower(Alerts.severity).in_(["high", "critical"]),
        )
        .order_by(Alerts.created_at.desc())
        .limit(5)
        .all()
    )
    recent_evidence = evidence_query.order_by(Evidence.created_at.desc()).limit(5).all()
    recent_access = access_query.order_by(CaseAccessGrant.granted_at.desc()).limit(5).all()
    bolo_query = db.query(BoloAlert)
    if accessible_case_ids:
        bolo_query = bolo_query.filter(BoloAlert.case_id.in_(accessible_case_ids))
    elif current_user.role != "admin":
        bolo_query = bolo_query.filter(BoloAlert.case_id == -1)

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
            "missing_info_legal_requests": missing_info_legal_requests,
            "denied_legal_requests": denied_legal_requests,
            "approved_legal_requests": approved_legal_requests,
            "pending_partner_sources": pending_partner_sources,
            "restricted_access_events": restricted_access_events,
        },
    }
    def serialize_case(case: Cases):
        return {
            "case_id": case.case_id,
            "case_number": case.case_number,
            "title": case.title,
            "person_id": case.person_id,
            "agency_id": case.agency_id,
            "investigator_id": case.investigator_id,
            "case_status": case.case_status,
            "priority_level": case.priority_level,
            "last_seen_location": case.last_seen_location,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
        }

    def serialize_alert(alert: Alerts):
        return {
            "alert_id": alert.alert_id,
            "case_id": alert.case_id,
            "person_id": alert.person_id,
            "title": alert.title,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "description": alert.description,
            "alert_status": alert.alert_status,
            "created_at": alert.created_at,
        }

    def serialize_evidence(item: Evidence):
        return {
            "evidence_id": item.evidence_id,
            "case_id": item.case_id,
            "evidence_type": item.evidence_type,
            "description": item.description,
            "custody_status": item.custody_status,
            "file_name": item.file_name,
            "created_at": item.created_at,
        }

    def serialize_bolo(item: BoloAlert):
        return {
            "bolo_id": item.bolo_id,
            "case_id": item.case_id,
            "title": item.title,
            "person_name": item.person_name,
            "last_known_location": item.last_known_location,
            "description": item.description,
            "risk_level": item.risk_level,
            "status": item.status,
            "expires_at": item.expires_at,
            "created_at": item.created_at,
        }

    def serialize_sighting(sighting: Sighting):
        return {
            "sighting_id": sighting.sighting_id,
            "case_id": sighting.case_id,
            "person_id": sighting.person_id,
            "location": sighting.location,
            "longitude": sighting.longitude,
            "latitude": sighting.latitude,
            "description": sighting.description,
            "confidence_score": sighting.confidence_score,
            "created_at": sighting.created_at,
        }

    def serialize_access(item: CaseAccessGrant):
        return {
            "grant_id": item.grant_id,
            "case_id": item.case_id,
            "user_id": item.user_id,
            "status": item.status,
            "reason": item.reason,
            "granted_at": item.granted_at,
            "expires_at": item.expires_at,
        }

    def serialize_activity(item: ActivityLog):
        return {
            "id": item.id,
            "user_id": item.user_id,
            "agency_id": item.agency_id,
            "action": item.action,
            "entity": item.entity,
            "entity_id": item.entity_id,
            "details": item.details,
            "timestamp": item.timestamp,
        }

    return {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "high_priority_cases": high_priority_cases,
        "stalled_cases": stalled_cases,
        "inactive_7_days": inactive_7_days,
        "inactive_14_days": inactive_14_days,
        "unassigned_cases": unassigned_cases,
        "pending_warrants": pending_legal_requests,
        "missing_reports": inactive_14_days,
        "external_matches": active_partner_sources,
        "agency_requests": pending_partner_sources,
        "outstanding_partner_requests": pending_partner_sources,
        "joint_investigations": 0,
        "predictive_alerts": stalled_cases + pending_legal_requests + unassigned_cases,
        "command_briefing": command_briefing,
        "new_alerts": new_alerts,
        "pending_legal_requests": pending_legal_requests,
        "missing_info_legal_requests": missing_info_legal_requests,
        "denied_legal_requests": denied_legal_requests,
        "approved_legal_requests": approved_legal_requests,
        "pending_partner_sources": pending_partner_sources,
        "evidence_uploaded_today": evidence_uploaded_today,
        "total_evidence": evidence_query.count(),
        "evidence_awaiting_review": len(recent_evidence),
        "restricted_access_events": restricted_access_events,
        "active_partner_sources": active_partner_sources,
        "urgent_cases": [serialize_case(case) for case in urgent_cases],
        "recent_alerts": [serialize_alert(alert) for alert in recent_alerts],
        "recent_evidence": [serialize_evidence(item) for item in recent_evidence],
        "active_bolos": [serialize_bolo(item) for item in active_bolos],
        "recent_access": [serialize_access(item) for item in recent_access],
        "recent_sightings": [serialize_sighting(item) for item in recent_sightings],
        "recent_activity": [serialize_activity(item) for item in recent_activity],
    }
