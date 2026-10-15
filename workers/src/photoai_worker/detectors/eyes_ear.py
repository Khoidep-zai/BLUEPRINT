"""Eye aspect ratio (EAR) (AGENT_SKILLS S3).

P1: real EAR maths from six eye landmarks, with a deterministic landmark
synthesiser that targets a given EAR so the pipeline is testable without a
heavy landmark model. A real landmark model (MediaPipe/InsightFace) lands
in a later phase.
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
    """Compute EAR from six eye landmarks (see module docstring).

    EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)
    """
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

    Builds geometrically plausible landmarks whose computed EAR equals ``ear``,
    so the filter step can be exercised deterministically without a landmark
    model. Replaced by a real landmark model later.
    """
    eye_width = face.width * 0.3
    center_x = face.x + (face.width * 0.32 if eye == "left" else face.width * 0.68)
    center_y = face.y + face.height * 0.42
    half = eye_width / 2.0
    p1 = (center_x - half, center_y)
    p4 = (center_x + half, center_y)
    vertical = ear * eye_width  # EAR = vertical / (2*half), and 2*half = eye_width
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

    P1: computes real EAR from synthesised landmarks targeting the supplied
    ear values. Returns ``None`` when no face is available.
    """
    if face is None:
        return None
    left = compute_ear(eye_landmarks(face, ear=left_ear, eye="left"))
    right = compute_ear(eye_landmarks(face, ear=right_ear, eye="right"))
    return EyeState(left_ear=left, right_ear=right, threshold=threshold)


def recheck_ear(
    image: Image.Image,
    face: Optional[FaceBox] = None,
    previous: Optional[EyeState] = None,
    params: Optional[dict] = None,
) -> Optional[EyeState]:
    """Re-detect EAR on the *edited* image (P1 QA re-check).

    The real implementation runs a landmark model on ``image``. Until that
    model lands, the measurement is simulated from the ``post_left_ear`` /
    ``post_right_ear`` params when they are provided; otherwise the pre-edit
    EAR is returned unchanged, so recipes that gate on ``ear_min`` fail
    honestly with the mock provider instead of silently passing.
    """
    if previous is None or face is None:
        return None
    params = params or {}
    left = float(params.get("post_left_ear", previous.left_ear))
    right = float(params.get("post_right_ear", previous.right_ear))
    return detect_eyes(
        image,
        face=face,
        left_ear=left,
        right_ear=right,
        threshold=previous.threshold,
    )
