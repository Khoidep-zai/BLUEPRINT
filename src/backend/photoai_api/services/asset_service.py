"""Asset service (P0 task 6)."""
from __future__ import annotations

from typing import Optional

from ..store import default_store


class AssetService:
    def __init__(self, store=None) -> None:
        self.store = store or default_store

    def create(self, **kwargs):
        return self.store.create_asset(**kwargs)

    def get(self, asset_id: str):
        return self.store.get_asset(asset_id)
