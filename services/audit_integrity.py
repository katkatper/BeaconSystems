import hashlib
import hmac
import json

from sqlalchemy import text

from config.settings import AUDIT_INTEGRITY_KEY, AUDIT_INTEGRITY_KEY_ID
from models.activity_log import ActivityLog

GENESIS_HASH = "0" * 64


def audit_event_hash(
    event: ActivityLog,
    *,
    previous_hash: str,
    key: str,
    key_id: str,
) -> str:
    payload = {
        "action": event.action,
        "agency_id": event.agency_id,
        "details": event.details,
        "entity": event.entity,
        "entity_id": event.entity_id,
        "integrity_key_id": key_id,
        "ip_address": event.ip_address,
        "previous_hash": previous_hash,
        "timestamp": event.timestamp.isoformat(timespec="microseconds"),
        "user_id": event.user_id,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hmac.new(key.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def sign_activity_log(
    db,
    event: ActivityLog,
    *,
    key: str = AUDIT_INTEGRITY_KEY,
    key_id: str = AUDIT_INTEGRITY_KEY_ID,
) -> None:
    if not key or not key_id:
        return

    if db.bind.dialect.name == "postgresql":
        scope = f"beacon-audit:{event.agency_id if event.agency_id is not None else 'global'}"
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:scope))"), {"scope": scope})

    previous_query = db.query(ActivityLog).filter(ActivityLog.event_hash.is_not(None))
    if event.agency_id is None:
        previous_query = previous_query.filter(ActivityLog.agency_id.is_(None))
    else:
        previous_query = previous_query.filter(ActivityLog.agency_id == event.agency_id)
    previous = previous_query.order_by(ActivityLog.id.desc()).first()
    event.previous_hash = previous.event_hash if previous else GENESIS_HASH
    event.integrity_key_id = key_id
    event.event_hash = audit_event_hash(
        event,
        previous_hash=event.previous_hash,
        key=key,
        key_id=key_id,
    )


def verify_activity_log_chain(events, *, keys: dict[str, str]) -> dict:
    expected_previous: dict[int | None, str] = {}
    verified = 0
    unsigned = 0

    for event in events:
        if not event.event_hash:
            unsigned += 1
            continue
        expected = expected_previous.get(event.agency_id, GENESIS_HASH)
        key = keys.get(event.integrity_key_id)
        if not key or event.previous_hash != expected:
            return {"valid": False, "verified": verified, "unsigned": unsigned}
        calculated = audit_event_hash(
            event,
            previous_hash=event.previous_hash,
            key=key,
            key_id=event.integrity_key_id,
        )
        if not hmac.compare_digest(calculated, event.event_hash):
            return {"valid": False, "verified": verified, "unsigned": unsigned}
        expected_previous[event.agency_id] = event.event_hash
        verified += 1

    return {"valid": True, "verified": verified, "unsigned": unsigned}
