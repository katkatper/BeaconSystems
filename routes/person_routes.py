import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi import Response
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.case import Cases
from models.person import Person
from models.user import User
from security.auth import get_current_user, require_role
from security.tenant_scope import apply_person_agency_scope
from schemas.person_schema import (
    MessageResponse,
    PersonCreate,
    PersonRegistrySummary,
    PersonResponse,
    PersonUpdate,
)
from services.activity_service import create_activity_log
from services.case_numbering import (
    missing_person_case_prefix,
    select_missing_person_case_number,
)
from services.clock import utc_now
from services.geocoding_service import geocode_address
from services.pagination import paginate_query_values
from services.object_storage import object_storage
from services.person_filters import apply_person_query_filters
from services.person_risk import infer_missing_person_risk
from services.upload_validation import validate_upload
from services.malware_scanner import scan_upload


router = APIRouter(prefix="/persons", tags=["Persons"])

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
REGISTRY_SEARCH_COLUMNS = (Person.first_name, Person.last_name)
INTERNAL_PERSON_SEARCH_COLUMNS = (
    Person.first_name,
    Person.last_name,
    Person.status,
    Person.risk_level,
    Person.last_seen_location,
    Person.primary_address,
    Person.housing_status,
    Person.school_name,
    Person.school_address,
    Person.employer_name,
    Person.work_address,
    Person.employment_status,
    Person.medical_conditions,
    Person.description,
)


def apply_person_collection_filters(query, *, q, reported_on, search_columns):
    try:
        return apply_person_query_filters(
            query,
            search_text=q,
            search_columns=search_columns,
            reported_on=reported_on,
            created_at_column=Person.created_at,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="reported_on must be YYYY-MM-DD",
        ) from exc


def build_missing_person_case_number(db: Session, person_id: int) -> str:
    opened_at = utc_now()
    base_number = missing_person_case_prefix(person_id, opened_at)
    matching_rows = (
        db.query(Cases.case_number)
        .filter(Cases.case_number.like(f"{base_number}%"))
        .all()
    )
    return select_missing_person_case_number(
        person_id,
        (case_number for (case_number,) in matching_rows),
        opened_at,
    )


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
    response: Response,
    risk_level: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    reported_on: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
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

    query = apply_person_collection_filters(
        query,
        q=q,
        reported_on=reported_on,
        search_columns=REGISTRY_SEARCH_COLUMNS,
    )

    return paginate_query_values(
        query.order_by(Person.created_at.desc()),
        limit=limit,
        offset=offset,
        response=response,
    )


@router.post("/photo-upload")
def upload_person_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    original_file_name = Path(file.filename or "missing-person-photo").name
    validate_upload(
        file.file,
        file_name=original_file_name,
        content_type=file.content_type,
        allowed_content_types=ALLOWED_PHOTO_TYPES,
    )
    scan_upload(file.file)
    if not current_user.agency_id:
        raise HTTPException(status_code=400, detail="Photo upload requires an owning agency")
    storage_key = object_storage.create_key(
        current_user.agency_id,
        "person-photos",
        original_file_name,
    )
    object_storage.put(file.file, storage_key, file.content_type)

    base_url = str(request.base_url).rstrip("/")
    return {
        "message": "Photo uploaded",
        "photo_url": f"{base_url}/persons/photo/{storage_key}",
    }


@router.get("/photo/{storage_key:path}")
def get_person_photo(
    storage_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    photo_owner = apply_person_agency_scope(
        db.query(Person).filter(
            Person.photo_url.like(f"%/persons/photo/{storage_key}")
        ),
        current_user,
    ).first()

    if not photo_owner:
        raise HTTPException(status_code=404, detail="Photo not found or access denied")

    if object_storage.backend == "s3":
        return RedirectResponse(object_storage.signed_url(storage_key), status_code=307)

    file_path = object_storage.local_path(storage_key)
    if not file_path.is_file():
        # Backward compatibility for pre-Phase-I person photos.
        legacy_path = Path("uploads") / "person_photos" / Path(storage_key).name
        if not legacy_path.is_file():
            raise HTTPException(status_code=404, detail="Photo not found")
        file_path = legacy_path

    return FileResponse(path=file_path)


@router.get("/", response_model=List[PersonResponse])
def get_persons(
    response: Response,
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    reported_on: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = apply_person_agency_scope(db.query(Person), current_user)

    if status:
        query = query.filter(Person.status == status)

    if risk_level:
        query = query.filter(Person.risk_level == risk_level)

    query = apply_person_collection_filters(
        query,
        q=q,
        reported_on=reported_on,
        search_columns=INTERNAL_PERSON_SEARCH_COLUMNS,
    )

    return paginate_query_values(
        query.order_by(Person.created_at.desc()),
        limit=limit,
        offset=offset,
        response=response,
    )


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
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
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
        date_opened=utc_now(),
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
    current_user: User = Depends(require_role("platform_admin", "investigator", "supervisor")),
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
    current_user: User = Depends(require_role("platform_admin")),
):
    person = db.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    db.delete(person)
    db.commit()

    return {"message": "Person deleted"}
