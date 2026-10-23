import ast
import io
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from fastapi import HTTPException, Response
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from database.connection import build_database_url
from services.evidence_retention import (
    assert_evidence_disposition_allowed,
    retention_decision,
)
from services.malware_scanner import MalwareScanner, scan_upload
from services.object_storage import ObjectStorage
from services.pagination import PaginationParams, paginate_query
from services.upload_validation import validate_upload

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class PhaseOneFoundationTests(unittest.TestCase):
    def test_local_storage_uses_tenant_scoped_keys_and_blocks_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ObjectStorage()
            storage.backend = "local"
            storage.local_root = Path(directory).resolve()
            key = storage.create_key(42, "evidence", "../statement.pdf")
            self.assertIn("agency-42/evidence/", key)
            stored = storage.put(io.BytesIO(b"beacon evidence"), key, "application/pdf")
            self.assertTrue(storage.local_path(stored.key).is_file())
            self.assertEqual(len(stored.sha256), 64)
            with self.assertRaises(ValueError):
                storage.local_path("../../outside.txt")

    def test_production_requires_shared_object_storage(self):
        source = (REPOSITORY_ROOT / "config" / "settings.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("OBJECT_STORAGE_BACKEND must be 's3' in production", source)
        self.assertIn("OBJECT_STORAGE_BUCKET is required in production", source)
        self.assertIn("OBJECT_STORAGE_KMS_KEY_ID is required in production", source)
        self.assertIn("OBJECT_STORAGE_EXPECTED_OWNER must be a 12 digit AWS account ID", source)

    def test_s3_uploads_require_customer_managed_kms_encryption_and_expected_owner(self):
        class FakeS3Client:
            def __init__(self):
                self.upload = None
                self.head_request = None
                self.public_access_request = None
                self.versioning_request = None
                self.encryption_request = None

            def head_bucket(self, **params):
                self.head_request = params

            def get_public_access_block(self, **params):
                self.public_access_request = params
                return {
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    }
                }

            def get_bucket_versioning(self, **params):
                self.versioning_request = params
                return {"Status": "Enabled"}

            def get_bucket_encryption(self, **params):
                self.encryption_request = params
                return {
                    "ServerSideEncryptionConfiguration": {
                        "Rules": [{
                            "ApplyServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "aws:kms",
                                "KMSMasterKeyID": "arn:aws:kms:us-gov-west-1:123456789012:key/test",
                            }
                        }]
                    }
                }

            def upload_fileobj(self, stream, bucket, key, ExtraArgs):
                self.upload = {
                    "body": stream.read(),
                    "bucket": bucket,
                    "key": key,
                    "extra": ExtraArgs,
                }

        storage = ObjectStorage.__new__(ObjectStorage)
        storage.backend = "s3"
        storage.bucket = "beacon-evidence"
        storage.prefix = "beacon"
        storage.kms_key_id = "arn:aws:kms:us-gov-west-1:123456789012:key/test"
        storage.expected_owner = "123456789012"
        storage._s3 = FakeS3Client()

        stored = storage.put(
            io.BytesIO(b"investigative evidence"),
            "beacon/agency-1/evidence/item.bin",
            "application/octet-stream",
        )

        self.assertEqual(len(stored.sha256), 64)
        self.assertEqual(storage._s3.upload["extra"]["ServerSideEncryption"], "aws:kms")
        self.assertEqual(storage._s3.upload["extra"]["SSEKMSKeyId"], storage.kms_key_id)
        self.assertEqual(storage._s3.upload["extra"]["ExpectedBucketOwner"], "123456789012")

        storage.validate_production_access()
        self.assertEqual(
            storage._s3.head_request,
            {"Bucket": "beacon-evidence", "ExpectedBucketOwner": "123456789012"},
        )
        self.assertEqual(storage._s3.public_access_request, storage._s3.head_request)
        self.assertEqual(storage._s3.versioning_request, storage._s3.head_request)
        self.assertEqual(storage._s3.encryption_request, storage._s3.head_request)
        self.assertTrue(storage.is_encrypted)
        self.assertEqual(storage.encryption_key_id, storage.kms_key_id)

    def test_s3_validation_rejects_public_or_unversioned_evidence_buckets(self):
        class UnsafeS3Client:
            def head_bucket(self, **params):
                return None

            def get_public_access_block(self, **params):
                return {
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": False,
                        "RestrictPublicBuckets": True,
                    }
                }

            def get_bucket_versioning(self, **params):
                return {"Status": "Suspended"}

            def get_bucket_encryption(self, **params):
                return {}

        storage = ObjectStorage.__new__(ObjectStorage)
        storage.backend = "s3"
        storage.bucket = "unsafe-evidence"
        storage.expected_owner = "123456789012"
        storage._s3 = UnsafeS3Client()

        with self.assertRaisesRegex(RuntimeError, "block every form of public access"):
            storage.validate_production_access()

    def test_database_fallback_url_preserves_verified_tls_options(self):
        with patch.dict(
            "os.environ",
            {
                "DATABASE_URL": "",
                "DB_USER": "beacon",
                "DB_PASSWORD": "secret value",
                "DB_HOST": "db.beacon.example",
                "DB_PORT": "5432",
                "DB_NAME": "beacon",
                "DB_SSLMODE": "verify-full",
                "DB_SSLROOTCERT": "/etc/beacon/rds-ca.pem",
            },
            clear=False,
        ):
            url = build_database_url()

        parsed = urlsplit(url)
        options = parse_qs(parsed.query)
        self.assertEqual(options["sslmode"], ["verify-full"])
        self.assertEqual(options["sslrootcert"], ["/etc/beacon/rds-ca.pem"])
        self.assertIn("secret+value", parsed.netloc)

    def test_upload_routes_use_shared_storage_boundary(self):
        evidence = (REPOSITORY_ROOT / "routes" / "evidence_routes.py").read_text(encoding="utf-8")
        persons = (REPOSITORY_ROOT / "routes" / "person_routes.py").read_text(encoding="utf-8")
        ast.parse(evidence)
        ast.parse(persons)
        self.assertIn('create_key(agency_id, "evidence"', evidence)
        self.assertIn('"person-photos"', persons)
        self.assertNotIn("shutil.copyfileobj", evidence)
        self.assertNotIn("shutil.copyfileobj", persons)

    def test_runtime_exposes_request_ids_and_readiness(self):
        source = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('@app.middleware("http")', source)
        self.assertIn('response.headers["X-Request-ID"]', source)
        self.assertIn('@app.get("/ready")', source)
        self.assertIn('sql_text("SELECT 1")', source)
        self.assertIn("validate_rate_limit_backend()", source)
        self.assertIn("object_storage.validate_production_access()", source)

    def test_phase_one_indexes_are_preserved_in_the_baseline(self):
        source = (REPOSITORY_ROOT / "migrations" / "versions" / "601d95116833_create_beacon_production_baseline.py").read_text(encoding="utf-8")
        self.assertIn("ix_cases_agency_status_updated", source)
        self.assertIn("ix_evidence_case_created", source)

    def test_upload_validation_rejects_oversized_spoofed_and_executable_files(self):
        with self.assertRaises(HTTPException):
            validate_upload(
                io.BytesIO(b"not a jpeg"),
                file_name="photo.jpg",
                content_type="image/jpeg",
                allowed_content_types={"image/jpeg"},
            )
        with self.assertRaises(HTTPException):
            validate_upload(
                io.BytesIO(b"MZ executable"),
                file_name="report.pdf",
                content_type="application/pdf",
            )

    def test_clamav_stream_scan_preserves_stream_and_accepts_clean_upload(self):
        class FakeConnection:
            def __init__(self):
                self.sent = bytearray()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def settimeout(self, timeout):
                self.timeout = timeout

            def sendall(self, payload):
                self.sent.extend(payload)

            def recv(self, size):
                return b"stream: OK\0"

        connection = FakeConnection()
        scanner = MalwareScanner()
        scanner.backend = "clamav"
        stream = io.BytesIO(b"investigative upload")
        stream.seek(4)

        with patch("services.malware_scanner.socket.create_connection", return_value=connection):
            result = scanner.scan(stream)

        self.assertTrue(result.clean)
        self.assertEqual(result.status, "clean")
        self.assertEqual(stream.tell(), 4)
        self.assertTrue(connection.sent.startswith(b"zINSTREAM\0"))
        self.assertTrue(connection.sent.endswith(b"\x00\x00\x00\x00"))

    def test_infected_upload_is_rejected_without_exposing_signature(self):
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def settimeout(self, timeout):
                pass

            def sendall(self, payload):
                pass

            def recv(self, size):
                return b"stream: Eicar-Signature FOUND\0"

        scanner = MalwareScanner()
        scanner.backend = "clamav"
        with patch("services.malware_scanner.socket.create_connection", return_value=FakeConnection()):
            result = scanner.scan(io.BytesIO(b"unsafe"))
        self.assertFalse(result.clean)
        self.assertEqual(result.signature, "Eicar-Signature")

        with patch("services.malware_scanner.malware_scanner.scan", return_value=result):
            with self.assertRaisesRegex(HTTPException, "Upload rejected") as raised:
                scan_upload(io.BytesIO(b"unsafe"))
        self.assertEqual(raised.exception.status_code, 422)
        self.assertNotIn("Eicar", raised.exception.detail)

    def test_scanner_outage_fails_closed(self):
        scanner = MalwareScanner()
        scanner.backend = "clamav"
        with patch(
            "services.malware_scanner.socket.create_connection",
            side_effect=TimeoutError,
        ):
            with self.assertRaises(HTTPException) as raised:
                scanner.scan(io.BytesIO(b"upload"))
        self.assertEqual(raised.exception.status_code, 503)

    def test_production_requires_malware_scanning(self):
        source = (REPOSITORY_ROOT / "config" / "settings.py").read_text(encoding="utf-8")
        self.assertIn("MALWARE_SCAN_BACKEND must be 'clamav' in production", source)
        evidence = (REPOSITORY_ROOT / "routes" / "evidence_routes.py").read_text(encoding="utf-8")
        persons = (REPOSITORY_ROOT / "routes" / "person_routes.py").read_text(encoding="utf-8")
        self.assertIn("scan_upload(file.file)", evidence)
        self.assertIn("scan_upload(file.file)", persons)
        self.assertIn('f"Malware scan: {scan_result.status}. "', evidence)
        main = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(
            main.count("malware_scanner.validate_production_access()"),
            2,
        )

    def test_clamav_readiness_uses_ping(self):
        class FakeConnection:
            def __init__(self):
                self.sent = None

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def settimeout(self, timeout):
                pass

            def sendall(self, payload):
                self.sent = payload

            def recv(self, size):
                return b"PONG\0"

        connection = FakeConnection()
        scanner = MalwareScanner()
        scanner.backend = "clamav"
        with patch("services.malware_scanner.socket.create_connection", return_value=connection):
            scanner.validate_production_access()
        self.assertEqual(connection.sent, b"zPING\0")

    def test_cursor_pagination_returns_an_opaque_next_cursor(self):
        base = declarative_base()

        class FeedItem(base):
            __tablename__ = "phase_one_feed_items"
            id = Column(Integer, primary_key=True)

        engine = create_engine("sqlite:///:memory:")
        base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        session.add_all([FeedItem(id=value) for value in range(1, 6)])
        session.commit()

        first_response = Response()
        first_page = paginate_query(
            session.query(FeedItem).order_by(FeedItem.id.desc()),
            PaginationParams(limit=2, offset=0),
            first_response,
            cursor_column=FeedItem.id,
        )
        cursor = first_response.headers["X-Next-Cursor"]
        second_response = Response()
        second_page = paginate_query(
            session.query(FeedItem).order_by(FeedItem.id.desc()),
            PaginationParams(limit=2, offset=0, cursor=cursor),
            second_response,
            cursor_column=FeedItem.id,
        )

        self.assertEqual([item.id for item in first_page], [5, 4])
        self.assertEqual([item.id for item in second_page], [3, 2])
        self.assertNotEqual(cursor, "4")

    def test_legal_hold_and_retention_period_block_disposition(self):
        now = datetime(2026, 10, 16, 12, 0, 0)
        evidence = SimpleNamespace(
            legal_hold=True,
            disposition_status="active",
            retention_until=now - timedelta(days=1),
        )
        self.assertEqual(retention_decision(evidence, now).reason, "legal_hold")
        with self.assertRaises(HTTPException) as held:
            assert_evidence_disposition_allowed(evidence, now)
        self.assertEqual(held.exception.status_code, 409)

        evidence.legal_hold = False
        evidence.retention_until = now + timedelta(days=1)
        self.assertEqual(
            retention_decision(evidence, now).reason,
            "retention_period_active",
        )

    def test_expired_unheld_evidence_is_eligible_for_controlled_disposition(self):
        now = datetime(2026, 10, 16, 12, 0, 0)
        evidence = SimpleNamespace(
            legal_hold=False,
            disposition_status="active",
            retention_until=now - timedelta(seconds=1),
        )
        self.assertTrue(retention_decision(evidence, now).eligible)
        assert_evidence_disposition_allowed(evidence, now)

    def test_retention_endpoint_is_supervisor_only_and_audited(self):
        source = (REPOSITORY_ROOT / "routes" / "evidence_routes.py").read_text(encoding="utf-8")
        self.assertIn('@router.put("/{evidence_id}/retention")', source)
        self.assertIn(
            'require_role("platform_admin", "agency_admin", "supervisor")',
            source,
        )
        self.assertIn('action = "RELEASE_LEGAL_HOLD"', source)
        migration = (
            REPOSITORY_ROOT
            / "migrations"
            / "versions"
            / "a73d11c6402e_add_evidence_retention_controls.py"
        ).read_text(encoding="utf-8")
        self.assertIn('down_revision = "f2cc04888254"', migration)
        self.assertIn("ck_evidence_legal_hold_reason", migration)
        self.assertIn("ix_evidence_retention_disposition", migration)


if __name__ == "__main__":
    unittest.main()
