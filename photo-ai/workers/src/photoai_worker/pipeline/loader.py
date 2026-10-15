"""Load recipe YAML files into :class:`Recipe` objects."""
import os
from typing import Dict, List

import yaml

from .recipe_schema import Recipe

DEFAULT_RECIPES_DIR = os.environ.get(
    "PHOTOAI_RECIPES_DIR",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "recipes")
    ),
)


def load_recipe(path: str) -> Recipe:
    """Load a single recipe from a YAML file path."""
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Recipe(**data)


def load_recipe_by_id(recipe_id: str, recipes_dir: str = DEFAULT_RECIPES_DIR) -> Recipe:
    """Load a recipe by id from a recipes directory."""
    return load_recipe(os.path.join(recipes_dir, f"{recipe_id}.yaml"))


def load_all(recipes_dir: str = DEFAULT_RECIPES_DIR) -> Dict[str, Recipe]:
    """Load every recipe in a directory, keyed by recipe id."""
    recipes: Dict[str, Recipe] = {}
    if not os.path.isdir(recipes_dir):
        return recipes
    for name in sorted(os.listdir(recipes_dir)):
        if name.endswith((".yaml", ".yml")):
            recipe = load_recipe(os.path.join(recipes_dir, name))
            recipes[recipe.id] = recipe
    return recipes
