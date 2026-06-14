from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    EVIDENCE_ENCRYPTION_ENABLED,
    EVIDENCE_ENCRYPTION_KEY_ID,
    SPLUNK_HEC_TOKEN,
    SPLUNK_HEC_URL,
)
from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.activity_log import ActivityLog
from models.agency_exchange import AgencyExchange
from models.case import Cases
from models.case_access_grant import CaseAccessGrant
from models.evidence import Evidence
from models.evidence_chain import EvidenceChain
from models.user import User
from security.auth import require_role


router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/posture")
def get_security_posture(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    since_24h = datetime.utcnow() - timedelta(hours=24)

    user_query = db.query(User)
    activity_query = db.query(ActivityLog)
    access_query = db.query(CaseAccessGrant)

    if current_user.role != "admin":
        user_query = user_query.filter(User.agency_id == current_user.agency_id)
        activity_query = activity_query.filter(ActivityLog.agency_id == current_user.agency_id)
        access_query = access_query.filter(CaseAccessGrant.agency_id == current_user.agency_id)

    total_users = user_query.count()
    active_users = user_query.filter(User.is_active == True).count()  # noqa: E712
    mfa_enabled_users = user_query.filter(User.mfa_enabled == True).count()  # noqa: E712
    roles_present = [
        role
        for role, in (
            user_query
            .with_entities(User.role)
            .filter(User.role != None)  # noqa: E711
            .distinct()
            .order_by(User.role.asc())
            .all()
        )
    ]

    evidence_query = db.query(Evidence)
    chain_query = db.query(EvidenceChain)

    if current_user.role != "admin":
        agency_case_ids = [
            case_id
            for case_id, in (
                db.query(Cases.case_id)
                .filter(Cases.agency_id == current_user.agency_id)
                .distinct()
                .all()
            )
        ]
        evidence_query = evidence_query.filter(Evidence.case_id.in_(agency_case_ids or [-1]))
        chain_query = chain_query.filter(EvidenceChain.case_id.in_(agency_case_ids or [-1]))

    total_evidence = evidence_query.count()
    encrypted_evidence = evidence_query.filter(Evidence.is_encrypted == True).count()  # noqa: E712
    sensitive_evidence = evidence_query.filter(Evidence.is_sensitive == True).count()  # noqa: E712
    chain_events = chain_query.count()

    splunk_configured = bool(SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN)
    recent_security_events = (
        activity_query
        .filter(
            ActivityLog.action.in_([
                "LOGIN",
                "PASSWORD_CHANGE",
                "ROLE_UPDATE",
                "DEACTIVATE_USER",
                "ACTIVATE_USER",
                "VIEW_EVIDENCE",
                "UPLOAD_EVIDENCE",
                "UPDATE_EVIDENCE_CUSTODY",
                "AGENCY_INFORMATION_EXCHANGE_APPROVED",
            ])
        )
        .order_by(ActivityLog.timestamp.desc())
        .limit(10)
        .all()
    )

    return {
        "controls": [
            {
                "key": "mfa",
                "label": "MFA",
                "status": "attention" if mfa_enabled_users < active_users else "active",
                "summary": f"{mfa_enabled_users} of {active_users} active users have MFA enabled.",
                "metric": mfa_enabled_users,
                "total": active_users,
            },
            {
                "key": "audit_logging",
                "label": "Enhanced audit logging",
                "status": "active",
                "summary": f"{activity_query.filter(ActivityLog.timestamp >= since_24h).count()} auditable events in the last 24 hours.",
                "metric": activity_query.count(),
            },
            {
                "key": "rbac",
                "label": "RBAC by agency and role",
                "status": "active" if roles_present else "attention",
                "summary": f"{len(roles_present)} roles active across {total_users} scoped users.",
                "metric": len(roles_present),
                "roles": roles_present,
            },
            {
                "key": "evidence_encryption",
                "label": "Evidence encryption",
                "status": "active" if EVIDENCE_ENCRYPTION_ENABLED else "attention",
                "summary": f"{encrypted_evidence} of {total_evidence} evidence records marked encrypted.",
                "metric": encrypted_evidence,
                "total": total_evidence,
                "key_id": EVIDENCE_ENCRYPTION_KEY_ID if EVIDENCE_ENCRYPTION_ENABLED else None,
                "sensitive_evidence": sensitive_evidence,
            },
            {
                "key": "session_timeout",
                "label": "Session timeout",
                "status": "active" if ACCESS_TOKEN_EXPIRE_MINUTES <= 60 else "attention",
                "summary": f"Access tokens expire after {ACCESS_TOKEN_EXPIRE_MINUTES} minutes.",
                "metric": ACCESS_TOKEN_EXPIRE_MINUTES,
            },
            {
                "key": "sharing_approvals",
                "label": "Inter-agency sharing approvals",
                "status": "active",
                "summary": f"{db.query(AgencyExchange).count()} approved agency exchanges and {access_query.filter(CaseAccessGrant.status == 'pending').count()} pending access reviews.",
                "metric": db.query(AgencyExchange).count(),
            },
            {
                "key": "security_dashboard",
                "label": "Security dashboard",
                "status": "active",
                "summary": "Security posture, access reviews, audit trails, and evidence custody are visible in Beacon.",
                "metric": len(recent_security_events),
            },
            {
                "key": "splunk",
                "label": "Splunk integration",
                "status": "active" if splunk_configured else "attention",
                "summary": "Splunk HEC endpoint configured." if splunk_configured else "Set SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN to enable export.",
                "metric": 1 if splunk_configured else 0,
            },
        ],
        "recent_security_events": recent_security_events,
        "transparency": {
            "audit_events_total": activity_query.count(),
            "evidence_chain_events": chain_events,
            "pending_partner_approvals": db.query(IntegrationSource).filter(IntegrationSource.status == "pending").count(),
            "restricted_access_pending": access_query.filter(CaseAccessGrant.status == "pending").count(),
        },
    }
