from sqlalchemy.orm import Session
from models.activity_log import ActivityLog


def log_activity(
    db: Session,
    user_id: int,
    action: str,
    entity: str,
    entity_id: int = None,
    details: str = None,
):
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry