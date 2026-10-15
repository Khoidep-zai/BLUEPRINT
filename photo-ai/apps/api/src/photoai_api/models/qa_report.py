"""``qa_reports`` table (design \u00a74): one row per attempt."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_column, new_id
from .types import JSONVariant


class QaReportRow(Base):
    __tablename__ = "qa_reports"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("qa"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    thresholds: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
