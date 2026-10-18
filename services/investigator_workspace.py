from sqlalchemy import case, func
from sqlalchemy.orm import Session

from models.alerts import Alerts
from models.case import Cases
from models.leads import Leads
from models.user import User


def load_investigator_workspace(db: Session, user: User, *, limit: int = 10) -> dict:
    """Return bounded personal work queues; assignment never overrides tenancy."""
    if not 1 <= limit <= 50:
        raise ValueError("Workspace limit must be between 1 and 50")
    assigned = db.query(Cases).filter(
        Cases.agency_id == user.agency_id,
        Cases.investigator_id == user.user_id,
        func.lower(func.coalesce(Cases.case_status, "open")).notin_(
            ("closed", "resolved", "archived")
        ),
    )
    case_ids = assigned.with_entities(Cases.case_id)
    priority = case(
        (func.lower(Cases.priority_level) == "critical", 0),
        (func.lower(Cases.priority_level) == "high", 1),
        else_=2,
    )
    cases = assigned.order_by(priority, Cases.updated_at.desc(), Cases.case_id.desc()).limit(limit + 1).all()
    alerts = db.query(Alerts).filter(
        Alerts.case_id.in_(case_ids),
        Alerts.recipient_agency_id == user.agency_id,
        func.lower(Alerts.alert_status) == "active",
        func.lower(Alerts.severity).in_(("high", "critical")),
    ).order_by(Alerts.created_at.desc(), Alerts.alert_id.desc()).limit(limit + 1).all()
    leads = db.query(Leads).filter(
        Leads.case_id.in_(case_ids),
        func.lower(func.coalesce(Leads.status, "new")).notin_(
            ("closed", "resolved", "rejected", "dismissed")
        ),
    ).order_by(Leads.created_at.asc(), Leads.lead_id.asc()).limit(limit + 1).all()
    return {
        "assigned_cases": [{
            "case_id": row.case_id, "case_number": row.case_number,
            "title": row.title, "priority": row.priority_level,
            "status": row.case_status, "updated_at": row.updated_at,
        } for row in cases[:limit]],
        "urgent_alerts": [{
            "alert_id": row.alert_id, "case_id": row.case_id,
            "title": row.title, "severity": row.severity,
        } for row in alerts[:limit]],
        "pending_leads": [{
            "lead_id": row.lead_id, "case_id": row.case_id,
            "status": row.status, "created_at": row.created_at,
        } for row in leads[:limit]],
        "has_more": {
            "assigned_cases": len(cases) > limit,
            "urgent_alerts": len(alerts) > limit,
            "pending_leads": len(leads) > limit,
        },
    }
