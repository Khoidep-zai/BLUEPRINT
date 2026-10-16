"""Face parsing: which pixels are skin (design §2 face_parsing.py).

Target model: BiSeNet, segmenting 19 facial regions (skin, eyes, nose, lips,
hair, beard). Used by recipes 1/2/8/9 to restrict retouching to skin. Offline it
uses a YCbCr skin heuristic masked to the face box and excluding the eye/mouth
bands.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image, ImageFilter

from photoai.engine.vram_manager import load_model
from .face_analyzer import FaceBox

MODEL_KEY = "bisenet"


def _ycrcb_skin(rgb: np.ndarray) -> np.ndarray:
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    luma = 0.299 * red + 0.587 * green + 0.114 * blue
    cb = 128.0 - 0.168736 * red - 0.331264 * green + 0.5 * blue
    cr = 128.0 + 0.5 * red - 0.418688 * green - 0.081312 * blue
    return (cb >= 77) & (cb <= 127) & (cr >= 133) & (cr <= 173) & (luma > 40)


def skin_mask(image: Image.Image, face: Optional[FaceBox] = None) -> Image.Image:
    """Return an ``L``-mode mask (255 = skin)."""
    source = image.convert("RGB")
    width, height = source.size

    model = load_model(MODEL_KEY)
    if model is not None:
        try:  # pragma: no cover - requires real weights
            out = model(np.asarray(source, dtype=np.uint8))
            mask = np.asarray(out)
            if mask.ndim == 3:
                mask = mask[..., 0]
            return Image.fromarray((mask > 127).astype(np.uint8) * 255, mode="L")
        except Exception:
            pass

    rgb = np.asarray(source, dtype=np.float64)
    skin = _ycrcb_skin(rgb)

    box = face or FaceBox(0, 0, width, height)
    region = np.zeros((height, width), dtype=bool)
    x0, y0 = max(0, box.x), max(0, box.y)
    x1, y1 = min(width, box.x + box.width), min(height, box.y + box.height)
    region[y0:y1, x0:x1] = True

    # Exclude the eye and mouth bands inside the face so they are never smoothed.
    eye_band = slice(int(box.y + box.height * 0.30), int(box.y + box.height * 0.55))
    mouth_band = slice(int(box.y + box.height * 0.72), int(box.y + box.height * 0.95))
    for band in (eye_band, mouth_band):
        region[band, max(0, box.x) : min(width, box.x + box.width)] = False

    mask = (skin & region).astype(np.uint8) * 255
    result = Image.fromarray(mask, mode="L").filter(ImageFilter.GaussianBlur(2.0))
    return result


def skin_coverage(image: Image.Image, face: Optional[FaceBox] = None) -> float:
    """Fraction of the image classified as skin (0..1)."""
    mask = np.asarray(skin_mask(image, face), dtype=np.float32) / 255.0
    return float(mask.mean())
