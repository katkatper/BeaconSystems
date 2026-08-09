from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException

from config.settings import MAX_UPLOAD_BYTES


IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    "image/webp": (b"RIFF",),
}
BLOCKED_EXECUTABLE_SIGNATURES = (b"MZ", b"\x7fELF", b"#!")


def _stream_size(stream: BinaryIO) -> int:
    position = stream.tell()
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(position)
    return size


def validate_upload(
    stream: BinaryIO,
    *,
    file_name: str,
    content_type: str | None,
    allowed_content_types: set[str] | None = None,
) -> None:
    safe_name = Path(file_name).name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Upload requires a valid file name")

    if _stream_size(stream) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds the configured size limit")

    if allowed_content_types and content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Unsupported upload content type")

    position = stream.tell()
    stream.seek(0)
    header = stream.read(16)
    stream.seek(position)

    if not header:
        raise HTTPException(status_code=400, detail="Empty files cannot be uploaded")
    if any(header.startswith(signature) for signature in BLOCKED_EXECUTABLE_SIGNATURES):
        raise HTTPException(status_code=400, detail="Executable files cannot be uploaded")

    if content_type in IMAGE_SIGNATURES:
        signatures = IMAGE_SIGNATURES[content_type]
        signature_matches = any(header.startswith(signature) for signature in signatures)
        if content_type == "image/webp":
            signature_matches = header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        if not signature_matches:
            raise HTTPException(status_code=400, detail="File contents do not match the declared image type")
