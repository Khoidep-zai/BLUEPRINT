"""Face restoration wrapper (design §2 face_restorer_gpu.py, recipe 7).

Restores facial detail on old photos with CodeFormer at fidelity weight ``w``
(higher ``w`` = closer to the degraded original = safer identity). Offline it
uses a detail-preserving unsharp step that sharpens structure without inventing
new features.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from PIL import Image, ImageFilter

from photoai.engine.vram_manager import load_model, register_model_loader

MODEL_KEY = "codeformer"


def _unsharp(image: Image.Image, amount: float, radius: float = 1.6) -> Image.Image:
    """Classical detail-preserving sharpen (kept deterministic, no hallucination)."""
    source = image.convert("RGB")
    blurred = source.filter(ImageFilter.GaussianBlur(radius))
    src = np.asarray(source, dtype=np.float32)
    blur = np.asarray(blurred, dtype=np.float32)
    sharpened = src + (src - blur) * amount
    return Image.fromarray(np.clip(sharpened, 0, 255).astype(np.uint8), mode="RGB")


def restore_face(
    image: Image.Image,
    mask: Optional[Image.Image] = None,
    fidelity: float = 0.85,
    strength: float = 0.6,
) -> Image.Image:
    """Restore facial detail; ``fidelity`` mirrors CodeFormer's ``w`` weight."""
    source = image.convert("RGB")

    model: Optional[Callable[..., np.ndarray]] = load_model(MODEL_KEY)
    if model is not None:
        try:
            mask_arr = None
            if mask is not None:
                mask_arr = np.asarray(mask.convert("L").resize(source.size), dtype=np.uint8)
            out = model(np.asarray(source, dtype=np.uint8), mask_arr, fidelity)
            return Image.fromarray(np.asarray(out, dtype=np.uint8))
        except Exception:  # pragma: no cover - GPU failure -> CPU fallback
            pass

    sharpened = _unsharp(source, amount=float(np.clip(strength, 0.0, 1.0)) * 1.5)
    if mask is None:
        return sharpened

    mask_l = mask.convert("L")
    if mask_l.size != source.size:
        mask_l = mask_l.resize(source.size)
    alpha = (np.asarray(mask_l, dtype=np.float32) / 255.0)[:, :, None]
    blended = np.asarray(source, dtype=np.float32) * (1 - alpha) + np.asarray(
        sharpened, dtype=np.float32
    ) * alpha
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGB")


__all__ = ["restore_face", "register_model_loader", "MODEL_KEY"]
