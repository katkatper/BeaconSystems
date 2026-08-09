from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from fastapi import Response
from sqlalchemy.orm import Session

from database.connection import get_db
from models.activity_log import ActivityLog
from models.case import Cases
from models.legal_access_request import LegalAccessRequest
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import apply_case_access_filter, get_authorized_case
from services.activity_service import create_activity_log
from services.pagination import PaginationParams, paginate_query


router = APIRouter(prefix="/legal-access", tags=["Legal Access Requests"])


def serialize_legal_request(request: LegalAccessRequest, db: Session):
    case_number = None
    if request.case_id:
        case_number = db.query(Cases.case_number).filter(
            Cases.case_id == request.case_id
        ).scalar()

    return {
        "request_id": request.request_id,
        "request_type": request.request_type,
        "authority_type": request.authority_type,
        "case_id": request.case_id,
        "case_number": case_number,
        "person_id": request.person_id,
        "agency_id": request.agency_id,
        "requested_by_user_id": request.requested_by_user_id,
        "assigned_investigator_id": request.assigned_investigator_id,
        "approved_by_user_id": request.approved_by_user_id,
        "reviewed_by_user_id": request.reviewed_by_user_id,
        "requester_name": request.requester_name,
        "requester_organization": request.requester_organization,
        "requester_role": request.requester_role,
        "contact_email": request.contact_email,
        "source_type": request.source_type,
        "receiving_entity": request.receiving_entity,
        "target_identifier": request.target_identifier,
        "jurisdiction": request.jurisdiction,
        "legal_reference": request.legal_reference,
        "purpose": request.purpose,
        "reason_for_request": request.reason_for_request,
        "scope_description": request.scope_description,
        "probable_cause_summary": request.probable_cause_summary,
        "minimization_plan": request.minimization_plan,
        "retention_plan": request.retention_plan,
        "document_location": request.document_location,
        "attachments": request.attachments,
        "status": request.status,
        "priority": request.priority,
        "review_notes": request.review_notes,
        "requested_at": request.requested_at,
        "due_date": request.due_date,
        "reviewed_at": request.reviewed_at,
    }


def get_accessible_legal_request(
    request_id: int,
    db: Session,
    current_user: User,
):
    request = db.query(LegalAccessRequest).filter(
        LegalAccessRequest.request_id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Legal request not found")

    if current_user.role != "admin" and request.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return request


class LegalAccessRequestCreate(BaseModel):
    case_id: Optional[int] = None
    case_number: Optional[str] = None
    person_id: Optional[int] = None
    assigned_investigator_id: Optional[int] = None
    approved_by_user_id: Optional[int] = None
    requester_name: str
    requester_organization: str
    requester_role: str
    contact_email: Optional[str] = None
    authority_type: str
    request_type: Optional[str] = None
    source_type: str
    receiving_entity: Optional[str] = None
    target_identifier: Optional[str] = None
    jurisdiction: Optional[str] = None
    legal_reference: Optional[str] = None
    purpose: str
    reason_for_request: Optional[str] = None
    scope_description: str
    probable_cause_summary: Optional[str] = None
    minimization_plan: Optional[str] = None
    retention_plan: Optional[str] = None
    document_location: Optional[str] = None
    attachments: Optional[str] = None
    priority: Optional[str] = "routine"
    due_date: Optional[datetime] = None
    status: Optional[str] = "draft"


class LegalAccessReview(BaseModel):
    status: str
    review_notes: Optional[str] = None


@router.post("/")
def create_legal_access_request(
    data: LegalAccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_authorities = {
        "agency_agreement",
        "interagency_request",
        "da_prosecutor_request",
        "warrant",
        "search_warrant",
        "subpoena",
        "court_order",
        "records_request",
        "preservation_request",
        "wiretap_order",
        "national_security_letter",
        "consent",
        "approved_api",
        "partner_integration",
    }

    allowed_statuses = {
        "draft",
        "submitted_for_supervisor_review",
        "returned_for_edits",
        "approved_by_supervisor",
        "sent_to_da",
        "sent_to_court",
        "sent",
        "awaiting_response",
        "signed_approved",
        "denied",
        "served",
        "completed",
        "closed",
        "pending",
        "approved",
        "missing_info",
        "expired",
        "revoked",
    }

    allowed_priorities = {"routine", "medium", "high", "urgent", "critical"}
    allowed_template_categories = {
        "judicial",
        "prosecutor",
        "emergency",
        "records",
        "interagency",
        "forensics",
        "evidence",
        "medical_examiner",
        "missing_persons",
        "healthcare",
        "social_services",
    }
    request_type = data.request_type or data.authority_type
    status_value = data.status or "draft"
    priority_value = data.priority or "routine"

    allowed_sources = {
        "hospital",
        "transportation",
        "camera",
        "toll",
        "cell_provider",
        "communications",
        "social_media",
        "coroner",
        "genealogy",
        "missing_persons_organization",
        "other",
    }

    if data.authority_type not in allowed_authorities:
        raise HTTPException(status_code=400, detail="Invalid authority type")

    is_configured_template = any(
        request_type.startswith(f"{category}__")
        for category in allowed_template_categories
    )

    if request_type not in allowed_authorities and not is_configured_template:
        raise HTTPException(status_code=400, detail="Invalid request type")

    if data.source_type not in allowed_sources:
        raise HTTPException(status_code=400, detail="Invalid source type")

    if status_value not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid request status")

    if priority_value not in allowed_priorities:
        raise HTTPException(status_code=400, detail="Invalid priority")

    linked_case = None
    submitted_case_number = (data.case_number or "").strip()

    if submitted_case_number:
        case_query = db.query(Cases).filter(Cases.case_number == submitted_case_number)
        linked_case = apply_case_access_filter(case_query, current_user).first()
        if not linked_case:
            raise HTTPException(status_code=404, detail="Case number not found or access denied")

        if data.case_id is not None and data.case_id != linked_case.case_id:
            raise HTTPException(status_code=400, detail="Case ID and case number do not match")
    elif data.case_id is not None:
        linked_case = get_authorized_case(db, data.case_id, current_user)

    request = LegalAccessRequest(
        case_id=linked_case.case_id if linked_case else None,
        person_id=data.person_id,
        agency_id=current_user.agency_id,
        requested_by_user_id=current_user.user_id,
        assigned_investigator_id=data.assigned_investigator_id,
        approved_by_user_id=data.approved_by_user_id,
        requester_name=data.requester_name,
        requester_organization=data.requester_organization,
        requester_role=data.requester_role,
        contact_email=data.contact_email,
        authority_type=data.authority_type,
        request_type=request_type,
        source_type=data.source_type,
        receiving_entity=data.receiving_entity or data.requester_organization,
        target_identifier=data.target_identifier,
        jurisdiction=data.jurisdiction,
        legal_reference=data.legal_reference,
        purpose=data.purpose,
        reason_for_request=data.reason_for_request or data.purpose,
        scope_description=data.scope_description,
        probable_cause_summary=data.probable_cause_summary or data.scope_description,
        minimization_plan=data.minimization_plan,
        retention_plan=data.retention_plan,
        document_location=data.document_location,
        attachments=data.attachments or data.document_location,
        priority=priority_value,
        due_date=data.due_date,
        status=status_value,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CREATE_LEGAL_ACCESS_REQUEST",
        entity="legal_access_request",
        entity_id=request.request_id,
        details=(
            f"{data.authority_type} request submitted for "
            f"{data.source_type} data with status {status_value}"
        ),
    )

    return serialize_legal_request(request, db)


@router.get("/")
def get_legal_access_requests(
    response: Response,
    status: Optional[str] = Query(None),
    case_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LegalAccessRequest)

    if current_user.role != "admin":
        query = query.filter(LegalAccessRequest.agency_id == current_user.agency_id)

    if status:
        query = query.filter(LegalAccessRequest.status == status)

    if case_id is not None:
        query = query.filter(LegalAccessRequest.case_id == case_id)

    requests = paginate_query(
        query.order_by(LegalAccessRequest.requested_at.desc()),
        pagination,
        response,
    )
    return [serialize_legal_request(request, db) for request in requests]


@router.get("/{request_id}")
def get_legal_access_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = get_accessible_legal_request(request_id, db, current_user)
    user_ids = {
        value
        for value in [
            request.requested_by_user_id,
            request.assigned_investigator_id,
            request.approved_by_user_id,
            request.reviewed_by_user_id,
        ]
        if value
    }
    users = (
        {
            user.user_id: user.username
            for user in db.query(User).filter(User.user_id.in_(user_ids)).all()
        }
        if user_ids
        else {}
    )
    audit_logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.entity == "legal_access_request",
            ActivityLog.entity_id == request_id,
        )
        .order_by(ActivityLog.timestamp.desc())
        .limit(25)
        .all()
    )

    data = serialize_legal_request(request, db)
    data.update({
        "requested_by_name": users.get(request.requested_by_user_id),
        "assigned_investigator_name": users.get(request.assigned_investigator_id),
        "approved_by_name": users.get(request.approved_by_user_id),
        "reviewed_by_name": users.get(request.reviewed_by_user_id),
        "audit_log": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "details": log.details,
                "timestamp": log.timestamp,
            }
            for log in audit_logs
        ],
    })

    return data


@router.put("/{request_id}/review")
def review_legal_access_request(
    request_id: int,
    data: LegalAccessReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    allowed_statuses = {
        "draft",
        "submitted_for_supervisor_review",
        "returned_for_edits",
        "approved_by_supervisor",
        "sent_to_da",
        "sent_to_court",
        "sent",
        "awaiting_response",
        "signed_approved",
        "denied",
        "served",
        "completed",
        "closed",
        "pending",
        "approved",
        "missing_info",
        "expired",
        "revoked",
    }

    if data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid request status")

    request = get_accessible_legal_request(request_id, db, current_user)

    request.status = data.status
    request.review_notes = data.review_notes
    request.reviewed_by_user_id = current_user.user_id
    if data.status in {"approved_by_supervisor", "signed_approved", "approved"}:
        request.approved_by_user_id = current_user.user_id
    request.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(request)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="REVIEW_LEGAL_ACCESS_REQUEST",
        entity="legal_access_request",
        entity_id=request.request_id,
        details=f"Legal access request {request.request_id} marked {data.status}",
    )

    return serialize_legal_request(request, db)
