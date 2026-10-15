"""Recipe runner (AGENT_SKILLS S1).

Executes a recipe as ``detect -> filter -> edit -> blend -> qa`` with retry:

* QA pass -> status ``done``.
* QA fail -> retry up to ``retry.max`` (lower strength, new seed).
* Still failing -> return the best-effort result with ``warnings`` (design §2.2).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from PIL import Image

from ..qa.report import QaReport, best_effort_report
from .context import JobContext
from .errors import OwnershipRequired
from .recipe_schema import Recipe
from .retry import retry_params, should_retry
from .steps import blend as blend_step
from .steps import detect as detect_step
from .steps import edit as edit_step
from .steps import filter as filter_step
from .steps import qa as qa_step
from providers.base import ImageEditProvider
from providers.registry import get_provider

# Recipes that require an explicit ownership confirmation before running.
OWNERSHIP_REQUIRED_RECIPES = {"remove_watermark"}


@dataclass
class RunResult:
    """Outcome of running a recipe on a single image."""

    image: Image.Image
    report: QaReport
    context: JobContext
    status: str = "done"
    best_effort: bool = False
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return self.report.passed


class RecipeRunner:
    """Runs recipes against a provider adapter."""

    def __init__(
        self,
        provider: Optional[ImageEditProvider] = None,
        provider_factory: Optional[Callable[[str], ImageEditProvider]] = None,
        qa_options: Optional[qa_step.QAOptions] = None,
    ) -> None:
        self._default_provider = provider
        self._provider_factory = provider_factory or get_provider
        self._qa_options = qa_options

    def _resolve_provider(self, name: Optional[str]) -> ImageEditProvider:
        if name and self._provider_factory is not None:
            return self._provider_factory(name)
        if self._default_provider is not None:
            return self._default_provider
        return get_provider(name or "mock")

    def run(
        self,
        recipe: Recipe,
        image: Image.Image,
        mask: Optional[Image.Image] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> RunResult:
        """Run ``recipe`` on ``image`` and return a :class:`RunResult`."""
        started = time.perf_counter()
        params = dict(params or {})

        if recipe.id in OWNERSHIP_REQUIRED_RECIPES and not params.get(
            "ownership_confirmed"
        ):
            raise OwnershipRequired(
                "Cần xác nhận quyền sở hữu trước khi xóa watermark."
            )

        context = JobContext(
            image=image, mask=mask, params=params, recipe_id=recipe.id
        )

        # detect + filter run once; retries only replay edit -> blend -> qa.
        detect_step.run(context, recipe.step("detect") or {})
        filter_step.run(context, recipe.step("filter") or {})

        edit_config = dict(recipe.step("edit") or {})
        provider = self._resolve_provider(edit_config.get("provider"))
        # Inject the resolved provider so the editor uses the adapter.
        context.params.setdefault("provider_name", edit_config.get("provider", "mock"))

        report = None
        attempts = recipe.retry.max + 1
        base_strength = float(
            params.get("strength", edit_config.get("strength", 0.5))
        )
        base_seed = int(params.get("seed", 42))
        for attempt in range(1, attempts + 1):
            strength, seed = retry_params(
                recipe.retry,
                base_strength=base_strength,
                base_seed=base_seed,
                attempt=attempt - 1,
            )
            context.image = context.original
            context.params["strength"] = strength
            context.params["seed"] = seed

            edit_step.run(context, edit_config, provider)
            blend_step.run(context, recipe.step("blend") or {})

            thresholds = recipe.qa.model_dump(exclude_none=True)
            report = qa_step.run(context, thresholds, attempt=attempt, options=self._qa_options)

            if report.passed:
                break
            if not should_retry(recipe.retry, attempt):
                break

        duration_ms = (time.perf_counter() - started) * 1000.0
        warnings = list(context.warnings)
        best_effort = not report.passed
        if best_effort:
            report = best_effort_report(report, attempts)
            warnings = list(report.warnings)

        return RunResult(
            image=context.image,
            report=report,
            context=context,
            status="done",
            best_effort=best_effort,
            warnings=warnings,
            duration_ms=round(duration_ms, 3),
        )
