from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from database.connection import get_db
from models.timeline_events import Timeline_Event
from security.auth import get_current_user
from models.user import User
from security.case_access import apply_related_case_access_filter, get_authorized_case



router = APIRouter(
    prefix="/timeline-events",
    tags=["Timeline Events"]
)


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
