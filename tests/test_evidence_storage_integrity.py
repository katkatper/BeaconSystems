import io
import tempfile
from pathlib import Path

from PIL import Image

from services.evidence_preview import create_image_preview
from services.object_storage import ObjectStorage, fingerprint_stream


def _local_storage(directory: str) -> ObjectStorage:
    storage = ObjectStorage.__new__(ObjectStorage)
    storage.backend = "local"
    storage.local_root = Path(directory).resolve()
    storage.bucket = ""
    storage.prefix = "beacon"
    storage.kms_key_id = ""
    storage.expected_owner = ""
    storage._s3 = None
    return storage


def test_fingerprint_preserves_stream_position():
    stream = io.BytesIO(b"immutable evidence")
    stream.seek(4)
    digest, size = fingerprint_stream(stream)
    assert stream.tell() == 4
    assert size == len(b"immutable evidence")
    assert len(digest) == 64


def test_local_storage_is_write_once_and_detects_tampering():
    with tempfile.TemporaryDirectory() as directory:
        storage = _local_storage(directory)
        key = storage.create_key(7, "evidence", "photo.jpg")
        stored = storage.put(io.BytesIO(b"original"), key)
        assert storage.verify(key, stored.sha256)
        try:
            storage.put(io.BytesIO(b"replacement"), key)
            raise AssertionError("write-once storage accepted a replacement")
        except FileExistsError:
            pass
        storage.local_path(key).write_bytes(b"tampered")
        assert not storage.verify(key, stored.sha256)


def test_local_archive_and_restore_keep_the_original_bytes_unchanged():
    with tempfile.TemporaryDirectory() as directory:
        storage = _local_storage(directory)
        key = storage.create_key(8, "evidence", "statement.txt")
        stored = storage.put(io.BytesIO(b"unchanged original"), key)
        storage.archive(key, stored.sha256)
        storage.request_restore(key)
        assert storage.restore_ready(key)
        assert storage.local_path(key).read_bytes() == b"unchanged original"
        assert storage.verify(key, stored.sha256)


def test_image_preview_is_bounded_and_original_is_unchanged():
    original = io.BytesIO()
    Image.new("RGB", (1200, 800), "navy").save(original, "PNG")
    original_bytes = original.getvalue()
    preview = create_image_preview(original, "image/png")
    assert preview is not None
    assert original.getvalue() == original_bytes
    with Image.open(preview) as image:
        assert image.format == "JPEG"
        assert image.width <= 512
        assert image.height <= 512
