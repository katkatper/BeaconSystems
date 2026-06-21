from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database.connection import get_db
from models.agency_exchange import AgencyExchange
from models.case import Cases
from models.user import User
from security.auth import require_role
from security.case_access import accessible_case_ids
from services.activity_service import create_activity_log


router = APIRouter(prefix="/agency-exchanges", tags=["Agency Exchanges"])

AGENCY_EXCHANGE_STATUSES = {
    "draft",
    "submitted",
    "under_review",
    "additional_information_requested",
    "approved",
    "denied",
    "fulfilled",
    "closed",
}


class AgencyExchangeCreate(BaseModel):
    case_id: int
    from_agency: str
    to_agency: str
    information_type: str
    summary: str
    reason: str
    legal_authority: str | None = None
    requesting_officer: str | None = None
    badge_number: str | None = None
    subject: str | None = None
    request_type: str | None = None
    priority: str | None = "routine"
    due_date: datetime | None = None
    delivery_method: str | None = None
    requested_records: str | None = None
    attachments: str | None = None
    assigned_to: str | None = None
    status: str | None = None


class AgencyExchangeStatusUpdate(BaseModel):
    status: str
    assigned_to: str | None = None
    audit_note: str | None = None


@router.get("/")
def list_agency_exchanges(
    case_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    query = db.query(AgencyExchange)

    if case_id is not None:
        query = query.filter(AgencyExchange.case_id == case_id)

    if current_user.role in {"agency_admin", "supervisor"}:
        query = (
            query
            .join(Cases, AgencyExchange.case_id == Cases.case_id)
            .filter(Cases.agency_id == current_user.agency_id)
        )

    if current_user.role == "investigator":
        allowed_case_ids = set(accessible_case_ids(db, current_user))

        if not allowed_case_ids:
            return []

        if case_id is not None and case_id not in allowed_case_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this case exchange log")

        query = query.filter(AgencyExchange.case_id.in_(allowed_case_ids))

    return query.order_by(AgencyExchange.created_at.desc()).limit(50).all()


@router.post("/")
def create_agency_exchange(
    data: AgencyExchangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    case = db.query(Cases).filter(Cases.case_id == data.case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if current_user.role != "admin" and case.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Cannot create request for another agency")

    if data.status:
        status_value = data.status
    elif current_user.role in {"admin", "agency_admin", "supervisor"}:
        status_value = "approved"
    else:
        status_value = "submitted"

    if status_value not in AGENCY_EXCHANGE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid agency request status")

    submitted_at = datetime.utcnow() if status_value != "draft" else None
    audit_log = f"{datetime.utcnow().isoformat()}Z - Created by {current_user.username} with status {status_value}."

    exchange = AgencyExchange(
        case_id=data.case_id,
        from_agency=data.from_agency,
        to_agency=data.to_agency,
        requesting_officer=data.requesting_officer,
        badge_number=data.badge_number,
        subject=data.subject,
        request_type=data.request_type or data.information_type,
        information_type=data.information_type,
        summary=data.summary,
        reason=data.reason,
        legal_authority=data.legal_authority,
        priority=data.priority or "routine",
        due_date=data.due_date,
        delivery_method=data.delivery_method,
        requested_records=data.requested_records,
        attachments=data.attachments,
        assigned_to=data.assigned_to,
        requested_by=current_user.user_id,
        approved_by=current_user.user_id,
        audit_log=audit_log,
        submitted_at=submitted_at,
        status=status_value,
    )

    db.add(exchange)
    db.commit()
    db.refresh(exchange)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="AGENCY_INFORMATION_REQUEST_CREATED",
        entity="case",
        entity_id=data.case_id,
        details=(
            f"Created agency request from {data.from_agency} to {data.to_agency}. "
            f"Reason: {data.reason}"
        ),
    )

    return {
        "message": "Agency information exchange recorded",
        "exchange_id": exchange.exchange_id,
        "case_id": exchange.case_id,
        "approved_by": exchange.approved_by,
    }


@router.put("/{exchange_id}/status")
def update_agency_exchange_status(
    exchange_id: int,
    data: AgencyExchangeStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    if data.status not in AGENCY_EXCHANGE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid agency request status")

    exchange = db.query(AgencyExchange).filter(AgencyExchange.exchange_id == exchange_id).first()

    if not exchange:
        raise HTTPException(status_code=404, detail="Agency request not found")

    case = db.query(Cases).filter(Cases.case_id == exchange.case_id).first()

    if current_user.role != "admin" and case and case.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Cannot update another agency request")

    old_status = exchange.status
    exchange.status = data.status

    if data.assigned_to is not None:
        exchange.assigned_to = data.assigned_to

    if data.status == "fulfilled":
        exchange.fulfilled_at = datetime.utcnow()

    audit_note = data.audit_note or f"Status changed from {old_status} to {data.status}"
    new_audit_line = f"{datetime.utcnow().isoformat()}Z - {current_user.username}: {audit_note}"
    exchange.audit_log = f"{exchange.audit_log or ''}\n{new_audit_line}".strip()

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="AGENCY_INFORMATION_REQUEST_STATUS_UPDATE",
        entity="case",
        entity_id=exchange.case_id,
        details=f"Agency request {exchange.exchange_id} moved from {old_status} to {data.status}",
    )

    db.commit()
    db.refresh(exchange)

    return exchange
