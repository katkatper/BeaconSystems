from sqlalchemy.orm import Session

from models.case import Cases
from models.notification import Notification
from models.user import User


def notify_assigned_investigator_of_alert(
    db: Session,
    *,
    case: Cases,
    alert_id: int,
    title: str,
    severity: str,
) -> Notification | None:
    if case.investigator_id is None:
        return None

    investigator = db.query(User).filter(
        User.user_id == case.investigator_id,
        User.agency_id == case.agency_id,
        User.role == "investigator",
        User.is_active.is_(True),
    ).first()
    if investigator is None:
        return None

    existing = db.query(Notification).filter(
        Notification.user_id == investigator.user_id,
        Notification.notification_type == "alert_assigned_case",
        Notification.entity_type == "alert",
        Notification.entity_id == alert_id,
    ).first()
    if existing:
        return existing

    notification = Notification(
        agency_id=case.agency_id,
        user_id=investigator.user_id,
        notification_type="alert_assigned_case",
        entity_type="alert",
        entity_id=alert_id,
        case_id=case.case_id,
        title=title,
        message=f"{severity.title()} alert on assigned case {case.case_number}.",
    )
    db.add(notification)
    db.flush()
    return notification
