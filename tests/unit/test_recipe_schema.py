"""Tests for recipe_schema.py (P0 §3)."""
from pathlib import Path

from photoai_worker.pipeline.recipe_schema import Recipe


def test_load_sample_recipe(tmp_path):
    p = tmp_path / "open_eyes.yaml"
    p.write_text(
        "id: open_eyes\nversion: 1\nsteps:\n  - detect: { faces: true }\nqa: {}\nretry: { max: 2 }\nprompt: { vi: a.vi.md, en: a.en.md }\n",
        encoding="utf-8",
    )
    recipe = Recipe.load(p)
    assert recipe.id == "open_eyes"
    assert recipe.version == 1
    assert len(recipe.steps) == 1
    assert recipe.retry.max == 2
    assert recipe.prompt["vi"] == "a.vi.md"


def test_rejects_bad_id(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("id: bad id!\nversion: 1\nsteps: []\nqa: {}\nretry: { max: 2 }\nprompt: {}\n", encoding="utf-8")
    try:
        Recipe.load(p)
    except Exception as exc:
        assert "identifier" in str(exc)
    else:
        raise AssertionError("expected validation error for invalid id")


def test_defaults():
    r = Recipe(id="test_recipe")
    assert r.version == 1
    assert r.steps == []
    assert r.retry.max == 2
