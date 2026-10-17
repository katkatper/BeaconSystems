from collections.abc import Callable

from sqlalchemy.orm import Session

from models.async_job import AsyncJob


JobHandler = Callable[[Session, AsyncJob], None]
_HANDLERS: dict[str, JobHandler] = {}


def register_job_handler(job_type: str):
    def decorator(handler: JobHandler) -> JobHandler:
        if job_type in _HANDLERS:
            raise RuntimeError(f"Duplicate job handler: {job_type}")
        _HANDLERS[job_type] = handler
        return handler

    return decorator


def dispatch_job(db: Session, job: AsyncJob) -> None:
    handler = _HANDLERS.get(job.job_type)
    if not handler:
        raise RuntimeError(f"No handler registered for job type: {job.job_type}")
    handler(db, job)
