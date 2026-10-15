"""Shared helpers for in-memory Pydantic models (replaces SQLAlchemy base)."""
from __future__ import annotations

import uuid
from datetime import datetime


def new_id(prefix: str) -> str:
    """Generate a short, prefixed identifier (e.g. ``ast_1a2b3c4d``)."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now()
