import unittest
from threading import Event
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from models.agencies import Agencies
from models.async_job import AsyncJob
from models.worker_heartbeat import WorkerHeartbeat
from scripts.run_worker import run_worker
from services.job_queue import enqueue_job


class WorkerFailureTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        for model in (Agencies, AsyncJob, WorkerHeartbeat):
            model.__table__.create(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as db:
            job, _ = enqueue_job(
                db, agency_id=10, job_type="test.failure", payload={"original": True},
                idempotency_key="failure-test",
            )
            db.commit()
            self.job_id = job.job_id

    def tearDown(self):
        self.engine.dispose()

    def run_failing_worker(self, handler):
        stop = Event()

        def dispatch(db, job):
            stop.set()
            handler(db, job)

        with (
            patch("scripts.run_worker.SessionLocal", self.sessions),
            patch("scripts.run_worker.validate_runtime_settings"),
            patch("scripts.run_worker.IS_PRODUCTION", False),
            patch("scripts.run_worker._install_shutdown_handlers"),
            patch("scripts.run_worker.dispatch_job", side_effect=dispatch),
            self.assertLogs("beacon.worker", level="ERROR"),
        ):
            run_worker(stop)

        with self.sessions() as db:
            job = db.get(AsyncJob, self.job_id)
            self.assertEqual(job.status, "retry")
            self.assertEqual(job.attempts, 1)
            self.assertIsNone(job.locked_by)
            self.assertEqual(job.payload, {"original": True})
            self.assertEqual(db.query(WorkerHeartbeat).one().status, "stopped")
            return job.last_error

    def test_handler_partial_writes_are_rolled_back_before_retry(self):
        def fail_after_write(db, job):
            job.payload = {"partial": True}
            db.flush()
            raise RuntimeError("Provider unavailable")

        self.assertIn("Provider unavailable", self.run_failing_worker(fail_after_write))

    def test_failed_database_transaction_can_record_retry(self):
        def invalidate_transaction(db, job):
            job.payload = {"partial": True}
            db.add(AsyncJob(
                agency_id=10, job_type="duplicate", payload={},
                idempotency_key="failure-test",
            ))
            try:
                db.flush()
            except IntegrityError:
                raise

        self.assertIn("UNIQUE constraint", self.run_failing_worker(invalidate_transaction))
