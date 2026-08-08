from datetime import datetime, time
import json
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.case import Cases
from models.person import Person
from models.user import User
from security.auth import get_current_user, require_role
from schemas.person_schema import (
    MessageResponse,
    PersonCreate,
    PersonRegistrySummary,
    PersonResponse,
    PersonUpdate,
)
from services.activity_service import create_activity_log
from services.geocoding_service import geocode_address


router = APIRouter(prefix="/persons", tags=["Persons"])

PHOTO_UPLOAD_DIR = Path("uploads") / "person_photos"
PHOTO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def apply_person_agency_scope(query, current_user: User):
    """Restrict person records to cases owned by the caller's agency."""
    if current_user.role == "admin":
        return query

    return query.filter(
        Person.cases.any(Cases.agency_id == current_user.agency_id)
    )


def infer_missing_person_risk(data: dict) -> str:
    current_risk = (data.get("risk_level") or "medium").lower()
    age = data.get("age")
    housing_status = (data.get("housing_status") or "").lower()
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

    if housing_status in {"homeless", "unhoused", "transient"}:
        return "high" if current_risk != "critical" else current_risk

    if any(term in risk_text for term in high_terms):
        return "high" if current_risk not in {"critical"} else current_risk

    return current_risk


def build_missing_person_case_number(db: Session, person_id: int) -> str:
    year = datetime.utcnow().year
    base_number = f"MP-{year}-{person_id:06d}"

    if not db.query(Cases).filter(Cases.case_number == base_number).first():
        return base_number

    suffix = 2
    while db.query(Cases).filter(Cases.case_number == f"{base_number}-{suffix}").first():
        suffix += 1

    return f"{base_number}-{suffix}"


def has_coordinate_pair(latitude, longitude) -> bool:
    return latitude is not None and longitude is not None


def enrich_person_coordinates(person_data: dict) -> dict:
    address_fields = [
        ("primary_address", "primary_address_latitude", "primary_address_longitude"),
        ("school_address", "school_address_latitude", "school_address_longitude"),
        ("work_address", "work_address_latitude", "work_address_longitude"),
        ("last_seen_location", "last_seen_latitude", "last_seen_longitude"),
    ]

    for source_field, latitude_field, longitude_field in address_fields:
        if has_coordinate_pair(person_data.get(latitude_field), person_data.get(longitude_field)):
            continue

        geocoded = geocode_address(person_data.get(source_field))

        if geocoded:
            person_data[latitude_field] = geocoded["latitude"]
            person_data[longitude_field] = geocoded["longitude"]
        elif source_field in person_data:
            person_data[latitude_field] = None
            person_data[longitude_field] = None

    return person_data


def enrich_associate_coordinates(update_data: dict) -> dict:
    raw_associates = update_data.get("known_associates")

    if not raw_associates:
        return update_data

    try:
        associates = json.loads(raw_associates)
    except (TypeError, ValueError):
        return update_data

    if not isinstance(associates, list):
        return update_data

    changed = False

    for associate in associates:
        if not isinstance(associate, dict):
            continue

        if has_coordinate_pair(associate.get("latitude"), associate.get("longitude")):
            continue

        geocoded = geocode_address(associate.get("address") or associate.get("location"))

        if geocoded:
            associate["latitude"] = geocoded["latitude"]
            associate["longitude"] = geocoded["longitude"]
            changed = True

    if changed:
        update_data["known_associates"] = json.dumps(associates)

    return update_data


@router.get("/test")
def persons_test():
    return {"message": "Persons router is working"}


@router.get("/registry", response_model=List[PersonRegistrySummary])
def get_missing_person_registry(
    risk_level: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    reported_on: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = apply_person_agency_scope(
        db.query(Person).filter(Person.status == "missing"),
        current_user,
    )

    if risk_level:
        if risk_level == "high":
            query = query.filter(Person.risk_level.in_(["high", "critical"]))
        else:
            query = query.filter(Person.risk_level == risk_level)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Person.first_name.ilike(search),
                Person.last_name.ilike(search),
            )
        )

    if reported_on:
        try:
            report_day = datetime.strptime(reported_on, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="reported_on must be YYYY-MM-DD",
            ) from exc

        query = query.filter(
            Person.created_at >= datetime.combine(report_day, time.min),
            Person.created_at <= datetime.combine(report_day, time.max),
        )

    return (
        query.order_by(Person.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


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
def get_person_photo(
    file_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    safe_name = Path(file_name).name
    file_path = PHOTO_UPLOAD_DIR / safe_name

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Photo not found")

    photo_owner = apply_person_agency_scope(
        db.query(Person).filter(
            Person.photo_url.like(f"%/persons/photo/{safe_name}")
        ),
        current_user,
    ).first()

    if not photo_owner:
        raise HTTPException(status_code=404, detail="Photo not found or access denied")

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
    query = apply_person_agency_scope(db.query(Person), current_user)

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
                Person.primary_address.ilike(search),
                Person.housing_status.ilike(search),
                Person.school_name.ilike(search),
                Person.school_address.ilike(search),
                Person.employer_name.ilike(search),
                Person.work_address.ilike(search),
                Person.employment_status.ilike(search),
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
    person = apply_person_agency_scope(
        db.query(Person).filter(Person.person_id == person_id),
        current_user,
    ).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return person


@router.post("/", response_model=MessageResponse)
def create_person(
    data: PersonCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    person_data = data.model_dump()
    person_data["risk_level"] = infer_missing_person_risk(person_data)
    person_data = enrich_person_coordinates(person_data)
    new_person = Person(**person_data)

    db.add(new_person)
    db.commit()
    db.refresh(new_person)

    case_number = build_missing_person_case_number(db, new_person.person_id)
    person_name = f"{new_person.first_name} {new_person.last_name}".strip()
    new_case = Cases(
        case_number=case_number,
        title=f"Missing Person: {person_name}",
        person_id=new_person.person_id,
        agency_id=current_user.agency_id,
        investigator_id=current_user.user_id,
        last_seen_location=new_person.last_seen_location,
        priority_level=new_person.risk_level,
        description=new_person.description,
        notes="Automatically created from missing person intake.",
        case_status="open",
        date_opened=datetime.utcnow(),
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CREATE_MISSING_PERSON_CASE",
        entity="case",
        entity_id=new_case.case_id,
        details=f"Missing person intake created case {new_case.case_number} for {person_name}",
        ip_address=request.client.host if request.client else None,
    )

    return {
        "message": "Person created and case opened",
        "person_id": new_person.person_id,
        "case_id": new_case.case_id,
        "case_number": new_case.case_number,
    }


@router.put("/{person_id}", response_model=MessageResponse)
def update_person(
    person_id: int,
    data: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "investigator", "supervisor")),
):
    person = apply_person_agency_scope(
        db.query(Person).filter(Person.person_id == person_id),
        current_user,
    ).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    update_data = data.model_dump(exclude_unset=True)
    update_data = enrich_person_coordinates(update_data)
    update_data = enrich_associate_coordinates(update_data)

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
