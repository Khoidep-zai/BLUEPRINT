"""``recipes_registry`` table synced from ``recipes/`` (design \u00a74)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_column


class RecipeRegistry(Base):
    __tablename__ = "recipes_registry"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # recipe_id
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    yaml_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
