import hashlib
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from config.aws_config import get_s3_client
from config.settings import (
    OBJECT_STORAGE_BACKEND,
    OBJECT_STORAGE_BUCKET,
    OBJECT_STORAGE_LOCAL_ROOT,
    OBJECT_STORAGE_PREFIX,
    OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS,
)


_SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass(frozen=True)
class StoredObject:
    key: str
    sha256: str


class ObjectStorage:
    """Tenant-scoped storage with a local development and S3 production backend."""

    def __init__(self):
        self.backend = OBJECT_STORAGE_BACKEND
        self.local_root = Path(OBJECT_STORAGE_LOCAL_ROOT).resolve()
        self.bucket = OBJECT_STORAGE_BUCKET
        self.prefix = OBJECT_STORAGE_PREFIX
        self._s3 = get_s3_client() if self.backend == "s3" else None

    @staticmethod
    def _segment(value: str | int) -> str:
        cleaned = _SAFE_SEGMENT.sub("-", str(value)).strip(".-")
        if not cleaned:
            raise ValueError("Storage key segment cannot be empty")
        return cleaned

    def create_key(self, agency_id: int, category: str, file_name: str) -> str:
        safe_name = Path(file_name).name
        extension = Path(safe_name).suffix.lower()
        parts = [
            self.prefix,
            f"agency-{self._segment(agency_id)}",
            self._segment(category),
            f"{uuid4().hex}{extension}",
        ]
        return "/".join(part for part in parts if part)

    def put(self, stream: BinaryIO, key: str, content_type: str | None = None) -> StoredObject:
        digest = hashlib.sha256()

        if self.backend == "s3":
            from tempfile import SpooledTemporaryFile

            with SpooledTemporaryFile(max_size=8 * 1024 * 1024) as buffered:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    buffered.write(chunk)
                buffered.seek(0)
                extra = {"ServerSideEncryption": "AES256"}
                if content_type:
                    extra["ContentType"] = content_type
                self._s3.upload_fileobj(buffered, self.bucket, key, ExtraArgs=extra)
        elif self.backend == "local":
            target = self.local_path(key)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as output:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
        else:
            raise RuntimeError(f"Unsupported object storage backend: {self.backend}")

        return StoredObject(key=key, sha256=digest.hexdigest())

    def local_path(self, key: str) -> Path:
        target = (self.local_root / key).resolve()
        if self.local_root != target and self.local_root not in target.parents:
            raise ValueError("Storage key escapes the configured local root")
        return target

    def signed_url(self, key: str, download_name: str | None = None) -> str:
        if self.backend != "s3":
            raise RuntimeError("Signed URLs are available only for S3 storage")
        params = {"Bucket": self.bucket, "Key": key}
        if download_name:
            content_type = mimetypes.guess_type(download_name)[0] or "application/octet-stream"
            params["ResponseContentType"] = content_type
            params["ResponseContentDisposition"] = f'inline; filename="{Path(download_name).name}"'
        return self._s3.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS,
        )


object_storage = ObjectStorage()
