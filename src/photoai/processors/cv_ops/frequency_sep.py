"""Frequency separation: "no plastic skin, keep the pores" (design §3.2).

Splits the image into a low-frequency layer (skin tone, shading, colour) and a
high-frequency layer (pores, hair, fabric weave). Retouching only touches the
low layer; the original high layer is re-injected so real texture survives.

Runs on OpenCV when it is installed and on a pure NumPy implementation
otherwise, so the algorithm is identical-ish and always available offline.
"""
from __future__ import annotations

import numpy as np

try:  # OpenCV is optional — NumPy fallbacks below keep the app runnable.
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - minimal installs
    cv2 = None  # type: ignore


def _gaussian_kernel(sigma: float) -> np.ndarray:
    radius = int(round(3.0 * sigma))
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-(x * x) / (2.0 * sigma * sigma), dtype=np.float32)
    return kernel / kernel.sum()


def gaussian_blur(image: np.ndarray, sigma: float) -> np.ndarray:
    """Blur a ``(H, W)`` or ``(H, W, C)`` float array with a sigma-Gaussian in float32."""
    if sigma <= 0:
        return image.astype(np.float32, copy=True)
    if cv2 is not None:
        ksize = int(2 * round(3 * sigma) + 1)
        return cv2.GaussianBlur(image, (ksize, ksize), sigma).astype(np.float32)

    kernel = _gaussian_kernel(sigma)
    radius = (len(kernel) - 1) // 2
    work = image.astype(np.float32, copy=False)
    squeeze = work.ndim == 2
    if squeeze:
        work = work[:, :, None]

    # Separable convolution along x then y with reflect padding.
    pad_x = np.pad(work, ((0, 0), (radius, radius), (0, 0)), mode="reflect")
    tmp = np.zeros_like(work, dtype=np.float32)
    for i, weight in enumerate(kernel):
        tmp += weight * pad_x[:, i : i + work.shape[1], :]

    pad_y = np.pad(tmp, ((radius, radius), (0, 0), (0, 0)), mode="reflect")
    out = np.zeros_like(work, dtype=np.float32)
    for i, weight in enumerate(kernel):
        out += weight * pad_y[i : i + work.shape[0], :, :]

    return out[:, :, 0] if squeeze else out


class FrequencySeparator:
    """Decompose / smooth / recombine an RGB image across frequency bands."""

    @staticmethod
    def decompose(img_rgb: np.ndarray, sigma: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(low_freq, high_freq)`` for an 8-bit ``img_rgb``.

        * ``low_freq``  — float32 in [0, 1]: tone, colour, shading.
        * ``high_freq`` — float32 around 0: pores, hair, fabric texture.
        """
        img_f = img_rgb.astype(np.float32) / 255.0
        low_freq = gaussian_blur(img_f, sigma)
        high_freq = img_f - low_freq
        return low_freq, high_freq

    @staticmethod
    def smooth_low_frequency(
        low_freq: np.ndarray,
        diameter: int = 9,
        sigma_color: float = 0.08,
        sigma_space: float = 9.0,
    ) -> np.ndarray:
        """Edge-preserving smooth of the low band (keeps the face outline)."""
        if cv2 is not None:
            return cv2.bilateralFilter(low_freq, diameter, sigma_color, sigma_space)

        radius = max(1, diameter // 2)
        work = low_freq.astype(np.float32, copy=False)
        out = np.zeros_like(work, dtype=np.float32)
        weight_sum = np.full(work.shape[:2], 1e-8, dtype=np.float32)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                shifted = np.roll(np.roll(work, dy, axis=0), dx, axis=1)
                spatial = np.exp(-(dx * dx + dy * dy) / (2.0 * sigma_space * sigma_space), dtype=np.float32)
                diff = ((work - shifted) ** 2).sum(axis=2)
                color = np.exp(-diff / (2.0 * sigma_color * sigma_color), dtype=np.float32)
                weight = spatial * color
                out += shifted * weight[:, :, None]
                weight_sum += weight
        return (out / weight_sum[:, :, None]).astype(np.float32)

    @staticmethod
    def recombine(
        edited_img_rgb: np.ndarray,
        original_high_freq: np.ndarray,
        skin_mask: np.ndarray,
        hf_restore_strength: float = 0.85,
        sigma: float = 3.0,
    ) -> np.ndarray:
        """Blend processed low band + original high band inside ``skin_mask`` with zero-copy broadcasting."""
        edited_low, _ = FrequencySeparator.decompose(edited_img_rgb, sigma=sigma)
        restored = np.clip(edited_low + original_high_freq * hf_restore_strength, 0.0, 1.0)

        orig_f = edited_img_rgb.astype(np.float32) / 255.0
        # Broadcast mask without allocating a 3-channel duplicate array
        mask = skin_mask[:, :, None] if skin_mask.ndim == 2 else skin_mask
        blended = orig_f * (1.0 - mask) + restored * mask
        return (blended * 255.0).astype(np.uint8)

