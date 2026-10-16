"""Relighting wrapper (design §2 relighter_gpu.py, recipes 8/9/10).

IC-Light relights a subject from a text prompt (warm sun, studio, background).
Offline it applies the equivalent classical grade: warm rim light for golden
hour, white-balance + shadow lift for low light, and a generated studio backdrop
for product shots.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from PIL import Image

from photoai.engine.vram_manager import load_model, register_model_loader
from photoai.processors.cv_ops import color_lighting

MODEL_KEY = "ic_light"


def _grade_golden_hour(rgb: np.ndarray, strength: float) -> np.ndarray:
    """Warm, slightly lifted shadows with a soft highlight roll-off."""
    out = rgb.astype(np.float32)
    gains = np.array([1.0 + 0.14 * strength, 1.0 + 0.06 * strength, 1.0 - 0.10 * strength])
    out = out * gains.reshape(1, 1, 3)
    # Rim-light: brighten along the horizontal gradient (sun coming from the left).
    width = out.shape[1]
    rim = np.linspace(1.0 + 0.08 * strength, 1.0, width).reshape(1, width, 1)
    out = out * rim
    return np.clip(out, 0, 255)


def _grade_low_light(rgb: np.ndarray, strength: float) -> np.ndarray:
    """Neutralise the colour cast and lift deep shadows without clipping."""
    balanced = color_lighting.gray_world_white_balance(rgb).astype(np.float32)
    # Shadow lift via gamma < 1, easing off near the highlights.
    gamma = 1.0 - 0.35 * float(np.clip(strength, 0.0, 1.0))
    lifted = np.power(balanced / 255.0, gamma) * 255.0
    return np.clip(lifted, 0, 255)


def studio_background(size: tuple[int, int], seed: int = 42) -> np.ndarray:
    """Generate a luxury studio backdrop: soft vertical gradient + vignette."""
    width, height = size
    top = np.array([236.0, 238.0, 240.0])
    bottom = np.array([176.0, 180.0, 186.0])
    ramp = np.linspace(0.0, 1.0, height).reshape(height, 1, 1)
    backdrop = top.reshape(1, 1, 3) * (1 - ramp) + bottom.reshape(1, 1, 3) * ramp
    backdrop = np.repeat(backdrop, width, axis=1)

    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = width / 2.0, height * 0.45
    dist = np.sqrt(((xx - cx) / width) ** 2 + ((yy - cy) / height) ** 2)
    vignette = np.clip(1.0 - 0.35 * (dist / dist.max()), 0.65, 1.0)
    return np.clip(backdrop * vignette[:, :, None], 0, 255).astype(np.uint8)


def relight(
    image: Image.Image,
    mask: Optional[Image.Image] = None,
    mode: str = "golden_hour",
    strength: float = 0.5,
    seed: int = 42,
) -> Image.Image:
    """Relight ``image`` according to ``mode`` (``golden_hour``/``lowlight``/``studio``)."""
    source = image.convert("RGB")

    model: Optional[Callable[..., np.ndarray]] = load_model(MODEL_KEY)
    if model is not None:
        try:
            mask_arr = None
            if mask is not None:
                mask_arr = np.asarray(mask.convert("L").resize(source.size), dtype=np.uint8)
            out = model(np.asarray(source, dtype=np.uint8), mask_arr, mode, strength)
            return Image.fromarray(np.asarray(out, dtype=np.uint8))
        except Exception:  # pragma: no cover - GPU failure -> CPU fallback
            pass

    rgb = np.asarray(source, dtype=np.uint8)
    if mode == "lowlight":
        graded = _grade_low_light(rgb, strength)
    elif mode == "studio":
        graded = studio_background(source.size, seed=seed).astype(np.float32)
    else:
        graded = _grade_golden_hour(rgb, strength)
    return Image.fromarray(np.clip(graded, 0, 255).astype(np.uint8), mode="RGB")


__all__ = ["relight", "studio_background", "register_model_loader", "MODEL_KEY"]
