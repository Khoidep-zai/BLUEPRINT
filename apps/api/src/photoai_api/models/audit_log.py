"""``audit_logs`` table (design \u00a74). Mandatory for ``remove_watermark``."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_column, new_id
from .types import JSONVariant


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("aud"))
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    # IP is hashed, never stored raw (design \u00a78).
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = created_at_column()
