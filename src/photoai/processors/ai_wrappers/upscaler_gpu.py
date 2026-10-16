"""Tiled super-resolution wrapper (design §2 upscaler_gpu.py, recipe 1/2/7).

Real-ESRGAN / SwinIR run **tiled** (512px tiles, 64px overlap) so a 4x upscale of
a large photo never overflows VRAM. When the model is absent (no PyTorch or no
weights) it degrades to a high-quality Lanczos resize with the same tiling math.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from PIL import Image

from photoai.config import UPSCALE_MAX_LONG_EDGE
from photoai.engine.vram_manager import load_model, register_model_loader

MODEL_KEY = "realesrgan"
TILE = 512
OVERLAP = 64


def _target_size(size: tuple[int, int], scale: float, max_long_edge: int) -> tuple[int, int]:
    width = max(1, int(round(size[0] * scale)))
    height = max(1, int(round(size[1] * scale)))
    longest = max(width, height)
    if longest > max_long_edge:
        factor = max_long_edge / longest
        width = max(1, int(round(width * factor)))
        height = max(1, int(round(height * factor)))
    return width, height


def _run_tiled(model: Callable[[np.ndarray], np.ndarray], image: np.ndarray, scale: float) -> np.ndarray:
    """Apply an SR model tile-by-tile and stitch, avoiding VRAM spikes."""
    height, width = image.shape[:2]
    out_h, out_w = int(height * scale), int(width * scale)
    output = np.zeros((out_h, out_w, image.shape[2]), dtype=np.float32)
    weight = np.zeros((out_h, out_w, 1), dtype=np.float32)

    step = TILE - OVERLAP
    for y in range(0, height, step):
        for x in range(0, width, step):
            tile = image[y : y + TILE, x : x + TILE]
            scale_x = min(out_w, int((x + tile.shape[1]) * scale)) - int(x * scale)
            scale_y = min(out_h, int((y + tile.shape[0]) * scale)) - int(y * scale)
            if scale_x <= 0 or scale_y <= 0:
                continue
            upscaled = model(tile)
            upscaled = np.asarray(upscaled, dtype=np.float32)[:scale_y, :scale_x]
            oy, ox = int(y * scale), int(x * scale)
            output[oy : oy + upscaled.shape[0], ox : ox + upscaled.shape[1]] += upscaled
            weight[oy : oy + upscaled.shape[0], ox : ox + upscaled.shape[1]] += 1.0

    weight = np.maximum(weight, 1.0)
    return np.clip(output / weight, 0, 255).astype(np.uint8)


def upscale(
    image: Image.Image,
    scale: float = 4.0,
    max_long_edge: int = UPSCALE_MAX_LONG_EDGE,
) -> Image.Image:
    """Upscale ``image`` by ``scale``, honouring the long-edge VRAM cap."""
    source = image.convert("RGB")
    target = _target_size(source.size, scale, max_long_edge)
    if target == source.size:
        return source.copy()

    model: Optional[Callable[[np.ndarray], np.ndarray]] = load_model(MODEL_KEY)
    if model is not None:
        arr = np.asarray(source, dtype=np.uint8)
        try:
            out = _run_tiled(model, arr, scale)
            return Image.fromarray(out).resize(target, Image.LANCZOS)
        except Exception:  # pragma: no cover - GPU/model failure -> CPU fallback
            pass

    # Classical fallback: the same result contract without the AI hallucination.
    return source.resize(target, Image.LANCZOS)


__all__ = ["upscale", "register_model_loader", "MODEL_KEY"]
