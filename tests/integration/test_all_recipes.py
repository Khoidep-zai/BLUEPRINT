"""Every recipe in ``recipes/`` must run end-to-end through the runner.

These tests verify the pipeline *contract* for all 10 functions: recipes load,
detect/filter/edit/blend/qa steps execute, detection config keys are honoured,
and the runner always returns a measured QA report (pass or documented
best-effort) instead of crashing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _path in (str(ROOT), str(ROOT / "workers" / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pytest  # noqa: E402

from photoai_worker.pipeline.errors import NoClosedEyes, OwnershipRequired  # noqa: E402
from photoai_worker.pipeline.loader import load_all, load_recipe  # noqa: E402
from photoai_worker.pipeline.runner import RecipeRunner  # noqa: E402
from providers.mock import MockProvider  # noqa: E402

from tests.golden.generate import ALL_RECIPES, _make_image  # noqa: E402

RECIPES_DIR = ROOT / "recipes"


def _run(recipe_id: str, params: dict | None = None):
    recipe = load_recipe(str(RECIPES_DIR / f"{recipe_id}.yaml"))
    runner = RecipeRunner(provider=MockProvider())
    return runner.run(recipe, _make_image(recipe_id, 0), params=params or {})


def test_all_ten_recipes_load():
    recipes = load_all(str(RECIPES_DIR))
    assert set(recipes) == set(ALL_RECIPES)
    assert len(recipes) == 10


@pytest.mark.parametrize("recipe_id", ALL_RECIPES)
def test_recipe_runs_end_to_end(recipe_id):
    params = {"ownership_confirmed": True} if recipe_id == "remove_watermark" else {}
    result = _run(recipe_id, params)
    assert result.status == "done"
    assert result.report is not None
    # Every run must carry measured pixel metrics, never an empty report.
    assert "outside_mask_ssim" in result.report.metrics
    assert "identity_cosine" in result.report.metrics
    assert "clip_ratio" in result.report.metrics
    if not result.passed:
        # Honest best-effort path: warnings explain what failed.
        assert result.best_effort is True
        assert result.warnings


def test_watermark_recipe_requires_ownership():
    with pytest.raises(OwnershipRequired):
        _run("remove_watermark")
    result = _run("remove_watermark", {"ownership_confirmed": True})
    assert result.status == "done"


def test_open_eyes_filter_rejects_already_open_eyes():
    with pytest.raises(NoClosedEyes):
        _run("open_eyes", {"left_ear": 0.4, "right_ear": 0.4})


def test_open_eyes_gate_passes_when_model_reports_open_eyes():
    """The ear gate is measured on the edited result: when the (simulated)
    landmark model reports open eyes after the edit, the function passes."""
    result = _run("open_eyes", {"post_left_ear": 0.3, "post_right_ear": 0.3})
    assert result.passed is True
    assert result.report.metrics["ear"] >= 0.20


def test_remove_bystanders_detect_person_key_is_honoured():
    """Regression: the YAML uses ``person: true`` (singular); the detect step
    must run person detection, not silently skip it."""
    result = _run("remove_bystanders")
    assert "persons" in result.context.detections
    assert "main_person" in result.context.detections


def test_upscale_recipe_produces_larger_output_within_cap():
    result = _run("upscale_4k")
    original_size = result.context.original.size
    assert result.image.size[0] > original_size[0]
    assert max(result.image.size) <= 8192
