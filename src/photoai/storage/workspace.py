"""Local workspace cache with TTL cleanup."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from photoai.config import CACHE_TTL_HOURS, WORKSPACE_CACHE, WORKSPACE_RESULTS, WORKSPACE_UPLOADS, ensure_workspace_dirs


def store_upload(data: bytes, name: str) -> Path:
    ensure_workspace_dirs()
    path = WORKSPACE_UPLOADS / name
    path.write_bytes(data)
    return path


def purge_expired_cache() -> int:
    """Remove cache files older than TTL; returns count removed."""
    ensure_workspace_dirs()
    cutoff = time.time() - CACHE_TTL_HOURS * 3600
    removed = 0
    for root in (WORKSPACE_CACHE, WORKSPACE_RESULTS):
        for item in root.glob("**/*"):
            if item.is_file() and item.stat().st_mtime < cutoff:
                item.unlink(missing_ok=True)
                removed += 1
    return removed


def clear_cache_dir() -> None:
    if WORKSPACE_CACHE.exists():
        shutil.rmtree(WORKSPACE_CACHE, ignore_errors=True)
    WORKSPACE_CACHE.mkdir(parents=True, exist_ok=True)
