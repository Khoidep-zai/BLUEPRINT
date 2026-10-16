"""Stage 7 — Export: write the finished image to ``workspace/results`` strictly as PNG or JPG (design §2)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from photoai.config import WORKSPACE_RESULTS, ensure_workspace_dirs
from photoai.engine.context import PipelineContext
from photoai.storage.image_codec import save_image


def run(context: PipelineContext, job_id: Optional[str] = None) -> PipelineContext:
    if job_id is None and not context.params.get("persist_result"):
        context.log("export", "skipped")
        return context

    ensure_workspace_dirs()
    name = job_id or context.params.get("job_id") or context.recipe_id
    fmt = str(context.params.get("export_format", "png")).lower()
    ext = ".jpg" if fmt in ("jpg", "jpeg") else ".png"

    path = WORKSPACE_RESULTS / f"{name}{ext}"
    saved_path = save_image(context.image, path, format=fmt)

    context.export_path = str(saved_path)
    context.job_id = job_id or context.job_id
    context.log("export", "ok", detail=str(saved_path))
    return context

