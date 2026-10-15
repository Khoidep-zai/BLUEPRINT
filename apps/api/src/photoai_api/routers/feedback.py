"""Feedback router stub (§6 POST /v1/feedback)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/feedback/stub")
async def stub():
    return {"note": "feedback route consolidated for P0"}
