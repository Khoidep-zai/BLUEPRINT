"""Product studio compositing editor (AGENT_SKILLS S10).

P0 placeholder with a stable interface; the background/reflection compositor
lands in P3.
"""
from __future__ import annotations

from typing import Optional

from PIL import Image

from providers.base import ImageEditProvider


def studio_composite(
    image: Image.Image,
    provider: Optional[ImageEditProvider] = None,
    mask: Optional[Image.Image] = None,
    prompt: str = "",
    strength: float = 0.4,
    seed: int = 42,
) -> Image.Image:
    """Composite ``image`` onto a studio background using ``provider`` if given."""
    if provider is not None:
        return provider.edit(
            image, mask=mask, prompt=prompt, strength=strength, seed=seed
        )
    return image.copy()
