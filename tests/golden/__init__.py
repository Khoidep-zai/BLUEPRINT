"""Golden-set skeleton for P1 functions.

Structure per recipe:
  tests/golden/<recipe_id>/
    images/          # synthetic / real test images
    expected.json    # {image_name: {metric: min|max|value, ...}}

Golden images are intentionally synthetic (generated in tests) so the suite is
self-contained and runnable on self-hosted CPU without downloading models.
"""
from __future__ import annotations

import json
from pathlib import Path

GOLDEN_ROOT = Path(__file__).resolve().parent.parent / "golden"

P1_RECIPES = ["open_eyes", "remove_bystanders", "remove_watermark", "upscale_4k"]


def golden_dir(recipe_id: str) -> Path:
    return GOLDEN_ROOT / recipe_id


def images_dir(recipe_id: str) -> Path:
    return golden_dir(recipe_id) / "images"


def expected_path(recipe_id: str) -> Path:
    return golden_dir(recipe_id) / "expected.json"


def ensure_golden(recipe_id: str) -> None:
    """Create golden directories for a recipe if missing."""
    d = images_dir(recipe_id)
    d.mkdir(parents=True, exist_ok=True)
    if not expected_path(recipe_id).exists():
        expected_path(recipe_id).write_text("{}\n", encoding="utf-8")


def init_all_golden() -> None:
    for recipe_id in P1_RECIPES:
        ensure_golden(recipe_id)
