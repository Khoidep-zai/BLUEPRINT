"""Mock edit provider for offline development and testing."""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from providers.base import EditResult, ImageEditProvider


class MockProvider(ImageEditProvider):
    """Deterministic mock: blends source with a subtle tint and labels via metadata.

    Never calls external services. Useful for CI and contract tests.
    """

    name = "mock"

    def __init__(self, delay_ms: float = 50.0, fail: bool = False) -> None:
        self.delay_ms = delay_ms
        self.fail = fail
        self.calls: list[dict] = []

    async def edit(
        self,
        image: Image.Image,
        prompt: str,
        *,
        mask: Optional[Image.Image] = None,
        strength: float = 0.5,
        seed: Optional[int] = None,
    ) -> EditResult:
        start = time.perf_counter()
        await asyncio.sleep(self.delay_ms / 1000.0)

        self.calls.append(
            {
                "prompt": prompt,
                "strength": strength,
                "seed": seed,
                "size": image.size,
                "has_mask": mask is not None,
            }
        )

        if self.fail:
            raise TimeoutError("mock provider timeout")

        src = image.convert("RGB")
        w, h = src.size
        out = Image.new("RGB", (w, h))
        px = out.load()
        spx = src.load()
        # Subtle deterministic tint so output differs from input but structure stays.
        for y in range(h):
            for x in range(w):
                r, g, b = spx[x, y]
                px[x, y] = (
                    min(255, int(r * 0.98 + 8)),
                    min(255, int(g * 0.98 + 4)),
                    min(255, int(b * 0.98 + 2)),
                )

        latency_ms = (time.perf_counter() - start) * 1000.0
        return EditResult(
            image=out,
            model_version="mock:v1",
            seed=seed or 0,
            strength=strength,
            latency_ms=latency_ms,
            cost_usd=0.0,
            warnings=[],
        )

    async def health(self) -> bool:
        return not self.fail
