"""Relighting editor (AGENT_SKILLS S8).

P0 placeholder with a stable interface; the real relight model lands in P2.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image

from providers.base import ImageEditProvider


def relight(
    image: Image.Image,
    provider: Optional[ImageEditProvider] = None,
    mask: Optional[Image.Image] = None,
    prompt: str = "",
    strength: float = 0.4,
    seed: int = 42,
) -> Image.Image:
    """Relight ``image`` (optionally within ``mask``).

    With a provider, delegates the model call; without one, applies a mild
    deterministic warm-gain as a stand-in so the pipeline stays runnable.
    """
    if provider is not None:
        return provider.edit(
            image, mask=mask, prompt=prompt, strength=strength, seed=seed
        )
    array = np.asarray(image.convert("RGB"), dtype=np.float32)
    gain = np.array([1.0 + 0.05 * strength, 1.0 + 0.02 * strength, 1.0 - 0.03 * strength])
    warmed = np.clip(array * gain.reshape(1, 1, 3), 0, 255)
    return Image.fromarray(warmed.astype(np.uint8), mode="RGB")
