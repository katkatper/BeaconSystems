from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import hashlib
from uuid import uuid4
from datetime import datetime

from database.connection import get_db
from models.case import Cases
from models.evidence import Evidence
from models.evidence_chain import EvidenceChain
from models.user import User
from security.auth import get_current_user
from security.case_access import (
    apply_related_case_access_filter,
    assert_case_write_access as assert_authorized_case_write_access,
)
from services.activity_service import create_activity_log
from config.settings import EVIDENCE_ENCRYPTION_ENABLED, EVIDENCE_ENCRYPTION_KEY_ID
from services.geocoding_service import geocode_address
from services.pagination import PaginationParams, paginate_query

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class EvidenceCustodyEvent(BaseModel):
    action: str
    from_holder: str | None = None
    to_holder: str | None = None
    location: str | None = None
    details: str | None = None
    lab_reference: str | None = None
    available_at: datetime | None = None


CUSTODY_STATUS_BY_ACTION = {
    "COLLECTED": "collected",
    "TRANSFERRED": "transferred",
    "SUBMITTED_TO_LAB": "at_lab",
    "LAB_RECEIVED": "at_lab",
    "LAB_ANALYSIS_STARTED": "in_analysis",
    "LAB_RESULTS_RETURNED": "results_returned",
    "RETURNED_TO_AGENCY": "returned_to_agency",
    "STORED": "stored",
    "RELEASED": "released",
    "MISSING": "missing",
    "OVERDUE_REVIEW": "overdue_review",
    "AUDIT_REVIEWED": "audit_reviewed",
}


def apply_evidence_case_access(query, current_user: User, include_grants: bool = True):
    return apply_related_case_access_filter(
        query=query,
        case_id_column=Evidence.case_id,
        current_user=current_user,
        include_grants=include_grants,
    )


def get_authorized_evidence(
    db: Session,
    evidence_id: int,
    current_user: User,
    include_grants: bool = True,
):
    query = db.query(Evidence).filter(Evidence.evidence_id == evidence_id)
    evidence = apply_evidence_case_access(query, current_user, include_grants).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found or access denied")

    return evidence


def assert_case_write_access(db: Session, case_id: int, current_user: User):
    return assert_authorized_case_write_access(db, case_id, current_user)


def serialize_evidence_items(items: list[Evidence], db: Session):
    case_ids = {item.case_id for item in items if item.case_id}
    user_ids = {item.collected_by for item in items if item.collected_by}
    cases = (
        {
            case.case_id: case
            for case in db.query(Cases).filter(Cases.case_id.in_(case_ids)).all()
        }
        if case_ids
        else {}
    )
    investigator_ids = {
        case.investigator_id for case in cases.values() if case.investigator_id
    }
    user_ids.update(investigator_ids)
    users = (
        {
            user.user_id: user.username
            for user in db.query(User).filter(User.user_id.in_(user_ids)).all()
        }
        if user_ids
        else {}
    )

    return [
        {
            "evidence_id": item.evidence_id,
            "case_id": item.case_id,
            "case_number": cases.get(item.case_id).case_number if cases.get(item.case_id) else None,
            "case_title": cases.get(item.case_id).title if cases.get(item.case_id) else None,
            "assigned_investigator": users.get(cases.get(item.case_id).investigator_id) if cases.get(item.case_id) else None,
            "description": item.description,
            "evidence_type": item.evidence_type,
            "collected_by": item.collected_by,
            "collected_by_name": users.get(item.collected_by),
            "evidence_location": item.evidence_location,
            "evidence_latitude": item.evidence_latitude,
            "evidence_longitude": item.evidence_longitude,
            "geocode_provider": item.geocode_provider,
            "geocode_accuracy": item.geocode_accuracy,
            "geocode_score": item.geocode_score,
            "geocoded_address": item.geocoded_address,
            "geocoded_at": item.geocoded_at,
            "custody_status": item.custody_status,
            "current_holder": item.current_holder,
            "lab_reference": item.lab_reference,
            "available_at": item.available_at,
            "is_sensitive": item.is_sensitive,
            "is_encrypted": item.is_encrypted,
            "encryption_key_id": item.encryption_key_id,
            "content_sha256": item.content_sha256,
            "file_name": item.file_name,
            "collected_at": item.collected_at,
            "created_at": item.created_at,
        }
        for item in items
    ]


@router.get("/")
def get_all_evidence(
    case_id: int | None = None,
    request: Request = None,
    response: Response = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Evidence)
    query = apply_evidence_case_access(query, current_user)

    if case_id is not None:
        query = query.filter(Evidence.case_id == case_id)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="VIEW_EVIDENCE_LIST",
        entity="evidence",
        details=f"{current_user.username} viewed evidence list",
        ip_address=request.client.host if request and request.client else None,
    )

    items = paginate_query(
        query.order_by(Evidence.created_at.desc()),
        pagination,
        response,
    )

    return serialize_evidence_items(items, db)


@router.post("/upload")
def upload_evidence(
    case_id: int = Form(...),
    evidence_type: str = Form(...),
    description: str = Form(None),
    evidence_location: str = Form(None),
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assert_case_write_access(db, case_id, current_user)

    original_file_name = Path(file.filename or "evidence-upload").name
    stored_file_name = f"{uuid4().hex}_{original_file_name}"
    file_path = UPLOAD_DIR / stored_file_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    content_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
    geocoded_location = geocode_address(evidence_location)

    evidence = Evidence(
        case_id=case_id,
        description=description,
        evidence_type=evidence_type,
        collected_by=current_user.user_id,
        evidence_location=evidence_location,
        evidence_latitude=geocoded_location["latitude"] if geocoded_location else None,
        evidence_longitude=geocoded_location["longitude"] if geocoded_location else None,
        geocode_provider=geocoded_location.get("provider") if geocoded_location else None,
        geocode_accuracy=geocoded_location.get("accuracy") if geocoded_location else None,
        geocode_score=geocoded_location.get("score") if geocoded_location else None,
        geocoded_address=geocoded_location.get("formatted_address") if geocoded_location else None,
        geocoded_at=datetime.utcnow() if geocoded_location else None,
        current_holder=current_user.username,
        custody_status="collected",
        file_name=original_file_name,
        file_path=str(file_path),
        is_encrypted=EVIDENCE_ENCRYPTION_ENABLED,
        encryption_key_id=EVIDENCE_ENCRYPTION_KEY_ID if EVIDENCE_ENCRYPTION_ENABLED else None,
        content_sha256=content_sha256,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    chain_event = EvidenceChain(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        user_id=current_user.user_id,
        action="UPLOAD_EVIDENCE",
        to_holder=current_user.username,
        details=(
            f"Evidence uploaded: {evidence.file_name}. "
            f"SHA-256: {content_sha256}. "
            f"Encryption: {'enabled' if evidence.is_encrypted else 'not configured'}"
        ),
    )

    db.add(chain_event)
    db.commit()

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="UPLOAD_EVIDENCE",
        entity="evidence",
        entity_id=evidence.evidence_id,
        details=f"{current_user.username} uploaded evidence for case {case_id}",
        ip_address=request.client.host if request and request.client else None,
    )

    return {
        "message": "Evidence uploaded successfully",
        "evidence_id": evidence.evidence_id,
    }


@router.get("/case/{case_id}")
def get_case_evidence(
    case_id: int,
    request: Request = None,
    response: Response = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Evidence).filter(Evidence.case_id == case_id)
    query = apply_evidence_case_access(query, current_user)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="VIEW_CASE_EVIDENCE",
        entity="case",
        entity_id=case_id,
        details=f"{current_user.username} viewed evidence for case {case_id}",
        ip_address=request.client.host if request and request.client else None,
    )

    items = paginate_query(
        query.order_by(Evidence.created_at.desc()),
        pagination,
        response,
    )
    return serialize_evidence_items(items, db)


@router.get("/chain/{evidence_id}")
def get_evidence_chain(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_authorized_evidence(db, evidence_id, current_user)

    return (
        db.query(EvidenceChain)
        .filter(EvidenceChain.evidence_id == evidence_id)
        .order_by(EvidenceChain.created_at.desc())
        .all()
    )


@router.post("/{evidence_id}/custody")
def add_evidence_custody_event(
    evidence_id: int,
    data: EvidenceCustodyEvent,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = get_authorized_evidence(
        db,
        evidence_id,
        current_user,
        include_grants=False,
    )
    assert_case_write_access(db, evidence.case_id, current_user)

    action = data.action.strip().upper()

    if action not in CUSTODY_STATUS_BY_ACTION:
        raise HTTPException(status_code=400, detail="Unsupported custody action")

    from_holder = data.from_holder or evidence.current_holder or current_user.username
    to_holder = data.to_holder or evidence.current_holder or current_user.username

    chain_event = EvidenceChain(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        user_id=current_user.user_id,
        action=action,
        from_holder=from_holder,
        to_holder=to_holder,
        location=data.location,
        available_at=data.available_at,
        details=data.details,
    )

    evidence.custody_status = CUSTODY_STATUS_BY_ACTION[action]
    evidence.current_holder = to_holder
    evidence.evidence_location = data.location or evidence.evidence_location
    geocoded_location = geocode_address(data.location) if data.location else None

    if geocoded_location:
        evidence.evidence_latitude = geocoded_location["latitude"]
        evidence.evidence_longitude = geocoded_location["longitude"]
        evidence.geocode_provider = geocoded_location.get("provider")
        evidence.geocode_accuracy = geocoded_location.get("accuracy")
        evidence.geocode_score = geocoded_location.get("score")
        evidence.geocoded_address = geocoded_location.get("formatted_address")
        evidence.geocoded_at = datetime.utcnow()
    elif data.location:
        evidence.evidence_latitude = None
        evidence.evidence_longitude = None
        evidence.geocode_provider = None
        evidence.geocode_accuracy = None
        evidence.geocode_score = None
        evidence.geocoded_address = None
        evidence.geocoded_at = None

    evidence.lab_reference = data.lab_reference or evidence.lab_reference
    evidence.available_at = data.available_at or evidence.available_at

    db.add(chain_event)
    db.commit()
    db.refresh(evidence)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="UPDATE_EVIDENCE_CUSTODY",
        entity="evidence",
        entity_id=evidence.evidence_id,
        details=f"{current_user.username} recorded {action} for evidence {evidence.evidence_id}",
        ip_address=request.client.host if request and request.client else None,
    )

    return {
        "message": "Evidence custody updated",
        "evidence_id": evidence.evidence_id,
        "custody_status": evidence.custody_status,
        "current_holder": evidence.current_holder,
        "available_at": evidence.available_at,
    }


@router.get("/view/{evidence_id}")
def view_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = get_authorized_evidence(db, evidence_id, current_user)

    if evidence.is_sensitive:
        try:
            assert_authorized_case_write_access(db, evidence.case_id, current_user)
        except HTTPException:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access sensitive evidence.",
            )

    if not evidence.file_path or not Path(evidence.file_path).is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "Evidence file is missing from storage. The registry record exists, "
                "but the uploaded file is not available on disk."
            ),
        )

    chain_event = EvidenceChain(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        user_id=current_user.user_id,
        action="VIEW_EVIDENCE",
        details=f"Evidence viewed: {evidence.file_name}",
    )

    db.add(chain_event)
    db.commit()

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="VIEW_EVIDENCE_FILE",
        entity="evidence",
        entity_id=evidence.evidence_id,
        details=f"{current_user.username} opened evidence file: {evidence.file_name}",
        ip_address=request.client.host if request.client else None,
    )

    return FileResponse(
        path=evidence.file_path,
        filename=evidence.file_name,
    )


@router.put("/{evidence_id}/sensitive")
def mark_evidence_sensitive(
    evidence_id: int,
    is_sensitive: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = get_authorized_evidence(
        db,
        evidence_id,
        current_user,
        include_grants=False,
    )
    assert_case_write_access(db, evidence.case_id, current_user)

    evidence.is_sensitive = is_sensitive

    chain_event = EvidenceChain(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        user_id=current_user.user_id,
        action="MARK_EVIDENCE_SENSITIVE" if is_sensitive else "UNMARK_EVIDENCE_SENSITIVE",
        details=f"Evidence sensitivity changed: {evidence.file_name}",
    )

    db.add(chain_event)
    db.commit()
    db.refresh(evidence)

    return {
        "message": "Evidence sensitivity updated",
        "evidence_id": evidence.evidence_id,
        "is_sensitive": evidence.is_sensitive,
    }
