"""Pydantic models for QA reports (replaces SQLAlchemy ``qa_reports`` table)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import new_id, utc_now


class QaReport(BaseModel):
    """In-memory QA report record, one row per attempt."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: new_id("qa"))
    job_id: str
    attempt: int = 1
    metrics: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    passed: bool = False
    created_at: datetime = Field(default_factory=utc_now)
