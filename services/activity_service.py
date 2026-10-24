import json
import logging

from models.activity_log import ActivityLog
from services.audit_integrity import sign_activity_log
from services.clock import utc_now

security_event_logger = logging.getLogger("beacon.security.audit")
security_event_logger.setLevel(logging.INFO)

#ACTIVITY LOG TO DATABASE

def create_activity_log(

    db,

    action: str,

    entity: str,

    user_id: int | None = None,

    agency_id: int | None = None,

    entity_id: int | None = None,

    details: str | None = None,

    ip_address: str | None = None,
):


    log = ActivityLog(

        user_id=user_id,

        agency_id=agency_id,

        action=action,

        entity=entity,

        entity_id=entity_id,

        details=details,

        ip_address=ip_address,
        timestamp=utc_now(),
    )

    sign_activity_log(db, log)
    db.add(log)
    db.commit()
    db.refresh(log)

    # Emit a sanitized duplicate to the container log stream. Production log
    # routing can forward this JSON to CloudWatch/Splunk without exposing the
    # potentially sensitive free-form details field.
    security_event_logger.info(json.dumps({
        "event": "beacon_audit_event",
        "audit_id": log.id,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "user_id": log.user_id,
        "agency_id": log.agency_id,
        "action": log.action,
        "entity": log.entity,
        "entity_id": log.entity_id,
        "ip_address": log.ip_address,
        "previous_hash": log.previous_hash,
        "event_hash": log.event_hash,
        "integrity_key_id": log.integrity_key_id,
    }))


    return log
