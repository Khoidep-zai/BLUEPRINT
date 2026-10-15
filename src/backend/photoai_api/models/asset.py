"""Pydantic models for assets (replaces SQLAlchemy ``assets`` table)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import new_id, utc_now


class Asset(BaseModel):
    """In-memory asset record. Originals are immutable."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: new_id("ast"))
    user_id: Optional[str] = None
    # kind: original | result | mask
    kind: str
    storage_key: str
    mime: str
    width: Optional[int] = None
    height: Optional[int] = None
    sha256: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
