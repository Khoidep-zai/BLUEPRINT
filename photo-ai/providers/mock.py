"""Deterministic mock provider (AGENT_SKILLS S2 / P0 task 4).

The mock must return an image that can be *verified* in tests:

* Outside the mask the output is byte-identical to the input.
* Inside the mask (or everywhere, when no mask is given) the output is shifted
  toward a deterministic tint derived from ``seed`` and ``strength``.
* The same ``(image, mask, strength, seed)`` always yields the same output.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image

from .base import ImageEditProvider

# Deterministic tint the mock blends toward, one channel offset per channel.
_BASE_TINT = np.array([24.0, -12.0, 18.0], dtype=np.float32)


class MockProvider(ImageEditProvider):
    """Provider adapter used for tests and local development."""

    name = "mock"
    model_version = "mock-1"
    cost_per_call_usd = 0.0

    def _edit(
        self,
        image: Image.Image,
        mask: Optional[Image.Image],
        prompt: str,
        strength: float,
        seed: int,
    ) -> Image.Image:
        source = image.convert("RGB")
        array = np.asarray(source, dtype=np.float32)

        # Direction of the shift is deterministic in the seed.
        rng = np.random.default_rng(seed)
        jitter = rng.uniform(-6.0, 6.0, size=3).astype(np.float32)
        tint = (_BASE_TINT + jitter) * float(np.clip(strength, 0.0, 1.0))

        shifted = np.clip(array + tint.reshape(1, 1, 3), 0, 255)

        if mask is None:
            blended = shifted
        else:
            alpha = self._mask_alpha(mask, source.size)
            blended = array * (1.0 - alpha) + shifted * alpha

        return Image.fromarray(blended.astype(np.uint8), mode="RGB")

    @staticmethod
    def _mask_alpha(mask: Image.Image, size: tuple[int, int]) -> np.ndarray:
        """Return a float alpha in [0, 1] shaped ``(h, w, 1)`` from a mask."""
        mask_gray = mask.convert("L")
        if mask_gray.size != size:
            mask_gray = mask_gray.resize(size)
        alpha = np.asarray(mask_gray, dtype=np.float32) / 255.0
        return alpha[:, :, None]
