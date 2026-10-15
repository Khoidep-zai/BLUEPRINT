"""Pydantic schemas for jobs API (design \u00a76)."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateJobRequest(BaseModel):
    recipe_id: str
    input_asset_id: str
    mask_asset_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    ownership_confirmed: bool = False
    idempotency_key: Optional[str] = None


class CreateJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime


class QaReportSchema(BaseModel):
    passed: bool
    attempt: int
    metrics: Dict[str, Any] = Field(default_factory=dict)
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    warnings: list = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    result_asset_id: Optional[str] = None
    warnings: list = Field(default_factory=list)
    qa_report: Optional[QaReportSchema] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
