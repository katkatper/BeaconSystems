import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.agencies import Agencies
from models.async_job import AsyncJob
from models.worker_heartbeat import WorkerHeartbeat
from services.alert_delivery_jobs import handle_alert_delivery
from services.job_queue import (
    CapacityQuotaExceeded,
    claim_next_job,
    complete_job,
    enqueue_job,
    fail_job,
    recover_stale_jobs,
)
from services.job_retention import prune_operational_history
from services.worker_monitoring import active_workers, record_worker_heartbeat

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class PhaseTwoJobQueueTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Agencies.__table__.create(self.engine)
        AsyncJob.__table__.create(self.engine)
        WorkerHeartbeat.__table__.create(self.engine)
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_enqueue_is_idempotent_within_a_tenant(self):
        first, created = enqueue_job(
            self.db,
            agency_id=10,
            job_type="matching.run",
            payload={"agency_id": 10},
            idempotency_key="matching:request-123",
        )
        second, created_again = enqueue_job(
            self.db,
            agency_id=10,
            job_type="matching.run",
            payload={"agency_id": 10},
            idempotency_key="matching:request-123",
        )
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.job_id, second.job_id)

        other_tenant, other_created = enqueue_job(
            self.db,
            agency_id=11,
            job_type="matching.run",
            payload={"agency_id": 11},
            idempotency_key="matching:request-123",
        )
        self.assertTrue(other_created)
        self.assertNotEqual(first.job_id, other_tenant.job_id)

    def test_enqueue_enforces_monthly_tenant_quotas_after_idempotency_check(self):
        agency = Agencies(
            agency_id=20,
            agency_name="Quota agency",
            monthly_job_quota=1,
            monthly_provider_request_quota=1,
        )
        self.db.add(agency)
        self.db.commit()

        first, created = enqueue_job(
            self.db,
            agency_id=20,
            job_type="partner_intake.process",
            payload={},
            idempotency_key="provider:first",
        )
        self.assertTrue(created)
        duplicate, duplicate_created = enqueue_job(
            self.db,
            agency_id=20,
            job_type="partner_intake.process",
            payload={},
            idempotency_key="provider:first",
        )
        self.assertFalse(duplicate_created)
        self.assertEqual(first.job_id, duplicate.job_id)

        with self.assertRaises(CapacityQuotaExceeded):
            enqueue_job(
                self.db,
                agency_id=20,
                job_type="matching.run",
                payload={},
                idempotency_key="matching:over-quota",
            )

        provider_agency = Agencies(
            agency_id=21,
            agency_name="Provider quota agency",
            monthly_job_quota=5,
            monthly_provider_request_quota=1,
        )
        self.db.add(provider_agency)
        self.db.commit()
        enqueue_job(
            self.db,
            agency_id=21,
            job_type="partner_intake.process",
            payload={},
            idempotency_key="provider:allowed",
        )
        with self.assertRaises(CapacityQuotaExceeded):
            enqueue_job(
                self.db,
                agency_id=21,
                job_type="partner_intake.process",
                payload={},
                idempotency_key="provider:over-quota",
            )

    def test_claim_complete_retry_and_dead_letter_lifecycle(self):
        now = datetime(2026, 10, 17, 12, 0, 0)
        job, _ = enqueue_job(
            self.db,
            agency_id=10,
            job_type="matching.run",
            payload={"agency_id": 10},
            idempotency_key="matching:lifecycle",
            max_attempts=2,
            available_at=now,
        )
        self.db.commit()

        claimed = claim_next_job(self.db, worker_id="worker-a", now=now)
        self.assertEqual(claimed.job_id, job.job_id)
        self.assertEqual(claimed.status, "running")
        self.assertEqual(claimed.attempts, 1)

        fail_job(self.db, claimed, "temporary", now=now, retry_base_seconds=10)
        self.assertEqual(claimed.status, "retry")
        self.assertEqual(claimed.available_at, now + timedelta(seconds=10))
        self.assertIsNone(claim_next_job(self.db, worker_id="worker-b", now=now))

        claimed = claim_next_job(
            self.db,
            worker_id="worker-b",
            now=now + timedelta(seconds=10),
        )
        fail_job(self.db, claimed, "permanent", now=now + timedelta(seconds=10))
        self.assertEqual(claimed.status, "dead_letter")

        completed, _ = enqueue_job(
            self.db,
            agency_id=10,
            job_type="matching.run",
            payload={"agency_id": 10},
            idempotency_key="matching:complete",
            available_at=now,
        )
        self.db.commit()
        completed = claim_next_job(self.db, worker_id="worker-a", now=now)
        complete_job(self.db, completed, now=now)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.completed_at, now)

    def test_phase_two_schema_and_routes_are_tenant_scoped(self):
        migration = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "b84e22d7513f_add_durable_async_jobs.py"
        ).read_text(encoding="utf-8")
        routes = (REPOSITORY_ROOT / "routes" / "jobs_routes.py").read_text(encoding="utf-8")
        matching = (REPOSITORY_ROOT / "routes" / "match_routes.py").read_text(encoding="utf-8")
        self.assertIn("ALTER TABLE async_jobs ENABLE ROW LEVEL SECURITY", migration)
        self.assertIn("beacon_tenant_isolation", migration)
        self.assertIn("AsyncJob.agency_id == current_user.agency_id", routes)
        self.assertIn('alias="Idempotency-Key"', matching)
        self.assertIn('job_type="matching.run"', matching)
        self.assertIn('@router.post("/{job_id}/replay")', routes)
        self.assertIn('action="REPLAY_ASYNC_JOB"', routes)

    def test_expired_worker_leases_are_retried_or_dead_lettered(self):
        now = datetime(2026, 10, 17, 12, 0, 0)
        retry_job, _ = enqueue_job(
            self.db,
            agency_id=10,
            job_type="matching.run",
            payload={"agency_id": 10},
            idempotency_key="matching:stale-retry",
            max_attempts=3,
            available_at=now,
        )
        dead_job, _ = enqueue_job(
            self.db,
            agency_id=10,
            job_type="matching.run",
            payload={"agency_id": 10},
            idempotency_key="matching:stale-dead",
            max_attempts=1,
            available_at=now,
        )
        for job, attempts in ((retry_job, 1), (dead_job, 1)):
            job.status = "running"
            job.attempts = attempts
            job.locked_by = "lost-worker"
            job.locked_at = now - timedelta(seconds=301)
        self.db.commit()

        recovered = recover_stale_jobs(self.db, now=now, lease_seconds=300)
        self.assertEqual(recovered, 2)
        self.assertEqual(retry_job.status, "retry")
        self.assertEqual(retry_job.available_at, now)
        self.assertEqual(dead_job.status, "dead_letter")

    def test_alert_delivery_handler_is_tenant_bound_and_idempotent(self):
        delivery = SimpleNamespace(
            delivery_id=7,
            agency_id=10,
            status="pending",
            sent_at=None,
            delivered_at=None,
            updated_at=None,
        )

        class Query:
            def filter(self, *args):
                return self

            def first(self):
                return delivery

        class FakeDb:
            def query(self, model):
                return Query()

            def flush(self):
                pass

        job = SimpleNamespace(
            agency_id=10,
            payload={"delivery_id": 7},
        )
        handle_alert_delivery(FakeDb(), job)
        self.assertEqual(delivery.status, "delivered")
        first_timestamp = delivery.delivered_at
        handle_alert_delivery(FakeDb(), job)
        self.assertEqual(delivery.delivered_at, first_timestamp)

    def test_alert_delivery_and_receipts_are_queued_tenant_scoped_and_audited(self):
        route_source = (REPOSITORY_ROOT / "routes" / "alerts_routes.py").read_text(encoding="utf-8")
        migration = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "c96f33e86240_add_alert_delivery_receipts.py"
        ).read_text(encoding="utf-8")
        self.assertIn('job_type="alert.deliver"', route_source)
        self.assertIn('@router.get("/{alert_id}/receipts")', route_source)
        self.assertIn('@router.post("/{alert_id}/viewed")', route_source)
        self.assertIn('@router.post("/{alert_id}/acknowledged")', route_source)
        self.assertIn('action="ACKNOWLEDGE_ALERT"', route_source)
        self.assertIn('down_revision = "b84e22d7513f"', migration)
        self.assertIn("ALTER TABLE alert_deliveries ENABLE ROW LEVEL SECURITY", migration)

    def test_partner_intake_queue_is_idempotent_and_runs_geocoding_off_request(self):
        routes = (REPOSITORY_ROOT / "routes" / "partner_intake_routes.py").read_text(encoding="utf-8")
        handler = (REPOSITORY_ROOT / "services" / "partner_intake_jobs.py").read_text(encoding="utf-8")
        model = (REPOSITORY_ROOT / "models" / "partner_intake_record.py").read_text(encoding="utf-8")
        migration = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "d07a44f97351_add_partner_intake_ingestion_keys.py"
        ).read_text(encoding="utf-8")
        self.assertIn('@router.post("/automated-async", status_code=202)', routes)
        self.assertIn('job_type="partner_intake.process"', routes)
        self.assertIn('alias="Idempotency-Key"', routes)
        self.assertIn('@register_job_handler("partner_intake.process")', handler)
        self.assertIn("create_intake_record", handler)
        self.assertIn("ingestion_key = Column", model)
        self.assertIn('down_revision = "c96f33e86240"', migration)
        audit_migration = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "e18b55a08462_allow_system_audit_actors.py"
        ).read_text(encoding="utf-8")
        self.assertIn('down_revision = "d07a44f97351"', audit_migration)
        self.assertIn('action="PROCESS_ASYNC_PARTNER_INTAKE"', handler)

    def test_worker_heartbeats_detect_active_and_stale_workers(self):
        now = datetime(2026, 10, 17, 12, 0, 0)
        record_worker_heartbeat(
            self.db,
            worker_id="worker-active",
            status="idle",
            now=now,
        )
        record_worker_heartbeat(
            self.db,
            worker_id="worker-stale",
            status="processing",
            current_job_id=None,
            now=now - timedelta(seconds=61),
        )
        workers = active_workers(self.db, timeout_seconds=60, now=now)
        self.assertEqual([worker.worker_id for worker in workers], ["worker-active"])
        record_worker_heartbeat(
            self.db,
            worker_id="worker-active",
            status="stopped",
            now=now,
        )
        self.assertEqual(active_workers(self.db, timeout_seconds=60, now=now), [])

    def test_operations_metrics_expose_backlog_without_job_payloads(self):
        routes = (REPOSITORY_ROOT / "routes" / "jobs_routes.py").read_text(encoding="utf-8")
        migration = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "f29c66b19573_add_worker_heartbeats.py"
        ).read_text(encoding="utf-8")
        self.assertIn('@router.get("/metrics")', routes)
        self.assertIn('"oldest_job_age_seconds"', routes)
        self.assertIn('"active_workers"', routes)
        self.assertNotIn('"payload": job.payload', routes)
        self.assertIn('down_revision = "e18b55a08462"', migration)

    def test_worker_runtime_is_non_root_and_handles_graceful_shutdown(self):
        worker = (REPOSITORY_ROOT / "scripts" / "run_worker.py").read_text(encoding="utf-8")
        dockerfile = (REPOSITORY_ROOT / "Dockerfile.worker").read_text(encoding="utf-8")
        workflow = (
            REPOSITORY_ROOT / ".github" / "workflows" / "release-gates.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("signal.SIGTERM", worker)
        self.assertIn("while not stop_event.is_set()", worker)
        self.assertIn('status="stopped"', worker)
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn("STOPSIGNAL SIGTERM", dockerfile)
        self.assertIn("Build production worker image", workflow)

    def test_retention_prunes_only_expired_operational_history(self):
        now = datetime(2026, 10, 17, 12, 0, 0)
        for key, status, age_days in (
            ("old-completed", "completed", 31),
            ("recent-completed", "completed", 2),
            ("old-dead", "dead_letter", 181),
            ("recent-dead", "dead_letter", 2),
            ("old-retry", "retry", 365),
        ):
            job, _ = enqueue_job(
                self.db,
                agency_id=10,
                job_type="matching.run",
                payload={"agency_id": 10},
                idempotency_key=f"retention:{key}",
                available_at=now - timedelta(days=age_days),
            )
            job.status = status
            job.updated_at = now - timedelta(days=age_days)
            if status == "completed":
                job.completed_at = now - timedelta(days=age_days)
        self.db.add(
            WorkerHeartbeat(
                worker_id="old-worker",
                status="stopped",
                started_at=now - timedelta(days=8),
                last_seen_at=now - timedelta(days=8),
            )
        )
        self.db.commit()

        deleted = prune_operational_history(
            self.db,
            completed_retention_days=30,
            dead_letter_retention_days=180,
            heartbeat_retention_days=7,
            now=now,
        )

        remaining = {
            job.idempotency_key for job in self.db.query(AsyncJob).all()
        }
        self.assertEqual(
            deleted,
            {"heartbeats": 1, "completed_jobs": 1, "dead_letter_jobs": 1},
        )
        self.assertEqual(
            remaining,
            {
                "retention:recent-completed",
                "retention:recent-dead",
                "retention:old-retry",
            },
        )

    def test_worker_runs_periodic_retention_maintenance(self):
        worker = (REPOSITORY_ROOT / "scripts" / "run_worker.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("prune_operational_history", worker)
        self.assertIn("WORKER_MAINTENANCE_INTERVAL_SECONDS", worker)


if __name__ == "__main__":
    unittest.main()
