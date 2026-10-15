"""``provider_calls`` table (design \u00a74): cost and latency accounting."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_column, new_id


class ProviderCallRow(Base):
    __tablename__ = "provider_calls"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("prc"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
