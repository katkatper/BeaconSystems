from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from sqlalchemy.orm import Session

from database.connection import get_db

from models.external_record import ExternalRecord
from models.user import User

from models.timeline_events import Timeline_Event
from security.auth import get_current_user, require_role
from security.case_access import (
    apply_related_case_access_filter,
    assert_case_write_access,
    get_authorized_case,
)
from services.geocoding_service import geocode_address
from services.pagination import PaginationParams, paginate_query



# EXTERNAL RECORDS ROUTES - FOR DIGESTING EXTERNAL INTELLIGENCE INTO THE SYSTEM

router = APIRouter(

    prefix="/external-records",

    tags=["External Records"]
)


def apply_geocode_fields(record: ExternalRecord, location: str | None) -> None:
    geocoded = geocode_address(location)
    if not geocoded:
        return

    record.latitude = geocoded.get("latitude")
    record.longitude = geocoded.get("longitude")
    record.geocode_provider = geocoded.get("provider")
    record.geocode_accuracy = geocoded.get("accuracy")
    record.geocode_score = geocoded.get("score")
    record.geocoded_address = geocoded.get("formatted_address")
    record.geocoded_at = datetime.utcnow()


@router.post("/")

def create_external_record(

    integration_source_id: int,

    record_type: str,

    first_name: str | None = None,

    last_name: str | None = None,

    age: int | None = None,

    location: str | None = None,

    notes: str | None = None,
    
    person_id: int | None = None,

    case_id: int | None = None,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):
    if current_user.role != "admin" and case_id is None:
        raise HTTPException(
            status_code=400,
            detail="Agency users must link external records to an authorized case.",
        )

    authorized_case = None
    if case_id is not None:
        authorized_case = assert_case_write_access(db, case_id, current_user)

    record = ExternalRecord(

        agency_id=authorized_case.agency_id if authorized_case else None,

        integration_source_id=integration_source_id,

        record_type=record_type,

        first_name=first_name,

        last_name=last_name,

        age=age,

        location=location,

        notes=notes,

        person_id=person_id,

        case_id=case_id,
    )
    apply_geocode_fields(record, location)

    db.add(record)
    db.commit()
    db.refresh(record)

    if record.case_id is not None:

        timeline_event = Timeline_Event(

            case_id=record.case_id,

            person_id=record.person_id,

            event_type="external_record",

            source_type=record.record_type,

            location=record.location,

            description=record.notes
        )

        db.add(timeline_event)
        db.commit()

    return record

@router.get("/")
def get_external_records(

    person_id: Optional[int] = None,

    case_id: Optional[int] = None,

    response: Response = None,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):


    query = db.query(ExternalRecord)
    query = apply_related_case_access_filter(query, ExternalRecord.case_id, current_user)

    if person_id is not None:
        query = query.filter(ExternalRecord.person_id == person_id)

    if case_id is not None:
        get_authorized_case(db, case_id, current_user)
        query = query.filter(ExternalRecord.case_id == case_id)

    return paginate_query(
        query.order_by(ExternalRecord.created_at.desc()),
        pagination,
        response,
    )
