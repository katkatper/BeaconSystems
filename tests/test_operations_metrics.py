from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database.connection import get_db
from models.agencies import Agencies
from models.async_job import AsyncJob
from models.worker_heartbeat import WorkerHeartbeat
from routes.jobs_routes import router
from security.auth import get_current_user
from services.job_queue import enqueue_job


def test_metrics_export_is_authenticated_tenant_scoped_and_payload_free():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for model in (Agencies, AsyncJob, WorkerHeartbeat):
        model.__table__.create(engine)
    with Session(engine) as db:
        for agency in (10, 11):
            job, _ = enqueue_job(db, agency_id=agency, job_type="test", payload={"secret": "private"}, idempotency_key="one")
            if agency == 11:
                job.status = "dead_letter"
        db.commit()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: db
        user = SimpleNamespace(role="supervisor", user_id=1, agency_id=10, is_active=True)
        app.dependency_overrides[get_current_user] = lambda: user
        with TestClient(app) as client:
            result = client.get("/operations/jobs/metrics/prometheus")
            assert result.status_code == 200
            assert "beacon_queue_backlog 1" in result.text
            assert "beacon_queue_dead_letters 0" in result.text
            assert "private" not in result.text
            user.role = "viewer"
            assert client.get("/operations/jobs/metrics/prometheus").status_code == 403
    engine.dispose()
