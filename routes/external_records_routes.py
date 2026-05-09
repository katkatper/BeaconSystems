from typing import Optional

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from database.connection import get_db

from models.external_record import ExternalRecord



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

    db: Session = Depends(get_db)
):
    record = ExternalRecord(

        integration_source_id=integration_source_id,

        record_type=record_type,

        first_name=first_name,

        last_name=last_name,

        age=age,

        location=location,

        notes=notes
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/")
def get_external_records(

    person_id: Optional[int] = None,

    case_id: Optional[int] = None,

    db: Session = Depends(get_db)
):

    query = db.query(ExternalRecord)

    if person_id is not None:
        query = query.filter(ExternalRecord.person_id == person_id)

    if case_id is not None:
        query = query.filter(ExternalRecord.case_id == case_id)

    return query.all()