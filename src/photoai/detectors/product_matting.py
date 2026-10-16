"""Product matting (design §2 product_matting.py, recipe 10).

Target models: BiRefNet / MODNet — a soft alpha matte including fine hair/fibre
edges. Recipe 10 uses this matte to keep the product's own pixels bit-identical
while compositing a new studio backdrop behind it.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image, ImageFilter

from photoai.engine.vram_manager import load_model

MODEL_KEY = "birefnet"


def product_alpha(image: Image.Image, mask: Optional[Image.Image] = None) -> Image.Image:
    """Return an ``L``-mode alpha matte (255 = product, 0 = background)."""
    source = image.convert("RGB")

    if mask is not None:
        return mask.convert("L").resize(source.size)

    model = load_model(MODEL_KEY)
    if model is not None:
        try:  # pragma: no cover - requires real weights
            out = model(np.asarray(source, dtype=np.uint8))
            alpha = np.asarray(out)
            if alpha.ndim == 3:
                alpha = alpha[..., 0]
            return Image.fromarray(np.clip(alpha, 0, 255).astype(np.uint8), mode="L")
        except Exception:
            pass

    return _background_diff_alpha(source)


def _background_diff_alpha(source: Image.Image) -> Image.Image:
    """Estimate the backdrop colour from the border and keep the rest."""
    rgb = np.asarray(source, dtype=np.float64)
    height, width = rgb.shape[:2]
    border = 4
    edges = np.concatenate(
        [
            rgb[:border].reshape(-1, 3),
            rgb[-border:].reshape(-1, 3),
            rgb[:, :border].reshape(-1, 3),
            rgb[:, -border:].reshape(-1, 3),
        ]
    )
    backdrop = edges.mean(axis=0)
    distance = np.sqrt(((rgb - backdrop) ** 2).sum(axis=2))
    alpha = np.clip((distance - 12.0) / 40.0, 0.0, 1.0)
    # Lock the product interior as fully opaque (recipe 10 must keep its pixels).
    alpha[alpha >= 0.98] = 1.0

    alpha_img = Image.fromarray((alpha * 255).astype(np.uint8), mode="L")
    alpha_img = alpha_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    return alpha_img.filter(ImageFilter.GaussianBlur(1.5))


def product_bounding_box(alpha: Image.Image) -> Optional[tuple[int, int, int, int]]:
    """Return ``(x0, y0, x1, y1)`` of the matte's non-zero region."""
    arr = np.asarray(alpha.convert("L"), dtype=np.uint8)
    ys, xs = np.where(arr > 128)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
