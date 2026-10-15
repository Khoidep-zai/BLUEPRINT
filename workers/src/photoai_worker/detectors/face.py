"""Face detection (AGENT_SKILLS S3).

P1: real OpenCV Haar Cascade detector when the cascade XML is available,
falling back to the deterministic centred-face placeholder so the pipeline
stays runnable in any environment (self-hosted CPU, no model downloads).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from PIL import Image

try:
    import cv2  # type: ignore
    import numpy as np
    _HAVE_OPENCV = True
except Exception:  # pragma: no cover - OpenCV optional in minimal installs
    _HAVE_OPENCV = False
    cv2 = None  # type: ignore
    np = None  # type: ignore


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


def _load_cascade() -> Optional["cv2.CascadeClassifier"]:
    """Load OpenCV's frontal-face Haar cascade if it ships with the install."""
    if not _HAVE_OPENCV or cv2 is None:
        return None
    candidates = [
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
        cv2.data.haarcascades + "haarcascade_frontalface_alt.xml",
    ]
    for path in candidates:
        try:
            cascade = cv2.CascadeClassifier(path)
            if not cascade.empty():
                return cascade
        except Exception:
            continue
    return None


_CASCADE = _load_cascade()


def detect_faces(image: Image.Image) -> List[FaceBox]:
    """Return detected faces.

    P1: uses OpenCV Haar Cascade when available; otherwise falls back to the
    P0 centred-face placeholder. Never downloads models.
    """
    width, height = image.size

    if _CASCADE is not None and np is not None:
        gray = np.array(image.convert("L"), dtype=np.uint8)
        faces = _CASCADE.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        if len(faces) > 0:
            return [
                FaceBox(x=int(x), y=int(y), width=int(w), height=int(h), score=1.0)
                for x, y, w, h in faces
            ]

    # Fallback: single centred face covering the middle third (P0 behaviour).
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
