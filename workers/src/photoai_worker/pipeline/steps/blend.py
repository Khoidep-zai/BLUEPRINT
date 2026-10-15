"""Blend step (AGENT_SKILLS S1/S5).

Composites the edited image back onto the original using a feathered mask so the
seam is invisible and pixels outside the edit region stay identical.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

from ...masking import prepare_mask
from ...pipeline.context import JobContext


def run(context: JobContext, config: Dict[str, Any]) -> JobContext:
    """Blend ``context.edited`` into ``context.original`` and set ``edit_mask``."""
    config = config or {}
    if context.edited is None:
        raise ValueError("blend step requires context.edited")

    edited = context.edited
    if config.get("method") == "none":
        # Whole-image output (e.g. upscale): keep the edited image as-is,
        # including a different output size. No compositing happens.
        context.image = edited
        context.edit_mask = None
        context.log("blend", "ok", detail="method none")
        return context
    if edited.size != context.original.size:
        edited = edited.resize(context.original.size, Image.LANCZOS)

    raw_mask = context.mask
    if raw_mask is None:
        # Whole-image edit: nothing to composite.
        context.image = edited
        context.edit_mask = None
        context.log("blend", "ok", detail="no mask")
        return context

    prepared = prepare_mask(raw_mask, feather_px=int(config.get("radius_px", 8)))

    original_array = np.asarray(context.original, dtype=np.float32)
    edited_array = np.asarray(edited, dtype=np.float32)
    alpha = (np.asarray(prepared, dtype=np.float32) / 255.0)[:, :, None]
    blended = original_array * (1.0 - alpha) + edited_array * alpha

    context.image = Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")
    context.edit_mask = prepared
    context.log("blend", "ok")
    return context
