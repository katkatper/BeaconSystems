from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List

from database.connection import get_db
from models.timeline_events import Timeline_Event
from security.auth import get_current_user, require_role
from models.user import User
from security.case_access import apply_related_case_access_filter, assert_case_write_access, get_authorized_case



router = APIRouter(
    prefix="/timeline-events",
    tags=["Timeline Events"]
)


class TimelineEventCreate(BaseModel):
    case_id: int
    person_id: Optional[int] = None
    event_type: str
    source_type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
def get_timeline_events(
    case_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    query = db.query(Timeline_Event)
    query = apply_related_case_access_filter(query, Timeline_Event.case_id, current_user)

    if case_id is not None:
        get_authorized_case(db, case_id, current_user)

        query = query.filter(

            Timeline_Event.case_id == case_id
        )

    events = query.order_by(

        Timeline_Event.timestamp.desc()

    ).all()

    return events


@router.post("/")
def create_timeline_event(
    data: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    assert_case_write_access(db, data.case_id, current_user)

    event = Timeline_Event(
        case_id=data.case_id,
        person_id=data.person_id,
        event_type=data.event_type,
        source_type=data.source_type,
        location=data.location,
        description=data.description,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event
