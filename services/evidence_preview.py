from io import BytesIO
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError

PREVIEW_CONTENT_TYPE = "image/jpeg"
PREVIEW_MAX_PIXELS = 40_000_000
PREVIEW_SIZE = (512, 512)


def create_image_preview(stream: BinaryIO, content_type: str | None) -> BytesIO | None:
    """Create a bounded derivative while leaving the immutable original untouched."""
    if not content_type or not content_type.lower().startswith("image/"):
        return None
    position = stream.tell()
    stream.seek(0)
    original_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = PREVIEW_MAX_PIXELS
    try:
        with Image.open(stream) as image:
            image.verify()
        stream.seek(0)
        with Image.open(stream) as image:
            preview = ImageOps.exif_transpose(image).convert("RGB")
            preview.thumbnail(PREVIEW_SIZE)
            output = BytesIO()
            preview.save(output, format="JPEG", quality=82, optimize=True)
            output.seek(0)
            return output
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        return None
    finally:
        Image.MAX_IMAGE_PIXELS = original_limit
        stream.seek(position)
