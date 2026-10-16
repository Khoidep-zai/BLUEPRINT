"""Watermark text detection + old-photo damage detection (design §2 ocr_damage.py).

Target models: PaddleOCR (watermark/logo text) + a scratch/tear detector for
recipe 7. Offline it uses OpenCV MSER / edge density, or a pure-NumPy gradient
grid, so watermark removal and scratch masking still work without models.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import numpy as np
from PIL import Image, ImageFilter

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore

TextDetector = Callable[[Image.Image], List[str]]


@dataclass
class TextRegion:
    x: int
    y: int
    width: int
    height: int
    label: str = "text"
    score: float = 1.0

    @property
    def area(self) -> int:
        return self.width * self.height


def _numpy_text_regions(gray: np.ndarray, cell: int = 24) -> List[TextRegion]:
    """Grid-based edge-density text/logo detector (pure NumPy)."""
    height, width = gray.shape
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
    gy[1:-1, :] = gray[2:, :] - gray[:-2, :]
    magnitude = np.sqrt(gx * gx + gy * gy)

    rows = (height + cell - 1) // cell
    cols = (width + cell - 1) // cell
    density = np.zeros((rows, cols))
    for r in range(rows):
        for c in range(cols):
            block = magnitude[r * cell : (r + 1) * cell, c * cell : (c + 1) * cell]
            density[r, c] = block.mean() if block.size else 0.0

    threshold = density.mean() + density.std()
    active = density > max(threshold, 20.0)
    regions: List[TextRegion] = []
    visited = np.zeros_like(active, dtype=bool)
    for r in range(rows):
        for c in range(cols):
            if not active[r, c] or visited[r, c]:
                continue
            stack = [(r, c)]
            visited[r, c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and active[nr, nc] and not visited[nr, nc]:
                        visited[nr, nc] = True
                        stack.append((nr, nc))
            if len(cells) < 2:
                continue
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            x0, y0 = min(cs) * cell, min(rs) * cell
            x1, y1 = min(width, (max(cs) + 1) * cell), min(height, (max(rs) + 1) * cell)
            regions.append(TextRegion(x0, y0, x1 - x0, y1 - y0, "text", 0.5))
    return regions


def detect_text_logo(image: Image.Image) -> List[TextRegion]:
    """Return candidate text/logo regions."""
    source = image.convert("RGB")
    gray = np.asarray(source.convert("L"), dtype=np.uint8)

    if cv2 is not None:
        mser = cv2.MSER_create(_delta=5, _min_area=60, _max_area=14000)
        regions, _ = mser.detectRegions(gray)
        boxes: List[TextRegion] = []
        for region in regions:
            x, y, w, h = cv2.boundingRect(region)
            if w < 8 or h < 8:
                continue
            boxes.append(TextRegion(int(x), int(y), int(w), int(h)))
        return _merge_boxes(boxes)

    return _numpy_text_regions(gray.astype(np.float64))


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
            current = TextRegion(x0, y0, x1 - x0, y1 - y0, "merged", max(current.score, nxt.score))
        else:
            merged.append(current)
            current = nxt
    merged.append(current)
    return merged


def detect_scratches(image: Image.Image) -> List[TextRegion]:
    """Return thin line regions (scratches / creases) on an old photo."""
    source = image.convert("RGB")
    gray = np.asarray(source.convert("L"), dtype=np.float32)
    high_pass = np.abs(gray - np.asarray(source.convert("L").filter(ImageFilter.GaussianBlur(3)), dtype=np.float32))
    threshold = high_pass.mean() + 2.0 * high_pass.std()
    mask = high_pass > threshold
    regions = _numpy_text_regions(mask.astype(np.float64) * 255.0, cell=16)
    for region in regions:
        region.label = "scratch"
    return regions


def merge_regions(regions: Sequence[TextRegion]) -> Optional[TextRegion]:
    """Merge a set of regions into their overall bounding box."""
    if not regions:
        return None
    x0 = min(r.x for r in regions)
    y0 = min(r.y for r in regions)
    x1 = max(r.x + r.width for r in regions)
    y1 = max(r.y + r.height for r in regions)
    return TextRegion(x0, y0, x1 - x0, y1 - y0, "merged")


def ocr_recheck_counts(detector: Optional[TextDetector], image: Image.Image) -> List[str]:
    """Run an OCR ``detector`` on ``image`` and return the strings it found."""
    if detector is None:
        return []
    return list(detector(image))
