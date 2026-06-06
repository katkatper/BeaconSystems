from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.legal_access_request import LegalAccessRequest
from models.user import User
from security.auth import get_current_user, require_role
from services.activity_service import create_activity_log


router = APIRouter(prefix="/legal-access", tags=["Legal Access Requests"])


class LegalAccessRequestCreate(BaseModel):
    case_id: Optional[int] = None
    requester_name: str
    requester_organization: str
    requester_role: str
    contact_email: Optional[str] = None
    authority_type: str
    source_type: str
    target_identifier: Optional[str] = None
    jurisdiction: Optional[str] = None
    legal_reference: Optional[str] = None
    purpose: str
    scope_description: str
    minimization_plan: Optional[str] = None
    retention_plan: Optional[str] = None
    document_location: Optional[str] = None


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
        "warrant",
        "search_warrant",
        "subpoena",
        "court_order",
        "wiretap_order",
        "national_security_letter",
        "consent",
        "approved_api",
        "partner_integration",
    }

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

    if data.source_type not in allowed_sources:
        raise HTTPException(status_code=400, detail="Invalid source type")

    request = LegalAccessRequest(
        case_id=data.case_id,
        agency_id=current_user.agency_id,
        requested_by_user_id=current_user.user_id,
        requester_name=data.requester_name,
        requester_organization=data.requester_organization,
        requester_role=data.requester_role,
        contact_email=data.contact_email,
        authority_type=data.authority_type,
        source_type=data.source_type,
        target_identifier=data.target_identifier,
        jurisdiction=data.jurisdiction,
        legal_reference=data.legal_reference,
        purpose=data.purpose,
        scope_description=data.scope_description,
        minimization_plan=data.minimization_plan,
        retention_plan=data.retention_plan,
        document_location=data.document_location,
        status="pending",
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
            f"{data.source_type} data"
        ),
    )

    return request


@router.get("/")
def get_legal_access_requests(
    status: Optional[str] = Query(None),
    case_id: Optional[int] = Query(None),
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

    return query.order_by(LegalAccessRequest.requested_at.desc()).all()


@router.put("/{request_id}/review")
def review_legal_access_request(
    request_id: int,
    data: LegalAccessReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    allowed_statuses = {"pending", "approved", "denied", "missing_info", "expired", "revoked"}

    if data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid request status")

    request = db.query(LegalAccessRequest).filter(
        LegalAccessRequest.request_id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Legal access request not found")

    if current_user.role != "admin" and request.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    request.status = data.status
    request.review_notes = data.review_notes
    request.reviewed_by_user_id = current_user.user_id
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

    return request
