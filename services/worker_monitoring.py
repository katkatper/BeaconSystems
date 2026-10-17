from datetime import timedelta

from sqlalchemy.orm import Session

from models.worker_heartbeat import WorkerHeartbeat
from services.clock import utc_now


def record_worker_heartbeat(
    db: Session,
    *,
    worker_id: str,
    status: str,
    current_job_id: int | None = None,
    now=None,
) -> WorkerHeartbeat:
    effective_now = now or utc_now()
    bounded_worker_id = worker_id[:200]
    heartbeat = db.query(WorkerHeartbeat).filter(
        WorkerHeartbeat.worker_id == bounded_worker_id
    ).first()
    if not heartbeat:
        heartbeat = WorkerHeartbeat(
            worker_id=bounded_worker_id,
            started_at=effective_now,
        )
        db.add(heartbeat)
    heartbeat.status = status[:30]
    heartbeat.current_job_id = current_job_id
    heartbeat.last_seen_at = effective_now
    db.commit()
    return heartbeat


def active_workers(db: Session, *, timeout_seconds: int, now=None):
    effective_now = now or utc_now()
    cutoff = effective_now - timedelta(seconds=timeout_seconds)
    return db.query(WorkerHeartbeat).filter(
        WorkerHeartbeat.last_seen_at >= cutoff,
        WorkerHeartbeat.status.in_(("idle", "processing", "stopping")),
    ).order_by(WorkerHeartbeat.worker_id).all()
