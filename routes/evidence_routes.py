from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from uuid import uuid4

from database.connection import get_db
from models.evidence import Evidence
from models.evidence_chain import EvidenceChain
from models.user import User
from security.auth import get_current_user
from security.case_access import (
    apply_related_case_access_filter,
    assert_case_write_access as assert_authorized_case_write_access,
)
from services.activity_service import create_activity_log

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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


@router.get("/")
def get_all_evidence(
    case_id: int | None = None,
    request: Request = None,
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

    return query.order_by(Evidence.created_at.desc()).all()


@router.post("/upload")
def upload_evidence(
    case_id: int = Form(...),
    evidence_type: str = Form(...),
    description: str = Form(None),
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

    evidence = Evidence(
        case_id=case_id,
        description=description,
        evidence_type=evidence_type,
        collected_by=current_user.user_id,
        file_name=original_file_name,
        file_path=str(file_path),
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    chain_event = EvidenceChain(
        evidence_id=evidence.evidence_id,
        case_id=evidence.case_id,
        user_id=current_user.user_id,
        action="UPLOAD_EVIDENCE",
        details=f"Evidence uploaded: {evidence.file_name}",
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

    return query.all()


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
        raise HTTPException(status_code=404, detail="Evidence file is missing")

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
