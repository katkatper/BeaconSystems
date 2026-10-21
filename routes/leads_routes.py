from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from database.connection import get_db
from models.case import Cases
from models.leads import Leads
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import apply_related_case_access_filter, assert_case_write_access
from services.activity_service import create_activity_log
from services.clock import utc_now
from services.pagination import PaginationParams, paginate_query


router = APIRouter(prefix="/leads", tags=["Leads"])
LEAD_STATUSES = {"new", "assigned", "in_progress", "pending", "resolved", "closed"}
LEAD_PRIORITIES = {"low", "medium", "high", "critical"}


class LeadCreate(BaseModel):
    case_id: int
    lead_source: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=4000)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    priority: str = "medium"
    assigned_to_user_id: int | None = None
    due_at: datetime | None = None

    @model_validator(mode="after")
    def normalize(self):
        self.lead_source = self.lead_source.strip()
        self.description = self.description.strip()
        self.priority = self.priority.strip().lower()
        if self.priority not in LEAD_PRIORITIES:
            raise ValueError("Unsupported lead priority")
        return self


class LeadUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to_user_id: int | None = None
    due_at: datetime | None = None
    resolution: str | None = Field(default=None, max_length=4000)


def serialize_lead(lead: Leads, assignee: User | None = None):
    return {
        "lead_id": lead.lead_id,
        "case_id": lead.case_id,
        "lead_source": lead.lead_source,
        "description": lead.description,
        "confidence_score": lead.confidence_score,
        "status": lead.status,
        "priority": lead.priority,
        "assigned_to_user_id": lead.assigned_to_user_id,
        "assigned_to": assignee.username if assignee else None,
        "due_at": lead.due_at,
        "resolution": lead.resolution,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
        "closed_at": lead.closed_at,
    }


def validate_assignee(db: Session, case: Cases, user_id: int | None, current_user: User):
    if user_id is None:
        return None
    if current_user.role == "investigator" and user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Investigators may only assign leads to themselves")
    assignee = db.query(User).filter(User.user_id == user_id, User.is_active.is_(True)).first()
    if not assignee or assignee.agency_id != case.agency_id:
        raise HTTPException(status_code=400, detail="Lead assignee must be an active user in the case agency")
    return assignee


def normalize_datetime(value: datetime | None):
    if value and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


@router.get("/assignees")
def list_lead_assignees(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = assert_case_write_access(db, case_id, current_user)
    query = db.query(User).filter(
        User.agency_id == case.agency_id,
        User.is_active.is_(True),
        User.role.in_(("investigator", "supervisor", "agency_admin")),
    )
    if current_user.role == "investigator":
        query = query.filter(User.user_id == current_user.user_id)
    return [
        {"user_id": user.user_id, "username": user.username, "role": user.role}
        for user in query.order_by(User.username.asc()).all()
    ]


@router.get("/")
def list_leads(
    response: Response,
    case_id: int | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = apply_related_case_access_filter(db.query(Leads), Leads.case_id, current_user)
    if case_id is not None:
        query = query.filter(Leads.case_id == case_id)
    leads = paginate_query(
        query.order_by(Leads.created_at.desc(), Leads.lead_id.desc()),
        pagination,
        response,
        cursor_column=Leads.lead_id,
    )
    assignee_ids = {lead.assigned_to_user_id for lead in leads if lead.assigned_to_user_id}
    assignees = {
        user.user_id: user for user in db.query(User).filter(User.user_id.in_(assignee_ids)).all()
    } if assignee_ids else {}
    return [serialize_lead(lead, assignees.get(lead.assigned_to_user_id)) for lead in leads]


@router.post("/", status_code=201)
def create_lead(
    data: LeadCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    case = assert_case_write_access(db, data.case_id, current_user)
    assignee = validate_assignee(db, case, data.assigned_to_user_id, current_user)
    lead = Leads(
        case_id=data.case_id,
        lead_source=data.lead_source,
        description=data.description,
        confidence_score=data.confidence_score,
        priority=data.priority,
        assigned_to_user_id=data.assigned_to_user_id,
        due_at=normalize_datetime(data.due_at),
        status="assigned" if assignee else "new",
        updated_at=utc_now(),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    create_activity_log(
        db=db, user_id=current_user.user_id, agency_id=case.agency_id,
        action="CREATE_LEAD", entity="lead", entity_id=lead.lead_id,
        details=f"{current_user.username} created lead for case {case.case_id}",
        ip_address=request.client.host if request.client else None,
    )
    return serialize_lead(lead, assignee)


@router.put("/{lead_id}")
def update_lead(
    lead_id: int,
    data: LeadUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    lead = apply_related_case_access_filter(
        db.query(Leads).filter(Leads.lead_id == lead_id), Leads.case_id, current_user
    ).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
    case = assert_case_write_access(db, lead.case_id, current_user)
    values = data.model_dump(exclude_unset=True)
    if "status" in values:
        values["status"] = values["status"].strip().lower()
        if values["status"] not in LEAD_STATUSES:
            raise HTTPException(status_code=400, detail="Unsupported lead status")
    if "priority" in values:
        values["priority"] = values["priority"].strip().lower()
        if values["priority"] not in LEAD_PRIORITIES:
            raise HTTPException(status_code=400, detail="Unsupported lead priority")
    if "due_at" in values:
        values["due_at"] = normalize_datetime(values["due_at"])
    assignee = None
    if "assigned_to_user_id" in values:
        assignee = validate_assignee(db, case, values["assigned_to_user_id"], current_user)
        if assignee and values.get("status", lead.status) == "new":
            values["status"] = "assigned"
    next_status = values.get("status", lead.status)
    resolution = (values.get("resolution") or lead.resolution or "").strip()
    if next_status in {"resolved", "closed"} and len(resolution) < 5:
        raise HTTPException(status_code=400, detail="A resolution is required to close a lead")
    values["resolution"] = resolution or None
    values["closed_at"] = utc_now() if next_status in {"resolved", "closed"} else None
    values["updated_at"] = utc_now()
    for field, value in values.items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    if lead.assigned_to_user_id and not assignee:
        assignee = db.query(User).filter(User.user_id == lead.assigned_to_user_id).first()
    create_activity_log(
        db=db, user_id=current_user.user_id, agency_id=case.agency_id,
        action="UPDATE_LEAD", entity="lead", entity_id=lead.lead_id,
        details=f"{current_user.username} updated lead {lead.lead_id} to {lead.status}",
        ip_address=request.client.host if request.client else None,
    )
    return serialize_lead(lead, assignee)
