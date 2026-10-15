"""Recipes router stub (§6 GET /v1/recipes)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/recipes/stub")
async def stub():
    return {"note": "recipes route consolidated in jobs router for P0"}
