import ast
import io
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException, Response
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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

    def test_phase_one_indexes_follow_phase_zero_head(self):
        source = (REPOSITORY_ROOT / "migrations" / "versions" / "0a6f708294b1_add_phase_one_query_indexes.py").read_text(encoding="utf-8")
        self.assertIn('down_revision = "fe5f60718293"', source)
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


if __name__ == "__main__":
    unittest.main()
