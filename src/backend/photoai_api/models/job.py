"""Pydantic models for jobs (replaces SQLAlchemy ``jobs`` table)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import new_id, utc_now


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    QA = "qa"
    DONE = "done"
    FAILED = "failed"


class Job(BaseModel):
    """In-memory job record."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: new_id("job"))
    user_id: Optional[str] = None
    recipe_id: str
    input_asset_id: str
    mask_asset_id: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    status: str = JobStatus.QUEUED.value
    idempotency_key: Optional[str] = None
    ownership_confirmed: bool = False
    result_asset_id: Optional[str] = None
    warnings: list = Field(default_factory=list)
    error_code: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    finished_at: Optional[datetime] = None
