"""SQLAlchemy declarative base and shared column helpers (design \u00a74)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all models."""


def new_id(prefix: str) -> str:
    """Generate a short, prefixed identifier (e.g. ``ast_1a2b3c4d``)."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def created_at_column() -> Mapped[datetime]:
    """A timezone-aware ``created_at`` column with a server default."""
    return mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
