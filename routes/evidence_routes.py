from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from database.connection import get_db
from models.case import Cases
from models.evidence import Evidence
from models.evidence_chain import EvidenceChain
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import (
    apply_related_case_access_filter,
)
from security.case_access import (
    assert_case_write_access as assert_authorized_case_write_access,
)
from services.activity_service import create_activity_log
from services.clock import utc_now
from services.evidence_retention import retention_decision
from services.geocoding_service import geocode_address
from services.malware_scanner import scan_upload
from services.object_storage import object_storage
from services.pagination import PaginationParams, paginate_query
from services.upload_validation import validate_upload

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)

class EvidenceCustodyEvent(BaseModel):
    action: str
    from_holder: str | None = None
    to_holder: str | None = None
    location: str | None = None
    details: str | None = None
    lab_reference: str | None = None
    available_at: datetime | None = None


class EvidenceRetentionUpdate(BaseModel):
    retention_policy_code: str = Field(min_length=2, max_length=100)
    retention_until: datetime | None = None
    legal_hold: bool
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def validate_retention(self):
        self.retention_policy_code = self.retention_policy_code.strip()
        self.reason = self.reason.strip()
        if not self.retention_policy_code or not self.reason:
            raise ValueError("Retention policy and reason are required")
        return self


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

EVIDENCE_TYPES = {
    "biological",
    "digital",
    "document",
    "physical",
    "photo_video",
    "trace",
    "vehicle",
    "other",
}

UPLOAD_RETENTION_POLICIES = {
    "agency-standard",
    "major-case",
    "juvenile-case",
    "permanent",
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
            "retention_policy_code": item.retention_policy_code,
            "retention_until": item.retention_until,
            "legal_hold": item.legal_hold,
            "legal_hold_reason": item.legal_hold_reason,
            "legal_hold_set_at": item.legal_hold_set_at,
            "disposition_status": item.disposition_status,
            "disposition_eligible": retention_decision(item).eligible,
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
        query.order_by(Evidence.created_at.desc(), Evidence.evidence_id.desc()),
        pagination,
        response,
        cursor_column=Evidence.evidence_id,
    )

    return serialize_evidence_items(items, db)


@router.post("/upload")
def upload_evidence(
    case_id: int = Form(...),
    evidence_type: str = Form(..., min_length=2, max_length=100),
    description: str = Form(None),
    evidence_location: str = Form(None),
    collected_at: datetime | None = Form(None),
    is_sensitive: bool = Form(False),
    retention_policy_code: str = Form("agency-standard"),
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = assert_case_write_access(db, case_id, current_user)

    normalized_type = evidence_type.strip().lower()
    normalized_retention = retention_policy_code.strip().lower()
    if normalized_type not in EVIDENCE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported evidence type")
    if normalized_retention not in UPLOAD_RETENTION_POLICIES:
        raise HTTPException(status_code=400, detail="Unsupported retention policy")
    if collected_at and collected_at.tzinfo is not None:
        collected_at = collected_at.astimezone(timezone.utc).replace(tzinfo=None)
    if collected_at and collected_at > utc_now():
        raise HTTPException(status_code=400, detail="Collection time cannot be in the future")

    original_file_name = Path(file.filename or "evidence-upload").name
    validate_upload(
        file.file,
        file_name=original_file_name,
        content_type=file.content_type,
    )
    scan_result = scan_upload(file.file)
    agency_id = case.agency_id or current_user.agency_id
    if not agency_id:
        raise HTTPException(status_code=400, detail="Evidence requires an owning agency")
    storage_key = object_storage.create_key(agency_id, "evidence", original_file_name)
    stored = object_storage.put(file.file, storage_key, file.content_type)
    content_sha256 = stored.sha256
    geocoded_location = geocode_address(evidence_location)

    evidence = Evidence(
        case_id=case_id,
        description=description,
        evidence_type=normalized_type,
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
        collected_at=collected_at or utc_now(),
        is_sensitive=is_sensitive,
        retention_policy_code=normalized_retention,
        file_name=original_file_name,
        file_path=stored.key,
        is_encrypted=object_storage.is_encrypted,
        encryption_key_id=object_storage.encryption_key_id,
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
            f"Malware scan: {scan_result.status}. "
            f"Encryption: {'enabled' if evidence.is_encrypted else 'not configured'}. "
            f"Classification: {normalized_type}; retention: {normalized_retention}; "
            f"sensitive: {is_sensitive}"
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
        query.order_by(Evidence.created_at.desc(), Evidence.evidence_id.desc()),
        pagination,
        response,
        cursor_column=Evidence.evidence_id,
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

    if not evidence.file_path:
        raise HTTPException(
            status_code=404,
            detail="Evidence file is missing from storage.",
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

    if object_storage.backend == "s3":
        return RedirectResponse(
            object_storage.signed_url(evidence.file_path, evidence.file_name),
            status_code=307,
        )

    storage_path = object_storage.local_path(evidence.file_path)
    if not storage_path.is_file():
        # Backward compatibility for evidence uploaded before tenant-scoped storage.
        legacy_path = Path(evidence.file_path)
        if not legacy_path.is_file():
            raise HTTPException(status_code=404, detail="Evidence file is missing from storage")
        storage_path = legacy_path

    return FileResponse(path=storage_path, filename=evidence.file_name)


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


@router.put("/{evidence_id}/retention")
def update_evidence_retention(
    evidence_id: int,
    data: EvidenceRetentionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    evidence = get_authorized_evidence(
        db,
        evidence_id,
        current_user,
        include_grants=False,
    )
    assert_case_write_access(db, evidence.case_id, current_user)

    if data.retention_until and data.retention_until.tzinfo is not None:
        retention_until = data.retention_until.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        retention_until = data.retention_until

    was_on_legal_hold = evidence.legal_hold
    evidence.retention_policy_code = data.retention_policy_code
    evidence.retention_until = retention_until
    evidence.legal_hold = data.legal_hold
    evidence.legal_hold_reason = data.reason if data.legal_hold else None
    evidence.legal_hold_set_at = utc_now() if data.legal_hold else None
    evidence.legal_hold_set_by = current_user.user_id if data.legal_hold else None

    if data.legal_hold:
        action = "PLACE_LEGAL_HOLD"
    elif was_on_legal_hold:
        action = "RELEASE_LEGAL_HOLD"
    else:
        action = "UPDATE_RETENTION_POLICY"
    chain_event = EvidenceChain(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        user_id=current_user.user_id,
        action=action,
        details=(
            f"Retention policy {data.retention_policy_code}; "
            f"retention until {retention_until.isoformat() if retention_until else 'indefinite'}; "
            f"reason: {data.reason}"
        ),
    )
    db.add(chain_event)
    db.commit()
    db.refresh(evidence)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action=action,
        entity="evidence",
        entity_id=evidence.evidence_id,
        details=f"{current_user.username} changed evidence retention controls",
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": "Evidence retention controls updated",
        "evidence_id": evidence.evidence_id,
        "retention_policy_code": evidence.retention_policy_code,
        "retention_until": evidence.retention_until,
        "legal_hold": evidence.legal_hold,
        "disposition_eligible": retention_decision(evidence).eligible,
    }
