from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from database.connection import get_db
from models.notification import Notification
from models.user import User
from security.auth import get_current_user
from services.activity_service import create_activity_log
from services.clock import utc_now_aware
from services.pagination import PaginationParams, paginate_query

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def user_notifications(db: Session, current_user: User):
    return db.query(Notification).filter(
        Notification.agency_id == current_user.agency_id,
        Notification.user_id == current_user.user_id,
    )


@router.get("/")
def list_notifications(
    response: Response,
    unread_only: bool = Query(False),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = user_notifications(db, current_user)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    return paginate_query(
        query.order_by(Notification.created_at.desc(), Notification.notification_id.desc()),
        pagination,
        response,
        cursor_column=Notification.notification_id,
    )


@router.get("/unread-count")
def unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "unread_count": user_notifications(db, current_user)
        .filter(Notification.read_at.is_(None))
        .count()
    }


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = user_notifications(db, current_user).filter(
        Notification.notification_id == notification_id
    ).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.read_at is None:
        notification.read_at = utc_now_aware()
        db.flush()
        create_activity_log(
            db=db,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            action="READ_NOTIFICATION",
            entity="notification",
            entity_id=notification.notification_id,
            details=f"{current_user.username} read notification {notification.notification_id}",
            ip_address=request.client.host if request.client else None,
        )
    return notification


@router.post("/read-all")
def mark_all_notifications_read(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unread = user_notifications(db, current_user).filter(Notification.read_at.is_(None)).all()
    read_at = utc_now_aware()
    for notification in unread:
        notification.read_at = read_at
    db.flush()
    if unread:
        create_activity_log(
            db=db,
            user_id=current_user.user_id,
            agency_id=current_user.agency_id,
            action="READ_ALL_NOTIFICATIONS",
            entity="notification",
            details=f"{current_user.username} read {len(unread)} notifications",
            ip_address=request.client.host if request.client else None,
        )
    else:
        db.commit()
    return {"read_count": len(unread), "read_at": read_at if unread else None}
