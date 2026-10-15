"""Tests for the recipe runner end-to-end with the mock provider (P0 task 5)."""
import numpy as np
import pytest
from PIL import Image

from photoai_worker.pipeline.errors import NoClosedEyes, OwnershipRequired
from photoai_worker.pipeline.loader import load_recipe
from photoai_worker.pipeline.recipe_schema import QAStep, Recipe, RetryConfig
from photoai_worker.pipeline.runner import RecipeRunner
from providers.mock import MockProvider


def _image(size=(96, 96)) -> Image.Image:
    width, height = size
    xs = np.linspace(40, 210, width)
    ys = np.linspace(40, 210, height)
    grid = ((xs[None, :] + ys[:, None]) / 2).astype(np.uint8)
    rgb = np.stack([grid, np.clip(grid.astype(int) + 10, 0, 255).astype(np.uint8), grid], axis=-1)
    return Image.fromarray(rgb, mode="RGB")


def _passing_recipe() -> Recipe:
    """open_eyes structure with thresholds the P0 mock can actually satisfy."""
    return Recipe(
        id="open_eyes",
        version=1,
        steps=[
            {"detect": {"faces": True, "eyes_ear": True}},
            {"filter": {"only_closed_eyes": True, "ear_below": 0.2}},
            {"edit": {"editor": "inpaint", "provider": "mock", "strength": 0.5, "padding": 0.3}},
            {"blend": {"method": "feather", "radius_px": 4}},
            {"qa": {"outside_mask_ssim_min": 0.98, "identity_cosine_min": 0.85, "structure_similarity_min": 0.5}},
        ],
        retry=RetryConfig(max=2, strength_step=-0.1, reseed=True),
    )


def test_runner_passes_with_mock_and_feather_blend():
    runner = RecipeRunner(provider=MockProvider())
    result = runner.run(_passing_recipe(), _image())
    assert result.passed is True
    assert result.status == "done"
    assert result.best_effort is False
    assert result.image.size == (96, 96)
    assert result.report.metrics["outside_mask_ssim"] >= 0.98
    assert result.report.metrics["identity_cosine"] >= 0.85
    assert len(result.context.provider_calls) == 1
    assert result.duration_ms >= 0.0


def test_runner_filter_rejects_open_eyes():
    runner = RecipeRunner(provider=MockProvider())
    # EAR high -> eyes already open -> filter must reject.
    with pytest.raises(NoClosedEyes):
        runner.run(_passing_recipe(), _image(), params={"left_ear": 0.6, "right_ear": 0.6})


def test_runner_best_effort_when_qa_cannot_pass():
    # The real open_eyes recipe demands ear_min 0.2, which the P0 mock cannot
    # produce; the runner must retry and then return a best-effort warning.
    import os

    recipes_dir = os.path.join(os.path.dirname(__file__), "..", "..", "recipes")
    recipe = load_recipe(os.path.join(recipes_dir, "open_eyes.yaml"))
    runner = RecipeRunner(provider=MockProvider())
    result = runner.run(recipe, _image())
    assert result.status == "done"
    assert result.best_effort is True
    assert result.report.passed is False
    assert any("best-effort" in w for w in result.warnings)
    # retry.max=2 -> 3 attempts -> 3 provider calls
    assert len(result.context.provider_calls) == 3


def test_runner_retry_reduces_strength_and_reseeds():
    recipe = _passing_recipe()
    # Force QA to always fail so every attempt runs.
    recipe.steps[-1]["qa"] = {"outside_mask_ssim_min": 1.5}
    runner = RecipeRunner(provider=MockProvider())
    result = runner.run(recipe, _image(), params={"strength": 0.9, "seed": 100})
    strengths = [call["strength"] for call in result.context.provider_calls]
    seeds = [call["seed"] for call in result.context.provider_calls]
    assert strengths == pytest.approx([0.9, 0.8, 0.7])
    assert seeds == [100, 101, 102]


def test_runner_requires_ownership_for_watermark():
    recipe = Recipe(
        id="remove_watermark",
        version=1,
        steps=[{"detect": {}}, {"qa": {}}],
        retry=RetryConfig(max=0),
    )
    runner = RecipeRunner(provider=MockProvider())
    with pytest.raises(OwnershipRequired):
        runner.run(recipe, _image())

    result = runner.run(recipe, _image(), params={"ownership_confirmed": True})
    assert result.status == "done"


def test_runner_no_face_detected_error(monkeypatch):
    from photoai_worker.detectors import face as face_detector
    from photoai_worker.pipeline.errors import NoFaceDetected

    monkeypatch.setattr(face_detector, "detect_faces", lambda image: [])
    runner = RecipeRunner(provider=MockProvider())
    with pytest.raises(NoFaceDetected):
        runner.run(_passing_recipe(), _image())
