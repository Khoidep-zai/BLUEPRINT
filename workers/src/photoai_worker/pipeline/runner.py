"""Recipe Runner (S1): parse YAML -> run detect -> filter -> edit -> blend -> qa.

Supports retry and writes qa_report JSON. Tested with mock provider.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from providers.base import ImageEditProvider
from providers.registry import get as get_provider
from photoai_worker.pipeline.context import PipelineContext
from photoai_worker.pipeline.recipe_schema import Recipe
from photoai_worker.pipeline.retry import RetryPolicy

log = logging.getLogger("photoai.runner")


class Runner:
    def __init__(self, provider: Optional[ImageEditProvider] = None) -> None:
        self.provider = provider

    async def run(
        self,
        job_id: str,
        recipe: Recipe,
        image: Image.Image,
        mask: Optional[Image.Image] = None,
        params: dict | None = None,
    ) -> dict:
        ctx = PipelineContext(
            job_id=job_id,
            recipe_id=recipe.id,
            input_image=image,
            mask_image=mask,
            params=params or {},
        )

        provider = self.provider or get_provider(recipe.steps[0].get("provider", "mock") if recipe.steps else "mock")

        best_result: Optional[dict] = None
        best_score = -1.0

        attempt = 0
        while True:
            ctx.attempt = attempt
            t0 = time.perf_counter()

            result = await self._run_attempt(ctx, recipe, provider)
            ctx.qa_report = result["qa_report"]
            passed = bool(ctx.qa_report.get("passed"))

            # Track best effort
            score = self._score(ctx.qa_report)
            if best_result is None or score > best_score:
                best_score = score
                best_result = {
                    "image": ctx.edited_image or ctx.input_image,
                    "qa_report": ctx.qa_report,
                    "warnings": list(ctx.warnings),
                    "attempt": attempt,
                    "elapsed_ms": (time.perf_counter() - t0) * 1000.0,
                }

            if passed:
                best_result["passed"] = True
                break

            if not RetryPolicy().should_retry(attempt, passed):
                best_result["passed"] = False
                best_result["warnings"].append("QA failed after max retries; returning best effort.")
                break

            # Retry: reduce strength, reseed
            attempt += 1
            ctx.params["strength"] = RetryPolicy().next_strength(
                float(ctx.params.get("strength", 0.5)), attempt
            )
            if RetryPolicy().reseed:
                import random
                ctx.params["seed"] = random.randint(0, 10**6)
            log.warning("job %s attempt %d QA failed, retrying", job_id, attempt)

        return best_result

    async def _run_attempt(
        self, ctx: PipelineContext, recipe: Recipe, provider: ImageEditProvider
    ) -> dict:
        for step in recipe.steps:
            for key, cfg in step.items():
                if key == "detect":
                    await self._step_detect(ctx, cfg)
                elif key == "filter":
                    self._step_filter(ctx, cfg)
                elif key == "edit":
                    await self._step_edit(ctx, cfg, provider)
                elif key == "blend":
                    self._step_blend(ctx, cfg)
                elif key == "qa":
                    ctx.qa_report = self._step_qa(ctx, cfg)
                else:
                    log.warning("unknown step %s", key)

        return {"qa_report": ctx.qa_report}

    async def _step_detect(self, ctx: PipelineContext, cfg: dict) -> None:
        # Placeholder: real detectors live in workers/detectors.
        if cfg.get("faces"):
            ctx.detections.append(
                {"kind": "face", "bbox": [0, 0, *ctx.size], "confidence": 1.0, "meta": {}}
            )
        if cfg.get("eyes_ear"):
            ctx.detections.append(
                {"kind": "eye", "bbox": [0, 0, ctx.size[0] // 2, ctx.size[1] // 2], "confidence": 0.9, "meta": {}}
            )
        log.info("job %s detect done: %d detections", ctx.job_id, len(ctx.detections))

    def _step_filter(self, ctx: PipelineContext, cfg: dict) -> None:
        # Placeholder filter - keeps detections meeting cfg.
        min_conf = cfg.get("min_confidence", 0.0)
        ctx.detections = [d for d in ctx.detections if d["confidence"] >= min_conf]
        log.info("job %s filter done: %d detections remain", ctx.job_id, len(ctx.detections))

    async def _step_edit(
        self, ctx: PipelineContext, cfg: dict, provider: ImageEditProvider
    ) -> None:
        prompt_id = cfg.get("prompt_id") or f"{ctx.recipe_id}"
        prompt = f"Edit image according to recipe {ctx.recipe_id}."
        strength = float(ctx.params.get("strength", cfg.get("strength", 0.5)))
        seed = ctx.params.get("seed")

        result = await provider.edit(
            ctx.input_image,
            prompt,
            mask=ctx.mask_image,
            strength=strength,
            seed=seed,
        )
        ctx.edited_image = result.image
        ctx.metadata["provider"] = provider.name
        ctx.metadata["model_version"] = result.model_version
        ctx.metadata["latency_ms"] = result.latency_ms
        ctx.metadata["cost_usd"] = result.cost_usd
        log.info("job %s edit done (%s, %.1fms)", ctx.job_id, provider.name, result.latency_ms)

    def _step_blend(self, ctx: PipelineContext, cfg: dict) -> None:
        # Feather blend placeholder: use edited image directly.
        ctx.blend_image = ctx.edited_image or ctx.input_image
        log.info("job %s blend done", ctx.job_id)

    def _step_qa(self, ctx: PipelineContext, cfg: dict) -> dict:
        # Placeholder QA - real metrics in workers/qa.
        report = {
            "passed": True,
            "attempt": ctx.attempt,
            "metrics": {},
            "thresholds": {},
            "warnings": [],
        }
        ctx.warnings.extend(report["warnings"])
        log.info("job %s qa done: passed=%s", ctx.job_id, report["passed"])
        return report

    @staticmethod
    def _score(qa_report: dict) -> float:
        metrics = qa_report.get("metrics", {})
        thresholds = qa_report.get("thresholds", {})
        score = 0.0
        count = 0
        for key, thr in thresholds.items():
            metric_key = key.replace("_min", "").replace("_max", "")
            if metric_key in metrics:
                count += 1
                val = metrics[metric_key]
                if key.endswith("_min") and val >= thr:
                    score += 1.0
                elif key.endswith("_max") and val <= thr:
                    score += 1.0
        return score / count if count else 0.0
