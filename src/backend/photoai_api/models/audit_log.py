"""Pydantic models for audit logs (replaces SQLAlchemy ``audit_logs`` table)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import new_id, utc_now


class AuditLog(BaseModel):
    """In-memory audit log record. IP is hashed, never stored raw."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: new_id("aud"))
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    action: str
    detail: dict[str, Any] = Field(default_factory=dict)
    ip_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
