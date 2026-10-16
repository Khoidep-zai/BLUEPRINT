"""Stage 3 — ROI/Mask: build the edit mask and frequency layers (design §2)."""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image

from photoai.detectors import eyes_gaze, face_parsing, ocr_damage, person_depth
from photoai.engine.context import PipelineContext
from photoai.engine.recipe_schema import EditStep
from photoai.processors.cv_ops.frequency_sep import FrequencySeparator
from photoai.processors.masking import box_mask, prepare_mask

# Recipes that protect skin texture via frequency separation.
_FREQUENCY_RECIPES = {"skin_retouch", "chin_fix", "golden_hour", "low_light_fix", "restore_old_photo"}


def _eyes_mask(context: PipelineContext, padding: float) -> Optional[Image.Image]:
    face = context.detections.get("main_face")
    eyes = context.detections.get("eyes")
    if face is None or eyes is None:
        return None

    left = eyes_gaze.eye_landmarks(face, ear=eyes.left_ear, eye="left")
    right = eyes_gaze.eye_landmarks(face, ear=eyes.right_ear, eye="right")
    xs = [p[0] for p in left + right]
    ys = [p[1] for p in left + right]
    pad_x = max(1.0, (max(xs) - min(xs)) * padding)
    pad_y = max(1.0, (max(ys) - min(ys)) * padding)
    box = (int(min(xs) - pad_x), int(min(ys) - pad_y), int(max(xs) + pad_x), int(max(ys) + pad_y))
    return box_mask(context.image.size, box)


def _face_box_mask(context: PipelineContext, padding: float) -> Optional[Image.Image]:
    face = context.detections.get("main_face")
    if face is None:
        return None
    pad_x, pad_y = face.width * padding, face.height * padding
    box = (
        int(face.x - pad_x),
        int(face.y - pad_y),
        int(face.x + face.width + pad_x),
        int(face.y + face.height + pad_y),
    )
    return box_mask(context.image.size, box)


def _regions_mask(context: PipelineContext, key: str, padding_px: int) -> Optional[Image.Image]:
    regions = context.detections.get(key)
    if not regions:
        return None
    mask = np.zeros((context.image.size[1], context.image.size[0]), dtype=np.uint8)
    for region in regions:
        x0 = max(0, region.x - padding_px)
        y0 = max(0, region.y - padding_px)
        x1 = min(context.image.size[0], region.x + region.width + padding_px)
        y1 = min(context.image.size[1], region.y + region.height + padding_px)
        mask[y0:y1, x0:x1] = 255
    return Image.fromarray(mask, mode="L")


def build_edit_mask(context: PipelineContext, padding: float) -> Optional[Image.Image]:
    """Return the recipe-appropriate edit mask (or ``None`` for full-frame edits)."""
    if context.mask is not None:
        return context.mask

    recipe_id = context.recipe_id

    if recipe_id == "product_studio":
        alpha = context.detections.get("product_alpha")
        return alpha if alpha is not None else None
    if recipe_id == "remove_watermark":
        return _regions_mask(context, "text_logo", 5)
    if recipe_id == "remove_bystanders":
        return person_depth.bystander_mask(
            context.image, context.detections.get("main_person")
        )
    if recipe_id == "open_eyes":
        return _eyes_mask(context, max(padding, 0.3))
    if recipe_id == "skin_retouch":
        return face_parsing.skin_mask(context.image, context.detections.get("main_face"))
    if recipe_id == "restore_old_photo":
        scratches = _regions_mask(context, "scratches", 3)
        face = _face_box_mask(context, padding)
        return scratches or face
    if recipe_id == "chin_fix":
        return _face_box_mask(context, max(padding, 0.35))

    return _face_box_mask(context, padding)


def run(context: PipelineContext, edit: EditStep) -> PipelineContext:
    if context.mask is None:
        context.mask = build_edit_mask(context, edit.padding)

    if context.original_rgb is not None and context.recipe_id in _FREQUENCY_RECIPES:
        low, high = FrequencySeparator.decompose(context.original_rgb)
        context.low_freq, context.high_freq = low, high

    if context.mask is not None:
        context.edit_mask = prepare_mask(context.mask, dilate_px=0, feather_px=2)

    context.log("roi_mask", "ok")
    return context
