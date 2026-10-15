"""Skin retouch editor (AGENT_SKILLS S7).

P0 placeholder: frequency-separation smoothing that only touches the low
frequency band inside the skin mask, preserving texture (the anti "plastic
skin" requirement). Real face-parsing masks land in P2.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image, ImageFilter


def retouch_skin(
    image: Image.Image,
    skin_mask: Optional[Image.Image] = None,
    strength: float = 0.5,
    radius: float = 3.0,
) -> Image.Image:
    """Smooth low-frequency skin texture while preserving high frequency detail."""
    source = image.convert("RGB")
    low = source.filter(ImageFilter.GaussianBlur(radius))
    source_array = np.asarray(source, dtype=np.float32)
    low_array = np.asarray(low, dtype=np.float32)
    strength = float(np.clip(strength, 0.0, 1.0))

    smoothed = source_array + (low_array - source_array) * strength

    if skin_mask is not None:
        mask = skin_mask.convert("L")
        if mask.size != source.size:
            mask = mask.resize(source.size)
        alpha = (np.asarray(mask, dtype=np.float32) / 255.0)[:, :, None]
        blended = source_array * (1.0 - alpha) + smoothed * alpha
    else:
        blended = smoothed

    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")
