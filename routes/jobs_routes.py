from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import QUEUE_BACKLOG_WARNING, WORKER_HEARTBEAT_TIMEOUT_SECONDS
from database.connection import get_db
from models.async_job import AsyncJob
from models.user import User
from security.auth import require_role
from services.activity_service import create_activity_log
from services.clock import utc_now
from services.http_metrics import http_metrics
from services.pagination import PaginationParams, paginate_query
from services.readiness import readiness_service
from services.worker_monitoring import active_workers

router = APIRouter(prefix="/operations/jobs", tags=["Operations Jobs"])


class JobReplayRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


def serialize_job(job: AsyncJob) -> dict:
    return {
        "job_id": job.job_id,
        "agency_id": job.agency_id,
        "job_type": job.job_type,
        "status": job.status,
        "priority": job.priority,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "replay_count": job.replay_count,
        "available_at": job.available_at,
        "locked_at": job.locked_at,
        "locked_by": job.locked_by,
        "last_error": job.last_error,
        "completed_at": job.completed_at,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def scoped_jobs(db: Session, current_user: User):
    query = db.query(AsyncJob)
    if current_user.role != "platform_admin":
        query = query.filter(AsyncJob.agency_id == current_user.agency_id)
    return query


@router.get("/")
def list_jobs(
    response: Response,
    job_status: str | None = Query(None, alias="status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    query = scoped_jobs(db, current_user)
    if job_status:
        query = query.filter(AsyncJob.status == job_status)
    jobs = paginate_query(
        query.order_by(AsyncJob.created_at.desc(), AsyncJob.job_id.desc()),
        pagination,
        response,
        cursor_column=AsyncJob.job_id,
    )
    return [serialize_job(job) for job in jobs]


@router.get("/metrics")
def get_job_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    query = scoped_jobs(db, current_user)
    counts = {
        status: count
        for status, count in query.with_entities(
            AsyncJob.status,
            func.count(AsyncJob.job_id),
        ).group_by(AsyncJob.status).all()
    }
    backlog = counts.get("queued", 0) + counts.get("retry", 0)
    oldest_available = query.filter(
        AsyncJob.status.in_(("queued", "retry"))
    ).with_entities(func.min(AsyncJob.available_at)).scalar()
    now = utc_now()
    oldest_age_seconds = (
        max(0, int((now - oldest_available).total_seconds()))
        if oldest_available
        else 0
    )
    workers = active_workers(
        db,
        timeout_seconds=WORKER_HEARTBEAT_TIMEOUT_SECONDS,
        now=now,
    )
    dead_letters = counts.get("dead_letter", 0)
    degraded = (
        backlog >= QUEUE_BACKLOG_WARNING
        or (backlog > 0 and not workers)
        or dead_letters > 0
    )
    result = {
        "status": "degraded" if degraded else "healthy",
        "counts": counts,
        "backlog": backlog,
        "dead_letters": dead_letters,
        "oldest_job_age_seconds": oldest_age_seconds,
        "active_workers": len(workers),
        "backlog_warning_threshold": QUEUE_BACKLOG_WARNING,
    }
    if current_user.role == "platform_admin":
        result["workers"] = [
            {
                "worker_id": worker.worker_id,
                "status": worker.status,
                "current_job_id": worker.current_job_id,
                "started_at": worker.started_at,
                "last_seen_at": worker.last_seen_at,
            }
            for worker in workers
        ]
    return result


@router.get("/metrics/prometheus", response_class=Response)
def export_job_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    metrics = get_job_metrics(db=db, current_user=current_user)
    values = {
        "beacon_queue_backlog": metrics["backlog"],
        "beacon_queue_dead_letters": metrics["dead_letters"],
        "beacon_queue_oldest_job_age_seconds": metrics["oldest_job_age_seconds"],
        "beacon_active_workers": metrics["active_workers"],
        "beacon_queue_degraded": int(metrics["status"] == "degraded"),
    }
    body = "".join(
        f"# TYPE {name} gauge\n{name} {value}\n"
        for name, value in values.items()
    )
    return Response(
        content=body,
        media_type="text/plain; version=0.0.4",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/metrics/system/prometheus", response_class=Response)
def export_system_metrics(
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    del current_user
    return Response(
        content=http_metrics.render_prometheus(readiness_service.snapshot()),
        media_type="text/plain; version=0.0.4",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    job = scoped_jobs(db, current_user).filter(AsyncJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job)


@router.post("/{job_id}/replay")
def replay_dead_letter_job(
    job_id: int,
    data: JobReplayRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    job = scoped_jobs(db, current_user).filter(AsyncJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "dead_letter":
        raise HTTPException(status_code=409, detail="Only dead-letter jobs can be replayed")

    reason = data.reason.strip()
    if len(reason) < 5:
        raise HTTPException(status_code=400, detail="Replay reason is required")
    job.status = "retry"
    job.attempts = 0
    job.replay_count += 1
    job.available_at = utc_now()
    job.locked_at = None
    job.locked_by = None
    job.completed_at = None
    job.last_error = f"Operator replay requested: {reason}"[:4000]
    db.commit()
    db.refresh(job)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=job.agency_id,
        action="REPLAY_ASYNC_JOB",
        entity="async_job",
        entity_id=job.job_id,
        details=f"{current_user.username} replayed {job.job_type}; reason: {reason}",
        ip_address=request.client.host if request.client else None,
    )
    return serialize_job(job)
