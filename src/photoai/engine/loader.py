"""Load and validate recipe YAML files (design §2)."""
from __future__ import annotations

import os
from typing import Dict

import yaml

from photoai.config import RECIPES_DIR
from photoai.engine.recipe_schema import Recipe

DEFAULT_RECIPES_DIR = str(RECIPES_DIR)


def load_recipe(path: str) -> Recipe:
    """Load a single recipe YAML file and validate it."""
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Recipe(**data)


def load_recipe_by_id(recipe_id: str, recipes_dir: str | os.PathLike[str] | None = None) -> Recipe:
    base = str(recipes_dir or RECIPES_DIR)
    return load_recipe(os.path.join(base, f"{recipe_id}.yaml"))


def load_all(recipes_dir: str | os.PathLike[str] | None = None) -> Dict[str, Recipe]:
    """Return every recipe in ``recipes_dir`` keyed by ``recipe.id``."""
    base = str(recipes_dir or RECIPES_DIR)
    recipes: Dict[str, Recipe] = {}
    if not os.path.isdir(base):
        return recipes
    for name in sorted(os.listdir(base)):
        if name.endswith((".yaml", ".yml")):
            recipe = load_recipe(os.path.join(base, name))
            recipes[recipe.id] = recipe
    return recipes
