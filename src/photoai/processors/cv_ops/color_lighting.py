"""Classical colour & lighting operations (design §2 processors/cv_ops).

Pure NumPy/Pillow with an OpenCV fast path. These are the deterministic,
non-hallucinating grade operations the hybrid pipeline leans on for white
balance, LAB histogram matching and film grain.
"""
from __future__ import annotations

import numpy as np

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore

# sRGB -> linear -> XYZ (D65) -> Lab constants in float32.
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ],
    dtype=np.float32,
)
_XYZ_TO_RGB = np.linalg.inv(_RGB_TO_XYZ).astype(np.float32)
_WHITE_D65 = np.array([0.95047, 1.00000, 1.08883], dtype=np.float32)


def gray_world_white_balance(img_rgb: np.ndarray) -> np.ndarray:
    """Neutralise a colour cast by equalising per-channel means."""
    img = img_rgb.astype(np.float32)
    means = img.reshape(-1, 3).mean(axis=0)
    gray = float(means.mean())
    scale = gray / np.maximum(means, 1e-6)
    return np.clip(img * scale, 0, 255).astype(np.uint8)


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert ``(..., 3)`` sRGB in [0, 255] to CIE Lab in float32."""
    normalized = rgb.astype(np.float32) / 255.0
    linear = np.where(
        normalized <= 0.04045,
        normalized / 12.92,
        ((normalized + 0.055) / 1.055) ** 2.4,
    )
    xyz = (linear @ _RGB_TO_XYZ.T) / _WHITE_D65
    epsilon = 216.0 / 24389.0
    kappa = 24389.0 / 27.0
    f = np.where(xyz > epsilon, np.cbrt(xyz), (kappa * xyz + 16.0) / 116.0)
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]
    return np.stack([116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)], axis=-1)


def lab_to_srgb(lab: np.ndarray) -> np.ndarray:
    """Inverse of :func:`srgb_to_lab` in float32."""
    lab_f = lab.astype(np.float32, copy=False)
    fy = (lab_f[..., 0] + 16.0) / 116.0
    fx = fy + lab_f[..., 1] / 500.0
    fz = fy - lab_f[..., 2] / 200.0

    epsilon = 216.0 / 24389.0
    kappa = 24389.0 / 27.0

    def _finv(t: np.ndarray) -> np.ndarray:
        t3 = t ** 3
        return np.where(t3 > epsilon, t3, (116.0 * t - 16.0) / kappa)

    xyz = np.stack([_finv(fx), _finv(fy), _finv(fz)], axis=-1) * _WHITE_D65
    linear = xyz @ _XYZ_TO_RGB.T
    linear = np.clip(linear, 0.0, 1.0)
    srgb = np.where(
        linear <= 0.0031308,
        linear * 12.92,
        1.055 * (linear ** (1.0 / 2.4)) - 0.055,
    )
    return np.clip(srgb * 255.0, 0, 255).astype(np.uint8)



def lab_histogram_match(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Match ``source`` colour statistics to ``reference`` in Lab space.

    Used after a GPU edit to restore the original white balance / light
    direction without touching structure (design §4 recipe 1).
    """
    src_lab = srgb_to_lab(source).astype(np.float32)
    ref_lab = srgb_to_lab(reference).astype(np.float32)

    matched = src_lab.copy()
    for channel in range(3):
        src_c = src_lab[..., channel]
        ref_c = ref_lab[..., channel]
        src_std = src_c.std() + 1e-6
        ref_std = ref_c.std() + 1e-6
        matched[..., channel] = (src_c - src_c.mean()) * (ref_std / src_std) + ref_c.mean()
    return lab_to_srgb(matched)


def _tile_clahe(l_channel: np.ndarray, clip_limit: float, grid: int) -> np.ndarray:
    """Minimal tile-based CLAHE on a uint8 luminance channel (NumPy)."""
    height, width = l_channel.shape
    tile_h = max(1, height // grid)
    tile_w = max(1, width // grid)
    out = np.empty_like(l_channel, dtype=np.float64)

    for ty in range(0, height, tile_h):
        for tx in range(0, width, tile_w):
            tile = l_channel[ty : ty + tile_h, tx : tx + tile_w]
            hist, _ = np.histogram(tile, bins=256, range=(0, 256))
            limit = max(1, int(clip_limit * tile.size / 256))
            excess = np.maximum(hist - limit, 0).sum()
            hist = np.minimum(hist, limit)
            hist += excess // 256
            cdf = np.cumsum(hist).astype(np.float64)
            cdf /= max(cdf[-1], 1.0)
            mapped = np.interp(tile.flatten(), np.arange(256), cdf * 255)
            out[ty : ty + tile_h, tx : tx + tile_w] = mapped.reshape(tile.shape)
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_clahe_l_channel(img_rgb: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    """Contrast-limited local histogram equalisation on the L channel."""
    if cv2 is not None:
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        merged = cv2.merge([clahe.apply(l), a, b])
        return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)

    lab = srgb_to_lab(img_rgb)
    l = lab[..., 0]
    d65_l = 116 * (_WHITE_D65[1] ** (1 / 3)) - 16  # L of white
    l_uint8 = np.clip(l / d65_l * 255.0, 0, 255).astype(np.uint8)
    lab[..., 0] = _tile_clahe(l_uint8, clip_limit, 8).astype(np.float64) / 255.0 * d65_l
    return lab_to_srgb(lab)


def film_grain(img_rgb: np.ndarray, strength: float = 0.04, seed: int = 42) -> np.ndarray:
    """Add deterministic monochrome film grain."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, strength * 255.0, img_rgb.shape[:2]).astype(np.float32)
    out = img_rgb.astype(np.float32) + noise[:, :, None]
    return np.clip(out, 0, 255).astype(np.uint8)
