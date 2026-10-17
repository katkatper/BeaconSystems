from datetime import timedelta

from sqlalchemy.orm import Session

from models.async_job import AsyncJob
from models.worker_heartbeat import WorkerHeartbeat
from services.clock import utc_now


def prune_operational_history(
    db: Session,
    *,
    completed_retention_days: int,
    dead_letter_retention_days: int,
    heartbeat_retention_days: int,
    now=None,
) -> dict[str, int]:
    """Delete expired operational history without touching actionable jobs."""
    effective_now = now or utc_now()
    heartbeat_cutoff = effective_now - timedelta(days=heartbeat_retention_days)
    completed_cutoff = effective_now - timedelta(days=completed_retention_days)
    dead_letter_cutoff = effective_now - timedelta(days=dead_letter_retention_days)

    # Remove old heartbeat references first so they do not retain completed jobs
    # after a worker disappears unexpectedly.
    heartbeats = db.query(WorkerHeartbeat).filter(
        WorkerHeartbeat.last_seen_at < heartbeat_cutoff
    ).delete(synchronize_session=False)
    completed_jobs = db.query(AsyncJob).filter(
        AsyncJob.status == "completed",
        AsyncJob.completed_at.is_not(None),
        AsyncJob.completed_at < completed_cutoff,
    ).delete(synchronize_session=False)
    dead_letter_jobs = db.query(AsyncJob).filter(
        AsyncJob.status == "dead_letter",
        AsyncJob.updated_at < dead_letter_cutoff,
    ).delete(synchronize_session=False)
    db.commit()
    return {
        "heartbeats": heartbeats,
        "completed_jobs": completed_jobs,
        "dead_letter_jobs": dead_letter_jobs,
    }
