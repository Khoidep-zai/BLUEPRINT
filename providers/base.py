"""ImageEditProvider interface - all external/internal edit models go through here."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image


@dataclass
class EditResult:
    image: Image.Image
    model_version: str
    seed: int
    strength: float
    latency_ms: float
    cost_usd: float
    warnings: list[str]


class ImageEditProvider:
    """Adapter contract for image editing providers.

    Only `providers/` may import external SDKs. All other modules must use
    this interface so providers can be swapped by configuration.
    """

    name: str = "base"

    async def edit(
        self,
        image: Image.Image,
        prompt: str,
        *,
        mask: Optional[Image.Image] = None,
        strength: float = 0.5,
        seed: Optional[int] = None,
    ) -> EditResult:
        """Run an edit on `image` guided by `prompt`.

        Args:
            image: source image (never mutated by provider).
            mask: optional mask image, same size as `image` (0=keep, 255=edit).
            strength: edit strength, 0..1.
            seed: deterministic seed when supported.

        Returns:
            EditResult with edited PIL image and metadata.
        """
        raise NotImplementedError

    async def health(self) -> bool:
        """Return True if provider is reachable."""
        raise NotImplementedError

    def close(self) -> None:
        """Release provider resources."""
        return None
