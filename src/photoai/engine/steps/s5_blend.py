"""Stage 5 — Blend: composite the edited ROI back onto the original (design §2)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from photoai.engine.context import PipelineContext
from photoai.engine.recipe_schema import BlendStep
from photoai.processors.masking import prepare_mask

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore


def run(context: PipelineContext, blend: BlendStep) -> PipelineContext:
    if context.edited is None:
        raise ValueError("blend step requires context.edited")

    edited = context.edited

    # Full-frame recipes (e.g. upscale) keep the whole edited image.
    if blend.method == "none":
        context.image = edited
        context.edit_mask = None
        context.log("blend", "ok", detail="none")
        return context

    original = context.original
    if edited.size != original.size:
        edited = edited.resize(original.size, Image.LANCZOS)

    raw_mask = context.mask
    if raw_mask is None:
        context.image = edited
        context.edit_mask = None
        context.log("blend", "ok", detail="no mask")
        return context

    prepared = prepare_mask(raw_mask, feather_px=int(blend.radius_px))

    if blend.method == "poisson" and cv2 is not None:
        try:
            src = np.asarray(edited.convert("RGB"))
            dst = np.asarray(original.convert("RGB"))
            centre = _mask_centre(prepared, original.size)
            merged = cv2.seamlessClone(src, dst, np.asarray(prepared), centre, cv2.NORMAL_CLONE)
            context.image = Image.fromarray(merged, mode="RGB")
            context.edit_mask = prepared
            context.log("blend", "ok", detail="poisson")
            return context
        except Exception:  # pragma: no cover - fall through to feather
            pass

    original_array = np.asarray(original, dtype=np.float32)
    edited_array = np.asarray(edited, dtype=np.float32)
    alpha = (np.asarray(prepared, dtype=np.float32) / 255.0)[:, :, None]
    blended = original_array * (1.0 - alpha) + edited_array * alpha

    context.image = Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")
    context.edit_mask = prepared
    context.log("blend", "ok", detail=blend.method)
    return context


def _mask_centre(mask: Image.Image, size: tuple[int, int]) -> tuple[int, int]:
    arr = np.asarray(mask, dtype=np.uint8)
    ys, xs = np.where(arr > 127)
    if len(xs) == 0:
        return (size[0] // 2, size[1] // 2)
    return (int(xs.mean()), int(ys.mean()))
