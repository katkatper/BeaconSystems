from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database.connection import get_db
from models.bolo_alert import BoloAlert
from models.case import Cases
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import apply_related_case_access_filter, assert_case_write_access
from services.activity_service import create_activity_log
from services.geocoding_fields import apply_geocode_result
from services.geocoding_service import geocode_address
from services.pagination import PaginationParams, paginate_query
from services.provider_observations import normalize_identifier

router = APIRouter(prefix="/bolos", tags=["BOLO Alerts"])


class BoloCreate(BaseModel):
    case_id: int | str
    title: str
    person_name: str | None = None
    last_known_location: str | None = None
    description: str
    risk_level: str = "high"
    share_with_partners: bool = False
    expires_at: datetime | None = None
    vehicle_year: int | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_color: str | None = None
    plate_number: str | None = None
    plate_state: str | None = None
    vehicle_identifiers: str | None = None

    @field_validator("case_id", mode="before")
    @classmethod
    def normalize_case_identifier(cls, value):
        if value is None or str(value).strip() == "":
            raise ValueError("Case ID or case number is required")

        return value

    @field_validator("expires_at", mode="before")
    @classmethod
    def normalize_browser_datetime(cls, value):
        if value in (None, ""):
            return None

        return value


class BoloUpdate(BaseModel):
    title: str | None = None
    person_name: str | None = None
    last_known_location: str | None = None
    description: str | None = None
    risk_level: str | None = None
    status: str | None = None
    share_with_partners: bool | None = None
    expires_at: datetime | None = None
    vehicle_year: int | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_color: str | None = None
    plate_number: str | None = None
    plate_state: str | None = None
    vehicle_identifiers: str | None = None

    @field_validator("expires_at", mode="before")
    @classmethod
    def normalize_browser_datetime(cls, value):
        if value in (None, ""):
            return None

        return value


def resolve_case_for_bolo(db: Session, case_identifier: int | str, current_user: User):
    identifier = str(case_identifier).strip()

    if identifier.isdigit():
        return assert_case_write_access(db, int(identifier), current_user)

    case = db.query(Cases).filter(Cases.case_number == identifier).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found. Enter the internal case ID or the exact case number.",
        )

    return assert_case_write_access(db, case.case_id, current_user)


def apply_geocode_fields(bolo: BoloAlert, location: str | None) -> None:
    geocoded = geocode_address(location)
    apply_geocode_result(bolo, geocoded, clear_when_missing=True)


@router.get("/")
def list_bolos(
    response: Response,
    status: str | None = "active",
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(BoloAlert)
    query = apply_related_case_access_filter(query, BoloAlert.case_id, current_user)

    if status:
        query = query.filter(BoloAlert.status == status)
        if status == "active":
            query = query.filter(
                or_(BoloAlert.expires_at.is_(None), BoloAlert.expires_at > datetime.utcnow())
            )

    return paginate_query(
        query.order_by(BoloAlert.created_at.desc()),
        pagination,
        response,
    )


@router.post("/")
def create_bolo(
    data: BoloCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    case = resolve_case_for_bolo(db, data.case_id, current_user)

    bolo = BoloAlert(
        case_id=case.case_id,
        agency_id=case.agency_id,
        created_by=current_user.user_id,
        title=data.title,
        person_name=data.person_name,
        last_known_location=data.last_known_location,
        description=data.description,
        risk_level=data.risk_level,
        share_with_partners=data.share_with_partners,
        expires_at=data.expires_at,
        vehicle_year=data.vehicle_year,
        vehicle_make=data.vehicle_make,
        vehicle_model=data.vehicle_model,
        vehicle_color=data.vehicle_color,
        plate_number=normalize_identifier(data.plate_number),
        plate_state=normalize_identifier(data.plate_state),
        vehicle_identifiers=data.vehicle_identifiers,
    )
    apply_geocode_fields(bolo, data.last_known_location)

    db.add(bolo)
    db.commit()
    db.refresh(bolo)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CREATE_BOLO",
        entity="bolo_alert",
        entity_id=bolo.bolo_id,
        details=f"Created BOLO alert: {bolo.title}",
    )

    return bolo


@router.put("/{bolo_id}")
def update_bolo(
    bolo_id: int,
    data: BoloUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    bolo = db.query(BoloAlert).filter(BoloAlert.bolo_id == bolo_id).first()

    if not bolo:
        raise HTTPException(status_code=404, detail="BOLO alert not found")

    assert_case_write_access(db, bolo.case_id, current_user)

    if current_user.role == "investigator" and bolo.created_by != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only creator or supervisor can update this BOLO")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field in {"plate_number", "plate_state"}:
            value = normalize_identifier(value)
        setattr(bolo, field, value)

    if "last_known_location" in update_data:
        apply_geocode_fields(bolo, data.last_known_location)

    db.commit()
    db.refresh(bolo)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="UPDATE_BOLO",
        entity="bolo_alert",
        entity_id=bolo.bolo_id,
        details=f"Updated BOLO alert: {bolo.title}",
    )

    return bolo
