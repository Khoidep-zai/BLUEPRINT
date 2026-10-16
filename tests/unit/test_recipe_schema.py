"""Recipe schema + loader tests (design §2 recipe_schema.py, §4)."""
from __future__ import annotations

from photoai.engine.loader import load_all, load_recipe_by_id


def test_loads_exactly_ten_recipes():
    recipes = load_all()
    assert len(recipes) == 10
    assert "upscale_4k" in recipes and "product_studio" in recipes


def test_watermark_is_the_only_ownership_recipe():
    owning = sorted(rid for rid, recipe in load_all().items() if recipe.ownership_required)
    assert owning == ["remove_watermark"]


def test_every_recipe_has_an_editor_and_a_qa_gate():
    for rid, recipe in load_all().items():
        assert recipe.edit.editor, f"{rid} has no editor"
        gates = recipe.qa.model_dump(exclude_none=True)
        assert gates, f"{rid} has no QA gate"


def test_recipe_accessors_return_typed_blocks():
    recipe = load_recipe_by_id("open_eyes")
    assert recipe.detect.faces is True
    assert recipe.filter.only_closed_eyes is True
    assert recipe.qa.ear_min == 0.22
    assert recipe.blend.method == "poisson"


def test_prompt_paths_point_at_markdown_files():
    for rid, recipe in load_all().items():
        assert recipe.prompt.vi.endswith(f"{rid}.vi.md")
        assert recipe.prompt.en.endswith(f"{rid}.en.md")
