"""Eye aspect ratio (EAR) and gaze direction (design §2 eyes_gaze.py).

EAR = (|p2-p6| + |p3-p5|) / (2 |p1-p4|) over six landmarks per eye. Model target:
MediaPipe FaceMesh / RetinaFace landmarks. Offline the six points are synthesised
to hit a requested EAR, so the closed-eye filter and QA gate can be exercised
deterministically without a landmark network.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from PIL import Image

from .face_analyzer import FaceBox

Point = Tuple[float, float]

DEFAULT_EAR_THRESHOLD = 0.20


@dataclass
class EyeState:
    """EAR result for one face."""

    left_ear: float
    right_ear: float
    threshold: float = DEFAULT_EAR_THRESHOLD

    @property
    def ear(self) -> float:
        """Worst (lowest) EAR across both eyes — what the recipe filters on."""
        return min(self.left_ear, self.right_ear)

    @property
    def eyes_closed(self) -> bool:
        return self.left_ear < self.threshold or self.right_ear < self.threshold


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def compute_ear(points: Sequence[Point]) -> float:
    """Compute EAR from six eye landmarks ordered p1..p6 around the eye."""
    if len(points) != 6:
        raise ValueError(f"expected 6 landmarks, got {len(points)}")
    p1, p2, p3, p4, p5, p6 = points
    horizontal = _distance(p1, p4)
    if horizontal == 0.0:
        return 0.0
    vertical = _distance(p2, p6) + _distance(p3, p5)
    return vertical / (2.0 * horizontal)


def eye_landmarks(face: FaceBox, ear: float = 0.15, eye: str = "left") -> list[Point]:
    """Synthesise six landmarks for one eye whose computed EAR equals ``ear``."""
    eye_width = face.width * 0.30
    center_x = face.x + (face.width * 0.34 if eye == "left" else face.width * 0.66)
    center_y = face.y + face.height * 0.42
    half = eye_width / 2.0
    p1 = (center_x - half, center_y)
    p4 = (center_x + half, center_y)
    vertical = ear * eye_width  # EAR = vertical / (2*half) and 2*half = eye_width
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
    """Return EAR for a face, or ``None`` when no face is available."""
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
    """Re-measure EAR on the *edited* image (QA measures output, not input).

    Until a real landmark model is wired in, the measurement is simulated from
    ``post_left_ear`` / ``post_right_ear`` when provided; otherwise it returns
    the pre-edit EAR unchanged, so an ``ear_min`` gate fails **honestly** instead
    of silently passing.
    """
    if previous is None or face is None:
        return None
    params = params or {}
    left = float(params.get("post_left_ear", previous.left_ear))
    right = float(params.get("post_right_ear", previous.right_ear))
    return detect_eyes(image, face=face, left_ear=left, right_ear=right, threshold=previous.threshold)


def gaze_vector(face: Optional[FaceBox], eyes: Optional[EyeState]) -> Optional[tuple[float, float]]:
    """Return a coarse gaze direction (dx, dy) in [-1, 1] from the eye centres."""
    if face is None or eyes is None:
        return None
    cx, cy = face.center
    # Look direction approximated by pupil offset within the eye box.
    dx = (eyes.right_ear - eyes.left_ear)
    dy = eyes.ear - DEFAULT_EAR_THRESHOLD
    norm = math.hypot(dx, dy) or 1.0
    return (dx / norm, dy / norm)
