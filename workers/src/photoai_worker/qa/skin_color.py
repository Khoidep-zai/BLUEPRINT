"""Skin colour difference (AGENT_SKILLS S11).

Implements CIE76 Delta-E between the mean skin colour of the original and the
edited image, plus a texture-variance measure used to detect the "plastic skin"
failure mode (S7).
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from PIL import Image

# sRGB -> XYZ (D65) matrix, then XYZ -> Lab.
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
_WHITE_D65 = np.array([0.95047, 1.00000, 1.08883])


def _srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert an ``(..., 3)`` sRGB array in [0, 255] to CIE Lab."""
    normalized = rgb.astype(np.float64) / 255.0
    linear = np.where(
        normalized <= 0.04045,
        normalized / 12.92,
        ((normalized + 0.055) / 1.055) ** 2.4,
    )
    xyz = linear @ _RGB_TO_XYZ.T
    xyz_norm = xyz / _WHITE_D65
    epsilon = 216 / 24389
    kappa = 24389 / 27
    f = np.where(xyz_norm > epsilon, np.cbrt(xyz_norm), (kappa * xyz_norm + 16) / 116)
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]
    return np.stack(
        [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1
    )


def _mean_lab(image: Image.Image, region: Optional[np.ndarray]) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float64)
    lab = _srgb_to_lab(rgb)
    if region is not None:
        if region.sum() == 0:
            raise ValueError("skin region mask is empty")
        return lab[region].mean(axis=0)
    return lab.reshape(-1, 3).mean(axis=0)


def delta_e_skin(
    original: Image.Image,
    edited: Image.Image,
    skin_mask: Optional[Image.Image] = None,
) -> float:
    """Return the CIE76 Delta-E between mean skin colours of both images."""
    region: Optional[np.ndarray] = None
    if skin_mask is not None:
        mask_array = np.asarray(skin_mask.convert("L"))
        if mask_array.shape != np.asarray(original.convert("L")).shape:
            mask_array = np.asarray(
                skin_mask.convert("L").resize(original.size), dtype=np.uint8
            )
        region = mask_array > 127

    lab_a = _mean_lab(original, region)
    lab_b = _mean_lab(edited, region)
    return float(np.linalg.norm(lab_a - lab_b))


def texture_variance(image: Image.Image, region: Optional[np.ndarray] = None) -> float:
    """Return high-frequency variance of luminance (proxy for skin texture)."""
    gray = np.asarray(image.convert("L"), dtype=np.float64)
    # High-pass = difference from a 3x3 box mean.
    padded = np.pad(gray, 1, mode="reflect")
    neighbors = (
        padded[0:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, 0:-2] + padded[1:-1, 2:]
    ) / 4.0
    high_pass = gray - neighbors
    if region is not None:
        return float(high_pass[region].var())
    return float(high_pass.var())


def auto_skin_mask(image: Image.Image) -> Optional[Image.Image]:
    """Heuristic YCbCr skin mask (no model needed, self-hosted CPU).

    Returns an ``L``-mode mask, or ``None`` when the image contains no
    skin-like pixels. Used by the QA step to measure ``delta_e_skin`` for
    recipes that gate on it, even before a real face parser lands.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.float64)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    luma = 0.299 * red + 0.587 * green + 0.114 * blue
    cb = 128.0 - 0.168736 * red - 0.331264 * green + 0.5 * blue
    cr = 128.0 + 0.5 * red - 0.418688 * green - 0.081312 * blue
    mask = (cb >= 77) & (cb <= 127) & (cr >= 133) & (cr <= 173) & (luma > 40)
    if not mask.any():
        return None
    return Image.fromarray((mask.astype(np.uint8) * 255), mode="L")
