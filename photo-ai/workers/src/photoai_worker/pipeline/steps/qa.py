"""QA step (AGENT_SKILLS S11).

Computes every measurement the QA layer can produce for the current context and
evaluates the subset declared in the recipe thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from PIL import Image

from ...pipeline.context import JobContext
from ...qa import clip_ratio, identity, lpips, ocr_recheck, person_recheck, ssim
from ...qa import skin_color
from ...qa.report import QaReport, evaluate


@dataclass
class QAOptions:
    """Optional injectable real models (P1+). Defaults keep P0 runnable."""

    embedder: Optional[Callable[[Image.Image], Any]] = None
    ocr_detector: Optional[Callable[[Image.Image], Any]] = None
    person_detector: Optional[Callable[[Image.Image], Any]] = None
    skin_mask: Optional[Image.Image] = None


def compute_metrics(context: JobContext, options: Optional[QAOptions] = None) -> Dict[str, Any]:
    """Compute all available QA metrics for the current context."""
    options = options or QAOptions()
    original = context.original
    edited = context.image
    metrics: Dict[str, Any] = {}

    eyes = context.detections.get("eyes")
    if eyes is not None:
        metrics["ear"] = round(float(eyes.ear), 6)

    if original is not None and edited is not None:
        metrics["identity_cosine"] = round(
            identity.identity_cosine(original, edited, embedder=options.embedder), 6
        )
        metrics["outside_mask_ssim"] = round(
            ssim.outside_mask_ssim(original, edited, context.edit_mask), 6
        )
        metrics["structure_similarity"] = round(
            lpips.structure_similarity(original, edited), 6
        )
        metrics["clip_ratio"] = round(clip_ratio.clip_ratio(edited), 6)

        if options.skin_mask is not None:
            metrics["delta_e_skin"] = round(
                skin_color.delta_e_skin(original, edited, options.skin_mask), 6
            )
            metrics["texture_variance"] = round(
                skin_color.texture_variance(edited), 6
            )

    if options.ocr_detector is not None:
        metrics["ocr_recheck"] = ocr_recheck.ocr_recheck(edited, detector=options.ocr_detector)
    if options.person_detector is not None:
        metrics["person_recheck"] = person_recheck.person_recheck(
            edited, detector=options.person_detector
        )

    return metrics


def run(
    context: JobContext,
    thresholds: Dict[str, Any],
    attempt: int = 1,
    options: Optional[QAOptions] = None,
) -> QaReport:
    """Compute metrics and evaluate them against ``thresholds``."""
    metrics = compute_metrics(context, options)
    context.metrics = metrics
    report = evaluate(metrics, thresholds or {}, attempt=attempt)
    context.log("qa", "passed" if report.passed else "failed", attempt=attempt)
    return report
