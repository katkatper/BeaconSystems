from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi import Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.alerts import Alerts
from  database.connection import get_db
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import apply_related_case_access_filter, assert_case_write_access
from services.pagination import PaginationParams, paginate_query

# ALERTS ROUTES - FOR MANAGING ALERTS GENERATED FROM CASES OR EXTERNAL SOURCES


router=APIRouter()

router = APIRouter(

    prefix="/alerts",

    tags=["Alerts"]
)


class AlertUpdate(BaseModel):
    case_id: int | None = None
    person_id: int | None = None
    alert_type: str | None = None
    alert_source: str | None = None
    source_detail: str | None = None
    confidence_score: float | None = None
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    alert_status: str | None = None


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

        alert_status="active",
    )
    
    db.add(alerts)
    db.commit()
    db.refresh(alerts)


    return alerts


@router.get("/")

def get_alerts(

    response: Response,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    query = db.query(Alerts)
    query = apply_related_case_access_filter(query, Alerts.case_id, current_user)
    query = query.filter(
        func.lower(Alerts.alert_status) == "active",
        (Alerts.alert_type.is_(None))
        | (~func.lower(Alerts.alert_type).like("%deleted%")),
        (Alerts.title.is_(None)) | (~func.lower(Alerts.title).like("%deleted%")),
    )

    return paginate_query(
        query.order_by(Alerts.created_at.desc()),
        pagination,
        response,
    )


@router.put("/{alert_id}")
def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor", "investigator")),
):
    alert = db.query(Alerts).filter(Alerts.alert_id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    assert_case_write_access(db, alert.case_id, current_user)

    update_data = data.model_dump(exclude_unset=True)
    next_case_id = update_data.get("case_id")

    if next_case_id is not None and next_case_id != alert.case_id:
        assert_case_write_access(db, next_case_id, current_user)

    for field, value in update_data.items():
        setattr(alert, field, value)

    db.commit()
    db.refresh(alert)

    return alert
