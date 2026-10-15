"""Asset repository."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Asset, new_id


class AssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        kind: str,
        storage_key: str,
        mime: str,
        user_id: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        sha256: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        asset_id: Optional[str] = None,
    ) -> Asset:
        asset = Asset(
            id=asset_id or new_id("ast"),
            user_id=user_id,
            kind=kind,
            storage_key=storage_key,
            mime=mime,
            width=width,
            height=height,
            sha256=sha256,
            expires_at=expires_at,
        )
        self.db.add(asset)
        self.db.flush()
        self.db.refresh(asset)
        return asset

    def get(self, asset_id: str) -> Optional[Asset]:
        return self.db.get(Asset, asset_id)
