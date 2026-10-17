from datetime import timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.async_job import AsyncJob
from services.clock import utc_now


QUEUED_STATUSES = ("queued", "retry")


def enqueue_job(
    db: Session,
    *,
    agency_id: int,
    job_type: str,
    payload: dict[str, Any],
    idempotency_key: str,
    priority: int = 0,
    max_attempts: int = 5,
    available_at=None,
) -> tuple[AsyncJob, bool]:
    existing = db.query(AsyncJob).filter(
        AsyncJob.agency_id == agency_id,
        AsyncJob.idempotency_key == idempotency_key,
    ).first()
    if existing:
        return existing, False

    job = AsyncJob(
        agency_id=agency_id,
        job_type=job_type,
        payload=payload,
        idempotency_key=idempotency_key,
        status="queued",
        priority=priority,
        attempts=0,
        max_attempts=max_attempts,
        available_at=available_at or utc_now(),
    )
    try:
        with db.begin_nested():
            db.add(job)
            db.flush()
        return job, True
    except IntegrityError:
        existing = db.query(AsyncJob).filter(
            AsyncJob.agency_id == agency_id,
            AsyncJob.idempotency_key == idempotency_key,
        ).one()
        return existing, False


def recover_stale_jobs(
    db: Session,
    *,
    now=None,
    lease_seconds: int = 300,
) -> int:
    effective_now = now or utc_now()
    expired_before = effective_now - timedelta(seconds=lease_seconds)
    jobs = (
        db.query(AsyncJob)
        .filter(
            AsyncJob.status == "running",
            AsyncJob.locked_at <= expired_before,
        )
        .with_for_update(skip_locked=True)
        .all()
    )
    for job in jobs:
        job.locked_at = None
        job.locked_by = None
        job.updated_at = effective_now
        if job.attempts >= job.max_attempts:
            job.status = "dead_letter"
            job.last_error = job.last_error or "Worker lease expired"
        else:
            job.status = "retry"
            job.available_at = effective_now
    if jobs:
        db.commit()
    return len(jobs)


def claim_next_job(db: Session, *, worker_id: str, now=None) -> AsyncJob | None:
    effective_now = now or utc_now()
    job = (
        db.query(AsyncJob)
        .filter(
            AsyncJob.status.in_(QUEUED_STATUSES),
            AsyncJob.available_at <= effective_now,
            AsyncJob.attempts < AsyncJob.max_attempts,
        )
        .order_by(
            AsyncJob.priority.desc(),
            AsyncJob.available_at.asc(),
            AsyncJob.job_id.asc(),
        )
        .with_for_update(skip_locked=True)
        .first()
    )
    if not job:
        return None

    job.status = "running"
    job.attempts += 1
    job.locked_at = effective_now
    job.locked_by = worker_id[:200]
    job.updated_at = effective_now
    db.commit()
    db.refresh(job)
    return job


def complete_job(db: Session, job: AsyncJob, *, now=None) -> None:
    effective_now = now or utc_now()
    job.status = "completed"
    job.completed_at = effective_now
    job.updated_at = effective_now
    job.locked_at = None
    job.locked_by = None
    job.last_error = None
    db.commit()


def fail_job(
    db: Session,
    job: AsyncJob,
    error: Exception | str,
    *,
    now=None,
    retry_base_seconds: int = 30,
) -> None:
    effective_now = now or utc_now()
    job.last_error = str(error)[:4000]
    job.locked_at = None
    job.locked_by = None
    job.updated_at = effective_now

    if job.attempts >= job.max_attempts:
        job.status = "dead_letter"
    else:
        job.status = "retry"
        delay = retry_base_seconds * (2 ** max(0, min(job.attempts - 1, 8)))
        job.available_at = effective_now + timedelta(seconds=delay)
    db.commit()
