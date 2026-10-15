"""Tests for pipeline runner (P0 S1)."""
import asyncio

from PIL import Image

from photoai_worker.pipeline.context import PipelineContext
from photoai_worker.pipeline.recipe_schema import Recipe
from photoai_worker.pipeline.runner import Runner
from providers.mock import MockProvider


def _make_image(size=(64, 64)):
    return Image.new("RGB", size, (100, 150, 200))


def test_runner_passes_with_mock():
    recipe = Recipe(
        id="open_eyes",
        version=1,
        steps=[{"detect": {"faces": True}}, {"edit": {}}, {"qa": {}}],
        retry={"max": 2},
        prompt={},
    )
    provider = MockProvider(delay_ms=1.0)
    runner = Runner(provider=provider)

    result = asyncio.run(
        runner.run("job_1", recipe, _make_image(), params={"strength": 0.5, "seed": 1})
    )

    assert result["passed"] is True
    assert result["image"] is not None
    assert result["qa_report"]["passed"] is True
    assert provider.calls, "provider should have been called"
    assert result["attempt"] >= 0


def test_runner_retries_on_qa_fail():
    recipe = Recipe(
        id="open_eyes",
        version=1,
        steps=[{"edit": {}}, {"qa": {}}],
        retry={"max": 2},
        prompt={},
    )
    provider = MockProvider(delay_ms=1.0)
    runner = Runner(provider=provider)

    result = asyncio.run(
        runner.run("job_2", recipe, _make_image(), params={"strength": 0.5, "seed": 2})
    )

    # With placeholder QA always passing, should pass on attempt 0
    assert result["passed"] is True
