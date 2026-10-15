"""Recipe schemas."""
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RecipeSchema(BaseModel):
    id: str
    version: int
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class RecipesResponse(BaseModel):
    recipes: List[RecipeSchema] = Field(default_factory=list)
