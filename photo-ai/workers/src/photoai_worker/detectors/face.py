"""Face detection (AGENT_SKILLS S3).

A real detector (MediaPipe/InsightFace) lands in P1. This module fixes the
interface (``detect_faces`` -> list of :class:`FaceBox`) and ships a
deterministic placeholder so the P0 pipeline runs without AI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from PIL import Image


@dataclass
class FaceBox:
    """A detected face bounding box in pixel coordinates."""

    x: int
    y: int
    width: int
    height: int
    score: float = 1.0

    @property
    def box(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)


def detect_faces(image: Image.Image) -> List[FaceBox]:
    """Return detected faces.

    P0 placeholder: reports a single centred face covering the middle third of
    the image. Replace with a real detector in P1.
    """
    width, height = image.size
    box_w = max(1, width // 3)
    box_h = max(1, height // 3)
    return [
        FaceBox(
            x=(width - box_w) // 2,
            y=(height - box_h) // 2,
            width=box_w,
            height=box_h,
            score=1.0,
        )
    ]


def largest_face(faces: Sequence[FaceBox]) -> Optional[FaceBox]:
    """Return the largest face, or ``None`` when there are no faces."""
    if not faces:
        return None
    return max(faces, key=lambda face: face.area)
