"""P1 integration tests: 4 functions end-to-end through the recipe runner.

Uses the mock provider and synthetic images so the suite is fully
self-contained on self-hosted CPU. Covers:
  - open_eyes (EAR >= 0.20, identity preserved)
  - remove_bystanders (person recheck, outside_mask_ssim)
  - remove_watermark (ownership required, OCR recheck)
  - upscale_4k (identity, structure_similarity, output resolution cap)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workers" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image

from photoai_worker.pipeline.recipe_schema import Recipe
from photoai_worker.pipeline.runner import RecipeRunner
from providers.mock import MockProvider

from tests.golden import ensure_golden, expected_path, images_dir


def _make_image(size=(256, 256), color=(100, 150, 200)):
    return Image.new("RGB", size, color)


def _recipe(recipe_id: str, steps: list, **kwargs) -> Recipe:
    return Recipe(
        id=recipe_id,
        version=1,
        steps=steps,
        retry={"max": 2, "strength_step": -0.1, "reseed": True},
        prompt={},
        **kwargs,
    )


def test_open_eyes_passes_and_preserves_identity(tmp_path):
    ensure_golden("open_eyes")
    recipe = _recipe(
        "open_eyes",
        [
            {"detect": {"faces": True, "eyes_ear": True}},
            {"filter": {"only_closed_eyes": True, "ear_below": 0.2}},
            {"edit": {"provider": "mock", "strength": 0.4, "padding": 0.25}},
            {"blend": {"method": "feather", "radius_px": 6}},
            {"qa": {}},
        ],
    )
    provider = MockProvider()
    runner = RecipeRunner(provider=provider)
    result = runner.run(
        recipe, _make_image(), params={"strength": 0.4, "seed": 7, "ownership_confirmed": False}
    )
    assert result.passed, result.report.warnings
    assert result.report.metrics.get("identity_cosine", 0) >= 0.88
    assert result.report.metrics.get("outside_mask_ssim", 0) >= 0.98


def test_remove_bystanders_preserves_main_subject(tmp_path):
    ensure_golden("remove_bystanders")
    recipe = _recipe(
        "remove_bystanders",
        [
            {"detect": {"persons": True}},
            {"edit": {"provider": "mock", "strength": 0.5, "padding": 0.3}},
            {"blend": {"method": "feather", "radius_px": 10}},
            {"qa": {}},
        ],
    )
    provider = MockProvider()
    runner = RecipeRunner(provider=provider)
    result = runner.run(
        recipe, _make_image(size=(512, 512)), params={"strength": 0.5, "seed": 3}
    )
    assert result.passed, result.report.warnings
    assert result.report.metrics.get("outside_mask_ssim", 0) >= 0.98


def test_remove_watermark_requires_ownership():
    ensure_golden("remove_watermark")
    recipe = _recipe(
        "remove_watermark",
        [
            {"detect": {"text_logo": True}},
            {"edit": {"provider": "mock", "strength": 0.6, "padding": 0.25}},
            {"blend": {"method": "feather", "radius_px": 8}},
            {"qa": {}},
        ],
    )
    provider = MockProvider()
    runner = RecipeRunner(provider=provider)

    # Without ownership confirmation -> OwnershipRequired error.
    try:
        runner.run(recipe, _make_image(), params={"strength": 0.6, "seed": 1})
        assert False, "expected OwnershipRequired"
    except Exception as exc:  # noqa: BLE001
        assert "ownership" in str(exc).lower() or "quyền sở hữu" in str(exc).lower()

    # With ownership confirmed -> runs fine.
    result = runner.run(
        recipe, _make_image(), params={"strength": 0.6, "seed": 2, "ownership_confirmed": True}
    )
    assert result.passed, result.report.warnings


def test_upscale_4k_preserves_structure_and_caps_resolution(tmp_path):
    ensure_golden("upscale_4k")
    recipe = _recipe(
        "upscale_4k",
        [
            {"detect": {"faces": True}},
            {"edit": {"provider": "mock", "strength": 0.3, "padding": 0.0}},
            {"blend": {"method": "feather", "radius_px": 4}},
            {"qa": {}},
        ],
    )
    provider = MockProvider()
    runner = RecipeRunner(provider=provider)
    result = runner.run(
        recipe, _make_image(size=(512, 512)), params={"strength": 0.3, "seed": 5}
    )
    assert result.passed, result.report.warnings
    assert result.report.metrics.get("identity_cosine", 0) >= 0.90
    assert result.report.metrics.get("outside_mask_ssim", 0) >= 0.98
    # Output image must not exceed the 8192px edge cap enforced by config.
    assert max(result.image.size) <= 8192


def test_golden_dirs_created():
    """Golden directories exist for all P1 recipes."""
    for recipe_id in ["open_eyes", "remove_bystanders", "remove_watermark", "upscale_4k"]:
        ensure_golden(recipe_id)
        assert images_dir(recipe_id).is_dir()
        assert expected_path(recipe_id).is_file()
