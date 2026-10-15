"""Pydantic request/response schemas (§6 API contract)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    filename: str
    mime: str
    size: int


class PresignResponse(BaseModel):
    asset_id: str
    upload_url: str
    expires_in: int


class AssetComplete(BaseModel):
    asset_id: str


class JobCreate(BaseModel):
    recipe_id: str
    input_asset_id: str
    mask_asset_id: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    ownership_confirmed: bool = False
    idempotency_key: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    result_asset_id: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    qa_report: Optional[dict[str, Any]] = None
    created_at: datetime
    finished_at: Optional[datetime] = None


class JobListItem(BaseModel):
    job_id: str
    recipe_id: str
    status: str
    created_at: datetime


class FeedbackCreate(BaseModel):
    job_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
