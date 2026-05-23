from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from models.case import Cases
from models.sighting import Sighting
from models.activity_log import ActivityLog
from models.user import User
from security.auth import get_current_user



router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")

def get_dashboard_summary(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):

    case_query = db.query(Cases)

    if current_user.role != "admin":

        case_query = case_query.filter(Cases.agency_id == current_user.agency_id)

    total_cases = case_query.count()

    open_cases = case_query.filter(func.lower(Cases.case_status) == "open").count()

    high_priority_cases = case_query.filter(Cases.priority_level == "high").count()


    recent_sightings = db.query(Sighting).order_by(

        Sighting.created_at.desc()

    ).limit(5).all()

    recent_activity = db.query(ActivityLog).order_by(

        ActivityLog.timestamp.desc()

    ).limit(5).all()

    return {

        "total_cases": total_cases,

        "open_cases": open_cases,

        "high_priority_cases": high_priority_cases,

        "recent_sightings": recent_sightings,

        "recent_activity": recent_activity,
    }
