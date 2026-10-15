"""Mask utilities (AGENT_SKILLS S4: dilate / feather, bbox masks)."""
from __future__ import annotations

from typing import Tuple

import numpy as np
from PIL import Image, ImageFilter


def box_mask(size: Tuple[int, int], box: Tuple[int, int, int, int]) -> Image.Image:
    """Create an L-mode mask with a filled rectangle ``box`` = (x0, y0, x1, y1)."""
    array = np.zeros((size[1], size[0]), dtype=np.uint8)
    x0, y0, x1, y1 = box
    x0 = max(0, min(x0, size[0]))
    x1 = max(0, min(x1, size[0]))
    y0 = max(0, min(y0, size[1]))
    y1 = max(0, min(y1, size[1]))
    array[y0:y1, x0:x1] = 255
    return Image.fromarray(array, mode="L")


def dilate_mask(mask: Image.Image, radius_px: int) -> Image.Image:
    """Grow the mask by ``radius_px`` using a max filter."""
    if radius_px <= 0:
        return mask.convert("L")
    return mask.convert("L").filter(ImageFilter.MaxFilter(2 * radius_px + 1))


def feather_mask(mask: Image.Image, radius_px: int) -> Image.Image:
    """Soften mask edges with a Gaussian blur of the given radius."""
    if radius_px <= 0:
        return mask.convert("L")
    return mask.convert("L").filter(ImageFilter.GaussianBlur(radius_px))


def prepare_mask(
    mask: Image.Image,
    dilate_px: int = 0,
    feather_px: int = 0,
) -> Image.Image:
    """Dilate then feather a mask, the standard prep before blending."""
    result = mask.convert("L")
    if dilate_px > 0:
        result = dilate_mask(result, dilate_px)
    if feather_px > 0:
        result = feather_mask(result, feather_px)
    return result


def mask_coverage(mask: Image.Image) -> float:
    """Fraction of the image the mask covers (0..1)."""
    array = np.asarray(mask.convert("L"), dtype=np.float32) / 255.0
    return float(array.mean())
