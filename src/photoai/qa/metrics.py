"""Quantitative QA metrics (design §2 qa/metrics.py).

Measures, per recipe: Identity Cosine, SSIM, EAR, CIELAB Delta-E, Clip Ratio and
Texture Variance (Laplacian). Everything is pure NumPy/Pillow so QA is exact,
fast and deterministic offline; identity/OCR/person checks accept an injected
model callable and otherwise use a documented deterministic placeholder.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from PIL import Image

from photoai.detectors import eyes_gaze, face_analyzer

# --- constants ---------------------------------------------------------------
_C1 = (0.01 * 255) ** 2
_C2 = (0.03 * 255) ** 2

_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
_WHITE_D65 = np.array([0.95047, 1.00000, 1.08883])


@dataclass
class MetricsOptions:
    """Optional injected models so QA can use real detectors when present."""

    embedder: Optional[Callable[[Image.Image], Any]] = None
    ocr_detector: Optional[Callable[[Image.Image], List[str]]] = None
    person_detector: Optional[Callable[[Image.Image], Any]] = None
    skin_mask: Optional[Image.Image] = None
    product_mask: Optional[Image.Image] = None
    extra: Dict[str, Any] = field(default_factory=dict)


# --- SSIM --------------------------------------------------------------------
def _to_gray(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("L"), dtype=np.float64)


def _box_filter(array: np.ndarray, radius: int) -> np.ndarray:
    if radius < 1:
        return array
    padded = np.pad(array, radius, mode="reflect")
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    integral = np.pad(integral, ((1, 0), (1, 0)), mode="constant")
    window = 2 * radius + 1
    h, w = array.shape
    total = (
        integral[window : window + h, window : window + w]
        - integral[0:h, window : window + w]
        - integral[window : window + h, 0:w]
        + integral[0:h, 0:w]
    )
    return total / (window * window)


def ssim(image_a: Image.Image, image_b: Image.Image, radius: int = 3, mask: Optional[np.ndarray] = None) -> float:
    """Mean SSIM between two images (optionally restricted to a boolean mask)."""
    a, b = _to_gray(image_a), _to_gray(image_b)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")

    mu_a, mu_b = _box_filter(a, radius), _box_filter(b, radius)
    sigma_a = _box_filter(a * a, radius) - mu_a * mu_a
    sigma_b = _box_filter(b * b, radius) - mu_b * mu_b
    sigma_ab = _box_filter(a * b, radius) - mu_a * mu_b

    numerator = (2 * mu_a * mu_b + _C1) * (2 * sigma_ab + _C2)
    denominator = (mu_a * mu_a + mu_b * mu_b + _C1) * (sigma_a + sigma_b + _C2)
    score = numerator / denominator

    if mask is not None:
        return 1.0 if not mask.any() else float(score[mask].mean())
    return float(score.mean())


def _erode_boolean(free: np.ndarray, radius: int) -> np.ndarray:
    if radius < 1:
        return free
    padded = np.pad(free.astype(np.int64), radius, mode="constant")
    integral = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    integral = np.pad(integral, ((1, 0), (1, 0)), mode="constant")
    window = 2 * radius + 1
    h, w = free.shape
    counts = (
        integral[window : window + h, window : window + w]
        - integral[0:h, window : window + w]
        - integral[window : window + h, 0:w]
        + integral[0:h, 0:w]
    )
    return counts == window * window


def outside_mask_ssim(
    original: Image.Image,
    edited: Image.Image,
    mask: Optional[Image.Image],
    radius: int = 3,
) -> float:
    """SSIM restricted to pixels *outside* the edit mask (untouched-pixel guard)."""
    if mask is None:
        return ssim(original, edited, radius=radius)

    mask_array = np.asarray(mask.convert("L"))
    if mask_array.shape != _to_gray(original).shape:
        mask_array = np.asarray(mask.convert("L").resize(original.size), dtype=np.uint8)
    outside = mask_array == 0
    eroded = _erode_boolean(outside, radius)
    return ssim(original, edited, radius=radius, mask=eroded if eroded.any() else outside)


# --- identity ----------------------------------------------------------------
def _default_embedder(image: Image.Image) -> np.ndarray:
    """Deterministic 16x16 luminance descriptor (placeholder for ArcFace)."""
    gray = np.asarray(image.convert("L").resize((16, 16)), dtype=np.float64)
    vector = gray.flatten()
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return 0.0 if denom == 0.0 else float(np.dot(a, b) / denom)


def identity_cosine(
    original: Image.Image,
    edited: Image.Image,
    embedder: Optional[Callable[[Image.Image], np.ndarray]] = None,
) -> float:
    """Cosine similarity between the two images' identity descriptors."""
    embed = embedder or _default_embedder
    return cosine_similarity(embed(original), embed(edited))


# --- colour / texture --------------------------------------------------------
def _srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    normalized = rgb.astype(np.float64) / 255.0
    linear = np.where(normalized <= 0.04045, normalized / 12.92, ((normalized + 0.055) / 1.055) ** 2.4)
    xyz = (linear @ _RGB_TO_XYZ.T) / _WHITE_D65
    epsilon, kappa = 216 / 24389, 24389 / 27
    f = np.where(xyz > epsilon, np.cbrt(xyz), (kappa * xyz + 16) / 116)
    fx, fy, fz = f[..., 0], f[..., 1], f[..., 2]
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)


def _region_of(skin_mask: Image.Image, reference: Image.Image) -> np.ndarray:
    mask = np.asarray(skin_mask.convert("L"))
    if mask.shape != np.asarray(reference.convert("L")).shape:
        mask = np.asarray(skin_mask.convert("L").resize(reference.size), dtype=np.uint8)
    return mask > 127


def delta_e_skin(original: Image.Image, edited: Image.Image, skin_mask: Optional[Image.Image] = None) -> float:
    """CIE76 Delta-E between mean skin colour of original vs edited."""
    region = _region_of(skin_mask, original) if skin_mask is not None else None
    lab_a = _srgb_to_lab(np.asarray(original.convert("RGB"), dtype=np.float64))
    lab_b = _srgb_to_lab(np.asarray(edited.convert("RGB"), dtype=np.float64))
    if region is not None:
        if region.sum() == 0:
            # No skin pixels to compare (e.g. a flat synthetic frame) -> no drift.
            return 0.0
        mean_a, mean_b = lab_a[region].mean(axis=0), lab_b[region].mean(axis=0)
    else:
        mean_a, mean_b = lab_a.reshape(-1, 3).mean(axis=0), lab_b.reshape(-1, 3).mean(axis=0)
    return float(np.linalg.norm(mean_a - mean_b))


def texture_variance(image: Image.Image, region: Optional[np.ndarray] = None) -> float:
    """High-frequency (Laplacian-like) luminance variance — the anti-plastic metric."""
    gray = np.asarray(image.convert("L"), dtype=np.float64)
    laplacian = (
        -4 * gray
        + np.roll(gray, 1, 0)
        + np.roll(gray, -1, 0)
        + np.roll(gray, 1, 1)
        + np.roll(gray, -1, 1)
    )
    if region is not None and region.any():
        return float(laplacian[region].var())
    return float(laplacian.var())


def clip_ratio(image: Image.Image, low: int = 2, high: int = 253) -> float:
    """Fraction of pixels clipped at either end of the range."""
    array = np.asarray(image.convert("RGB"), dtype=np.uint8)
    return float(((array <= low) | (array >= high)).mean())


def structure_similarity(original: Image.Image, edited: Image.Image, size: tuple[int, int] = (64, 64)) -> float:
    """Normalised, exposure-invariant structural similarity in [0, 1]."""
    a = np.asarray(original.convert("L").resize(size), dtype=np.float64)
    b = np.asarray(edited.convert("L").resize(size), dtype=np.float64)
    a = (a - a.mean()) / (a.std() + 1e-8)
    b = (b - b.mean()) / (b.std() + 1e-8)
    return float(np.clip(1.0 - np.mean((a - b) ** 2) / 2.0, 0.0, 1.0))


def product_pixel_diff(original: Image.Image, edited: Image.Image, mask: Optional[Image.Image]) -> float:
    """Fraction of *locked* product pixels that changed (must be 0.0 for recipe 10).

    Only the fully-opaque product interior counts (matte > 250): soft matte edges
    are legitimately blended with the new backdrop and are not a violation.
    """
    a = np.asarray(original.convert("RGB"), dtype=np.float64)
    b = np.asarray(edited.convert("RGB"), dtype=np.float64)
    if a.shape != b.shape:
        b = np.asarray(edited.convert("RGB").resize(original.size), dtype=np.float64)
    diff = np.abs(a - b).max(axis=2)
    if mask is not None:
        mask_arr = np.asarray(mask.convert("L"))
        if mask_arr.shape != a.shape[:2]:
            mask_arr = np.asarray(mask.convert("L").resize(original.size), dtype=np.uint8)
        region = mask_arr > 250
        if not region.any():
            return 0.0
        return float((diff[region] > 2.0).mean())
    return float((diff > 2.0).mean())


# --- re-checks ---------------------------------------------------------------
def ocr_recheck(edited: Image.Image, detector: Optional[Callable[[Image.Image], List[str]]] = None) -> bool:
    """True when no watermark/logo text remains (no detector -> pass-through)."""
    if detector is None:
        return True
    return len(detector(edited)) == 0


def person_recheck(edited: Image.Image, detector: Optional[Callable[[Image.Image], Any]] = None) -> bool:
    """True when no bystander remains (no detector -> pass-through)."""
    if detector is None:
        return True
    return len(detector(edited)) == 0


# --- aggregation -------------------------------------------------------------
_BOOLEAN_KEYS = {"ocr_recheck", "person_recheck"}


def compute_metrics(
    context: Any,
    thresholds: Optional[Dict[str, Any]] = None,
    options: Optional[MetricsOptions] = None,
) -> Dict[str, Any]:
    """Compute every metric the recipe's ``thresholds`` gate on (plus core ones)."""
    thresholds = thresholds or {}
    options = options or MetricsOptions()
    original = context.original
    edited = context.image
    metrics: Dict[str, Any] = {}

    # EAR (re-measured on the *edited* image, not the input).
    eyes = context.detections.get("eyes")
    if eyes is not None and thresholds.get("ear_min") is not None:
        rechecked = eyes_gaze.recheck_ear(
            edited, face=context.detections.get("main_face"), previous=eyes, params=context.params
        )
        metrics["ear"] = round(float((rechecked or eyes).ear), 6)
    elif eyes is not None:
        metrics["ear"] = round(float(eyes.ear), 6)

    if original is not None and edited is not None:
        comparison = edited if edited.size == original.size else edited.resize(original.size, Image.LANCZOS)

        metrics["identity_cosine"] = round(
            identity_cosine(original, comparison, embedder=options.embedder), 6
        )
        metrics["outside_mask_ssim"] = round(outside_mask_ssim(original, comparison, context.edit_mask), 6)
        metrics["structure_similarity"] = round(structure_similarity(original, comparison), 6)
        metrics["clip_ratio"] = round(clip_ratio(edited), 6)
        metrics["max_edge"] = int(max(edited.size))

        skin_gated = (
            thresholds.get("delta_e_skin_max") is not None
            or thresholds.get("texture_variance_min") is not None
        )
        if options.skin_mask is not None or skin_gated:
            region = _region_of(options.skin_mask, original) if options.skin_mask is not None else None
            metrics["delta_e_skin"] = round(delta_e_skin(original, comparison, options.skin_mask), 6)
            metrics["texture_variance"] = round(texture_variance(comparison, region), 6)

        if thresholds.get("product_pixel_diff_max") is not None:
            product_mask = (
                options.product_mask
                or context.edit_mask
                or context.detections.get("product_alpha")
            )
            metrics["product_pixel_diff"] = round(product_pixel_diff(original, comparison, product_mask), 6)

    metrics["ocr_recheck"] = ocr_recheck(edited, detector=options.ocr_detector)
    metrics["person_recheck"] = person_recheck(edited, detector=options.person_detector)
    return metrics


__all__ = [
    "MetricsOptions",
    "ssim",
    "outside_mask_ssim",
    "identity_cosine",
    "cosine_similarity",
    "delta_e_skin",
    "texture_variance",
    "clip_ratio",
    "structure_similarity",
    "product_pixel_diff",
    "ocr_recheck",
    "person_recheck",
    "compute_metrics",
]
