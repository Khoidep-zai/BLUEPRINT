"""Structural similarity metrics (AGENT_SKILLS S11).

Self-contained SSIM implementation (Wang et al., 2004) so the QA layer has no
heavy runtime dependency and is fully deterministic in tests.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image

_C1 = (0.01 * 255) ** 2
_C2 = (0.03 * 255) ** 2


def _to_gray_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("L"), dtype=np.float64)


def _uniform_filter(array: np.ndarray, radius: int) -> np.ndarray:
    """Fast box filter using an integral image (mean over (2r+1)^2 window)."""
    if radius < 1:
        return array
    padded = np.pad(array, radius, mode="reflect")
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    integral = np.pad(integral, ((1, 0), (1, 0)), mode="constant")
    window = 2 * radius + 1
    height, width = array.shape
    total = (
        integral[window:window + height, window:window + width]
        - integral[0:height, window:window + width]
        - integral[window:window + height, 0:width]
        + integral[0:height, 0:width]
    )
    return total / (window * window)


def ssim(
    image_a: Image.Image,
    image_b: Image.Image,
    radius: int = 3,
    mask: Optional[np.ndarray] = None,
) -> float:
    """Return the mean SSIM between two images.

    If ``mask`` is given (boolean array), only pixels where ``mask`` is True are
    averaged.
    """
    a = _to_gray_array(image_a)
    b = _to_gray_array(image_b)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")

    mu_a = _uniform_filter(a, radius)
    mu_b = _uniform_filter(b, radius)
    mu_a_sq = mu_a * mu_a
    mu_b_sq = mu_b * mu_b
    mu_ab = mu_a * mu_b

    sigma_a_sq = _uniform_filter(a * a, radius) - mu_a_sq
    sigma_b_sq = _uniform_filter(b * b, radius) - mu_b_sq
    sigma_ab = _uniform_filter(a * b, radius) - mu_ab

    numerator = (2 * mu_ab + _C1) * (2 * sigma_ab + _C2)
    denominator = (mu_a_sq + mu_b_sq + _C1) * (sigma_a_sq + sigma_b_sq + _C2)
    score_map = numerator / denominator

    if mask is not None:
        if not mask.any():
            return 1.0
        return float(score_map[mask].mean())
    return float(score_map.mean())


def _erode_boolean(free: np.ndarray, radius: int) -> np.ndarray:
    """Return ``free`` shrunk by ``radius`` (a pixel survives only if its whole
    (2r+1)^2 window is free)."""
    if radius < 1:
        return free
    padded = np.pad(free.astype(np.int64), radius, mode="constant")
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    integral = np.pad(integral, ((1, 0), (1, 0)), mode="constant")
    window = 2 * radius + 1
    height, width = free.shape
    counts = (
        integral[window:window + height, window:window + width]
        - integral[0:height, window:window + width]
        - integral[window:window + height, 0:width]
        + integral[0:height, 0:width]
    )
    return counts == window * window


def outside_mask_ssim(
    original: Image.Image,
    edited: Image.Image,
    mask: Optional[Image.Image],
    radius: int = 3,
) -> float:
    """SSIM restricted to the region *outside* the edit mask.

    This is the key guardrail: untouched pixels must stay effectively identical
    (threshold ``outside_mask_ssim_min`` in each recipe). The measured region is
    eroded by the SSIM window radius so that window bleed from the edited region
    does not count against the score.
    """
    if mask is None:
        return ssim(original, edited, radius=radius)

    mask_array = np.asarray(mask.convert("L"))
    if mask_array.shape != _to_gray_array(original).shape:
        mask_array = np.asarray(
            mask.convert("L").resize(original.size), dtype=np.uint8
        )
    outside = mask_array == 0
    eroded = _erode_boolean(outside, radius)
    region = eroded if eroded.any() else outside
    return ssim(original, edited, radius=radius, mask=region)
