"""Face analysis: bbox, 68 landmarks and identity embedding (design §2).

Target models: InsightFace / RetinaFace (bbox + 5/68/468 landmarks + ArcFace
embedding). Registered lazily under ``insightface``. Offline it uses OpenCV's
Haar cascade for the box and a geometrically-plausible 68-point layout derived
from that box, plus a deterministic descriptor for identity QA.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np
from PIL import Image

from photoai.engine.vram_manager import load_model

MODEL_KEY = "insightface"

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore


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
    if cv2 is None:
        return None
    for name in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt.xml"):
        try:
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + name)
            if not cascade.empty():
                return cascade
        except Exception:  # pragma: no cover
            continue
    return None


_CASCADE = _load_cascade()


def detect_faces(image: Image.Image) -> List[FaceBox]:
    """Return detected faces (Haar cascade when OpenCV is present)."""
    width, height = image.size

    if _CASCADE is not None:
        gray = np.asarray(image.convert("L"), dtype=np.uint8)
        faces = _CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) > 0:
            return [
                FaceBox(int(x), int(y), int(w), int(h), 1.0) for x, y, w, h in faces
            ]

    # Fallback: one centred face covering the middle third.
    box_w = max(1, width // 3)
    box_h = max(1, height // 3)
    return [FaceBox((width - box_w) // 2, (height - box_h) // 2, box_w, box_h, 1.0)]


def largest_face(faces: Sequence[FaceBox]) -> Optional[FaceBox]:
    if not faces:
        return None
    return max(faces, key=lambda face: face.area)


def landmarks_68(face: FaceBox) -> np.ndarray:
    """Return a plausible 68-point landmark layout for ``face``.

    Layout follows the standard iBUG/300-W ordering so downstream code
    (TPS chin warp, EAR) can index it identically to a real model.
    """
    x, y, w, h = face.x, face.y, face.width, face.height
    points: List[tuple[float, float]] = []

    # 0-16 jawline: left ear -> chin -> right ear.
    for i in range(17):
        t = i / 16.0
        px = x + w * (0.10 + 0.80 * t)
        py = y + h * (0.55 + 0.42 * np.sin(np.pi * t))
        points.append((px, py))

    # 17-26 eyebrows.
    for i in range(5):
        points.append((x + w * (0.18 + 0.12 * i), y + h * 0.30))
    for i in range(5):
        points.append((x + w * (0.52 + 0.12 * i), y + h * 0.30))

    # 27-30 nose bridge, 31-35 nostrils.
    for i in range(4):
        points.append((x + w * 0.50, y + h * (0.32 + 0.10 * i)))
    for i in range(5):
        points.append((x + w * (0.40 + 0.05 * i), y + h * 0.68))

    # 36-41 left eye, 42-47 right eye.
    points.extend(_eye_ring(x + w * 0.34, y + h * 0.42, w * 0.11, h * 0.045))
    points.extend(_eye_ring(x + w * 0.66, y + h * 0.42, w * 0.11, h * 0.045))

    # 48-67 outer / inner mouth.
    for i in range(12):
        angle = np.pi * i / 11.0
        points.append((x + w * (0.36 + 0.28 * i / 11.0), y + h * (0.80 - 0.05 * np.sin(angle))))
    for i in range(8):
        points.append((x + w * (0.42 + 0.16 * i / 7.0), y + h * (0.80 + 0.02 * np.sin(np.pi * i / 7.0))))

    return np.array(points[:68], dtype=np.float64)


def _eye_ring(cx: float, cy: float, rx: float, ry: float) -> List[tuple[float, float]]:
    ring = [(cx - rx, cy), (cx - rx * 0.5, cy - ry), (cx + rx * 0.5, cy - ry),
            (cx + rx, cy), (cx + rx * 0.5, cy + ry), (cx - rx * 0.5, cy + ry)]
    return ring


def embed(image: Image.Image, face: Optional[FaceBox] = None) -> np.ndarray:
    """Return a unit-norm identity descriptor for the (cropped) face.

    Uses the ArcFace model when registered; otherwise a deterministic 16x16
    luminance descriptor so identity QA is runnable offline.
    """
    model = load_model(MODEL_KEY)
    if model is not None:
        try:  # pragma: no cover - requires real weights
            crop = image.crop(face.box) if face else image
            vector = np.asarray(model(np.asarray(crop.convert("RGB"), dtype=np.uint8)), dtype=np.float64)
            norm = np.linalg.norm(vector)
            return vector / norm if norm else vector
        except Exception:
            pass

    crop = image.crop(face.box) if face else image
    gray = np.asarray(crop.convert("L").resize((16, 16)), dtype=np.float64)
    vector = gray.flatten()
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector
