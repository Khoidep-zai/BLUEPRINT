"""Image encoding helpers for the API layer."""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image


def decode_image(data: bytes) -> Image.Image:
    """Decode upload bytes into an RGB ``PIL.Image``.

    Raises ``ValueError`` when the payload is not a readable image.
    """
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except Exception as exc:  # noqa: BLE001 - normalised to a domain error
        raise ValueError("Không đọc được ảnh đầu vào.") from exc
    return image.convert("RGB")


def encode_png(image: Image.Image) -> bytes:
    """Encode a PIL image as lossless PNG bytes."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data`` (asset integrity check)."""
    return hashlib.sha256(data).hexdigest()
