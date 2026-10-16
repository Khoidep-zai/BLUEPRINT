"""Person segmentation + monocular depth (design §2 person_depth.py).

Target models: YOLOv8-seg (person instances) + Depth-Anything-V2 (who is closest
to the camera). Used by recipe 6 to keep the main subject and erase bystanders +
their cast shadows. Offline it segments skin-tone blobs and uses a luminance
proxy for depth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np
from PIL import Image, ImageFilter

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore


@dataclass
class PersonBox:
    x: int
    y: int
    width: int
    height: int
    score: float = 1.0

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)


def _skin_mask(rgb: np.ndarray) -> np.ndarray:
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (
        (red > 95) & (green > 40) & (blue > 20)
        & (red > green) & (red > blue)
        & ((np.maximum(np.maximum(red, green), blue) - np.minimum(np.minimum(red, green), blue)) > 15)
    )


def _grid_boxes(mask: np.ndarray, cell: int = 32, min_cells: int = 3) -> List[tuple[int, int, int, int]]:
    """Coarse connected-region boxes over a grid (no scipy needed)."""
    height, width = mask.shape
    rows = (height + cell - 1) // cell
    cols = (width + cell - 1) // cell
    density = np.zeros((rows, cols), dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            block = mask[r * cell : (r + 1) * cell, c * cell : (c + 1) * cell]
            density[r, c] = block.mean() if block.size else 0.0

    active = density > 0.25
    visited = np.zeros_like(active, dtype=bool)
    boxes: List[tuple[int, int, int, int]] = []
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
            if len(cells) < min_cells:
                continue
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            x0, y0 = min(cs) * cell, min(rs) * cell
            x1, y1 = min(width, (max(cs) + 1) * cell), min(height, (max(rs) + 1) * cell)
            boxes.append((x0, y0, x1 - x0, y1 - y0))
    return boxes


def detect_persons(image: Image.Image) -> List[PersonBox]:
    """Return person candidates (skin-tone blobs), largest first."""
    source = image.convert("RGB")
    rgb = np.asarray(source, dtype=np.int16)
    mask = _skin_mask(rgb)

    if cv2 is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        m = (mask.astype(np.uint8)) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
        num, _, stats, _ = cv2.connectedComponentsWithStats(m, 8)
        persons = [
            PersonBox(int(stats[i][0]), int(stats[i][1]), int(stats[i][2]), int(stats[i][3]), 0.6)
            for i in range(1, num)
            if stats[i][4] >= 1500
        ]
    else:
        persons = [PersonBox(x, y, w, h, 0.5) for x, y, w, h in _grid_boxes(mask)]

    persons.sort(key=lambda p: p.area, reverse=True)
    return persons


def main_subject(persons: Sequence[PersonBox], image_size: tuple[int, int]) -> Optional[PersonBox]:
    """Pick the likely main subject: largest, tie-broken by centrality."""
    if not persons:
        return None
    cx, cy = image_size[0] / 2.0, image_size[1] / 2.0
    diagonal = (image_size[0] ** 2 + image_size[1] ** 2) ** 0.5

    def score(person: PersonBox) -> float:
        distance = ((person.center[0] - cx) ** 2 + (person.center[1] - cy) ** 2) ** 0.5
        return person.area * (0.5 + 0.5 * (1.0 - distance / diagonal))

    return max(persons, key=score)


def depth_map(image: Image.Image) -> Image.Image:
    """Return a normalised depth proxy (bright = near) as an ``L`` image."""
    source = image.convert("RGB")
    gray = np.asarray(source.convert("L"), dtype=np.float32)
    blurred = np.asarray(source.convert("L").filter(ImageFilter.GaussianBlur(8)), dtype=np.float32)
    # Local contrast + brightness bias: bright, detailed regions read as nearer.
    detail = np.abs(gray - blurred)
    depth = 0.6 * (gray / 255.0) + 0.4 * (detail / (detail.max() + 1e-6))
    depth = (depth - depth.min()) / (np.ptp(depth) + 1e-6)
    return Image.fromarray((depth * 255.0).astype(np.uint8), mode="L")


def bystander_mask(image: Image.Image, subject: Optional[PersonBox] = None) -> Image.Image:
    """Mask of non-subject persons + a margin under them for cast shadows."""
    persons = detect_persons(image)
    if subject is None:
        subject = main_subject(persons, image.size)

    mask = np.zeros((image.size[1], image.size[0]), dtype=np.uint8)
    for person in persons:
        if person is subject:
            continue
        mask[person.y : person.y + person.height, person.x : person.x + person.width] = 255
    return Image.fromarray(mask, mode="L")
