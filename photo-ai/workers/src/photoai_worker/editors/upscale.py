"""Super-resolution editor (AGENT_SKILLS S6).

P0 placeholder: a Lanczos resize with the 8192px long-edge cap enforced. The
real tiled SR model replaces :func:`_resize` in P1 while keeping the interface.
"""
from __future__ import annotations

from PIL import Image

# Decision recorded in PROGRESS.md: cap the output long edge at 8192px.
MAX_LONG_EDGE = 8192


def _target_size(
    size: tuple[int, int],
    scale: float,
    max_long_edge: int,
) -> tuple[int, int]:
    width = max(1, int(round(size[0] * scale)))
    height = max(1, int(round(size[1] * scale)))
    longest = max(width, height)
    if longest > max_long_edge:
        factor = max_long_edge / longest
        width = max(1, int(round(width * factor)))
        height = max(1, int(round(height * factor)))
    return width, height


def upscale(
    image: Image.Image,
    scale: float = 2.0,
    max_long_edge: int = MAX_LONG_EDGE,
) -> Image.Image:
    """Upscale ``image`` by ``scale``, respecting ``max_long_edge``."""
    size = _target_size(image.size, scale, max_long_edge)
    if size == image.size:
        return image.copy()
    return image.resize(size, Image.LANCZOS)
