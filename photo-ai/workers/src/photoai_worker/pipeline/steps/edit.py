"""Edit step (AGENT_SKILLS S1/S5).

Builds the region to edit, dispatches to the right editor, and runs the provider
adapter. Records provider call metadata for cost/latency accounting.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from PIL import Image

from ...detectors.eyes_ear import eye_landmarks
from ...editors import inpaint, relight, restore, studio, upscale
from ...masking import box_mask
from ...pipeline.context import JobContext
from providers.base import ImageEditProvider


def build_edit_mask(context: JobContext, padding: float = 0.3) -> Optional[Image.Image]:
    """Derive the edit mask from a user mask or from detections."""
    if context.mask is not None:
        return context.mask

    face = context.detections.get("main_face")
    eyes = context.detections.get("eyes")
    if face is not None and eyes is not None:
        # Cover both eyes, grown by ``padding`` for context.
        left = eye_landmarks(face, ear=eyes.left_ear, eye="left")
        right = eye_landmarks(face, ear=eyes.right_ear, eye="right")
        xs = [p[0] for p in left + right]
        ys = [p[1] for p in left + right]
        span_x = (max(xs) - min(xs)) or 1.0
        span_y = (max(ys) - min(ys)) or 1.0
        pad_x = span_x * padding
        pad_y = span_y * padding
        box = (
            int(min(xs) - pad_x),
            int(min(ys) - pad_y),
            int(max(xs) + pad_x),
            int(max(ys) + pad_y),
        )
        return box_mask(context.image.size, box)

    if face is not None:
        pad_x = face.width * padding
        pad_y = face.height * padding
        box = (
            int(face.x - pad_x),
            int(face.y - pad_y),
            int(face.x + face.width + pad_x),
            int(face.y + face.height + pad_y),
        )
        return box_mask(context.image.size, box)

    return None


def run(
    context: JobContext,
    config: Dict[str, Any],
    provider: ImageEditProvider,
) -> JobContext:
    """Execute the edit step, storing the provider output in ``context.edited``."""
    config = config or {}
    editor = config.get("editor", "inpaint")
    padding = float(config.get("padding", 0.3))
    prompt = config.get("prompt") or context.params.get("prompt", "")
    strength = float(context.params.get("strength", config.get("strength", 0.5)))
    seed = int(context.params.get("seed", 42))

    mask = build_edit_mask(context, padding)

    if editor == "upscale":
        context.edited = upscale.upscale(
            context.image, scale=float(config.get("scale", 2.0))
        )
    elif editor == "relight":
        context.edited = relight.relight(
            context.image, provider=provider, mask=mask, prompt=prompt,
            strength=strength, seed=seed,
        )
    elif editor == "restore":
        context.edited = restore.restore(
            context.image, provider=provider, mask=mask, prompt=prompt,
            strength=strength, seed=seed,
        )
    elif editor == "studio":
        context.edited = studio.studio_composite(
            context.image, provider=provider, mask=mask, prompt=prompt,
            strength=strength, seed=seed,
        )
    else:  # default: inpaint
        if mask is None:
            # No localisation available -> edit whole image through the provider.
            context.edited = provider.edit(
                context.image, mask=None, prompt=prompt, strength=strength, seed=seed
            )
        else:
            context.edited = inpaint.inpaint(
                context.image, mask, provider, prompt=prompt,
                strength=strength, seed=seed,
            )

    context.mask = mask
    metadata = provider.call_metadata()
    if metadata:
        context.provider_calls.append(metadata)
    context.log("edit", "ok")
    return context
