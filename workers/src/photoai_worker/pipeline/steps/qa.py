"""QA step (AGENT_SKILLS S11).

Computes every measurement the QA layer can produce for the current context and
evaluates the subset declared in the recipe thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from PIL import Image

from ...detectors import eyes_ear
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


def compute_metrics(
    context: JobContext,
    options: Optional[QAOptions] = None,
    thresholds: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute all available QA metrics for the current context.

    ``thresholds`` only influences metrics whose definition depends on the
    gate being evaluated (currently: post-edit EAR re-detection).
    """
    options = options or QAOptions()
    thresholds = thresholds or {}
    original = context.original
    edited = context.image
    metrics: Dict[str, Any] = {}

    eyes = context.detections.get("eyes")
    if eyes is not None:
        metrics["ear"] = round(float(eyes.ear), 6)
        if thresholds.get("ear_min") is not None:
            # Re-detect the eyes on the edited image: the gate must measure the
            # *result*, not the input. Without a real landmark model this keeps
            # the pre-edit EAR (honest failure) unless the measurement is
            # simulated via ``post_left_ear``/``post_right_ear`` params.
            rechecked = eyes_ear.recheck_ear(
                edited,
                face=context.detections.get("main_face"),
                previous=eyes,
                params=context.params,
            )
            if rechecked is not None:
                metrics["ear"] = round(float(rechecked.ear), 6)

    if original is not None and edited is not None:
        # Pixel metrics always compare against the original size so an
        # upscaled output can be verified without a shape mismatch.
        comparison = edited
        if edited.size != original.size:
            comparison = edited.resize(original.size, Image.LANCZOS)

        metrics["identity_cosine"] = round(
            identity.identity_cosine(original, comparison, embedder=options.embedder), 6
        )
        metrics["outside_mask_ssim"] = round(
            ssim.outside_mask_ssim(original, comparison, context.edit_mask), 6
        )
        metrics["structure_similarity"] = round(
            lpips.structure_similarity(original, comparison), 6
        )
        metrics["clip_ratio"] = round(clip_ratio.clip_ratio(edited), 6)

        # Skin metrics are measured whenever the recipe gates on them (or a
        # mask was injected). The mask defaults to a heuristic YCbCr skin mask
        # so the gate is evaluated instead of silently skipped.
        skin_gated = (
            thresholds.get("delta_e_skin_max") is not None
            or thresholds.get("texture_variance_min") is not None
        )
        if options.skin_mask is not None or skin_gated:
            skin_mask = options.skin_mask
            if skin_mask is None:
                skin_mask = skin_color.auto_skin_mask(original)
            for_skin = edited if edited.size == original.size else comparison
            metrics["delta_e_skin"] = round(
                skin_color.delta_e_skin(original, for_skin, skin_mask), 6
            )
            metrics["texture_variance"] = round(
                skin_color.texture_variance(for_skin), 6
            )

    # Boolean rechecks are always reported so the gates are evaluated; with no
    # detector injected the documented placeholder contract returns True.
    metrics["ocr_recheck"] = ocr_recheck.ocr_recheck(edited, detector=options.ocr_detector)
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
    metrics = compute_metrics(context, options, thresholds)
    context.metrics = metrics
    report = evaluate(metrics, thresholds or {}, attempt=attempt)
    context.log("qa", "passed" if report.passed else "failed", attempt=attempt)
    return report
