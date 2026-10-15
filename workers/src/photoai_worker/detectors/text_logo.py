"""Text / logo detection for watermark removal (AGENT_SKILLS S4).

P1: lightweight text-region heuristic using OpenCV (MSER / edge density) when
available, falling back to empty list (P0 behaviour). A real OCR/logo detector
lands in a later phase.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from PIL import Image

try:
    import cv2  # type: ignore
    import numpy as np
    _HAVE_OPENCV = True
except Exception:  # pragma: no cover
    _HAVE_OPENCV = False
    cv2 = None  # type: ignore
    np = None  # type: ignore


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
    """Return detected text/logo regions.

    P1 heuristic: use MSER (Maximally Stable Extremal Regions) to find
    text-like blobs, then merge nearby ones. Falls back to ``[]`` when OpenCV
    is unavailable.
    """
    if not _HAVE_OPENCV or cv2 is None or np is None:
        return []

    gray = np.array(image.convert("L"), dtype=np.uint8)
    mser = cv2.MSER_create(_delta=5, _min_area=60, _max_area=14000)
    regions, _ = mser.detectRegions(gray)

    boxes: List[TextRegion] = []
    for region in regions:
        x, y, w, h = cv2.boundingRect(region)
        if w < 8 or h < 8:
            continue
        boxes.append(TextRegion(x=int(x), y=int(y), width=int(w), height=int(h)))

    # Merge overlapping/nearby boxes into larger text regions.
    return _merge_boxes(boxes)


def _merge_boxes(boxes: List[TextRegion]) -> List[TextRegion]:
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: (b.y, b.x))
    merged: List[TextRegion] = []
    current = boxes[0]
    for nxt in boxes[1:]:
        overlap_x = min(current.x + current.width, nxt.x + nxt.width) - max(current.x, nxt.x)
        overlap_y = min(current.y + current.height, nxt.y + nxt.height) - max(current.y, nxt.y)
        if overlap_x > 0 and overlap_y > 0:
            x0 = min(current.x, nxt.x)
            y0 = min(current.y, nxt.y)
            x1 = max(current.x + current.width, nxt.x + nxt.width)
            y1 = max(current.y + current.height, nxt.y + nxt.height)
            current = TextRegion(
                x=x0, y=y0, width=x1 - x0, height=y1 - y0,
                label="merged", score=max(current.score, nxt.score),
            )
        else:
            merged.append(current)
            current = nxt
    merged.append(current)
    return merged


def merge_regions(regions: Sequence[TextRegion]) -> Optional[TextRegion]:
    """Merge overlapping regions into their bounding box (helper for masking)."""
    if not regions:
        return None
    x0 = min(region.x for region in regions)
    y0 = min(region.y for region in regions)
    x1 = max(region.x + region.width for region in regions)
    y1 = max(region.y + region.height for region in regions)
    return TextRegion(x=x0, y=y0, width=x1 - x0, height=y1 - y0, label="merged")
