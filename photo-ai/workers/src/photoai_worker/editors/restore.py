"""Old photo restoration editor (AGENT_SKILLS S9).

P0 placeholder: mild denoise through the provider or a no-op. The full
classify -> mask damage -> inpaint -> denoise -> restore -> colourise chain
lands in P3.
"""
from __future__ import annotations

from typing import Optional

from PIL import Image

from providers.base import ImageEditProvider


def restore(
    image: Image.Image,
    provider: Optional[ImageEditProvider] = None,
    mask: Optional[Image.Image] = None,
    prompt: str = "",
    strength: float = 0.4,
    seed: int = 42,
) -> Image.Image:
    """Restore ``image`` using ``provider`` when available."""
    if provider is not None:
        return provider.edit(
            image, mask=mask, prompt=prompt, strength=strength, seed=seed
        )
    return image.copy()
