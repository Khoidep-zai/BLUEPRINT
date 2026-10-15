"""Recipe catalog endpoints: the 10 editing functions."""
from __future__ import annotations

from fastapi import APIRouter

from ..services.processing import ProcessingService

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("")
def list_recipes() -> dict:
    """List every available editing function with its metadata."""
    service = ProcessingService()
    return {"recipes": [info.to_dict() for info in service.list_recipes()]}


@router.get("/{recipe_id}")
def get_recipe(recipe_id: str) -> dict:
    """Return one editing function's metadata."""
    return ProcessingService().get_info(recipe_id).to_dict()
