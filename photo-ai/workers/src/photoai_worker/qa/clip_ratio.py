"""Highlight/shadow clipping ratio (AGENT_SKILLS S11)."""
from __future__ import annotations

import numpy as np
from PIL import Image


def clip_ratio(image: Image.Image, low: int = 2, high: int = 253) -> float:
    """Return the fraction of pixels clipped at either end of the range.

    A pixel is "clipped" when any channel is <= ``low`` or >= ``high``. Recipes
    require this to stay below ``clip_ratio_max`` (< 1% by default).
    """
    array = np.asarray(image.convert("RGB"), dtype=np.uint8)
    clipped = (array <= low) | (array >= high)
    return float(clipped.mean())
