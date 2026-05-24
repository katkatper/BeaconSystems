from typing import Optional

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from database.connection import get_db

from models.external_record import ExternalRecord
from models.user import User

from models.timeline_events import Timeline_Event
from security.auth import get_current_user, require_role



# EXTERNAL RECORDS ROUTES - FOR DIGESTING EXTERNAL INTELLIGENCE INTO THE SYSTEM

router = APIRouter(

    prefix="/external-records",

    tags=["External Records"]
)


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

    record = ExternalRecord(

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

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):


    query = db.query(ExternalRecord)

    if person_id is not None:
        query = query.filter(ExternalRecord.person_id == person_id)

    if case_id is not None:
        query = query.filter(ExternalRecord.case_id == case_id)

    return query.all()
