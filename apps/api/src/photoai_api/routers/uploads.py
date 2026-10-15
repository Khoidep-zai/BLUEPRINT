"""Uploads router stub (§6: presign, complete, delete)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/uploads/stub")
async def stub():
    return {"note": "uploads routes consolidated in jobs router for P0"}
