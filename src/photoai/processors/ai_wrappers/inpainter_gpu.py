"""Inpainting wrapper (design §2 inpainter_gpu.py, recipes 2/5/6/7).

Fills masked regions (acne, watermarks, bystanders, tears) with LaMa on GPU, or
an SDXL/Flux ControlNet handoff registered under the same key. Falls back to
OpenCV's Telea inpaint, or a NumPy Laplacian diffusion fill, offline.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from PIL import Image

from photoai.engine.vram_manager import load_model, register_model_loader

MODEL_KEY = "lama"

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore


def _diffusion_inpaint(rgb: np.ndarray, mask: np.ndarray, iterations: int = 256) -> np.ndarray:
    """Fill the hole by iteratively averaging border pixels (Laplacian solve)."""
    out = rgb.astype(np.float32).copy()
    hole = mask > 127
    if not hole.any():
        return rgb
    for _ in range(iterations):
        neighbors = (
            np.roll(out, 1, axis=0)
            + np.roll(out, -1, axis=0)
            + np.roll(out, 1, axis=1)
            + np.roll(out, -1, axis=1)
        ) / 4.0
        out[hole] = neighbors[hole]
    return np.clip(out, 0, 255).astype(np.uint8)


def inpaint(
    image: Image.Image,
    mask: Image.Image,
    strength: float = 1.0,
    seed: int = 42,
) -> Image.Image:
    """Inpaint the masked region of ``image``."""
    source = image.convert("RGB")
    mask_l = mask.convert("L")
    if mask_l.size != source.size:
        mask_l = mask_l.resize(source.size)

    mask_arr = np.asarray(mask_l, dtype=np.uint8)
    if not (mask_arr > 127).any():
        return source.copy()

    model: Optional[Callable[..., np.ndarray]] = load_model(MODEL_KEY)
    if model is not None:
        try:
            out = model(np.asarray(source, dtype=np.uint8), mask_arr)
            return Image.fromarray(np.asarray(out, dtype=np.uint8))
        except Exception:  # pragma: no cover - GPU failure -> CPU fallback
            pass

    rgb = np.asarray(source, dtype=np.uint8)
    if cv2 is not None:
        filled = cv2.inpaint(rgb, mask_arr, 3, cv2.INPAINT_TELEA)
        return Image.fromarray(filled)
    return Image.fromarray(_diffusion_inpaint(rgb, mask_arr))


__all__ = ["inpaint", "register_model_loader", "MODEL_KEY"]
