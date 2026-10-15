"""Colour science editor (AGENT_SKILLS S8).

P0 placeholder: gray-world white balance with clamping to avoid highlight
clipping. The learned tone-mapping model lands in P2.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def white_balance(image: Image.Image, strength: float = 0.5) -> Image.Image:
    """Apply gray-world white balance, blended by ``strength`` in [0, 1]."""
    array = np.asarray(image.convert("RGB"), dtype=np.float32)
    channel_means = array.reshape(-1, 3).mean(axis=0)
    gray = float(channel_means.mean())
    gains = gray / np.maximum(channel_means, 1e-6)
    gains = 1.0 + (gains - 1.0) * float(np.clip(strength, 0.0, 1.0))
    balanced = np.clip(array * gains.reshape(1, 1, 3), 0, 255)
    return Image.fromarray(balanced.astype(np.uint8), mode="RGB")
