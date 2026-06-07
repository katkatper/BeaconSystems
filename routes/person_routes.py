from datetime import datetime, time
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.person import Person
from models.user import User
from security.auth import get_current_user, require_role
from schemas.person_schema import PersonCreate, PersonUpdate, PersonResponse, MessageResponse


router = APIRouter(prefix="/persons", tags=["Persons"])

PHOTO_UPLOAD_DIR = Path("uploads") / "person_photos"
PHOTO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def infer_missing_person_risk(data: dict) -> str:
    current_risk = (data.get("risk_level") or "medium").lower()
    age = data.get("age")
    risk_text = " ".join(
        str(data.get(field) or "")
        for field in [
            "description",
            "medical_conditions",
            "scars",
            "tattoos",
            "last_seen_location",
        ]
    ).lower()
    critical_terms = [
        "autism",
        "alzheimer",
        "dementia",
        "diabetic",
        "insulin",
        "medication",
        "medicine",
        "needs meds",
        "life saving",
        "lifesaving",
        "wheelchair",
        "disability",
        "disabled",
        "nonverbal",
        "cognitive",
        "developmental",
    ]
    high_terms = [
        "elderly",
        "child",
        "minor",
        "runaway",
        "pregnant",
        "injured",
        "hospital",
        "danger",
        "impaired",
        "limp",
    ]

    if age is not None and (age <= 12 or age >= 65):
        return "critical"

    if any(term in risk_text for term in critical_terms):
        return "critical"

    if age is not None and age < 18:
        return "high"

    if any(term in risk_text for term in high_terms):
        return "high" if current_risk not in {"critical"} else current_risk

    return current_risk


@router.get("/test")
def persons_test():
    return {"message": "Persons router is working"}


@router.post("/photo-upload")
def upload_person_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPEG, PNG, WEBP, or GIF image",
        )

    original_file_name = Path(file.filename or "missing-person-photo").name
    extension = Path(original_file_name).suffix.lower() or ".jpg"
    stored_file_name = f"{uuid4().hex}{extension}"
    file_path = PHOTO_UPLOAD_DIR / stored_file_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    base_url = str(request.base_url).rstrip("/")
    return {
        "message": "Photo uploaded",
        "photo_url": f"{base_url}/persons/photo/{stored_file_name}",
    }


@router.get("/photo/{file_name}")
def get_person_photo(file_name: str):
    safe_name = Path(file_name).name
    file_path = PHOTO_UPLOAD_DIR / safe_name

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Photo not found")

    return FileResponse(path=file_path)


@router.get("/", response_model=List[PersonResponse])
def get_persons(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    reported_on: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Person)

    if status:
        query = query.filter(Person.status == status)

    if risk_level:
        query = query.filter(Person.risk_level == risk_level)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Person.first_name.ilike(search),
                Person.last_name.ilike(search),
                Person.status.ilike(search),
                Person.risk_level.ilike(search),
                Person.last_seen_location.ilike(search),
                Person.medical_conditions.ilike(search),
                Person.description.ilike(search),
            )
        )

    if reported_on:
        try:
            report_day = datetime.strptime(reported_on, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="reported_on must be YYYY-MM-DD") from exc

        query = query.filter(
            Person.created_at >= datetime.combine(report_day, time.min),
            Person.created_at <= datetime.combine(report_day, time.max),
        )

    return query.order_by(Person.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{person_id}", response_model=PersonResponse)
def get_person_by_id(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return person


@router.post("/", response_model=MessageResponse)
def create_person(
    data: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    person_data = data.model_dump()
    person_data["risk_level"] = infer_missing_person_risk(person_data)
    new_person = Person(**person_data)

    db.add(new_person)
    db.commit()
    db.refresh(new_person)

    return {
        "message": "Person created",
        "person_id": new_person.person_id,
    }


@router.put("/{person_id}", response_model=MessageResponse)
def update_person(
    person_id: int,
    data: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "investigator")),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)

    return {"message": "Person updated"}


@router.delete("/{person_id}", response_model=MessageResponse)
def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    db.delete(person)
    db.commit()

    return {"message": "Person deleted"}
