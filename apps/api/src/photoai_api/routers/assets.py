"""Assets router stub (§6 DELETE /v1/assets/{id})."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.delete("/assets/{asset_id}/stub")
async def stub(asset_id: str):
    return {"asset_id": asset_id, "note": "assets route consolidated for P0"}
