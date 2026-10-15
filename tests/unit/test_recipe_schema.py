import os
import yaml
from photoai_worker.pipeline.recipe_schema import Recipe


def test_recipe_parser():
    """Test recipe YAML parsing."""
    recipe_path = os.path.join(os.path.dirname(__file__), "..", "..", "recipes", "open_eyes.yaml")
    with open(recipe_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    recipe = Recipe(**data)
    assert recipe.id == "open_eyes"
    assert recipe.version == 1
    assert len(recipe.steps) == 5
    assert recipe.retry.max == 2
    assert recipe.qa.ear_min == 0.2
