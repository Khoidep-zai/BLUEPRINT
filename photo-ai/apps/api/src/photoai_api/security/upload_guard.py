"""Upload validation helpers (design \u00a78)."""
from __future__ import annotations

from typing import Tuple


def validate_file(filename: str, mime: str, size: int) -> Tuple[bool, str]:
    """Basic upload guard: whitelist types and sane size limit.

    The limit here is intentionally conservative for P0; it will be tuned in
    later phases.
    """
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if mime.lower() not in allowed:
        return False, "INVALID_FILE_TYPE"
    if size < 1:
        return False, "IMAGE_TOO_SMALL"
    if size > 20 * 1024 * 1024:  # 20MB
        return False, "IMAGE_TOO_LARGE"
    return True, "ok"
