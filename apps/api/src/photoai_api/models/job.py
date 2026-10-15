"""``jobs`` table (design \u00a74). Status: queued/running/qa/done/failed."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_column, new_id
from .types import JSONVariant


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    QA = "qa"
    DONE = "done"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("job"))
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recipe_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_registry.id"), nullable=False, index=True
    )
    input_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=False)
    mask_asset_id: Mapped[Optional[str]] = mapped_column(ForeignKey("assets.id"), nullable=True)
    params: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    status: Mapped[str] = mapped_column(
        String(16), default=JobStatus.QUEUED.value, nullable=False, index=True
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True
    )
    ownership_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    result_asset_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("assets.id"), nullable=True
    )
    warnings: Mapped[list] = mapped_column(JSONVariant, default=list)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = created_at_column()
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
