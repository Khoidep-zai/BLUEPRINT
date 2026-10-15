"""Text / logo detection for watermark removal (AGENT_SKILLS S4).

P0 placeholder with a stable interface; OCR/logo detection lands in P1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from PIL import Image


@dataclass
class TextRegion:
    """A detected text/logo region in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int
    label: str = "text"
    score: float = 1.0

    @property
    def area(self) -> int:
        return self.width * self.height


def detect_text_logo(image: Image.Image) -> List[TextRegion]:
    """Return detected text/logo regions. P0 placeholder returns an empty list."""
    return []


def merge_regions(regions: Sequence[TextRegion]) -> Optional[TextRegion]:
    """Merge overlapping regions into their bounding box (helper for masking)."""
    if not regions:
        return None
    x0 = min(region.x for region in regions)
    y0 = min(region.y for region in regions)
    x1 = max(region.x + region.width for region in regions)
    y1 = max(region.y + region.height for region in regions)
    return TextRegion(x=x0, y=y0, width=x1 - x0, height=y1 - y0, label="merged")
