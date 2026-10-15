"""Eye aspect ratio (EAR) (AGENT_SKILLS S3).

The EAR formula is:

    EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)

with the six eye landmarks ordered ``p1..p6`` around the eye (left corner, two
upper-lid points, right corner, two lower-lid points). Landmark extraction needs
a real model (P1); the EAR maths is real and unit-tested here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from PIL import Image

from .face import FaceBox

Point = Tuple[float, float]

# Default threshold from S3; tuned later against the golden set.
DEFAULT_EAR_THRESHOLD = 0.2


@dataclass
class EyeState:
    """EAR result for a single face."""

    left_ear: float
    right_ear: float
    threshold: float = DEFAULT_EAR_THRESHOLD

    @property
    def ear(self) -> float:
        """Worst (lowest) EAR across both eyes -- the value the recipe filters on."""
        return min(self.left_ear, self.right_ear)

    @property
    def eyes_closed(self) -> bool:
        """True when at least one eye is below the threshold."""
        return self.left_ear < self.threshold or self.right_ear < self.threshold


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def compute_ear(points: Sequence[Point]) -> float:
    """Compute EAR from six eye landmarks (see module docstring)."""
    if len(points) != 6:
        raise ValueError(f"expected 6 landmarks, got {len(points)}")
    p1, p2, p3, p4, p5, p6 = points
    horizontal = _distance(p1, p4)
    if horizontal == 0.0:
        return 0.0
    vertical = _distance(p2, p6) + _distance(p3, p5)
    return vertical / (2.0 * horizontal)


def eye_landmarks(
    face: FaceBox,
    ear: float = 0.15,
    eye: str = "left",
) -> list[Point]:
    """Synthesise six landmarks for one eye of ``face`` with a target EAR.

    P0 placeholder: builds geometrically plausible landmarks whose computed EAR
    equals ``ear``. Replaced by a real landmark model in P1.
    """
    eye_width = face.width * 0.3
    center_x = face.x + (face.width * 0.32 if eye == "left" else face.width * 0.68)
    center_y = face.y + face.height * 0.42
    half = eye_width / 2.0
    # p1 (left), p4 (right); vertical span chosen so EAR == target.
    p1 = (center_x - half, center_y)
    p4 = (center_x + half, center_y)
    vertical = ear * eye_width  # since EAR = vertical / (2*half) and 2*half = width
    p2 = (center_x - half * 0.5, center_y - vertical * 0.5)
    p3 = (center_x + half * 0.5, center_y - vertical * 0.5)
    p6 = (center_x - half * 0.5, center_y + vertical * 0.5)
    p5 = (center_x + half * 0.5, center_y + vertical * 0.5)
    return [p1, p2, p3, p4, p5, p6]


def detect_eyes(
    image: Image.Image,
    face: Optional[FaceBox] = None,
    left_ear: float = 0.15,
    right_ear: float = 0.15,
    threshold: float = DEFAULT_EAR_THRESHOLD,
) -> Optional[EyeState]:
    """Return EAR for a face.

    P0 placeholder: EAR values are supplied/configurable rather than measured,
    so the filter step can be exercised deterministically. Returns ``None`` when
    no face is available.
    """
    if face is None:
        return None
    # Exercise the real EAR maths so the plumbing is genuine even in P0.
    left = compute_ear(eye_landmarks(face, ear=left_ear, eye="left"))
    right = compute_ear(eye_landmarks(face, ear=right_ear, eye="right"))
    return EyeState(left_ear=left, right_ear=right, threshold=threshold)
