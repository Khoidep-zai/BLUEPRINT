"""Pipeline engine: VRAM management, context, recipe schema and the 7-stage runner.

Imports are kept lazy: detectors depend on ``engine.vram_manager`` while the
runner depends on detectors, so eagerly importing the runner here would create a
circular import. Submodule imports (``photoai.engine.runner``) always work.
"""
from __future__ import annotations

from typing import Any

from .context import JobContext, PipelineContext, StepLog  # noqa: F401

__all__ = [
    "RecipeRunner",
    "RunResult",
    "PipelineContext",
    "JobContext",
    "StepLog",
    "VRAMModelManager",
    "load_model",
    "register_model_loader",
]


def __getattr__(name: str) -> Any:  # pragma: no cover - trivial indirection
    if name in {"RecipeRunner", "RunResult"}:
        from .runner import RecipeRunner, RunResult

        return {"RecipeRunner": RecipeRunner, "RunResult": RunResult}[name]
    if name in {"VRAMModelManager", "load_model", "register_model_loader"}:
        from . import vram_manager

        return getattr(vram_manager, name)
    raise AttributeError(f"module 'photoai.engine' has no attribute {name!r}")
