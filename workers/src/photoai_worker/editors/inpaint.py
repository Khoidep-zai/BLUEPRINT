"""Inpainting editor (AGENT_SKILLS S5).

Runs an edit through a provider adapter on a mask region. In P0 the "model" is
the mock provider; a real LaMa/diffusion inpaint adapter is swapped in via the
provider registry without changing this code.
"""
from __future__ import annotations

from typing import Optional

from PIL import Image

from providers.base import ImageEditProvider


def inpaint(
    image: Image.Image,
    mask: Image.Image,
    provider: ImageEditProvider,
    prompt: str = "",
    strength: float = 0.5,
    seed: int = 42,
) -> Image.Image:
    """Inpaint ``mask`` region of ``image`` using ``provider``."""
    if mask is None:
        raise ValueError("inpaint requires a mask")
    return provider.edit(image, mask=mask, prompt=prompt, strength=strength, seed=seed)
