"""Real PostgreSQL claim tests, requiring an explicitly supplied disposable DB."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from models.agencies import Agencies
from models.async_job import AsyncJob
from services.job_queue import claim_next_job, enqueue_job


@pytest.fixture
def queue_sessions():
    url = os.getenv("BEACON_QUEUE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set BEACON_QUEUE_TEST_DATABASE_URL to a disposable PostgreSQL database")
    base = create_engine(url)
    if base.dialect.name != "postgresql":
        base.dispose()
        pytest.fail("Queue concurrency acceptance requires PostgreSQL")
    schema = "beacon_queue_test_" + uuid4().hex
    with base.begin() as connection:
        connection.execute(CreateSchema(schema))
    engine = base.execution_options(schema_translate_map={None: schema})
    try:
        Agencies.__table__.create(engine)
        AsyncJob.__table__.create(engine)
        sessions = sessionmaker(bind=engine)
        with sessions() as db:
            db.add(Agencies(agency_id=10, agency_name="Synthetic test agency"))
            db.commit()
            for number in range(4):
                enqueue_job(db, agency_id=10, job_type="test", payload={}, idempotency_key=f"job-{number}")
            db.commit()
        yield sessions
    finally:
        # Only this test's freshly generated schema is removed.
        with base.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        base.dispose()


def test_simultaneous_workers_claim_different_jobs(queue_sessions):
    barrier = Barrier(2)

    def claim(worker):
        with queue_sessions() as db:
            barrier.wait(timeout=10)
            job = claim_next_job(db, worker_id=worker)
            return job.job_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(claim, worker) for worker in ("worker-a", "worker-b")]
        claimed = [future.result(timeout=20) for future in futures]
    assert len(set(claimed)) == 2
    with queue_sessions() as db:
        jobs = db.query(AsyncJob).filter(AsyncJob.job_id.in_(claimed)).all()
        assert all(job.status == "running" and job.attempts == 1 for job in jobs)


def test_locked_job_does_not_block_another_worker(queue_sessions):
    with queue_sessions() as locker, queue_sessions() as worker:
        locked = locker.execute(select(AsyncJob).order_by(AsyncJob.job_id).with_for_update().limit(1)).scalar_one()
        worker.execute(text("SET LOCAL statement_timeout = '3s'"))
        claimed = claim_next_job(worker, worker_id="worker-b")
        assert claimed.job_id != locked.job_id
        locker.rollback()
