from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.alerts import Alerts
from  database.connection import get_db
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import apply_related_case_access_filter, assert_case_write_access

# ALERTS ROUTES - FOR MANAGING ALERTS GENERATED FROM CASES OR EXTERNAL SOURCES


router=APIRouter()

router = APIRouter(

    prefix="/alerts",

    tags=["Alerts"]
)


@router.post("/")

def create_alerts(

    case_id: int,

    person_id: int,

    alert_type: str,

    title: str,

    description: str,

    severity: str = "medium",

    alert_source: str = "investigator",

    source_detail: str | None = None,

    confidence_score: float | None = None,

    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    assert_case_write_access(db, case_id, current_user)


    alerts = Alerts(

        case_id=case_id,

        person_id=person_id, 

        alert_type=alert_type,

        alert_source=alert_source,

        source_detail=source_detail,

        confidence_score=confidence_score,

        title=title,

        description=description,

        severity=severity,
    )
    
    db.add(alerts)
    db.commit()
    db.refresh(alerts)


    return alerts


@router.get("/")

def get_alerts(

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    query = db.query(Alerts)
    query = apply_related_case_access_filter(query, Alerts.case_id, current_user)

    return query.order_by(

        Alerts.created_at.desc()

    ).all()
