from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil

from database.connection import get_db
from models.evidence import Evidence
from models.evidence_chain import EvidenceChain
from models.user import User
from models.case import Cases
from security.auth import get_current_user

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
def upload_evidence(
    case_id: int = Form(...),
    evidence_type: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    evidence = Evidence(
        case_id=case_id,
        description=description,
        evidence_type=evidence_type,
        collected_by=current_user.user_id,
        file_name=file.filename,
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

    return {
        "message": "Evidence uploaded successfully",
        "evidence_id": evidence.evidence_id,
    }


@router.get("/case/{case_id}")
def get_case_evidence(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Evidence).filter(Evidence.case_id == case_id).all()


@router.get("/chain/{evidence_id}")
def get_evidence_chain(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(EvidenceChain)
        .filter(EvidenceChain.evidence_id == evidence_id)
        .order_by(EvidenceChain.created_at.desc())
        .all()
    )


@router.get("/view/{evidence_id}")
def view_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evidence = db.query(Evidence).filter(
        Evidence.evidence_id == evidence_id
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if evidence.is_sensitive:
        case = db.query(Cases).filter(
            Cases.case_id == evidence.case_id
        ).first()

        allowed_roles = ["admin", "agency_admin"]

        is_assigned_investigator = (
            case and case.investigator_id == current_user.user_id
        )

        if current_user.role not in allowed_roles and not is_assigned_investigator:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access sensitive evidence.",
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
    evidence = db.query(Evidence).filter(
        Evidence.evidence_id == evidence_id
    ).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

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
