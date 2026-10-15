"""Asset service (P0 task 6)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..repositories.asset_repository import AssetRepository


class AssetService:
    def __init__(self, db: Session) -> None:
        self.repo = AssetRepository(db)

    def create(self, **kwargs):
        return self.repo.create(**kwargs)

    def get(self, asset_id: str):
        return self.repo.get(asset_id)
