"""Stage 4 — Edit: hybrid Classical-CV + GPU model dispatch (design §2, §4).

Each recipe selects an ``editor``; the editor combines classical ops (frequency
separation, TPS, colour science, studio physics) with a GPU wrapper
(Real-ESRGAN, LaMa, CodeFormer, IC-Light). GPU wrappers fall back to their
classical path when the model is unavailable.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image

from photoai.config import RESTORE_MAX_LONG_EDGE
from photoai.detectors import face_analyzer, face_parsing, product_matting
from photoai.engine.context import PipelineContext
from photoai.engine.recipe_schema import EditStep
from photoai.processors.ai_wrappers import (
    face_restorer_gpu,
    inpainter_gpu,
    relighter_gpu,
    upscaler_gpu,
)
from photoai.processors.cv_ops import color_lighting, geometry_tps
from photoai.processors.cv_ops import frequency_sep as fsep
from photoai.processors.cv_ops.studio_physics import compose_luxury_studio_product

_REINJECT_RECIPES = {"chin_fix", "golden_hour", "low_light_fix"}


def _skin_mask(context: PipelineContext) -> np.ndarray:
    mask = context.params.get("skin_mask")
    if mask is None:
        mask = face_parsing.skin_mask(context.image, context.detections.get("main_face"))
    if isinstance(mask, Image.Image):
        arr = np.asarray(mask.convert("L"), dtype=np.float32) / 255.0
    else:
        arr = np.asarray(mask, dtype=np.float32)
        if arr.max() > 1.0:
            arr /= 255.0
    return arr


def _reinject_detail(context: PipelineContext, edited: Image.Image) -> Image.Image:
    """Re-inject the original high-frequency layer so structure never gets soft."""
    if context.high_freq is None:
        return edited
    if edited.size != context.original.size:
        edited = edited.resize(context.original.size, Image.LANCZOS)
    mask = _skin_mask(context)
    out = fsep.FrequencySeparator.recombine(
        np.asarray(edited.convert("RGB")), context.high_freq, mask
    )
    return Image.fromarray(out, mode="RGB")


def _editor_upscale(context: PipelineContext, step: EditStep) -> Image.Image:
    scale = float(context.params.get("scale", step.scale or 4.0))
    upscaled = upscaler_gpu.upscale(context.image, scale=scale)
    # Restore the original white balance / light direction in Lab space.
    return Image.fromarray(
        color_lighting.lab_histogram_match(
            np.asarray(upscaled.convert("RGB")),
            np.asarray(context.original.convert("RGB")),
        ),
        mode="RGB",
    )


def _editor_skin(context: PipelineContext, step: EditStep) -> Image.Image:
    strength = float(context.strength)
    arr = np.asarray(context.image.convert("RGB"), dtype=np.uint8)
    low, high = fsep.FrequencySeparator.decompose(arr)
    smoothed_low = fsep.FrequencySeparator.smooth_low_frequency(low)
    edited_low = low * (1.0 - strength) + smoothed_low * strength
    restored = np.clip(edited_low + high * 0.85, 0.0, 1.0)

    base = arr.astype(np.float32) / 255.0
    mask = _skin_mask(context)[:, :, None]
    blended = base * (1.0 - mask) + restored * mask
    image = Image.fromarray(np.clip(blended * 255.0, 0, 255).astype(np.uint8), mode="RGB")

    scale = float(context.params.get("scale", step.scale or 1.0))
    if scale != 1.0:
        image = upscaler_gpu.upscale(image, scale=scale)
    return image


def _editor_geometry(context: PipelineContext, step: EditStep) -> Image.Image:
    face = context.detections.get("main_face")
    image = context.image
    if face is not None:
        landmarks = face_analyzer.landmarks_68(face)
        warped = geometry_tps.subtle_perspective_chin_warp(
            np.asarray(image.convert("RGB")), landmarks
        )
        image = Image.fromarray(warped, mode="RGB")
    if context.mask is not None:
        image = inpainter_gpu.inpaint(image, context.mask, strength=float(context.strength))
    return image


def _editor_eyes(context: PipelineContext, step: EditStep) -> Image.Image:
    if context.mask is None:
        return context.image.copy()
    return inpainter_gpu.inpaint(context.image, context.mask, strength=float(context.strength))


def _editor_inpaint(context: PipelineContext, step: EditStep) -> Image.Image:
    if context.mask is None:
        return context.image.copy()
    return inpainter_gpu.inpaint(context.image, context.mask, strength=float(context.strength))


def _editor_restore(context: PipelineContext, step: EditStep) -> Image.Image:
    image = context.image
    # 1. Patch scratches / tears.
    if context.mask is not None:
        image = inpainter_gpu.inpaint(image, context.mask, strength=float(context.strength))
    # 2. Restore facial detail (CodeFormer w=0.85).
    image = face_restorer_gpu.restore_face(image, fidelity=0.85, strength=float(context.strength))
    # 3. Re-inject original detail at source resolution before upscaling.
    image = _reinject_detail(context, image)
    # 4. Upscale to the 4K long edge, then finish with film grain.
    target = float(context.params.get("target_long_edge", getattr(step, "target_long_edge", None) or RESTORE_MAX_LONG_EDGE))
    scale = target / max(image.size)
    if scale > 1.0:
        image = upscaler_gpu.upscale(image, scale=scale, max_long_edge=int(target))
    return Image.fromarray(color_lighting.film_grain(np.asarray(image.convert("RGB")), seed=context.seed))


def _editor_relight(context: PipelineContext, step: EditStep) -> Image.Image:
    return relighter_gpu.relight(
        context.image, mask=context.mask, mode="golden_hour", strength=float(context.strength)
    )


def _editor_lowlight(context: PipelineContext, step: EditStep) -> Image.Image:
    lit = relighter_gpu.relight(
        context.image, mask=context.mask, mode="lowlight", strength=float(context.strength)
    )
    arr = color_lighting.apply_clahe_l_channel(np.asarray(lit.convert("RGB")))
    return Image.fromarray(arr, mode="RGB")


def _editor_studio(context: PipelineContext, step: EditStep) -> Image.Image:
    alpha = context.detections.get("product_alpha")
    if alpha is None:
        alpha = product_matting.product_alpha(context.image, context.mask)
    backdrop = relighter_gpu.studio_background(context.image.size, seed=context.seed)
    composed = compose_luxury_studio_product(
        np.asarray(context.original.convert("RGB")),
        np.asarray(alpha.convert("L")),
        backdrop,
    )
    return Image.fromarray(composed, mode="RGB")


_EDITORS = {
    "upscale": _editor_upscale,
    "skin": _editor_skin,
    "geometry": _editor_geometry,
    "eyes": _editor_eyes,
    "inpaint": _editor_inpaint,
    "bystanders": _editor_inpaint,
    "restore": _editor_restore,
    "relight": _editor_relight,
    "lowlight": _editor_lowlight,
    "studio": _editor_studio,
}


def run(context: PipelineContext, edit: EditStep) -> PipelineContext:
    editor = _EDITORS.get(edit.editor, _editor_inpaint)
    edited: Optional[Image.Image] = editor(context, edit)

    if context.recipe_id in _REINJECT_RECIPES:
        edited = _reinject_detail(context, edited)

    context.edited = edited
    context.log("edit", "ok", detail=edit.editor)
    return context
