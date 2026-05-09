from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from database.connection import get_db
from models.timeline_events import Timeline_Event
from security.auth import get_current_user
from models.user import User



router = APIRouter(
    prefix="/timeline-events",
    tags=["Timeline Events"]
)


@router.get("/")
def get_timeline_events(
    case_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):

    query = db.query(Timeline_Event)

    if case_id is not None:

        query = query.filter(

            Timeline_Event.case_id == case_id
        )

    events = query.order_by(

        Timeline_Event.timestamp.desc()

    ).all()

    return events