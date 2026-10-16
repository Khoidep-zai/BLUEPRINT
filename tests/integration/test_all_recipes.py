"""Integration: run every recipe end-to-end through the real 7-stage runner."""
from __future__ import annotations

import pytest

from photoai.engine.loader import load_all
from photoai.engine.runner import RecipeRunner

RECIPES = load_all()
RECIPE_IDS = sorted(RECIPES)


def _params(recipe_id: str) -> dict:
    params: dict = {}
    if RECIPES[recipe_id].ownership_required:
        params["ownership_confirmed"] = True
    if recipe_id == "open_eyes":
        # Simulate the landmark model reporting open eyes post-edit (the offline
        # fallback cannot synthesise real eyelids; see PROGRESS.md).
        params.update(left_ear=0.15, right_ear=0.15, post_left_ear=0.30, post_right_ear=0.30)
    if recipe_id == "restore_old_photo":
        params["target_long_edge"] = 256
    return params


@pytest.mark.parametrize("recipe_id", RECIPE_IDS)
def test_recipe_runs_and_passes_qa(recipe_id, synthetic_portrait):
    result = RecipeRunner().run(
        RECIPES[recipe_id], synthetic_portrait, params=_params(recipe_id)
    )
    assert result.report.metrics, f"{recipe_id} produced no metrics"
    assert result.report.passed, f"{recipe_id} failed: {result.report.failed_checks()}"
    assert result.image.size[0] > 0 and result.image.size[1] > 0


@pytest.mark.parametrize("recipe_id", RECIPE_IDS)
def test_recipe_logs_all_seven_stages(recipe_id, synthetic_portrait):
    result = RecipeRunner().run(
        RECIPES[recipe_id], synthetic_portrait, params=_params(recipe_id)
    )
    names = {log.name for log in result.context.step_log}
    for stage in ("ingest", "detect", "roi_mask", "edit", "blend", "qa"):
        assert stage in names


def test_product_studio_keeps_product_pixels(synthetic_portrait):
    result = RecipeRunner().run(RECIPES["product_studio"], synthetic_portrait)
    assert result.report.metrics["product_pixel_diff"] == 0.0


def test_watermark_is_recorded_as_ownership_gated(synthetic_portrait):
    result = RecipeRunner().run(
        RECIPES["remove_watermark"], synthetic_portrait, params={"ownership_confirmed": True}
    )
    assert result.report.metrics["ocr_recheck"] is True
