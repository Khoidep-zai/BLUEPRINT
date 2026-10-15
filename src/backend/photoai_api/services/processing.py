"""Synchronous recipe processing service (select function -> upload -> output).

Bridges the FastAPI layer to the worker recipe pipeline. There is no queue and
no database: one request processes one image end-to-end, which matches the
self-hosted CPU scope chosen for the tool.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from PIL import Image

from .. import paths  # noqa: F401  (sys.path bootstrap before worker imports)
from ..errors import APIError, ErrorCode

from photoai_worker.pipeline import loader
from photoai_worker.pipeline.errors import PipelineError
from photoai_worker.pipeline.recipe_schema import Recipe
from photoai_worker.pipeline.runner import RecipeRunner
from providers.registry import get_provider

# Pipeline error code -> API error code.
_PIPELINE_ERROR_MAP = {
    "OWNERSHIP_REQUIRED": ErrorCode.OWNERSHIP_REQUIRED,
    "NO_FACE_DETECTED": ErrorCode.NO_FACE_DETECTED,
    "NO_CLOSED_EYES": ErrorCode.NO_CLOSED_EYES,
    "FILTER_REJECTED": ErrorCode.FILTER_REJECTED,
}


@dataclass
class RecipeInfo:
    """Public metadata for one editing function."""

    id: str
    name_vi: str
    name_en: str
    description: str = ""
    requires_ownership: bool = False
    steps: List[str] = field(default_factory=list)
    editor: str = "inpaint"
    provider: str = "mock"
    qa_thresholds: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessingService:
    """Loads recipes and runs them through the worker pipeline."""

    def __init__(self, recipes_dir: Optional[str] = None) -> None:
        from ..paths import RECIPES_DIR

        self.recipes_dir = str(recipes_dir or RECIPES_DIR)

    # ----- catalog -----
    def _raw(self, recipe_id: str) -> Dict[str, Any]:
        path = Path(self.recipes_dir) / f"{recipe_id}.yaml"
        if not path.is_file():
            raise APIError(
                ErrorCode.RECIPE_NOT_FOUND, f"Không tìm thấy chức năng: {recipe_id}"
            )
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _info(self, recipe_id: str) -> RecipeInfo:
        raw = self._raw(recipe_id)
        steps = raw.get("steps") or []
        step_names = [next(iter(step.keys())) for step in steps if step]
        edit = next((step["edit"] for step in steps if "edit" in step), {}) or {}
        return RecipeInfo(
            id=raw.get("id", recipe_id),
            name_vi=raw.get("name_vi", recipe_id),
            name_en=raw.get("name_en", recipe_id),
            description=raw.get("description", ""),
            requires_ownership=bool(raw.get("ownership_required", False)),
            steps=step_names,
            editor=str(edit.get("editor", "inpaint")),
            provider=str(edit.get("provider", "mock")),
            qa_thresholds=raw.get("qa_thresholds", {}) or {},
        )

    def list_recipes(self) -> List[RecipeInfo]:
        return [self._info(path.stem) for path in sorted(Path(self.recipes_dir).glob("*.yaml"))]

    def get_info(self, recipe_id: str) -> RecipeInfo:
        return self._info(recipe_id)

    def get_recipe(self, recipe_id: str) -> Recipe:
        try:
            return loader.load_recipe_by_id(recipe_id, self.recipes_dir)
        except FileNotFoundError:
            raise APIError(
                ErrorCode.RECIPE_NOT_FOUND, f"Không tìm thấy chức năng: {recipe_id}"
            ) from None

    # ----- execution -----
    def process(self, recipe: Recipe, image: Image.Image, params: Dict[str, Any]):
        """Run the recipe and translate pipeline errors into API errors."""
        runner = RecipeRunner(provider_factory=get_provider)
        try:
            return runner.run(recipe, image, params=params)
        except PipelineError as exc:
            code = _PIPELINE_ERROR_MAP.get(exc.code, ErrorCode.INTERNAL_ERROR)
            raise APIError(code, exc.message) from exc
        except APIError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalised to a domain error
            raise APIError(ErrorCode.INTERNAL_ERROR, f"Xử lý thất bại: {exc}") from exc
