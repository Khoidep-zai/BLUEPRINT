"""Person detection / segmentation (AGENT_SKILLS S4).

P1: lightweight heuristic person detector using OpenCV contour/colour analysis
when OpenCV is available, falling back to empty list (P0 behaviour). A real
segmenter (SAM) lands in a later phase.
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
class PersonBox:
    """A detected person bounding box in pixel coordinates."""

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


def detect_persons(image: Image.Image) -> List[PersonBox]:
    """Return detected persons.

    P1 heuristic: detect skin-tone blobs in the image and return their bounding
    boxes as person candidates. Falls back to ``[]`` when OpenCV is unavailable.
    """
    if not _HAVE_OPENCV or cv2 is None or np is None:
        return []

    width, height = image.size
    rgb = np.array(image.convert("RGB"), dtype=np.uint8)

    # Simple skin-tone mask (crude but dependency-free heuristic).
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    skin = (
        (r > 95) & (g > 40) & (b > 20)
        & (r > g) & (r > b)
        & ((np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) > 15)
    ).astype(np.uint8) * 255

    # Clean up with morphology.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, kernel)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(skin, 8)
    persons: List[PersonBox] = []
    for label in range(1, num_labels):
        x, y, w, h, area = stats[label]
        if area < 1500:  # ignore tiny blobs
            continue
        persons.append(PersonBox(x=int(x), y=int(y), width=int(w), height=int(h), score=0.6))

    # Sort by area descending.
    persons.sort(key=lambda p: p.area, reverse=True)
    return persons


def main_subject(
    persons: Sequence[PersonBox],
    image_size: tuple[int, int],
) -> Optional[PersonBox]:
    """Pick the main subject: largest area, breaking ties by closeness to centre."""
    if not persons:
        return None
    center_x, center_y = image_size[0] / 2.0, image_size[1] / 2.0
    diagonal = (image_size[0] ** 2 + image_size[1] ** 2) ** 0.5

    def score(person: PersonBox) -> float:
        distance = (
            (person.center[0] - center_x) ** 2 + (person.center[1] - center_y) ** 2
        ) ** 0.5
        centrality = 1.0 - distance / diagonal
        return person.area * (0.5 + 0.5 * centrality)

    return max(persons, key=score)
