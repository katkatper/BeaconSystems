import logging
import os
import signal
import socket
from threading import Event
from time import monotonic

from config.settings import (
    IS_PRODUCTION,
    JOB_COMPLETED_RETENTION_DAYS,
    JOB_DEAD_LETTER_RETENTION_DAYS,
    WORKER_HEARTBEAT_RETENTION_DAYS,
    WORKER_MAINTENANCE_INTERVAL_SECONDS,
    validate_runtime_settings,
)
from database.connection import SessionLocal, engine
from database.security_posture import validate_database_security
from database.tenant_context import configure_tenant_session
from services.job_handlers import dispatch_job
from services.job_queue import claim_next_job, complete_job, fail_job, recover_stale_jobs
from services.job_retention import prune_operational_history
from services.worker_monitoring import record_worker_heartbeat
import services.matching_jobs  # noqa: F401, E402
import services.alert_delivery_jobs  # noqa: F401, E402
import services.partner_intake_jobs  # noqa: F401, E402


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("beacon.worker")


def _install_shutdown_handlers(stop_event: Event) -> None:
    def request_shutdown(signum, frame):
        logger.info("Worker shutdown requested by signal %s", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)


def run_worker(stop_event: Event | None = None) -> None:
    validate_runtime_settings()
    if IS_PRODUCTION:
        validate_database_security(engine)

    stop_event = stop_event or Event()
    _install_shutdown_handlers(stop_event)
    worker_id = os.getenv("WORKER_ID") or f"{socket.gethostname()}-{os.getpid()}"
    poll_seconds = max(0.1, float(os.getenv("WORKER_POLL_SECONDS", "1")))
    lease_seconds = max(30, int(os.getenv("WORKER_LEASE_SECONDS", "300")))
    retry_base_seconds = max(1, int(os.getenv("WORKER_RETRY_BASE_SECONDS", "30")))
    next_maintenance_at = 0.0

    while not stop_event.is_set():
        with SessionLocal() as db:
            configure_tenant_session(db, agency_id=None, platform_admin=True)
            record_worker_heartbeat(db, worker_id=worker_id, status="idle")
            recover_stale_jobs(db, lease_seconds=lease_seconds)
            if monotonic() >= next_maintenance_at:
                deleted = prune_operational_history(
                    db,
                    completed_retention_days=JOB_COMPLETED_RETENTION_DAYS,
                    dead_letter_retention_days=JOB_DEAD_LETTER_RETENTION_DAYS,
                    heartbeat_retention_days=WORKER_HEARTBEAT_RETENTION_DAYS,
                )
                if any(deleted.values()):
                    logger.info("Pruned operational history: %s", deleted)
                next_maintenance_at = (
                    monotonic() + WORKER_MAINTENANCE_INTERVAL_SECONDS
                )
            job = claim_next_job(db, worker_id=worker_id)
            if not job:
                stop_event.wait(poll_seconds)
                continue
            record_worker_heartbeat(
                db,
                worker_id=worker_id,
                status="processing",
                current_job_id=job.job_id,
            )
            try:
                dispatch_job(db, job)
            except Exception as exc:
                # A handler may have flushed partial writes or invalidated the
                # transaction. Roll it back before persisting retry state.
                db.rollback()
                logger.exception("Job %s failed", job.job_id)
                fail_job(db, job, exc, retry_base_seconds=retry_base_seconds)
            else:
                complete_job(db, job)
            record_worker_heartbeat(
                db,
                worker_id=worker_id,
                status="stopping" if stop_event.is_set() else "idle",
            )

    with SessionLocal() as db:
        configure_tenant_session(db, agency_id=None, platform_admin=True)
        record_worker_heartbeat(db, worker_id=worker_id, status="stopped")
    logger.info("Worker %s stopped cleanly", worker_id)


if __name__ == "__main__":
    run_worker()
