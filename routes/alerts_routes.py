from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.connection import get_db
from models.alert_delivery import AlertDelivery
from models.alerts import Alerts
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import (
    apply_related_case_access_filter,
    assert_case_write_access,
)
from services.activity_service import create_activity_log
from services.clock import utc_now
from services.job_queue import enqueue_job
from services.notification_service import notify_assigned_investigator_of_alert
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
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    case = assert_case_write_access(db, case_id, current_user)


    alerts = Alerts(

        case_id=case_id,

        person_id=person_id, 

        recipient_agency_id=case.agency_id,

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
    db.flush()
    delivery = AlertDelivery(
        alert_id=alerts.alert_id,
        agency_id=case.agency_id,
        status="pending",
    )
    db.add(delivery)
    db.flush()
    notify_assigned_investigator_of_alert(
        db,
        case=case,
        alert_id=alerts.alert_id,
        title=alerts.title,
        severity=alerts.severity,
    )
    enqueue_job(
        db,
        agency_id=case.agency_id,
        job_type="alert.deliver",
        payload={
            "alert_id": alerts.alert_id,
            "delivery_id": delivery.delivery_id,
        },
        idempotency_key=f"alert-delivery:{delivery.delivery_id}",
        priority=100 if severity.lower() in {"critical", "emergency"} else 50,
    )
    db.commit()
    db.refresh(alerts)


    return alerts


def get_authorized_alert(db: Session, alert_id: int, current_user: User) -> Alerts:
    query = apply_related_case_access_filter(
        db.query(Alerts).filter(Alerts.alert_id == alert_id),
        Alerts.case_id,
        current_user,
    )
    alert = query.first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/{alert_id}/receipts")
def get_alert_receipts(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = get_authorized_alert(db, alert_id, current_user)
    query = db.query(AlertDelivery).filter(AlertDelivery.alert_id == alert.alert_id)
    if current_user.role != "platform_admin":
        query = query.filter(AlertDelivery.agency_id == current_user.agency_id)
    deliveries = query.order_by(AlertDelivery.delivery_id).all()
    return {
        "alert_id": alert.alert_id,
        "sent": sum(item.sent_at is not None for item in deliveries),
        "delivered": sum(item.delivered_at is not None for item in deliveries),
        "viewed": sum(item.viewed_at is not None for item in deliveries),
        "acknowledged": sum(item.acknowledged_at is not None for item in deliveries),
        "pending": sum(item.status in {"pending", "queued"} for item in deliveries),
        "deliveries": deliveries,
    }


def get_user_delivery(db: Session, alert_id: int, current_user: User) -> AlertDelivery:
    get_authorized_alert(db, alert_id, current_user)
    if current_user.agency_id is None:
        raise HTTPException(status_code=400, detail="An agency is required for receipts")
    delivery = db.query(AlertDelivery).filter(
        AlertDelivery.alert_id == alert_id,
        AlertDelivery.agency_id == current_user.agency_id,
    ).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Alert delivery not found")
    return delivery


@router.post("/{alert_id}/viewed")
def mark_alert_viewed(
    alert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery = get_user_delivery(db, alert_id, current_user)
    if delivery.viewed_at is None:
        delivery.viewed_at = utc_now()
        delivery.viewed_by_user_id = current_user.user_id
        if delivery.status != "acknowledged":
            delivery.status = "viewed"
        db.commit()
        db.refresh(delivery)
        create_activity_log(
            db=db,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            action="VIEW_ALERT",
            entity="alert",
            entity_id=alert_id,
            details=f"{current_user.username} viewed alert {alert_id}",
            ip_address=request.client.host if request.client else None,
        )
    return delivery


@router.post("/{alert_id}/acknowledged")
def acknowledge_alert(
    alert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery = get_user_delivery(db, alert_id, current_user)
    now = utc_now()
    delivery.viewed_at = delivery.viewed_at or now
    delivery.viewed_by_user_id = delivery.viewed_by_user_id or current_user.user_id
    delivery.acknowledged_at = delivery.acknowledged_at or now
    delivery.acknowledged_by_user_id = (
        delivery.acknowledged_by_user_id or current_user.user_id
    )
    delivery.status = "acknowledged"
    db.commit()
    db.refresh(delivery)
    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="ACKNOWLEDGE_ALERT",
        entity="alert",
        entity_id=alert_id,
        details=f"{current_user.username} acknowledged alert {alert_id}",
        ip_address=request.client.host if request.client else None,
    )
    return delivery


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
        query.order_by(Alerts.created_at.desc(), Alerts.alert_id.desc()),
        pagination,
        response,
        cursor_column=Alerts.alert_id,
    )


@router.put("/{alert_id}")
def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
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
