"""Person detection / segmentation (AGENT_SKILLS S4).

P0 placeholder with a stable interface; a real segmenter (SAM) lands in P1.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from PIL import Image


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
    """Return detected persons. P0 placeholder returns an empty list."""
    return []


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
