from datetime import timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.agencies import Agencies
from models.async_job import AsyncJob
from services.clock import utc_now

QUEUED_STATUSES = ("queued", "retry")


class CapacityQuotaExceeded(RuntimeError):
    def __init__(self, quota_name: str):
        self.quota_name = quota_name
        super().__init__(f"Agency {quota_name} quota exceeded")


def _month_start(now):
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _enforce_enqueue_quotas(
    db: Session,
    *,
    agency_id: int,
    job_type: str,
    now,
) -> None:
    agency = (
        db.query(Agencies)
        .filter(Agencies.agency_id == agency_id)
        .with_for_update()
        .first()
    )
    if agency is None:
        return

    month_start = _month_start(now)
    monthly_jobs = db.query(func.count(AsyncJob.job_id)).filter(
        AsyncJob.agency_id == agency_id,
        AsyncJob.created_at >= month_start,
    ).scalar()
    if (
        agency.monthly_job_quota is not None
        and int(monthly_jobs or 0) >= agency.monthly_job_quota
    ):
        raise CapacityQuotaExceeded("monthly job")

    if job_type == "partner_intake.process" and agency.monthly_provider_request_quota is not None:
        provider_jobs = db.query(func.count(AsyncJob.job_id)).filter(
            AsyncJob.agency_id == agency_id,
            AsyncJob.job_type == "partner_intake.process",
            AsyncJob.created_at >= month_start,
        ).scalar()
        if int(provider_jobs or 0) >= agency.monthly_provider_request_quota:
            raise CapacityQuotaExceeded("monthly provider request")


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

    quota_now = utc_now()
    effective_now = available_at or quota_now
    _enforce_enqueue_quotas(
        db,
        agency_id=agency_id,
        job_type=job_type,
        now=quota_now,
    )

    job = AsyncJob(
        agency_id=agency_id,
        job_type=job_type,
        payload=payload,
        idempotency_key=idempotency_key,
        status="queued",
        priority=priority,
        attempts=0,
        max_attempts=max_attempts,
        available_at=effective_now,
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
        .outerjoin(Agencies, Agencies.agency_id == AsyncJob.agency_id)
        .filter(
            AsyncJob.status.in_(QUEUED_STATUSES),
            AsyncJob.available_at <= effective_now,
            AsyncJob.attempts < AsyncJob.max_attempts,
        )
        .order_by(
            Agencies.queue_last_claimed_at.asc().nullsfirst(),
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
    agency = db.query(Agencies).filter(Agencies.agency_id == job.agency_id).first()
    if agency:
        agency.queue_last_claimed_at = effective_now
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
    _record_provider_result(db, job, succeeded=True, now=effective_now)
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
    _record_provider_result(db, job, succeeded=False, now=effective_now, error=str(error))
    db.commit()


def _record_provider_result(
    db: Session,
    job: AsyncJob,
    *,
    succeeded: bool,
    now,
    error: str | None = None,
) -> None:
    if job.job_type != "partner_intake.process":
        return
    # Imported only for provider jobs so isolated queue tests do not need the
    # complete integrations relationship graph.
    from models.integration_source import IntegrationSource
    from models.integration_source_agency import IntegrationSourceAgency  # noqa: F401

    source_id = (job.payload.get("data") or {}).get("integration_source_id")
    if not source_id:
        return
    source = db.query(IntegrationSource).filter(IntegrationSource.id == int(source_id)).first()
    if not source:
        return
    if succeeded:
        source.consecutive_failures = 0
        source.circuit_open_until = None
        source.last_success_at = now
        source.last_failure_reason = None
        return
    source.consecutive_failures = int(source.consecutive_failures or 0) + 1
    source.last_failure_at = now
    source.last_failure_reason = (error or "Provider job failed")[:1000]
    if source.consecutive_failures >= 5:
        source.circuit_open_until = now + timedelta(minutes=5)
