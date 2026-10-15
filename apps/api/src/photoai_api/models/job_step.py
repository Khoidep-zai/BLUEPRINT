"""``job_steps`` table (design \u00a74): detect/filter/edit/blend/qa audit trail."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_column, new_id


class JobStep(Base):
    __tablename__ = "job_steps"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("stp"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = created_at_column()
