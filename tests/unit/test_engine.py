"""Engine tests: immutability, VRAM, the 7-stage runner, filters and retry."""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from photoai.engine.context import PipelineContext
from photoai.engine.loader import load_recipe_by_id
from photoai.engine.recipe_schema import Recipe, RetryConfig
from photoai.engine.retry import retry_params
from photoai.engine.runner import RecipeRunner
from photoai.engine.steps import s1_ingest
from photoai.engine.vram_manager import VRAMModelManager
from photoai.errors import NoClosedEyesError, OwnershipError


def test_ingest_locks_original_pixels(synthetic_portrait):
    context = PipelineContext(image=synthetic_portrait)
    s1_ingest.run(context)
    assert context.original_rgb is not None
    assert context.original_rgb.flags.writeable is False
    with pytest.raises(ValueError):
        context.original_rgb[0, 0, 0] = 0


def test_vram_manager_evicts_oldest():
    manager = VRAMModelManager()
    manager.clear_all()
    manager.max_active_models = 2

    manager.get_model("a", lambda: {"name": "a"})
    manager.get_model("b", lambda: {"name": "b"})
    manager.get_model("c", lambda: {"name": "c"})

    assert "a" not in manager.loaded_models
    assert "b" in manager.loaded_models and "c" in manager.loaded_models


def test_vram_manager_reuses_cached_model():
    manager = VRAMModelManager()
    manager.clear_all()
    calls = []
    manager.get_model("x", lambda: (calls.append(1), {"n": 1})[1])
    manager.get_model("x", lambda: (calls.append(1), {"n": 1})[1])
    assert calls == [1]


def test_runner_runs_all_seven_stages(synthetic_portrait):
    recipe = Recipe(
        id="upscale_4k",
        version=1,
        steps=[
            {"detect": {}},
            {"edit": {"editor": "upscale", "scale": 2.0}},
            {"blend": {"method": "none"}},
            {"qa": {"structure_similarity_min": 0.5}},
        ],
        retry=RetryConfig(max=0),
    )
    result = RecipeRunner().run(recipe, synthetic_portrait)
    assert result.image.size[0] >= synthetic_portrait.size[0]
    names = [log.name for log in result.context.step_log]
    for stage in ("ingest", "detect", "roi_mask", "edit", "blend", "qa"):
        assert stage in names


def test_open_eyes_filter_rejects_open_eyes(synthetic_portrait):
    recipe = load_recipe_by_id("open_eyes")
    with pytest.raises(NoClosedEyesError):
        RecipeRunner().run(recipe, synthetic_portrait, params={"left_ear": 0.30, "right_ear": 0.30})


def test_watermark_recipe_requires_ownership(synthetic_portrait):
    recipe = load_recipe_by_id("remove_watermark")
    with pytest.raises(OwnershipError):
        RecipeRunner().run(recipe, synthetic_portrait)
    # With confirmation it runs.
    result = RecipeRunner().run(recipe, synthetic_portrait, params={"ownership_confirmed": True})
    assert result.context.step_log


def test_retry_params_lower_strength_and_reseed():
    config = RetryConfig(max=2, strength_step=-0.1, reseed=True)
    strength, seed = retry_params(config, base_strength=0.5, base_seed=42, attempt=2)
    assert strength == pytest.approx(0.3)
    assert seed == 44


def test_runner_returns_best_effort_on_unreachable_gate(synthetic_portrait):
    recipe = Recipe(
        id="skin_retouch",
        version=1,
        steps=[
            {"detect": {"faces": True}},
            {"edit": {"editor": "skin", "strength": 0.4}},
            {"blend": {"method": "feather", "radius_px": 4}},
            {"qa": {"tsunami_min": 1.0}},  # a gate no metric can satisfy
        ],
        retry=RetryConfig(max=2),
    )
    result = RecipeRunner().run(recipe, synthetic_portrait)
    assert result.best_effort is True
    assert result.report.passed is False
    assert any("Classical CV" in w for w in result.context.warnings)
