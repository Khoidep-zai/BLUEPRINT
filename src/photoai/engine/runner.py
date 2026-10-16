"""Recipe runner: 7-stage hybrid pipeline + retry + CV fallback (design §1.2, §5).

Runs ``Ingest -> Detect -> ROI/Mask -> GPU Edit -> Blend -> AutoQA -> Export``
in-process. QA failure retries stage 4 with reduced strength; exhausting the
retries returns the safe Classical-CV branch with explicit warnings.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

from photoai.engine.context import PipelineContext
from photoai.errors import OwnershipError
from photoai.engine.recipe_schema import Recipe
from photoai.engine.retry import retry_params, should_retry
from photoai.engine.steps import (
    s1_ingest,
    s2_detect,
    s3_roi_mask,
    s4_edit,
    s5_blend,
    s6_qa,
    s7_export,
)
from photoai.qa.evaluator import QaReport, best_effort_report
from photoai.qa.metrics import MetricsOptions


@dataclass
class RunResult:
    image: Image.Image
    report: QaReport
    context: PipelineContext
    status: str = "done"
    best_effort: bool = False
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return self.report.passed


def _cv_safe_fallback(context: PipelineContext, recipe_id: str) -> Image.Image:
    """Classical-CV branch used when the GPU edit fails QA after every retry."""
    if context.cv_fallback_image is not None:
        return context.cv_fallback_image

    base = context.original or context.image

    if recipe_id in {"skin_retouch", "golden_hour", "low_light_fix"}:
        from photoai.processors.cv_ops.frequency_sep import FrequencySeparator

        arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
        low, high = FrequencySeparator.decompose(arr)
        # Gentle low-frequency smoothing that always keeps the original detail.
        smoothed = FrequencySeparator.smooth_low_frequency(low)
        blended_low = low * 0.6 + smoothed * 0.4
        restored = np.clip(blended_low + high * 0.9, 0.0, 1.0)
        return Image.fromarray((restored * 255.0).astype(np.uint8), mode="RGB")

    if recipe_id == "chin_fix" and context.detections.get("main_face") is not None:
        from photoai.detectors import face_analyzer
        from photoai.processors.cv_ops.geometry_tps import subtle_perspective_chin_warp

        landmarks = face_analyzer.landmarks_68(context.detections["main_face"])
        warped = subtle_perspective_chin_warp(np.asarray(base.convert("RGB")), landmarks)
        return Image.fromarray(warped, mode="RGB")

    return base.copy()


class RecipeRunner:
    def __init__(self, qa_options: Optional[MetricsOptions] = None) -> None:
        self._qa_options = qa_options

    def run(
        self,
        recipe: Recipe,
        image: Image.Image,
        mask: Optional[Image.Image] = None,
        params: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
    ) -> RunResult:
        started = time.perf_counter()
        params = dict(params or {})

        if recipe.ownership_required and not params.get("ownership_confirmed"):
            raise OwnershipError("Cần xác nhận quyền sở hữu trước khi xoá watermark.")

        context = PipelineContext(image=image, mask=mask, params=params, recipe_id=recipe.id)

        s1_ingest.run(context)
        s2_detect.run(context, recipe.detect, recipe.filter)
        s3_roi_mask.run(context, recipe.edit)

        edit_step = recipe.edit
        report: Optional[QaReport] = None
        attempts = recipe.retry.max + 1
        base_strength = float(params.get("strength", edit_step.strength))
        base_seed = int(params.get("seed", 42))

        from photoai.engine.vram_manager import inference_scope

        with inference_scope():
            for attempt in range(1, attempts + 1):
                strength, seed = retry_params(
                    recipe.retry, base_strength=base_strength, base_seed=base_seed, attempt=attempt - 1
                )
                if context.original is not None:
                    context.image = context.original.copy()
                context.params["strength"] = strength
                context.params["seed"] = seed

                s4_edit.run(context, edit_step)
                s5_blend.run(context, recipe.blend)

                thresholds = recipe.qa.model_dump(exclude_none=True)
                report = s6_qa.run(context, thresholds, attempt=attempt, options=self._qa_options)
                if report.passed or not should_retry(recipe.retry, attempt):
                    break


        best_effort = report is not None and not report.passed
        warnings = list(context.warnings)
        if best_effort and report is not None:
            fallback = _cv_safe_fallback(context, recipe.id)
            context.edited = fallback
            context.image = fallback
            context.warnings.append("QA trượt sau retry — trả về nhánh Classical CV an toàn.")
            report = best_effort_report(report, attempts)
            warnings = list(report.warnings)

        if params.get("persist_result") or job_id:
            s7_export.run(context, job_id=job_id)

        assert report is not None
        return RunResult(
            image=context.image,
            report=report,
            context=context,
            status="done",
            best_effort=best_effort,
            warnings=warnings,
            duration_ms=round((time.perf_counter() - started) * 1000.0, 3),
        )
